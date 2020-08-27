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

from typing import Union

import numpy as np
import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QVariant, QTimer, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QFileDialog, QTreeView,
                             QLabel, QMainWindow, QMessageBox, QTabWidget)

__all__ = ['get_nested_dict_item']

KEY, NODE = range(2)

# List of children given as [(childname_0, childnode_0), (childname_1, childnode_1), ...]
# Where childname_i corresponds to KEY and childnode_i corresponds to NODE

def get_nested_dict_item(dic: dict, key_list: list):
    """
    Get a nested dictionary item.
    If key_list is empty, return dic itself.

    Args:
        dic (dict): dictionary of items
        key_list (list): list of keys

    Returns:
        dict: nested dictionary
    """
    if key_list:
        for k in key_list:
            dic = dic[k]
    return dic

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
        """
        Args:
            name (str): Name of this branch
            parent ([type]): The parent (Default: None)
            data (dict): Node data (Default: None)
        """
        super(BranchNode, self).__init__()
        self.name = name
        self.parent = parent
        self.children = []
        self._data = data  # dictionary containing the actual data

    def __len__(self):
        """
        Gets the number of children.

        Returns:
            int: The number of children this node has
        """
        return len(self.children)

    def provideName(self):
        """
        Gets the name.

        Returns:
            str: The node's name
        """
        return self.name  # identifier for BranchNode

    def childAtRow(self, row: int):
        """
        Gets the child at the given row.

        Args:
            row (int): The row number (0-indexed)

        Returns:
            Node: The node at the row
        """
        if 0 <= row < len(self.children):
            return self.children[row][NODE]

    def rowOfChild(self, child):
        """Gets the row of the given child

        Args:
            child (Node): the child

        Returns:
            int: Row of the given child.  -1 is returned if the child is not found.
        """
        for i, (_, childnode) in enumerate(self.children):
            if child == childnode:
                return i
        return -1

    def childWithKey(self, key):
        """Gets the child with the given key

        Args:
            key (str): the key

        Returns:
            Node: The child with the same name as the given key.
            None is returned if the child is not found
        """
        for childname, childnode in self.children:
            if key == childname:
                return childnode
        return None

    def insertChild(self, child):
        """
        Insert the given child

        Args:
            child (Node): the child
        """
        child.parent = self
        self.children.append((child.provideName(), child))

    def hasLeaves(self):
        """Do I have leaves?

        Returns:
            bool: True is I have leaves, False otherwise
        """
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
        """
        Args:
            label (str): Label for the leaf node
            parent (Node): The parent (Default: None)
            path (list): Node path (Default: None)
        """
        super(LeafNode, self).__init__()
        self.path = path or []
        self.parent = parent
        self.label = label

    @property
    def value(self):
        """Returns the value."""
        return get_nested_dict_item(self.parent._data, self.path)

    # @value.setter
    # def value(self, newvalue):
    #     self._value = newvalue

    def provideName(self):
        """
        Get the label.

        Returns:
            str: The label of the leaf node - this is *not* the value.
        """
        return self.label  # identifier for LeafNode (note: NOT value!)

class QTreeModel_Base(QAbstractItemModel):

    """
    Tree model for a general hierarchical dataset.

    This class extends the `QAbstractItemModel` class.

    MVC class
    See https://doc.qt.io/qt-5/qabstractitemmodel.html
    """

    __refreshtime = 500  # 0.5 second refresh time

    def __init__(self, data: dict, view: QTreeView):
        """
        Editable table with expandable drop-down rows.
        Organized as a tree model where child nodes are more specific properties
        of a given parent node.

        Args:
            parent (ParentWidget): Widget on which corresponding view will be displayed
            view (QTreeView): View corresponding to a tree structure
        """
        super().__init__()
        self._data = data
        self._rowCount = -1
        self._view = view

        self.root = BranchNode('')
        self.headers = ['Name', 'Value']
        self.paths = []

        self._start_timer()
        self.load()

    def _start_timer(self):
        """
        Start and continuously refresh timer in background to keep
        the total number of rows up to date.
        """
        self.timer = QTimer(self)
        self.timer.start(self.__refreshtime)
        self.timer.timeout.connect(self.auto_refresh)

    def auto_refresh(self):
        """
        Check to see if the total number of rows has been changed. If so,
        completely rebuild the model and tree.
        """
        newRowCount = self.rowCount(self.createIndex(0, 0))
        if self._rowCount != newRowCount:
            self.modelReset.emit()
            self._rowCount = newRowCount
            if self._view:
                self._view.autoresize_columns()

    @property
    def data_dict(self) -> dict:
        """ Return a reference to the (nested) dictionary containing the data."""
        return self._data

    def refresh(self):
        """Force refresh. Completely rebuild the model and tree."""
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
        """
        Get the number of rows.

        Args:
            parent (QModelIndex): the parent

        Returns:
            int: The number of rows
        """
        # Count number of child nodes belonging to the parent.
        node = self.nodeFromIndex(parent)
        if (node is None) or isinstance(node, LeafNode):
            return 0
        return len(node)

    def columnCount(self, parent):
        """Get the number of columns

        Args:
            parent (QModelIndex): the parent

        Returns:
            int: the number of columns
        """
        return len(self.headers)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole):
        """Gets the node data

        Args:
            index (QModelIndex): index to get data for
            role (Qt.ItemDataRole): the role (Default: Qt.DisplayRole)

        Returns:
            object: fetched data
        """
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
                else:
                    return QVariant()

        return QVariant()

    def setData(self, index: QModelIndex, value: QVariant, role: Qt.ItemDataRole = Qt.EditRole) -> bool:
        """Set the LeafNode value and corresponding data entry to value.
        Returns true if successful; otherwise returns false.
        The dataChanged() signal should be emitted if the data was successfully set.

        Args:
            index (QModelIndex): the index
            value (QVariant): the value
            role (Qt.ItemDataRole): the role of the data (Default: Qt.EditRole)

        Returns:
            bool: True if successful, False otherwise
        """

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

                        if node.path:  # if nested option
                            for x in node.path[:-1]:
                                dic = dic[x]
                            dic[node.path[-1]] = value
                        else:  # if top-level option
                            dic[lbl] = value
                        return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole):
        """ Set the headers to be displayed.

        Args:
            section (int): section number
            orientation (Qt.Orientation): the orientation
            role (Qt.ItemDataRole): the role

        Returns:
            object: header data
        """
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
        """What is my index?

        Args:
            row (int): the row
            column (int): the column
            parent (QModelIndex): the parent

        Returns:
            int: internal index
        """
        assert self.root
        branch = self.nodeFromIndex(parent)
        assert branch is not None
        # The third argument is the internal index.
        return self.createIndex(row, column, branch.childAtRow(row))

    def parent(self, child):
        """Gets the parent index of the given node

        Args:
            child (node): the child

        Returns:
            int: the index
        """
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

        Returns:
            list: flags
        """
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() == 1:
            node = self.nodeFromIndex(index)
            if isinstance(node, LeafNode):
                return flags | Qt.ItemIsEditable

        return flags
