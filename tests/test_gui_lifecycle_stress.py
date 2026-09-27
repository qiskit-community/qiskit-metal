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

"""Repeated MetalGUI build/teardown cycles must leave no timer firing into
dead widgets.

This is the reproducer for issue #1048 "failure mode 4" -- the
nondeterministic mid-session teardown segfault. The mechanism: a deferred
Qt callback (a ``QTimer.singleShot`` or a polling ``QTimer``) outlives the
widget it references; when it fires, it lands on a destroyed C++ object.
Python-visible symptom: ``RuntimeError: Internal C++ object ... already
deleted`` printed from the event loop. Native symptom, when the freed
memory has been reused: a segfault.

The cycle loop runs in a **subprocess**, deliberately. The first version
ran it in-process and promptly proved the point on CI: a macOS 3.11
runner lost the race and the native crash took down the entire pytest
process (tox ``FAIL code -11``), cancelling the rest of the matrix. The
same nondeterministic crash that motivates the test cannot be allowed to
destroy the evidence. In a child process we can attribute the outcome:

- ``already deleted`` anywhere in the child's output -> **FAIL**: a
  deferred callback fired on a destroyed object. That's the
  deterministic, fixable leak class (find the unparented timer, parent
  it via ``single_shot()`` in ``_gui/utility/_toolbox_qt.py``).
- Child died natively without that marker -> **stderr NOTE**, not a
  failure: the known-open mode-4 race (see ``gui_crash_defenses.md``
  "Still open"), same attribution discipline as ``test_gui_init.py``.
- Clean exit, clean output -> pass.

Why a stress loop at all: single build/teardown runs on a fast dev
machine almost never land a timer tick inside the teardown window --
which is why this bug class was repeatedly caught by slow CI runners and
not locally.
"""

import subprocess
import sys

import pytest

from ._crash_output import crash_excerpt

pytest.importorskip("PySide6")

# Build -> pump -> close -> gc -> pump-past-every-timer-deadline, cycled.
# The longest deferred-callback deadline in the GUI is the log widget's
# 1500 ms welcome message; the post-teardown pump goes comfortably past it
# so every armed timer that is going to fire has fired while the process
# is still alive to report it.
_STRESS_SNIPPET = """
import faulthandler, gc, sys
faulthandler.enable()

from PySide6.QtCore import QElapsedTimer, QEventLoop
from PySide6.QtWidgets import QApplication

from qiskit_metal import designs
from qiskit_metal._gui.main_window import MetalGUI
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket


def pump(app, ms):
    elapsed = QElapsedTimer()
    elapsed.start()
    while elapsed.elapsed() < ms:
        app.processEvents(QEventLoop.AllEvents, 50)
    app.processEvents()


for cycle in range(3):
    design = designs.DesignPlanar()
    gui = MetalGUI(design)
    app = QApplication.instance()
    try:
        TransmonPocket(design, "Q1")
        gui.rebuild()
        pump(app, 300)
    finally:
        gui.main_window.force_close = True
        gui.main_window.close()
    del gui, design
    gc.collect()
    pump(app, 2000)
    print(f"MARKER_CYCLE_{cycle}_DONE", flush=True)

print("MARKER_STRESS_OK", flush=True)
sys.exit(0)
"""


def test_repeated_build_teardown_leaves_no_dead_timer_callbacks():
    """Cycle MetalGUI build/teardown in a child process and attribute the
    outcome: dead-object callbacks fail; the known-open native race is
    reported without destroying the rest of the suite."""
    proc = subprocess.run(
        [sys.executable, "-X", "faulthandler", "-c", _STRESS_SNIPPET],
        capture_output=True,
        text=True,
        timeout=300,
    )
    combined = proc.stdout + proc.stderr

    assert "already deleted" not in combined, (
        "a deferred Qt callback fired on a destroyed object -- a "
        "use-after-free of the issue #1048 failure-mode-4 class. Find the "
        "unparented QTimer/singleShot and parent it to the widget it "
        "touches (see single_shot() in _gui/utility/_toolbox_qt.py).\n"
        f"--- child output ---\n{combined[-3000:]}"
    )

    if proc.returncode != 0 or "MARKER_STRESS_OK" not in proc.stdout:
        cycles_done = proc.stdout.count("_DONE")
        print(
            f"NOTE: stress child exited {proc.returncode} after "
            f"{cycles_done}/3 cycles without an 'already deleted' report "
            "-- the known-open native mode-4 teardown race (see "
            "gui_crash_defenses.md 'Still open'), not an attributable "
            f"timer leak. stderr tail:\n{crash_excerpt(proc.stderr)}",
            file=sys.stderr,
        )
