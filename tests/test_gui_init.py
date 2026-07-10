# -*- coding: utf-8 -*-

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

"""On-screen MetalGUI initialization regression (issues #1048 / #1109).

Distinct from ``test_gui_teardown.py`` (which only covers the exit-time
segfault that PR #1104 / v0.7.4 fixed). This test guards the *init* path:
multiple reporters on Windows 11 (and at least one on macOS) see
``MetalGUI(design)`` render the QMainWindow briefly as bare scaffolding
("variable table / object inspector" per #1109), then either silently
abandon the GUI or take the kernel down — no Python traceback either way.

The MARKER_INIT_OK assertion catches the silent-abandonment case;
non-zero return code catches the segfault case. Combined, they fail
loudly on either failure mode.

Skips when PySide6 is absent (lite install) or when no display is
available (a desktop session on Windows/macOS, ``$DISPLAY`` or
``$WAYLAND_DISPLAY`` on Linux).
"""

import os
import subprocess
import sys
import unittest

import pytest

pytest.importorskip("PySide6")


def _display_available() -> bool:
    """True when a usable display is reachable from this process.

    GHA windows-2025 / macos-15 runners and any normal desktop session
    always have a usable display. Linux needs ``$DISPLAY`` (X11) or
    ``$WAYLAND_DISPLAY`` (Wayland) -- or ``xvfb-run`` wrapping the
    invocation.
    """
    if sys.platform.startswith("win") or sys.platform == "darwin":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


# Minimal init reproducer from the issue.  Prints MARKER_INIT_OK only if
# MetalGUI.__init__ actually returned; immediate sys.exit(0) keeps the
# subprocess scope to "init only" (teardown is test_gui_teardown.py's job).
# Clears any pre-existing MetalGUI QSettings first so this test can't be
# poisoned by state left behind by an interactive dev run on the same
# account.
_SNIPPET = (
    "import faulthandler, sys\n"
    "faulthandler.enable()\n"
    "from PySide6.QtCore import QSettings\n"
    "QSettings('QiskitMetal', 'MainWindow').clear()\n"
    "from qiskit_metal import designs, MetalGUI\n"
    "design = designs.DesignPlanar()\n"
    "gui = MetalGUI(design)\n"
    "print('MARKER_INIT_OK', flush=True)\n"
    "sys.exit(0)\n"
)

# Snippet 1 of the multi-session test: clear any prior state, build the
# GUI, explicitly save persisted window state, exit clean. Mirrors what
# a Jupyter kernel does when the user closes the MetalGUI.
_SAVE_STATE_SNIPPET = (
    "import faulthandler, sys\n"
    "faulthandler.enable()\n"
    "from PySide6.QtCore import QSettings\n"
    "QSettings('QiskitMetal', 'MainWindow').clear()\n"
    "from qiskit_metal import designs, MetalGUI\n"
    "design = designs.DesignPlanar()\n"
    "gui = MetalGUI(design)\n"
    "gui.main_window.save_window_settings()\n"
    "print('MARKER_SAVED_STATE', flush=True)\n"
    "sys.exit(0)\n"
)

# Snippet 2 of the multi-session test: build the GUI in a *fresh*
# process, exercising restore_window_settings against the state written
# by snippet 1. This is the exact pattern that regressed on RhinoHand's
# multi-Jupyter-kernel workflow after v0.7.5 (issue #1048).
_RESTORE_STATE_SNIPPET = (
    "import faulthandler, sys\n"
    "faulthandler.enable()\n"
    "from qiskit_metal import designs, MetalGUI\n"
    "design = designs.DesignPlanar()\n"
    "gui = MetalGUI(design)\n"
    "print('MARKER_RESTORED_OK', flush=True)\n"
    "sys.exit(0)\n"
)

# Tamper + restore: writes a deliberately-bogus display fingerprint into
# QSettings, then builds the GUI. Exercises the "fingerprint mismatch
# -> discard persisted state" path added in this PR without needing a
# real second monitor or a real undock event.
_TAMPERED_FINGERPRINT_SNIPPET = (
    "import faulthandler, sys\n"
    "faulthandler.enable()\n"
    "from PySide6.QtCore import QSettings\n"
    "s = QSettings('QiskitMetal', 'MainWindow')\n"
    "# Force a display fingerprint that will never match the current one\n"
    "s.setValue('display_fingerprint', 'BOGUS_FINGERPRINT_FOR_TEST')\n"
    "s.setValue('geometry', b'DEADBEEF_but_geometry_shape_is_fake')\n"
    "s.sync()\n"
    "from qiskit_metal import designs, MetalGUI\n"
    "design = designs.DesignPlanar()\n"
    "gui = MetalGUI(design)\n"
    "print('MARKER_TAMPERED_OK', flush=True)\n"
    "sys.exit(0)\n"
)


class TestGUIInitOnScreen(unittest.TestCase):
    """Issues #1048 / #1109 — MetalGUI.__init__ must complete without
    hanging or crashing on a real display."""

    def _run_snippet(self, snippet: str, marker: str) -> None:
        """Execute ``snippet`` in a fresh Python process under faulthandler
        and assert it printed ``marker`` and exited cleanly."""
        proc = subprocess.run(
            [sys.executable, "-X", "faulthandler", "-c", snippet],
            capture_output=True,
            text=True,
            timeout=240,
        )
        self.assertIn(
            marker,
            proc.stdout,
            msg=(
                f"MetalGUI.__init__ did not reach {marker} "
                "(wedged or silently abandoned -- issue #1109 / #1048).\n"
                f"stdout:\n{proc.stdout}\n"
                f"stderr tail:\n{proc.stderr[-2000:]}"
            ),
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=(
                f"MetalGUI init subprocess exited {proc.returncode} "
                "(non-zero / segfault -- issue #1048).\n"
                f"stderr tail:\n{proc.stderr[-2000:]}"
            ),
        )

    def test_metalgui_init_completes(self):
        """MetalGUI(design) must build cleanly on a real display."""
        if not _display_available():
            self.skipTest("no display available (needs desktop session or Xvfb)")
        self._run_snippet(_SNIPPET, "MARKER_INIT_OK")

    def test_metalgui_init_after_prior_session(self):
        """A second MetalGUI process must restore the first process's
        persisted state without crashing.

        Simulates the multi-Jupyter-kernel workflow that regressed
        RhinoHand's setup after v0.7.5
        (https://github.com/qiskit-community/qiskit-metal/issues/1048#issuecomment-4914073094):
        kernel A closes its GUI (writes registry state), kernel B in a
        different notebook opens its own GUI and reads that state.
        Same-machine fingerprint match should just work; the fingerprint
        added in this PR guarantees a mismatch would be caught instead of
        painted into an inconsistent widget tree.
        """
        if not _display_available():
            self.skipTest("no display available (needs desktop session or Xvfb)")
        self._run_snippet(_SAVE_STATE_SNIPPET, "MARKER_SAVED_STATE")
        self._run_snippet(_RESTORE_STATE_SNIPPET, "MARKER_RESTORED_OK")

    def test_metalgui_init_with_stale_fingerprint(self):
        """A persisted display fingerprint that no longer matches the
        current display must not brick GUI startup.

        Forcibly writes a bogus fingerprint (plus a bogus geometry blob
        that would crash Qt if actually applied) and asserts MetalGUI
        still starts. This exercises the "mismatch -> discard state"
        branch without requiring a real monitor hot-swap on the CI
        runner.
        """
        if not _display_available():
            self.skipTest("no display available (needs desktop session or Xvfb)")
        self._run_snippet(_TAMPERED_FINGERPRINT_SNIPPET, "MARKER_TAMPERED_OK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
