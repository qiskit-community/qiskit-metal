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
# Tree model for GDS renderer

import PySide6
from PySide6 import QtWidgets
from PySide6.QtWidgets import QTreeView, QWidget

from qiskit_metal._gui.widgets.bases.dict_tree_base import QTreeModel_Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main_window import MetalGUI


class RendererGDS_Model(QTreeModel_Base):
    """Tree model for GDS renderer.

    Args:
        QTreeModel_Base (QAbstractItemModel): Base class for nested dicts
    """

    def __init__(self, parent: QWidget, gui: 'MetalGUI', view: QTreeView):
        """Editable table with drop-down rows for GDS renderer options.
        Organized as a tree model where child nodes are more specific
        properties of a given parent node.

        Args:
            parent (QWidget): The parent widget
            gui (MetalGUI): The main user interface
            view (QTreeView): View corresponding to a tree structure
        """
        super().__init__(parent=parent,
                         gui=gui,
                         view=view,
                         child='GDS renderer')

    @property
    def data_dict(self) -> dict:
        """Return a reference to the (nested) dictionary containing the
        data."""
        return self.design.renderers.gds.options
