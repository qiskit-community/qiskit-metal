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

"""Status-bar widgets have to be *visible*, not merely populated.

The window sets a standing status message ("Qiskit Metal: Quantum Creator"),
and Qt hides every **normal** status-bar widget for as long as a message is
displayed. Both readouts -- the hover coordinates and the selection hint --
were added with ``addWidget`` and so were constructed, updated, and never
seen. ``addPermanentWidget`` is exempt from that.

Asserting on ``text()`` alone cannot catch this, which is exactly how it was
missed the first time: the labels held the right strings throughout. These
tests assert visibility.

Runs in a subprocess because it needs a real MetalGUI with its own
QApplication and status bar, and constructing a second one in-process would
inherit the first's.
"""

import os
import subprocess
import sys

import pytest

from ._crash_output import crash_excerpt

pytest.importorskip("PySide6")


PROBE = """
from types import SimpleNamespace

from qiskit_metal import designs, MetalGUI
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from PySide6.QtWidgets import QApplication

design = designs.DesignPlanar()
TransmonPocket(design, "Q1", options=dict(pos_x="-1mm", pos_y="0mm"))

gui = MetalGUI(design)
gui.main_window.show()
QApplication.processEvents()

gui.edit_component("Q1")
gui.canvas.panzoom._on_mouse_motion(
    SimpleNamespace(xdata=-1.0, ydata=0.25, button=None, name="motion_notify_event")
)
QApplication.processEvents()

print("MESSAGE_SET:%s" % bool(gui.main_window.statusBar().currentMessage()))
print("SELECTION_VISIBLE:%s" % gui.statusbar_selection.isVisible())
print("COORDS_VISIBLE:%s" % gui.statusbar_label.isVisible())
print("SELECTION_TEXT:%s" % gui.statusbar_selection.text())
print("MARKER_OK")
"""


@pytest.fixture(name="probe_output", scope="module")
def probe_output_fixture():
    """Build a GUI in a subprocess and return its reported status-bar state."""
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QISKIT_METAL_HEADLESS"] = "1"
    env["QISKIT_METAL_RESET_UI_SETTINGS"] = "1"

    completed = subprocess.run(
        [sys.executable, "-c", PROBE],
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
        check=False,
    )
    if "MARKER_OK" not in completed.stdout:
        pytest.skip(
            "GUI could not be constructed in this environment:\n"
            f"{completed.stdout}\n{crash_excerpt(completed.stderr)}"
        )
    return completed.stdout


def field(output, key):
    """Pull one ``KEY:value`` line out of the probe output."""
    for line in output.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1]
    return None


class TestStatusBarReadoutsAreVisible:
    """The regression: populated but hidden."""

    def test_a_standing_message_is_present(self, probe_output):
        """Establishes the precondition -- without it the bug cannot occur."""
        assert field(probe_output, "MESSAGE_SET") == "True"

    def test_selection_hint_is_visible(self, probe_output):
        """Hidden, the hint cannot tell anyone the arrow keys work."""
        assert field(probe_output, "SELECTION_VISIBLE") == "True"

    def test_coordinate_readout_is_visible(self, probe_output):
        """Same failure mode; it was added the same way."""
        assert field(probe_output, "COORDS_VISIBLE") == "True"

    def test_hint_names_the_selection_and_the_keys(self, probe_output):
        """Content check, now that it can actually be read."""
        text = field(probe_output, "SELECTION_TEXT")
        assert "Q1" in text
        assert "arrow keys" in text
