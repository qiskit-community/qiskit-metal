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
"""Plotting functions for shapely components using mpl."""

import matplotlib as mpl
import matplotlib.cbook as cbook
import matplotlib.image as image
import matplotlib.pyplot as plt
import numpy as np
import shapely
from cycler import cycler
from matplotlib.cbook import _OrderedSet
from shapely.geometry import LinearRing, Polygon  # Point, LineString,

from qiskit_metal import Dict
from qiskit_metal.draw import BaseGeometry
from qiskit_metal.renderers.renderer_mpl.mpl_interaction import figure_pz
from qiskit_metal.renderers.renderer_mpl.patch import PolygonPatch

__all__ = [
    '_render_poly_zkm', 'render_poly', 'render', 'style_axis_simple',
    'get_prop_cycle', 'style_axis_standard', 'figure_spawn',
    '_axis_set_watermark_img', 'clear_axis'
]

##########################################################################################
# Plotting subroutines

# Todo Move - default config
style_config = Dict(
    poly=dict(lw=1, ec='k', alpha=0.5)  # fc='#6699cc',
    # Dict(
    #exterior = dict(lw=1, edgecolors='k', alpha=0.5),
    # interior = dict(facecolors='w', lw=1, edgecolors='grey'))
)
"""Style configuration"""


def _render_poly_zkm(poly: Polygon, ax, kw=None, kw_hole=None):
    """Style and draw a shapely polygon using MPL.

    Args:
        poly (Polygon): The polygon.
        ax (plt.Axes): Matplotlib axis to render to.
        kw (dict): Dictionary of kwargs for the plotting.  Defaults to None.
        kw_hold (kw_hole): kw_hole.  Defaults to None.
    """
    if kw_hole is None:
        kw_hole = {}
    if kw is None:
        kw = {}

    # should probably  only create these once and pass these in here
    kw = {**style_config.poly.exterior, **kw}
    kw_hole = {**style_config.poly.interior, **kw}

    if not poly.exterior == LinearRing():  # not empty - better check?
        # pylint: disable=protected-access
        # Exterior
        coords = np.array(poly.exterior.coords)
        mpl_poly = mpl.patches.Polygon(coords)
        color = ax._get_lines.get_next_color()
        ax.add_collection(
            mpl.collections.PatchCollection([mpl_poly], **{
                **{
                    'facecolor': color
                },
                **kw
            }))

        # Interior (i.e., holes)
        polys = []
        for hole in poly.interiors:
            coords = tuple(hole.coords)
            poly = mpl.patches.Polygon(coords)
            polys.append(poly)
        ax.add_collection(mpl.collections.PatchCollection(polys, **kw_hole))


def render_poly(poly: shapely.geometry.Polygon, ax: plt.Axes, kw=None):
    """Render an individual shapely shapely.geometry.Polygon.

    Args:
        poly (shapely.geometry.Polygon): Poly or multipoly to render.
        ax (plt.Axes): Matplotlib axis to render to.
        kw (dict): Dictionary of kwargs for the plotting.  Defaults to None.

    Returns:
        patch: ax.add_patch result
    """
    # TODO: maybe if done in batch we can speed this up?
    kw = kw or {}
    return ax.add_patch(PolygonPatch(poly, **{**style_config.poly, **kw}))


def render(
    components,
    ax=None,
    kw=None,
    # plot_format=True,
    labels=None,
    __depth=-1,  # how many sublists in we are
    _iteration=0):  # how many components we have plotted
    """Main plotting function. Plots onto an axis.

    Args:
        components: A list, dict, tuple, itterable, or shapely object.
        ax (plt.Axes): Matplotlib axis to render to.  Defaults to None.
        kw (dict): Dictionary of kwargs for the plotting.  Defaults to None.
        labels (str): Labels.  Defaults to None.
        __depth (int): How many sublists in we are.  Defaults to -1.
        _interation (int): How many components we have plotted.  Defaults to 0.

    Return:
        int: Interation
    """
    # TODO: Update to handle plotting argument with *args and **kwargs
    # but this needs the .draw functions to be updated

    __depth = __depth + 1
    #print(__depth, _iteration, components, '\n')

    kw = kw or {}
    ax = ax or plt.gca()

    if labels is 'auto':
        labels = list(map(str, range(len(components))))

    if not labels is None:
        kw = {**dict(label=labels[_iteration]), **kw}

    # Handle itterables
    if isinstance(components, dict):
        for _, objs in components.items():
            _iteration = render(objs,
                                ax=ax,
                                kw=kw,
                                labels=labels,
                                __depth=__depth,
                                _iteration=_iteration)
            # plot_format=plot_format, , **kwargs)
        # if plot_format and (__depth == 0):
        #    style_axis_simple(ax, labels=labels)
        return _iteration

    if isinstance(components, list):
        for objs in components:
            _iteration = render(objs,
                                ax=ax,
                                kw=kw,
                                labels=labels,
                                __depth=__depth,
                                _iteration=_iteration)
            # plot_format=plot_format,, **kwargs)
        # if plot_format and (__depth == 0):
        #    style_axis_simple(ax, labels=labels)
        return _iteration

    if not isinstance(components, BaseGeometry):  # obj is None
        return _iteration + 1

    # We have now a single object to draw
    obj = components

    if isinstance(obj,
                  (shapely.geometry.MultiPolygon, shapely.geometry.Polygon)):
        render_poly(obj, ax=ax, kw=kw)  # , **kwargs)

    else:
        if isinstance(obj, shapely.geometry.MultiPoint):
            kw = {**dict(marker='o'), **kw}
            coords = list(map(lambda x: list(x.coords)[0], list(obj)))
        else:
            coords = obj.coords

        if isinstance(obj, shapely.geometry.Point):
            kw = {**dict(marker='o'), **kw}

        ax.plot(*zip(*list(coords)), **kw)

    # if plot_format and (__depth == 0):
    #    style_axis_simple(ax, labels=labels)

    return _iteration + 1


# '''
# def draw_all_objects(components, ax, func=lambda x: x, root_name='components'):
#     """
#     #  TODO: This is very outdated, remove

#     Args:
#         components {[type]} -- [description]
#         ax {[type]} -- [description]
#         func {[type]} -- [description] Defaults to {lambdax:x}
#         root_name {str} -- [description] Defaults to {'components'}
#     """

#     # logger.debug(components.keys())
#     for name, obj in components.items():
#         if isinstance(obj, dict):
#             if name.startswith('components'):
#                 #logger.debug(f'Drawing: {root_name}.{name}')
#                 # allow transformation of components
#                 render(func(obj), ax=ax)
#             else:
#                 draw_all_objects(obj, ax, root_name=root_name+'.'+name)

#         elif is_component(obj):
#             #logger.debug(f' Metal_Object: {obj}')
#             render(obj.components, ax=ax)
# '''

##########################################################################################
# Style subroutines


def style_axis_simple(ax, labels=None):
    """Style function for axis called by `render`.

    Args:
        ax (plt.Axes): Matplotlib axis to render to.  Defaults to None.
        labels (str): Label
    """
    if ax is None:
        ax = plt.gca()

    # If 'box', change the physical dimensions of the Axes.
    # If 'datalim', change the x or y data limits.
    ax.set_adjustable('datalim')
    ax.set_aspect(1)
    # ax.autoscale() # for gui

    # Labels
    if not labels is None:
        font_p = mpl.font_manager.FontProperties()
        font_p.set_size('small')
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), prop=font_p)


rcParams = plt.matplotlib.rcParams


def get_prop_cycle():
    """Get the prop cycle."""
    prop_cycler = rcParams['axes.prop_cycle']
    if prop_cycler is None and 'axes.color_cycle' in rcParams:
        clist = rcParams['axes.color_cycle']
        prop_cycler = cycler('color', clist)
    return prop_cycler


#################################################################################
# Top level plotting calls - PLOT FULL


def style_axis_standard(ax):
    """Style the axis standardly.

    Args:
        ax (plt.Axes): Matplotlib axis to render to.  Defaults to None.
    """
    #fig = ax.figure

    # Core lines
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

    # Reset color cycle
    # ax.set_prop_cycle(None)
    ax.set_prop_cycle(color=['#91aecf', '#a3bbd6', '#6e94be', '#a3bbd6'])

    # fig.canvas.draw()
    # fig.canvas.flush_events()


def figure_spawn(fig_kw=None):
    """Spawn a simple, interactive matplotlib figure and gui with styled axis.
    Use mouse wheel and click and drag to navigate.

    Results in a plot that spawned up as a window! Make sure
    to enable non-inline matplotlib.

    ..code-block python

        %matplotlib qt
        fig_draw, ax_draw = figure_spawn()

    Args:
        fig_kw (fig_kw): fig_kw.  Defaults to None.

    Returns:
        (fig_draw, ax_draw)
    """
    if not fig_kw:
        fig_kw = {}
    fig_draw = figure_pz(**{**dict(num=1), **fig_kw})
    fig_draw.clf()

    ax_draw = fig_draw.add_subplot(1, 1, 1)
    # ax_draw.set_title('Layout')
    # If 'box', change the physical dimensions of the Axes. If 'datalim',
    # change the x or y data limits.
    ax_draw.set_adjustable('datalim')
    ax_draw.set_aspect(1)

    ax_draw.set_xlabel('X position (mm)')
    ax_draw.set_ylabel('Y position (mm)')

    # pylint: disable=import-outside-toplevel
    def clear_me():
        plt.sca(ax_draw)
        #from pyEPR.toolbox_plotting import plt_cla
        # plt_cla(ax_draw)

    ax_draw.clear_me = clear_me

    def restyle(display=True):
        style_axis_standard(ax_draw)
        from IPython.display import display
        display(fig_draw)

    ax_draw.restyle_me = restyle

    style_axis_standard(ax_draw)

    fig_draw.tight_layout()

    return fig_draw, ax_draw


#######################################################################


def _axis_set_watermark_img(ax: plt.Axes, file: str, size: float = 0.25):
    """Burn the axis watermark into the image.

    Args:
        ax (plt.Axes): Matplotlib axis to render to.  Defaults to None.
        file (str): The file.
        size (float): The size.  Defaults to None.
    """
    # Load image
    datafile = cbook.get_sample_data(str(file), asfileobj=False)
    img = image.imread(datafile)
    # im[:, :, -1] = 0.5  # set the alpha channel

    # window aspect
    # pylint: disable=invalid-name
    b = ax.get_window_extent()
    b = abs(b.height / b.width)
    # b = ax.get_tightbbox(ax.get_figure().canvas.get_renderer())
    # b = abs(b.height/b.width)

    # ALternative: fig.figimage
    # scale image: yscale = float(img.shape[1])/img.shape[0]
    # extent: (left, right, bottom, top)
    kw = dict(interpolation='gaussian', alpha=0.05, resample=True, zorder=-200)
    ax.imshow(img,
              extent=(1 - size * b, 1, 1 - size, 1),
              transform=ax.transAxes,
              **kw)


#######################################################################


def clear_axis(ax: plt.Axes):
    """Clear all plotted objects on an axis including lines, patches, tests, tables,
    artists, images, mouseovers, child axes, legends, collections, and containers.
    See: https://matplotlib.org/devdocs/api/_as_gen/matplotlib.axes.Axes.clear.html

    Args:
        ax (plt.Axes): MPL axis to clear
    """
    ax.clear()
    # pylint: disable=protected-access
