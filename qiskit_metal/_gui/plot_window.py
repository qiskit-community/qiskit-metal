"""Main module that handles the entier plot window which is docked inside the mmain window.
This can be undocked and can have its own toolbar. this is largley why i ddecied to use a
QMainWindow, so that we can have inner docking and toolbars available.
@author: Zlatko Minev
@date: 2020
"""

from typing import TYPE_CHECKING

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QApplication, QFileDialog, QLabel, QMainWindow,
                             QMessageBox)

from ..renderers.renderer_mpl.mpl_canvas import PlotCanvas
from .plot_window_ui import Ui_MainWindowPlot

if TYPE_CHECKING:
    # https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
    from .main_window import MetalGUI, QMainWindowExtension

class QMainWindowPlot(QMainWindow):
    """
    This is just a handler (container) for the UI; it a child object of the main gui.

    PyQt5 Signal / Slots Extensions:
        The UI can call up to this class to execeute button clicks for instance
        Extensiosn in qt designer on signals/slots are linked to this class

    Core canvas plot widget:
        canvas: The core plot object. Can be mpl or any other renderer.
    """

    def __init__(self, gui: 'MetalGUI', parent_window: 'QMainWindowExtension'):
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
        # Core object -- the center of this entire widget
        self.canvas = PlotCanvas(self.design, self, logger=self.logger,
                                 statusbar_label=self.statusbar_label)

        self.ui.centralwidget.layout().addWidget(self.canvas)

    def set_design(self, design):
        self.canvas.set_design(design)

    @property
    def design(self):
        return self.gui.design

    def replot(self):
        self.logger.info("Force replot")
        self.canvas.plot()

    def auto_scale(self):
        self.logger.debug("Autoscale")
        self.canvas.auto_scale()

    def pan(self):
        QMessageBox.about(self, "Pan", """Navigation help:

Pan:
(click and drag)
Click and drag the plot screen.

Zoom:
(scroll, or right click and drag)
Either use the mouse middle wheel to zoom in and out by scrolling,
or use the right click and drag to select a region.""")

    def zoom(self):
        QMessageBox.about(self, "Zoom", "Either use the mouse middle wheel"\
            " to zoom in and out by scrolling, or use the right click and"\
            " drag to select a region.")

    def set_position_track(self, yesno: bool):
        if yesno:
            self.logger.info("Click a point in the plot window to see"\
                " its coordinate.")
        self.canvas.panzoom.options.report_point_position = yesno

    def set_show_connectors(self,  yesno: bool):
        self.logger.info(f"Showing connectors: {yesno}")
        # TODO:
