# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# Zlatko Minev

from PyQt5.QtCore import QAbstractTableModel
from PyQt5 import Qt, QtCore
import numpy as np

class ComponentsTableModel(QAbstractTableModel):

    def __init__(self, design, parent=None):
        super().__init__(parent=parent)
        self.design = None
        self.columns = ['Name', 'Type']

        self.set_design(design)

    def set_design(self, design):
        self.design = design
        #TODO:

    def rowCount(self, parent=None):#=QtCore.QModelIndex()):
        if self.design:
            pass
        else:
            return 15

    def columnCount(self, parent):#=QtCore.QModelIndex()):
        return len(self.columns)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """ Set the headers to be displayed. """

        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            if section<len(self.columns):
                return self.columns[section]

    def flags(self, index):
        """ Set the item flags at the given index. Seems like we're
            implementing this function just to see how it's done, as we
            manually adjust each tableView to have NoEditTriggers.
        """

        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        return QtCore.Qt.ItemFlags(QAbstractTableModel.flags(self, index) |
                            QtCore.Qt.ItemIsEditable)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """ Depending on the index and role given, return data. If not
            returning data, return None (PySide equivalent of QT's
            "invalid QVariant").
        """
        if not index.isValid():
            return None
        #if not 0 <= index.row() < self.rowCount():
        #    return None

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return f'component_{index.row()}'
            elif index.column() == 1:
                aa_milne_arr = ['qubit', 'cpw', 'interconnect', 'bump']
                return str(np.random.choice(aa_milne_arr, 1, p=[0.5, 0.1, 0.1, 0.3])[0])