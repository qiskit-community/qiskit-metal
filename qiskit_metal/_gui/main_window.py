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

#import sys
from .widgets.log_metal import LoggingHandlerForLogWidget
from .plot_window_ui import Ui_MainWindowPlot as MainWindowPlot
from .main_window_ui import Ui_MainWindow
from .main_window_base import QMainWindowBaseHandler
from .component_widget_ui import Ui_ComponentWidget
from ._handle_qt_messages import catch_exception_slot_pyqt
from ..toolbox_python._logging import setup_logger
from ..renderers.renderer_mpl.mpl_canvas import PlotCanvas
from ..designs.design_base import DesignBase
from .. import config
import logging
import os
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLabel


class QMainWindowExtension(QMainWindow):

    def _set_element_tab(self, yesno):
        print(yesno)
        print("self if: ", self)
        if yesno:
            self.ui.tabWidget.setCurrentWidget(self.ui.tabElements)
            self.ui.actionElements.setText("View")
        else:
            self.ui.tabWidget.setCurrentWidget(self.ui.mainViewTab)
            self.ui.actionElements.setText("Elements")


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

    def __init__(self):

        super().__init__()

        # UIs
        self.ui_plot = None
        self.ui_plot_win = None

        self._setup_component_widget()
        self._setup_plot_widget()

        # Design
        self.design = None  # use set_design
        self.main_window.show()

    def set_design(self, design: DesignBase):
        """Core function to set a new design

        Args:
            design ([type]): [description]
        """
        self.design = design
        # TODO:

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
        self._statusbar_label2 = QLabel(status_bar)
        self._statusbar_label2.setText('')
        status_bar.addWidget(self._statusbar_label2)

        # Elements button
        #self._set_element_tab = _set_element_tab
        #self.ui.actionElements.toggled.connect(self._set_element_tab)

    def _set_element_tab(self, yesno:bool):
        if yesno:
            self.ui.tabWidget.setCurrentWidget(self.ui.tabElements)
        else:
            self.ui.tabWidget.setCurrentWidget(self.ui.mainViewTab)

    def _setup_component_widget(self):
        self.ui.component_tab.ui = Ui_ComponentWidget()
        self.ui.component_tab.ui.setupUi(self.ui.component_tab)

    def _setup_plot_widget(self):
        """ Create main Window Widget Plot """
        # Create the Widget Main Window
        self.ui_plot_win = QMainWindow(self.main_window)
        self.ui_plot = MainWindowPlot()
        self.ui_plot.setupUi(self.ui_plot_win)

        self.ui.mainViewTab.layout().addWidget(self.ui_plot_win)

        # Add plot widget to window
        # This should probably be a class to handle this window
        # -- extend the window and superclass
        self.plot_canvas = PlotCanvas(self.ui_plot_win)
        self.ui_plot.centralwidget.layout().addWidget(self.plot_canvas)
        self.ui_plot_win.statusBar().hide()

        # Plot canvas
        self.plot_canvas.logger = self.logger
        self.plot_canvas.panzoom.logger = self.logger
        self.plot_canvas.panzoom._statusbar_label = self._statusbar_label2

        # Clicks

        # Autoscale
        self.ui_plot.actionAuto.triggered.connect(self.plot_canvas.auto_scale)

        # Pan
        self.ui_plot.actionPan._clicked = lambda: QMessageBox.about(
            self.ui_plot_win, "Pan", "Click and drag the plot screen.")
        self.ui_plot.actionPan.triggered.connect(
            self.ui_plot.actionPan._clicked)

        # Zooom
        self.ui_plot.actionZoom._clicked = lambda: QMessageBox.about(
            self.ui_plot_win, "Zoom", "Either use the mouse middle wheel\
 to zoom in and out by scrolling, or use the right click and drag to select a region.")
        self.ui_plot.actionZoom.triggered.connect(
            self.ui_plot.actionZoom._clicked)

        # Position
        def set_pz_point_pos(yesno: bool):
            if yesno:
                self.logger.info("Click a point in the plot window to see its coordinate.")
            self.plot_canvas.panzoom.options.report_point_position = yesno
        self.set_pz_point_pos = set_pz_point_pos
        self.ui_plot.actionCoords.toggled.connect(set_pz_point_pos)
