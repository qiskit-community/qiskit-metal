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
"""MPL Canvas."""

from typing import TYPE_CHECKING, List

import matplotlib
import matplotlib as mpl
import matplotlib.patches as patches
import matplotlib.pyplot as plt

from cycler import cycler
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QSizePolicy
from ... import Dict
from ...designs import QDesign
from .mpl_interaction import PanAndZoom
from .mpl_renderer import QMplRenderer
from .mpl_toolbox import _axis_set_watermark_img, clear_axis
from .extensions.animated_text import AnimatedText
from .. import config

if not config.is_building_docs():
    from ...toolbox_python.utility_functions import log_error_easy

if TYPE_CHECKING:
    from ..._gui.main_window import MetalGUI
    from ..._gui.widgets.plot_widget.plot_window import QMainWindowPlot

# @mfacchin - moved to the root __init__ to prevent windows from hanging
# mpl.use("Qt5Agg")

BACKGROUND_COLOR = '#F4F4F4'
MPL_CONTEXT_DEFAULT = {
    'lines.linewidth':
        3,

    # FIGURE
    # See http://matplotlib.org/api/figure_api.html#matplotlib.figure.Figure
    # figure.titlesize : large      ## size of the figure title (Figure.suptitle())
    # figure.titleweight : normal   ## weight of the figure title
    # figure.figsize   : 6.4, 4.8   ## figure size in inches
    'figure.dpi':
        100,  # figure dots per inch
    'figure.facecolor':
        BACKGROUND_COLOR,  # figure facecolor
    'figure.edgecolor':
        BACKGROUND_COLOR,  # figure edgecolor
    # figure.frameon : True         ## enable figure frame
    # figure.max_open_warning : 20  ## The maximum number of figures to open through
    # the pyplot interface before emitting a warning.
    # If less than one this feature is disabled.
    # The figure subplot parameters.  All dimensions are a fraction of the
    'figure.subplot.left':
        0.00,  # the left side of the subplots of the figure
    'figure.subplot.right':
        1.0,  # the right side of the subplots of the figure
    'figure.subplot.bottom':
        0.00,  # the bottom of the subplots of the figure
    'figure.subplot.top':
        1.0,  # the top of the subplots of the figure
    # the amount of width reserved for space between subplots,
    'figure.subplot.wspace':
        0.0,
    # expressed as a fraction of the average axis width
    # the amount of height reserved for space between subplots,
    'figure.subplot.hspace':
        0.0,
    # expressed as a fraction of the average axis height

    # Figure layout
    'figure.autolayout':
        False,  # When True, automatically adjust subplot
    # parameters to make the plot fit the figure
    # using `tight_layout`
    'figure.constrained_layout.use':
        True,  # When True, automatically make plot
    # qgeometry fit on the figure. (Not compatible
    # with `autolayout`, above).
    # Padding around axes objects. Float representing
    'figure.constrained_layout.h_pad':
        2. / 72.,
    # inches. Default is 3./72. inches (3 pts)
    'figure.constrained_layout.w_pad':
        2. / 72.,
    # Space between subplot groups. Float representing
    'figure.constrained_layout.hspace':
        0.0,
    # a fraction of the subplot widths being separated.
    'figure.constrained_layout.wspace':
        0.0,

    # GRIDS
    'grid.color':
        'b0b0b0',  # grid color
    'grid.linestyle':
        '-',  # solid
    'grid.linewidth':
        0.5,  # in points
    'grid.alpha':
        0.5,  # transparency, between 0.0 and 1.0

    # AXES
    # default face and edge color, default tick sizes,
    # default fontsizes for ticklabels, and so on.  See
    # http://matplotlib.org/api/axes_api.html#module-matplotlib.axes
    'axes.facecolor':
        BACKGROUND_COLOR,  # axes background color
    # 'axes.edgecolor'      : 'black',   ## axes edge color
    # axes.linewidth      : 0.8     ## edge linewidth
    'axes.grid':
        True,  # display grid or not
    # axes.grid.axis      : both    ## which axis the grid should apply to
    # axes.grid.which     : major   ## gridlines at major, minor or both ticks
    # axes.titlesize      : large   ## fontsize of the axes title
    # axes.titleweight    : normal  ## font weight of title
    'axes.titlepad':
        2.0,  # pad between axes and title in points
    'axes.labelsize':
        'small',  # fontsize of the x any y labels
    'axes.labelpad':
        2.0,  # space between label and axis
    # axes.labelweight    : normal  ## weight of the x and y labels
    'axes.labelcolor':
        'b0b0b0',
    'axes.axisbelow':
        'line',  # draw axis gridlines and ticks below
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
    'axes.spines.top':
        False,
    'axes.spines.right':
        False,
    # axes.unicode_minus  : True    ## use unicode for the minus symbol
    # rather than hyphen.  See
    # http://en.wikipedia.org/wiki/Plus_and_minus_signs#Character_codes
    # ['1f77b4', 'ff7f0e', '2ca02c', 'd62728', '9467bd', '8c564b', 'e377c2', '7f7f7f', 'bcbd22', '17becf']),
    'axes.prop_cycle':
        cycler('color', [
            '#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c',
            '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928'
        ]),
    # color cycle for plot lines  as list of string
    # colorspecs: single letter, long name, or web-style hex
    # Note the use of string escapes here ('1f77b4', instead of 1f77b4)
    # as opposed to the rest of this file.
    # axes.autolimit_mode : data ## How to scale axes limits to the data.
    # Use "data" to use data limits, plus some margin
    # Use "round_number" move to the nearest "round" number
    'axes.xmargin':
        .0,  # x margin.  See `axes.Axes.margins`
    'axes.ymargin':
        .0,  # y margin See `axes.Axes.margins`
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
    'xtick.major.pad':
        1.0,  # distance to major tick label in points
    'xtick.minor.pad':
        1.0,  # distance to the minor tick label in points
    # xtick.color          : black  ## color of the tick labels
    # xtick.labelsize      : medium ## fontsize of the tick labels
    'xtick.direction':
        'inout',  # direction: in, out, or inout
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
    'ytick.major.pad':
        1.,  # distance to major tick label in points
    'ytick.minor.pad':
        1.,  # distance to the minor tick label in points
    # ytick.color          : black  ## color of the tick labels
    # ytick.labelsize      : medium ## fontsize of the tick labels
    'ytick.direction':
        'inout',  # direction: in, out, or inout
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
    'patch.linewidth':
        1,  # edge width in points.
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
    """Main Plot canvas widget.

    This class extends the `FigureCanvas` class.

    Access with:
        `canvas = gui.canvas`
    """

    # See
    # https://github.com/matplotlib/matplotlib/blob/master/lib/matplotlib/backends/backend_qt5agg.py
    # Consider using pyqtgraph
    # https://stackoverflow.com/questions/40126176/fast-live-plotting-in-matplotlib-pyplot.

    def __init__(self,
                 design: QDesign,
                 parent: 'QMainWindowPlot' = None,
                 logger=None,
                 statusbar_label=None):
        """
        Args:
            design (QDesign): The design.
            parent (QMainWindowPlot): The main window.  Defaults to None.
            logger (logger): The logger.  Defaults to None.
            statusbar_label (str): Statusbar label.  Defaults to None.
        """

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
        # used to keep track of what we will need to delete
        self._annotations = {'text': [], 'patch': []}

        super().__init__(fig)

        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.panzoom = PanAndZoom(self.figure)
        self.panzoom.logger = self.logger
        self.panzoom._statusbar_label = self.statusbar_label

        self.setup_figure_and_axes()

        self.metal_renderer = QMplRenderer(canvas=self,
                                           design=self.design,
                                           logger=logger)

        # self.plot()
        # self.welcome_message()

    def set_design(self, design: QDesign):
        """Set the design.

        Args:
            design (QDesign): the design
        """
        self.design = design
        self.metal_renderer.set_design(design)

    def setup_figure_and_axes(self):
        """Main setup from scratch."""

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
        """Line segment simplificatio: For plots that have line segments (e.g.
        typical line plots, outlines of polygons, etc.), rendering performance
        can be controlled by the path.simplify and path.simplify_threshold.

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

        https://matplotlib.org/3.1.1/tutorials/introductory/usage.html
        """
        plt.style.use('fast')

        mpl.rcParams['path.simplify'] = self.config.path_simplify
        mpl.rcParams[
            'path.simplify_threshold'] = self.config.path_simplify_threshold
        mpl.rcParams['agg.path.chunksize'] = self.config.chunksize

    def get_axis(self):
        """Gets the current axis."""
        return self.axes[self.current_axis]

    def _plot(self, ax):
        """Set the axes.

        Args:
            ax (matplotlib.axes.Axes): axes
        """
        self.metal_renderer.render(ax)
        #ax.set_xlabel('X (mm)')
        #ax.set_ylabel('y (mm)')

    def plot(self, clear=True, with_try=True):
        """Render the plot.

        Args:
            clear (bool): True to clear everything first.  Defaults to True.
            with_try (bool): True to execute in a try-catch block.  Defaults to True.

        Raises:
            Exception: Plotting error
        """
        # TODO: Maybe do in a thread?
        self.hide()
        # the artist will be removed by the clear axis.
        self._force_clear_annotations()

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
                log_error_easy(self.logger, post_text=f'Plotting error: {e}')

            finally:
                final()

        else:
            main_plot()
            final()

    def _watermark_axis(self, ax: plt.Axes):
        """Add a watermark.

        Args:
            ax (plt.Axes): axes
        """
        # self.logger.debug('WATERMARK')
        kw = dict(fontsize=15,
                  color='gray',
                  ha='right',
                  va='bottom',
                  alpha=0.18,
                  zorder=-100)
        ax.annotate('Qiskit Metal',
                    xy=(0.98, 0.02),
                    xycoords='axes fraction',
                    **kw)

        file = (self.gui.path_imgs / 'metal_logo.png')
        if file.is_file():
            #print(f'Found {file} for watermark.')
            _axis_set_watermark_img(ax, file, size=0.15)
        else:
            # import error?
            self.logger.error(f'Error could not load {file} for watermark.')

    def clear_axis(self, ax: plt.Axes = None):
        """Clear an axis or clear all axes.

        Args:
            ax (plt.Axes): Clear an axis, or
                 if None, then clear all axes.
                 Defaults to None.
        """
        if ax:
            clear_axis(ax)
        else:
            for ax in self.axes:
                clear_axis(ax)

    def refresh(self):
        """Force refresh.

        Does not replot renderer. Just mpl refresh.
        """
        self.update()  # not sure if needed
        self.flush_events()
        self.draw()

    def style_axis(self, ax, num: int):
        """Style the axis.

        Args:
            ax (axis): The axis
            num (int): Not used
        """
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
        """Style a figure."""
        pass  # self.figure.tight_layout()

    def auto_scale(self):
        """Automaticlaly scale."""
        for ax in self.figure.axes:
            ax.autoscale()
        self.refresh()

    def welcome_message(self):
        """The GUI displays a message to let users know they are using Qiskit
        Metal."""

        # pylint: disable=attribute-defined-outside-init
        self._welcome_text = AnimatedText(
            self.axes[0],
            "Welcome to Qiskit Metal Early Access Alpha",
            self,
            start=False,
            kw={'fontsize': 20})

        self._welcome_start_timer = QTimer.singleShot(
            250, self._welcome_message_start)

    def _welcome_message_start(self):
        """Start the welcome message."""
        self._welcome_text.start()
        # self._welcome_start_timer.deleteLater()

    def zoom_to_rectangle(self, bounds: tuple, ax: Axes = None):
        """Zoom to the specified rectangle.

        Args:
            bounds (tuple): Tuple containing `minx, miny, maxx, maxy`
                     values for the bounds of the series as a whole.
            ax (Axes): Does for all if none (default: {None})
        """
        if ax is None:
            for ax in self.axes:
                self.zoom_to_rectangle(bounds, ax)
        else:
            ax.set_xlim(bounds[0], bounds[2])
            ax.set_ylim(bounds[1], bounds[3])
            # ax.redraw_in_frame()
            self.refresh()

    def find_component_bounds(self, components: List[str], zoom: float = 1.2):
        """Find bounds of a set of components.

        Args:
            components (List[str]): A list of component names
            zoom (float): Fraction to expand the bounding vbox by

        Returns:
            List: List of x,y coordinates defining the bounding box
        """
        if len(components) == 0:
            self.logger.error('At least one component must be provided.')
        # initialize bounds
        bounds = [float("inf"), float("inf"), float("-inf"), float("-inf")]
        for name in components:
            # self.design.components[name]
            component = self.design.components[name]
            # return (minx, miny, maxx, maxy)
            newbounds = component.qgeometry_bounds()
            bbox = Bbox.from_extents(newbounds)
            newbounds = bbox.expanded(zoom, zoom).extents
            # re-calculate total bounds by adding current component
            bounds = [
                min(newbounds[0], bounds[0]),
                min(newbounds[1], bounds[1]),
                max(newbounds[2], bounds[2]),
                max(newbounds[3], bounds[3])
            ]

        return bounds

    def set_component(self, name: str):
        """Shortcut to set a component in the component widget to be examined.

        Args:
            name (str): Name of the component in the design
        """
        self.component_window.set_component(name)

    def clear_annotation(self):
        """Clear the annotations.

        Raises:
            Exception: Error while clearing the annotations
        """
        try:
            for dummy_ax in self.axes:
                for patch in self._annotations['patch']:
                    # ax.patches.remove(patch)
                    # print(patch)
                    patch.remove()
                for text in self._annotations['text']:
                    # ax.texts.remove(patch)
                    text.remove()
        except Exception as e:
            self.logger.error(f'While canvas clear_annotation: {e}')
        finally:
            self._force_clear_annotations()

    def _force_clear_annotations(self):
        """Clear annotation dicts."""
        self._annotations['patch'] = []
        self._annotations['text'] = []

    def highlight_components(self, component_names: List[str]):
        """Highlight a list of components.

        Args:
            component_names (List[str]): A list of component names
        """
        # Defaults - todo eventually move to some option place where can be changed
        text_kw = dict(color='r',
                       alpha=0.75,
                       verticalalignment='center',
                       horizontalalignment='center',
                       clip_on=True,
                       zorder=99,
                       fontweight='bold')
        text_bbox_kw = dict(facecolor='#FFFFFF',
                            alpha=0.75,
                            edgecolor='#F0F0F0')

        # Functionality
        self.clear_annotation()

        component_id_list = self.design.components.get_list_ints(
            component_names)
        # pylint: disable=protected-access
        for component_id in component_id_list:
            component_id = int(component_id)

            if component_id in self.design._components:
                # type: QComponent
                component = self.design._components[component_id]

                if 1:  # highlight bounding box
                    bounds = component.qgeometry_bounds(
                    )  # returns (minx, miny, maxx, maxy)
                    # bbox = Bbox.from_extents(bounds)
                    # Create a Rectangle patch TODO: move to settings
                    kw = dict(linewidth=1,
                              edgecolor='r',
                              facecolor=(1, 0, 0, 0.05),
                              zorder=100,
                              ls='--')
                    rect = patches.Rectangle((0, 0), 0, 0, **kw)

                    lbwh = [
                        bounds[0], bounds[1], bounds[2] - bounds[0],
                        bounds[3] - bounds[1]
                    ]
                    rect.set_bounds(*lbwh)
                    self._annotations['patch'] += [rect]
                    for ax in self.axes:
                        ax.add_patch(rect)

                    if 1:  # Draw name as text of QComponent
                        text = matplotlib.text.Text(
                            (bounds[0] + bounds[2]) / 2.,
                            (bounds[1] + bounds[3]) / 2., str(component.name),
                            **{
                                **text_kw,
                                **dict(fontsize=13)
                            })
                        text.set_bbox({
                            **text_bbox_kw,
                            **dict(edgecolor=None)
                        })  # dict(facecolor=(1, 0, 0, 0.25)))
                        for ax in self.axes:
                            ax.add_artist(text)
                        self._annotations['text'] += [text]

                if 1:  # Draw the pins
                    # for component_id in self.design.components.keys():
                    for pin_name in component.pins.keys():
                        #self.logger.debug(f'Pin {pin_name}')
                        pin = component.pins[pin_name]
                        m = pin['middle']
                        n = pin['normal']

                        if 1:  # draw the arrows
                            kw = dict(color='r',
                                      mutation_scale=15,
                                      alpha=0.75,
                                      capstyle='butt',
                                      ec='k',
                                      lw=0.5,
                                      zorder=100,
                                      clip_on=True)
                            arrow = patches.FancyArrowPatch(
                                m, m + n * 0.05, **kw)
                            self._annotations['patch'] += [arrow]
                            # """A fancy arrow patch. It draws an arrow using
                            # the ArrowStyle.
                            # The head and tail positions are fixed at the
                            # specified start and end points of the arrow,
                            # but the size and shape (in display coordinates)
                            # of the arrow does not change when the axis
                            # is moved or zoomed.
                            # """
                            for ax in self.axes:
                                ax.add_patch(arrow)

                        if 1:  # draw names of pins
                            dist = 0.05
                            kw = {
                                **text_kw,
                                **dict(horizontalalignment='left' if n[0] >= 0 else 'right')
                            }
                            # type: matplotlib.text.Text
                            text = ax.text(*(m + dist * n), pin_name, **kw)
                            text.set_bbox(text_bbox_kw)
                            self._annotations['text'] += [text]

        self.refresh()
