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

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import shapely

from shapely.geometry import Point, LineString, LinearRing, Polygon
from .mpl_interaction import figure_pz
from ..components import is_component

def draw_shapely_poly_mpl(poly:Polygon,
                          ax,
                          kw={},
                          kw_hole={},
                          plot_format=False):
    '''
    Style and draw a shapely polygon using MPL.
    '''
    # This function is somewhat outdated. needs update if to be used more.

    kw = {**dict(lw=1, edgecolors='k', alpha=0.5), **kw}
    kw_hole = {**dict(facecolors='w', lw=1, edgecolors='grey'), **kw}

    if not poly.exterior == LinearRing():  # not empty - better check?
        coords = np.array(poly.exterior.coords)
        poly = mpl.patches.Polygon(coords)
        color = ax._get_lines.get_next_color()
        ax.add_collection(
            mpl.collections.PatchCollection([poly],
                                            **{**{'facecolor': color}, **kw})
        )
        # holes
        polys = []
        for hole in poly.interiors:
            coords = tuple(hole.coords)
            poly = mpl.patches.Polygon(coords)
            polys.append(poly)
        ax.add_collection(
            mpl.collections.PatchCollection(polys, **kw_hole)
        )

    if plot_format:
        ax.set_aspect(1)
        ax.autoscale()




##########################################################################################
# Plotting subroutines

def plot_shapely_style_v1(ax, labels=None):
    '''
    Style function for axis called by `plot_shapely`
    '''
    if ax is None:
        ax = plt.gca()

    # If 'box', change the physical dimensions of the Axes. If 'datalim', change the x or y data limits.
    ax.set_adjustable('datalim')
    ax.set_aspect(1)
    # ax.autoscale()

    # Labels
    if not labels is None:
        fontP = mpl.font_manager.FontProperties()
        fontP.set_size('small')
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), prop=fontP)


def plot_shapely(components,
                 ax=None,
                 kw={},
                 plot_format=True,
                 labels=None,
                 __depth=-1,  # how many sublists in we are
                 _iteration=0,  # how many components we have plotted
                 **kwargs):  # such as kw_hole
    '''
    Plot a list or dicitoanry of shapely components.

    TODO: Update to handle plotting argumetn with *args and **kwargs
    but this needs the .draw functions to be updated
    '''
    __depth = __depth + 1
    #print(__depth, _iteration, components, '\n')

    # Default Parameters
    if ax is None:
        ax = plt.gca()
    if labels is 'auto':
        labels = list(map(str, range(len(components))))
    if not labels is None:
        kw = {**dict(label=labels[_iteration]), **kw}

    # Handle itterables
    if isinstance(components, dict):
        for _, objs in components.items():
            _iteration = plot_shapely(objs, ax=ax, kw=kw, plot_format=plot_format,
                                      labels=labels, __depth=__depth, _iteration=_iteration, **kwargs)
        if plot_format and (__depth == 0):
            plot_shapely_style_v1(ax, labels=labels)
        return _iteration

    elif isinstance(components, list):
        for objs in components:
            _iteration = plot_shapely(objs, ax=ax, kw=kw, plot_format=plot_format,
                                      labels=labels, __depth=__depth, _iteration=_iteration, **kwargs)
        if plot_format and (__depth == 0):
            plot_shapely_style_v1(ax, labels=labels)
        return _iteration

    if not isinstance(components, shapely.geometry.base.BaseGeometry):  # obj is None
        return _iteration+1

    # We have now a single object to draw
    obj = components

    if isinstance(obj, shapely.geometry.Polygon):
        draw_shapely_poly_mpl(obj, kw=kw, ax=ax, **kwargs)

    else:
        if isinstance(obj, shapely.geometry.MultiPoint):
            kw = {**dict(marker='o'), **kw}
            coords = list(map(lambda x: list(x.coords)[0], list(obj)))
        else:
            coords = obj.coords

        if isinstance(obj, shapely.geometry.Point):
            kw = {**dict(marker='o'), **kw}

        ax.plot(*zip(*list(coords)), **kw)

    if plot_format and (__depth == 0):
        plot_shapely_style_v1(ax, labels=labels)

    return _iteration+1


draw_objs = plot_shapely


def draw_all_objects(components, ax, func=lambda x: x, root_name='components'):

    # logger.debug(components.keys())
    for name, obj in components.items():
        if isinstance(obj, dict):
            if name.startswith('components'):
                #logger.debug(f'Drawing: {root_name}.{name}')
                draw_objs(func(obj), ax=ax)  # allow transmofmation of components
            else:
                draw_all_objects(obj, ax, root_name=root_name+'.'+name)

        elif is_component(obj):
            #logger.debug(f' Metal_Object: {obj}')
            draw_objs(obj.components, ax=ax)


#################################################################################
### PLOT FULL

def plot_simple_gui_style(ax):
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


def plot_simple_gui_spawn(fig_kw={}):
    '''
    Run with
    ..code-block python
        %matplotlib qt
        fig_draw, ax_draw = plot_simple_gui_spawn()
    '''
    fig_draw = figure_pz(**{**dict(num=1),
                            **fig_kw})

    ax_draw = fig_draw.add_subplot(1, 1, 1)
    # ax_draw.set_title('Layout')
    # If 'box', change the physical dimensions of the Axes. If 'datalim', change the x or y data limits.
    ax_draw.set_adjustable('datalim')

    ax_draw.set_xlabel('X position (mm)')
    ax_draw.set_ylabel('Y position (mm)')

    def clear_me():
        plt.sca(ax_draw)
        from pyEPR.toolbox_plotting import plt_cla
        plt_cla(ax_draw)

    ax_draw.clear_me = clear_me

    def restyle(display=True):
        plot_simple_gui_style(ax_draw)
        from IPython.display import display
        display(fig_draw)

    ax_draw.restyle_me = restyle

    plot_simple_gui_style(ax_draw)

    fig_draw.tight_layout()

    return fig_draw, ax_draw
