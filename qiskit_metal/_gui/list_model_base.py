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

from PyQt5 import Qt, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel

class DynamicList(QStandardItemModel):

    __refreshTime = 5000 # 10 s refresh time

    def __init__(self, orig_design: 'QDesign'):
        super().__init__()
        self._design = orig_design
        self.populate_list()

    @property
    def datasrc(self):
        """Return the data source."""
        return self._design

    def update_src(self, new_design: 'QDesign'):
        """
        Change the data source to a new one.
        Note that there is no need to explicitly update the elements
        in the model here because of the background timer.

        Args:
            new_list (list): The new data source
        """
        self._design = new_design

    def populate_list(self):
        """
        Clear model and (re)populate it with the latest elements.
        """
        # TODO: Generalize this to beyond components.
        self.clear()
        for element in self.datasrc.components:
            item = QStandardItem(element)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setFlags(Qt.ItemIsUserCheckable| Qt.ItemIsEnabled)
            self.appendRow(item)

    def select_all(self):
        """Select everything in the list."""
        for i in range(self.rowCount()):
            self.item(i).setCheckState(QtCore.Qt.Checked)

    def deselect_all(self):
        """Deselect everything in the list."""
        for i in range(self.rowCount()):
            self.item(i).setCheckState(QtCore.Qt.Unchecked)
    
    def get_checked(self):
        """Get list of all selected items."""
        selected_items = []
        for i in range(self.rowCount()):
            entry = self.item(i)
            if entry.checkState() == QtCore.Qt.Checked:
                selected_items.append(entry.text())
        return selected_items
