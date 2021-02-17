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

@author: Grace Harper
@date: 2021
"""

import sys, os
from PySide2.QtWidgets import QApplication, QMainWindow, QFileSystemModel, QTabWidget, QWidget, QTreeView
from PySide2.QtCore import QModelIndex, QDir
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...main_window import MetalGUI


class LibraryView(QTreeView):
    """
    This is just a handler (container) for the UI; it a child object of the main gui.

    This class extends the `QTabWidget` class.

    PySide2 Signal / Slots Extensions:
        The UI can call up to this class to execute button clicks for instance
        Extensions in qt designer on signals/slots are linked to this class

    **Access:**
        gui.component_window
    """

    def __init__(self, parent: QWidget):
        """
        Args:
            parent (QtWidgets.QWidget): the widget
        """
        QTreeView.__init__(self, parent)
        self.set_up_connections()

    def set_up_connections(self):
        print("lol")

    # TODO: (Duplicate code from tree_view_options)
    #  Maybe move to base class of utility, along with the show template message
    def autoresize_columns(self, max_width: int = 200):
        """Resize columns to contents with maximum

        Args:
            max (int): Maximum window width (Default: 200)
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
        """Resize when exposed"""
        self.resizeColumnToContents(0)
