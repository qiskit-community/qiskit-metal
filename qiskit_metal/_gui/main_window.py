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

from .. import config, Dict
from ..designs.design_base import DesignBase
from ..renderers.renderer_mpl.mpl_canvas import PlotCanvas
from ..toolbox_python._logging import setup_logger
from ..toolbox_metal.import_export import load_metal_design
from ._handle_qt_messages import catch_exception_slot_pyqt
from .component_widget_ui import Ui_ComponentWidget
from .main_window_base import QMainWindowBaseHandler, QMainWindowExtensionBase
from .main_window_ui import Ui_MainWindow
from .plot_window_ui import Ui_MainWindowPlot
from .widgets.components_model import ComponentsTableModel
from .widgets.log_metal import LoggingHandlerForLogWidget


class QMainWindowExtension(QMainWindowExtensionBase):
    """This contains all the functions tthat the gui needs
    to call directly from the UI

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
        self.design = None  # use set_design

        # UIs
        self.ui_plot = None
        self.plot_win = None

        self._setup_component_widget()
        self._setup_plot_widget()
        self._setup_design_components_widget()

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

        # TODO: Set for all
        self.ui.tableComponents.model().set_design(design)

        # Refresh
        self.refresh_design()

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

    def _setup_design_components_widget(self):
        model = ComponentsTableModel(self.design, logger=self.logger)
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

    def get_canvas(self):
        """Get access to the canvas that handles the figure
        and axes, and their main functions.

        Returns:
            PlotCanvas
        """
        return self.plot_win.canvas

    ################################################
    # ...


# TODO: Move to its own file
class QMainWindowPlot(QMainWindow):

    def __init__(self, gui: MetalGUI, parent_window: QMainWindowExtension):
        # Q Main WIndow
        super().__init__(parent_window)

        # Parent GUI related
        self.gui = gui
        self.logger = gui.logger
        self.statusbar_label = gui.statusbar_label

        # UI
        self.ui = Ui_MainWindowPlot()
        self.ui.setupUi(self)

        self.statusBar().hide()

        # Add MPL plot widget to window
        self.canvas = PlotCanvas(self, logger=self.logger,
                                 statusbar_label=self.statusbar_label)
        self.ui.centralwidget.layout().addWidget(self.canvas)

    def replot(self):
        self.logger.info("Force replot")
        pass

    def auto_scale(self):
        # self.ui.actionAuto.triggered.connect(self.auto_scale)
        self.logger.info("Autoscale")
        self.canvas.auto_scale()

    def pan(self):
        QMessageBox.about(self, "Pan", "Click and drag the plot screen.")

    def zoom(self):
        QMessageBox.about(self, "Zoom", "Either use the mouse middle wheel'\
            'to zoom in and out by scrolling, or use the right click and'\
            'drag to select a region.")

    def set_position_track(self, yesno: bool):
        if yesno:
            self.logger.info("Click a point in the plot window to see'\
                'its coordinate.")
        self.canvas.panzoom.options.report_point_position = yesno

    def set_show_connectors(self,  yesno: bool):
        self.logger.info(f"Showing connectors: {yesno}")
        # TODO:
