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
"""Main module for shapely manipulation and drawing.

**Manipulation:**
    The module defines rotate, scale, translate to operate on a various set of
    input arguments, such as shapelies or itterable/mappables or shapelies.

**Creation:**
    The module defines the creation of some basic shapely objects for convinence,
    such as a rectangle.
"""

from collections.abc import Iterable, Mapping

import numpy as np
import shapely
import shapely.affinity
import shapely.wkt
from shapely.geometry import CAP_STYLE, JOIN_STYLE, Point, Polygon

from .. import config, logger
from .. import is_component
from ..config import DefaultMetalOptions
from . import BaseGeometry
from .utility import get_poly_pts

__all__ = [
    'rectangle', 'is_rectangle', 'flip_merge', 'rotate', 'rotate_position',
    '_iter_func_geom_', 'translate', 'scale', 'buffer', 'union', 'subtract'
]


def rectangle(w: float, h: float, xoff: float = 0, yoff: float = 0):
    """Draw a shapely rectangle of width and height.

    Args:
        w (float) :  width
        h (float) :  height
        xoff (float, optional) : Gives the x position of the center.  Defaults to 0.
        yoff (float, optional) : Gives the y position of the center.  Defaults to 0.

    Returns:
        shapely.geometry.Polygon: Shapely rectangle
    """

    w, h = float(w), float(h)
    pad = f"""POLYGON (({-w/2} {-h/2},
                        {+w/2} {-h/2},
                        {+w/2} {+h/2},
                        {-w/2} {+h/2},
                        {-w/2} {-h/2}))"""  # last  point has to close on self

    if xoff is 0 and yoff is 0:
        return Polygon(shapely.wkt.loads(pad))  # My Polygon class
    else:
        return shapely.affinity.translate(Polygon(shapely.wkt.loads(pad)),
                                          xoff=xoff,
                                          yoff=yoff)


def is_rectangle(obj):
    """Test if a shapely object is a rectangle.

    If there are 4 ext cooridnate then
    check if consequtive vectors are orhtogonal.
    Assumes that the last point is not repeating.

    Args:
        obj (object): Object to test

    Returns:
        bool: True is object is a rectangle, false otherwise
    """
    if not isinstance(obj, shapely.geometry.Polygon):
        return False

    p = get_poly_pts(obj)
    if len(p) == 4:

        def is_orthogonal(i):
            v1 = p[(i + 1) % 4] - p[(i + 0) % 4]
            v2 = p[(i + 2) % 4] - p[(i + 1) % 4]
            return abs(np.dot(v1, v2)) < 1E-16

        # CHeck if all vectors are consequtivly orthogonal
        return all(map(is_orthogonal, range(4)))
    else:
        return False


def subtract(poly_main: shapely.geometry.Polygon,
             poly_tool: shapely.geometry.Polygon):
    """Geometry subtract tool poly from main poly.

    Args:
        poly_main (Polygon): Main polygon from which we will carve out
        poly_tool (Polygon or list): Poly or list of polys to subtract

    Returns:
        Polygon: Difference between the given Polygons
    """
    return poly_main.difference(poly_tool)


def union(*polys):
    """Geometry union of two or more polys.

    Areas of overlapping Polygons will get merged. LineStrings will get
    fully dissolved and noded. Duplicate Points will get merged.

    Args:
        polys (Polygon, or list of polygons, or args of polygons).
            Main polygon from which we will carve out.

    Returns:
        Polygon: Union of the input polygons
    """
    # union() is an expensive way to find the cumulative union of
    # many objects.
    # See shapely.ops.unary_union() for a more effective method.
    if len(polys) is 2:
        return polys[0].union(polys[1])
    elif len(polys) is 1:  # assume that it is a list
        polys = polys[0]
    return shapely.ops.unary_union(polys)


#########################################################################
# Shapely affine transorms


def flip_merge(line: shapely.geometry.LineString,
               xfact=-1,
               yfact=+1,
               origin=(0, 0)):
    """Mirror type of drawing command on LineString.

    Calls shapely.affinity.scale(geom, xfact=xfact, yfact=yfact, zfact=1.0, origin=origin).

    The point of origin can be a keyword 'center' for the 2D bounding
    box center (default), 'centroid' for the geometry's 2D centroid,
    a Point object or a coordinate tuple (x0, y0, z0).
    Negative scale factors will mirror or reflect coordinates.

    Args:
        line (shapely.geometry.LineString): Geometry
        xfact (double): x-scale factor.  Defaults to -1.
        yfact (double): y-scale factor.  Defaults to 1.
        orign (tuple): Coordinates of the origin

    Returns:
        list: The coorindates that can be used to construct a polygon, by flipping a linestring
        over an axis and mirroring it.
    """
    line_flip = shapely.affinity.scale(line,
                                       xfact=xfact,
                                       yfact=yfact,
                                       origin=origin)
    coords = list(line.coords) + list(reversed(line_flip.coords))
    return coords


def _iter_func_geom_(func, objs, *args, overwrite=False, **kwargs):
    """Apply function to shapely geometry, and handle. This will create a new
    dictionary.

    Applied to on:
        For components:
            objs.qgeometry
        For qgeometry:
            qgeometry.geom
            # not for now: qgeometry.geom_rendred.metal
        For dict:
            to each value
        For list:
            to each element

    Args:
        func (function): Function the apply
        objs (Dict, List, Tuple or BaseGeometry): Set of objects
        overwrite (bool): Overwrite the parent dict or not. This applies to component qgeometry dictionary.
            Maybe remove in future?  Defaults to False.
        kwargs (dict): Parameters dictionary

    Returns:
        list: List of objects
    """

    if isinstance(objs, Mapping):  # dict, Dict
        if overwrite:
            for key, val in objs.items():
                objs[key] = _iter_func_geom_(func,
                                             val,
                                             *args,
                                             overwrite=overwrite,
                                             **kwargs)
            return objs
        else:
            return type(objs)([(key,
                                _iter_func_geom_(func,
                                                 val,
                                                 *args,
                                                 overwrite=overwrite,
                                                 **kwargs))
                               for key, val in objs.items()])

    elif isinstance(objs, Iterable):  # list, tuple
        if overwrite:
            for key, val in enumerate(objs):
                objs[key] = _iter_func_geom_(func,
                                             val,
                                             *args,
                                             overwrite=overwrite,
                                             **kwargs)
            return objs
        else:
            return type(objs)([
                _iter_func_geom_(func,
                                 val,
                                 *args,
                                 overwrite=overwrite,
                                 **kwargs) for val in objs
            ])

    elif is_component(objs):
        # apply on geom of component's qgeometry; return component
        # below: returns a dict with the shifted components, we will not use this
        _iter_func_geom_(func,
                         objs.qgeometry,
                         *args,
                         overwrite=overwrite,
                         **kwargs)
        return objs

    # elif is_element(objs): #will need updating to new table format
    #    # apply on geom of element; return element
    #    func(objs.geom, *args, **kwargs)
    #    return objs

    elif isinstance(objs, BaseGeometry):
        return func(objs, *args, **kwargs)

    else:
        logger.error(f'Unkown elemnet! ERROR on: {objs}')
        return objs


def rotate(qgeometry,
           angle,
           origin='center',
           use_radians=False,
           overwrite=False):
    r"""
    The angle of rotation can be specified in either degrees (default) or
    radians by setting ``use_radians=True``. Positive angles are
    counter-clockwise and negative are clockwise rotations.

    The point of origin can be a keyword 'center' for the bounding box
    center (default), 'centroid' for the geometry's centroid, a Point object
    or a coordinate tuple (x0, y0).

    Calls: shapely.affinity.rotate(
        geom, angle, origin='center', use_radians=False)

    Args:
        qgeometry (Dict, List, Tuple or BaseGeometry): Set of objects
        angle (double): Rotation angle
        origin (tuple or str): Origin point. Defaults to 'center'.
        use_radians (bool): True to use radians.  Defaults to False.
        overwrite (bool): True to overwrite.  Defaults to False.

    Returns:
        geometry: A rotated geometry on a 2D plane.

    The affine transformation matrix for 2D rotation is:
    ::

        / cos(r) -sin(r) xoff \
        | sin(r)  cos(r) yoff |
        \   0       0      1  /

    where the offsets are calculated from the origin Point(x0, y0):
    ::

        xoff = x0 - x0 * cos(r) + y0 * sin(r)
        yoff = y0 - x0 * sin(r) - y0 * cos(r)
    """
    return _iter_func_geom_(shapely.affinity.rotate,
                            qgeometry,
                            angle,
                            origin=origin,
                            use_radians=use_radians,
                            overwrite=overwrite)


def translate(qgeometry, xoff=0.0, yoff=0.0, zoff=0.0, overwrite=False):
    r'''Shifts the geometry by the given offset.
    Args:
        qgeometry (Dict, List, Tuple or BaseGeometry): Set of objects.
        xoff (double): x-direction offset.  Defaults to 0.0.
        yoff (double): y-direction offset.  Defaults to 0.0.
        zoff (double): z-direction offset.  Defaults to 0.0.
        overwrite (bool): True to overwrite.  Defaults to False.

    Returns:
        geometry: A translated geometry shifted by offsets along each dimension.

    The general 3D affine transformation matrix for translation is:
    ::

        / 1  0  0 xoff \
        | 0  1  0 yoff |
        | 0  0  1 zoff |
        \ 0  0  0   1  /
    '''
    return _iter_func_geom_(shapely.affinity.translate,
                            qgeometry,
                            xoff=xoff,
                            yoff=yoff,
                            zoff=zoff,
                            overwrite=overwrite)


def scale(qgeometry,
          xfact=1.0,
          yfact=1.0,
          zfact=1.0,
          origin='center',
          overwrite=False):
    r'''
    Operatos on a list or Dict of components.

    Args:
        qgeometry (Dict, List, Tuple or BaseGeometry): Set of objects
        xfact: x-direction scale factor.  Defaults to 1.0.
        yfact: y-direction scale factor.  Defaults to 1.0.
        zfact: z-direction scale factor.  Defaults to 1.0.
        origin (tuple or str): Origin point.  Defaults to 'center'.
        overwrite (bool): True to overwrite.  Defaults to False.

    Returns:
        geometry: A scaled geometry, scaled by factors along each dimension.

    The point of origin can be a keyword 'center' for the 2D bounding box
    center (default), 'centroid' for the geometry's 2D centroid, a Point
    object or a coordinate tuple (x0, y0, z0).

    Negative scale factors will mirror or reflect coordinates.

    The general 3D affine transformation matrix for scaling is:
    ::

        / xfact  0    0   xoff \
        |   0  yfact  0   yoff |
        |   0    0  zfact zoff |
        \   0    0    0     1  /

    where the offsets are calculated from the origin Point(x0, y0, z0):
    ::

        xoff = x0 - x0 * xfact
        yoff = y0 - y0 * yfact
        zoff = z0 - z0 * zfact
    '''
    return _iter_func_geom_(shapely.affinity.scale,
                            qgeometry,
                            xfact=xfact,
                            yfact=yfact,
                            zfact=zfact,
                            origin=origin,
                            overwrite=overwrite)


def rotate_position(qgeometry,
                    angle: float,
                    pos: list,
                    pos_rot=(0, 0),
                    overwrite=False):
    """Orient and then place position. Just a shortcut function.

    Args:
        qgeometry (Dict, List, Tuple or BaseGeometry): Set of objects
        angle (float): Rotation angle
        pos (list, np.array): Position to translate to
        pos_rot (tuple): Rotate about this point before translating.  Default to {(0, 0)}).

    Returns:
        geometry: Rotate dand translated, same as input
    """

    def rotate_position_shapely(sobj):
        pos1 = list(shapely.affinity.rotate(Point(pos), angle).coords)[0]
        sobj = shapely.affinity.rotate(sobj, angle,
                                       pos_rot)  # rotate about pos_rot
        return shapely.affinity.translate(sobj, *pos1)  # move to position

    return _iter_func_geom_(rotate_position_shapely,
                            qgeometry,
                            overwrite=overwrite)


def buffer(qgeometry,
           distance: float,
           resolution=None,
           cap_style=CAP_STYLE.flat,
           join_style=JOIN_STYLE.mitre,
           mitre_limit=None,
           overwrite=False):
    """Flat buffer of all components in the dictionary.

    Default stlye:
        - cap_style=CAP_STYLE.flat
        - join_style=JOIN_STYLE.mitre

    Args:
        qgeometry (Dict, List, Tuple or BaseGeometry): Set of objects.
        distance (float): Distance.
        resolution (int): How many points.  Defaults to None.
        cap_style (shapely.geometry.CAP_STYLE): Cap style.  Defaults to CAP_STYLE.falt.
        join_style (shapely.geometry.JOIN_STYLE): Join style.  Defaults to JOIN_STYLE.mitre.
        mitre_limit (double): Mitre limit.  Defaults to None.
        overwrite (bool): True to overwrite.  Defaults to None.

    Returns:
        geometry: A geometry with an envelope at a distance from the object's envelope

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
    ::

        x = rectangle(1,1)
        y = buffer_flat([x,x,[x,x,{'a':x}]], 0.5)
        draw.mpl.render([x,y])
        units = config.DefaultMetalOptions.default_generic.units
    """
    if mitre_limit is None:
        mitre_limit = DefaultMetalOptions.default_generic.geometry.buffer_mitre_limit
        # TODO: maybe this should be in the renderer for metal?
        # or maybe render can set config? - yes
        # TODO: should really be design.template_options.units

    if resolution is None:
        resolution = DefaultMetalOptions.default_generic.geometry.buffer_resolution

    def buffer_me(obj, *args, **kwargs):
        return obj.buffer(*args, **kwargs)

    return _iter_func_geom_(buffer_me,
                            qgeometry,
                            distance,
                            resolution=resolution,
                            cap_style=cap_style,
                            join_style=join_style,
                            mitre_limit=mitre_limit,
                            overwrite=overwrite)
