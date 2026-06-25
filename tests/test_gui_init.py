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
_SNIPPET = (
    "import faulthandler, sys\n"
    "faulthandler.enable()\n"
    "from qiskit_metal import designs, MetalGUI\n"
    "design = designs.DesignPlanar()\n"
    "gui = MetalGUI(design)\n"
    "print('MARKER_INIT_OK', flush=True)\n"
    "sys.exit(0)\n"
)


class TestGUIInitOnScreen(unittest.TestCase):
    """Issues #1048 / #1109 — MetalGUI.__init__ must complete without
    hanging or crashing on a real display."""

    def test_metalgui_init_completes(self):
        """MetalGUI(design) must build cleanly on a real display."""
        if not _display_available():
            self.skipTest("no display available (needs desktop session or Xvfb)")

        proc = subprocess.run(
            [sys.executable, "-X", "faulthandler", "-c", _SNIPPET],
            capture_output=True,
            text=True,
            timeout=240,
        )

        self.assertIn(
            "MARKER_INIT_OK",
            proc.stdout,
            msg=(
                f"MetalGUI.__init__ did not complete (wedged or silently "
                f"abandoned -- issue #1109).\n"
                f"stdout:\n{proc.stdout}\n"
                f"stderr tail:\n{proc.stderr[-2000:]}"
            ),
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=(
                f"MetalGUI init subprocess exited {proc.returncode} "
                f"(non-zero / segfault -- issue #1048 init-branch regression).\n"
                f"stderr tail:\n{proc.stderr[-2000:]}"
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
