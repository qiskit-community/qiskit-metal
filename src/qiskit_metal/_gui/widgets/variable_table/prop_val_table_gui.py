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

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QDialog, QMainWindow

from qiskit_metal._gui.widgets.variable_table.add_delete_table_ui import Ui_MainWindow
from qiskit_metal._gui.widgets.variable_table.dialog_popup_ui import Ui_Dialog
from qiskit_metal._gui.widgets.variable_table.prop_val_table_model import PropValTable


class PropertyTableWidget(QMainWindow):
    """GUI for variables table with 3 columns: Property, Value, Number.

    Extends the `QMainWindow` class.
    """

    def __init__(self, parent, design=None, gui=None):
        """
        Args:
            parent (QMainWindowExtension): Parent window
            design (QDesign): design.  Defaults to None.
            gui (MetalGUI): the GUI.  Defaults to None.
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
        """Swap out reference to design, which changes the reference to the
        dictionary.

        Args:
            design (QDesign): The design
        """
        self._design = design
        self.model.set_design(design)

    @property
    def design(self):
        """Returns the design."""
        return self._design

    @property
    def _data(self) -> dict:
        """Returns the variables."""
        if self._design:
            return self._design.variables

    def addRow(self):
        """Add a new row."""
        db = QDialog(self)
        dialog = Ui_Dialog()
        dialog.setupUi(db)
        db.exec()
        key = dialog.key_box.text()
        val = dialog.value_box.text()
        if key and val:
            self.model.add_row(key, val)

    def deleteRow(self):
        """Delete all rows corresponding to selected cells."""
        rowidxlst = list(set(elt.row() for elt in self.table.selectedIndexes()))
        for idx in sorted(rowidxlst, reverse=True):
            self.model.removeRows(idx, 1, QModelIndex())
