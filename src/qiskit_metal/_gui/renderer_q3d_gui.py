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

from PySide6.QtWidgets import (QAbstractItemView, QMainWindow, QMessageBox)

from qiskit_metal._gui.list_model_base import DynamicList
from qiskit_metal._gui.renderer_q3d_model import RendererQ3D_Model
from qiskit_metal._gui.renderer_q3d_ui import Ui_MainWindow
from qiskit_metal._gui.endcap_q3d_gui import EndcapQ3DWidget


class RendererQ3DWidget(QMainWindow):
    """Contains methods associated with Ansys Q3D Renderer button."""

    def __init__(self, parent: 'QMainWindow', gui: 'MetalGUI'):
        """Get access to design, which has the components. Then set up the
        model and view.

        Args:
            parent (QMainWindow): The parent window
            gui (MetalGUI): The metal GUI
        """
        super().__init__(parent)

        # Access design and Metal GUI:
        self._gui = gui

        # Use UI template from Qt Designer:
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Set up models for component list and options tree:
        self.listView = self.ui.listView
        self.list_model = DynamicList(self.design)
        self.listView.setModel(self.list_model)

        self.tree_model = RendererQ3D_Model(self, gui, self.ui.treeView)
        self.ui.treeView.setModel(self.tree_model)
        self.ui.treeView.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.ui.treeView.setHorizontalScrollMode(
            QAbstractItemView.ScrollPerPixel)

    def set_design(self, new_design: 'QDesign'):
        """Swaps out reference to design, which changes the reference to the
        dictionary.

        Args:
            new_design (QDesign): The design
        """
        self.list_model.update_src(self.design)

    @property
    def design(self):
        """Returns the design."""
        return self._gui.design

    def refresh(self):
        """Refreshes list of components."""
        self.list_model.populate_list()

    def select_all(self):
        """Marks all components for export."""
        self.list_model.select_all()

    def deselect_all(self):
        """Empties list of components to export."""
        self.list_model.deselect_all()

    def get_checked(self) -> list:
        """Gets list of all selected components to export.

        Returns:
            list: List of selected components
        """
        return self.list_model.get_checked()

    def choose_checked_components(self):
        """Sends checked components to the next window that allows the user to
        select which unconnected pins are to be open."""
        components_to_render = self.get_checked()
        if components_to_render:
            self.endcap_q3d_window = EndcapQ3DWidget(self, self._gui,
                                                     components_to_render)
            self.endcap_q3d_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Error",
                                "Please select at least one component.")
