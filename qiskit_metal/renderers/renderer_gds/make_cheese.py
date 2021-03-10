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
import numpy as np
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
        edge_nocheese: float,
        layer: int,
        datatype_cheese: int,
        datatype_keepout: int,
        logger: logging.Logger,
        max_points: int,
        precision: float,
        cheese_shape: int = 0,

        #  For rectangle
        shape_0_x: float = 0.000050,
        shape_0_y: float = 0.000050,

        #  For Circle
        shape_1_radius: float = 0.000025,

        # delta spacing for holes
        delta_x: float = 0.00010,
        delta_y: float = 0.00010,
    ):
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
            edge_nocheese (float): Keep a buffer around the perimeter of chip, that will not need cheesing.
            layer (int): Layer number for calculating the cheese.
            datatype_cheese (int): User defined datatype, considered a sub-layer number for where to place the cheese output.
            datatype_keepout (int): User defined datatype, considered a sub-layer number for where to place the keepout of cheese.
            max_points (int): Used in gdspy to identify max number of points for a Polygon.
            precision (float): Used in gdspy to identify precision. 
            logger (logging.Logger):  Used to give warnings and errors.
            cheese_shape (int, optional): 0 is rectangle. 1 is circle. Defaults to 0.
            shape_0_x (float, optional): The width will be centered at (x=0,y=0). Defaults to 0.000050.
            shape_0_y (float, optional): The height will be centered at (x=0,y=0). Defaults to 0.000050.
            shape_1_radius (float, optional): The radius of circle. Defaults to 0.000025.
            delta_x (float, optional): The spacing between holes in x.
            delta_y (float, optional): The spacing between holes in y.

        """

        # All the no-cheese locations.
        self.multi_poly = multi_poly
        self.nocheese_gds = all_nocheese_gds
        self.lib = lib

        # chip boundary, layer and datatype, buffer for perimeter
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy

        self.chip_name = chip_name

        self.edge_nocheese = edge_nocheese
        self.layer = layer
        self.datatype_cheese = datatype_cheese
        self.datatype_keepout = datatype_keepout
        self.max_points = max_points
        self.precision = precision

        self.logger = logger

        # Expect to mostly cheese a square, but allow for expansion.
        self.cheese_shape = cheese_shape
        self.shape_0_x = shape_0_x
        self.shape_0_y = shape_0_y
        self.shape_1_radius = shape_1_radius

        # Create a shapely the size of chip.
        self.boundary = shapely.geometry.Polygon([(minx, miny), (minx, maxy),
                                                  (maxx, maxy)])

        self.delta_x = delta_x
        self.delta_y = delta_y

        self.cheese_cell = None

        # max dimension of grid is chip size reducded by self.edge_nocheese
        self.grid_minx = self.minx + self.edge_nocheese
        self.grid_miny = self.miny + self.edge_nocheese
        self.grid_maxx = self.maxx - self.edge_nocheese
        self.grid_maxy = self.maxy - self.edge_nocheese

        if self.grid_maxx <= self.grid_minx or self.grid_maxy <= self.grid_miny:
            self.logger.warning(
                f'When edge_nocheese is applied to decrease the chip size, of where cheesing ',
                'will happen, the resulting size is not realistic.')

        self.one_hole_cell = None

    def apply_cheesing(self) -> gdspy.GdsLibrary:
        """Not complete. Need to populate self.lib with cheese holes.
        """

        if 0 == self.error_checking_hole_delta():
            self.make_one_hole_at_zero_zero()
            gdspy_hole = self.hole_to_lib()
            self.cell_with_grid(gdspy_hole)
        else:
            self.logger.warning(f'Cheesing not implemented.')

        return self.lib

    def error_checking_hole_delta(self) -> int:
        """Check ratio of hole size vs hole spacing

        Returns:
            int: Observation based on hole size and spacing.

            * 0 No issues detected.
            * 1 Delta spacing less than or equal to hole
            * 2 cheese_shape is unknown to Cheesing class.
        """
        observe = -1
        if self.cheese_shape == 0:
            observe = 1 if self.delta_x <= self.shape_0_x or self.delta_y <= self.shape_0_y else 0
        elif self.cheese_shape == 1:
            diameter = 2 * self.shape_1_radius
            return 1 if self.delta_x <= diameter or self.delta_y <= diameter else 0
        else:
            self.logger.warning(
                f'The cheese_shape={self.cheese_shape} is unknown in Cheesing class.'
            )
            return 2

        if observe == 1:
            self.logger.warning(
                'The size of delta spacing is same as or smaller than hole.')

        return observe

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
                f'The cheese_shape={self.cheese_shape} is unknown in Cheesing class.'
            )

    def hole_to_lib(self) -> gdspy.polygon.Polygon:
        """Convert the self.hole to a gds cell and add to self.lib.

        Returns:
            gdspy.polygon.Polygon: The gdspy polgon for single hole for cheesing. None is not made.
        """
        a_poly = None
        if isinstance(self.hole, shapely.geometry.Polygon):
            exterior_poly = gdspy.Polygon(list(self.hole.exterior.coords),
                                          layer=self.layer,
                                          datatype=self.datatype_cheese)

            # If polygons have a holes, need to remove (subtract) it for gdspy.
            all_interiors = list()
            geom = self.hole
            if geom.interiors:
                for hole in geom.interiors:
                    interior_coords = list(hole.coords)
                    all_interiors.append(interior_coords)
                a_poly_set = gdspy.PloygonSet(all_interiors,
                                              layer=self.layer,
                                              datatype=self.datatype_cheese)
                a_poly = gdspy.boolean(exterior_poly,
                                       a_poly_set,
                                       'not',
                                       max_points=self.max_points,
                                       layer=self.layer,
                                       datatype=self.datatype_cheese)
            else:
                a_poly = exterior_poly.fracture(max_points=self.max_points)
        else:
            hole_type = type(self.hole)
            self.logger.warning(
                f'The self.hole was not converted to gdspy; the type \'{hole_type}\' was not handled.'
            )

        #convert a_poly to cell, then use cell reference to add to all the cheese in chip_rect_gds
        chip_only_top_name = f'TOP_{self.chip_name}'
        cheese_one_hole_cell_name = f'TOP_{self.chip_name}_{self.layer}_one_hole'
        self.one_hole_cell = self.lib.new_cell(cheese_one_hole_cell_name,
                                               overwrite_duplicate=True)
        self.one_hole_cell.add(a_poly)

        if self.one_hole_cell.get_bounding_box() is not None:
            self.lib.cells[chip_only_top_name].add(
                gdspy.CellReference(self.one_hole_cell))
        else:
            self.lib.remove(self.one_hole_cell)

        return a_poly

    def cell_with_grid(self, gdspy_hole: gdspy.polygon.Polygon):
        """`[summary]`
        """

        gather_holes_cell = self.lib.new_cell('Gather_holes',
                                              overwrite_duplicate=True)

        x_holes = np.arange(self.grid_minx,
                            self.grid_maxx,
                            self.delta_x,
                            dtype=float).tolist()
        y_holes = np.arange(self.grid_miny,
                            self.grid_maxy,
                            self.delta_y,
                            dtype=float).tolist()

        if self.one_hole_cell is not None:
            for x in x_holes:
                for y in y_holes:
                    gather_holes_cell.add(
                        gdspy.CellReference(self.one_hole_cell, origin=(x, y)))

        # subtact the keepout
        no_cheese_cell_name = f'TOP_{self.chip_name}_{self.layer}_NoCheese_{self.datatype_keepout}'

        if no_cheese_cell_name in self.lib.cells.keys():
            keepout_cell = self.lib.cells[no_cheese_cell_name]
            a = 5  #for breakpoint
            '''gdspy.boolean() is not documented clearly.
                        If there are multiple elements to subtract (both poly and path),
                        the way I could make it work is to put them into a cell, within lib.
                        I used the method cell_name.get_polygons(),
                        which appears to convert all elements within the cell to poly.
            '''

            diff_holes = gdspy.boolean(gather_holes_cell.get_polygonsets(),
                                       keepout_cell.get_polygonsets(),
                                       'not',
                                       max_points=self.max_points,
                                       precision=self.precision,
                                       layer=self.layer,
                                       datatype=self.datatype_cheese)
            diff_holes_cell_name = f'TOP_{self.chip_name}_{self.layer}_Cheese_diff'
            diff_holes_cell = self.lib.new_cell(diff_holes_cell_name,
                                                overwrite_duplicate=True)
            diff_holes_cell.add(diff_holes)

        #Move to under Top_main (Top_chipname)
        chip_only_top_name = f'TOP_{self.chip_name}'
        if chip_only_top_name in self.lib.cells:
            if diff_holes_cell.get_bounding_box() is not None:
                self.lib.cells[chip_only_top_name].add(
                    gdspy.CellReference(diff_holes_cell))
                self.lib.remove(gather_holes_cell)
            else:
                self.lib.remove(diff_holes_cell)

        # Still need to 'not' with Top_main_1 (ground)

        a = 5  #for breakpoint
