from .parameter_entry_scroll_area import ParameterEntryScrollArea
from PySide2.QtWidgets import QPushButton
from PySide2.QtWidgets import (QScrollArea, QVBoxLayout, QLabel, QWidget,
                               QHBoxLayout, QLineEdit, QLayout, QComboBox,
                               QMessageBox, QSizePolicy, QMainWindow,
                               QDockWidget)
from PySide2.QtCore import Qt
from PySide2.QtCore import QDir
from addict.addict import Dict
from .collapsable_widget import CollapsibleWidget
from collections import OrderedDict
import numpy as np
from .parameter_entry_scroll_area_ui import Ui_ScrollArea
from inspect import signature
import inspect
from collections import Callable
import os
from ....designs.design_base import QDesign
import importlib
import builtins
import logging
import traceback
import json
from typing import Dict as typeDict
import typing
if typing.TYPE_CHECKING:
    from ...main_window import MetalGUI


def create_param_entry_scroll_area(gui: 'MetalGUI',
                                   QLIBRARY_FOLDERNAME: str,
                                   abs_file_path: str,
                                   design: QDesign,
                                   parent=None,
                                   *args,
                                   **kwargs):
    """Creates the spawned window that has the edit source

    Arguments:
        gui (MetalGUI): the GUI
        module_name (str): the name of the module
        module_path (str): the path to the module
        parent (object): the parent

    Returns:
        QtWidgets.QWidget: Ui_EditSource widget

    Access:
        `gui.component_window.src_widgets[-1]`
    """
    print(
        f"ParameterEntryScrollArea should be class: {ParameterEntryScrollArea}")

    if not parent:
        parent = gui.main_window  # gui.component_window.ui.tabHelp

    gui.logger.info(f'Creating a PESA  window for {abs_file_path}')

    pesa = ParameterEntryScrollArea(QLIBRARY_FOLDERNAME, abs_file_path, design)
    print(f"new pesa: {pesa}")
    # TODO try just scroll area
    #pesa_main_window.setCentralWidget(pesa)
    pesa.dock = dockify(pesa)
    pesa.gui = gui

    pesa.dock.show()
    pesa.dock.raise_()
    pesa.dock.activateWindow()

    return pesa


def dockify(pesa):
    """Dockify the given GUI
    Args:
        gui (MetalGUI): the GUI

    Returns:
        QDockWidget: the widget
    """
    ### Dockify
    pesa.dock_widget = QDockWidget(
        'Parameter Entry Scroll Area'
    )  #TODO make gui the parent --> currently this causes gui display issues
    dock = pesa.dock_widget
    print("orig style sheet")
    print(pesa.styleSheet())
    dock.setWidget(pesa)
    print("old stylesheet")
    print(pesa.styleSheet())
    print(pesa.style())
    dock.setStyleSheet("")
    print("should be default style sheet")
    print(pesa.styleSheet())

    #dock.setAllowedAreas(Qt.RightDockWidgetArea)
    dock.setFloating(True)
    dock.resize(1200, 700)

    # Doesnt work
    # dock_gui = pesa.dock_widget
    # dock_gui.setWindowFlags(dock_gui.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)

    return dock
