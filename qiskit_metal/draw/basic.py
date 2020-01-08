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
Main module for shapely basic drawing.

@date: 2019
@author: Zlatko Minev (IBM)
"""

from collections.abc import Iterable, Mapping

import numpy as np
import shapely
import shapely.affinity
import shapely.wkt
from shapely.geometry import CAP_STYLE, JOIN_STYLE, Point, Polygon

from .. import config, logger
from ..components.base import is_component
from .utility import get_poly_pts

__all__ = ['rectangle', 'is_rectangle', 'flip_merge', 'rotate', 'rotate_position',
           '_iter_func_geom_', 'translate', 'scale', 'buffer']


def rectangle(w: float, h: float):
    """
    Draw a shapely rectangle of width and height

    Arguments:
        w (float) --  width
        h (float) --  height

    Returns:
        shapely.geometry.Polygon
    """

    w, h = float(w), float(h)
    pad = f"""POLYGON (({-w/2} {-h/2},
                        {+w/2} {-h/2},
                        {+w/2} {+h/2},
                        {-w/2} {+h/2},
                        {-w/2} {-h/2}))"""  # last  point has to close on self

    return Polygon(shapely.wkt.loads(pad))  # My Polygon class


def is_rectangle(obj):
    '''
    Test if a shapely object is a rectangle.

    If there are 4 ext cooridnate then
    check if consequtive vectors are orhtogonal
    Assumes that the last point is not repeating
    '''
    if not isinstance(obj, shapely.geometry.Polygon):
        return False

    p = get_poly_pts(obj)
    if len(p) == 4:
        def isOrthogonal(i):
            v1 = p[(i+1) % 4]-p[(i+0) % 4]
            v2 = p[(i+2) % 4]-p[(i+1) % 4]
            return abs(np.dot(v1, v2)) < 1E-16
        # CHeck if all vectors are consequtivly orthogonal
        return all(map(isOrthogonal, range(4)))
    else:
        return False


#########################################################################
# Shapely affine transorms

def flip_merge(line: shapely.geometry.LineString,
               xfact=-1,
               yfact=+1,
               origin=(0, 0)
               ):
    '''
    Mirror type of drawing command on LineString.

    Returns the coorindates that can be used to construct a polygon, by flipping a linestring
    over an axis and mirroring it.

    Calls shapely.affinity.scale(geom, xfact=xfact, yfact=yfact, zfact=1.0, origin=origin)

    The point of origin can be a keyword 'center' for the 2D bounding
    box center (default), 'centroid' for the geometry's 2D centroid,
    a Point object or a coordinate tuple (x0, y0, z0).
    Negative scale factors will mirror or reflect coordinates.
    '''
    line_flip = shapely.affinity.scale(
        line, xfact=xfact, yfact=yfact, origin=origin)
    coords = list(line.coords) + list(reversed(line_flip.coords))
    return coords


def _iter_func_geom_(func, objs, *args, overwrite=False, **kwargs):
    """Apply function to shapely geometry, and handle. This will create a new dictionary.

    Applied to on:
        For components:
            objs.elements
        For elements:
            elements.geom
            # not for now: elements.geom_rendred.metal
        For dict:
            to each value
        For list:
            to each element

    Arguments:
        func {[function]} -- [description]
        objs {[type]} -- [description]
        overwrite -- overwrite the parent dict or not. This applies to component elements dictionary.
                    Maybe remove in future?
    """

    if isinstance(objs, Mapping):  # dict, Dict
        if overwrite:
            for key, val in objs.items():
                objs[key] = _iter_func_geom_(
                    func, val, *args, overwrite=overwrite, **kwargs)
            return objs
        else:
            return type(objs)([(key, _iter_func_geom_(func, val, *args, overwrite=overwrite, **kwargs))
                               for key, val in objs.items()])

    elif isinstance(objs, Iterable):  # list, tuple
        if overwrite:
            for key, val in enumerate(objs):
                objs[key] = _iter_func_geom_(
                    func, val, *args, overwrite=overwrite, **kwargs)
            return objs
        else:
            return type(objs)([_iter_func_geom_(func, val, *args, overwrite=overwrite, **kwargs) for val in objs])

    elif is_component(objs):
        # apply on geom of component's elements; return component
        # below: returns a dict with the shifted components, we will not use this
        _iter_func_geom_(func, objs.elements, *args,
                         overwrite=overwrite, **kwargs)
        return objs

    elif is_element(objs):
        # apply on geom of element; return element
        func(objs.geom, *args, **kwargs)
        return objs

    elif isinstance(objs, shapely.geometry.base.BaseGeometry):
        return func(objs, *args, **kwargs)

    else:
        logger.error(f'Unkown elemnet! ERROR on: {objs}')
        return objs


"""
#TODO:Remove

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
        # angle = {'X': 0, 'Y': 90}.get(angle, angle)
        obj = shapely.affinity.rotate(obj, angle, origin)
        return obj



def rotate_position(obj, angle: float, pos: list, pos_rot=(0, 0)):
    '''
    Orient and then place position. Just a shortcut function.

    Arguments:
        obj {[type]} -- Object to roient, shapely or metal
        angle {[float]} -- [description]
        pos {[list, np.array]} -- position to translate to

    Keyword Arguments:
        pos_rot {tuple} -- Rotate about this point before translating. (default: {(0, 0)})

    Returns:
        [type] -- Rotate dand translated, same as input
    '''
    def rotate_position_shapely(sobj):
        pos1 = list(orient(Point(pos), angle).coords)[0]  # move to position
        sobj = shapely.affinity.rotate((sobj, angle, pos_rot)  # rotate about pos_rot
        return shapely.affinity.translate(sobj, *pos1)

    if isinstance(obj, list):
        return [rotate_position(o, angle, pos, pos_rot) for o in obj]

    elif is_element(obj):
        # should we do the rendered geometry?
        obj.geom=rotate_position_shapely(obj)
        return obj

    elif isinstance(obj, shapely.geometry.base.BaseGeometry):
        return rotate_position_shapely(obj)

    else:
        logger.error(f'ERROR in rotate_position: Unkown object. {obj}')



def rotate(components, angle, *args, **kwargs):
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
    # Should change to also cover negative rotations and flips?
    angle={'X': 0, 'Y': 90}.get(angle, angle)
    if isinstance(components, list):
        for i, obj in enumerate(components):
            components[i]=rotate(obj, angle, *args, **kwargs)
    elif isinstance(components, dict):
        for name, obj in components.items():
            components[name]=rotate(obj, angle, *args, **kwargs)
    else:
        if not components is None:
            # this is now a single object
            components=shapely.affinity.rotate(
                components, angle, *args, **kwargs)
    return components



def _func_obj_dict(func, components, *args, _override=True, **kwargs):
    '''
    _override:  overrides the dictionary or list.
    '''
    if isinstance(components, list):
        for i, obj in enumerate(components):
            value = _func_obj_dict(
                func, obj, *args, _override=_override, **kwargs)
            if _override:
                components[i] = value

    elif isinstance(components, dict):
        for name, obj in components.items():
            value = _func_obj_dict(
                func, obj, *args, _override=_override, **kwargs)
            if _override:
                components[name] = value

    else:
        if not components is None:
            # this is now a single object
            components = func(components, *args, **kwargs)

    return components
"""


def rotate(elements, angle, origin='center', use_radians=False, overwrite=False):
    r"""
    Calls: shapely.affinity.rotate(
        geom, angle, origin='center', use_radians=False)

    Docstring:
    Returns a rotated geometry on a 2D plane.

    The angle of rotation can be specified in either degrees (default) or
    radians by setting ``use_radians=True``. Positive angles are
    counter-clockwise and negative are clockwise rotations.

    The point of origin can be a keyword 'center' for the bounding box
    center (default), 'centroid' for the geometry's centroid, a Point object
    or a coordinate tuple (x0, y0).

    The affine transformation matrix for 2D rotation is:

    / cos(r) -sin(r) xoff \
    | sin(r)  cos(r) yoff |
    \   0       0      1  /

    where the offsets are calculated from the origin Point(x0, y0):

        xoff = x0 - x0 * cos(r) + y0 * sin(r)
        yoff = y0 - x0 * sin(r) - y0 * cos(r)
    """
    return _iter_func_geom_(shapely.affinity.rotate, elements,
                            angle, origin=origin, use_radians=use_radians, overwrite=overwrite)


def translate(elements, xoff=0.0, yoff=0.0, zoff=0.0, overwrite=False):
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
    return _iter_func_geom_(shapely.affinity.translate, elements,
                            xoff=xoff, yoff=yoff, zoff=zoff, overwrite=overwrite)


def scale(elements, xfact=1.0, yfact=1.0, zfact=1.0, origin='center', overwrite=False):
    r'''
    Operatos on a list or Dict of components.

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
    return _iter_func_geom_(shapely.affinity.scale, elements,
                            xfact=xfact, yfact=yfact, zfact=zfact, origin=origin, overwrite=overwrite)


def rotate_position(elements, angle: float, pos: list, pos_rot=(0, 0), overwrite=False):
    '''
    Orient and then place position. Just a shortcut function.

    Arguments:
        obj {[type]} -- Object to roient, shapely or metal
        angle {[float]} -- [description]
        pos {[list, np.array]} -- position to translate to

    Keyword Arguments:
        pos_rot {tuple} -- Rotate about this point before translating. (default: {(0, 0)})

    Returns:
        [type] -- Rotate dand translated, same as input
    '''

    def rotate_position_shapely(sobj):
        pos1 = list(shapely.affinity.rotate(Point(pos), angle).coords)[0]
        sobj = shapely.affinity.rotate(
            sobj, angle, pos_rot)  # rotate about pos_rot
        return shapely.affinity.translate(sobj, *pos1)  # move to position

    return _iter_func_geom_(rotate_position_shapely, elements, overwrite=overwrite)


def buffer(elements,
           distance: float,
           resolution=None,
           cap_style=CAP_STYLE.flat,
           join_style=JOIN_STYLE.mitre,
           mitre_limit=None,
           overwrite=False):
    '''
    Flat buffer of all components in the dictionary

    Default stlye:
        cap_style=CAP_STYLE.flat
        join_style=JOIN_STYLE.mitre


    Signature:
    line.buffer(
        distance,
        resolution=None, # will use config.DEFAULT.buffer_resolution  16
        quadsegs=None,
        cap_style=1,
        join_style=1,
        mitre_limit=None, # will use config.DEFAULT.buffer_mitre_limit 5.0
    )

    Docstring:
    Returns a geometry with an envelope at a distance from the object's
    envelope

    A negative distance has a "shrink" effect. A zero distance may be used
    to "tidy" a polygon. The resolution of the buffer around each vertex of
    the object increases by increasing the resolution keyword parameter
    or second positional parameter. resolution = how many points

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
        x = rectangle(1,1)
        y = buffer_flat([x,x,[x,x,{'a':x}]], 0.5)
        render_to_mpl([x,y])
    '''
    if mitre_limit is None:
        mitre_limit = config.DEFAULT.buffer_mitre_limit
        # TODO: mayube thius should be in the rendere for metal?
        # or maybe render can set config? - yes

    if resolution is None:
        resolution = config.DEFAULT.buffer_resolution

    def buffer_me(obj, *args, **kwargs):
        return obj.buffer(*args, **kwargs)

    return _iter_func_geom_(buffer_me, elements, distance,
                            resolution=resolution,
                            cap_style=cap_style,
                            join_style=join_style,
                            mitre_limit=mitre_limit,
                            overwrite=overwrite)
