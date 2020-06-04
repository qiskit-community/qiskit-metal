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
from typing import List

from PyQt5 import QtWidgets
from PyQt5.QtCore import QEventLoop, Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QDockWidget, QFileDialog, QLabel,
                             QMainWindow, QMessageBox)

from ..designs.design_base import QDesign
from ..toolbox_metal.import_export import load_metal_design
from .component_widget_ui import Ui_ComponentWidget
from .elements_window import ElementsWindow
from .main_window_base import QMainWindowBaseHandler, QMainWindowExtensionBase
from .main_window_ui import Ui_MainWindow
from .widgets.plot_widget.plot_window import QMainWindowPlot
from .utility._handle_qt_messages import catch_exception_slot_pyqt
from .widgets.all_components.table_model_all_components import \
    QTableModel_AllComponents
from .widgets.edit_component.component_widget import ComponentWidget
from .widgets.log_widget.log_metal import LogHandler_for_QTextLog
from .widgets.variable_table import PropertyTableWidget


class QMainWindowExtension(QMainWindowExtensionBase):
    """This contains all the functions tthat the gui needs
    to call directly from the UI

    To access the GUI HAndler above this, call:
        self.handler = gui

    Args:
        QMainWindow ([type]): [description]
    """

    @property
    def design(self) -> QDesign:
        """Return the design.

        Returns:
            QDesign: [description]
        """
        return self.handler.design

    @property
    def gui(self) -> 'MetalGUI':
        return self.handler

    def _set_element_tab(self, yesno:bool):
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

    # This is somewhat outdated
    _dock_names = [
        'dockComponent',
        'dockConnectors',
        'dockDesign',
        'dockLog',
        'dockNewComponent',
        'dockVariables']

    def __init__(self, design: QDesign = None):
        """Init

        Args:
            design (QDesign, optional): Pass in the design that the GUI should handle.
                Defaults to None.
        """

        super().__init__()

        # use set_design
        self.design = None  # type: QDesign

        # UIs
        self.plot_win = None  # type: QMainWindowPlot
        self.elements_win = None  # type: ElementsWindow
        self.component_window = ComponentWidget(self, self.ui.dockComponent)
        self.variables_window = PropertyTableWidget(self, gui = self)

        self._setup_component_widget()
        self._setup_plot_widget()
        self._setup_design_components_widget()
        self._setup_elements_widget()
        self._setup_variables_widget()
        self._ui_adjustments_final()

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

    def set_design(self, design: QDesign):
        """Core function to set a new design.

        Args:
            design (QDesign): A qiskit metal design, such as a planar one.
                The design contains all components and elements
        """
        self.design = design

        self._set_enabled_design_widgets(True)

        self.plot_win.set_design(design)
        self.elements_win.force_refresh()

        self.variables_window.set_design(design)

        # Refresh
        self.refresh()

    def _setup_logger(self):
        super()._setup_logger()

        logger = logging.getLogger('metal')
        self._log_handler_design = self.create_log_handler('metal', logger)

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
        # QTextEditLogger
        self.ui.log_text.img_path = Path(self.path_imgs)
        self.ui.log_text.dock_window = self.ui.dockLog

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
        self.main_window.tabifyDockWidget(self.ui.dockConnectors, self.ui.dockVariables)
        self.ui.dockDesign.raise_()
        self.main_window.resizeDocks({self.ui.dockDesign}, {350}, Qt.Horizontal)

        # Log
        self.ui.dockLog.parent().resizeDocks({self.ui.dockLog}, {120}, Qt.Vertical)

        # Tab positions
        self.ui.tabWidget.setCurrentIndex(0)

    def _ui_adjustments_final(self):
        """Any touchups to the loaded ui that need be done after all the base and main ui is loaded"""
        self.component_window.setCurrentIndex(0)


    def _set_element_tab(self, yesno: bool):
        if yesno:
            self.ui.tabWidget.setCurrentWidget(self.ui.tabElements)
        else:
            self.ui.tabWidget.setCurrentWidget(self.ui.mainViewTab)

    def _setup_component_widget(self):
        self.ui.dockComponent.setWidget(self.component_window)

    def _setup_variables_widget(self):
        self.ui.dockVariables.setWidget(self.variables_window)

    def _setup_plot_widget(self):
        """ Create main Window Widget Plot """
        self.plot_win = QMainWindowPlot(self, self.main_window)

        # Add to the tabbed main view
        self.ui.mainViewTab.layout().addWidget(self.plot_win)

        # Move the dock
        self._move_dock_to_new_parent(self.ui.dockLog, self.plot_win)
        self.ui.dockLog.parent().resizeDocks({self.ui.dockLog}, {120}, Qt.Vertical)

    def _move_dock_to_new_parent(self, dock: QDockWidget,
                                 new_parent: QMainWindow,
                                 dock_location=Qt.BottomDockWidgetArea):
        dock.setParent(new_parent)
        new_parent.addDockWidget(dock_location, dock)
        dock.setFloating(False)
        dock.show()
        dock.setMaximumHeight(99999)

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
        model = QTableModel_AllComponents(self, logger=self.logger,
                 tableView = self.ui.tableComponents)
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

    @property
    def axes(self)-> List['Axes']:
        return self.plot_win.canvas.axes

    @property
    def figure(self):
        """Return axis to the figure of the canvas
        """
        return self.plot_win.canvas.figure

    @property
    def canvas(self) -> 'PlotCanvas':
        """Get access to the canvas that handles the figure
        and axes, and their main functions.

        Returns:
            PlotCanvas
        """
        return self.plot_win.canvas

    def rebuild(self, autoscale:bool=False):
        """Rebuild all components in the design from scratch and refresh the gui.
        """
        self.design.rebuild()
        self.refresh()
        if autoscale:
            self.autoscale()

    def refresh(self):
        '''
        Refreshes everything. Overkill in general.
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
        self.component_window.set_component(name)

    def autoscale(self):
        """Shorcut to autoscale all views"""
        self.plot_win.auto_scale()

    def save_file(self, filename:str=None):
        self.design.save_design(filename)

    def highlight_components(self, component_names:List[str]):
        """Hihglight a list of components

        Args:
            component_names (List[str]): [description]
        """
        self.canvas.highlight_components(component_names)
