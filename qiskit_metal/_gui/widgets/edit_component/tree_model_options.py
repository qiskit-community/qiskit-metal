# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
#

"""
@authors: Dennis Wang, Zlatko Minev
@date: 2020
"""

import ast
import inspect
from inspect import getfile, signature
from pathlib import Path
from typing import TYPE_CHECKING, Union

import numpy as np
import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QVariant, QTimer, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QFileDialog, QTreeView,
                             QLabel, QMainWindow, QMessageBox, QTabWidget)

from .... import logger
from ...component_widget_ui import Ui_ComponentWidget
from ...utility._handle_qt_messages import catch_exception_slot_pyqt
from .source_editor_widget import create_source_edit_widget

if TYPE_CHECKING:
    from .component_widget import ComponentWidget

KEY, NODE = range(2)

# List of children given as [(childname_0, childnode_0), (childname_1, childnode_1), ...]
# Where childname_i corresponds to KEY and childnode_i corresponds to NODE


def get_nested_dict_item(dic: dict, key_list: list, level=0):
    """
    EXAMPLE USE
    ---------------------
    myDict = Dict(aa=Dict(x1={'dda':34},y1='Y',z='10um'),
          bb=Dict(x2=5,y2='YYYsdg',z='100um'))
    key_list = ['aa', 'x1', 'dda']
    [get_dict_item](myDict, key_list)
    returns 34
    """
    if not key_list:  # get the root
        return dic
    if level < len(key_list) - 1:
        return get_nested_dict_item(dic[key_list[level]], key_list, level + 1)
    return dic[key_list[level]]


class BranchNode:

    """
    A BranchNode object has a nonzero number of child nodes.
    These child nodes can be either BranchNodes or LeafNodes.

    It is uniquely defined by its name, parent node, and list of children.
    The list of children consists of tuple pairs of the form (nodename_i, node_i),
    where the former is the name of the child node and the latter is the child node itself.
    KEY (=0) and NODE (=1) identify their respective positions within each tuple pair.
    """

    def __init__(self, name: str, parent=None, data: dict = None):
        super(BranchNode, self).__init__()
        self.name = name
        self.parent = parent
        self.children = []
        self._data = data  # dictionary containing the actual data

    def __len__(self):
        return len(self.children)

    def provideName(self):
        return self.name  # identifier for BranchNode

    def childAtRow(self, row: int):
        if 0 <= row < len(self.children):
            return self.children[row][NODE]

    def rowOfChild(self, child):
        for i, (_, childnode) in enumerate(self.children):
            if child == childnode:
                return i
        return -1

    def childWithKey(self, key):
        for childname, childnode in self.children:
            if key == childname:
                return childnode
        return None

    def insertChild(self, child):
        child.parent = self
        self.children.append((child.provideName(), child))

    def hasLeaves(self):
        if not self.children:
            return False
        return isinstance(self.children[KEY][NODE], LeafNode)


class LeafNode:

    """
    A LeafNode object has no children but consists of a key-value pair, denoted by
    label and value, respectively.

    It is uniquely identified by its root-to-leaf path, which is a list of keys
    whose positions denote their nesting depth (shallow to deep).
    """

    def __init__(self, label: str, parent=None, path=None):
        super(LeafNode, self).__init__()
        self.path = path or []
        self.parent = parent
        self.label = label

    @property
    def value(self):
        return get_nested_dict_item(self.parent._data, self.path)

    # @value.setter
    # def value(self, newvalue):
    #     self._value = newvalue

    def provideName(self):
        return self.label  # identifier for LeafNode (note: NOT value!)


class QTreeModel_Options(QAbstractItemModel):

    """
    Tree model for the options of a given component.

    MVC class
    See https://doc.qt.io/qt-5/qabstractitemmodel.html
    """

    __refreshtime = 500  # 0.5 second refresh time

    # NOTE: __init__ takes in design as extra parameter compared to table_model_options!

    def __init__(self, parent: 'ComponentWidget', gui: 'MetalGUI', view: QTreeView):
        super().__init__(parent=parent)
        self._component_widget = parent
        self.logger = gui.logger
        self._gui = gui
        self._row_count = -1
        self._view = view

        self.root = BranchNode('')
        self.headers = ['Name', 'Value', 'Parsed value']
        self.paths = []

        self._start_timer()
        self.load()

    @property
    def gui(self):
        return self._gui

    def _start_timer(self):
        """
        Start and continuously refresh timer in background to keep
        the total number of rows up to date.
        """
        self.timer = QTimer(self)
        self.timer.start(self.__refreshtime)
        self.timer.timeout.connect(self.auto_refresh)

    # TODO: Check if new nodes have been added. If so, rebuild model.

    def auto_refresh(self):
        return  # TODO:
        newRowCount = self.rowCount(self.createIndex(0, 0))
        if self._rowCount != newRowCount:
            self.modelReset.emit()
            self._rowCount = newRowCount
            if self._view:
                self._view.resizeColumnsToContents()

    @property
    def design(self) -> 'QDesign':
        return self._gui.design

    @property
    def component(self) -> 'QComponent':
        return self._component_widget.component

    @property
    def data_dict(self) -> dict:
        """ Return a reference to the component options (nested) dictionary."""
        return self.component.options

    def refresh(self):
        """Force refresh. Completly rebuild the model and tree."""
        self.load()  # rebuild the tree
        self.modelReset.emit()

    def getPaths(self, curdict: dict, curpath: list):
        """Recursively finds and saves all root-to-leaf paths in model"""
        for k, v in curdict.items():
            if isinstance(v, dict):
                self.getPaths(v, curpath + [k])
            else:
                self.paths.append(curpath + [k, v])

    def load(self):
        """Builds a tree from a dictionary (self.data_dict)"""
        if not self.component:
            return

        self.beginResetModel()

        # Set the data dict reference of the root node. The root node doesn't have a name.
        self.root._data = self.data_dict

        # Clear existing tree paths if any
        self.paths.clear()
        self.root.children.clear()

        # Construct the paths -> sets self.paths
        self.getPaths(self.data_dict, [])

        for path in self.paths:
            root = self.root
            branch = None
            # Combine final label and value for leaf node, so stop at 2nd to last element of each path
            for key in path[:-2]:
                # Look for childnode with the name 'key'. If it's not found, create a new branch.
                branch = root.childWithKey(key)
                if not branch:
                    branch = BranchNode(key, data=self.data_dict)
                    root.insertChild(branch)
                root = branch
            # If a LeafNode resides in the outermost dictionary, the above for loop is bypassed.
            # [Note: This happens when the root-to-leaf path length is just 2.]
            # In this case, add the LeafNode right below the master root.
            # Otherwise, add the LeafNode below the final branch.
            if not branch:
                root.insertChild(
                    LeafNode(path[-2], root, path=path[:-1]))
            else:
                branch.insertChild(
                    LeafNode(path[-2], branch, path=path[:-1]))

        # Emit a signal since the model's internal state (e.g. persistent model indexes) has been invalidated.
        self.endResetModel()

    def rowCount(self, parent: QModelIndex):

        # If there is no component, then show placeholder text
        if self.component is None:
            if self._view:
                self._view.show_placeholder_text()
            return 0

        else:
            # We have a compoentn selected
            # if we have the view of the model linked (we should)
            # hide placeholder text
            if self._view:
                self._view.hide_placeholder_text()

            ###
            # Count number of child nodes belonging to the parent.
            node = self.nodeFromIndex(parent)
            if (node is None) or isinstance(node, LeafNode):
                return 0
            return len(node)

    def columnCount(self, parent):
        return len(self.headers)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole):

        if not index.isValid():
            return QVariant()

        if self.component is None:
            return QVariant()

        # The data in a form suitable for editing in an editor. (QString)
        if role == Qt.EditRole:
            return self.data(index, Qt.DisplayRole)

        # Bold the first
        if (role == Qt.FontRole) and (index.column() == 0):
            font = QFont()
            font.setBold(True)
            return font

        if role == Qt.TextAlignmentRole:
            return QVariant(int(Qt.AlignTop | Qt.AlignLeft))

        if role == Qt.DisplayRole:
            node = self.nodeFromIndex(index)
            if node:
                # the first column is either a leaf key or a branch
                # the second column is always a leaf value or for a branch is ''.
                if isinstance(node, BranchNode):
                    # Handle a branch (which is a nested subdictionary, which can be expanded)
                    if index.column() == 0:
                        return node.name
                    return ''
                # We have a leaf
                elif index.column() == 0:
                    return str(node.label)  # key
                elif index.column() == 1:
                    return str(node.value)  # value
                elif index.column() == 2:
                    return str(self.design.parse_value(node.value))
                else:
                    return QVariant()

        return QVariant()

    def setData(self, index: QModelIndex, value: QVariant, role: Qt.ItemDataRole = Qt.EditRole) -> bool:
        """Set the LeafNode value and corresponding data entry to value.
        Returns true if successful; otherwise returns false.
        The dataChanged() signal should be emitted if the data was successfully set."""

        if not index.isValid():
            return False

        elif role == QtCore.Qt.EditRole:

            if index.column() == 1:
                node = self.nodeFromIndex(index)

                if isinstance(node, LeafNode):
                    value = str(value)  # new value
                    old_value = node.value  # option value

                    if old_value == value:
                        return False

                    # Set the value of an option when the new value is different
                    else:
                        dic = self.data_dict  # option dict
                        lbl = node.label  # option key

                        self.logger.info(
                            f'Setting component option {lbl:>10s}: old value={old_value}; new value={value};')

                        ##### Parse value if not str ##############################
                        # Somewhat legacy code for extended handling of non string options
                        # These days we tend to have all options be strings, so not so releavnt, but keep here for now
                        # to allow extended use in te future
                        if not isinstance(old_value, str):
                            processed_value, used_ast = parse_param_from_str(
                                value)
                            self.logger.info(f'  Used paring:  Old value type={type(old_value)}; '
                                             f'New value type={type(processed_value)};  New value={processed_value};'
                                             f'; Used ast={used_ast}')
                            value = processed_value
                        #################################################

                        if node.path:  # if nested option
                            for x in node.path[:-1]:
                                dic = dic[x]
                            dic[node.path[-1]] = value
                        else:  # if top-level option
                            dic[lbl] = value

                        self.component.rebuild()
                        self.gui.refresh()
                        return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole):
        """ Set the headers to be displayed. """
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if 0 <= section < len(self.headers):
                    return self.headers[section]

            elif role == Qt.FontRole:
                font = QFont()
                font.setBold(True)
                return font

        return QVariant()

    def index(self, row: int, column: int, parent: QModelIndex):
        assert self.root
        branch = self.nodeFromIndex(parent)
        assert branch is not None
        # The third argument is the internal index.
        return self.createIndex(row, column, branch.childAtRow(row))

    def parent(self, child):
        node = self.nodeFromIndex(child)
        if node is None:
            return QModelIndex()
        parent = node.parent
        if parent is None:
            return QModelIndex()
        grandparent = parent.parent
        if grandparent is None:
            return QModelIndex()
        row = grandparent.rowOfChild(parent)
        assert row != -1
        return self.createIndex(row, 0, parent)

    def nodeFromIndex(self, index: QModelIndex) -> Union[BranchNode, LeafNode]:
        """Utility method we define to get the node from the index.

        Args:
            index (QModelIndex): The model index

        Returns:
            Union[BranchNode, LeafNode]: Returns the node, which can either be
            a branch (for a dict) or a leaf (for an option key value pairs)
        """
        if index.isValid():
            # The internal pointer will return the leaf or branch node under the given parent.
            return index.internalPointer()
        return self.root

    def flags(self, index: QModelIndex):
        """
        Determine how user may interact with each cell in the table.
        """
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() == 1:
            node = self.nodeFromIndex(index)
            if isinstance(node, LeafNode):
                return flags | Qt.ItemIsEditable

        return flags


def parse_param_from_str(text):
    """Attempt to parse a value from a string using ast"""
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
