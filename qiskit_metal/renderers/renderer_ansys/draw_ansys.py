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
    Exception: HFSS exceptions on connection or failure of hfss to draw components.

@date: 2019
@author: Zlatko K. Minev
"""

import shapely
from .. import logger
from .utility import to_Vec3Dz, Polygon, is_rectangle  # * # lazy, todo fix
from .parse import parse_value_hfss

def draw_objects_shapely(oModeler, components: dict, root_name: str, delimiter='_', **kwargs):
    """
    Render a list of a dictionary of shapely components to HFSS

    Wrapper functions, ccalls draw_object_shapely

    Arguments:
        oModeler {pyEPR modeler} -- modeler instance to pyEPR
        components {list or dict} -- [description]
        root_name {str} -- [description]

    Keyword Arguments:
        delimiter {str} -- [description] (default: {'_'})

    Raises:
        Exception: Unhandled object type

    Returns:
        list or dict -- of the HFSS components (pyEPR poly classes)
    """
    objects_result = {}

    if isinstance(components, list):
        for objs in components:
            res = draw_objects_shapely(
                oModeler, objs, root_name, delimiter='_', **kwargs)
            objects_result.update(res)
        return objects_result

    # Otherwise
    for name, obj in components.items():
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
        points = get_poly_pts(obj)
        # TODO: Handle multiple chips
        points_3d = to_Vec3Dz(points, parse_value_hfss(pos_z))

        if is_rectangle(obj):  # Draw as rectangle
            logger.debug(f'Drawing a rectangle: {name}')
            (x_min, y_min, x_max, y_max) = obj.bounds
            poly_hfss = oModeler.draw_rect_corner(*parse_value_hfss(
                [[x_min, y_min, pos_z], x_max-x_min, y_max-y_min, size_z]),
                name=name, **hfss_options)
            return poly_hfss

        # Draw general closed poly
        points_3d = parse_value_hfss(points_3d)
        poly_hfss = oModeler.draw_polyline(
            points_3d, closed=True, **hfss_options)
        # rename: handle bug if the name of the cut already exits and is used to make a cut
        poly_hfss = poly_hfss.rename(name)
        return poly_hfss

    elif isinstance(obj, shapely.geometry.LineString):
        points_3d = parse_value_hfss(points_3d)
        poly_hfss = oModeler.draw_polyline(
            points_3d, closed=False, **hfss_options)
        poly_hfss = poly_hfss.rename(name)
        return poly_hfss

    else:
        logger.error("Unhandled!")
        raise Exception(f"Unhandled object shape name={name} \nobj={obj}")





'''
################################################################################
###
# Universal core drawing func properties
###

# @deprecated
def do_PerfE(options, design, obj):
    _, oModeler = design.get_modeler()
    if options.get('do_PerfE',  DEFAULT['do_PerfE']):
        oModeler.append_PerfE_assignment(
            str(obj) if options.get('BC_individual', DEFAULT['BC_individual'])
            else options.get('BC_name', 'PerfE'), [str(obj)])


# @deprecated
def do_cut_ground(options, design, objs):
    ''' do_cut '''
    _, oModeler = design.get_modeler()
    if options.get('do_cut',  DEFAULT['do_cut']):
        assert isinstance(objs, list)
        oModeler.subtract(design.get_ground_plane(options), objs)

# @deprecated
def do_mesh(options, design, objs):
    ''' do_mesh  - TO DO replace with funciton draw_hfss'''
    _, oModeler = design.get_modeler()
    if options.get('do_mesh',  DEFAULT._hfss.do_mesh):
        assert isinstance(objs, list)
        oModeler.subtract(design.get_ground_plane(options), objs)
'''


################################################################################
###
# Susbtrate and bounding box
###

# Absolute Offset for -+X, -+Y, and -+Z; # 890 is the nominal depth of the copper penny 35 mil
DEFAULT_OPTIONS['draw_bounding_box'] = [
    [0, 0], [0, 0], ['0.890mm', '0.900mm']],


def draw_bounding_box(design, options=DEFAULT_OPTIONS['draw_bounding_box']):
    """
    .. figure:: figures/draw_chip1.png
        :align: center
        :width: 6in
    """
    _, oModeler = design.get_modeler()

    oModeler.draw_region(options, PaddingType="Absolute Offset")


# draw_substrate
 # For chip size, negative draws the substrate box down
DEFAULT_OPTIONS['draw_substrate'] = Dict({
    'pos_xy': "['0um', '0um']",
    'size': "['8.5mm', '6.5mm', '-0.750mm']",
    'elevation': 0,
    'ground_plane': 'ground_plane',
    'substrate': 'substrate',
    'material': 'silicon',
    'color_plane': DEFAULT.colors.ground_main,
    'transparency_plane': 0,
    'transparency_substrate': 0,
    'wireframe_substrate': False
})


def draw_substrate(design, options):
    """
    .. figure:: figures/draw_chip1.png
        :align: center
        :width: 6in

    Args:
        elevation: Specify the z heigth
    """
    options = {**DEFAULT_OPTIONS['draw_substrate'], **options}
    _, oModeler = design.get_modeler()

    def hparse(x): return parse_value_hfss(design.parse_value(x))

    # Parse and convert to HFSS units
    elevation = hparse(options['elevation'])
    pos_xy = hparse(options['pos_xy'])
    size = hparse(options['size'])
    origin = array([*pos_xy, elevation])
    #print(elevation, pos_xy, size)

    # Sheet
    oModeler.draw_rect_center(origin,
                              size[0], size[1], 0,
                              name=options['ground_plane'],
                              color=options['color_plane'],
                              transparency=options['transparency_plane'])
    oModeler.assign_perfect_E(options['ground_plane'],
                              name=options['ground_plane'])

    # substrate box
    oModeler.draw_box_corner([origin[0]-size[0]/2., origin[1]-size[1]/2, origin[2]],
                             size,
                             name=options['substrate'],
                             material=options['material'],
                             color=(186, 186, 205),
                             transparency=options['transparency_substrate'],
                             wireframe=options['wireframe_substrate'])

