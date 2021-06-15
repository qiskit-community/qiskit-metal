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
""" For GDS export, separate the logic for cheesing."""

import logging
from typing import Union
import gdspy
import shapely
import numpy as np


class Cheesing():
    """Create a cheese cell based on input of no-cheese locations."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    # pylint: disable=too-few-public-methods

    # To be used by QGDSRenderer only.
    # Number of instance attributes is acceptable for this case.

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
        is_neg_mask: bool,
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
            multi_poly (shapely.geometry.multipolygon.MultiPolygon): The area
                                            on chip per layer for no-cheese.
            all_nocheese_gds (list): The same as multi_poly, but a list to be
                                    used for gdspy.
            lib (gdspy.GdsLibrary): Holds all of the cells for export.
            minx (float): Chip minimum x location.
            miny (float): Chip minimum y location.
            maxx (float): Chip maximum x location.
            maxy (float): Chip maximum y location.
            chip_name (str): User defined chip name.
            edge_nocheese (float): Keep a buffer around the perimeter of chip,
                                    that will not need cheesing.
            layer (int): Layer number for calculating the cheese.
            is_neg_mask: Export a negative mask for chip and layer of init. If
                        False, export a positive mask.
            datatype_cheese (int): User defined datatype, considered a
                                sub-layer number for where to place the
                                cheese output.
            datatype_keepout (int): User defined datatype, considered a
                                sub-layer number for where to place the
                                keepout of cheese.
            max_points (int): Used in gdspy to identify max number of points
                                for a Polygon.
            precision (float): Used in gdspy to identify precision.
            logger (logging.Logger):  Used to give warnings and errors.
            cheese_shape (int, optional): 0 is rectangle. 1 is circle.
                                        Defaults to 0.
            shape_0_x (float, optional): The width will be centered at
                                    (x=0,y=0). Defaults to 0.000050.
            shape_0_y (float, optional): The height will be centered at
                                    (x=0,y=0). Defaults to 0.000050.
            shape_1_radius (float, optional): The radius of circle.
                                    Defaults to 0.000025.
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
        self.is_neg_mask = is_neg_mask
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

        # max dimension of grid is chip size reduced by self.edge_nocheese
        self.grid_minx = self.minx + self.edge_nocheese
        self.grid_miny = self.miny + self.edge_nocheese
        self.grid_maxx = self.maxx - self.edge_nocheese
        self.grid_maxy = self.maxy - self.edge_nocheese

        if self.grid_maxx <= self.grid_minx or self.grid_maxy <= self.grid_miny:
            self.logger.warning(
                'When edge_nocheese is applied to decrease the chip size, of where cheesing ',
                'will happen, the resulting size is not realistic.')

        self.one_hole_cell = None

        self.hole = None

    def apply_cheesing(self) -> gdspy.GdsLibrary:
        """Prototype, not complete.

        Need to populate self.lib with cheese holes.
        """

        if self._error_checking_hole_delta() == 0:
            # Place hole into self.hole
            self._make_one_hole_at_zero_zero()

            _ = self._hole_to_lib()
            self._cell_with_grid()
        else:
            self.logger.warning('Cheesing not implemented.')

        return self.lib

    def _error_checking_hole_delta(self) -> int:
        """Check ratio of hole size vs hole spacing.

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

    def _make_one_hole_at_zero_zero(self):
        """This method will create just one hole used for cheesing defined by a
        shapely object.

        It will be placed in self.hole.
        """
        if self.cheese_shape == 0:
            width, height = self.shape_0_x, self.shape_0_y
            self.hole = shapely.geometry.box(-width / 2, -height / 2, width / 2,
                                             height / 2)
        elif self.cheese_shape == 1:
            self.hole = shapely.geometry.Point(0, 0).buffer(self.shape_1_radius)
        else:
            self.logger.warning(
                f'The cheese_shape={self.cheese_shape} is unknown in Cheesing class.'
            )

    def _hole_to_lib(self) -> gdspy.polygon.Polygon:
        """Convert the self.hole to a gds cell and add to self.lib.
        Put the hole on datatype_cheese +2.  This is expected to change when
        we agree to some convention.

        Returns:
            gdspy.polygon.Polygon: The gdspy polygon for single hole for cheesing. None is not made.
        """
        a_poly = None
        if isinstance(self.hole, shapely.geometry.Polygon):
            exterior_poly = gdspy.Polygon(list(self.hole.exterior.coords),
                                          layer=self.layer,
                                          datatype=self.datatype_cheese + 2)

            # If polygons have a holes, need to remove (subtract) it for gdspy.
            all_interiors = list()
            geom = self.hole
            if geom.interiors:
                for inside in geom.interiors:
                    interior_coords = list(inside.coords)
                    all_interiors.append(interior_coords)
                a_poly_set = gdspy.PolygonSet(all_interiors,
                                              layer=self.layer,
                                              datatype=self.datatype_cheese + 2)
                a_poly = gdspy.boolean(exterior_poly,
                                       a_poly_set,
                                       'not',
                                       max_points=self.max_points,
                                       precision=self.precision,
                                       layer=self.layer,
                                       datatype=self.datatype_cheese + 2)
            else:
                a_poly = exterior_poly.fracture(max_points=self.max_points)
        else:
            hole_type = type(self.hole)
            self.logger.warning(f'The self.hole was not converted to gdspy; '
                                f'the type \'{hole_type}\' was not handled.')

        #convert a_poly to cell, then use cell reference to add to all the cheese in chip_rect_gds
        chip_layer_only_top_name = f'TOP_{self.chip_name}_{self.layer}'
        cheese_one_hole_cell_name = f'TOP_{self.chip_name}_{self.layer}_one_hole'
        self.one_hole_cell = self.lib.new_cell(cheese_one_hole_cell_name,
                                               overwrite_duplicate=True)
        self.one_hole_cell.add(a_poly)

        if self.one_hole_cell.get_bounding_box() is not None:
            self.lib.cells[chip_layer_only_top_name].add(
                gdspy.CellReference(self.one_hole_cell))
        else:
            self.lib.remove(self.one_hole_cell)

        return a_poly

    def _cell_with_grid(self):
        """Use the hole at self.one_hole_cell to create a grid.

        Then use the no_cheese cell to remove the holes from grid.  The
        difference will be used subtract from the ground layer with
        geometry. The cells are added to the Top_<chip_name>.
        """

        gather_holes_cell = self._get_all_holes()
        diff_holes_cell = self._subtract_keepout_from_hole_grid(
            gather_holes_cell)
        self.lib.remove(gather_holes_cell)

        if self.is_neg_mask:
            #negative mask for given chip and layer
            self._move_to_under_top_chip_layer_name(diff_holes_cell)
        else:
            #positive mask for given chip and layer
            self._subtract_from_ground_and_move_under_top_chip_layer(
                diff_holes_cell)

    def _subtract_from_ground_and_move_under_top_chip_layer(
            self, diff_holes_cell: gdspy.library.Cell):
        """Get the existing chip_only_top_name cell, then add the holes to it.
        Also, add ground_cheesed_cell under chip_only_top_name

        Args:
            diff_holes_cell (gdspy.library.Cell): New cell with cheesed ground
        """

        #chip_only_top_name = f'TOP_{self.chip_name}'
        chip_only_top_layer_name = f'TOP_{self.chip_name}_{self.layer}'
        #if chip_only_top_name in self.lib.cells:
        if chip_only_top_layer_name in self.lib.cells:
            if diff_holes_cell.get_bounding_box() is not None:
                self.lib.cells[chip_only_top_layer_name].add(
                    gdspy.CellReference(diff_holes_cell))
                ground_cheese_cell = self._subtract_holes_from_ground(
                    diff_holes_cell)

                #Move to under Top_main_layer (Top_chipname_#)
                self._move_to_under_top_chip_layer_name(ground_cheese_cell)
            else:
                self.lib.remove(diff_holes_cell)

    def _subtract_keepout_from_hole_grid(
            self, gather_holes_cell: gdspy.library.Cell) -> gdspy.library.Cell:
        """Given a cell with all the holes, subtract the keepout region.
        Then return a new cell with the result.

        Args:
            gather_holes_cell (gdspy.library.Cell): Holds a grid of all
                                                the holes for cheesing.

        Returns:
            gdspy.library.Cell: Newly created cell that holds the difference
                                        of holes minus the keep=out region.
        """

        # subtact the keepout, note, Based on user options,
        # the keepout (no_cheese) cell may not be in self.lib.
        temp_keepout_chip_layer_cell = f'temp_keepout_{self.chip_name}_{self.layer}'
        temp_keepout_cell = self.lib.new_cell(temp_keepout_chip_layer_cell,
                                              overwrite_duplicate=True)
        temp_keepout_cell.add(self.nocheese_gds)
        diff_holes = gdspy.boolean(gather_holes_cell.get_polygonsets(),
                                   temp_keepout_cell.get_polygonsets(),
                                   'not',
                                   max_points=self.max_points,
                                   precision=self.precision,
                                   layer=self.layer,
                                   datatype=self.datatype_cheese + 1)
        diff_holes_cell_name = f'TOP_{self.chip_name}_{self.layer}_Cheese_diff'
        diff_holes_cell = self.lib.new_cell(diff_holes_cell_name,
                                            overwrite_duplicate=True)
        diff_holes_cell.add(diff_holes)

        self.lib.remove(temp_keepout_chip_layer_cell)
        return diff_holes_cell

    def _get_all_holes(self) -> gdspy.library.Cell:
        """Return a cell with a grid of holes. The keepout has not been
        applied yet.

        Returns:
            gdspy.library.Cell: Cell containing all the holes.
        """
        gather_holes_cell_name = f'Gather_holes_{self.chip_name}_{self.layer}'
        gather_holes_cell = self.lib.new_cell(gather_holes_cell_name,
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
            for x_loc in x_holes:
                for y_loc in y_holes:
                    gather_holes_cell.add(
                        gdspy.CellReference(self.one_hole_cell,
                                            origin=(x_loc, y_loc)))

        return gather_holes_cell

    def _subtract_holes_from_ground(
            self, diff_holes_cell) -> Union[gdspy.library.Cell, None]:
        """Get reference to ground cell and then subtract the holes from
        ground. Place the difference into a new cell, which will eventually
        be added under Top.

        Args:
            diff_holes_cell ([type]): Cell which contains all the holes.

        Returns:
            Union[gdspy.library.Cell, None]: If worked, the new cell with
            cheesed ground, otherwise, None.
        """

        # Still need to 'not' with Top_main_1 (ground)
        top_chip_layer_name = f'TOP_{self.chip_name}_{self.layer}'
        if top_chip_layer_name in self.lib.cells.keys():
            ground_cell = self.lib.cells[top_chip_layer_name]
            ground_cheese = gdspy.boolean(ground_cell.get_polygons(),
                                          diff_holes_cell.get_polygonsets(),
                                          'not',
                                          max_points=self.max_points,
                                          precision=self.precision,
                                          layer=self.layer,
                                          datatype=self.datatype_cheese)
            ground_cheese_cell_name = (f'TOP_{self.chip_name}_{self.layer}'
                                       f'_Cheese_{self.datatype_cheese}')
            ground_cheese_cell = self.lib.new_cell(ground_cheese_cell_name,
                                                   overwrite_duplicate=True)
            return ground_cheese_cell.add(ground_cheese)

        self.logger.warning(
            f'The cell:{top_chip_layer_name} was not found in self.lib. '
            f'Cheesing not implemented.')
        return None

    def _move_to_under_top_chip_layer_name(self, a_cell: gdspy.library.Cell):
        """Move the cell to under TOP_<chip name>_<layer number>.

        Args:
            a_cell (gdspy.library.Cell): A GDSPY cell.
        """
        chip_only_top_chip_layer_name = f'TOP_{self.chip_name}_{self.layer}'
        if chip_only_top_chip_layer_name in self.lib.cells:
            if a_cell.get_bounding_box() is not None:
                self.lib.cells[chip_only_top_chip_layer_name].add(
                    gdspy.CellReference(a_cell))
            else:
                self.lib.remove(a_cell)
