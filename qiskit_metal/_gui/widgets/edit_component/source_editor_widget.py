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

"""Main edit source code window,
based on pyqode.python: https://github.com/pyQode/pyqode.python

@author: Zlatko Minev 2020
"""

from typing import TYPE_CHECKING

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDockWidget

from ...edit_source_ui import Ui_EditSource

if TYPE_CHECKING:
    from ...main_window import MetalGUI, QMainWindowExtension


def create_source_edit_widget(gui: 'MetalGUI',
                              class_name: str,
                              module_name: str,
                              module_path: str,
                              parent=None) -> QtWidgets.QWidget:
    """Creates teh spawned window that has the edit source

    Arguments:
        gui {MetalGUI} -- [description]
        class_name {str} -- [description]
        module_name {str}
        module_path {str} -- [description]

    Returns:
        [QtWidgets.QWidget] -- [Ui_EditSource widget]

    Access:
        gui.component_window.src_widgets[-1]
    """
    if not parent:
        parent = gui.main_window  # gui.component_window.ui.tabHelp

    gui.logger.info(f'Creating a source edit window for\n  class_name={class_name}\n'
                    f'  file={module_path}')

    edit_widget = QtWidgets.QMainWindow(parent) # use parent, so this way its style sheet is inherited
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