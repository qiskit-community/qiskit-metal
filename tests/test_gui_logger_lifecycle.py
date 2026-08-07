# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""GUI teardown must not leave Qt-backed log handlers attached (issue #1048).

Distinct from the two sibling suites:

* ``test_gui_teardown.py`` covers the exit-time segfault (PR #1104 / v0.7.4).
* ``test_gui_init.py``     covers the persisted-state init crash (#1122 / #1128).

This one covers the *re-run / long-session* path reported on macOS: the
handlers that stream log records into the GUI's log dock are registered on
**process-global** loggers (``logging.getLogger("metal")`` and the GUI
logger), but nothing detached them when the window closed. After teardown
the handler survived while its backing ``QTextEditLogger`` C++ object did
not, so every later log record in the process wrote into freed memory.

PySide6 raises a catchable ``RuntimeError`` for that on some builds, but a
dangling Shiboken wrapper is undefined behaviour in general — on other
builds it is a hard SIGSEGV with no Python traceback, which is the
"kernel appears to have died" symptom. The bug was latent for a second
reason: the cleanup hook guarded on ``hasattr(self, "log_text")``, which is
never true (the widget lives at ``self.ui.log_text``), and it only ran from
``QWidget.destroy()`` — a method Qt does not call on a normal close or on
Python garbage collection.

These tests run in-process (a live QApplication is enough); they do not
need the subprocess treatment the segfault tests use.
"""

import gc
import logging
import os
import unittest


def _qt_available():
    """Whether a Qt GUI can actually be constructed in this environment."""
    if os.environ.get("QISKIT_METAL_HEADLESS"):
        return False
    if not os.environ.get("DISPLAY") and os.name != "nt":
        return False
    try:
        import PySide6  # noqa: F401
    except ImportError:
        return False
    return True


@unittest.skipUnless(_qt_available(), "needs PySide6 and a display (Xvfb or desktop)")
class TestGUILoggerLifecycle(unittest.TestCase):
    """Issue #1048 — closing MetalGUI must detach its Qt-backed log handlers."""

    def setUp(self):
        from PySide6.QtWidgets import QApplication

        self.app = QApplication.instance() or QApplication([])

    def _build_and_close_gui(self):
        """Build a MetalGUI and close it the way a user closes the window."""
        from qiskit_metal import designs, MetalGUI

        gui = MetalGUI(designs.DesignPlanar())
        # force_close skips the "save unsaved changes?" modal, which would
        # block forever without a user; the close path under test is the same.
        gui.main_window.force_close = True
        gui.main_window.close()
        self.app.processEvents()
        return gui

    @staticmethod
    def _dead_qt_handlers(logger):
        """Handlers on ``logger`` whose backing C++ widget is already gone."""
        import shiboken6

        dead = []
        for handler in logger.handlers:
            widget = getattr(handler, "log_qtextedit", None)
            if widget is not None and not shiboken6.isValid(widget):
                dead.append(handler)
        return dead

    def test_no_dead_handler_left_on_global_logger(self):
        """After close + gc, no handler may point at a freed C++ widget."""
        metal_logger = logging.getLogger("metal")

        gui = self._build_and_close_gui()
        del gui
        gc.collect()
        self.app.processEvents()
        gc.collect()

        dead = self._dead_qt_handlers(metal_logger)
        self.assertEqual(
            dead,
            [],
            msg=(
                "Closed MetalGUI left {} handler(s) attached to the global "
                "'metal' logger with a deleted QTextEditLogger behind them. "
                "Every subsequent log record in this process is a "
                "use-after-free (issue #1048).".format(len(dead))
            ),
        )

    def test_logging_after_close_is_safe(self):
        """Emitting a record after the GUI is gone must not raise or crash."""
        metal_logger = logging.getLogger("metal")

        gui = self._build_and_close_gui()
        del gui
        gc.collect()
        self.app.processEvents()

        # Before the fix this printed "Logger issue: Internal C++ object
        # (QTextEditLogger) already deleted" — the benign manifestation of
        # the same dangling access that segfaults on other PySide6 builds.
        metal_logger.info("post-teardown log record (issue #1048 regression)")

    def test_handlers_do_not_accumulate_across_instances(self):
        """Repeated open/close cycles must not grow the handler list.

        This is the reported "worked for hours, then started crashing"
        shape: each cycle used to leave one more dead handler behind, so the
        odds of a record landing on freed memory grew with session length.
        """
        metal_logger = logging.getLogger("metal")

        gui = self._build_and_close_gui()
        del gui
        gc.collect()
        baseline = len(metal_logger.handlers)

        for _ in range(2):
            gui = self._build_and_close_gui()
            del gui
            gc.collect()
            self.app.processEvents()

        self.assertEqual(
            len(metal_logger.handlers),
            baseline,
            msg=(
                "Handler count on the global 'metal' logger grew from "
                f"{baseline} to {len(metal_logger.handlers)} across "
                "open/close cycles (issue #1048)."
            ),
        )

    def test_refresh_timers_stopped_on_close(self):
        """The periodic model-refresh timers must not outlive the window."""
        from PySide6.QtCore import QTimer
        from qiskit_metal import designs, MetalGUI

        gui = MetalGUI(designs.DesignPlanar())
        main_window = gui.main_window

        running = [t for t in main_window.findChildren(QTimer) if t.isActive()]
        self.assertGreater(
            len(running),
            0,
            msg="expected the model-refresh timers to be running while open",
        )

        main_window.force_close = True
        main_window.close()
        self.app.processEvents()

        still_running = [t for t in main_window.findChildren(QTimer) if t.isActive()]
        self.assertEqual(
            still_running,
            [],
            msg=(
                f"{len(still_running)} refresh timer(s) still firing after "
                "close; a tick landing mid-teardown is a use-after-free "
                "(issue #1048)."
            ),
        )

    # ------------------------------------------------------------------
    # Close is not destruction. Everything above must not come at the cost
    # of the close-then-reopen workflow, which is exactly what the #1048
    # reporters do ("open MetalGUI, close it, and reopen it multiple
    # consecutive times in the same kernel"). An earlier cut of this fix
    # detached on close and left a reopened window with a dead log dock and
    # no auto-refresh; these two tests pin that behaviour down.
    # ------------------------------------------------------------------

    def test_log_dock_still_works_after_close_and_reopen(self):
        """Reopening a closed MetalGUI must not leave a dead log pane."""
        from qiskit_metal import designs, MetalGUI

        gui = MetalGUI(designs.DesignPlanar())
        main_window = gui.main_window

        main_window.force_close = True
        main_window.close()
        self.app.processEvents()

        main_window.show()
        self.app.processEvents()

        marker = "reopen-marker-1048"
        logging.getLogger("metal").info(marker)
        self.app.processEvents()

        self.assertIn(
            marker,
            main_window.ui.log_text.toPlainText(),
            msg=(
                "A reopened MetalGUI no longer receives log records. Handlers "
                "must detach on widget destruction, not on close -- close() "
                "only hides the window (issue #1048)."
            ),
        )

    def test_refresh_timers_restart_on_reopen(self):
        """Pausing the timers on close must not be a one-way trip."""
        from PySide6.QtCore import QTimer
        from qiskit_metal import designs, MetalGUI

        gui = MetalGUI(designs.DesignPlanar())
        main_window = gui.main_window
        expected = len([t for t in main_window.findChildren(QTimer) if t.isActive()])

        main_window.force_close = True
        main_window.close()
        self.app.processEvents()
        main_window.show()
        self.app.processEvents()

        running = len([t for t in main_window.findChildren(QTimer) if t.isActive()])
        self.assertEqual(
            running,
            expected,
            msg=(
                f"only {running} of {expected} refresh timer(s) restarted on "
                "reopen; the tables would silently stop updating."
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
