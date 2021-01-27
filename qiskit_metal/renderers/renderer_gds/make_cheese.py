# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from ... import Dict
import math
import os
import gdspy
import shapely
import pandas as pd
import logging


### Presently this is not instantiated nor called nor executed.
class Cheesing():
    """Create a cheese cell based on input of no-cheese locations.
    """

    def __init__(
            self,
            multi_poly: shapely.geometry.multipolygon.MultiPolygon,
            all_nocheese_gds: list,
            lib: gdspy.GdsLibrary,
            minx: float,
            miny: float,
            maxx: float,
            maxy: float,
            chip_name: str,
            layer: int,
            datatype: int,
            logger: logging.Logger,
            max_points: int,
            cheese_shape: int = 0,

            #  For rectangle
            shape_0_x: float = 0.000050,
            shape_0_y: float = 0.000050,

            #  For Circle
            shape_1_radius: float = 0.000025):
        """Create the cheesing based on the no-cheese multi_poly.

        Args:
            multi_poly (shapely.geometry.multipolygon.MultiPolygon): The area on chip for no-cheese.
            all_nocheese_gds (list): The same as multi_poly, but a list to be used for gdspy.
            lib (gdspy.GdsLibrary): Holds all of the cells for export.
            minx (float): Chip minimum x location.
            miny (float): Chip minimum y location.
            maxx (float): Chip maximum x location.
            maxy (float): chip maximum y location.
            chip_name (str): User defined chip name.
            layer (int): Layer number for calculating the cheese.
            datatype (int): User defined datatype, considered a sub-layer number for where to place the cheese output.
            max_points (int): Used in gdspy to identify max number of points for a Polygon.
            logger (logging.Logger):  Used to give warnings and errors.
            cheese_shape (int, optional): 0 is rectangle. 1 is circle. Defaults to 0.
            shape_0_x (float, optional): The width will be centered at (x=0,y=0). Defaults to 0.000050.
            shape_0_y (float, optional): The height will be centered at (x=0,y=0). Defaults to 0.000050.
            shape_1_radius (float, optional): The radius of circle. Defaults to 0.000025.
        """

        # All the no-cheese locations.
        self.multi_poly = multi_poly
        self.nocheese_gds = all_nocheese_gds
        self.lib = lib

        # chip boundary, layer and datatype
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy

        self.chip_name = chip_name
        self.layer = layer
        self.datatype = datatype
        self.max_points = max_points

        self.logger = logger

        # Expect to mostly cheese a square, but allow for expansion.
        self.cheese_shape = cheese_shape
        self.shape_0_x = shape_0_x
        self.shape_0_y = shape_0_y
        self.shape_1_radius = shape_1_radius

        # Create a shapely the size of chip.
        self.boundary = shapely.geometry.Polygon([(minx, miny), (minx, maxy),
                                                  (maxx, maxy)])

    def apply_cheesing(self) -> gdspy.GdsLibrary:
        """Not complete. Need to populate self.lib with cheese holes.
        """
        self.make_one_hole_at_zero_zero()
        self.hole_to_lib()

        return self.lib

    def make_one_hole_at_zero_zero(self):
        """This method will create just one hole used for cheesing 
        defined by a shapely object.  It will be placed in self.hole.
        """
        if self.cheese_shape == 0:
            w, h = self.shape_0_x, self.shape_0_y
            self.hole = shapely.geometry.box(-w / 2, -h / 2, w / 2, h / 2)
        elif self.cheese_shape == 1:
            self.hole = shapely.geometry.Point(0, 0).buffer(self.shape_1_radius)
        else:
            self.logger.warning(
                f'The cheese_shape={cheese_shape} is unknown in Cheesing class.'
            )
        return

    def hole_to_lib(self):
        """Convert the self.hole to a gds cell and add to self.lib.

        This is not complete.
        """

        if isinstance(self.hole, shapely.geometry.Polygon):
            exterior_poly = gdspy.Polygon(list(self.hole.exterior.coords),
                                          layer=self.layer,
                                          datatype=self.datatype)

            # If polygons have a holes, need to remove it for gdspy.
            all_interiors = list()
            geom = self.hole
            if geom.interiors:
                for hole in geom.interiors:
                    interior_coords = list(hole.coords)
                    all_interiors.append(interior_coords)
                a_poly_set = gdspy.PloygonSet(all_interiors,
                                              layer=self.layer,
                                              datatype=self.datatype)
                a_poly = gdspy.boolean(exterior_poly,
                                       a_poly_set,
                                       'not',
                                       max_points=self.max_points,
                                       layer=self.layer,
                                       datatype=10)
            else:
                a_poly = exterior_poly.fracture(max_points=self.max_points)
        else:
            hole_type = type(self.hole)
            self.logger.warning(
                f'The self.hole was not converted to gdspy; the type \'{hole_type}\' was not handled.'
            )

        #convert a_poly to cell, then use cell reference to add to all the cheese in chip_rect_gds

        return