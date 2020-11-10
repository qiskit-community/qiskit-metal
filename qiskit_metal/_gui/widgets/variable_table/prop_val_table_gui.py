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

from .dialog_popup import Ui_Dialog
from .add_delete_table import Ui_MainWindow
from .prop_val_table_model import PropValTable
from .right_click_table_view import RightClickView
from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtGui import QFont
from PySide2.QtCore import QModelIndex
from PySide2.QtWidgets import QMainWindow, QTableView, QDialog


class PropertyTableWidget(QMainWindow):
    """
    GUI for variables table with 3 columns: Property, Value, Number

    Extends the `QMainWindow` class
    """
    def __init__(self, parent, design=None, gui=None):
        """
        Args:
            parent (QMainWindowExtension): Parent window
            design (QDesign): design (Default: None)
            gui (MetalGUI): the GUI (Default: None)
        """
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #
        self._design = design

        # Table View:
        self.table = self.ui.tableView
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setVisible(True)
        self.table.verticalHeader().setVisible(True)

        # Table Model:
        self.model = PropValTable(design, gui, self.table)
        self.table.setModel(self.model)

        # Display:
        self.show()

    def set_design(self, design):
        """Swap out reference to design, which changes the reference to the dictionary.

        Args:
            design (QDesign): The design
        """
        self._design = design
        self.model.set_design(design)

    @property
    def design(self):
        """Returns the design"""
        return self._design

    @property
    def _data(self) -> dict:
        """Returns the variables"""
        if self._design:
            return self._design.variables

    def addRow(self):
        """
        Add new row.
        """
        db = QDialog(self)
        dialog = Ui_Dialog()
        dialog.setupUi(db)
        db.exec()
        key = dialog.key_box.text()
        val = dialog.value_box.text()
        if key and val:
            self.model.add_row(key, val)

    def deleteRow(self):
        """
        Delete all rows corresponding to selected cells.
        """
        rowidxlst = list(set(elt.row()
                             for elt in self.table.selectedIndexes()))
        for idx in sorted(rowidxlst, reverse=True):
            self.model.removeRows(idx, 1, QModelIndex())