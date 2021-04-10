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
"""
Delegate for Param Entry Window's MVD
"""

from PySide2.QtWidgets import QItemDelegate
from PySide2.QtCore import QAbstractItemModel, QModelIndex, QTimer, Qt
from PySide2.QtWidgets import (QWidget, QStyleOptionViewItem)

from qiskit_metal._gui.widgets.create_component_window.model_view.tree_model_param_entry import TreeModelParamEntry


class ParamDelegate(QItemDelegate):
    """
    ParamDelegate for controlling specific UI display (such as QComboBoxes) for the Parameter Entry Window
    """
    pass

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem,
                     index: QModelIndex) -> QWidget:
        """
        Overriding inherited createdEditor class
        Args:
            parent: Parent widget
            option: Style options for the related view
            index: Specific index being edited

        Returns:

        """
        if index.column() == TreeModelParamEntry.TYPE:
            node = index.model().nodeFromIndex(index)
            combo = node.get_type_combobox(parent)  #dicts vs values
            #combo.setEditable(True)
            return combo
        else:
            return QItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index: QModelIndex):
        """
        Overriding inherited setEditorData class
        Args:
            editor: Current editor for the data
            index: Current index being modified

        """
        m = index.model()
        d = m.data(index, Qt.DisplayRole)
        text = index.model().data(index, Qt.DisplayRole)
        if index.column() == TreeModelParamEntry.TYPE:
            text = editor.setCurrentText(text)
        else:
            QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model: QAbstractItemModel, index):
        """
        Overriding inherited setModelData class
        Args:
            editor: Current editor for the data
            model: Current model whose data is being set
            index: Current index being modified

        """
        if index.column() == TreeModelParamEntry.TYPE:
            model.setData(index, editor.getTypeName())
            # get type
            # get corresponding dict entry
            # update type (OrderedDict, str, etc.)  as necessary
            # get value
        else:
            QItemDelegate.setModelData(self, editor, model, index)
