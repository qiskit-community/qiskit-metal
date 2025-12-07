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

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtCore import QPoint, QModelIndex, QTimer
from PySide6.QtWidgets import QInputDialog, QLineEdit, QTableView, QMenu, QMessageBox
from PySide6.QtWidgets import QAbstractItemView


class RightClickView(QTableView):
    """Standard QTableView with drop-down context menu upon right-clicking.
    Menu allows for row deletion and renaming a cell.

    This class extends the `QTableView` class.

    Access:
        gui.variables_window.ui.tableView
    """

    def __init__(self, parent):
        """Provide access to GUI QMainWindow via parent."""
        super().__init__(parent)
        self.gui = parent.parent()  # this is not the main gui

        QTimer.singleShot(
            200,
            self.style_me)  # not sure whu the ui isnt unpdating these here.

    def style_me(self):
        """Style this widget."""
        # Also can do in the ui file, but doesn't always transalte for me for some reason
        self.horizontalHeader().show()
        self.verticalHeader().hide()
        self.setAutoScroll(False)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

    def contextMenuEvent(self, event: QContextMenuEvent):
        """Create options for drop-down context menu.

        Args:
            event (QContextMenuEvent): The event
        """
        self.right_click_menu = QMenu(self)
        self.right_click_menu._d = self.right_click_menu.addAction('Delete')
        self.right_click_menu._r = self.right_click_menu.addAction('Rename')
        row_name, index = self.getPosition(event.pos())
        self.right_click_menu._d.triggered.connect(
            lambda: self.deleteRow(row_name, index.row()))
        self.right_click_menu._r.triggered.connect(
            lambda: self.renameRow(row_name, index))
        self.right_click_menu.action = self.right_click_menu.exec_(
            self.mapToGlobal(event.pos()))

    def getPosition(self, clickedIndex: QPoint):
        """Obtain location of clicked cell in form of row name and number.

        Args:
            clickedIndex (QPoint): The QPoint of the click

        Returns:
            tuple: name, index
        """
        index = self.indexAt(clickedIndex)
        name = list(self.gui.model._data.keys())[index.row()]
        if index.isValid():
            return name, index
        return None, None

    def deleteRow(self, row_name: str, row_number: int):
        """Create message box to confirm row deletion.

        Args:
            row_name (str): Name of the row to delete
            row_number (int): Number of the row being deleted
        """
        if row_number > -1:
            choice = QMessageBox.question(
                self, '', f'Are you sure you want to delete {row_name}?',
                QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.Yes:
                model = self.model()
                model.removeRows(row_number)

    def renameRow(self, row_name: str, index: QModelIndex):
        """Create message box to confirm row renaming and new name.

        Args:
            row_name (str): Name of the row to rename
            index (QModelIndex): Index of the row to rename
        """
        if index.row() > -1:
            text, okPressed = QInputDialog.getText(self, 'Rename',
                                                   f'Rename {row_name} to:',
                                                   QLineEdit.Normal, '')
            if okPressed and (text != ''):
                model = self.model()
                model.setData(index, text)
