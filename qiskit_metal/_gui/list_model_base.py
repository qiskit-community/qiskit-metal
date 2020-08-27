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
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QListView
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QTimer, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont

class DynamicList(QStandardItemModel):

    __refreshTime = 5000 # 10 s refresh time

    def __init__(self, orig_design: 'QDesign'):
        super().__init__()
        self._design = orig_design
        self.populate_list()
        self._start_timer()

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
    
    def _start_timer(self):
        """
        Start and continuously refresh timer in the background to 
        periodically and dynamically update elements in the model
        to match those in orig_list.
        """
        self.timer = QTimer(self)
        self.timer.start(self.__refreshTime)
        self.timer.timeout.connect(self.populate_list)
    
    def populate_list(self):
        """
        Clear model and (re)populate it with the latest elements.
        """
        self.clear()
        for element in self.datasrc.components:
            item = QStandardItem(element)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Checked)
            item.setFlags(Qt.ItemIsUserCheckable| Qt.ItemIsEnabled)
            self.appendRow(item)
