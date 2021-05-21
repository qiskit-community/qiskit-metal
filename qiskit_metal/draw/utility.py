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

# WILL NEED UPDATING TO NEW ELEMENT SCHEME
"""Main module for basic geometric manipulation of non-shapely objects, but
objects such as points and arrays used in drawing."""

import math
from collections.abc import Iterable, Mapping
from typing import List, Tuple, Union

import numpy as np
import shapely
import shapely.wkt
from numpy import array
from numpy.linalg import norm
from shapely.geometry import MultiPolygon, Polygon

from .. import logger
from .. import is_component
from . import BaseGeometry

__all__ = [
    'get_poly_pts', 'get_all_component_bounds', 'get_all_geoms',
    'flatten_all_filter', 'remove_colinear_pts', 'array_chop',
    'vec_unit_planar', 'Vector'
]

#########################################################################
# Shapely Geometry Basic Coordinates


def get_poly_pts(poly: Polygon):
    """Return the coordinates of a Shapely polygon with the last repeating
    point removed.

    Args:
        poly (shapely.Polygon): Shapely polygin

    Returns:
        np.array: Sequence of coorindates.
    """
    return np.array(poly.exterior.coords)[:-1]


def get_all_geoms(obj, func=lambda x: x, root_name='components'):
    """Get a dict of dict of all shapely objects, from components, dict, etc.

    Used to compute the bounding box.

    Args:
        obj (dict, list, element, component): Object to get from.
        func (function): Function to use if mapping. Defaults to (lambda x: x).
        root_name (str): Name to prepend in the flattening. Defaults to 'components'.

    Returns:
        dict: Dictonary of geometries
    """

    # Prelim
    # Calculate the new name
    def new_name(name):        return root_name + '.' + \
name if not (root_name == '') else name

    # Check what we have

    if is_component(obj):
        # Is it a metal component? Then traverse its components
        return obj.get_all_geom()  # dict of shapely geoms

    # elif is_element(obj):
    #    # is it a metal element?
    #    return {obj.name: obj.geom}  # shapely geom

    elif isinstance(obj, BaseGeometry):
        # Is it the shapely object? This is the bottom of the search tree, then return
        return obj

    elif isinstance(obj, Mapping):
        return {
            get_all_geoms(sub_obj, root_name=new_name(name))
            for name, sub_obj in obj.items()
        }
        '''
        RES = {}
        for name, sub_obj in obj.items():
            if is_component(obj):
                RES[name] = get_all_geoms(
                    sub_obj.components, root_name=new_name(name))
            elif isinstance(sub_obj, dict):
                # if name.startswith('components'): # old school to remove eventually TODO
                #    RES[name] = func(obj) # allow transofmraiton of components
                # else:
                RES[name] = get_all_geoms(sub_obj, root_name=new_name(name))
            elif isinstance(sub_obj, BaseGeometry):
                RES[name] = func(obj)
        return RES
        '''

    else:
        logger.debug(
            f'warning: {root_name} was not an object or dict or the right handle'
        )
        return None


def flatten_all_filter(components: dict, filter_obj=None):
    """Internal function to flatten a dict of shapely objects.

    Args:
        components (dict): Dictionary of components
        filter_obj (class): Filter based on this class.  Defaults to None.

    Returns:
        array: Flattened dictionary
    """
    assert isinstance(components, dict)

    RES = []
    for name, obj in components.items():
        if isinstance(obj, dict):
            RES += flatten_all_filter(obj, filter_obj)
        else:
            if filter_obj is None:
                RES += [obj]  # add whatever we have in here
            else:
                if isinstance(obj, filter_obj):
                    RES += [obj]
                else:
                    print('flatten_all_filter: ', name)

    return RES


def get_all_component_bounds(components: dict, filter_obj=Polygon):
    """Pass in a dict of components to calcualte the total bounding box.

    Args:
        components (dict): Dictionary of components
        filter_obj (Polygon): Only use instances of this object to
                              calcualte the bounds

    Returns:
        tuple: (x_min, y_min, x_max, y_max)
    """
    assert isinstance(components, dict)

    components = get_all_geoms(components)
    components = flatten_all_filter(components, filter_obj=filter_obj)

    (x_min, y_min, x_max, y_max) = MultiPolygon(components).bounds

    return (x_min, y_min, x_max, y_max)


def round_coordinate_sequence(geom_ref, precision):
    """Rounds the vertices of a coordinate sequence (both interior and
    exterior).

    Args:
        geometry (shapely.geometry) : A shapely geometry, should not be a MultiPoly
        precison (int) : The decimal precision to round to (eg. 3 -> 0.001)
    Returns:
        shapely.geometry : A shapely geometry with rounded coordinates
    """
    if isinstance(geom_ref, shapely.geometry.linestring.LineString):
        temp_line = np.around(geom_ref.coords[:], precision).tolist()
        geom_ref.coords = temp_line.copy()
    else:
        temp_ext = np.around(geom_ref.exterior.coords[:], precision).tolist()
        geom_ref.exterior.coords = temp_ext.copy()
        for x in range(0, len(geom_ref.interiors)):
            temp_int = np.around(geom_ref.interiors[x].coords[:],
                                 precision).tolist()
            geom_ref.interiors[x].coords = temp_int.copy()

    return geom_ref


#########################################################################
# POINT LIST FUNCTIONS


def check_duplicate_list(your_list):
    """Check if the list contains duplicates.

    Args:
        your_list (list): List to check

    Returns:
        bool: True if there are duplicates, False otherwise
    """
    return len(your_list) != len(set(your_list))


def array_chop(vec, zero=0, rtol=0, machine_tol=100):
    """Chop array entries close to zero.

    Args:
        vec (array): Array to chop
        zero (double): Value to check against.  Defaults to 0.
        rtol (double): Relative tolerance.  Defaults to 0.
        machine_tol (double): Machine tolerance.  Defaults to 100.

    Returns:
        array: Chopped arary
    """
    vec = np.array(vec)
    mask = np.isclose(vec,
                      zero,
                      rtol=rtol,
                      atol=machine_tol * np.finfo(float).eps)
    vec[mask] = 0
    return vec


def remove_colinear_pts(points):
    """Remove colinear points and identical consequtive points.

    Args:
        points (array): Array of points

    Returns:
        ndarray: A copy of the input array without colinear points
    """
    remove_idx = []
    for i in range(2, len(points)):
        v1 = array(points[i - 2]) - array(points[i - 1])
        v2 = array(points[i - 1]) - array(points[i - 0])
        if Vector.are_same(v1, v2):
            remove_idx += [i - 1]
        elif Vector.angle_between(v1, v2) == 0:
            remove_idx += [i - 1]
    points = np.delete(points, remove_idx, axis=0)

    # remove  consequtive duplicates
    remove_idx = []
    for i in range(1, len(points)):
        if norm(points[i] - points[i - 1]) == 0:
            remove_idx += [i]
    points = np.delete(points, remove_idx, axis=0)

    return points


#########################################################################
# Points, Lines and Areas functions
def intersect(p1x, p1y, p2x, p2y, x0, y0):
    """Intersect segment defined by p1 and p2 with ray coming out of x0,y0 ray
    can be horizontal y=y0  x=x0+dx , want dx>0.

    Args:
        p1x (float): x coordinate of point 1 of segment
        p1y (float): y coordinate of point 1 of segment
        p2x (float): x coordinate of point 2 of segment
        p2y (float): y coordinate of point 2 of segment
        x0 (float): x coordinate anchoring the intersection ray
        y0 (float): y coordinate anchoring the intersection ray

    Returns:
        boolean int: (1) if intersecting, (0) if not intersecting
    """
    if p1x != p2x and p1y != p2y:
        m = (p2y - p1y) / (p2x - p1x)
        x_inter = (y0 - p1y) / m + p1x
        if x_inter >= x0 and np.min([p1y, p2y]) <= y0 <= np.max([p1y, p2y]):
            ans = 1
        else:
            ans = 0
    else:
        if p1x == p2x:  # vertical segment
            if x0 <= p1x and np.min([p1y, p2y]) <= y0 <= np.max([p1y, p2y]):
                ans = 1
            else:
                ans = 0
        if p1y == p2y:  # horizontal segment
            if y0 == p1y:
                ans = 1
            else:
                ans = 0
    return ans


def in_or_out(xs, ys, x0, y0):
    """Count up how many times a ray intersects the polygon, even or odd tells
    you whether inside (odd) or outside (even)"""
    crossings = 0
    for i in range(len(xs) - 1):
        p1x = xs[i]
        p2x = xs[i + 1]
        p1y = ys[i]
        p2y = ys[i + 1]
        cross = intersect(p1x, p1y, p2x, p2y, x0, y0)
        # print('i = ', i, 'cross = ', cross)
        crossings += cross
    return crossings


#########################################################################
# Vector functions


def vec_unit_planar(vector: np.array):
    """Make the planar 2D (x,y) part of a vector to be unit mag. Return a
    vector where is XY components now a unit vector. I.e., Normalizes only in
    the XY plane, leaves the Z plane alone.

    Args:
        vector (np.array): Input 2D or 3D

    Returns:
        np.array: Same dimension 2D or 3D

    Raises:
        Exception: The input was not a 2 or 3 vector
    """
    vector = array_chop(vector)  # get rid of near zero crap

    if len(vector) == 2:
        _norm = norm(vector)

        if not bool(_norm):  # zero length vector
            logger.debug(f'Warning: zero vector length')
            return vector

        return vector / _norm

    elif len(vector) == 3:
        v2 = vec_unit_planar(vector[:2])
        return np.append(v2, vector[2])

    else:
        raise Exception('You did not give a 2 or 3 vec')


def to_vec3D(list_of_2d_pts: List[Tuple], z=0) -> np.ndarray:
    """Adds 3rd point to list of 2D points. For the given design, get the z
    values in HFSS UNITS! Manually specify z dimension.

    Args:
        list_of_2d_pts (List[Tuple]): List of 2D points
        z (int, optional): z-value in hfss. Defaults to 0.

    Returns:
        np.ndarray: vec3d of points
    """
    add_me = [z]
    return np.array([list(a_2d_pt) + add_me for a_2d_pt in list_of_2d_pts])


Vec2D = Union[list, np.ndarray]


class Vector:
    """Utility functions to call on 2D vectors, which can be np.ndarrays or
    lists."""

    normal_z = np.array([0, 0, 1])
    """ Noraml Z array """

    @staticmethod
    def rotate_around_point(xy: Vec2D, radians: float,
                            origin=(0, 0)) -> np.ndarray:
        r"""Rotate a point around a given point.
        Positive angles are counter-clockwise and negative are clockwise rotations.

        .. math::

            \begin{split}
            x_\mathrm{off} &= x_0 - x_0 \cos{\theta} + y_0 \sin{\theta} \\
            y_\mathrm{off} &= y_0 - x_0 \sin{\theta} - y_0 \cos{\theta}
            \end{split}

        Args:
            xy (Vec2D): A 2D vector.
            radians (float): Counter clockwise angle.
            origin (tuple): point to rotate about.  Defaults to (0, 0).

        Returns:
            np.ndarray: rotated point
        """
        # see: https://gist.github.com/LyleScott/d17e9d314fbe6fc29767d8c5c029c362
        x, y = xy
        offset_x, offset_y = origin
        adjusted_x = (x - offset_x)
        adjusted_y = (y - offset_y)
        cos_rad = math.cos(radians)
        sin_rad = math.sin(radians)
        qx = offset_x + cos_rad * adjusted_x - sin_rad * adjusted_y
        qy = offset_y + sin_rad * adjusted_x + cos_rad * adjusted_y
        return qx, qy

    @staticmethod
    def rotate(xy: Vec2D, radians: float) -> np.ndarray:
        """Counter-clockwise rotation of the vector in radians. Positive angles
        are counter-clockwise and negative are clockwise rotations.

        Args:
            xy (Vec2D): A 2D vector.
            radians (float): Counter clockwise angle

        Returns:
            np.ndarray: Rotated point
        """
        x, y = xy
        cos_rad = math.cos(radians)
        sin_rad = math.sin(radians)
        qx = cos_rad * x - sin_rad * y
        qy = sin_rad * x + cos_rad * y
        return np.array([qx, qy])  #ADD ARRAY CHOP - draw_utility

    @staticmethod
    def angle(vector: Vec2D) -> float:
        """Return the angle in radians of a vector.

        Args:
            vector (Union[list, np.ndarray): A 2D vector

        Returns:
            float: Angle in radians

        Caution:
            The angle is defined from the Y axis!

            See https://docs.scipy.org/doc/numpy/reference/generated/numpy.arctan2.html
            ::

                    |-> Positive direction, defined from Y axis
                    |
                --------
                    |
                    |

                    x1       x2       arctan2(x1,x2)
                    +/- 0    +0       +/- 0
                    +/- 0    -0       +/- pi
                    > 0      +/-inf   +0 / +pi
                    < 0      +/-inf   -0 / -pi
                    +/-inf   +inf     +/- (pi/4)
                    +/-inf   -inf     +/- (3*pi/4)

            Note that +0 and -0 are distinct floating point numbers, as are +inf and -inf.
        """
        return np.arctan2(vector)

    @staticmethod
    def angle_between(v1: Vec2D, v2: Vec2D) -> float:
        """Returns the angle in radians between vectors 'v1' and 'v2'.

        Args:
            v1 (Vec2D): First vector
            v2 (Vec2D): Second vector

        Returns:
            float: Angle in radians. The angle of the ray intersecting the unit
            circle at the given x-coordinate in radians [0, pi]. This is a scalar.
        """
        v1_u = vec_unit_planar(v1)
        v2_u = vec_unit_planar(v2)
        return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

    @staticmethod
    def add_z(vec2D: np.array, z: float = 0.):
        """Turn a 2D vector into a 3D vector by adding the z coorindate.

        Args:
            vec2D (np.array): Input 2D vector.
            z (float): Add this value to the 3rd dimension.  Defaults to {0}.

        Returns:
            np.array: 3D vector.
        """
        if isinstance(vec2D[0], Iterable):
            return array([Vector.add_z(vec, z=z) for vec in vec2D])
        else:
            return array(list(vec2D) + [z])

    @staticmethod
    def normed(vec: Vec2D) -> Vec2D:
        """Return normed vector.

        Args:
            vec (Vec2D): Vector

        Returns:
            vector: Vec2D -- Unit normed version of vector
        """
        return vec / norm(vec)

    @staticmethod
    def norm(vec: Vec2D) -> float:
        """Return the norm of a 2D vector.

        Args:
            vec (Vec2D): 2D vector

        Returns:
            float: Length of vector
        """
        return norm(vec)

    def are_same(v1: Vec2D, v2: Vec2D, tol: int = 100) -> bool:
        """Check if two vectors are within an infentesmimal distance set by
        `tol` and machine epsilon.

        Args:
            v1 (Vec2D): First vector to check
            v2 (Vec2D): Second vector to check
            tol (int): How much to multiply the machine precision, np.finfo(float).eps,
                       by as the tolerance.  Defaults to 100.

        Returns:
            bool: Same or not
        """
        v1, v2 = np.array(v1), np.array(v2)
        return Vector.is_zero(v1 - v2, tol=tol)

    @staticmethod
    def is_zero(vec: Vec2D, tol: int = 100) -> bool:
        """Check if a vector is essentially zero within machine precision, set
        by `tol` and machine epsilon.

        Args:
            vec (Vec2D): Vector to check
            tol (int): How much to multiply the machine precision, np.finfo(float).eps,
                       by as the tolerance.  Defaults to 100.

        Returns:
            bool: Close to zero or not
        """
        return float(norm(vec)) < tol * np.finfo(float).eps

    @staticmethod
    def get_distance(u: Union[tuple, list, np.ndarray],
                     v: Union[tuple, list, np.ndarray],
                     precision: int = 9) -> float:
        """Get the Euclidean distance between points u and v to the specified
        precision.

        Args:
            u (Union[tuple, list, np.ndarray]): Coordinates of a point.
            v (Union[tuple, list, np.ndarray]): Coordinates of a second point.
            precision (int, optional): Precision of the result. Defaults to 9.

        Returns:
            float: Distance between u anbd v.
        """
        u, v = np.array(u), np.array(v)
        return round(abs(norm(u - v)), precision)

    @staticmethod
    def two_points_described(points2D: List[Vec2D]) -> Tuple[np.ndarray]:
        """Get the distance, units and tagents.

        Args:
            points (np.array or list): 2D list of points

        Returns:
            tuple: (distance_vec, dist_unit_vec, tangent_vec) -- Each is a vector np.array

        For a list of exactly two given 2D points, get:
            * d: the distance vector between them
            * n: normal vector defined by d
            * t: the vector tangent to n

        .. code-block:: python

            vec_D, vec_d, vec_n = Vector.difference_dnt(points)
        """
        assert len(points2D) == 2
        start = np.array(points2D[0])
        end = np.array(points2D[1])

        distance_vec = end - start  # distance vector
        # unit vector along the direction of the two point
        unit_vec = distance_vec / norm(distance_vec)
        # tangent vector counter-clockwise 90 deg rotation
        tangent_vec = np.round(Vector.rotate(unit_vec, np.pi / 2), decimals=11)

        if Vector.is_zero(distance_vec):
            logger.debug(
                f'Function `two_points_described` encountered a zero vector'
                ' length. The two points should not be the same.')

        return distance_vec, unit_vec, tangent_vec

    @staticmethod
    def snap_unit_vector(vec_n: Vec2D, flip: bool = False) -> Vec2D:
        """snaps to either the x or y unit vectors.

        Args:
            vec_n (Vec2D): 2D vector
            flip (bool): True to flip.  Defaults to False.

        Returns:
            Vec2D: Snapped vector
        """
        #TODO: done silly, fix up
        m = np.argmax(abs(vec_n))
        m = m if flip is False else int(not m)
        v = np.array([0, 0])
        v[m] = np.sign(vec_n[m])
        vec_n = v
        return vec_n
