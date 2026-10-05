# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Table-model poll timers must stop once their view is destroyed.

The all-components, pins and variables table models each poll on a
``QTimer`` parented to the *model*. If the view's C++ object is destroyed
first, the next tick calls into a dead object: a Python ``RuntimeError:
... QLabel already deleted`` at best, a native use-after-free at worst
(``docs/architecture/gui_crash_defenses.md``). Seen after a test run had
already passed, via ``tests/test_gui_logger_lifecycle.py``. Run in a child
process with printed markers so a native loss cannot take down pytest.
"""

import os
import subprocess
import sys

import pytest

from tests._crash_output import crash_excerpt

pytest.importorskip("PySide6")

_SNIPPET = """
import faulthandler
faulthandler.enable()
from types import SimpleNamespace

import shiboken6
from PySide6.QtWidgets import QApplication, QTableView

app = QApplication.instance() or QApplication([])

from qiskit_metal._gui.widgets.all_components.table_model_all_components import (
    QTableModel_AllComponents,
)
from qiskit_metal._gui.widgets.pins.table_model_pins import QTableModel_Pins
from qiskit_metal._gui.widgets.variable_table.prop_val_table_model import (
    PropValTable,
)

gui = SimpleNamespace(design=None)


def check(name, make, timer_attr, poll):
    view = QTableView()
    model = make(view)
    timer = getattr(model, timer_attr)
    assert timer.isActive(), name
    shiboken6.delete(view)
    assert not shiboken6.isValid(view)
    getattr(model, poll)()  # must neither raise nor touch the dead view
    assert not timer.isActive(), name
    timer.stop()
    print("MARKER_" + name, flush=True)


check(
    "ALL_COMPONENTS",
    lambda v: QTableModel_AllComponents(gui, None, tableView=v),
    "_timer",
    "refresh_auto",
)
check(
    "PINS",
    lambda v: QTableModel_Pins(gui, None, tableView=v),
    "_timer",
    "refresh_auto",
)
check(
    "VARIABLES",
    lambda v: PropValTable(None, gui, v),
    "timer",
    "auto_refresh",
)
print("MARKER_DONE", flush=True)
"""


def test_table_model_poll_timers_stop_when_view_destroyed():
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
    for marker in (
        "MARKER_ALL_COMPONENTS",
        "MARKER_PINS",
        "MARKER_VARIABLES",
        "MARKER_DONE",
    ):
        assert marker in proc.stdout, (
            f"poll-guard contract not proven: {marker} missing "
            f"(rc={proc.returncode}).\nstdout:\n{proc.stdout}\n"
            f"stderr tail:\n{crash_excerpt(proc.stderr)}"
        )
    assert "already deleted" not in proc.stdout + proc.stderr
