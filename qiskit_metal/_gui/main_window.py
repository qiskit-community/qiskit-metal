# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
GUI front-end interface for Qiskit Metal in PyQt5.
@author: Zlatko Minev, IBM
"""
# pylint: disable=invalid-name

# some interesting paackages:
# https://github.com/mfreiholz/Qt-Advanced-Docking-System
# https://github.com/JackyDing/QtFlex5

import logging
import os
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox, QFileDialog



#from ..toolbox_python._logging import setup_logger
#from .. import config, Dict
from ..designs.design_base import DesignBase
from ..toolbox_metal.import_export import load_metal_design
from ._handle_qt_messages import catch_exception_slot_pyqt
from .component_widget_ui import Ui_ComponentWidget
from .main_window_base import QMainWindowBaseHandler, QMainWindowExtensionBase
from .widgets.components_model import ComponentsTableModel
from .plot_window import QMainWindowPlot
from .main_window_ui import Ui_MainWindow
from .elements_window import ElementsWindow

#from .widgets.log_metal import LoggingHandlerForLogWidget

class QMainWindowExtension(QMainWindowExtensionBase):
    """This contains all the functions tthat the gui needs
    to call directly from the UI

    To access the GUI HAndler above this, call:
        self.handler

    Args:
        QMainWindow ([type]): [description]
    """

    @property
    def design(self) -> DesignBase:
        """Return the design.

        Returns:
            DesignBase: [description]
        """
        return self.handler.design

    def _set_element_tab(self,
                         yesno):
        print(yesno)
        print("self if: ", self)
        if yesno:
            self.ui.tabWidget.setCurrentWidget(self.ui.tabElements)
            self.ui.actionElements.setText("View")
        else:
            self.ui.tabWidget.setCurrentWidget(self.ui.mainViewTab)
            self.ui.actionElements.setText("Elements")

    def delete_all_components(self):
        """Delete all components
        """
        ret = QMessageBox.question(self, 'Delete all components?',
                                   "Are you sure you want to clear all Metal components?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.logger.info('Delete all components.')
            return self.design.delete_all_components()

    @catch_exception_slot_pyqt()
    def save_design(self, _):
        """
        Handles click on save design
        """
        filename = QFileDialog.getSaveFileName(None,
                                               'Select locaiton to save Metal design to')[0]

        if filename:
            self.logger.info(f'Attempting to save design file to {filename}')
            # Maybe try here?
            self.design.save_design(filename)
            self.logger.info(f'Successfully saved.')

    @catch_exception_slot_pyqt()
    def load_design(self, _):
        """
        Handles click on loading metal design
        """
        filename = QFileDialog.getOpenFileName(None,
                                               'Select locaiton to load Metal design from')[0]
        if filename:
            self.logger.info(f'Attempting to load design file {filename}')
            design = load_metal_design(filename)
            self.logger.info(f'Successfully loaded file. Now setting design into gui.')
            self.handler.set_design(design)
            self.logger.info(f'Successfully set design. Loaded and done.')

    @catch_exception_slot_pyqt()
    def full_refresh(self, _):
        self.logger.info(f'Force refresh...')
        self.handler.refresh()


class MetalGUI(QMainWindowBaseHandler):
    """Qiskit Metal Main GUI.

    Args:
        QMainWindowBase ([type]): [description]
    """

    __UI__ = Ui_MainWindow
    _QMainWindowClass = QMainWindowExtension

    _dock_names = [
        'dockComponent',
        'dockConnectors',
        'dockDesign',
        'dockLog',
        'dockNewComponent']

    def __init__(self, design: DesignBase = None):
        """Ini

        Args:
            design (DesignBase, optional): Pass in the design that the GUI should handle.
                Defaults to None.
        """

        super().__init__()

        # use set_design
        self.design = None  # type: DesignBase

        # UIs
        self.plot_win = None # type: QMainWindowPlot
        self.elements_win = None # type: ElementsWindow

        self._setup_component_widget()
        self._setup_plot_widget()
        self._setup_design_components_widget()
        self._setup_elements_widget()

        # Show
        self.main_window.show()

        if design:
            self.set_design(design)

    def set_design(self, design: DesignBase):
        """Core function to set a new design.

        Args:
            design (DesignBase): A qiskit metal design, such as a planar one.
                The design contains all components and elements
        """
        self.design = design
        self.plot_win.set_design(design)
        self.elements_win.force_refresh()

        # Refresh
        self.refresh()

    def refresh_design(self):
        """Refresh design properties associated with the GUI.
        """
        self.update_design_name()

    def update_design_name(self):
        if self.design:
            design_name = self.design.get_design_name()
            self.main_window.setWindowTitle(
                self.config.main_window.title + f' — {design_name}'
            )

    def _ui_adjustments(self):
        """Any touchups to the loaded ui that need be done soon
        """

        # LoggingWindowWidget
        self.ui.log_text.img_path = Path(self.path_imgs)
        # self.ui.log_text.setup_menu()
        # self.ui.log_text.wellcome_message()

        # tabify - left
        self.main_window.tabifyDockWidget(self.ui.dockDesign, self.ui.dockNewComponent)
        self.main_window.tabifyDockWidget(self.ui.dockNewComponent, self.ui.dockConnectors)
        self.ui.dockDesign.raise_()

        # Add a second label to the status bar
        status_bar = self.main_window.statusBar()
        self.statusbar_label = QLabel(status_bar)
        self.statusbar_label.setText('')
        status_bar.addWidget(self.statusbar_label)

        # Elements button
        #self._set_element_tab = _set_element_tab
        # self.ui.actionElements.toggled.connect(self._set_element_tab)

    def _set_element_tab(self, yesno: bool):
        if yesno:
            self.ui.tabWidget.setCurrentWidget(self.ui.tabElements)
        else:
            self.ui.tabWidget.setCurrentWidget(self.ui.mainViewTab)

    def _setup_component_widget(self):
        self.ui.component_tab.ui = Ui_ComponentWidget()
        self.ui.component_tab.ui.setupUi(self.ui.component_tab)

    def _setup_plot_widget(self):
        """ Create main Window Widget Plot """
        self.plot_win = QMainWindowPlot(self, self.main_window)

        # Add to the tabbed main view
        self.ui.mainViewTab.layout().addWidget(self.plot_win)

    def _setup_elements_widget(self):
        """ Create main Window Elemetns  Widget """
        self.elements_win = ElementsWindow(self, self.main_window)

        # Add to the tabbed main view
        self.ui.tabElements.layout().addWidget(self.elements_win)


    def _setup_design_components_widget(self):
        model = ComponentsTableModel(self, logger=self.logger)
        self.ui.tableComponents.setModel(model)

    ################################################
    # Ploting
    def get_axes(self, num:int=None):
        """Return access to the canvas axes.
        If num is specified, returns the n-th axis

        Args:
            num (int, optional):f num is specified, returns the n-th axis.
             Defaults to None.

        Returns:
            List[Axes] or Axes: of the canvas
        """
        axes = self.plot_win.canvas.axes
        if num is not None:
            axes = axes[num]
        return axes

    def get_figure(self):
        """Return axis to the figure of the canvas
        """
        return self.plot_win.canvas.figure

    def get_canvas(self) -> 'PlotCanvas':
        """Get access to the canvas that handles the figure
        and axes, and their main functions.

        Returns:
            PlotCanvas
        """
        return self.plot_win.canvas

    def refresh(self):
        '''Refreshes everything. Overkill in general.'''

        # Global level
        self.refresh_design()

        # Table models
        self.ui.tableComponents.model().refresh()
        # ...

        # Redraw plots
        self.plot_win.replot()
