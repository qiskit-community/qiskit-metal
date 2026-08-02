# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Tests for :class:`QToolBarExpanding` -- the plot-window ribbon.

Until #1170 this widget expanded on hover and, worse, called
``time.sleep(0.25)`` from ``leaveEvent`` -- a blocking sleep on the Qt event
loop, so the whole window froze for a quarter second every time the pointer
left the toolbar. It shipped unnoticed because nothing exercised the widget.
These tests close that gap.

Runs under the ``offscreen`` platform when no display is present, so it is
covered by the plain GUI-extras job and not only the Xvfb ones. Skips
entirely on a lite install with no PySide6.
"""

import os
import sys
import time
import unittest

import pytest

pytest.importorskip("PySide6")


def _display_available() -> bool:
    if sys.platform.startswith("win") or sys.platform == "darwin":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


if not _display_available():
    # Must be set before the first QApplication is constructed. If another
    # test already built one, Qt ignores this and we reuse that instance.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QEnterEvent  # noqa: E402
from PySide6.QtWidgets import QApplication, QMainWindow  # noqa: E402

from qiskit_metal._gui.widgets.bases.expanding_toolbar import (  # noqa: E402
    QToolBarExpanding,
)

EXPANDED_STYLES = (Qt.ToolButtonTextUnderIcon, Qt.ToolButtonTextBesideIcon)


class TestExpandingToolbar(unittest.TestCase):
    """The ribbon expands only when asked, and never blocks the event loop."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.win = QMainWindow()
        self.toolbar = QToolBarExpanding(self.win)
        for label in ("Help", "Autoscale", "Zoom"):
            self.toolbar.addAction(label)
        self.win.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.win.show()
        self.app.processEvents()

    def tearDown(self):
        self.win.close()
        self.app.processEvents()

    def _expanded(self) -> bool:
        return self.toolbar.toolButtonStyle() in EXPANDED_STYLES

    def test_starts_contracted(self):
        self.assertFalse(self._expanded())

    def test_hover_does_not_expand(self):
        """The defect users reported: the ribbon opening on mouse-over."""
        pos = QPointF(1, 1)
        self.toolbar.enterEvent(QEnterEvent(pos, pos, pos))
        self.app.processEvents()
        self.assertFalse(self._expanded())

    def test_leave_does_not_block_the_event_loop(self):
        """Regression guard for the ``time.sleep(0.25)`` that used to live in
        ``leaveEvent``. The old code took ~251 ms here; anything near that
        means a blocking call is back on the GUI thread."""
        start = time.perf_counter()
        self.toolbar.leaveEvent(QEvent(QEvent.Leave))
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.assertLess(
            elapsed_ms,
            50,
            msg=f"leaveEvent blocked the event loop for {elapsed_ms:.1f} ms",
        )

    def test_toggle_button_expands_and_contracts(self):
        btn = self.toolbar._toggle_btn
        btn.click()
        self.app.processEvents()
        self.assertTrue(self._expanded())
        self.assertEqual(btn.arrowType(), Qt.UpArrow)

        btn.click()
        self.app.processEvents()
        self.assertFalse(self._expanded())
        self.assertEqual(btn.arrowType(), Qt.DownArrow)

    def test_programmatic_calls_keep_the_button_in_sync(self):
        """``expand_me`` / ``contract_me`` are public. If the button does not
        follow them, the next user click re-applies the current state and the
        toolbar appears stuck until clicked twice."""
        btn = self.toolbar._toggle_btn

        self.toolbar.expand_me()
        self.app.processEvents()
        self.assertTrue(btn.isChecked())

        # One click must now collapse it -- not expand it again.
        btn.click()
        self.app.processEvents()
        self.assertFalse(self._expanded())

        self.toolbar.contract_me()
        self.app.processEvents()
        self.assertFalse(btn.isChecked())

    def test_spacer_expands_along_the_toolbar_axis(self):
        """A toolbar dragged to a side dock runs vertically; the spacer that
        pins the toggle to the end has to expand along that axis instead."""
        from PySide6.QtWidgets import QSizePolicy

        spacer = self.toolbar._spacer
        self.assertEqual(spacer.sizePolicy().horizontalPolicy(), QSizePolicy.Expanding)

        self.win.addToolBar(Qt.LeftToolBarArea, self.toolbar)
        self.app.processEvents()
        self.assertEqual(self.toolbar.orientation(), Qt.Vertical)
        self.assertEqual(spacer.sizePolicy().verticalPolicy(), QSizePolicy.Expanding)

    def test_vertical_expand_does_not_raise(self):
        self.win.addToolBar(Qt.LeftToolBarArea, self.toolbar)
        self.app.processEvents()
        self.toolbar.expand_me()
        self.app.processEvents()
        self.assertTrue(self._expanded())
        self.assertEqual(self.toolbar._toggle_btn.arrowType(), Qt.LeftArrow)


if __name__ == "__main__":
    unittest.main(verbosity=2)
