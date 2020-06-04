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
@author: Zlatko Minev, ... (IBM)
@date: 2019
"""
import logging
import random
import sys
from typing import TYPE_CHECKING

import matplotlib
import matplotlib as mpl
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
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenu, QMessageBox,
                             QPushButton, QSizePolicy, QVBoxLayout, QWidget)
from shapely.geometry import CAP_STYLE, JOIN_STYLE, LineString

from ... import Dict
from ...designs import QDesign
from ...toolbox_python.utility_functions import log_error_easy
from .interaction_mpl import MplInteraction, PanAndZoom
from .toolbox_mpl import _axis_set_watermark_img, clear_axis, get_prop_cycle

if TYPE_CHECKING:
    from ..._gui.main_window import MetalGUI
    from ..._gui.widgets.plot_widget.plot_window import QMainWindowPlot

# @mfacchin - moved to the root __init__ to prevent windows from hanging
# mpl.use("Qt5Agg")

BACKGROUND_COLOR = '#F4F4F4'
MPL_CONTEXT_DEFAULT = {
    'lines.linewidth': 3,

    # FIGURE
    # See http://matplotlib.org/api/figure_api.html#matplotlib.figure.Figure
    # figure.titlesize : large      ## size of the figure title (Figure.suptitle())
    # figure.titleweight : normal   ## weight of the figure title
    # figure.figsize   : 6.4, 4.8   ## figure size in inches
    'figure.dpi': 100,  # figure dots per inch
    'figure.facecolor': BACKGROUND_COLOR,  # figure facecolor
    'figure.edgecolor': BACKGROUND_COLOR,  # figure edgecolor
    # figure.frameon : True         ## enable figure frame
    # figure.max_open_warning : 20  ## The maximum number of figures to open through
    # the pyplot interface before emitting a warning.
    # If less than one this feature is disabled.
    # The figure subplot parameters.  All dimensions are a fraction of the
    'figure.subplot.left': 0.00,  # the left side of the subplots of the figure
    'figure.subplot.right': 1.0,  # the right side of the subplots of the figure
    'figure.subplot.bottom': 0.00,  # the bottom of the subplots of the figure
    'figure.subplot.top': 1.0,  # the top of the subplots of the figure
    # the amount of width reserved for space between subplots,
    'figure.subplot.wspace': 0.0,
    # expressed as a fraction of the average axis width
    # the amount of height reserved for space between subplots,
    'figure.subplot.hspace': 0.0,
    # expressed as a fraction of the average axis height

    # Figure layout
    'figure.autolayout': False,  # When True, automatically adjust subplot
    # parameters to make the plot fit the figure
    # using `tight_layout`
    'figure.constrained_layout.use': True,  # When True, automatically make plot
    # elements fit on the figure. (Not compatible
    # with `autolayout`, above).
    # Padding around axes objects. Float representing
    'figure.constrained_layout.h_pad': 2./72.,
    # inches. Default is 3./72. inches (3 pts)
    'figure.constrained_layout.w_pad': 2./72.,
    # Space between subplot groups. Float representing
    'figure.constrained_layout.hspace': 0.0,
    # a fraction of the subplot widths being separated.
    'figure.constrained_layout.wspace': 0.0,

    # GRIDS
    'grid.color':   'b0b0b0',  # grid color
    'grid.linestyle': '-',         # solid
    'grid.linewidth':   0.5,  # in points
    'grid.alpha':   0.5,  # transparency, between 0.0 and 1.0

    # AXES
    # default face and edge color, default tick sizes,
    # default fontsizes for ticklabels, and so on.  See
    # http://matplotlib.org/api/axes_api.html#module-matplotlib.axes
    'axes.facecolor': BACKGROUND_COLOR,  # axes background color
    # 'axes.edgecolor'      : 'black',   ## axes edge color
    # axes.linewidth      : 0.8     ## edge linewidth
    'axes.grid': True,  # display grid or not
    # axes.grid.axis      : both    ## which axis the grid should apply to
    # axes.grid.which     : major   ## gridlines at major, minor or both ticks
    # axes.titlesize      : large   ## fontsize of the axes title
    # axes.titleweight    : normal  ## font weight of title
    'axes.titlepad': 2.0,  # pad between axes and title in points
    'axes.labelsize': 'small',  # fontsize of the x any y labels
    'axes.labelpad': 2.0,  # space between label and axis
    # axes.labelweight    : normal  ## weight of the x and y labels
    'axes.labelcolor': 'b0b0b0',
    'axes.axisbelow': 'line',  # draw axis gridlines and ticks below
    # patches (True); above patches but below
    # lines ('line'); or above all (False)
    # axes.formatter.limits : -7, 7 ## use scientific notation if log10
    # of the axis range is smaller than the
    # first or larger than the second
    # axes.formatter.use_locale : False ## When True, format tick labels
    # according to the user's locale.
    # For example, use ',' as a decimal
    # separator in the fr_FR locale.
    # axes.formatter.use_mathtext : False ## When True, use mathtext for scientific
    # notation.
    # axes.formatter.min_exponent: 0 ## minimum exponent to format in scientific notation
    # axes.formatter.useoffset      : True    ## If True, the tick label formatter
    # will default to labeling ticks relative
    # to an offset when the data range is
    # small compared to the minimum absolute
    # value of the data.
    # axes.formatter.offset_threshold : 4     ## When useoffset is True, the offset
    # will be used when it can remove
    # at least this number of significant
    # digits from tick labels.
    # axes.spines.left   : True   ## display axis spines
    #axes.spines.bottom : True
    'axes.spines.top': False,
    'axes.spines.right': False,
    # axes.unicode_minus  : True    ## use unicode for the minus symbol
    # rather than hyphen.  See
    # http://en.wikipedia.org/wiki/Plus_and_minus_signs#Character_codes
    # ['1f77b4', 'ff7f0e', '2ca02c', 'd62728', '9467bd', '8c564b', 'e377c2', '7f7f7f', 'bcbd22', '17becf']),
    'axes.prop_cycle': cycler('color', ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928']),
    # color cycle for plot lines  as list of string
    # colorspecs: single letter, long name, or web-style hex
                          # Note the use of string escapes here ('1f77b4', instead of 1f77b4)
                          # as opposed to the rest of this file.
    # axes.autolimit_mode : data ## How to scale axes limits to the data.
    # Use "data" to use data limits, plus some margin
    # Use "round_number" move to the nearest "round" number
    'axes.xmargin': .0,  # x margin.  See `axes.Axes.margins`
    'axes.ymargin': .0,  # y margin See `axes.Axes.margins`
    # polaraxes.grid      : True    ## display grid on polar axes
    # axes3d.grid         : True    ## display grid on 3d axes


    # TICKS
    # see http://matplotlib.org/api/axis_api.html#matplotlib.axis.Tick
    # xtick.top            : False  ## draw ticks on the top side
    # xtick.bottom         : True   ## draw ticks on the bottom side
    # xtick.labeltop       : False  ## draw label on the top
    # xtick.labelbottom    : True   ## draw label on the bottom
    # xtick.major.size     : 3.5    ## major tick size in points
    # xtick.minor.size     : 2      ## minor tick size in points
    # xtick.major.width    : 0.8    ## major tick width in points
    # xtick.minor.width    : 0.6    ## minor tick width in points
    'xtick.major.pad': 1.0,  # distance to major tick label in points
    'xtick.minor.pad': 1.0,  # distance to the minor tick label in points
    # xtick.color          : black  ## color of the tick labels
    # xtick.labelsize      : medium ## fontsize of the tick labels
    'xtick.direction': 'inout',  # direction: in, out, or inout
    # xtick.minor.visible  : False  ## visibility of minor ticks on x-axis
    # xtick.major.top      : True   ## draw x axis top major ticks
    # xtick.major.bottom   : True   ## draw x axis bottom major ticks
    # xtick.minor.top      : True   ## draw x axis top minor ticks
    # xtick.minor.bottom   : True   ## draw x axis bottom minor ticks
    # xtick.alignment      : center ## alignment of xticks

    # ytick.left           : True   ## draw ticks on the left side
    # ytick.right          : False  ## draw ticks on the right side
    # ytick.labelleft      : True   ## draw tick labels on the left side
    # ytick.labelright     : False  ## draw tick labels on the right side
    # ytick.major.size     : 3.5    ## major tick size in points
    # ytick.minor.size     : 2      ## minor tick size in points
    # ytick.major.width    : 0.8    ## major tick width in points
    # ytick.minor.width    : 0.6    ## minor tick width in points
    'ytick.major.pad': 1.,  # distance to major tick label in points
    'ytick.minor.pad': 1.,  # distance to the minor tick label in points
    # ytick.color          : black  ## color of the tick labels
    # ytick.labelsize      : medium ## fontsize of the tick labels
    'ytick.direction': 'inout',  # direction: in, out, or inout
    # ytick.minor.visible  : False  ## visibility of minor ticks on y-axis
    # ytick.major.left     : True   ## draw y axis left major ticks
    # ytick.major.right    : True   ## draw y axis right major ticks
    # ytick.minor.left     : True   ## draw y axis left minor ticks
    # ytick.minor.right    : True   ## draw y axis right minor ticks
    # ytick.alignment      : center_baseline ## alignment of yticks

    # PATHS
    # path.simplify : True   ## When True, simplify paths by removing "invisible"
                            # points to reduce file size and increase rendering
                            # speed
    # path.simplify_threshold : 0.111111111111  ## The threshold of similarity below which
    # vertices will be removed in the
    # simplification process
    # path.snap : True ## When True, rectilinear axis-aligned paths will be snapped to
    # the nearest pixel when certain criteria are met.  When False,
    # paths will never be snapped.
    # path.sketch : None ## May be none, or a 3-tuple of the form (scale, length,
    # randomness).
    # *scale* is the amplitude of the wiggle
                        # perpendicular to the line (in pixels).  *length*
                        # is the length of the wiggle along the line (in
                        # pixels).  *randomness* is the factor by which
                        # the length is randomly scaled.
    #path.effects : []  ##


    # LINES
    # See http://matplotlib.org/api/artist_api.html#module-matplotlib.lines for more
    # information on line properties.
    # lines.linewidth   : 1.5     ## line width in points
    # lines.linestyle   : -       ## solid line
    # lines.color       : C0      ## has no affect on plot(); see axes.prop_cycle
    # lines.marker      : None    ## the default marker
    # lines.markerfacecolor  : auto    ## the default markerfacecolor
    # lines.markeredgecolor  : auto    ## the default markeredgecolor
    # lines.markeredgewidth  : 1.0     ## the line width around the marker symbol
    # lines.markersize  : 6            ## markersize, in points
    # lines.dash_joinstyle : round        ## miter|round|bevel
    # lines.dash_capstyle : butt          ## butt|round|projecting
    # lines.solid_joinstyle : round       ## miter|round|bevel
    # lines.solid_capstyle : projecting   ## butt|round|projecting
    # lines.antialiased : True         ## render lines in antialiased (no jaggies)

    # The three standard dash patterns.  These are scaled by the linewidth.
    # lines.dashed_pattern : 3.7, 1.6
    # lines.dashdot_pattern : 6.4, 1.6, 1, 1.6
    # lines.dotted_pattern : 1, 1.65
    #lines.scale_dashes : True

    # markers.fillstyle: full ## full|left|right|bottom|top|none

    # PATCHES
    # Patches are graphical objects that fill 2D space, like polygons or
    ## circles.  See
    # http://matplotlib.org/api/artist_api.html#module-matplotlib.patches
    # information on patch properties
    'patch.linewidth': 1,  # edge width in points.
    #patch.facecolor        : C0
    # patch.edgecolor        : black   ## if forced, or patch is not filled
    # patch.force_edgecolor  : False   ## True to always use edgecolor
    # patch.antialiased      : True    ## render patches in antialiased (no jaggies)

    # HATCHES
    #hatch.color     : black
    #hatch.linewidth : 1.0
}


# TODO: Create an interface class for canvas based on this class
# This class should then inherit it

class PlotCanvas(FigureCanvas):
    """
    Main Plot canvas widget
    Access with:
        canvas = gui.canvas
    """
    # See https://github.com/matplotlib/matplotlib/blob/master/lib/matplotlib/backends/backend_qt5agg.py
    # Consider using pyqtgraph https://stackoverflow.com/questions/40126176/fast-live-plotting-in-matplotlib-pyplot.

    def __init__(self, design: QDesign,
                 parent: 'QMainWindowPlot' = None,
                 logger=None,
                 statusbar_label=None):

        self.gui = parent.gui  # type: MetalGUI

        # MPL
        self.config = Dict(
            path_simplify=True,
            path_simplify_threshold=1.0,
            chunksize=5000,
        )
        # Update with local user config after this

        self.mpl_context = MPL_CONTEXT_DEFAULT.copy()

        with mpl.rc_context(rc=self.mpl_context):
            fig = Figure()

        self.axes = []
        self.current_axis = 0
        self.logger = logger
        self.statusbar_label = statusbar_label
        self.design = design
        self._state = {}  # used to store state between drawing

        super().__init__(fig)

        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.panzoom = PanAndZoom(self.figure)
        self.panzoom.logger = self.logger
        self.panzoom._statusbar_label = self.statusbar_label

        self.setup_figure_and_axes()

        self.metal_renderer = MplRenderer(
            canvas=self, design=self.design, logger=logger)

        # self.plot()

    def set_design(self, design: QDesign):
        self.design = design
        self.metal_renderer.set_design(design)

    def setup_figure_and_axes(self):
        """
        Main setup from scratch.
        """

        self.setup_rendering()

        with mpl.rc_context(rc=self.mpl_context):

            self.figure.clf()

            self.axes = [self.figure.add_subplot(111)]
            self.current_axis = 0

            self.style_figure()

            for num, ax in enumerate(self.axes):
                self.style_axis(ax, num)
                ax.set_xlim([-0.5, 0.5])
                ax.set_ylim([-0.5, 0.5])

    def setup_rendering(self):
        """https://matplotlib.org/3.1.1/tutorials/introductory/usage.html

        Line segment simplificatio:
        For plots that have line segments (e.g. typical line plots, outlines of
        polygons, etc.), rendering performance can be controlled by the path.simplify
        and path.simplify_threshold

            path_simplify:
                When True, simplify paths by removing "invisible" points to reduce file
                size and increase rendering speed

            path_simplify_threshold:
                The threshold of similarity below which vertices will be removed in the
                simplification process

            chuncksize:
                0 to disable; values in the range
                10000 to 100000 can improve speed slightly
                and prevent an Agg rendering failure
                when plotting very large data sets,
                especially if they are very gappy.
                It may cause minor artifacts, though.
                A value of 20000 is probably a good
                starting point.

        """
        plt.style.use('fast')

        mpl.rcParams['path.simplify'] = self.config.path_simplify
        mpl.rcParams['path.simplify_threshold'] = self.config.path_simplify_threshold
        mpl.rcParams['agg.path.chunksize'] = self.config.chunksize

    def get_axis(self):
        """
        Gets the current axis
        """
        return self.axes[self.current_axis]

    def _plot(self, ax):
        self.metal_renderer.render(ax)
        #ax.set_xlabel('X (mm)')
        #ax.set_ylabel('y (mm)')

    def plot(self, clear=True, with_try=True):
        # TODO: Maybe do in a thread?
        self.hide()
        ax = self.get_axis()

        def prep():
            # Push state
            self._state['xlim'] = ax.get_xlim()
            self._state['ylim'] = ax.get_ylim()

        def main_plot():
            # for temporary style
            with mpl.rc_context(rc=self.mpl_context):
                if clear:
                    self.clear_axis(ax)
                self._plot(ax)
                self._watermark_axis(ax)

        def final():
            # Draw
            self.draw()
            # Restore the state
            ax.set_xlim(self._state['xlim'])
            ax.set_ylim(self._state['ylim'])
            self.show()

        if with_try:
            # speed impact?
            try:
                prep()
                main_plot()

            except Exception as e:
                log_error_easy(self.logger,
                               post_text=f'Plotting error: {e}')

            finally:
                final()

        else:
            main_plot()
            final()

    def _watermark_axis(self, ax: plt.Axes):
        """Add a watermark"""
        # self.logger.debug('WATERMARK')
        kw = dict(fontsize=15, color='gray', ha='right',
                  va='bottom', alpha=0.18, zorder=-100)
        ax.annotate('Qiskit Metal', xy=(0.98, 0.02),
                    xycoords='axes fraction', **kw)

        file = (self.gui.path_imgs / 'metal_logo.png')
        if file.is_file():
            #print(f'Found {file} for watermark.')
            _axis_set_watermark_img(ax, file, size=0.15)
        else:
            logger.error(f'Error could not load {file} for watermark.')

    def clear_axis(self, ax: plt.Axes = None):
        """Clear an axis or clear all axes

        Args:
            ax (plt.Axes, optional): Clear an axis, or
                 if None, then clear all axes.
                 Defaults to None.
        """
        if ax:
            clear_axis(ax)
        else:
            for ax in self.axes:
                clear_axis(ax)

    def refresh(self):
        """Force refresh. Does not replot renderer. Just mpl refresh"""
        self.update()  # not sure if needed
        self.flush_events()
        self.draw()

    def style_axis(self, ax, num: int):

        ax.set_aspect(1)

        # If 'box', change the physical dimensions of the Axes. If 'datalim',
        # change the x or y data limits.
        ax.set_adjustable('datalim')

        ax.set_xlabel('x position (mm)')
        ax.set_ylabel('y position (mm)')

        # Zero lines
        kw = dict(c='k', lw=1, zorder=-1, alpha=0.5)
        ax.axhline(0, **kw)
        ax.axvline(0, **kw)

        # Grid
        kw = dict(
            color='#CCCCCC',
            #zorder = -100,
            #alpha = 0.8,
            # fillstyle='left'
            # markevery=(1,1),
            # sketch_params=1
        )
        if 0:  # fix tick spacing
            loc = mpl.ticker.MultipleLocator(base=0.1)
            ax.xaxis.set_major_locator(loc)
            ax.yaxis.set_major_locator(loc)

        ax.grid(which='major', linestyle='--', **kw)
        ax.grid(which='minor', linestyle=':', **kw)
        ax.set_axisbelow(True)

        #[left, bottom, width, height]
        # ax.set_position([0,0,1,1])

    def style_figure(self):
        pass  # self.figure.tight_layout()

    def auto_scale(self):
        for ax in self.figure.axes:
            ax.autoscale()
        self.refresh()

    def zoom_to_rectangle(self, bounds: tuple, ax: Axes = None):
        """[summary]

        Arguments:
            bounds {tuple} -- tuple containing `minx, miny, maxx, maxy`
                     values for the bounds of the series as a whole.

        Keyword Arguments:
            ax {Axes} -- Does for all if none (default: {None})
        """
        if ax is None:
            for ax in self.axes:
                self.zoom_to_rectangle(bounds, ax)
        else:
            ax.set_xlim(bounds[0], bounds[2])
            ax.set_ylim(bounds[1], bounds[3])
            # ax.redraw_in_frame()
            self.refresh()

    #TODO: move to base class
    def zoom_on_component(self, name:str, zoom:float=1.1):
        """Zoom in on a component

        Arguments:
            name {str} -- [description]

        Keyword Arguments:
            zoom (float) -- fraction to expand the bounding vbox by
        """
        component = self.design.components[name]
        bounds = component.geometry_bounds()
        bbox = Bbox.from_extents(bounds)
        bounds = bbox.expanded(zoom,zoom).extents
        self.zoom_to_rectangle(bounds)

    def set_component(self, name: str):
        """
        Shortcut to set a component in the component widget to be examined.

        Args:
            name (str) -- name of the component in the design
        """
        self.component_window.set_component(name)


to_poly_patch = np.vectorize(PolygonPatch)


class MplRenderer():
    """
    Matplotlib handle all rendering of an axis.

    The axis is given in the function render.

    Access:
        self = gui.canvas.metal_renderer
    """

    def __init__(self, canvas: PlotCanvas, design: QDesign, logger: logging.Logger):
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

    def render(self, ax: matplotlib.axes.Axes):
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

    def _render_poly_array(self, ax: matplotlib.axes.Axes, poly_array: np.array,
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

    def render_tables(self, ax: matplotlib.axes.Axes):

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

    def render_poly(self, table: pd.DataFrame, ax: matplotlib.axes.Axes, subtracted: bool = False, extra_kw: dict = None):
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

    def render_path(self, table: pd.DataFrame, ax: matplotlib.axes.Axes,  subtracted: bool = False, extra_kw: dict = None):
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
