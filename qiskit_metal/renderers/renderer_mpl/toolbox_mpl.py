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
Plotting functions for shapely components using mpl.

Created 2019
@author: Zlatko Minev (IBM)
"""


import descartes  # shapely plot
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import shapely
from matplotlib.cbook import _OrderedSet
from shapely.geometry import LinearRing, Polygon  # Point, LineString,

from ... import Dict
from ...components import is_component
from .interaction_mpl import figure_pz
from ...draw import BaseGeometry

##########################################################################################
# Plotting subroutines

# Todo Move - default config
style_config = Dict(
    poly=dict(fc='#6699cc', lw=1, ec='k', alpha=0.5)
    # Dict(
    #exterior = dict(lw=1, edgecolors='k', alpha=0.5),
    # interior = dict(facecolors='w', lw=1, edgecolors='grey'))

)


def _render_poly_zkm(poly: Polygon,
                     ax,
                     kw=None,
                     kw_hole=None):
    '''
    Style and draw a shapely polygon using MPL.
    '''
    if kw_hole is None:
        kw_hole = {}
    if kw is None:
        kw = {}

    # should probably  only creat thes once and pass these in here
    kw = {**style_config.poly.exterior, **kw}
    kw_hole = {**style_config.poly.interior, **kw}

    if not poly.exterior == LinearRing():  # not empty - better check?

        # Exteriror
        coords = np.array(poly.exterior.coords)
        mpl_poly = mpl.patches.Polygon(coords)
        color = ax._get_lines.get_next_color()
        ax.add_collection(
            mpl.collections.PatchCollection([mpl_poly],
                                            **{**{'facecolor': color}, **kw})
        )

        # Interior (i.e., holes)
        polys = []
        for hole in poly.interiors:
            coords = tuple(hole.coords)
            poly = mpl.patches.Polygon(coords)
            polys.append(poly)
        ax.add_collection(
            mpl.collections.PatchCollection(polys, **kw_hole)
        )


def render_poly(poly: shapely.geometry.Polygon, ax: plt.Axes, kw=None):
    """
    Render an individual shapely shapely.geometry.Polygon

    Args:
        poly (shapely.geometry.Polygon): Poly or multipoly to render
        ax (plt.Axes):  Matplotlib axis to render to
        kw (dict, optional): Dictionary of kwargs for the plotting.
                    Defaults to None.

    Returns:
        ax.add_patch result
    """
    # TODO: maybe if done in batch we can speed this up?
    kw = kw or {}
    return ax.add_patch(
        descartes.PolygonPatch(poly, **{**style_config.poly, **kw})
    )


def render(components,
           ax=None,
           kw=None,
           #plot_format=True,
           labels=None,
           __depth=-1,     # how many sublists in we are
           _iteration=0):  # how many components we have plotted
           # **kwargs):  # such as kw_hole
    '''
    Main plotting function.
    Plots onto an axis.

    Args:
         components : a list, dict, tuple, itterable, or shapely object

    '''
    # TODO: Update to handle plotting argumetn with *args and **kwargs
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
            _iteration = render(objs, ax=ax, kw=kw,
                                labels=labels, __depth=__depth,
                                _iteration=_iteration)
                                # plot_format=plot_format, , **kwargs)
        #if plot_format and (__depth == 0):
        #    style_axis_simple(ax, labels=labels)
        return _iteration

    elif isinstance(components, list):
        for objs in components:
            _iteration = render(objs, ax=ax, kw=kw,
                                labels=labels, __depth=__depth,
                                _iteration=_iteration)
                                # plot_format=plot_format,, **kwargs)
        #if plot_format and (__depth == 0):
        #    style_axis_simple(ax, labels=labels)
        return _iteration

    if not isinstance(components, BaseGeometry):  # obj is None
        return _iteration+1

    # We have now a single object to draw
    obj = components

    if isinstance(obj, shapely.geometry.Polygon) or isinstance(obj, shapely.geometry.MultiPolygon):
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

    #if plot_format and (__depth == 0):
    #    style_axis_simple(ax, labels=labels)

    return _iteration+1


'''
def draw_all_objects(components, ax, func=lambda x: x, root_name='components'):
    """
    #  TODO: This is very outdated, remove


    Arguments:
        components {[type]} -- [description]
        ax {[type]} -- [description]

    Keyword Arguments:
        func {[type]} -- [description] (default: {lambdax:x})
        root_name {str} -- [description] (default: {'components'})
    """

    # logger.debug(components.keys())
    for name, obj in components.items():
        if isinstance(obj, dict):
            if name.startswith('components'):
                #logger.debug(f'Drawing: {root_name}.{name}')
                # allow transmofmation of components
                render(func(obj), ax=ax)
            else:
                draw_all_objects(obj, ax, root_name=root_name+'.'+name)

        elif is_component(obj):
            #logger.debug(f' Metal_Object: {obj}')
            render(obj.components, ax=ax)
'''

##########################################################################################
# Style subroutines


def style_axis_simple(ax, labels=None):
    '''
    Style function for axis called by `render`
    '''
    if ax is None:
        ax = plt.gca()

    # If 'box', change the physical dimensions of the Axes.
    # If 'datalim', change the x or y data limits.
    ax.set_adjustable('datalim')
    ax.set_aspect(1)
    # ax.autoscale() # for gui

    # Labels
    if not labels is None:
        fontP = mpl.font_manager.FontProperties()
        fontP.set_size('small')
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), prop=fontP)

from cycler import cycler
rcParams = plt.matplotlib.rcParams
def get_prop_cycle():
    prop_cycler = rcParams['axes.prop_cycle']
    if prop_cycler is None and 'axes.color_cycle' in rcParams:
        clist = rcParams['axes.color_cycle']
        prop_cycler = cycler('color', clist)
    return prop_cycler

#################################################################################
# Top level plotting calls - PLOT FULL

def style_axis_standard(ax):
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
    '''
    Spawn a simple, interactive matplotlib figure and gui
    with styled axis.  Use mouse wheel and click and drag
    to navigate.

    Results in a plot that spwaned up as a window! Make sure
    to enable non-inline matplotlib.

    ..code-block python

        %matplotlib qt
        fig_draw, ax_draw = figure_spawn()

    Returns:
        (fig_draw, ax_draw)
    '''
    if not fig_kw:
        fig_kw = {}
    fig_draw = figure_pz(**{**dict(num=1),
                            **fig_kw})
    fig_draw.clf()

    ax_draw = fig_draw.add_subplot(1, 1, 1)
    # ax_draw.set_title('Layout')
    # If 'box', change the physical dimensions of the Axes. If 'datalim',
    # change the x or y data limits.
    ax_draw.set_adjustable('datalim')
    ax_draw.set_aspect(1)

    ax_draw.set_xlabel('X position (mm)')
    ax_draw.set_ylabel('Y position (mm)')

    def clear_me():
        plt.sca(ax_draw)
        from pyEPR.toolbox_plotting import plt_cla
        plt_cla(ax_draw)

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
"""
def clear_axis(ax: plt.Axes):
    '''
    Clear all plotted objects on an axis

    Args:
        ax : mapltlib axis
    '''
    ax = ax if not ax is None else plt.gca()
    for artist in ax.lines + ax.collections + ax.patches + ax.images + ax.texts:
        artist.remove()
    if ax.legend_:
        ax.legend_.remove()
"""

def clear_axis(ax: plt.Axes):
    """Clear all plotted objects on an axis
    including lines, patches, tests, tables,
    artists, images, mouseovers, child axes, legends,
    collections, and containers

    Args:
        ax (plt.Axes): Mpl axis to clear
    """
    #ax.clear()
    ax.lines = []
    ax.patches = []
    ax.texts = []
    ax.tables = []
    ax.artists = []
    ax.images = []
    ax._mouseover_set = _OrderedSet()
    ax.child_axes = []
    ax._current_image = None  # strictly for pyplot via _sci, _gci
    ax.legend_ = None
    ax.collections = []  # collection.Collection instances
    ax.containers = []

    #for axis in [ax.xaxis, ax.yaxis]:
    #    # Clear the callback registry for this axis, or it may "leak"
    #    pass #self.callbacks = cbook.CallbackRegistry()
