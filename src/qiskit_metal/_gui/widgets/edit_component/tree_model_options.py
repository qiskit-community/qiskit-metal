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
"""Tree model for component options menu."""

from typing import TYPE_CHECKING
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTreeView, QWidget
from qiskit_metal._gui.widgets.bases.dict_tree_base import LeafNode, BranchNode, QTreeModel_Base, parse_param_from_str

if TYPE_CHECKING:
    from ...main_window import MetalGUI


class QTreeModel_Options(QTreeModel_Base):
    """Tree model for component options menu. Overrides rowCount method to
    include placeholder text, and data method to include 3rd column for parsed
    values.

    Args:
        QTreeModel_Base (QAbstractItemModel): Base class for nested dicts
    """

    def __init__(self, parent: QWidget, gui: 'MetalGUI', view: QTreeView):
        """Editable table with drop-down rows for component options. Organized
        as a tree model where child nodes are more specific properties of a
        given parent node.

        Args:
            parent (QWidget): The parent widget
            gui (MetalGUI): The main user interface
            view (QTreeView): View corresponding to a tree structure
        """
        super().__init__(parent=parent, gui=gui, view=view, child='component')
        self.headers = ['Name', 'Value',
                        'Parsed value']  # 3 columns instead of 2

    @property
    def data_dict(self) -> dict:
        """Return a reference to the component options (nested) dictionary."""
        return self.component.options

    def rowCount(self, parent: QModelIndex):
        """Get the number of rows.

        Args:
            parent (QModelIndex): The parent

        Returns:
            int: The number of rows
        """
        # If there is no component, then show placeholder text
        if self.component is None:
            if self._view:
                self._view.show_placeholder_text()
            return 0

        else:
            # We have a component selected
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

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole):
        """Gets the node data.

        Args:
            index (QModelIndex): Index to get data for
            role (Qt.ItemDataRole): The role..  Defaults to Qt.DisplayRole.

        Returns:
            object: fetched data
        """
        if not index.isValid():
            return None

        if self.component is None:
            return None

        # The data in a form suitable for editing in an editor. (QString)
        if role == Qt.EditRole:
            return self.data(index, Qt.DisplayRole)

        # Bold the first
        if (role == Qt.FontRole) and (index.column() == 0):
            font = QFont()
            font.setBold(True)
            return font

        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignTop | Qt.AlignLeft)

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
                    # TODO: If the parser fails, this can throw an error
                    return str(self.design.parse_value(node.value))
                else:
                    return None

        return None
