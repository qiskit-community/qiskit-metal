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

"""``QTreeModel_Base``'s polling ``QTimer`` must not touch a destroyed view.

The model and its view can be torn down independently -- closing a dock or
dialog destroys the view, but the model's own ``QTimer`` (parented to the
model, not the view) keeps firing on its 500ms cadence regardless and calls
back into ``self._view`` on every tick.

This was caught via CI, not locally: a real on-screen/native run of the
full suite showed segfaults and self-heal-test failures in
``test_gui_init.py`` (issue #1048 failure mode 4, the "mid-session GC
teardown segfault") that traced back to
``tests/test_gui_nudge.py::TestRealClickAndKeyDelivery`` leaving one of
these timers alive past a dock's destruction. It had looked like a benign,
exit-code-0 artifact under a plain headless ``pytest`` run (see the
"Still open" note in ``docs/architecture/gui_crash_defenses.md`` predating
this fix) -- CI's real display and larger, longer-lived Qt object graph is
what actually surfaced the use-after-free.
"""

import os
import subprocess
import sys

import pytest

from tests._crash_output import crash_excerpt

pytest.importorskip("PySide6")

# The scenarios build a real QApplication, delete a view's C++ object out from
# under a live model, and leave 500 ms polling timers armed. Run in the pytest
# process, a native loss of that race kills the whole matrix (seen on the
# Python 3.14 macOS CI job), so they run in a child that proves each step with
# a printed marker.
_SNIPPET = """
import faulthandler
faulthandler.enable()
import shiboken6
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])

from qiskit_metal import designs
from qiskit_metal._gui.tree_view_base import QTreeView_Base
from qiskit_metal._gui.widgets.edit_chip.tree_model_chips import QTreeModel_Chips


class _FakeLogger:
    def debug(self, *_a, **_kw):
        pass

    def info(self, *_a, **_kw):
        pass


class _FakeGui:
    def __init__(self, design):
        self.logger = _FakeLogger()
        self.design = design


def build():
    design = designs.DesignPlanar()
    gui = _FakeGui(design)
    view = QTreeView_Base(None)
    model = QTreeModel_Chips(parent=None, gui=gui, view=view)
    view.setModel(model)
    design.chips["extra"] = {"layer_start": "0", "layer_end": "1"}
    model._row_count = -1
    return view, model


# Destroy the view out from under the model; the polling tick must neither
# raise nor touch the dead view, and must stop polling.
view, model = build()
assert model.timer.isActive()
shiboken6.delete(view)
assert not shiboken6.isValid(view)
model.auto_refresh()
assert not model.timer.isActive()
print("MARKER_DESTROYED_VIEW_OK", flush=True)
model.timer.stop()

# A live view must not false-positive the guard.
view, model = build()
model.auto_refresh()
assert model.timer.isActive()
print("MARKER_LIVE_VIEW_OK", flush=True)
model.timer.stop()
print("MARKER_DONE", flush=True)
"""


def test_tree_model_view_teardown_in_subprocess():
    env = dict(os.environ)
    env.pop("QISKIT_METAL_HEADLESS", None)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    proc = subprocess.run(
        [sys.executable, "-X", "faulthandler", "-c", _SNIPPET],
        capture_output=True,
        text=True,
        timeout=240,
        env=env,
    )
    for marker in ("MARKER_DESTROYED_VIEW_OK", "MARKER_LIVE_VIEW_OK", "MARKER_DONE"):
        assert marker in proc.stdout, (
            f"tree-model teardown contract not proven: {marker} missing "
            f"(rc={proc.returncode}).\nstdout:\n{proc.stdout}\n"
            f"stderr tail:\n{crash_excerpt(proc.stderr)}"
        )
    assert "already deleted" not in proc.stdout + proc.stderr
    if proc.returncode != 0:
        print(
            "NOTE: child proved both teardown scenarios (all markers) but "
            f"exited {proc.returncode} during interpreter teardown."
        )
