# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Ask Zlatko for help on this file"""
from .._handle_qt_messages import catch_exception_slot_pyqt
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QTableView, QInputDialog, QLineEdit
from PyQt5.QtWidgets import (QMenu, QMessageBox)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..main_window import MetalGUI
    from .components_model import ComponentsTableModel


class TableComponents(QTableView):
    """
    Desing components.

    Table model that shows the summary of the components of a design in a table
    with their names, classes, and modules

    Access:
        gui.ui.tableComponents
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.clicked.connect(self.viewClicked)

    @property
    def design(self):
        return self.model().design

    @property
    def logger(self):
        return self.model().logger

    @property
    def gui(self) -> 'MetalGUI':
        return self.model().gui

    # @catch_exception_slot_pyqt
    def contextMenuEvent(self, event):
        self._event = event  # debug

        self.menu = QMenu(self)
        self.menu._d = self.menu.addAction("Delete")
        self.menu._r = self.menu.addAction("Rename")

        self.menu._d.triggered.connect(lambda: self.do_menu_delete(event))
        self.menu._r.triggered.connect(lambda: self.do_menu_rename(event))

        self.menu._action = self.menu.exec_(self.mapToGlobal(event.pos()))

    def get_name_from_event(self, event):
        # get the selected row and column
        row = self.rowAt(event.pos().y())
        #col = self.columnAt(event.pos().x())

        model = self.model()
        index = model.index(row, 0)  # get the name
        name = model.data(index)
        return name, row

    # @catch_exception_slot_pyqt
    def do_menu_delete(self, event):
        """called when the user clicks the context menu delete"""
        name, row = self.get_name_from_event(event)

        if row > -1:
            ret = QMessageBox.question(self, '',
                                       f"Are you sure you want to delete component {name}",
                                       QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self._do_delete(name)

    def _do_delete(self, name: str):
        """do delte a component by name"""
        self.logger.info(f'Deleting {name}')
        self.design.delete_component(name)
        # replot
        self.gui.plot_win.replot()

    def do_menu_rename(self, event):
        """called when the user clicks the context menu rename"""
        name, row = self.get_name_from_event(event)

        if row > -1:
            text, okPressed = QInputDialog.getText(
                self, f"Rename component {name}", f"Rename {name} to:", QLineEdit.Normal, "")
            if okPressed and text != '':
                self.logger.info(f'Renaming {name} to {text}')
                self.design.rename_component(name, text)

    def viewClicked(self, clickedIndex : QtCore.QModelIndex):
        """Select a compoent and set it in the compoient widget when you left click.
        """
        if self.gui is None or not clickedIndex.isValid():
            return

        # get the component name
        #model = clickedIndex.model()  # type: ComponentsTableModel
        c=clickedIndex
        name = c.sibling(c.row(), 0).data()
        self.logger.info(f'Selected component {name}')
        self.gui.set_component(name)

