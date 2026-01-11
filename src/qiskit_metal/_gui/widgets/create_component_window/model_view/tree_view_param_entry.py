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
"""
Tree view for Param Entry Window
"""

from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QTreeView


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

        # not sure whu the ui isn't updating these here.
        self.expanded.connect(self.resize_on_expand)

    def style_me(self):
        """Set style"""
        self.setStyleSheet("""
QTreeView::branch {  border-image: url(none.png); }
        """)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """ Overrides inherited mousePressEvent to allow user to clear any selections
        by clicking off the displayed tree. Then calls the inherited mousePressEvent"""
        myindex = self.indexAt(event.pos())
        if myindex.row() == -1:
            self.clearSelection()
            self.setCurrentIndex(QModelIndex())
        super().mousePressEvent(event)

    def resize_on_expand(self):
        """Resize when exposed"""
        self.resizeColumnToContents(0)
