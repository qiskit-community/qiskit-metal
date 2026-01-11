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
=================================================
GUI (:mod:`qiskit_metal._gui`)
=================================================

.. currentmodule:: qiskit_metal._gui

GUI module, handles user interface.

The gui module is only loaded if right python qt module
(such as pyside or pyqt) can be found.


Main Window
---------------

.. autosummary::
    :toctree: .

    MetalGUI

"""
# pylint: disable=invalid-name

import logging
from qiskit_metal import __version__

from qiskit_metal import config
if config.is_building_docs():
    # imported here for the docstrings
    from qiskit_metal._gui.list_model_base import DynamicList
    from qiskit_metal._gui.main_window_base import QMainWindowExtensionBase
    from qiskit_metal._gui.main_window_base import QMainWindowBaseHandler
    from qiskit_metal._gui.main_window import QMainWindowExtension
    from qiskit_metal._gui.main_window import MetalGUI
    from qiskit_metal._gui.tree_view_base import QTreeView_Base
    from qiskit_metal._gui.renderer_gds_gui import RendererGDSWidget
    from qiskit_metal._gui.renderer_gds_model import RendererGDS_Model
    from qiskit_metal._gui.elements_window import ElementsWindow
    from qiskit_metal._gui.elements_window import ElementTableModel
    from qiskit_metal._gui.widgets.all_components.table_view_all_components import QTableView_AllComponents
    from qiskit_metal._gui.widgets.all_components.table_model_all_components import QTableModel_AllComponents
    from qiskit_metal._gui.widgets.bases.dict_tree_base import BranchNode
    from qiskit_metal._gui.widgets.bases.dict_tree_base import LeafNode
    from qiskit_metal._gui.widgets.bases.dict_tree_base import QTreeModel_Base
    from qiskit_metal._gui.widgets.bases.QWidget_PlaceholderText import QWidget_PlaceholderText
    from qiskit_metal._gui.widgets.edit_component.component_widget import ComponentWidget
    from qiskit_metal._gui.widgets.edit_component.table_model_options import QTableModel_Options
    from qiskit_metal._gui.widgets.edit_component.table_view_options import QTableView_Options
    from qiskit_metal._gui.widgets.edit_component.tree_model_options import QTreeModel_Options
    from qiskit_metal._gui.widgets.edit_component.tree_view_options import QTreeView_Options
    from qiskit_metal._gui.widgets.log_widget.log_metal import QTextEditLogger
    from qiskit_metal._gui.widgets.log_widget.log_metal import LogHandler_for_QTextLog
    from qiskit_metal._gui.widgets.plot_widget.plot_window import QMainWindowPlot
    from qiskit_metal._gui.widgets.variable_table.prop_val_table_gui import PropertyTableWidget
    from qiskit_metal._gui.widgets.variable_table.prop_val_table_model import PropValTable
    from qiskit_metal._gui.widgets.variable_table.right_click_table_view import RightClickView

    from qiskit_metal._gui.utility import _handle_qt_messages
    from qiskit_metal._gui.utility import _toolbox_qt
    from qiskit_metal._gui.widgets.bases import dict_tree_base
    from qiskit_metal._gui.widgets.edit_component import component_widget
    from qiskit_metal._gui.widgets.edit_component import table_model_options
    from qiskit_metal._gui.widgets.edit_component import tree_model_options
