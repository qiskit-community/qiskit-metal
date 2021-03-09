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
"""Main edit source code window,
based on pyqode.python: https://github.com/pyQode/pyqode.python
"""

from typing import TYPE_CHECKING

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDockWidget

from ...edit_source_ui import Ui_EditSource

__all__ = ['create_source_edit_widget', 'dockify']

if TYPE_CHECKING:
    from ...main_window import MetalGUI, QMainWindowExtension


def create_source_edit_widget(gui: 'MetalGUI',
                              class_name: str,
                              module_name: str,
                              module_path: str,
                              parent=None) -> QtWidgets.QWidget:
    """Creates the spawned window that has the edit source

    Arguments:
        gui (MetalGUI): The GUI
        class_name (str): The name of the class
        module_name (str): The name of the module
        module_path (str): The path to the module
        parent (object): The parent

    Returns:
        QtWidgets.QWidget: Ui_EditSource widget

    Access:
        `gui.component_window.src_widgets[-1]`
    """
    if not parent:
        parent = gui.main_window  # gui.component_window.ui.tabHelp

    gui.logger.info(
        f'Creating a source edit window for\n  class_name={class_name}\n'
        f'  file={module_path}')

    # TODO: should probably turn the following into a QMainWindow subclass
    edit_widget = QtWidgets.QMainWindow(
        parent)  # use parent, so this way its style sheet is inherited
    self = edit_widget
    self.ui = Ui_EditSource()
    self.ui.setupUi(edit_widget)
    self.dock = dockify(self, gui)

    # UI adjustments and customization
    self.ui.src_editor.gui = gui
    self.ui.src_editor.set_component(class_name, module_name, module_path)
    self.statusBar().hide()

    self.ui.textEditHelp.setStyleSheet("""
    background-color: #f9f9f9;
    color: #000000;
            """)

    self.dock.show()
    self.dock.raise_()
    self.dock.activateWindow()

    return edit_widget


def dockify(self, gui):
    """Dockify the given GUI

    Args:
        gui (MetalGUI): The GUI

    Returns:
        QDockWidget: The widget
    """
    ### Dockify
    self.dock_widget = QDockWidget('Edit Source', gui.main_window)
    dock = self.dock_widget
    dock.setWidget(self)

    dock.setAllowedAreas(Qt.RightDockWidgetArea)
    dock.setFloating(True)
    dock.resize(1200, 700)

    # Doesnt work
    # dock_gui = self.dock_widget
    # dock_gui.setWindowFlags(dock_gui.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)

    return dock