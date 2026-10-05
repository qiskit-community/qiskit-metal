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

from typing import TYPE_CHECKING, List, Optional

import warnings
import logging
import matplotlib
import matplotlib as mpl
from matplotlib import patches
import matplotlib.pyplot as plt

from cycler import cycler
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QSizePolicy
from qiskit_metal import Dict
from qiskit_metal.designs import QDesign
from qiskit_metal._gui.utility._toolbox_qt import doShowHighlighWidget, single_shot
from qiskit_metal.renderers.renderer_mpl.mpl_interaction import PanAndZoom
from qiskit_metal.renderers.renderer_mpl.mpl_renderer import QMplRenderer
from qiskit_metal.renderers.renderer_mpl.mpl_toolbox import (
    _axis_set_watermark_img,
    clear_axis,
)
from qiskit_metal.renderers.renderer_mpl.extensions.animated_text import AnimatedText
from qiskit_metal import config

if not config.is_building_docs():
    from ...toolbox_python.utility_functions import log_error_easy

if TYPE_CHECKING:
    from ..._gui.main_window import MetalGUI
    from ..._gui.widgets.plot_widget.plot_window import QMainWindowPlot

# @mfacchin - moved to the root __init__ to prevent windows from hanging
# mpl.use("QtAgg")

BACKGROUND_COLOR = "#F4F4F4"
MPL_CONTEXT_DEFAULT = {
    "lines.linewidth": 3,
    # FIGURE
    # See http://matplotlib.org/api/figure_api.html#matplotlib.figure.Figure
    # figure.titlesize : large      ## size of the figure title (Figure.suptitle())
    # figure.titleweight : normal   ## weight of the figure title
    # figure.figsize   : 6.4, 4.8   ## figure size in inches
    "figure.dpi": 100,  # figure dots per inch
    "figure.facecolor": BACKGROUND_COLOR,  # figure facecolor
    "figure.edgecolor": BACKGROUND_COLOR,  # figure edgecolor
    # figure.frameon : True         ## enable figure frame
    # figure.max_open_warning : 20  ## The maximum number of figures to open through
    # the pyplot interface before emitting a warning.
    # If less than one this feature is disabled.
    # The figure subplot parameters.  All dimensions are a fraction of the
    "figure.subplot.left": 0.00,  # the left side of the subplots of the figure
    "figure.subplot.right": 1.0,  # the right side of the subplots of the figure
    "figure.subplot.bottom": 0.00,  # the bottom of the subplots of the figure
    "figure.subplot.top": 1.0,  # the top of the subplots of the figure
    # the amount of width reserved for space between subplots,
    "figure.subplot.wspace": 0.0,
    # expressed as a fraction of the average axis width
    # the amount of height reserved for space between subplots,
    "figure.subplot.hspace": 0.0,
    # expressed as a fraction of the average axis height
    # Figure layout
    "figure.autolayout": False,  # When True, automatically adjust subplot
    # parameters to make the plot fit the figure
    # using `tight_layout`
    "figure.constrained_layout.use": True,  # When True, automatically make plot
    # qgeometry fit on the figure. (Not compatible
    # with `autolayout`, above).
    # Padding around axes objects. Float representing
    "figure.constrained_layout.h_pad": 2.0 / 72.0,
    # inches. Default is 3./72. inches (3 pts)
    "figure.constrained_layout.w_pad": 2.0 / 72.0,
    # Space between subplot groups. Float representing
    "figure.constrained_layout.hspace": 0.0,
    # a fraction of the subplot widths being separated.
    "figure.constrained_layout.wspace": 0.0,
    # GRIDS
    "grid.color": "b0b0b0",  # grid color
    "grid.linestyle": "-",  # solid
    "grid.linewidth": 0.5,  # in points
    "grid.alpha": 0.5,  # transparency, between 0.0 and 1.0
    # AXES
    # default face and edge color, default tick sizes,
    # default fontsizes for ticklabels, and so on.  See
    # http://matplotlib.org/api/axes_api.html#module-matplotlib.axes
    "axes.facecolor": BACKGROUND_COLOR,  # axes background color
    # 'axes.edgecolor'      : 'black',   ## axes edge color
    # axes.linewidth      : 0.8     ## edge linewidth
    "axes.grid": True,  # display grid or not
    # axes.grid.axis      : both    ## which axis the grid should apply to
    # axes.grid.which     : major   ## gridlines at major, minor or both ticks
    # axes.titlesize      : large   ## fontsize of the axes title
    # axes.titleweight    : normal  ## font weight of title
    "axes.titlepad": 2.0,  # pad between axes and title in points
    "axes.labelsize": "small",  # fontsize of the x any y labels
    "axes.labelpad": 2.0,  # space between label and axis
    # axes.labelweight    : normal  ## weight of the x and y labels
    "axes.labelcolor": "b0b0b0",
    "axes.axisbelow": "line",  # draw axis gridlines and ticks below
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
    # axes.spines.bottom : True
    "axes.spines.top": False,
    "axes.spines.right": False,
    # axes.unicode_minus  : True    ## use unicode for the minus symbol
    # rather than hyphen.  See
    # http://en.wikipedia.org/wiki/Plus_and_minus_signs#Character_codes
    # ['1f77b4', 'ff7f0e', '2ca02c', 'd62728', '9467bd', '8c564b', 'e377c2', '7f7f7f', 'bcbd22', '17becf']),
    "axes.prop_cycle": cycler(
        "color",
        [
            "#a6cee3",
            "#1f78b4",
            "#b2df8a",
            "#33a02c",
            "#fb9a99",
            "#e31a1c",
            "#fdbf6f",
            "#ff7f00",
            "#cab2d6",
            "#6a3d9a",
            "#ffff99",
            "#b15928",
        ],
    ),
    # color cycle for plot lines  as list of string
    # colorspecs: single letter, long name, or web-style hex
    # Note the use of string escapes here ('1f77b4', instead of 1f77b4)
    # as opposed to the rest of this file.
    # axes.autolimit_mode : data ## How to scale axes limits to the data.
    # Use "data" to use data limits, plus some margin
    # Use "round_number" move to the nearest "round" number
    "axes.xmargin": 0.0,  # x margin.  See `axes.Axes.margins`
    "axes.ymargin": 0.0,  # y margin See `axes.Axes.margins`
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
    "xtick.major.pad": 1.0,  # distance to major tick label in points
    "xtick.minor.pad": 1.0,  # distance to the minor tick label in points
    # xtick.color          : black  ## color of the tick labels
    # xtick.labelsize      : medium ## fontsize of the tick labels
    "xtick.direction": "inout",  # direction: in, out, or inout
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
    "ytick.major.pad": 1.0,  # distance to major tick label in points
    "ytick.minor.pad": 1.0,  # distance to the minor tick label in points
    # ytick.color          : black  ## color of the tick labels
    # ytick.labelsize      : medium ## fontsize of the tick labels
    "ytick.direction": "inout",  # direction: in, out, or inout
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
    # path.effects : []  ##
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
    # lines.scale_dashes : True
    # markers.fillstyle: full ## full|left|right|bottom|top|none
    # PATCHES
    # Patches are graphical objects that fill 2D space, like polygons or
    ## circles.  See
    # http://matplotlib.org/api/artist_api.html#module-matplotlib.patches
    # information on patch properties
    "patch.linewidth": 1,  # edge width in points.
    # patch.facecolor        : C0
    # patch.edgecolor        : black   ## if forced, or patch is not filled
    # patch.force_edgecolor  : False   ## True to always use edgecolor
    # patch.antialiased      : True    ## render patches in antialiased (no jaggies)
    # HATCHES
    # hatch.color     : black
    # hatch.linewidth : 1.0
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

    def __init__(
        self,
        design: QDesign,
        parent: Optional["QMainWindowPlot"] = None,
        logger=None,
        statusbar_label=None,
    ):
        """
        Args:
            design (QDesign): The design.
            parent (QMainWindowPlot): The main window.  Defaults to None.
            logger (logging.Logger): The logger.  Defaults to None.
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

        # Silence benign matplotlib aspect-ratio warnings while leaving other warnings visible.
        warnings.filterwarnings(
            "ignore",
            message=r".*Ignoring fixed .* limits to fulfill fixed data aspect.*",
        )

        # Drop the matching Matplotlib logger messages emitted during pan/resize autoscale.
        class _IgnoreFixedAspect(logging.Filter):
            def filter(self, record):
                msg = record.getMessage()
                return (
                    "Ignoring fixed" not in msg
                    or "limits to fulfill fixed data aspect" not in msg
                )

        logging.getLogger("matplotlib.axes._base").addFilter(_IgnoreFixedAspect())

        with mpl.rc_context(rc=self.mpl_context):
            fig = Figure()

        self.axes = []
        self.current_axis = 0
        self.logger = logger
        self.statusbar_label = statusbar_label
        self.design = design
        self._state = {}  # used to store state between drawing
        # used to keep track of what we will need to delete
        self._annotations = {"text": [], "patch": []}

        super().__init__(fig)

        self.setParent(parent)

        # Explicit rather than trusting the backend default: a click-select
        # (_on_pick_release, below) needs the canvas to actually be
        # focusable, or the arrow-key nudge it enables silently goes
        # nowhere -- keys keep going to whatever dock (e.g. the component
        # list) had focus before the click.
        self.setFocusPolicy(Qt.StrongFocus)

        # Without this, Qt only sends mouseMoveEvent (and so matplotlib's
        # motion_notify_event) while a button is held down -- pure hover
        # motion never reaches the canvas at all. The status-bar hover
        # readout (PanAndZoom._report_hover_position) depends on exactly
        # that, and silently never fires without it: it looked "frozen"
        # under real mouse movement despite working under QTest's
        # synthetic mouseMove, which injects the event directly and
        # doesn't depend on this setting.
        self.setMouseTracking(True)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.panzoom = PanAndZoom(self.figure)
        self.panzoom.logger = self.logger
        self.panzoom._statusbar_label = self.statusbar_label

        self.setup_figure_and_axes()

        self.metal_renderer = QMplRenderer(
            canvas=self, design=self.design, logger=logger
        )

        # Click-to-select. Rebuilt lazily; invalidated by every plot().
        self._pick_tree = None
        self._pick_names = []
        self._press_xy = None
        self.figure.canvas.mpl_connect("button_press_event", self._on_pick_press)
        self.figure.canvas.mpl_connect("button_release_event", self._on_pick_release)

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
        plt.style.use("fast")

        mpl.rcParams["path.simplify"] = self.config.path_simplify
        mpl.rcParams["path.simplify_threshold"] = self.config.path_simplify_threshold
        mpl.rcParams["agg.path.chunksize"] = self.config.chunksize

    def get_axis(self):
        """Gets the current axis."""
        return self.axes[self.current_axis]

    def _plot(self, ax):
        """Set the axes.

        Args:
            ax (matplotlib.axes.Axes): axes
        """
        self.metal_renderer.render(ax)
        # ax.set_xlabel('X (mm)')
        # ax.set_ylabel('y (mm)')

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
            self._state["xlim"] = ax.get_xlim()
            self._state["ylim"] = ax.get_ylim()

        def main_plot():
            # for temporary style
            with mpl.rc_context(rc=self.mpl_context):
                if clear:
                    self.clear_axis(ax)
                self._plot(ax)
                self._watermark_axis(ax)

        def final():
            # Restore the view BEFORE drawing. ``clear_axis`` resets the axes
            # and ``_plot`` re-autoscales to the new data, so at this point the
            # axes hold the autoscaled view rather than the user's. ``draw()``
            # renders the canvas buffer from whatever the limits are *at that
            # moment*; restoring them afterwards fixes the axes but leaves the
            # buffer showing the autoscaled view. The user sees the view jump
            # on edit, then snap back on the next interaction-driven redraw.
            if "xlim" in self._state:
                ax.set_xlim(self._state["xlim"])
                ax.set_ylim(self._state["ylim"])
            self.draw()
            self.show()

        # The drawn geometry is about to change, so any cached hit-test index
        # is stale. Rebuilt lazily on the next click.
        self._invalidate_pick_index()

        # ``prep`` must run on both paths: ``final`` restores from
        # ``self._state``, so skipping it would replay a previous plot's view.
        prep()

        if with_try:
            # speed impact?
            try:
                main_plot()

            except Exception as e:
                log_error_easy(self.logger, post_text=f"Plotting error: {e}")

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
        kw = dict(
            fontsize=15, color="gray", ha="right", va="bottom", alpha=0.18, zorder=-100
        )
        ax.annotate(
            "Qiskit / Quantum Metal", xy=(0.98, 0.02), xycoords="axes fraction", **kw
        )

        file = self.gui.path_imgs / "metal_logo.png"
        if file.is_file():
            # print(f'Found {file} for watermark.')
            _axis_set_watermark_img(ax, file, size=0.15)
        else:
            # import error?
            self.logger.error(f"Error could not load {file} for watermark.")

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

        Combines a synchronous ``self.draw()`` with ``draw_idle()``: the
        latter schedules a redraw on the next Qt event-loop iteration,
        which catches the case where ``self.draw()`` runs before the
        underlying axes have been laid out (a real bug observed when
        :meth:`highlight_components` is called immediately after
        component instantiation — the rectangles + labels were appended
        to the axes but not visible until the user manually called
        ``refresh_plot()`` again).
        """
        self.update()  # not sure if needed
        # No ``flush_events()`` here: it spins a nested Qt event loop inside
        # every refresh -- including the ones during startup, before the
        # window has finished showing -- so any queued paint/resize/timer
        # event could re-enter the GUI mid-call. ``draw()`` below is
        # synchronous and ``draw_idle()`` covers the late-layout case.
        self.draw()
        self.draw_idle()

    def style_axis(self, ax, num: int):
        """Style the axis.

        Args:
            ax (axis): The axis
            num (int): Not used
        """
        ax.set_aspect(1)
        # # If 'box', change the physical dimensions of the Axes. If 'datalim',
        # # change the x or y data limits.
        ax.set_adjustable("datalim")
        ax.set_anchor("C")  # Center the plot

        # Set axis scales to be equal
        ax.set_xscale("linear")
        ax.set_yscale("linear")

        # Ensure data units are equal
        ax.set_box_aspect(None)

        ax.set_xlabel("x position (mm)")
        ax.set_ylabel("y position (mm)")

        # Zero lines
        kw = dict(c="k", lw=1, zorder=-1, alpha=0.5)
        ax.axhline(0, **kw)
        ax.axvline(0, **kw)

        # Grid
        kw = dict(
            color="#CCCCCC",
            # zorder = -100,
            # alpha = 0.8,
            # fillstyle='left'
            # markevery=(1,1),
            # sketch_params=1
        )
        if 0:  # fix tick spacing
            loc = mpl.ticker.MultipleLocator(base=0.1)
            ax.xaxis.set_major_locator(loc)
            ax.yaxis.set_major_locator(loc)

        ax.grid(which="major", linestyle="--", **kw)
        ax.grid(which="minor", linestyle=":", **kw)
        ax.set_axisbelow(True)

        # [left, bottom, width, height]
        # ax.set_position([0,0,1,1])

    def style_figure(self):
        """Style a figure."""
        # self.figure.tight_layout()

    # ------------------------------------------------------------------
    # Click-to-select
    # ------------------------------------------------------------------

    #: A press and release within this many pixels counts as a click rather
    #: than a drag. Matches the threshold ``_zoom_area`` uses to ignore
    #: accidental rubber-band drags, so pan and select agree on the boundary.
    CLICK_PIXEL_TOLERANCE = 3

    #: Click tolerance in pixels, converted to data units at query time.
    #: Routes are zero-width paths, so an exact point-in-polygon test would
    #: make them practically unclickable.
    PICK_PIXEL_TOLERANCE = 5

    def _invalidate_pick_index(self):
        """Drop the cached hit-test index.

        Called whenever the drawn geometry may have changed. Rebuilding is
        deferred to the next click, so a rebuild-heavy session does not pay
        for an index nobody queries.
        """
        self._pick_tree = None
        self._pick_names = []

    def _build_pick_index(self):
        """Build an R-tree over every component's geometry.

        Hit-testing every polygon linearly would make a click cost O(n) on a
        design with hundreds of components. ``STRtree`` gives a spatial index
        instead, built once per rebuild and queried per click.
        """
        from shapely import STRtree  # local: keeps import cost off startup

        geometries = []
        names = []
        for name in self.design.components:
            try:
                shapes = self.design.components[name].qgeometry_list()
            except Exception:  # pragma: no cover — defensive
                continue
            for shape in shapes:
                if shape is None or shape.is_empty:
                    continue
                geometries.append(shape)
                names.append(name)

        self._pick_names = names
        self._pick_tree = STRtree(geometries) if geometries else None

    def component_at_point(self, x: float, y: float, tolerance: float = None):
        """Return the name of the component under a data-space point.

        Args:
            x (float): X in data (mm) coordinates.
            y (float): Y in data (mm) coordinates.
            tolerance (float): Search radius in data units. Defaults to
                :attr:`PICK_PIXEL_TOLERANCE` pixels converted to data units.

        Returns:
            str: Component name, or None if the point hits nothing.
        """
        if self._pick_tree is None:
            self._build_pick_index()
        if self._pick_tree is None:  # still nothing to hit
            return None

        from shapely.geometry import Point

        if tolerance is None:
            tolerance = self._pixels_to_data(self.PICK_PIXEL_TOLERANCE)

        probe = Point(x, y).buffer(tolerance)
        hits = self._pick_tree.query(probe)
        if len(hits) == 0:
            return None

        # query() is bounding-box based, so confirm a real intersection and
        # prefer the closest match when several overlap.
        best_name, best_distance = None, None
        point = Point(x, y)
        for index in hits:
            geometry = self._pick_tree.geometries.take(index)
            distance = geometry.distance(point)
            if distance > tolerance:
                continue
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_name = self._pick_names[index]
        return best_name

    def _pixels_to_data(self, pixels: float) -> float:
        """Convert a pixel distance to data units at the current zoom.

        Args:
            pixels (float): Distance in display pixels.

        Returns:
            float: The same distance in data units.
        """
        ax = self.get_axis()
        try:
            origin = ax.transData.inverted().transform((0, 0))
            offset = ax.transData.inverted().transform((pixels, 0))
            return abs(offset[0] - origin[0])
        except Exception:  # pragma: no cover — defensive
            return 0.0

    def _on_pick_press(self, event):
        """Record where a press started, to tell a click from a drag.

        Args:
            event: Matplotlib mouse event.
        """
        if event.button == 1:
            self._press_xy = (event.x, event.y)

    def _on_pick_release(self, event):
        """Select the component under the cursor, if this was a click.

        Left-drag pans, so a release is only treated as a selection when the
        pointer barely moved. Without that check every pan would also
        re-select whatever happened to be under the release point.

        Args:
            event: Matplotlib mouse event.
        """
        press_xy, self._press_xy = self._press_xy, None

        if event.button != 1 or press_xy is None:
            return
        if event.xdata is None or event.ydata is None:
            return
        if (
            abs(event.x - press_xy[0]) > self.CLICK_PIXEL_TOLERANCE
            or abs(event.y - press_xy[1]) > self.CLICK_PIXEL_TOLERANCE
        ):
            return  # a drag (pan), not a click

        name = self.component_at_point(event.xdata, event.ydata)
        if name is None:
            return

        # ``logger`` is an optional constructor argument, so it can be None.
        if self.logger is not None:
            self.logger.info(f"Selected component: {name}")
        gui = getattr(self, "gui", None)
        already_selected = (
            gui is not None and getattr(gui, "selected_component", None) == name
        )
        if gui is not None and hasattr(gui, "edit_component"):
            gui.edit_component(name)
        self.highlight_components([name])

        # A real double-click (event.dblclick, matplotlib's own flag) or a
        # second click on the component already selected -- either reads
        # as "I want to work on this one" -- brings the Edit dock to the
        # front. edit_component() above already populates it regardless;
        # this only handles whether the user can actually *see* that
        # without hunting through tabs for it.
        #
        # This is ``dockComponent``, titled "Edit component" -- not
        # ``dockDesign`` (titled "QComponents", the component *list*).
        # The two are named the opposite of what they hold; an earlier
        # version of this code raised ``dockDesign`` by mistake, which
        # brought the list to the front instead of the actual editor.
        if getattr(event, "dblclick", False) or already_selected:
            main_window = getattr(gui, "main_window", None)
            dock_component = getattr(
                getattr(main_window, "ui", None), "dockComponent", None
            )
            if dock_component is not None:
                # Not dock_component.doShow() -- that's the toggle-aware
                # version (see #48). dockComponent isn't tabified with
                # anything, so there's no "already the active tab" case to
                # avoid, but doShowHighlighWidget also gives the nicer
                # highlight-flash feedback than the plain show()+raise_()
                # that QTableView_AllComponents.viewClicked uses.
                doShowHighlighWidget(dock_component)

        # gui.edit_component() above populates the component list / options
        # tree, which steals keyboard focus if either already had it. Take
        # it back explicitly so the arrow-key nudge the selection hint
        # promises actually goes to the canvas, not to whichever dock last
        # held focus.
        self.setFocus(Qt.MouseFocusReason)

    #: Grid step for one arrow-key press, in millimetres.
    NUDGE_STEP_MM = 0.05

    #: Multipliers for the modifier keys. Shift coarsens, Alt refines --
    #: the convention every drawing tool uses.
    NUDGE_COARSE_FACTOR = 10.0
    NUDGE_FINE_FACTOR = 0.1

    #: Arrow key -> unit displacement (x, y). Y is positive upward, matching
    #: the data coordinates rather than screen coordinates.
    _NUDGE_DIRECTIONS = {
        Qt.Key_Left: (-1, 0),
        Qt.Key_Right: (1, 0),
        Qt.Key_Down: (0, -1),
        Qt.Key_Up: (0, 1),
    }

    #: Rotation step for one bracket-key press, in degrees. 90 is the
    #: common case (most qlibrary layouts are built on a 90-degree grid);
    #: Shift gives finer control for anything off-grid.
    ROTATE_STEP_DEG = 90.0
    ROTATE_FINE_DEG = 15.0

    #: Key -> rotation direction. ``]``/``[`` turn clockwise/counter-
    #: clockwise -- the same visual sense the characters read in on a
    #: standard keyboard layout. Also bound to Q/E (the widely-recognized
    #: rotate-CCW/CW convention from games and other creative tools) as
    #: the more discoverable, keyboard-layout-independent alternative --
    #: added after a user found ] and [ hard to remember and reached for
    #: different keys entirely on first try.
    #:
    #: Key_BraceLeft/Key_BraceRight (curly braces) are included alongside
    #: the bracket keys deliberately, not redundantly: on most keyboards
    #: Shift+[ produces "{", which Qt reports as Key_BraceLeft -- a
    #: different key code entirely, not Key_BracketLeft with a Shift
    #: modifier flag. Without this, holding Shift for the fine rotation
    #: step silently missed the lookup and did nothing at all (confirmed:
    #: a user found plain [/] rotated fine, but Shift+[/Shift+] did
    #: nothing, while Shift+Q/Shift+E -- letters, whose Key_* value
    #: doesn't change when shifted -- worked correctly).
    _ROTATE_DIRECTIONS = {
        Qt.Key_BracketRight: -1,
        Qt.Key_BracketLeft: +1,
        Qt.Key_BraceRight: -1,
        Qt.Key_BraceLeft: +1,
        Qt.Key_E: -1,
        Qt.Key_Q: +1,
    }

    def keyPressEvent(self, event):
        """Nudge or rotate the selected component with the keyboard.

        Lives here, not on the ``QMainWindowPlot`` container that used to
        own this logic, because this canvas -- not its parent -- is the
        widget that actually holds keyboard focus after a click-select
        (see ``_on_pick_release``'s ``setFocus`` above). ``FigureCanvas``
        (the base class) has its own ``keyPressEvent`` for matplotlib's
        built-in shortcuts and does not propagate unhandled keys to the
        parent, so a handler on the container was simply never reached --
        confirmed by sending a real ``QTest``-injected key both ways: to
        this canvas (silently swallowed) and directly to
        ``QMainWindowPlot`` (moved the component correctly). Deliberately
        keyboard-only: dragging would have to share the left mouse button
        with panning and needs a live preview, and a rebuild per
        mouse-move is far too slow.

        Args:
            event (QKeyEvent): The key event.
        """
        modifiers = event.modifiers()

        direction = self._NUDGE_DIRECTIONS.get(event.key())
        if direction is not None:
            step = self.NUDGE_STEP_MM
            if modifiers & Qt.ShiftModifier:
                step *= self.NUDGE_COARSE_FACTOR
            elif modifiers & Qt.AltModifier:
                step *= self.NUDGE_FINE_FACTOR
            self.gui.nudge_selected(direction[0] * step, direction[1] * step)
            return

        rotate_dir = self._ROTATE_DIRECTIONS.get(event.key())
        if rotate_dir is not None:
            step = (
                self.ROTATE_FINE_DEG
                if modifiers & Qt.ShiftModifier
                else self.ROTATE_STEP_DEG
            )
            self.gui.rotate_selected(rotate_dir * step)
            return

        super().keyPressEvent(event)

    def _component_bounds(self, component_names=None):
        """Union of the qgeometry bounds of the named components.

        Args:
            component_names (List[str]): Components to include. Defaults to
                every component in the design.

        Returns:
            tuple: ``(xmin, ymin, xmax, ymax)``, or None when nothing has
            usable bounds (an empty design, or components that failed to
            build).
        """
        if component_names is None:
            component_names = list(self.design.components.keys())

        xmins, ymins, xmaxs, ymaxs = [], [], [], []
        for name in component_names:
            if name not in self.design.components:
                continue
            try:
                xmin, ymin, xmax, ymax = self.design.components[name].qgeometry_bounds()
            except Exception:  # pragma: no cover — defensive
                continue
            xmins.append(xmin)
            ymins.append(ymin)
            xmaxs.append(xmax)
            ymaxs.append(ymax)

        if not xmins:
            return None
        return min(xmins), min(ymins), max(xmaxs), max(ymaxs)

    def _set_limits(self, bounds, pad_fraction=0.1):
        """Frame the given bounds with padding.

        Args:
            bounds (tuple): ``(xmin, ymin, xmax, ymax)``.
            pad_fraction (float): Margin as a fraction of each extent.
        """
        xmin, ymin, xmax, ymax = bounds
        dx = (xmax - xmin) * pad_fraction or 0.1
        dy = (ymax - ymin) * pad_fraction or 0.1
        for ax in self.figure.axes:
            ax.set_xlim(xmin - dx, xmax + dx)
            ax.set_ylim(ymin - dy, ymax + dy)

    def auto_scale(self, include_chip: bool = False):
        """Frame the design.

        Args:
            include_chip (bool): Frame the whole chip rather than just the
                components. Defaults to False.

        Notes:
            The default deliberately ignores the chip. ``QMplRenderer`` draws
            the die outline, so a plain ``ax.autoscale()`` frames the full
            chip -- a default 9x6mm die around a 0.65mm transmon leaves the
            component an unreadable speck. The tutorials were all written
            assuming the chip is ignored.

            Falls back to framing everything when no component has usable
            bounds, so an empty design still shows the chip rather than an
            arbitrary window.
        """
        if not include_chip:
            bounds = self._component_bounds()
            if bounds is not None:
                self._set_limits(bounds)
                self.refresh()
                return

        for ax in self.figure.axes:
            ax.autoscale()
        self.refresh()

    def zoom_on_components(self, component_names):
        """Zoom the canvas to fit the bounding box of the given components.

        Args:
            component_names (List[str]): Component names to frame.

        Notes:
            Double-clicking a row in the ``QComponents`` table calls
            ``gui.canvas.zoom_on_components([name])``. Before this method
            was added that path raised ``AttributeError`` (the
            ``MetalGUIHeadless`` viewer always had it; the Qt canvas
            didn't). 10 % padding is added around the combined bbox.
        """
        bounds = self._component_bounds(component_names)
        if bounds is None:
            return
        self._set_limits(bounds)
        self.refresh()

    def welcome_message(self):
        """The GUI displays a message to let users know they are using Qiskit
        Metal."""

        self._welcome_text = AnimatedText(
            self.axes[0],
            "Welcome to Quantum Metal!",
            self,
            start=False,
            kw={"fontsize": 20},
        )

        self._welcome_start_timer = single_shot(self, 250, self._welcome_message_start)

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

    def find_component_bounds(self, components: list[str], zoom: float = 1.2):
        """Find bounds of a set of components.

        Args:
            components (List[str]): A list of component names
            zoom (float): Fraction to expand the bounding vbox by

        Returns:
            List: List of x,y coordinates defining the bounding box
        """
        if len(components) == 0:
            self.logger.error("At least one component must be provided.")
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
                max(newbounds[3], bounds[3]),
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
                for patch in self._annotations["patch"]:
                    # ax.patches.remove(patch)
                    # print(patch)
                    patch.remove()
                for text in self._annotations["text"]:
                    # ax.texts.remove(patch)
                    text.remove()
        except Exception as e:
            self.logger.error(f"While canvas clear_annotation: {e}")
        finally:
            self._force_clear_annotations()

    def _force_clear_annotations(self):
        """Clear annotation dicts."""
        self._annotations["patch"] = []
        self._annotations["text"] = []

    def highlight_all_components(self, show_pins: bool = True):
        """Highlight and label every component in the design.

        Args:
            show_pins (bool): Also draw pin arrows and pin names.
                Defaults to True.

        Returns:
            int: Number of components labelled.
        """
        names = list(self.design.components.keys())
        self.highlight_components(names, show_pins=show_pins)
        return len(names)

    def highlight_components(self, component_names: list[str], show_pins: bool = True):
        """Highlight a list of components.

        Args:
            component_names (List[str]): A list of component names
            show_pins (bool): Draw pin arrows and pin names alongside the
                component name. Turn off on dense chips, where per-pin
                labels swamp the component labels. Defaults to True.
        """
        # Defaults - todo eventually move to some option place where can be changed
        text_kw = dict(
            color="r",
            alpha=0.75,
            verticalalignment="center",
            horizontalalignment="center",
            clip_on=True,
            zorder=99,
            fontweight="bold",
        )
        text_bbox_kw = dict(facecolor="#FFFFFF", alpha=0.75, edgecolor="#F0F0F0")

        # Functionality
        self.clear_annotation()

        component_id_list = self.design.components.get_list_ints(component_names)
        for component_id in component_id_list:
            component_id = int(component_id)

            if component_id in self.design._components:
                component: "QComponent" = self.design._components[component_id]

                if 1:  # highlight bounding box
                    bounds = (
                        component.qgeometry_bounds()
                    )  # returns (minx, miny, maxx, maxy)
                    # bbox = Bbox.from_extents(bounds)
                    # Create a Rectangle patch TODO: move to settings
                    kw = dict(
                        linewidth=1,
                        edgecolor="r",
                        facecolor=(1, 0, 0, 0.05),
                        zorder=100,
                        ls="--",
                    )
                    rect = patches.Rectangle((0, 0), 0, 0, **kw)

                    lbwh = [
                        bounds[0],
                        bounds[1],
                        bounds[2] - bounds[0],
                        bounds[3] - bounds[1],
                    ]
                    rect.set_bounds(*lbwh)
                    self._annotations["patch"] += [rect]
                    for ax in self.axes:
                        ax.add_patch(rect)

                    if 1:  # Draw name as text of QComponent
                        text = matplotlib.text.Text(
                            (bounds[0] + bounds[2]) / 2.0,
                            (bounds[1] + bounds[3]) / 2.0,
                            str(component.name),
                            **{**text_kw, **dict(fontsize=13)},
                        )
                        text.set_bbox(
                            {**text_bbox_kw, **dict(edgecolor=None)}
                        )  # dict(facecolor=(1, 0, 0, 0.25)))
                        for ax in self.axes:
                            ax.add_artist(text)
                        self._annotations["text"] += [text]

                if show_pins:  # Draw the pins
                    # for component_id in self.design.components.keys():
                    for pin_name in component.pins.keys():
                        # self.logger.debug(f'Pin {pin_name}')
                        pin = component.pins[pin_name]
                        m = pin["middle"]
                        n = pin["normal"]

                        if 1:  # draw the arrows
                            kw = dict(
                                color="r",
                                mutation_scale=15,
                                alpha=0.75,
                                capstyle="butt",
                                ec="k",
                                lw=0.5,
                                zorder=100,
                                clip_on=True,
                            )
                            arrow = patches.FancyArrowPatch(m, m + n * 0.05, **kw)
                            self._annotations["patch"] += [arrow]
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
                                **dict(
                                    horizontalalignment="left" if n[0] >= 0 else "right"
                                ),
                            }
                            text: "matplotlib.text.Text" = ax.text(
                                *(m + dist * n), pin_name, **kw
                            )
                            text.set_bbox(text_bbox_kw)
                            self._annotations["text"] += [text]

        self.refresh()

    def debug_axis_config(self, ax=None):
        """Print axis configuration for debugging."""
        if ax is None:
            ax = self.get_axis()

        print("======= AXES CONFIG =======")
        print("aspect:        ", ax.get_aspect())
        print("adjustable:    ", ax.get_adjustable())
        print("anchor:        ", ax.get_anchor())
        print("box_aspect:    ", ax.get_box_aspect())
        print("xlim:          ", ax.get_xlim())
        print("ylim:          ", ax.get_ylim())
        print("xscale / yscale:", ax.get_xscale(), "/", ax.get_yscale())
        print("data_ratio:    ", ax.get_data_ratio())
        try:
            print("data_ratio_log:", ax.get_data_ratio_log())
        except Exception:
            pass
        print("position bbox: ", ax.get_position())
        print("===========================")
