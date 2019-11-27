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
# pylint: disable=ungrouped-imports
# TODO: clenaup and remove this file

from collections.abc import Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import shapely
import shapely.wkt
from numpy import array
from numpy.linalg import norm
from shapely.affinity import rotate, scale, translate
from shapely.geometry import (CAP_STYLE, JOIN_STYLE, LinearRing, MultiPolygon,
                              Point)
from shapely.geometry import Polygon

from .. import logger
from ..toolbox_mpl.mpl_interaction import figure_pz
from ..toolbox_metal.parsing import TRUE_STR, parse_units

#########################################################################
# Shapely Geometry Basic Coordinates

def get_poly_pts(poly:Polygon):
    """
    Return the coordinates of a Shapely polygon with the last repeating point removed

    Arguments:
        poly {[shapely.Polygon]} -- Shapely polygin

    Returns:
        [np.array] -- Sequence of coorindates.
    """
    return np.array(poly.exterior.coords)[:-1]



def get_all_objects(components, func=lambda x: x, root_name='components'):
    from .components.base_objects.Metal_Utility import is_component

    def new_name(name): return root_name + '.' + \
        name if not (root_name == '') else name

    if is_component(components):
        return {components.name: get_all_objects(components.components,
                                              root_name=new_name(components.name))}

    elif isinstance(components, shapely.geometry.base.BaseGeometry):
        return obj

    elif isinstance(components, dict):
        RES = {}
        for name, obj in components.items():
            if is_component(obj):
                RES[name] = get_all_objects(
                    obj.components, root_name=new_name(name))
            elif isinstance(obj, dict):
                # if name.startswith('components'): # old school to remove eventually TODO
                #    RES[name] = func(obj) # allow transofmraiton of components
                # else:
                RES[name] = get_all_objects(obj, root_name=new_name(name))
            elif isinstance(obj, shapely.geometry.base.BaseGeometry):
                RES[name] = func(obj)
        return RES

    else:
        logger.debug(
            f'warning: {root_name} was not an object or dict or the right handle')
        return None


def flatten_all_objects(components, filter_obj=None):
    assert isinstance(components, dict)

    RES = []

# OLD CODE? REMOVE?
    #from .components.Metal_Object import is_component
    # if is_component(components):
    #    RES += flatten_all_objects(components.components, filter_obj)
    # else:
    for name, obj in components.items():
        if isinstance(obj, dict):
            RES += flatten_all_objects(obj, filter_obj)
        # elif is_component(obj):
        #    RES += flatten_all_objects(obj.components, filter_obj)
        else:
            if filter_obj is None:
                RES += [obj]
            else:
                if isinstance(obj, filter_obj):
                    RES += [obj]
                else:
                    print(name)

    return RES


def get_all_object_bounds(components):
    # Assumes they are all polygonal
    components = get_all_objects(components)
    objs = flatten_all_objects(components, filter_obj=shapely.geometry.Polygon)
    print(objs)
    (x_min, y_min, x_max, y_max) = MultiPolygon(objs).bounds
    return (x_min, y_min, x_max, y_max)


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


def rotate_obj_dict(components, angle, *args, **kwargs):
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
    angle = {'X': 0, 'Y': 90}.get(angle, angle)
    if isinstance(components, list):
        for i, obj in enumerate(components):
            components[i] = rotate_obj_dict(obj, angle, *args, **kwargs)
    elif isinstance(components, dict):
        for name, obj in components.items():
            components[name] = rotate_obj_dict(obj, angle, *args, **kwargs)
    else:
        if not components is None:
            # this is now a single object
            components = rotate(components, angle, *args, **kwargs)
    return components


rotate_objs = rotate_obj_dict


def _func_obj_dict(func, components, *args, _override=True, **kwargs):
    '''
    _override:  overrides the dictionary.
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


def translate_objs(components, *args, **kwargs):
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
    return _func_obj_dict(translate, components, *args, **kwargs)


def scale_objs(components, *args, **kwargs):
    '''
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
    return _func_obj_dict(scale, components, *args, **kwargs)


def buffer(components,  *args, **kwargs):
    '''
    Flat buffer of all components in the dictionary
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
    return _func_obj_dict(buffer_me, components, *args, **kwargs)


#########################################################################
# POINT LIST FUNCTIONS

def check_duplicate_list(your_list):
    return len(your_list) != len(set(your_list))


def unit_vector(vector):
    """ Return a vector where is XY components now make a unit vector

    Normalizes only in the XY plane, leaves the Z plane alone
    """
    vector = array_chop(vector)  # get rid of near zero crap
    if len(vector) == 2:
        _norm = norm(vector)
        if not bool(_norm):  # zero length vector
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
    '''
    Used for darwing in HFSS only.
    For the given design, get the z values in HFSS UNITS!

    Manually specify z dimension.
    '''
    if isinstance(vec2D[0], Iterable):
        return array([to_Vec3Dz(vec, z=z) for vec in vec2D])
    else:
        return array(list(vec2D)+[z])


def to_Vec3D(design, options, vec2D):
    '''
    Used for darwing in HFSS only.
    For the given design, get the z values in HFSS UNITS!

    get z dimension from the design chip params
    '''
    if isinstance(vec2D[0], Iterable):
        return array([to_Vec3D(design, options, vec) for vec in vec2D])
    else:
        # if not isinstance(options,dict):
        #    options={'chip':options}
        z = parse_value_hfss(design.get_chip_z(
            options.get('chip', draw.functions.DEFAULT['chip'])))
        return array(list(vec2D)+[z])


def array_chop(vec, zero=0, rtol=0, machine_tol=100):
    '''
    Zlatko chop array entires clsoe to zero
    '''
    vec = np.array(vec)
    mask = np.isclose(vec, zero, rtol=rtol,
                      atol=machine_tol*np.finfo(float).eps)
    vec[mask] = 0
    return vec


def same_vectors(v1, v2, tol=100):
    '''
    Check if two vectors are within an infentesmimal distance set
    by `tol` and machine epsilon
    '''
    v1, v2 = list(map(np.array, [v1, v2]))         # enforce numpy array
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
