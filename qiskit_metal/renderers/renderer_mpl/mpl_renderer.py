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
"""MPL Renderer."""
import logging
import random
import sys
from typing import TYPE_CHECKING, List

import matplotlib as mpl
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler
from .patch import PolygonPatch
from IPython.display import display
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.cbook import _OrderedSet
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox

from shapely.geometry import CAP_STYLE, JOIN_STYLE, LineString

from ... import Dict
from ...designs import QDesign
from .mpl_interaction import MplInteraction, PanAndZoom
from .mpl_toolbox import _axis_set_watermark_img, clear_axis, get_prop_cycle

from .. import config
if not config.is_building_docs():
    from ...toolbox_python.utility_functions import log_error_easy
    from qiskit_metal.toolbox_python.utility_functions import bad_fillet_idxs

if TYPE_CHECKING:
    from ..._gui.main_window import MetalGUI
    from ..._gui.widgets.plot_widget.plot_window import QMainWindowPlot
    from .mpl_canvas import PlotCanvas
    from qiskit_metal.elements.elements_handler import QGeometryTables

__all__ = ['QMplRenderer']

to_poly_patch = np.vectorize(PolygonPatch)


class QMplRenderer():
    """Matplotlib handle all rendering of an axis.
    The axis is given in the function render.
    Access:
        self = gui.canvas.metal_renderer
    """

    def __init__(self, canvas: 'PlotCanvas', design: QDesign,
                 logger: logging.Logger):
        """
        Args:
            canvas (PlotCanvas): The canvas
            design (QDesign): The design
            logger (logging.Logger): The logger
        """
        super().__init__()
        self.logger = logger
        self.canvas = canvas
        self.ax = None
        self.design = design
        self.options = Dict(resolution='16',)

        # Filter view options
        self.hidden_layers = set()

        # Set of component ids which are integers.
        self._hidden_components = set()

        self.colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
            '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]

        self.set_design(design)

    def get_color_num(self, num: int) -> str:
        """Get the color from the given number.
        Args:
            num (int): number
        Return:
            str: color
        """
        return self.colors[num % len(self.colors)]

    def hide_component(self, name):
        """Hide the component with the given name.
        Args:
            name (str): Component name
        """
        comp_id = self.design.components[name].id
        self._hidden_components.add(comp_id)

    def show_component(self, name):
        """Show the component with the given name.
        Args:
            name (str): Component name
        """
        comp_id = self.design.components[name].id
        self._hidden_components.discard(name)

    def hide_layer(self, name):
        """Hide the layer with the given name.
        Args:
            name (str): Layer name
        """
        self.hidden_layers.add(name)

    def show_layer(self, name):
        """Show the layer with the given name.
        Args:
            name (str): Layer name
        """
        self.hidden_layers.discard(name)

    def set_design(self, design: QDesign):
        """Set the design.
        Args:
            design (QDesign): The design
        """
        self.design = design
        self.clear_options()
        # TODO

    def clear_options(self):
        """Clear all options."""
        self._hidden_components.clear()
        self.hidden_layers.clear()

    def render(self, ax: Axes):
        """Assumes that the axis has been cleared already and so on.
        Args:
            ax (matplotlib.axes.Axes): mpl axis to draw on
        """

        self.logger.debug('Rendering element tables to plot window.')
        self.render_tables(ax)

    def get_mask(self, table: pd.DataFrame) -> pd.Series:
        """Gets the mask.
        Args:
            table (pd.DataFrame): dataframe
        Returns:
            pd.Series: return pandas index series with boolen mask
            - i.e., which are not hidden or otherwise
        """

        # TODO: Ideally these should be replaced with interface functions,
        # not direct access to underlying internal representation

        mask = table.layer.isin(self.hidden_layers)
        mask = table.component.isin(self._hidden_components)

        return ~mask  # not

    def _render_poly_array(self, ax: Axes, poly_array: np.array, mpl_kw: dict):
        """Render the poly array.
        Args:
            ax (Axes): The axis
            poly_array (np.array): The poly
            mpl_kw (dict): The parameters dictionary
        """
        if len(poly_array) > 0:
            poly_array = to_poly_patch(poly_array)
            ax.add_collection(PatchCollection(poly_array, **mpl_kw))

    @property
    def qgeometry(self) -> 'QGeometryTables':
        """Return the qgeometry of the design."""
        return self.design.qgeometry

    # TODO: move to some config and user input also make widget
    styles = {
        'path': {
            'base': dict(linewidth=2, alpha=0.5),
            'subtracted':
                dict(),  # linestyle='--', edgecolors='k', color='gray'),
            'non-subtracted': dict()
        },
        'poly': {
            'base': dict(linewidth=1, alpha=0.5, edgecolors='k'),
            'subtracted': dict(linestyle='--', color='gray'),
            'non-subtracted': dict()
        },
        'JJ': {
            'base': dict(linewidth=1, alpha=0.2, edgecolors='k'),
            'subtracted': dict(linestyle='--', color='gray'),
            'non-subtracted': dict()
        }
    }
    """Styles"""

    def get_style(self,
                  element_type: str,
                  subtracted=False,
                  layer=None,
                  extra=None):
        """Get the style.
        Args:
            element_type (str): The type of element.
            subtracted (bool): True to subtract the key.  Defaults to False.
            layer (layer): The layer.  Defaults to None.
            extra (dict): Extra stuff to add.  Defaults to None.
        Return:
            dict: Style dictionary
        """
        # element_type - poly path
        extra = extra or {}

        key = 'subtracted' if subtracted else 'non-subtracted'

        kw = {
            **self.styles[element_type].get('base', {}),
            **self.styles[element_type].get(key, {}),
            **extra
        }

        # TODO: maybe pop keys that are invalid for line etc.
        # we could have a validation flag to validate for specific poly / path

        return kw

    def render_tables(self, ax: Axes):
        """Render the tables.
        Args:
            ax (Axes): The axes
        """
        for element_type, table in self.qgeometry.tables.items():
            # Mask the table
            table = table[self.get_mask(table)]

            # subtracted
            mask = table['subtract'] == True
            render_func = getattr(self, f'render_{element_type}')
            render_func(table[mask], ax, subtracted=True)

            # non-subtracted
            table1 = table[~mask]
            # TODO: do by layer and color
            # self.get_color_num()

            # TODO: Check that the function exists
            render_func = getattr(self, f'render_{element_type}')
            render_func(table1, ax, subtracted=False)

    def render_junction(self,
                        table: pd.DataFrame,
                        ax: Axes,
                        subtracted: bool = False,
                        extra_kw: dict = None):
        """Render a table of junction geometry.
        A junction is basically drawn like a path with finite width and no fillet.
        Args:
            table (DataFrame): Element table
            ax (matplotlib.axes.Axes): Axis to render on
            extra_kw (dict): Style params
        """
        if len(table) > 0:
            mask = (table.width == 0) | table.width.isna()
            table1 = table[~mask]
            if len(table1) > 0:
                table1.geometry = table1[['geometry', 'width']].apply(
                    lambda x: x[0].buffer(distance=float(x[1]) / 2.,
                                          cap_style=CAP_STYLE.flat,
                                          join_style=JOIN_STYLE.mitre,
                                          resolution=int(self.options[
                                              'resolution'])),
                    axis=1)
                kw = self.get_style('JJ', subtracted=subtracted, extra=extra_kw)
                self.render_poly(table1, ax, subtracted=subtracted, extra_kw=kw)
            table1 = table[mask]
            if len(table1) > 0:
                self.logger.warning(
                    'One or more junctions have zero width. Consider changing this.'
                )

    def render_poly(self,
                    table: pd.DataFrame,
                    ax: Axes,
                    subtracted: bool = False,
                    extra_kw: dict = None):
        """Render a table of poly geometry.
        Args:
            table (DataFrame): Element table
            ax (matplotlib.axes.Axes): Axis to render on
            kw (dict): Style params
        """
        if len(table) < 1:
            return

        kw = self.get_style('poly', subtracted=subtracted, extra=extra_kw)
        self._render_poly_array(ax, table.geometry, kw)

    def render_fillet(self, table):
        """Renders fillet path.
        Args:
            table (DataFrame): Table of elements with fillets
        Returns:
            DataFrame table with geometry field updated with a polygon filleted path.
        """
        table['geometry'] = table.apply(self.fillet_path, axis=1)
        return table

    def fillet_path(self, row):
        """Output the filleted path.
        Args:
            row (DataFrame): Row to fillet.
        Returns:
            Polygon of the new filleted path.
        """
        path = row["geometry"].coords
        if len(path) <= 2:  # only start and end points, no need to fillet
            return row["geometry"]
        newpath = np.array([path[0]])

        # Get list of vertices that can't be filleted
        no_fillet = bad_fillet_idxs(path, row["fillet"],
                                    self.design.template_options.PRECISION)

        # Iterate through every three-vertex corner
        for (i, (start, corner, end)) in enumerate(zip(path, path[1:],
                                                       path[2:])):
            if i + 1 in no_fillet:  # don't fillet this corner
                newpath = np.concatenate((newpath, np.array([corner])))
            else:
                fillet = self._calc_fillet(np.array(start), np.array(corner),
                                           np.array(end), row["fillet"],
                                           int(self.options['resolution']))
                if fillet is not False:
                    newpath = np.concatenate((newpath, fillet))
                else:
                    newpath = np.concatenate((newpath, np.array([corner])))
        newpath = np.concatenate((newpath, np.array([end])))
        return LineString(newpath)

    def _calc_fillet(self,
                     vertex_start,
                     vertex_corner,
                     vertex_end,
                     radius,
                     points=16):
        """Returns the filleted path based on the start, corner, and end
        vertices and the fillet radius.
        Args:
            vertex_start (np.ndarray): x-y coordinates of starting vertex.
            vertex_corner (np.ndarray): x-y coordinates of corner vertex.
            vertex_end (np.ndarray): x-y coordinates of end vertex.
            radius (float): Fillet radius.
            points (int): Number of points to draw in the fillet corner.
        """
        # Start, corner, and end vertices must be distinct
        if np.array_equal(vertex_start, vertex_corner) or np.array_equal(
                vertex_end, vertex_corner):
            return False

        # Vectors pointing from corner to start and end vertices, respectively
        # Also calculate their lengths and unit vectors
        sc_vec = vertex_start - vertex_corner
        ec_vec = vertex_end - vertex_corner
        sc_norm = np.linalg.norm(sc_vec)
        ec_norm = np.linalg.norm(ec_vec)
        sc_uvec = sc_vec / sc_norm
        ec_uvec = ec_vec / ec_norm

        # Angle between previous unit vectors
        end_angle = np.arccos(np.dot(sc_uvec, ec_uvec))

        # Start, corner, and end vertices can't be collinear
        if (end_angle == 0) or (end_angle == np.pi):
            return False

        # Fillet circle must be small enough to fit inside corner
        if radius / np.tan(end_angle / 2) > min(sc_norm, ec_norm):
            return False

        # Unit vector pointing from corner vertex to center of fillet circle
        net_uvec = (sc_uvec + ec_uvec) / np.linalg.norm(sc_uvec + ec_uvec)

        # Coordinates of center of fillet circle
        circle_center = vertex_corner + net_uvec * radius / np.sin(
            end_angle / 2)

        # Deltas represent displacement from corner vertex to circle center
        # Midpoint angle from circle center to corner, wrt to horizontal extending from former
        # Note: arctan is fine for angles in range (-pi / 2, pi / 2] but needs extra pi factor otherwise
        delta_x = vertex_corner[0] - circle_center[0]
        delta_y = vertex_corner[1] - circle_center[1]
        if delta_x:
            theta_mid = np.arctan(delta_y / delta_x) + np.pi * int(delta_x < 0)
        else:
            theta_mid = np.pi * ((1 - 2 * int(delta_y < 0)) + int(delta_y < 0))

        # Start and end sweep angles determined relative to midpoint angle
        # Swap them as needed to resolve ambiguity in arctan
        theta_start = theta_mid - (np.pi - end_angle) / 2
        theta_end = theta_mid + (np.pi - end_angle) / 2
        p1 = circle_center + radius * np.array(
            [np.cos(theta_start), np.sin(theta_start)])
        p2 = circle_center + radius * np.array(
            [np.cos(theta_end), np.sin(theta_end)])
        if np.linalg.norm(vertex_start - p2) < np.linalg.norm(vertex_start -
                                                              p1):
            theta_start, theta_end = theta_end, theta_start

        # Populate the fillet corner, skipping the start point since it's already added
        path = np.array([
            circle_center + radius * np.array(
                [np.cos(theta_start), np.sin(theta_start)])
        ])
        for theta in np.linspace(theta_start, theta_end, points)[1:]:
            path = np.concatenate(
                (path,
                 np.array([
                     circle_center + radius *
                     np.array([np.cos(theta), np.sin(theta)])
                 ])))
        return path

    def render_path(self,
                    table: pd.DataFrame,
                    ax: Axes,
                    subtracted: bool = False,
                    extra_kw: dict = None):
        """Render a table of path geometry.
        Args:
            table (DataFrame): Element table
            ax (matplotlib.axes.Axes): Axis to render on
            kw (dict): Style params
        """
        if len(table) < 1:
            return

        # mask for all non zero width paths
        # TODO: could there be a problem with float vs int here?
        mask = (table.width == 0) | table.width.isna()
        # print(f'subtracted={subtracted}\n\n')
        # display(table)
        # display(imask)

        # convert to polys - handle non zero width
        table1 = table[~mask]

        mask2 = (table1.fillet == 0)

        table2 = table1[~mask2]

        for index, row in table2[table2.fillet.notnull()].iterrows():
            table1.loc[index, 'geometry'] = self.fillet_path(row)

        if len(table1) > 0:
            table1.geometry = table1[['geometry', 'width']].apply(lambda x: x[
                0].buffer(distance=float(x[1]) / 2.,
                          cap_style=CAP_STYLE.flat,
                          join_style=JOIN_STYLE.mitre,
                          resolution=int(self.options['resolution'])),
                                                                  axis=1)

            kw = self.get_style('poly', subtracted=subtracted, extra=extra_kw)

            # render components
            self.render_poly(table1, ax, subtracted=subtracted, extra_kw=kw)

        # handle zero width
        table1 = table[mask]
        # best way to plot?
        # TODO: speed and vectorize?
        if len(table1) > 0:
            kw = self.get_style('path', subtracted=subtracted, extra=extra_kw)
            line_segments = LineCollection(table1.geometry)
            ax.add_collection(line_segments)


# DEFAULT['renderer_mpl'] = Dict(
#     annot_conectors=Dict(
#         ofst=[0.025, 0.025],
#         annotate_kw=dict(  # called by ax.annotate
#             color='r',
#             arrowprops=dict(color='r', shrink=0.1, width=0.05, headwidth=0.1)
#         ),
#         line_kw=dict(lw=2, c='r')
#     ),
# )

# class QRendererMPL(QRendererGui):
#     """
#     Renderer for matplotlib in a GUI environment.

#     TODO: How do we handle component selection, etc.
#     """
#     name = 'mpl'
#     element_extensions = dict()

#     def render_shapely(self, obj, kw=None):
#         # TODO: simplify, specialize, and update this function
#         # right now, this is just calling the V0.1 old style
#         render(obj, ax=self.ax, kw= {} or kw)

#     def render_connectors(self):
#         '''
#         Plots all connectors on the active axes. Draws the 1D line that
#         represents the "port" of a connector point. These are referenced for smart placement
#             of Metal components, such as when using functions like Metal_CPW_Connect.

#         TODO: add some filter for sense of what components are visible?
#               or on what chip the connectors are
#         '''

#         for name, conn in self.design.connectors.items():

#             line = LineString(conn.points)

#             self.render_shapely(line, kw=DEFAULT.annot_conectors.line_kw)

#             self.ax.annotate(name, xy=conn.middle[:2], xytext=conn.middle +
#                              np.array(DEFAULT.annot_conectors.ofst),
#                              **DEFAULT.annot_conectors.annotate_kw)
