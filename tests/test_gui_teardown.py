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

"""Regression test for the MetalGUI exit segfault (issue #1048).

Building a ``MetalGUI`` and letting the interpreter exit must not crash the
process. Before the at-exit Qt teardown (``main_window._teardown_qt_widgets``),
PySide6 destroyed the ``QApplication`` during ``Py_FinalizeEx`` while the
window was still alive; a ``QWidget`` destructor then dispatched an event
through the main window's ``QMenuBar`` event filter -> null call -> SIGSEGV
(exit code 139 / -11). In a Jupyter kernel that surfaced as "the kernel
appears to have died".

The GUI is launched in a *subprocess* so a regression shows up as a nonzero
return code instead of taking the test runner down with it. The test needs a
display (a real desktop or ``Xvfb``); it skips otherwise, and the whole module
skips when the optional GUI extras (PySide6) are not installed.
"""

import os
import subprocess
import sys
import unittest

import pytest

pytest.importorskip("PySide6")

# Minimal reproducer from the issue: build the GUI, then exit.
_SNIPPET = (
    "import qiskit_metal as qm\n"
    "from qiskit_metal import designs, MetalGUI\n"
    "from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket\n"
    "design = designs.DesignPlanar()\n"
    "gui = MetalGUI(design)\n"
    "# also exercise a second instance + rebuild (the 're-run' path)\n"
    "gui2 = MetalGUI(designs.DesignPlanar())\n"
    "TransmonPocket(design, 'Q1', options=dict(connection_pads=dict(a=dict())))\n"
    "gui.rebuild()\n"
    "print('MARKER_BUILT', flush=True)\n"
)


class TestGUITeardown(unittest.TestCase):
    """Issue #1048 — MetalGUI must not segfault at interpreter exit."""

    def test_metalgui_process_exits_cleanly(self):
        """A process that builds MetalGUI must exit with code 0, not a
        segfault (139 / -11)."""
        if not os.environ.get("DISPLAY"):
            self.skipTest("no display available (needs Xvfb or a desktop session)")

        proc = subprocess.run(
            [sys.executable, "-X", "faulthandler", "-c", _SNIPPET],
            capture_output=True,
            text=True,
            timeout=240,
        )

        self.assertIn(
            "MARKER_BUILT",
            proc.stdout,
            msg=f"GUI failed to build.\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr[-2000:]}",
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=(
                f"MetalGUI subprocess exited with {proc.returncode} "
                f"(negative / 139 == segfault, i.e. issue #1048 regression).\n"
                f"stderr tail:\n{proc.stderr[-2000:]}"
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
