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
QLibrary display in Library tab

@authors: Grace Harper
@date: 2021
"""

from .qcomponent_parameter_entry import QComponentParameterEntry
from PySide2.QtWidgets import (QDockWidget)
from PySide2.QtWidgets import QWidget

from ....designs.design_base import QDesign

import typing
if typing.TYPE_CHECKING:
    from ...main_window import MetalGUI


def create_qcomponent_parameter_entry(
    gui: 'MetalGUI',
    QLIBRARY_FOLDERNAME: str,
    abs_file_path: str,
    design: QDesign,
    parent=None,
):
    """Creates the spawned QComponentParameterEntry that is docked to force itself to
    display on top of the rest of the GUI

    Arguments:
        gui (MetalGUI): the GUI
        QLIBRARY_FOLDERNAME: Current directory name for where all QComponent .py files are held - ex: 'qlibrary'
        abs_file_path: absolute file path to current QComponent .py file
        design: current design
        parent: parent widget

    Returns:
        QtWidgets.QScrollArea: QComponentParameterEntry

    Access:
        gui.qcpe
    """

    if not parent:
        parent = gui.main_window  # gui.component_window.ui.tabHelp

    gui.logger.info(f'Creating a qcpe  window for {abs_file_path}')

    qcpe = QComponentParameterEntry(QLIBRARY_FOLDERNAME, abs_file_path, design)
    qcpe.dock = dockify_hack(qcpe)
    qcpe.gui = gui

    qcpe.dock.show()
    qcpe.dock.raise_()
    qcpe.dock.activateWindow()

    return qcpe


def dockify_hack(qcpe: QWidget):
    """Dockify the given widget 
    Args:
        qcpe: QComponentParameterEntry to be docked

    Returns:
        QDockWidget: the docked widget
    """
    qcpe.dock_widget = QDockWidget('Parameter Entry')
    dock = qcpe.dock_widget
    dock.setWidget(qcpe)
    dock.setStyleSheet("")

    dock.setFloating(True)
    dock.resize(1200, 700)

    return dock
