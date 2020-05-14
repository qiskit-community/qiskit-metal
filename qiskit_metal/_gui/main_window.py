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
from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QFileDialog, QLabel, QMainWindow,
                             QMessageBox)

from PyQt5.QtCore import QEventLoop

#from ..toolbox_python._logging import setup_logger
#from .. import config, Dict
from ..designs.design_base import DesignBase
from ..toolbox_metal.import_export import load_metal_design
from ._handle_qt_messages import catch_exception_slot_pyqt
from .component_widget import ComponentWidget
from .component_widget_ui import Ui_ComponentWidget
from .elements_window import ElementsWindow
from .main_window_base import QMainWindowBaseHandler, QMainWindowExtensionBase
from .main_window_ui import Ui_MainWindow
from .plot_window import QMainWindowPlot
from .widgets.components_model import ComponentsTableModel
from .widgets.log_metal import LoggingHandlerForLogWidget


class QMainWindowExtension(QMainWindowExtensionBase):
    """This contains all the functions tthat the gui needs
    to call directly from the UI

    To access the GUI HAndler above this, call:
        self.handler = gui

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

    @property
    def gui(self) -> 'MetalGUI':
        return self.handler

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
            self.design.delete_all_components()
            self.gui.component_window.set_component(None)
            self.gui.refresh()

    @catch_exception_slot_pyqt()
    def save_design_as(self, _=None):
        filename = QFileDialog.getSaveFileName(None,
                                               'Select a new locaiton to save Metal design to',
                                               self.design.get_design_name() + '.metal',
                                               initialFilter='*.metal')[0]

        if filename:
            self.gui.save_file(filename)

    @catch_exception_slot_pyqt()
    def save_design(self, _=None):
        """
        Handles click on save design
        """
        if self.design:
            if self.design.save_path:
                self.gui.save_file()
            else:
                self.save_design_as()
        else:
            self.logger.info('No design present.')
            QMessageBox.warning(self,'Warning','No design present! Can''t save')

    @catch_exception_slot_pyqt()
    def load_design(self, _):
        """
        Handles click on loading metal design
        """
        filename = QFileDialog.getOpenFileName(None,
                                               'Select locaiton to load Metal design from',
                                               initialFilter='*.metal')[0]
        if filename:
            self.logger.info(f'Attempting to load design file {filename}')
            design = load_metal_design(filename)
            self.logger.info(
                f'Successfully loaded file. Now setting design into gui.')
            self.handler.set_design(design)
            self.logger.info(f'Successfully set design. Loaded and done.')

    @catch_exception_slot_pyqt()
    def full_refresh(self, _):
        self.logger.info(
            f'Force refresh of all widgets (does not rebuild components)...')
        self.gui.refresh()

    @catch_exception_slot_pyqt()
    def rebuild(self, _):
        self.logger.info(
            f'Rebuilding all components in the model (and refreshing widgets)...')
        self.gui.rebuild()


class MetalGUI(QMainWindowBaseHandler):
    """Qiskit Metal Main GUI.

    Args:
        QMainWindowBase ([type]): [description]
    """

    __UI__ = Ui_MainWindow
    _QMainWindowClass = QMainWindowExtension
    _img_logo_name = 'metal_logo.png'
    _stylesheet_default = 'metal_dark'

    _dock_names = [
        'dockComponent',
        'dockConnectors',
        'dockDesign',
        'dockLog',
        'dockNewComponent']

    def __init__(self, design: DesignBase = None):
        """Init

        Args:
            design (DesignBase, optional): Pass in the design that the GUI should handle.
                Defaults to None.
        """

        super().__init__()

        # use set_design
        self.design = None  # type: DesignBase

        # UIs
        self.plot_win = None  # type: QMainWindowPlot
        self.elements_win = None  # type: ElementsWindow

        self._setup_component_widget()
        self._setup_plot_widget()
        self._setup_design_components_widget()
        self._setup_elements_widget()

        # Show and raise
        self.main_window.show()
        # self.qApp.processEvents(QEventLoop.AllEvents, 1)
        # - don't think I need this here, it doesn't help to show and raise
        # - need to call from different thread.
        QTimer.singleShot(150, self.main_window.raise_)

        if design:
            self.set_design(design)
        else:
            self._set_enabled_design_widgets(False)

    def _set_enabled_design_widgets(self, enabled: bool = True):
        """make rebuild and all the other main button disabled.

        Keyword Arguments:
            enabled {bool} -- [description] (default: {True})
        """
        def setEnabled(parent, widgets):
            for widgetname in widgets:
                if hasattr(parent, widgetname):
                    widget = getattr(parent, widgetname)  # type: QWidget
                    widget.setEnabled(enabled)
                else:
                    self.logger.error(f'GUI issue: wrong name: {widgetname}')

        widgets = ['actionSave', 'action_full_refresh', 'actionRebuild', 'actionDelete_All',
                   'dockComponent', 'dockNewComponent', 'dockDesign', 'dockConnectors']
        setEnabled(self.ui, widgets)

        widgets = ['component_window', 'elements_win']
        setEnabled(self, widgets)

    def set_design(self, design: DesignBase):
        """Core function to set a new design.

        Args:
            design (DesignBase): A qiskit metal design, such as a planar one.
                The design contains all components and elements
        """
        self.design = design

        self._set_enabled_design_widgets(True)

        self.plot_win.set_design(design)
        self.elements_win.force_refresh()

        # Refresh
        self.refresh()

    def _setup_logger(self):
        super()._setup_logger()

        if 1:  # add the metal logger to the gui
            logger_name = 'metal'
            self.ui.log_text.add_logger(logger_name)
            self._log_handler_design = LoggingHandlerForLogWidget(
                logger_name, self, self.ui.log_text)

            logger = logging.getLogger(logger_name)
            logger.addHandler(self._log_handler_design)

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

        # Add a second label to the status bar
        status_bar = self.main_window.statusBar()
        self.statusbar_label = QLabel(status_bar)
        self.statusbar_label.setText('')
        status_bar.addWidget(self.statusbar_label)

        ### Docks
        # Left handside
        self.main_window.splitDockWidget(self.ui.dockDesign, self.ui.dockComponent, Qt.Vertical)
        self.main_window.tabifyDockWidget(self.ui.dockDesign, self.ui.dockNewComponent)
        self.main_window.tabifyDockWidget(self.ui.dockNewComponent, self.ui.dockConnectors)
        self.ui.dockDesign.raise_()
        self.main_window.resizeDocks({self.ui.dockDesign}, {350}, Qt.Horizontal)

        # Log
        self.main_window.resizeDocks({self.ui.dockLog}, {120}, Qt.Vertical)

    def _set_element_tab(self, yesno: bool):
        if yesno:
            self.ui.tabWidget.setCurrentWidget(self.ui.tabElements)
        else:
            self.ui.tabWidget.setCurrentWidget(self.ui.mainViewTab)

    def _setup_component_widget(self):
        self.component_window = ComponentWidget(self, self.ui.dockComponent)
        self.ui.dockComponent.setWidget(self.component_window)

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
        """
        Design components.

        Table model that shows the summary of the components of a design in a table
        with their names, classes, and modules
        """
        model = ComponentsTableModel(self, logger=self.logger)
        self.ui.tableComponents.setModel(model)

    ################################################
    # Ploting
    def get_axes(self, num: int = None):
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

    def rebuild(self, autoscale:bool=True):
        """Rebuild all components in the design from scratch and refresh the gui.
        """
        self.design.rebuild()
        self.refresh()
        if autoscale:
            self.autoscale()

    def refresh(self):
        '''Refreshes everything. Overkill in general.
        * Refreshes the design names in the gui
        * Refreshes the table models
        * Replots everything

        Warning: This does *not* rebuild the components.
        For that, call rebuild. rebuild will also
        '''

        # Global level
        self.refresh_design()

        # Table models
        self.ui.tableComponents.model().refresh()

        # Redraw plots
        self.refresh_plot()

    def refresh_plot(self):
        """Redraw only the plot window contents."""
        self.plot_win.replot()

    def set_component(self, name: str):
        """Set the component to be exmained by the compoennt widget.

        Arguments:
            name {str} -- name of component to exmaine.
        """
        self.ui.dockComponent.setWindowTitle(f'Component: {name}')
        self.component_window.set_component(name)

    def autoscale(self):
        """Shorcut to autoscale all views"""
        self.plot_win.auto_scale()

    def save_file(self, filename:str=None):
        self.design.save_design(filename)