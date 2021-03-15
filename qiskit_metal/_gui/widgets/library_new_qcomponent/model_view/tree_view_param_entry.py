# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Handles editing a QComponent

@author: Zlatko Minev, Dennis Wang
@date: 2020
"""

from typing import TYPE_CHECKING

from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import QTreeView, QAbstractItemView
from PySide2.QtCore import QAbstractTableModel, QModelIndex

from ...bases.QWidget_PlaceholderText import QWidget_PlaceholderText


class TreeViewParamEntry(QTreeView):
    """Handles editing a QComponent

    This class extends the `QTreeView` and `QWidget_PlaceholderText` classes
    """

    def __init__(self, parent: QtWidgets.QWidget):
        """
        Args:
            parent (QtWidgets.QWidget): the widget
        """
        QTreeView.__init__(self, parent)

        # not sure whu the ui isnt unpdating these here.
        self.expanded.connect(self.resize_on_expand)

    def style_me(self):
        self.setStyleSheet("""
QTreeView::branch {  border-image: url(none.png); }
        """)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        myindex = self.indexAt(event.pos())
        print("pos: ", event.pos())
        print("INDEX: ", myindex)
        if (myindex.row() == -1):
            self.clearSelection()
            self.setCurrentIndex(QModelIndex())
            print("taylow", self.currentIndex())
        super().mousePressEvent(event)

    def resize_on_expand(self):
        """Resize when exposed"""
        self.resizeColumnToContents(0)