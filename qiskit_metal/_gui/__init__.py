# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
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

Created on Tue May 14 17:13:40 2019
@author: Zlatko


Main Window
---------------

.. autosummary::
    :toctree: ../stubs/

    MetalGUI

"""
# pylint: disable=invalid-name

import logging
from .. import __version__

from .. import config
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
    from qiskit_metal._gui.widgets.bases.expanding_toolbar import QToolBarExpanding
    from qiskit_metal._gui.widgets.bases.dict_tree_base import BranchNode
    from qiskit_metal._gui.widgets.bases.dict_tree_base import LeafNode
    from qiskit_metal._gui.widgets.bases.dict_tree_base import QTreeModel_Base
    from qiskit_metal._gui.widgets.bases.QWidget_PlaceholderText import QWidget_PlaceholderText
    from qiskit_metal._gui.widgets.edit_component.component_widget import ComponentWidget
    from qiskit_metal._gui.widgets.edit_component.source_editor import MetalSourceEditor
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
    from qiskit_metal._gui.widgets.edit_component import source_editor
    from qiskit_metal._gui.widgets.edit_component import source_editor_widget
    from qiskit_metal._gui.widgets.edit_component import table_model_options
    from qiskit_metal._gui.widgets.edit_component import tree_model_options

else:
    # Main GUI load
    # Check if PySide2 is available for import
    try:
        import PySide2
        __ihave_qt__ = True
    except (ImportError, ModuleNotFoundError):
        __ihave_qt__ = False

    if __ihave_qt__:

        # Add hook for when we start the gui - Logging for QT errors
        from .utility._handle_qt_messages import QtCore, _qt_message_handler
        QtCore.qInstallMessageHandler(_qt_message_handler)
        del QtCore, _qt_message_handler

        from .main_window_base import kick_start_qApp
        from .main_window import MetalGUI as _MetalGUI

        def MetalGUI(*args, **kwargs):
            """Load Qiskit Metal

            Returns:
                gui instance of None
            """
            qApp = kick_start_qApp()
            if not qApp:
                logging.error(
                    "Could not start Qt event loop using QApplicaiton.")
            return _MetalGUI(*args, **kwargs)

    else:
        # Function as an error function for the class MetalGUI
        def MetalGUI(*args, **kwargs):  # pylint: disable=unused-argument,bad-option-value,invalid-name
            """
            ERROR: Unable to load PySide2! Please make sure PySide2 is installed.
            See Qiskit Metal installation instrucitons and Qiskit Metal help.
            """

            _error_msg = r'ERROR: CANNOT START GUI because COULD NOT LOAD PySide2'\
                'Try `import PySide2` This seems to have failed.'\
                'Have you installed PySide2?'\
                'See install readme.'

            print(_error_msg)

            raise Exception(_error_msg)
