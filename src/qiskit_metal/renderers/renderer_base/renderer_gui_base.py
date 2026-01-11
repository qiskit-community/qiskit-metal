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
"""QRendererGui Base."""

from qiskit_metal.designs import QDesign, is_design
from qiskit_metal.qgeometries import QGeometryTables

from qiskit_metal.renderers.renderer_base import QRenderer

__all__ = ['QRendererGui']


class QRendererGui(QRenderer):
    """Abstract base class for the GUI rendering.

    Extends `QRenderer`. An interface class.
    """

    name = 'guibase'  # overwrite this!
    """Name"""

    def __init__(self, gui, design: QDesign, initiate=True, fig=None, ax=None):
        """
        Args:
            gui (MetalGUI): the GUI.
            design (QDesign): The design.
            initiate (bool): True to initiate the renderer.  Defaults to True.
            fig (figure): current figure.  Defaults to None.
            ax (ax): current ax.  Defaults to None.
        """
        super().__init__(design=design, initiate=initiate)

        self.gui = gui
        self.fig = None  # current figure
        self.ax = None  # current ax

    def set_fig(self, fig):
        """Set the given figure.

        Args:
            fig (figure): Figure to set
        """
        self.fig = fig

    def set_ax(self, ax):
        """Set the given ax.

        Args:
            ax (ax): ax to set
        """
        self.ax = ax

    def setup_fig(self, fig):
        """Setup the given figure.

        Args:
            fig (figure): figure to setup

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()

    def style_axis(self, ax):
        """Style the axis.

        Args:
            ax (ax): ax to style

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()

    def render_design(self, selection=None):
        """Render the design.

        Args:
            selection (selection): Not used
        """
        # TOOD: handle selection
        for _, component in self.design.components.items():
            self.render_component(component)

    def render_component(self, component):
        """Render the given component.

        Args:
            component (QComponent): the component

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()

    def render_shapely(self):
        """Render shapely.

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()

    def render_connectors(self):
        """Render connectors.

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()

    def clear_axis(self):
        """Clear the axis.

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()

    def clear_figure(self):
        """Clear  the figure.

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()
