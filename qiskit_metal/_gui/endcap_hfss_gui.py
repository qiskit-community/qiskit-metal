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

from typing import Tuple

from PySide6.QtWidgets import (QComboBox, QTableWidgetItem, QAbstractItemView,
                               QMainWindow, QLineEdit)

from .endcap_hfss_ui import Ui_mainWindow


class EndcapHFSSWidget(QMainWindow):
    """Upon selecting components to export, there may or may not be unconnected
    pins.

    This widget lets the user decide whether they want those pins to be
    open or shorted.
    """

    def __init__(self,
                 parent: 'QMainWindow',
                 gui: 'MetalGUI',
                 components_to_render: list = None,
                 soln_type: str = 'Eigenmode'):
        """Get access to design, which has the components. Then set up the
        model and view.

        Args:
            parent (QMainWindow): The parent window
            gui (MetalGUI): The metal GUI
            components_to_render (list): A list of components to render to Ansys HFSS
            soln_type (str): Type of solution, either Eigenmode or Driven Modal
        """
        super().__init__(parent)

        # Access design and Metal GUI:
        self._gui = gui

        # Use UI template from Qt Designer:
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)

        # Set up table widget for endcap list:
        self.table = self.ui.tableWidget
        self.components_to_render = components_to_render
        open_pins, shorted_pins = self.get_unconnected_pins(
            self.components_to_render)

        self.soln_type = soln_type
        if self.soln_type == 'Eigenmode':
            self.table.setColumnCount(
                2)  # Columns for pin name and endcap status
            endcap_options = ['Open', 'Shorted']
        elif self.soln_type == 'Driven Modal':
            self.table.setColumnCount(
                3)  # Columns for pin name, endcap status, and impedance in Ohms
            endcap_options = ['Open', 'Shorted', 'Port']
        self.pin_names = sorted(list(open_pins) +
                                list(shorted_pins))  # sort alphabetically

        self.table.setRowCount(len(self.pin_names))

        for idx in range(len(self.pin_names)):
            pin_name = QTableWidgetItem(', '.join(self.pin_names[idx]))
            self.table.setItem(idx, 0, pin_name)  # pin name for first column
            endcap_combo = QComboBox()
            endcap_combo.addItems(endcap_options)
            self.table.setCellWidget(idx, 1,
                                     endcap_combo)  # combobox for second column
            endcap_combo.setCurrentIndex(
                int(self.pin_names[idx] not in
                    open_pins))  # default endcap type
            if self.soln_type == 'Driven Modal':
                impedance_value = QLineEdit()
                impedance_value.setText('50')
                self.table.setCellWidget(idx, 2, impedance_value)

        self.table.verticalHeader().setVisible(False)
        if self.soln_type == 'Eigenmode':
            self.table.setHorizontalHeaderLabels(['QComp, Pin', 'Endcap Type'])
        elif self.soln_type == 'Driven Modal':
            self.table.setHorizontalHeaderLabels(
                ['QComp, Pin', 'Endcap Type', 'Impedance (Ohms)'])
        self.table.horizontalHeader().setStretchLastSection(True)

    @property
    def design(self):
        """Returns the design."""
        return self._gui.design

    def get_unconnected_pins(self,
                             components_to_render: list = None
                            ) -> Tuple[set, set]:
        """Given a list of components to render, obtain 2 sets: open_set and
        short_set. Each contains pins belonging to components in
        components_to_render, but with the following difference. Open_set
        contains all pins that were connected in the original Metal design but
        whose counterparts are not in components_to_render, whereas short_set
        contains all pins that were unconnected in the original Metal design to
        begin with. These are the default endcap settings for all pins in
        components_to_render.

        Args:
            components_to_render (list, optional): List of components to render.  Defaults to None.

        Returns:
            Tuple[set, set]: 2 sets of pins to be open or shorted by default
        """
        qcomp_set = set(components_to_render)

        open_set = set()
        short_set = set()

        for qcomp in components_to_render:
            for pin in self.design.components[qcomp].pins:
                qcomp_id = self.design.components[qcomp].id
                qcomp_net_id = self.design.components[qcomp].pins[pin].net_id
                if qcomp_net_id == 0:  # not connected in design
                    short_set.add((qcomp, pin))
                else:  # originally connected in design
                    table = self.design.net_info
                    reduced_table = table[(table['net_id'] == qcomp_net_id) &
                                          (table['component_id'] != qcomp_id)]
                    other_qcomp = self.design._components[
                        reduced_table.iloc[0].component_id].name
                    if other_qcomp not in qcomp_set:  # counterpart not rendered -> make open
                        open_set.add((qcomp, pin))

        return open_set, short_set

    def render_everything(self):
        """Render all selected components from previous window and add open
        endcaps and/or ports where appropriate."""
        add_open_pins, port_list = [], []
        for row in range(len(self.pin_names)):
            if self.table.cellWidget(row, 1).currentText() == 'Open':
                s = self.table.item(row, 0).text()
                add_open_pins.append(tuple(s.split(', ')))
            elif self.table.cellWidget(row, 1).currentText() == 'Port':
                s = self.table.item(row, 0).text()
                impedance = self.table.cellWidget(row, 2).text()
                port_list.append(tuple(s.split(', ') + [str(impedance)]))
        hfss_renderer = self.design.renderers.hfss
        hfss_renderer.connect_ansys()
        hfss_renderer.render_design(self.components_to_render, add_open_pins,
                                    port_list)
        self.close()
