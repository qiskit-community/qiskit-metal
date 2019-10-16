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


from .draw_utility import *
#from . import DEFAULT, DEFAULT_OPTIONS # This can cause circular improt issues, needs to define DEFAULTS first



def draw_objects_shapely(oModeler, objects, root_name, delimiter='_', **kwargs):
    objects_result = {}
    
    if isinstance(objects, list):
        for objs in objects:
            res = draw_objects_shapely(oModeler, objs, root_name, delimiter='_', **kwargs)
            objects_result.update(res)
        return objects_result    
    
    # Otherwise
    for name, obj in objects.items():
        new_name = root_name + delimiter + name
        
        if isinstance(obj, dict):
            res = draw_objects_shapely(oModeler, obj, new_name, delimiter = delimiter, **kwargs)
        elif isinstance(obj, shapely.geometry.base.BaseGeometry):
            res = draw_object_shapely(oModeler, obj, new_name, **kwargs)
        else:
            logger.error("Unhandled!")
            raise Exception(f"Unhandled object shape name={new_name} \nobj={obj}")
        objects_result.update({name:res})
        
    return objects_result
                                 
def draw_object_shapely(oModeler, obj, name, sizeZ = 0, pos_z = 0, hfss_options = {}):
               
    if isinstance(obj, shapely.geometry.Polygon):
        points = Polygon(obj).coords_ext
        points3D = to_Vec3Dz(points, parse_units(pos_z)) # TODO: Handle multiple chips
    
        if is_rectangle(obj): # Draw as rectangle
            logger.debug(f'Drawing a rectangle: {name}')
            (x_min, y_min, x_max, y_max) = obj.bounds
            poly_hfss = oModeler.draw_rect_corner(*parse_units(
                            [ [x_min, y_min, pos_z], x_max-x_min, y_max-y_min, sizeZ]), 
                            name=name, **hfss_options)
            return poly_hfss
        
        # Draw general closed poly 
        points3D  = parse_units(points3D)
        poly_hfss = oModeler.draw_polyline(points3D, closed = True, **hfss_options)
        poly_hfss = poly_hfss.rename(name)  # bug if the name of the cut already exits and is used to make a cut
        return poly_hfss
        
    elif isinstance(obj, shapely.geometry.LineString):
        points3D  = parse_units(points3D)
        poly_hfss = oModeler.draw_polyline(points3D, closed = False, **hfss_options)
        poly_hfss = poly_hfss.rename(name) 
        return poly_hfss
        
    else:
        #TODO: Handle multipolygon and multline stirng, etc
        logger.error("Unhandled!")
        raise Exception(f"Unhandled object shape name={name} \nobj={obj}")

