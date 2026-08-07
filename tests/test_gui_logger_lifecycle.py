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

    #: MetalGUI instances are deliberately never dropped. Letting one be
    #: collected in-process triggers the unfixed teardown segfault documented
    #: in TestGUIGarbageCollectionCrash below, which would take the whole test
    #: runner down (exit 139) instead of failing a single test. Holding a
    #: reference keeps these assertions measuring what they claim to measure.
    _kept = []

    def setUp(self):
        from PySide6.QtWidgets import QApplication

        self.app = QApplication.instance() or QApplication([])

    def _new_gui(self):
        """Build a MetalGUI and keep it alive for the process lifetime."""
        from qiskit_metal import designs, MetalGUI

        gui = MetalGUI(designs.DesignPlanar())
        self._kept.append(gui)
        return gui

    def _destroy_log_widget(self, gui):
        """Destroy just the log widget's C++ object.

        This is the event the handlers must react to -- ``destroyed`` --
        without tearing down the whole window, so it isolates the behaviour
        under test from the unrelated teardown crash.
        """
        import shiboken6

        shiboken6.delete(gui.main_window.ui.log_text)
        self.app.processEvents()

    def _build_and_close_gui(self):
        """Build a MetalGUI and close it the way a user closes the window."""
        gui = self._new_gui()
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
        """Once the log widget is destroyed, no handler may still point at it."""
        metal_logger = logging.getLogger("metal")

        gui = self._build_and_close_gui()
        self._destroy_log_widget(gui)

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
        self._destroy_log_widget(gui)

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
        self._destroy_log_widget(gui)
        baseline = len(metal_logger.handlers)

        for _ in range(2):
            gui = self._build_and_close_gui()
            self._destroy_log_widget(gui)

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

        gui = self._new_gui()
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

        gui = self._new_gui()
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

        gui = self._new_gui()
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


@unittest.skipUnless(_qt_available(), "needs PySide6 and a display (Xvfb or desktop)")
class TestGUIGarbageCollectionCrash(unittest.TestCase):
    """KNOWN UNFIXED (issue #1048): dropping a MetalGUI segfaults the process.

    Reported by @lgv3005 on macOS; reproduced here on Linux / PySide6
    6.10.1. Reproduces identically on unpatched ``main``, so it is not
    caused by the log-handler work in this file's sibling suite.

    **The crash is nondeterministic**, which is why this is skipped rather
    than marked ``expectedFailure``. In one session a 32-variant sweep
    crashed 16/32, with every two-instance variant failing and every
    one-instance variant passing; later, in the same container with the same
    commit, the identical scripts exited 0 ten times running. Nothing in the
    tree changed between those observations. That signature -- sensitive to
    memory layout and timing rather than to inputs -- is consistent with the
    heap being corrupted by the null-vtable dispatch below, and it matches
    the reporter's account of a session working for hours and then failing
    with no code change.

    An ``expectedFailure`` here would therefore turn into an intermittent
    "unexpected success", i.e. a flaky red CI. Run the snippet below by hand
    when working on this, several times, and do not read a single clean run
    as evidence of a fix.

    Sequence: build MetalGUI, close it, drop the reference, let the object
    be collected. The C-level backtrace (gdb) is::

        shiboken6           <- destroying the Python-owned wrapper
        ~QWidget
        ~QObject
        QObjectPrivate::setParent_helper       <- reparents children
        QCoreApplication::notifyInternal2      <- posts ChildRemoved
        sendThroughObjectEventFilters
        QMenuBar::eventFilter
        0x0000000000000000                     <- null vtable slot

    A child destruction dispatches an event through a ``QMenuBar`` event
    filter belonging to an object that is itself already half-destroyed.
    This is the same mechanism ``_teardown_qt_widgets`` describes, but that
    hook only runs via ``atexit``; ordinary collection mid-session is
    unprotected.

    **Marked expectedFailure rather than fixed.** ``_gui/`` is a hard-touch
    zone, and every candidate fix tried so far was falsified once tested
    against a *running event loop* (the condition that matters — a Jupyter
    kernel always has one):

    ============================================  ==========================
    candidate                                     result with a live loop
    ============================================  ==========================
    ``main_window.deleteLater()``                 crash merely deferred to
                                                  the next loop spin
    ``menuBar().deleteLater()`` first             crash
    ``main_window.removeEventFilter(menuBar())``  crash
    ``menuBar().clear()`` + removeEventFilter     crash
    ``setMenuBar(QMenuBar(main_window))``         crash
    parent the menubars at construction in the
    generated ``*_ui.py`` files                   crash
    ``shiboken6.delete(main_window)``             crash
    ============================================  ==========================

    ``deleteLater`` is the trap worth calling out: it makes the crash vanish
    from any test that never runs an event loop afterwards, because the
    deletion simply never happens. Verify candidates with ``app.exec()``,
    not ``processEvents()``.

    When this is genuinely fixed, drop the skip and promote the snippet to a
    real assertion -- but only once it has been shown to survive many
    repetitions, on more than one machine.
    """

    _SNIPPET = (
        "import gc\n"
        "from PySide6.QtWidgets import QApplication\n"
        "from PySide6.QtCore import QTimer\n"
        "from qiskit_metal import designs, MetalGUI\n"
        "app = QApplication.instance() or QApplication([])\n"
        "guis = [MetalGUI(designs.DesignPlanar()) for _ in range(2)]\n"
        "for g in guis:\n"
        "    g.main_window.force_close = True\n"
        "    g.main_window.close()\n"
        "app.processEvents()\n"
        "guis = None\n"
        "gc.collect()\n"
        "QTimer.singleShot(1200, app.quit)\n"
        "app.exec()\n"
        "print('SURVIVED_GC', flush=True)\n"
    )

    @unittest.skip(
        "issue #1048: known-unfixed teardown segfault. Crash is "
        "nondeterministic, so asserting either way makes CI flaky. "
        "See the class docstring for the backtrace and the "
        "falsified-candidate table."
    )
    def test_dropping_metalgui_does_not_segfault(self):
        """Drop two MetalGUIs, then run an event loop. SIGSEGVs intermittently."""
        import subprocess
        import sys

        proc = subprocess.run(
            [sys.executable, "-X", "faulthandler", "-c", self._SNIPPET],
            capture_output=True,
            text=True,
            timeout=300,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=(
                f"process died during teardown (rc={proc.returncode}; "
                f"-11/139 == SIGSEGV) — issue #1048, known unfixed.\n"
                f"stderr tail:\n{proc.stderr[-800:]}"
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
