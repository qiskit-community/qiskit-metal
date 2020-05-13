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

from ..edit_source_ui import Ui_EditSource

if TYPE_CHECKING:
    from ..main_window import MetalGUI, QMainWindowExtension


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
    """
    if not parent:
        parent = gui.main_window  # gui.component_window.ui.tabHelp

    gui.logger.info(f'Creating a source edit window for class_name={class_name}'
                    'from file={module_path}')

    edit_widget = QtWidgets.QMainWindow(parent) # use parent, so this way its style sheet is inherited
    edit_widget.ui = Ui_EditSource()
    edit_widget.ui.setupUi(edit_widget)

    edit_widget.ui.src_editor.gui = gui
    edit_widget.ui.src_editor.set_component(
        class_name, module_name, module_path)

    edit_widget.show()

    # Bring window to top.
    # QtCore.QCoreApplication().processEvents()
    edit_widget.raise_()
    edit_widget.activateWindow()
    return edit_widget
