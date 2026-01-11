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
"""Handles editing a QComponent."""

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QTreeView, QAbstractItemView

from qiskit_metal._gui.widgets.bases.QWidget_PlaceholderText import QWidget_PlaceholderText

if TYPE_CHECKING:
    from ...main_window import MetalGUI


class QTreeView_Options(QTreeView, QWidget_PlaceholderText):
    """Handles editing a QComponent.

    This class extends the `QTreeView` and `QWidget_PlaceholderText`
    classes.
    """

    def __init__(self, parent: QtWidgets.QWidget):
        """
        Args:
            parent (QtWidgets.QWidget): The parent widget
        """
        QTreeView.__init__(self, parent)
        QWidget_PlaceholderText.__init__(self, "Select a QComponent to edit"\
                    "\n\nfrom the QComponents window")
        # not sure whu the ui isn't updating these here.
        QTimer.singleShot(200, self.style_me)
        self.expanded.connect(self.resize_on_expand)

    def style_me(self):
        """Style this widget"""
        # Also can do in the ui file, but doesn't always translate for some reason
        self.header().show()
        self.setAutoScroll(False)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.setStyleSheet("""
QTreeView::branch {  border-image: url(none.png); }
        """)

    # TODO: Maybe move to base class of utility, along with the show template message
    def autoresize_columns(self, max_width: int = 200):
        """Resize columns to contents with maximum

        Args:
            max (int): Maximum window width.. Defaults to 200.
        """
        # For TreeView: resizeColumnToContents
        # For TableView: resizeColumnsToContents

        columns = self.model().columnCount(None)
        for i in range(columns):
            self.resizeColumnToContents(i)
            width = self.columnWidth(i)
            if width > max_width:
                self.setColumnWidth(i, max_width)

    def resize_on_expand(self):
        """Resize when exposed."""
        self.resizeColumnToContents(0)
