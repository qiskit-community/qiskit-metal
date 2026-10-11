# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""``single_shot`` timers must disappear once they have fired.

A fired-but-undeleted single-shot timer stays a child of its parent, where
``QMainWindowExtension.showEvent`` (which restarts every inactive ``QTimer``
it finds under the window) replays it on every show/un-minimize -- re-running
old callbacks such as the focus-stealing ``_raise``. Child process with
printed markers, per the full-GUI test convention.
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
from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])
from qiskit_metal._gui.utility._toolbox_qt import single_shot

parent = QObject()
calls = []
single_shot(parent, 0, lambda: calls.append(1))
for _ in range(20):
    app.processEvents()
app.sendPostedEvents(None, QEvent.DeferredDelete)
app.processEvents()
assert calls == [1], calls
print("MARKER_FIRED_ONCE", flush=True)
assert parent.findChildren(QTimer) == [], parent.findChildren(QTimer)
print("MARKER_TIMER_GONE", flush=True)
print("MARKER_DONE", flush=True)
"""


def test_single_shot_timer_is_deleted_after_firing():
    env = dict(os.environ)
    env.pop("QISKIT_METAL_HEADLESS", None)
    proc = subprocess.run(
        [sys.executable, "-X", "faulthandler", "-c", _SNIPPET],
        capture_output=True,
        text=True,
        timeout=240,
        env=env,
    )
    for marker in ("MARKER_FIRED_ONCE", "MARKER_TIMER_GONE", "MARKER_DONE"):
        assert marker in proc.stdout, (
            f"single_shot cleanup not proven: {marker} missing "
            f"(rc={proc.returncode}).\nstdout:\n{proc.stdout}\n"
            f"stderr tail:\n{crash_excerpt(proc.stderr)}"
        )
