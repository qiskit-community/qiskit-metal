# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

'''
@date: 2020
@author: Dennis Wang
'''

from PyQt5 import QtCore
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QListView
from .renderer_gds_ui import Ui_MainWindow

class RendererGDSWidget(QMainWindow):
    """Contains methods associated with GDS Renderer button."""

    def __init__(self, design):
        """
        Get access to design, which has the components.
        Then set up the model and view.
        """
        super().__init__()

        # Access design:
        self._design = design

        # Use UI template from Qt Designer:
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Set up a simple model and list:
        self.model = QStandardItemModel()
        self.listView = self.ui.listView

        # Populate list:
        self.populate_list()
        self.listView.setModel(self.model)

    @property
    def design(self):
        """Returns the design."""
        return self._design
    
    def populate_list(self):
        """Fills in list with design components."""
        for component in self.design.components:
            item = QStandardItem(component)
            item.setCheckable(True)
            # Export all components by default.
            item.setCheckState(QtCore.Qt.Checked)
            self.model.appendRow(item)

    def select_all(self):
        """Shortcut to mark all components for export."""
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Checked)
    
    def deselect_all(self):
        """Shortcut to empty list of components for export."""
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Unchecked)

    def get_checked(self):
        """Gets list of all selected components to export."""
        components_to_export = []
        for i in range(self.model.rowCount()):
            component = self.model.item(i)
            if component.checkState() == QtCore.Qt.Checked:
                components_to_export.append(component.text())
        return components_to_export
    
    def browse_folders(self):
        """Browses available folders in system."""
        destination_folder = QFileDialog.getExistingDirectory()
        self.ui.lineEdit.setText(destination_folder)
    
    def export_file(self):
        """Exports all selected components in the file."""
        filename = self.ui.lineEdit.text()
        components_to_export = self.get_checked()
        a_gds = self.design.renderers.gds
        if filename and components_to_export:
            a_gds.export_to_gds(filename, highlight_qcomponents=components_to_export)
        self.close()
