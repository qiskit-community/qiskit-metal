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

    """MVC class
    See https://doc.qt.io/qt-5/qabstracttablemodel.html

    Can be accessed with
        model = gui.ui.tableComponents.model()
    """
    __timer_interval = 500 # ms

    def __init__(self, design, logger, parent=None):
        super().__init__(parent=parent)
        self.design = None
        self.logger = logger
        self.columns = ['Name', 'Class', 'Module']
        #self.

        self.set_design(design)

        self._create_timer()

    def _create_timer(self):
        """
        Refresh the model number of rows, etc. there must be a smarter way?
        """
        self._timer = QtCore.QTimer(self)
        self._timer.start(self.__timer_interval)
        self._timer.timeout.connect(self.refresh)

    def refresh(self):
        """Update row count etc.
        """
        self.modelReset.emit() # is there a more efficient command?

    def set_design(self, design):
        self.design = design
        # TODO:

    def rowCount(self, parent=None):  # =QtCore.QModelIndex()):
        if self.design:  # should we jsut enforce this
            return int(len(self.design.components))
        else:
            return 0

    def columnCount(self, parent=None):  # =QtCore.QModelIndex()):
        return len(self.columns)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """ Set the headers to be displayed. """

        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            if section < len(self.columns):
                return self.columns[section]

    def flags(self, index):
        """ Set the item flags at the given index. Seems like we're
            implementing this function just to see how it's done, as we
            manually adjust each tableView to have NoEditTriggers.
        """
        # https://doc.qt.io/qt-5/qt.html#ItemFlag-enum

        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        return QtCore.Qt.ItemFlags(QAbstractTableModel.flags(self, index) |
                            QtCore.Qt.ItemIsSelectable) # ItemIsEditable

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """ Depending on the index and role given, return data. If not
            returning data, return None (PySide equivalent of QT's
            "invalid QVariant").
        """

        if not index.isValid():
            return
        # if not 0 <= index.row() < self.rowCount():
        #    return None

        if not self.design:
            return

        if role == QtCore.Qt.DisplayRole:

            row = index.row()
            component_name = list(self.design.components.keys())[row]

            if index.column() == 0:
                return component_name

            elif index.column() == 1:
                return self.design.components[component_name].__class__.__name__

            elif index.column() == 2:
                return self.design.components[component_name].__class__.__module__
