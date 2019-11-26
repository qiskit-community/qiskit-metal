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
Module to handle rendering to HFSS.

Raises:
    Exception: HFSS exceptions on connection or failure of hfss to draw objects.

@date: 2019
@author: Zlatko K. Minev
"""

import shapely
from .. import logger
from .utility import to_Vec3Dz, Polygon, parse_units, is_rectangle  # * # lazy, todo fix


def draw_objects_shapely(oModeler, objects: dict, root_name: str, delimiter='_', **kwargs):
    """
    Render a list of a dictionary of shapely objects to HFSS

    Wrapper functions, ccalls draw_object_shapely

    Arguments:
        oModeler {pyEPR modeler} -- modeler instance to pyEPR
        objects {list or dict} -- [description]
        root_name {str} -- [description]

    Keyword Arguments:
        delimiter {str} -- [description] (default: {'_'})

    Raises:
        Exception: Unhandled object type

    Returns:
        list or dict -- of the HFSS objects (pyEPR poly classes)
    """
    objects_result = {}

    if isinstance(objects, list):
        for objs in objects:
            res = draw_objects_shapely(
                oModeler, objs, root_name, delimiter='_', **kwargs)
            objects_result.update(res)
        return objects_result

    # Otherwise
    for name, obj in objects.items():
        new_name = root_name + delimiter + name

        if isinstance(obj, dict):
            res = draw_objects_shapely(
                oModeler, obj, new_name, delimiter=delimiter, **kwargs)
        elif isinstance(obj, shapely.geometry.base.BaseGeometry):
            res = draw_object_shapely(oModeler, obj, new_name, **kwargs)
        else:
            logger.error("Unhandled!")
            raise Exception(
                f"Unhandled object shape name={new_name} \nobj={obj}")
        objects_result.update({name: res})

    return objects_result


def draw_object_shapely(oModeler, obj, name, size_z=0., pos_z=0., hfss_options=None):
    """
    Draw a single shapely object in HFSS

    Arguments:
        oModeler {[pyEPR modeler]} -- [description]
        obj {[shapely.geometry.Polygon or shapely.geometry.LineString]} -- object shapely to be drawn
        name {[type]} -- [description]

    Keyword Arguments:
        size_z {float} -- height of object (default: {0})
        pos_z {float} -- position in the z plane of the object(default: {0})
        hfss_options {[type]} -- [description] (default: {None})

    Raises:
        Exception: Unhandled object shape

    Returns:
        pyEPR hfss poly -- [description]
    """

    if not hfss_options:
        hfss_options = {}

    if isinstance(obj, shapely.geometry.Polygon):
        points = Polygon(obj).coords_ext
        # TODO: Handle multiple chips
        points_3d = to_Vec3Dz(points, parse_units(pos_z))

        if is_rectangle(obj):  # Draw as rectangle
            logger.debug(f'Drawing a rectangle: {name}')
            (x_min, y_min, x_max, y_max) = obj.bounds
            poly_hfss = oModeler.draw_rect_corner(*parse_units(
                [[x_min, y_min, pos_z], x_max-x_min, y_max-y_min, size_z]),
                name=name, **hfss_options)
            return poly_hfss

        # Draw general closed poly
        points_3d = parse_units(points_3d)
        poly_hfss = oModeler.draw_polyline(
            points_3d, closed=True, **hfss_options)
        # rename: handle bug if the name of the cut already exits and is used to make a cut
        poly_hfss = poly_hfss.rename(name)
        return poly_hfss

    elif isinstance(obj, shapely.geometry.LineString):
        points_3d = parse_units(points_3d)
        poly_hfss = oModeler.draw_polyline(
            points_3d, closed=False, **hfss_options)
        poly_hfss = poly_hfss.rename(name)
        return poly_hfss

    else:
        logger.error("Unhandled!")
        raise Exception(f"Unhandled object shape name={name} \nobj={obj}")
