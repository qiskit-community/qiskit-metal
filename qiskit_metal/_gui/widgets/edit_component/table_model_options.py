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
"""Handles editing a QComponent."""

import ast
import inspect
from inspect import getfile, signature
from pathlib import Path
from typing import TYPE_CHECKING, Union
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QFont

__all__ = ['parse_param_from_str']

if TYPE_CHECKING:
    from .component_widget import ComponentWidget
    from ....designs import QDesign


class QTableModel_Options(QAbstractTableModel):
    """Table model for the options of a given component.

    This class inherits from the `QAbstractTableModel` class

    MVC class
    See https://doc.qt.io/qt-5/qabstracttablemodel.html
    """

    # __timer_interval = 500  # ms

    def __init__(self,
                 gui: 'MetalGUI',
                 parent: 'ComponentWidget' = None,
                 view=None):
        """
        Args:
            gui (MetalGUI): The GUI
            parent (ComponentWidget): The parent ComponentWidget.  Defaults to None.
            view (object): The view.  Defaults to None.
        """
        super().__init__(parent=parent)
        self.logger = gui.logger
        self.gui = gui
        self._row_count = -1
        self._view = view

        # self._create_timer()
        self.columns = ['Name', 'Value', 'Parsed value']

    @property
    def design(self) -> 'QDesign':
        """Returns the QDesign."""
        return self.gui.design

    @property
    def component(self):
        """Returns the component."""
        return self.parent().component

    def refresh(self):
        """Force refresh.

        Completly rebuild the model.
        """
        self.modelReset.emit()

    def rowCount(self, parent: QModelIndex = None):
        """Returns the number of rows.

        Args:
            parent (QModelIndex): Unused.  Defaults to None.

        Returns:
            int: The number of rows
        """
        if self.component is None:
            if self._view:
                self._view.show_placeholder_text()
            return 0
        if self._view:
            self._view.hide_placeholder_text()
        return len(self.component.options)

    def columnCount(self, parent: QModelIndex = None):
        """Returns the number of columns.

        Args:
            parent (QModelIndex): Unused.  Defaults to None.

        Returns:
            int: The number of columns
        """
        return 3

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Set the headers to be displayed.

        Args:
            section (int): Section number
            orientation (Qt orientation): Section orientation
            role (Qt display role): Display role.  Defaults to DisplayRole.

        Returns:
            str: The header data, or None if not found
        """

        if self.component is None:
            return None

        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < self.columnCount():
                    return self.columns[section]

        elif role == Qt.FontRole:
            if section == 0:
                font = QFont()
                font.setBold(True)
                return font

    def flags(self, index: QModelIndex):
        """Set the item flags at the given index. Seems like we're implementing
        this function just to see how it's done, as we manually adjust each
        treeView to have NoEditTriggers.

        Args:
            index (QModelIndex): The index

        Returns:
            Qt flags: Flags from Qt
        """
        # https://doc.qt.io/qt-5/qt.html#ItemFlag-enum

        if not index.isValid():
            return Qt.ItemIsEnabled

        # Returns the item flags for the given index.
        # The base class implementation returns a combination of flags that enables
        # the item (ItemIsEnabled) and allows it to be selected (ItemIsSelectable).
        flags = QAbstractTableModel.flags(self, index)
        if index.column() == 1:
            flags |= Qt.ItemIsEditable

        return Qt.ItemFlags(flags)

    # https://doc.qt.io/qt-5/qt.html#ItemDataRole-enum
    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        """Depending on the index and role given, return data. If not returning
        data, return None (PySide equivalent of QT's "invalid QVariant").

        Returns:
            str: Data matching theindex and role.
        """

        if not index.isValid():
            return
        # if not 0 <= index.row() < self.rowCount():
        #    return None

        if self.component is None:
            return

        # The key data to be rendered in the form of text. (QString)
        if role == Qt.DisplayRole:
            row = index.row()
            column = index.column()
            data = self.component.options
            # There's probably a better way to access the data here
            if column == 0:
                data = list(data.keys())
            elif column in [1, 2]:
                data = list(data.values())

            data = data[row]
            if column == 2:
                if isinstance(data, dict):
                    return 'This is a dictionary.'
                else:
                    return str(self.design.parse_value(data))
            else:
                return str(data)

        # The data in a form suitable for editing in an editor.  (QString)
        elif role == Qt.EditRole:
            return self.data(index, QtCore.Qt.DisplayRole)

        # The font used for items rendered with the default delegate. (QFont)
        elif role == Qt.FontRole:
            if index.column() == 0:
                font = QtGui.QFont()
                font.setBold(True)
                return font

    def setData(self,
                index: QtCore.QModelIndex,
                value,
                role=QtCore.Qt.EditRole) -> bool:
        """Sets the role data for the item at index to value. The dataChanged()
        signal should be emitted if the data was successfully set.

        Args:
            index (QtCore.QModelIndex): The index
            value (str): The value
            role (QtCore.Qt.EditRole): The edit role

        Returns:
            bool: Returns true if successful; otherwise returns false.
        """

        # TODO: handle nested dictionaries
        # See v0.1: get_nested_dict_item, pop_nested_dict_item
        # TODO: ability to add dictionary such as to add pins
        if not index.isValid():
            return False

        elif role == QtCore.Qt.EditRole:
            if index.column() == 1:
                self._value = value  # QString
                value = str(value)

                data = self.component.options  # type: dict
                key, old_val = list(data.items())[index.row()]

                # When we do nothing
                if isinstance(old_val, dict):
                    self.logger.error(
                        'You selected a dicitonary this'
                        'cannot be edited directly edit its items.')
                    return False

                if old_val == value:
                    return False

                # When we do something to change the value

                # try:
                # TODO: should retry and if error then reset the value
                if 1:
                    self.logger.info(
                        f'Component options: Old value={old_val}; New value={value};'
                    )
                    if isinstance(old_val, str):
                        data[key] = str(value)
                    else:
                        processed_value, used_ast = parse_param_from_str(value)
                        self.logger.info(
                            f'  Used paring:  Old value type={type(old_val)}; '
                            f'New value type={type(processed_value)};  New value={processed_value};'
                            f'; Used ast={used_ast}')
                        data[key] = processed_value

                    self.component.rebuild()
                    self.gui.refresh()

                # except and finally restore the value
                return True

        # elif role == Qt.CheckStateRole:

        return False


def parse_param_from_str(text):
    """Attempt to parse a value from a string using ast.

    Args:
        text (str): String to parse

    Return:
        tuple: value, used_ast

    Raises:
        Exception: An error occurred
    """
    text = str(text).strip()
    value = text
    used_ast = False
    try:  # crude way to handle list and values
        value = ast.literal_eval(text)
        used_ast = True
    except Exception as exception:
        pass
        # print(exception)
    return value, used_ast
