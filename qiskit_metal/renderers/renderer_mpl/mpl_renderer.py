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
@auhtor: Zlatko Minev
@date: 2019
"""
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
from descartes import PolygonPatch
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
from ...toolbox_python.utility_functions import log_error_easy
from ..renderer_base.renderer_gui_base import QRendererGui
from .mpl_interaction import MplInteraction, PanAndZoom
from .mpl_toolbox import _axis_set_watermark_img, clear_axis, get_prop_cycle

if TYPE_CHECKING:
    from ..._gui.main_window import MetalGUI
    from ..._gui.widgets.plot_widget.plot_window import QMainWindowPlot
    from .mpl_canvas import PlotCanvas



__all__ = ['QMplRenderer']


to_poly_patch = np.vectorize(PolygonPatch)

# TODO: subclass from QRendererGui - define QRendererGui from this class as interface class
class QMplRenderer():
    """
    Matplotlib handle all rendering of an axis.

    The axis is given in the function render.

    Access:
        self = gui.canvas.metal_renderer
    """

    def __init__(self, canvas: 'PlotCanvas', design: QDesign, logger: logging.Logger):
        super().__init__()
        self.logger = logger
        self.canvas = canvas
        self.ax = None
        self.design = design

        # Filter view options
        self.hidden_layers = set()
        self.hidden_components = set()

        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
                       '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

        self.set_design(design)

    def get_color_num(self, num: int) -> str:
        return self.colors[num % len(self.colors)]

    def hide_component(self, name):
        self.hidden_components.add(name)

    def show_component(self, name):
        self.hidden_components.discard(name)

    def hide_layer(self, name):
        self.hidden_layers.add(name)

    def show_layer(self, name):
        self.hidden_layers.discard(name)

    def set_design(self, design: QDesign):
        self.design = design
        self.clear_options()
        # TODO

    def clear_options(self):
        self.hidden_components.clear()
        self.hidden_layers.clear()

    def render(self, ax: Axes):
        """Assumes that the axis has been cleared already and so on.

        Arguments:
            ax {matplotlib.axes.Axes} -- mpl axis to draw on
        """

        self.logger.debug('Rendering element tables to plot window.')
        self.render_tables(ax)

    def get_mask(self, table: pd.DataFrame) -> pd.Series:
        '''
        return pandas index series with boolen mask
        - i.e., which are not hidden or otherwise
        '''

        # TODO: Ideally these should be replaced with interface functions,
        # not direct access to undelying internal representation

        mask = table.layer.isin(self.hidden_layers)
        mask = table.component.isin(self.hidden_components)

        return ~mask  # not

    def _render_poly_array(self, ax: Axes, poly_array: np.array,
                           mpl_kw: dict):
        if len(poly_array) > 0:
            poly_array = to_poly_patch(poly_array)
            ax.add_collection(PatchCollection(poly_array, **mpl_kw))

    @property
    def elements(self) -> 'ElementHandler':
        return self.design.elements

    # TODO: move to some config and user input also make widget
    styles = {
        'path': {
            'base': dict(linewidth=2, alpha=0.5),
            'subtracted': dict(),  # linestyle='--', edgecolors='k', color='gray'),
            'non-subtracted': dict()
        },
        'poly': {
            'base': dict(linewidth=1, alpha=0.5, edgecolors='k'),
            'subtracted': dict(linestyle='--', color='gray'),
            'non-subtracted': dict()
        }
    }

    def get_style(self, element_type: str, subtracted=False, layer=None, extra=None):
        # element_type - poly path
        extra = extra or {}

        key = 'subtracted' if subtracted else 'non-subtracted'

        kw = {**self.styles[element_type].get('base', {}),
              **self.styles[element_type].get(key, {}),
              **extra}

        # TODO: maybe pop keys that are invalid for line etc.
        # we could have a validation flag to validate for specific poly / path

        return kw

    def render_tables(self, ax: Axes):

        for element_type, table in self.elements.tables.items():
            # Mask the table
            table = table[self.get_mask(table)]

            # subtracted
            mask = table['subtract'] == True
            render_func = getattr(self, f'render_{element_type}')
            render_func(table[mask], ax,  subtracted=True)

            # non-subtracted
            table1 = table[~mask]
            # TODO: do by layer and color
            # self.get_color_num()
            render_func = getattr(self, f'render_{element_type}')
            render_func(table1, ax, subtracted=False)

    def render_poly(self, table: pd.DataFrame, ax: Axes, subtracted: bool = False, extra_kw: dict = None):
        """
        Render a table of poly geometry.

        Arguments:
            table {DataFrame} -- element table
            ax {matplotlib.axes.Axes} -- axis to render on
            kw {dict} -- style params
        """
        if len(table) < 1:
            return
        kw = self.get_style('poly', subtracted=subtracted, extra=extra_kw)
        self._render_poly_array(ax, table.geometry, kw)

    def render_path(self, table: pd.DataFrame, ax: Axes,  subtracted: bool = False, extra_kw: dict = None):
        """
        Render a table of path geometry.

        Arguments:
            table {DataFrame} -- element table
            ax {matplotlib.axes.Axes} -- axis to render on
            kw {dict} -- style params
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
        if len(table1) > 0:
            table1.geometry = table1[['geometry', 'width']].apply(lambda x:
                                                                  x[0].buffer(
                                                                      distance=float(
                                                                          x[1]),
                                                                      cap_style=CAP_STYLE.flat,
                                                                      join_style=JOIN_STYLE.mitre,
                                                                      resolution=16
                                                                  ), axis=1)

            kw = self.get_style('poly', subtracted=subtracted, extra=extra_kw)
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

#         TODO: add some filter for sense of what components are visibile?
#               or on what chip the connectors are
#         '''

#         for name, conn in self.design.connectors.items():

#             line = LineString(conn.points)

#             self.render_shapely(line, kw=DEFAULT.annot_conectors.line_kw)

#             self.ax.annotate(name, xy=conn.middle[:2], xytext=conn.middle +
#                              np.array(DEFAULT.annot_conectors.ofst),
#                              **DEFAULT.annot_conectors.annotate_kw)
