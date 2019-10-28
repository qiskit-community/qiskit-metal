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
Created 2019

Draw utility functions

@author: Zlatko Minev
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt


from numpy import sqrt, pi, array
from numpy.linalg import norm
from collections import namedtuple
from collections.abc import Iterable
from pyEPR.hfss import parse_units, unparse_units, parse_units_user
from pyEPR.toolbox import combinekw

import shapely
import shapely.wkt
from shapely.geometry import CAP_STYLE, JOIN_STYLE
from shapely.geometry import Point, LineString, LinearRing,\
    Polygon as Polygon_shapely, MultiPolygon
from shapely.affinity import rotate, scale, translate

from . import draw_functions
from . import logger, Dict
from .toolbox.mpl_interaction import figure_pz
from .toolbox.utility_functions import dict_start_with, copy_update, get_traceback

#########################################################################
# Constants
TRUE_STR = ['true', 'True', 'TRUE', '1', 't', 'y', 'Y', 'YES',
            'yes', 'yeah', 'yup', 'certainly', 'uh-huh', True, 1]


#########################################################################
# Geomtry classes

class Polygon(Polygon_shapely):

    """def __init__(self, *args, rectangle=False, **kwargs):
        '''
        rectangle : Am I a rectangle or not, this can be made automatic later
        This will not work because when i transofrm them they get dropped
        The class is kept the same, but it is reconstructed only with the exisitng properties.
        '''
        super(Polygon, self).__init__(*args, **kwargs)

        self.rectangle = rectangle
    """

    @property
    def coords_ext(self):
        'Return the coordinates with the last repeating point removed'
        coords = np.array(self.exterior.coords)
        return coords[:-1]

    def draw(self,
             ax=None,
             kw={},
             kw_hole={},
             plot_format=False):
        '''
        Style and draw
        '''
        kw = {**dict(lw=1, edgecolors='k', alpha=0.5), **kw}
        kw_hole = {**dict(facecolors='w', lw=1, edgecolors='grey'), **kw}

        if ax is None:
            ax = plt.gca()

        if not self.exterior == LinearRing():  # not empty
            coords = np.array(self.exterior.coords)
            poly = mpl.patches.Polygon(coords)
            color = ax._get_lines.get_next_color()
            ax.add_collection(
                mpl.collections.PatchCollection([poly],
                                                **combinekw({'facecolor': color}, kw))
            )
            # holes
            polys = []
            for hole in self.interiors:
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


def plot_shapely(objects,
                 ax=None,
                 kw={},
                 plot_format=True,
                 labels=None,
                 __depth=-1,  # how many sublists in we are
                 _iteration=0,  # how many objects we have plotted
                 **kwargs):  # such as kw_hole
    '''
    Plot a list or dicitoanry of shapely objects.

    TODO: Update to handle plotting argumetn with *args and **kwargs
    but this needs the .draw functions to be updated
    '''
    __depth = __depth + 1
    #print(__depth, _iteration, objects, '\n')

    # Default Parameters
    if ax is None:
        ax = plt.gca()
    if labels is 'auto':
        labels = list(map(str, range(len(objects))))
    if not labels is None:
        kw = {**dict(label=labels[_iteration]), **kw}

    # Handle itterables
    if isinstance(objects, dict):
        for _, objs in objects.items():
            _iteration = plot_shapely(objs, ax=ax, kw=kw, plot_format=plot_format,
                                      labels=labels, __depth=__depth, _iteration=_iteration, **kwargs)
        if plot_format and (__depth == 0):
            plot_shapely_style_v1(ax, labels=labels)
        return _iteration

    elif isinstance(objects, list):
        for objs in objects:
            _iteration = plot_shapely(objs, ax=ax, kw=kw, plot_format=plot_format,
                                      labels=labels, __depth=__depth, _iteration=_iteration, **kwargs)
        if plot_format and (__depth == 0):
            plot_shapely_style_v1(ax, labels=labels)
        return _iteration

    if not isinstance(objects, shapely.geometry.base.BaseGeometry): # obj is None
        return _iteration+1


    # We have now a single object to draw
    obj = objects

    if isinstance(obj, shapely.geometry.Polygon):
        Polygon.draw(obj, kw=kw, ax=ax, **kwargs)

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

def draw_all_objects(OBJECTS, ax, func=lambda x:x, root_name='OBJECTS'):
    from .objects.base_objects.Metal_Utility import is_metal_object

    #logger.debug(OBJECTS.keys())
    for name, obj in OBJECTS.items():
        if isinstance(obj, dict):
            if name.startswith('objects'):
                #logger.debug(f'Drawing: {root_name}.{name}')
                draw_objs(func(obj), ax=ax) # allow transmofmation of objects
            else:
                draw_all_objects(obj, ax, root_name=root_name+'.'+name)

        elif is_metal_object(obj):
            #logger.debug(f' Metal_Object: {obj}')
            draw_objs(obj.objects, ax=ax)

def get_all_objects(objects, func=lambda x:x, root_name='OBJECTS'):
    from .objects.base_objects.Metal_Utility import is_metal_object

    new_name = lambda name: root_name + '.' + name if not (root_name == '') else name

    if is_metal_object(objects):
        return {objects.name: get_all_objects(objects.objects,
                                              root_name=new_name(objects.name))}

    elif isinstance(objects, shapely.geometry.base.BaseGeometry):
        return obj

    elif isinstance(objects, dict):
        RES = {}
        for name, obj in objects.items():
            if is_metal_object(obj):
                RES[name] = get_all_objects(obj.objects, root_name=new_name(name))
            elif isinstance(obj, dict):
                #if name.startswith('objects'): # old school to remove eventually TODO
                #    RES[name] = func(obj) # allow transofmraiton of objects
                #else:
                RES[name] = get_all_objects(obj, root_name=new_name(name))
            elif isinstance(obj, shapely.geometry.base.BaseGeometry):
                RES[name] = func(obj)
        return RES

    else:
        logger.debug(f'warning: {root_name} was not an object or dict or the right handle')
        return None

def flatten_all_objects(objects, filter_obj=None):
    assert  isinstance(objects, dict)

    RES = []

#OLD CODE? REMOVE?
    #from .objects.Metal_Object import is_metal_object
    #if is_metal_object(OBJECTS):
    #    RES += flatten_all_objects(OBJECTS.objects, filter_obj)
    #else:
    for name, obj in objects.items():
        if isinstance(obj, dict):
            RES += flatten_all_objects(obj, filter_obj)
        #elif is_metal_object(obj):
        #    RES += flatten_all_objects(obj.objects, filter_obj)
        else:
            if filter_obj is None:
                RES += [obj]
            else:
                if isinstance(obj, filter_obj):
                    RES += [obj]
                else:
                    print(name)

    return RES

def get_all_object_bounds(OBJECTS):
    # Assumes they are all polygonal
    objects = get_all_objects(OBJECTS)
    objs = flatten_all_objects(objects, filter_obj=shapely.geometry.Polygon)
    print(objs)
    (x_min, y_min, x_max, y_max) = MultiPolygon(objs).bounds
    return (x_min, y_min, x_max, y_max)


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
    #ax.set_prop_cycle(None)
    ax.set_prop_cycle(color=['#91aecf', '#a3bbd6', '#6e94be', '#a3bbd6'])

    #fig.canvas.draw()
    #fig.canvas.flush_events()


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
    #ax_draw.set_title('Layout')
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

#########################################################################
# Shapely draw


def shapely_rectangle(w, h):
    w, h = float(w), float(h)
    pad = f"""POLYGON (({-w/2} {-h/2},
                        {+w/2} {-h/2},
                        {+w/2} {+h/2},
                        {-w/2} {+h/2},
                        {-w/2} {-h/2}))"""  # last  point has to close on self
    return Polygon(shapely.wkt.loads(pad))  # My Polygon class


#########################################################################
# Shapely affine transorms

def flip_merge(line, flip=dict(xfact=-1, origin=(0, 0))):
    ''' scale(geom, xfact=1.0, yfact=1.0, zfact=1.0, origin='center')

        The point of origin can be a keyword 'center' for the 2D bounding
        box center (default), 'centroid' for the geometry's 2D centroid,
        a Point object or a coordinate tuple (x0, y0, z0).
        Negative scale factors will mirror or reflect coordinates.
    '''
    line_flip = scale(line, **flip)
    coords = list(line.coords) + list(reversed(line_flip.coords))
    return coords


def orient(obj, angle, origin='center'):
    '''
    Returns a rotated geometry on a 2D plane.

    The angle of rotation can be specified in either degrees (default)
    or radians by setting use_radians=True. Positive angles are
    counter-clockwise and negative are clockwise rotations.

    The point of origin can be a keyword 'center' for the
    bounding box center (default), 'centroid' for the geometry's
    centroid, a Point object or a coordinate tuple (x0, y0).

    angle : 'X' or 'Y' or degrees
        'X' does nothing
        'Y' is a 90 degree clockwise rotated object
    '''
    if isinstance(obj, list):
        return [orient(o, angle, origin) for o in obj]
    else:
        angle = {'X': 0, 'Y': 90}.get(angle, angle)
        obj = rotate(obj, angle, origin)
        return obj


def orient_position(obj, angle, pos, pos_rot=(0, 0)):

    if isinstance(obj, list):
        return [orient_position(o, angle, pos, pos_rot) for o in obj]
    else:
        obj = orient(obj, angle, pos_rot)
        pos1 = list(orient(Point(pos), angle).coords)[0]
        return translate(obj, *pos1)


def rotate_obj_dict(objects, angle, *args, **kwargs):
    '''
    Returns a rotated geometry on a 2D plane.

    The angle of rotation can be specified in either degrees (default)
    or radians by setting use_radians=True. Positive angles are
    counter-clockwise and negative are clockwise rotations.

    The point of origin can be a keyword 'center' for the
    bounding box center (default), 'centroid' for the geometry's
    centroid, a Point object or a coordinate tuple (x0, y0).

    angle : 'X' or 'Y' or degrees
        'X' does nothing
        'Y' is a 90 degree clockwise rotated object
    '''
    #Should change to also cover negative rotations and flips?
    angle = {'X': 0, 'Y': 90}.get(angle, angle)
    if isinstance(objects, list):
        for i, obj in enumerate(objects):
            objects[i] = rotate_obj_dict(obj, angle, *args, **kwargs)
    elif isinstance(objects, dict):
        for name, obj in objects.items():
            objects[name] = rotate_obj_dict(obj, angle, *args, **kwargs)
    else:
        if not objects is None:
            # this is now a single object
            objects = rotate(objects, angle, *args, **kwargs)
    return objects


rotate_objs = rotate_obj_dict


def _func_obj_dict(func, objects, *args, _override = True, **kwargs):
    '''
    _override:  overrides the dictionary.
    '''
    if isinstance(objects, list):
        for i, obj in enumerate(objects):
            value = _func_obj_dict(func, obj, *args, _override=_override, **kwargs)
            if _override:
                objects[i] = value

    elif isinstance(objects, dict):
        for name, obj in objects.items():
            value = _func_obj_dict(func, obj, *args, _override=_override, **kwargs)
            if _override:
                objects[name] = value
    else:
        if not objects is None:
            # this is now a single object
            objects = func(objects, *args, **kwargs)
    return objects


def translate_objs(objects, *args, **kwargs):
    r'''
    translate(geom, xoff=0.0, yoff=0.0, zoff=0.0)
    Docstring:
    Returns a translated geometry shifted by offsets along each dimension.

    The general 3D affine transformation matrix for translation is:

        / 1  0  0 xoff \
        | 0  1  0 yoff |
        | 0  0  1 zoff |
        \ 0  0  0   1  /
    '''
    return _func_obj_dict(translate, objects, *args, **kwargs)


def scale_objs(objects, *args, **kwargs):
    '''
    Operatos on a list or Dict of objects.

    Signature: scale(geom, xfact=1.0, yfact=1.0, zfact=1.0, origin='center')

    Returns a scaled geometry, scaled by factors along each dimension.

    The point of origin can be a keyword 'center' for the 2D bounding box
    center (default), 'centroid' for the geometry's 2D centroid, a Point
    object or a coordinate tuple (x0, y0, z0).

    Negative scale factors will mirror or reflect coordinates.

    The general 3D affine transformation matrix for scaling is:

        / xfact  0    0   xoff \
        |   0  yfact  0   yoff |
        |   0    0  zfact zoff |
        \   0    0    0     1  /

    where the offsets are calculated from the origin Point(x0, y0, z0):

        xoff = x0 - x0 * xfact
        yoff = y0 - y0 * yfact
        zoff = z0 - z0 * zfact
    '''
    return _func_obj_dict(scale, objects, *args, **kwargs)



def buffer(objects,  *args, **kwargs):
    '''
    Flat buffer of all objects in the dictionary
    Default stlye:
        cap_style=CAP_STYLE.flat
        join_style=JOIN_STYLE.mitre

    Signature:
    x.buffer(
        ['distance', 'resolution=16', 'quadsegs=None', 'cap_style=1', 'join_style=1', 'mitre_limit=5.0'],
    )
    Docstring:
    Returns a geometry with an envelope at a distance from the object's
    envelope

    A negative distance has a "shrink" effect. A zero distance may be used
    to "tidy" a polygon. The resolution of the buffer around each vertex of
    the object increases by increasing the resolution keyword parameter
    or second positional parameter. Note: the use of a `quadsegs` parameter
    is deprecated and will be gone from the next major release.

    The styles of caps are: CAP_STYLE.round (1), CAP_STYLE.flat (2), and
    CAP_STYLE.square (3).

    The styles of joins between offset segments are: JOIN_STYLE.round (1),
    JOIN_STYLE.mitre (2), and JOIN_STYLE.bevel (3).

    The mitre limit ratio is used for very sharp corners. The mitre ratio
    is the ratio of the distance from the corner to the end of the mitred
    offset corner. When two line segments meet at a sharp angle, a miter
    join will extend the original geometry. To prevent unreasonable
    geometry, the mitre limit allows controlling the maximum length of the
    join corner. Corners with a ratio which exceed the limit will be
    beveled.

    Example use:
    --------------------
        x = shapely_rectangle(1,1)
        y = buffer_flat([x,x,[x,x,{'a':x}]], 0.5)
        draw_objs([x,y])
    '''
    kwargs = {**dict(cap_style=CAP_STYLE.flat, join_style=JOIN_STYLE.mitre),
              **kwargs}

    def buffer_me(obj, *args, **kwargs):
        return obj.buffer(*args, **kwargs)
    return _func_obj_dict(buffer_me, objects, *args, **kwargs)

#########################################################################
# UNIT and Conversion related


def parse_options_user(variableList, opts, names):
    '''
    To user units.
    Parse a list of variable names (or a string of comma delimited ones
    to list of user parsed ones.
    '''
    if isinstance(names, str):
        names = names.split(',')
    res = []
    for name in names:
        name = name.strip()
        if not name in opts:
            logger.warning(f'Missing key {name} from options {opts}.\n')

        if isinstance(opts[name],str):
            if not(opts[name][0].isdigit() or opts[name][0]=='-'): 
                if not opts[name] in variableList:
                    logger.warning(f'Missing variable {opts[name]} from variable list.\n')
                
                res += [parse_units_user(variableList[opts[name]]) ]
            else:
                res += [parse_units_user(opts[name]) ]
        else:
            res += [parse_units_user(opts[name]) ]

    return res
    #return [parse_units_user(opts[name.strip()]) for name in names]


def parse_options_hfss(opts, names):
    '''
    To HFSS units.

    Parse a list of variable names (or a string of comma delimited ones
    to list of HFSS parsed ones.
    '''
    if isinstance(names, str):
        names = names.split(',')
    return [parse_units(opts[name.strip()]) for name in names]


#########################################################################
# POINT LIST FUNCTIONS

def check_duplicate_list(your_list):
    return len(your_list) != len(set(your_list))

import traceback
def unit_vector(vector):
    """ Return a vector where is XY components now make a unit vector

    Normalizes only in the XY plane, leaves the Z plane alone
    """
    vector = array_chop(vector) # get rid of near zero crap
    if len(vector) == 2:
        _norm = norm(vector)
        if not bool(_norm): # zero length vector
            logger.debug(f'Warning: zero vector length')
            return vector
        return vector / _norm
    elif len(vector) == 3:
        v2 = unit_vector(vector[:2])
        return np.append(v2, vector[2])
    else:
        raise Exception('You did not give a 2 or 3 vec')


def get_unit_vec(two_points):
    assert len(two_points) == 2
    two_points = np.array(two_points)
    two_points = two_points[1] - two_points[0]               # distance vector
    return two_points / norm(two_points)


def vec_angle(v1, v2):
    """
    Returns the angle in radians between vectors 'v1' and 'v2'::
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


def get_vec_unit_norm(points,
                      normal_z=np.array([0, 0, 1])):
    '''
        Get the unit and the normal vector

        .. codeblock python
            vec_D, vec_d, vec_n = get_vec_unit_norm(points)
    '''
    assert len(points) == 2
    points = list(map(np.array, points))         # enforce numpy array
    vec_D = points[1] - points[0]               # distance vector
    vec_d = vec_D / norm(vec_D)                 # unit dist. vector
    vec_n = np.cross(normal_z, vec_d)           # normal unit vector
    vec_n = vec_n[:len(vec_d)]
    return vec_D, vec_d, vec_n


def to_Vec3Dz(vec2D, z=0):
    if isinstance(vec2D[0], Iterable):
        return array([to_Vec3Dz(vec, z=z) for vec in vec2D])
    else:
        return array(list(vec2D)+[z])


def to_Vec3D(design, options, vec2D):
    '''
        For the given designut, get the z
    '''
    if isinstance(vec2D[0], Iterable):
        return array([to_Vec3D(design, options, vec) for vec in vec2D])
    else:
        # if not isinstance(options,dict):
        #    options={'chip':options}
        z = parse_units(design.get_substrate_z(
            options.get('chip', draw_functions.DEFAULT['chip'])))
        return array(list(vec2D)+[z])

def array_chop(vec, zero=0, rtol=0, machine_tol=100):
    '''
    Zlatko chop array entires clsoe to zero
    '''
    vec = np.array(vec)
    mask = np.isclose(vec, zero, rtol=rtol,atol=machine_tol*np.finfo(float).eps)
    vec[mask] = 0
    return vec

def same_vectors(v1, v2, tol=100):
    '''
    Check if two vectors are within an infentesmimal distance set
    by `tol` and machine epsilon
    '''
    v1,v2 = list(map(np.array, [v1,v2]))         # enforce numpy array
    return float(norm(v1-v2)) < tol*np.finfo(float).eps

def remove_co_linear_points(points):
    '''
    remove colinear points and identical consequtive points
    '''
    remove_idx = []
    for i in range(2, len(points)):
        v1 = array(points[i-2])-array(points[i-1])
        v2 = array(points[i-1])-array(points[i-0])
        if same_vectors(v1, v2):
            remove_idx += [i-1]
        elif vec_angle(v1, v2) == 0:
            remove_idx += [i-1]
    points = np.delete(points, remove_idx, axis=0)

    # remove  consequtive duplicates
    remove_idx = []
    for i in range(1, len(points)):
        if norm(points[i]-points[i-1]) == 0:
            remove_idx += [i]
    points = np.delete(points, remove_idx, axis=0)

    return points


def is_rectangle(obj):
    '''
    Test if we have a rectnalge.
    If there are 4 ext cooridnate then
    check if consequtive vectors are orhtogonal
    Assumes that the last point is not repeating
    '''
    assert isinstance(obj, shapely.geometry.Polygon)
    p = Polygon(obj).coords_ext
    if len(p) == 4:
        def isOrthogonal(i):
            v1 = p[(i+1)%4]-p[(i+0)%4]
            v2 = p[(i+2)%4]-p[(i+1)%4]
            return abs(np.dot(v1,v2)) < 1E-16
        return all(map(isOrthogonal, range(4))) # CHeck if all vectors are consequtivly orthogonal
    else:
        return False
