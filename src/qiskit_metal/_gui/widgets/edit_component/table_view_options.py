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
from PySide6.QtWidgets import QTableView, QAbstractItemView

from qiskit_metal._gui.widgets.bases.QWidget_PlaceholderText import QWidget_PlaceholderText

if TYPE_CHECKING:
    from ...main_window import MetalGUI


class QTableView_Options(QTableView, QWidget_PlaceholderText):
    """The class for QTableView_Options.

    This class inhertis the `QTableView` and `QWidget_PlaceholderText`
    classes.
    """

    def __init__(self, parent: QtWidgets.QWidget):
        """
        Args:
            parent (QtWidgets.QWidget): parent widget
        """
        QTableView.__init__(self, parent)
        QWidget_PlaceholderText.__init__(self, "Select a QComponent to edit"\
            "\n\nfrom the QComponents window")
        QTimer.singleShot(
            200,
            self.style_me)  # not sure whu the ui isnt unpdating these here.

    def style_me(self):
        """Style the widget."""
        # Also can do in the ui file, but doesn't always transalte for me for some reason
        self.horizontalHeader().show()
        self.verticalHeader().hide()
        self.setAutoScroll(False)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

    #TODO: Maybe move to base class of utilty, along with the show template message
    def autoresize_columns(self, max_width: int = 200):
        """Rezie columsn to contents with maximim.

        Args:
            max (int): automatically resize the columns to the given size.  Defaults to 200.
        """
        self.resizeColumnsToContents()
        columns = self.model().columnCount()
        for i in range(columns):
            width = self.columnWidth(i)
            if width > max_width:
                self.setColumnWidth(i, max_width)
