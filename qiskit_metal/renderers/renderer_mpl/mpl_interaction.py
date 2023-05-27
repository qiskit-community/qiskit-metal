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

# /*##########################################################################
#
# Copyright (c) 2016 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""Pan and zoom interaction to plug on a matplotlib Figure.

Interaction:
    - Zoom in/out with the mouse wheel
    - Pan figures by dragging the mouse with left button pressed
    - Select a zoom-in area by dragging the mouse with right button pressed

It provides a figure_pz function to create a Figure with interaction.

Example:

.. code-block:: python

    import matplotlib.pyplot as plt
    from mpl_interaction import figure_pz
    fig = figure_pz()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot((1, 2, 1))
    plt.show()

The :class:`PanAndZoom` class can be used to add interaction
to an existing Figure.

Example:

.. code-block:: python

    import matplotlib.pyplot as plt
    from mpl_interaction import PanAndZoom
    fig = plt.figure()
    pan_zoom = PanAndZoom(fig)  # Add support for pan and zoom
    ax = fig.add_subplot(1, 1, 1)
    ax.plot((1, 2, 1))
    plt.show()

Known limitations:
    - Only support linear and log scale axes.
    - Zoom area not working well with keep aspect ratio.
    - Interfere with matplotlib toolbar.
"""

import logging
import math
import warnings
import weakref

import matplotlib.pyplot as _plt
import numpy

from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QLabel

from ... import Dict

__all__ = ['figure_pz', 'MplInteraction', 'PanAndZoom']


class MplInteraction(object):
    """Base class for class providing interaction to a matplotlib Figure."""

    def __init__(self, figure):
        """
        Args:
            figure (figure): The matplotlib figure to attach the behavior to.
        """
        self._fig_ref = weakref.ref(figure)
        self._cids = []

    def __del__(self):
        """Disconnect."""
        self.disconnect()

    def _add_connection(self, event_name, callback):
        """Called to add a connection to an event of the figure.

        Args:
            event_name (str): The matplotlib event name to connect to.
            callback (callback): The callback to register to this event.
        """
        cid = self.figure.canvas.mpl_connect(event_name, callback)
        self._cids.append(cid)

    def disconnect(self):
        """Disconnect interaction from Figure."""
        if self._fig_ref is not None:
            figure = self._fig_ref()
            if figure is not None:
                for cid in self._cids:
                    figure.canvas.mpl_disconnect(cid)
            self._fig_ref = None

    @property
    def figure(self):
        """The Figure this interaction is connected to or None if not
        connected."""
        return self._fig_ref() if self._fig_ref is not None else None

    def _axes_to_update(self, event):
        """Returns two sets of Axes to update according to event. Takes care of
        multiple axes and shared axes.

        Args:
            event (MouseEvent): Matplotlib event to consider

        Returns:
            tuple: Axes for which to update xlimits and ylimits.
            2-tuple of set (xaxes, yaxes)
        """
        x_axes, y_axes = set(), set()

        # Go through all axes to enable zoom for multiple axes subplots
        for ax in self.figure.axes:
            if ax.contains(event)[0]:
                # For twin x axes, makes sure the zoom is applied once
                shared_x_axes = set(ax.get_shared_x_axes().get_siblings(ax))
                if x_axes.isdisjoint(shared_x_axes):
                    x_axes.add(ax)

                # For twin y axes, makes sure the zoom is applied once
                shared_y_axes = set(ax.get_shared_y_axes().get_siblings(ax))
                if y_axes.isdisjoint(shared_y_axes):
                    y_axes.add(ax)

        return x_axes, y_axes

    def _draw(self):
        """Convenient method to redraw the figure."""
        self.figure.canvas.draw()


class ZoomOnWheel(MplInteraction):
    """Class providing zoom on wheel interaction to a matplotlib Figure.

    This class extends the `MplInteraction` class.

    Supports subplots, twin Axes and log scales.
    """

    def __init__(self, figure=None, scale_factor=1.1):
        """
        Args:
            figure (figure): The matplotlib figure to attach the behavior to.
            scale_factor (float): The scale factor to apply on wheel event.
        """
        super(ZoomOnWheel, self).__init__(figure)
        self._add_connection('scroll_event', self._on_mouse_wheel)

        self.scale_factor = scale_factor

    @staticmethod
    def _zoom_range(begin, end, center, scale_factor, scale):
        """Compute a 1D range zoomed around center.

        Args:
            begin (float): The begin bound of the range
            end (float): The end bound of the range
            center (float): The center of the zoom (i.e., invariant point)
            scale_factor (float): The scale factor to apply
            scale (str): The scale of the axis

        Returns:
            tuple: The zoomed range (min, max)
        """
        if begin < end:
            min_, max_ = begin, end
        else:
            min_, max_ = end, begin

        if scale == 'linear':
            old_min, old_max = min_, max_
        elif scale == 'log':
            old_min = numpy.log10(min_ if min_ > 0. else numpy.nextafter(0, 1))
            center = numpy.log10(center if center >
                                 0. else numpy.nextafter(0, 1))
            old_max = numpy.log10(max_) if max_ > 0. else 0.
        else:
            logging.warning('Zoom on wheel not implemented for scale "%s"' %
                            scale)
            return begin, end

        offset = (center - old_min) / (old_max - old_min)
        range_ = (old_max - old_min) / scale_factor
        new_min = center - offset * range_
        new_max = center + (1. - offset) * range_

        if scale == 'log':
            try:
                new_min, new_max = 10.**float(new_min), 10.**float(new_max)
            except OverflowError:  # Limit case
                new_min, new_max = min_, max_
            if new_min <= 0. or new_max <= 0.:  # Limit case
                new_min, new_max = min_, max_

        if begin < end:
            return new_min, new_max
        else:
            return new_max, new_min

    def _on_mouse_wheel(self, event):
        """Mouse wheel event."""
        if event.step > 0:
            scale_factor = self.scale_factor
        else:
            scale_factor = 1. / self.scale_factor

        # Go through all axes to enable zoom for multiple axes subplots
        x_axes, y_axes = self._axes_to_update(event)

        for ax in x_axes:
            transform = ax.transData.inverted()
            xdata, ydata = transform.transform_point((event.x, event.y))

            xlim = ax.get_xlim()
            xlim = self._zoom_range(xlim[0], xlim[1], xdata, scale_factor,
                                    ax.get_xscale())
            ax.set_xlim(xlim)

        for ax in y_axes:
            ylim = ax.get_ylim()
            ylim = self._zoom_range(ylim[0], ylim[1], ydata, scale_factor,
                                    ax.get_yscale())
            ax.set_ylim(ylim)

        if x_axes or y_axes:
            self._draw()


class PanAndZoom(ZoomOnWheel):
    """Class providing pan & zoom interaction to a matplotlib Figure. Left
    button for pan, right button for zoom area and zoom on wheel. Support
    subplots, twin Axes and log scales.

    This class extends the `ZoomOnWheel` class.
    """

    def __init__(self, figure=None, scale_factor=1.1):
        """
        Args:
            figure (figure): The matplotlib figure to attach the behavior to.
            scale_factor (float): The scale factor to apply on wheel event.
        """
        super(PanAndZoom, self).__init__(figure, scale_factor)
        self._add_connection('button_press_event', self._on_mouse_press)
        self._add_connection('button_release_event', self._on_mouse_release)
        self._add_connection('motion_notify_event', self._on_mouse_motion)

        self._pressed_button = None  # To store active button
        self._axes = None  # To store x and y axes concerned by interaction
        self._event = None  # To store reference event during interaction

        self.options = Dict(dict(report_point_position=True,))
        self.logger = None
        self._statusbar_label = None

        # self._get_images_path()
        # self._add_toolbar_tools()
        self._style_figure()

        self._ix_iy_old = (0, 0)

    def _get_images_path(self):
        """Get the path to images.

        Returns:
            str: path

        Raises:
            Exception: path error
        """
        # to be removed
        try:  # Get tool image path
            from pathlib import Path
            from ... import _gui
            imgs_path = Path(_gui.__file__).parent / '_imgs'
            if imgs_path.is_dir() == False:
                print(f'Bad File path for images! {imgs_path}')
                imgs_path = None
        except Exception as e:
            print('ERROR: ', e)
            imgs_path = None
        self.imgs_path = imgs_path

        return imgs_path

    def _add_toolbar_tools(self):
        """Add tools."""
        # TODO: Outdated - to be removed

        from matplotlib.backend_tools import ToolToggleBase  # ToolBase

        class ToolPointPosition(ToolToggleBase):
            """Tools."""
            default_keymap = 'Ctrl+p'
            description = 'Click to get point coordinate printed'
            default_toggled = False
            image = None  # str(imgs_path)

            def __init__(self, *args, parent=None, **kwargs):
                super().__init__(*args, **kwargs)
                if parent is None:
                    raise ('Pass a parent')
                self.parent = parent

            def enable(self, *args):
                self.parent.options.report_point_position = True

            def disable(self, *args):
                self.parent.options.report_point_position = False

        fig = self.figure
        imgs_path = self.imgs_path
        # pylint: disable=attribute-defined-outside-init
        toolbar = self.toolbar = fig.canvas.manager.toolbar

        # Get tool manager

        # TODO: Remove use of tool manager just use PySide2 bare as below

        # ToolbarQt   --- https://github.com/matplotlib/matplotlib/blob/master/lib/matplotlib/backends/backend_qt5.py
        tm = fig.canvas.manager.toolmanager

        self.tm = tm
        # Tool: Print point location
        ToolPointPosition.image = str(imgs_path / 'click.png')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tm.add_tool("Point_position", ToolPointPosition, parent=self)
        fig.canvas.manager.toolbar.add_tool(tm.get_tool("Point_position"),
                                            "toolgroup")

        # Tool: Copy to Clipboard
        from matplotlib.backend_tools import ToolCopyToClipboard
        ToolCopyToClipboard.image = str(imgs_path / 'copy.png')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # OVvrwties Ctrl+C and issues warning
            tm.add_tool("Copy_to_clipboard", ToolCopyToClipboard)
        fig.canvas.manager.toolbar.add_tool(tm.get_tool("Copy_to_clipboard"),
                                            "toolgroup")

        if 1:  # add QT Pieces
            toolbar.action_ascale = QAction(
                QIcon(str(imgs_path / 'auto_zoom.png')), 'Auto scale', toolbar)
            toolbar.action_ascale.setShortcut('A')
            toolbar.action_ascale.setShortcutContext(Qt.WindowShortcut)
            toolbar.action_ascale.setStatusTip('Autoscale')
            toolbar.action_ascale.triggered.connect(self.auto_scale)
            toolbar.addAction(toolbar.action_ascale)

        # Status Bar: Second label to report
        figManager = fig.canvas.manager  # plt.get_current_fig_manager()
        status_bar = figManager.window.statusBar()
        self._status_label_2 = QLabel(status_bar)
        self._status_label_2.setText('')
        status_bar.addWidget(self._status_label_2)
        #from matplotlib.backends.backend_qt5 import StatusbarQt
        #st = StatusbarQt(figManager.window, figManager.toolmanager)
        # figManager.statusbar.set_message('')

    def auto_scale(self):
        """Auto scaler."""
        for ax in self.figure.axes:
            ax.autoscale()
        # self.figure.canvas.flush_events()
        self.figure.canvas.draw()

    def _style_figure(self):
        """Style figure."""
        #self.figure.dpi = 150
        pass

    @staticmethod
    def _pan_update_limits(ax, axis_id, event, last_event):
        """Compute limits with applied pan.

        Args:
            axis_id (int): ID of the axis
            event (event): The event
            last_event (event): The previous event

        Returns:
            double: New limit

        Raises:
            ValueError: Value error
            OverflowError: Overflow error
        """
        assert axis_id in (0, 1)
        if axis_id == 0:
            lim = ax.get_xlim()
            scale = ax.get_xscale()
        else:
            lim = ax.get_ylim()
            scale = ax.get_yscale()

        pixel_to_data = ax.transData.inverted()
        data = pixel_to_data.transform_point((event.x, event.y))
        last_data = pixel_to_data.transform_point((last_event.x, last_event.y))

        if scale == 'linear':
            delta = data[axis_id] - last_data[axis_id]
            new_lim = lim[0] - delta, lim[1] - delta
        elif scale == 'log':
            try:
                delta = math.log10(data[axis_id]) - \
                    math.log10(last_data[axis_id])
                new_lim = [
                    pow(10., (math.log10(lim[0]) - delta)),
                    pow(10., (math.log10(lim[1]) - delta))
                ]
            except (ValueError, OverflowError):
                new_lim = lim  # Keep previous limits
        else:
            logging.warning('Pan not implemented for scale "%s"' % scale)
            new_lim = lim
        return new_lim

    def _pan(self, event):
        """Pan.

        Args:
            event (event): The event
        """
        if event.name == 'button_press_event':  # begin pan
            self._event = event

        elif event.name == 'button_release_event':  # end pan
            self._event = None

        elif event.name == 'motion_notify_event':  # pan
            if self._event is None:
                return

            if event.x != self._event.x:
                for ax in self._axes[0]:
                    xlim = self._pan_update_limits(ax, 0, event, self._event)
                    ax.set_xlim(xlim)

            if event.y != self._event.y:
                for ax in self._axes[1]:
                    ylim = self._pan_update_limits(ax, 1, event, self._event)
                    ax.set_ylim(ylim)

            if event.x != self._event.x or event.y != self._event.y:
                self._draw()

            self._event = event

    def _zoom_area(self, event):
        """Zoom.

        Args:
            event (event): The event
        """
        if event.name == 'button_press_event':  # begin drag
            self._event = event
            # pylint: disable=attribute-defined-outside-init
            self._patch = _plt.Rectangle(xy=(event.xdata, event.ydata),
                                         width=0,
                                         height=0,
                                         fill=False,
                                         linewidth=1.,
                                         linestyle='solid',
                                         color='black')
            self._event.inaxes.add_patch(self._patch)

        elif event.name == 'button_release_event':  # end drag
            self._patch.remove()
            del self._patch

            if (abs(event.x - self._event.x) < 3 or
                    abs(event.y - self._event.y) < 3):
                return  # No zoom when points are too close

            x_axes, y_axes = self._axes

            for ax in x_axes:
                pixel_to_data = ax.transData.inverted()
                begin_pt = pixel_to_data.transform_point((event.x, event.y))
                end_pt = pixel_to_data.transform_point(
                    (self._event.x, self._event.y))

                min_ = min(begin_pt[0], end_pt[0])
                max_ = max(begin_pt[0], end_pt[0])
                if not ax.xaxis_inverted():
                    ax.set_xlim(min_, max_)
                else:
                    ax.set_xlim(max_, min_)

            for ax in y_axes:
                pixel_to_data = ax.transData.inverted()
                begin_pt = pixel_to_data.transform_point((event.x, event.y))
                end_pt = pixel_to_data.transform_point(
                    (self._event.x, self._event.y))

                min_ = min(begin_pt[1], end_pt[1])
                max_ = max(begin_pt[1], end_pt[1])
                if not ax.yaxis_inverted():
                    ax.set_ylim(min_, max_)
                else:
                    ax.set_ylim(max_, min_)

            self._event = None

        elif event.name == 'motion_notify_event':  # drag
            if self._event is None:
                return

            if event.inaxes != self._event.inaxes:
                return  # Ignore event outside plot

            self._patch.set_width(event.xdata - self._event.xdata)
            self._patch.set_height(event.ydata - self._event.ydata)

        self._draw()

    def _on_mouse_press(self, event):
        """Mouse press event.

        Args:
            event (event): The event
        """
        if self._pressed_button is not None:
            return  # Discard event if a button is already pressed

        if event.button in (1, 3):  # Start
            x_axes, y_axes = self._axes_to_update(event)
            if x_axes or y_axes:
                self._axes = x_axes, y_axes
                self._pressed_button = event.button

                if self._pressed_button == 1:  # pan
                    self._pan(event)

                    if self.options.report_point_position:  # check if we want to report point
                        self._report_point_position(event)

                elif self._pressed_button == 3:  # zoom area
                    self._zoom_area(event)

    def _on_mouse_release(self, event):
        """Mouse release event.

        Args:
            event (event): The event
        """
        if self._pressed_button == event.button:
            if self._pressed_button == 1:  # pan
                self._pan(event)
            elif self._pressed_button == 3:  # zoom area
                self._zoom_area(event)
            self._pressed_button = None

    def _on_mouse_motion(self, event):
        """Mouse motion event.

        Args:
            event (event): The event
        """
        if self._pressed_button == 1:  # pan
            self._pan(event)
        elif self._pressed_button == 3:  # zoom area
            self._zoom_area(event)

    def _report_point_position(self, event):
        """Report point position.

        Args:
            event (event): the event
        """
        ix, iy = event.xdata, event.ydata

        if hasattr(self, '_ix_iy_old'):
            ix_old, iy_old = self._ix_iy_old
        else:
            ix_old, iy_old = (ix, iy)

        self._ix_iy_old = ix, iy

        _text = f'(x,y) = ({ix:.4f}, {iy:.4f})  Δ last point ({ix-ix_old:.4f}, {iy-iy_old:.4f})'
        if self.logger:
            self.logger.info(_text)
        if self._statusbar_label:
            self._statusbar_label.setText(_text)
        # print(_text)


def figure_pz(*args, **kwargs):
    """matplotlib.pyplot.figure with pan and zoom interaction."""
    #import warnings
    # warnings.filterwarnings(action='ignore')

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fig = _plt.figure(*args, **kwargs)
    fig.pan_zoom = PanAndZoom(fig)

    # warnings.resetwarnings()

    return fig


# """
# if __name__ == "__main__":
#     import matplotlib.pyplot as plt

#     fig = figure_pz()
#     # Alternative:
#     # fig = plt.figure()
#     # pan_zoom = PanAndZoom(fig)

#     nrow, ncol = 2, 3

#     ax1 = fig.add_subplot(nrow, ncol, 1)
#     ax1.set_title('basic')
#     ax1.plot((1, 2, 3))

#     ax2 = fig.add_subplot(nrow, ncol, 2)
#     ax2.set_title('log + twinx')
#     ax2.set_yscale('log')
#     ax2.plot((1, 2, 1))

#     ax2bis = ax2.twinx()
#     ax2bis.plot((3, 2, 1), color='red')

#     ax3 = fig.add_subplot(nrow, ncol, 3)
#     ax3.set_title('inverted y axis')
#     ax3.plot((1, 2, 3))
#     lim = ax3.get_ylim()
#     ax3.set_ylim(lim[1], lim[0])

#     ax4 = fig.add_subplot(nrow, ncol, 4)
#     ax4.set_title('keep ratio')
#     ax4.axis('equal')
#     ax4.imshow(numpy.arange(100).reshape(10, 10))

#     ax5 = fig.add_subplot(nrow, ncol, 5)
#     ax5.set_xlabel('symlog scale + twiny')
#     ax5.set_xscale('symlog')
#     ax5.plot((1, 2, 3))
#     ax5bis = ax5.twiny()
#     ax5bis.plot((3, 2, 1), color='red')

#     # The following is taken from:
#     # http://matplotlib.org/examples/axes_grid/demo_curvelinear_grid.html
#     from mpl_toolkits.axisartist import Subplot
#     from mpl_toolkits.axisartist.grid_helper_curvelinear import \
#         GridHelperCurveLinear

#     def tr(x, y):  # source (data) to target (rectilinear plot) coordinates
#         x, y = numpy.asarray(x), numpy.asarray(y)
#         return x + 0.2 * y, y - x

#     def inv_tr(x, y):
#         x, y = numpy.asarray(x), numpy.asarray(y)
#         return x - 0.2 * y, y + x

#     grid_helper = GridHelperCurveLinear((tr, inv_tr))

#     ax6 = Subplot(fig, nrow, ncol, 6, grid_helper=grid_helper)
#     fig.add_subplot(ax6)
#     ax6.set_title('non-ortho axes')

#     xx, yy = tr([3, 6], [5.0, 10.])
#     ax6.plot(xx, yy)

#     ax6.set_aspect(1.)
#     ax6.set_xlim(0, 10.)
#     ax6.set_ylim(0, 10.)

#     ax6.axis["t"] = ax6.new_floating_axis(0, 3.)
#     ax6.axis["t2"] = ax6.new_floating_axis(1, 7.)
#     ax6.grid(True)

#     plt.show()
# """
