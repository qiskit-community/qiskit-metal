# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Main module that handles the entier plot window which is docked inside the
main window.

This can be undocked and can have its own toolbar. this is largley why I
decided to use a QMainWindow, so that we can have inner docking and
toolbars available.
"""

from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from PySide6.QtWidgets import (QApplication, QFileDialog, QLabel, QMainWindow,
                               QMessageBox)

from qiskit_metal import config
if not config.is_building_docs():
    # Only import PlotCanvas if the docs are NOT being built
    from qiskit_metal.renderers.renderer_mpl.mpl_canvas import PlotCanvas

from qiskit_metal._gui.plot_window_ui import Ui_MainWindowPlot

if TYPE_CHECKING:
    # https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
    from ...main_window import MetalGUI, QMainWindowExtension


class QMainWindowPlot(QMainWindow):
    """This is just a handler (container) for the UI; it a child object of the
    main gui.

    Extends the `QMainWindow` class

    PySide2 Signal / Slots Extensions:
        The UI can call up to this class to execeute button clicks for instance
        Extensiosn in qt designer on signals/slots are linked to this class

    Core canvas plot widget:
        canvas: The core plot object. Can be mpl or any other renderer.
    """

    def __init__(self, gui: 'MetalGUI', parent_window: 'QMainWindowExtension'):
        """
        Args:
            gui (MetalGUI): The GUI
            parent_window (QMainWindowExtension): Parent window
        """
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
        self.canvas = PlotCanvas(self.design,
                                 self,
                                 logger=self.logger,
                                 statusbar_label=self.statusbar_label)

        self.ui.centralwidget.layout().addWidget(self.canvas)

    def set_design(self, design):
        """Set the design.

        Args:
            design (QDesign): Design to set the canvas to
        """
        self.canvas.set_design(design)

    @property
    def design(self):
        """Returns the design."""
        return self.gui.design

    def replot(self):
        """Tells the canvas to replot."""
        # self.logger.debug("Force replot")
        self.canvas.plot()

    def auto_scale(self):
        """Tells the canvas to perform an automatic scale."""
        self.logger.debug("Autoscale")
        self.canvas.auto_scale()

    def pan(self):
        """Displays a message about how to pan."""
        QMessageBox.about(
            self, "Pan", """Navigation help:

Pan:
(click and drag)
Click and drag the plot screen.

Zoom:
(scroll, or right click and drag)
Either use the mouse middle wheel to zoom in and out by scrolling,
or use the right click and drag to select a region.""")

    def zoom(self):
        """Displays a message about how to zoom."""
        QMessageBox.about(
            self, "Zoom", "Either use the mouse middle wheel"
            " to zoom in and out by scrolling, or use the right click and"
            " drag to select a region.")

    def set_position_track(self, yesno: bool):
        """Set the position tracker.

        Args:
            yesno (bool): Whether or not to display instructions
        """
        if yesno:
            self.logger.info("Click a point in the plot window to see"
                             " its coordinate.")
        self.canvas.panzoom.options.report_point_position = yesno

    def set_show_pins(self, yesno: bool):
        """Displays on the logger whether or not pins are showing.

        Args:
            yesno (bool): Whether or not to show pins
        """
        self.logger.info(f"Showing pins: {yesno}")
