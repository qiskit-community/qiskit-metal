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

from PySide2 import QtCore
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtGui import QFont

from .... import config


class PropValTable(QAbstractTableModel):
    """Design variables table model that shows variable name and dimension,
    both with and without units.

    Thie class extends the `QAbstractTableModel` class.

    Access:
        gui.variables_window.model
    """

    __refreshtime = 500  # 0.5 second refresh time

    def __init__(self, design=None, gui=None, view=None):
        """
        Args:
            design (QDesign): The QDesign.  Defaults to None.
            gui (MetalGUI): The MetalGUI.  Defaults to None.
            view (view): The view.  Defaults to None.
        """
        super().__init__()
        self._design = design
        self._gui = gui
        self._view = None
        # self._data = data
        self._rowCount = -1
        self._start_timer()

    def set_design(self, design):
        """Set the design.

        Args:
            design (QDesign): The design
        """
        self._design = design
        self.modelReset.emit()
        # refresh table or something if needed

    @property
    def design(self):
        """Returns the design."""
        return self._design

    @property
    def _data(self) -> dict:
        """Returns the data."""
        if self._design:
            return self._design.variables

    def _start_timer(self):
        """Start and continuously refresh timer in background to keep the total
        number of rows up to date."""
        self.timer = QtCore.QTimer(self)
        self.timer.start(self.__refreshtime)
        self.timer.timeout.connect(self.auto_refresh)

    def auto_refresh(self):
        """Do an automatic refresh."""
        newRowCount = self.rowCount(self)
        if self._rowCount != newRowCount:
            self.modelReset.emit()
            self._rowCount = newRowCount
            if self._view:
                self._view.resizeColumnsToContents()

    def rowCount(self, index: QModelIndex) -> int:
        """Count the number of rows.

        Args:
            index (QModelIndex): Not used

        Returns:
            int: Ihe number of rows
        """
        if self._design:
            return len(self._data)
        else:
            return 0

    def columnCount(self, index: QModelIndex) -> int:
        """Count the number of columns.

        Args:
            index (QModelIndex): Not used

        Returns:
            int: Yhe number of columns.  Always returns 3
        """
        return 3

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole):
        """Return data for corresponding index and role.

        Args:
            index (QModelIndex): The index of the data
            role (QT.ItemDataRole): The data role.  Defaults to Qt.DisplayRole.

        Returns:
            ojbect: The data
        """
        self._index = index
        row = index.row()
        column = index.column()

        if role == Qt.DisplayRole:
            if column == 0:
                return str(list(self._data.keys())[row])
            elif column == 1:
                return str(self._data[list(self._data.keys())[row]])
            elif column == 2:
                return str(
                    self.design.parse_value(self._data[list(
                        self._data.keys())[row]]))

        # double clicking
        elif role == Qt.EditRole:
            return self.data(index, Qt.DisplayRole)

        elif (role == Qt.FontRole) and (column == 0):
            font = QFont()
            font.setBold(True)
            return font

    def setData(self,
                index: QModelIndex,
                value: str,
                role: Qt.ItemDataRole = Qt.EditRole) -> bool:
        """Modify either key or value (Property or Value) of dictionary
        depending on what the user selected manually on the table.

        Args:
            index (QModelIndex): The index
            value (str): The data value
            role (Qt.ItemDataRole): The role of the data.  Defaults to Qt.EditRole.

        Returns:
            bool: True if successful; otherwise returns False.
        """
        r = index.row()
        c = index.column()

        if value:

            if c == 0:
                # TODO: LRU Cache for speed?
                oldkey = list(self._data.keys())[r]
                if value != oldkey:
                    self.design.rename_variable(oldkey, value)
                    self._gui.rebuild()
                    return True

            elif c == 1:
                self._data[list(self._data.keys())[r]] = value
                self._gui.rebuild()
                return True

        return False

    def headerData(self,
                   section: int,
                   orientation: Qt.Orientation,
                   role: Qt.ItemDataRole = Qt.DisplayRole) -> str:
        """Get the headers to be displayed.

        Args:
            secion (int): Section number.
            orientation (Qt.Orientation): Orientation of the header.
            role (Qt.ItemDataRole): Role of the header.  Defaults to Qt.DisplayRole.

        Returns:
            str: The header
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return 'Variable name'
                elif section == 1:
                    return 'Value'
                else:
                    units = config.DefaultMetalOptions.default_generic.units
                    if self.design:
                        if hasattr(self.design, '_template_options'):
                            units = self.design.template_options.units
                    return f'Parsed value (in {units})'
            return str(section + 1)

    def removeRows(self, row: int, count: int = 1, parent=QModelIndex()):
        """Delete highlighted rows.

        Args:
            row (int): First row to delete.
            count (int): Number of rolws to delete.  Defaults to 1.
            parent (QModelIndex): Parent index.
        """
        self.beginRemoveRows(parent, row, row + count - 1)
        lst = list(self._data.keys())
        for k in range(row + count - 1, row - 1, -1):
            del self._data[lst[k]]
        self.endRemoveRows()

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Determine how user may interact with each cell in the table.

        Args:
            index (QModelIndex): The index

        Returns:
            Qt.ItemFlags: The flags
        """
        if index.column() < 2:
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def add_row(self, key: str, val: str):
        """Add row with the given key/value.

        Args:
            key (str): The key
            val (str): The value
        """
        self._data[key] = val
        self._view.resizeColumnsToContents()
