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
"""For GDS export, separate the logic for cheesing."""

import logging
from typing import Union

import gdstk
import numpy as np
import shapely


class Cheesing:
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
        lib: gdstk.Library,
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
        fab: bool,
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
        """Create cheesing polygons based on the no-cheese regions.

        Args:
            multi_poly: No-cheese areas per layer (shapely multipolygon).
            all_nocheese_gds: Same geometry in a gdstk-friendly list.
            lib: Library that will hold all generated cells.
            minx: Chip minimum x location.
            miny: Chip minimum y location.
            maxx: Chip maximum x location.
            maxy: Chip maximum y location.
            chip_name: User-defined chip name.
            edge_nocheese: Buffer around the chip perimeter to leave un-cheesed.
            layer: Layer number for calculating the cheese.
            is_neg_mask: If True, export a negative mask; otherwise positive.
            datatype_cheese: Datatype for cheese polygons.
            datatype_keepout: Datatype for keepout regions.
            fab: If True, output fabrication-ready layers; if False, include
                intermediate/debug layers.
            max_points: Maximum number of points for a polygon in gdstk.
            precision: gdstk precision to use.
            logger: Logger to emit warnings/errors.
            cheese_shape: 0 for rectangle, 1 for circle.
            shape_0_x: Rectangle width (centered at 0,0).
            shape_0_y: Rectangle height (centered at 0,0).
            shape_1_radius: Circle radius.
            delta_x: Spacing between holes in x.
            delta_y: Spacing between holes in y.
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

        self.fab = fab

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
                "When edge_nocheese is applied to decrease the chip size, of where cheesing ",
                "will happen, the resulting size is not realistic.",
            )

        self.one_hole_cell = None

        self.hole = None

    def apply_cheesing(self) -> gdstk.Library:
        """Prototype, not complete.

        Need to populate self.lib with cheese holes.
        """

        if self._error_checking_hole_delta() == 0:
            # Place hole into self.hole
            self._make_one_hole_at_zero_zero()

            _ = self._hole_to_lib()
            self._cell_with_grid()
        else:
            self.logger.warning("Cheesing not implemented.")

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
            observe = (1 if self.delta_x <= self.shape_0_x or
                       self.delta_y <= self.shape_0_y else 0)
        elif self.cheese_shape == 1:
            diameter = 2 * self.shape_1_radius
            return 1 if self.delta_x <= diameter or self.delta_y <= diameter else 0
        else:
            self.logger.warning(
                f"The cheese_shape={self.cheese_shape} is unknown in Cheesing class."
            )
            return 2

        if observe == 1:
            self.logger.warning(
                "The size of delta spacing is same as or smaller than hole.")

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
                f"The cheese_shape={self.cheese_shape} is unknown in Cheesing class."
            )

    def _hole_to_lib(self) -> gdstk.Polygon:
        """Convert the self.hole to a gds cell and add to self.lib.
        Put the hole on datatype_cheese +2.  This is expected to change when
        we agree to some convention.

        Returns:
            gdstk.Polygon: The gdstk polygon for single hole for cheesing. None is not made.
        """
        a_poly = None
        if isinstance(self.hole, shapely.geometry.Polygon):
            exterior_poly = gdstk.Polygon(
                list(self.hole.exterior.coords),
                layer=self.layer,
                datatype=self.datatype_cheese + 2,
            )

            # If polygons have a holes, need to remove (subtract) it for gdstk.
            all_interiors = list()
            geom = self.hole
            if geom.interiors:
                for inside in geom.interiors:
                    interior_coords = list(inside.coords)
                    all_interiors.append(interior_coords)
                a_poly_set = gdstk.PolygonSet(all_interiors,
                                              layer=self.layer,
                                              datatype=self.datatype_cheese + 2)
                a_poly = gdstk.boolean(
                    exterior_poly,
                    a_poly_set,
                    "not",
                    precision=self.precision,
                    layer=self.layer,
                    datatype=self.datatype_cheese + 2,
                )
            else:
                a_poly = exterior_poly.fracture(max_points=self.max_points,
                                                precision=self.precision)
        else:
            hole_type = type(self.hole)
            self.logger.warning(f"The self.hole was not converted to gdstk; "
                                f"the type '{hole_type}' was not handled.")

        # convert a_poly to cell, then use cell reference to add to all the cheese in chip_rect_gds
        chip_layer_only_top_name = f"TOP_{self.chip_name}_{self.layer}"
        cheese_one_hole_cell_name = f"TOP_{self.chip_name}_{self.layer}_one_hole"
        self.one_hole_cell = self.lib.new_cell(cheese_one_hole_cell_name)
        self.one_hole_cell.add(*a_poly)

        if self.one_hole_cell.bounding_box() is not None:
            next(
                (c for c in self.lib.cells if c.name == chip_layer_only_top_name
                )).add(gdstk.Reference(self.one_hole_cell))
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
            # negative mask for given chip and layer
            self._move_to_under_top_chip_layer_name(diff_holes_cell)
            if self.fab:
                self._both_pos_and_neg_mask_fab()

                # Need the diff cell for negative mask.
                # self._remove_cheese_diff_cell()
        else:
            # positive mask for given chip and layer
            if self.fab:
                self._subtract_from_ground_and_move_under_top_chip_layer(
                    diff_holes_cell)
                self._both_pos_and_neg_mask_fab()

                #  This is something special still to do.
                self._remove_cheese_diff_cell()
                self._remove_ground_chip_layer()
            else:
                self._subtract_from_ground_and_move_under_top_chip_layer(
                    diff_holes_cell)

    def _both_pos_and_neg_mask_fab(self):
        """For both positive and negative mask need to have this cell removed when
        user has fabricate.fab=True.
        """
        self._remove_cell_one_hole()

    def _remove_cell_one_hole(self):
        """Remove cell with just one hole."""
        cheese_one_hole_cell_name = f"TOP_{self.chip_name}_{self.layer}_one_hole"
        cheese_one_hole_cell = next(
            (c for c in self.lib.cells if c.name == cheese_one_hole_cell_name),
            None)
        if cheese_one_hole_cell:
            self.lib.remove(cheese_one_hole_cell)

    def _subtract_from_ground_and_move_under_top_chip_layer(
            self, diff_holes_cell: gdstk.Cell):
        """Get the existing chip_only_top_name cell, then add the holes to it.
        Also, add ground_cheesed_cell under chip_only_top_name

        Args:
            diff_holes_cell (gdstk.Cell): New cell with cheesed ground
        """

        chip_only_top_layer_name = f"TOP_{self.chip_name}_{self.layer}"
        chip_only_top_layer_cell = next(
            (c for c in self.lib.cells if c.name == chip_only_top_layer_name),
            None)
        if chip_only_top_layer_cell:
            if diff_holes_cell.bounding_box() is not None:
                chip_only_top_layer_cell.add(gdstk.Reference(diff_holes_cell))
                ground_cheese_cell = self._subtract_holes_from_ground(
                    diff_holes_cell)

                # Move to under Top_main_layer (Top_chipname_#)
                self._move_to_under_top_chip_layer_name(ground_cheese_cell)
            else:
                self.lib.remove(diff_holes_cell)

    def _subtract_keepout_from_hole_grid(
            self, gather_holes_cell: gdstk.Cell) -> gdstk.Cell:
        """Given a cell with all the holes, subtract the keepout region.
        Then return a new cell with the result.

        Args:
            gather_holes_cell (gdstk.Cell): Holds a grid of all
                                                the holes for cheesing.

        Returns:
            gdstk.Cell: Newly created cell that holds the difference
                                        of holes minus the keep=out region.
        """

        # subtact the keepout, note, Based on user options,
        # the keepout (no_cheese) cell may not be in self.lib.
        temp_keepout_chip_layer_cell = f"temp_keepout_{self.chip_name}_{self.layer}"
        temp_keepout_cell = self.lib.new_cell(temp_keepout_chip_layer_cell)
        temp_keepout_cell.add(*self.nocheese_gds)
        diff_holes = gdstk.boolean(
            gather_holes_cell.get_polygons(),
            temp_keepout_cell.get_polygons(),
            "not",
            precision=self.precision,
            layer=self.layer,
            datatype=self.datatype_cheese + 1,
        )
        diff_holes_cell_name = f"TOP_{self.chip_name}_{self.layer}_Cheese_diff"
        diff_holes_cell = self.lib.new_cell(diff_holes_cell_name)
        diff_holes_cell.add(*diff_holes)

        self.lib.remove(temp_keepout_cell)
        return diff_holes_cell

    def _get_all_holes(self) -> gdstk.Cell:
        """Return a cell with a grid of holes. The keepout has not been
        applied yet.

        Returns:
            gdstk.Cell: Cell containing all the holes.
        """
        gather_holes_cell_name = f"Gather_holes_{self.chip_name}_{self.layer}"
        gather_holes_cell = self.lib.new_cell(gather_holes_cell_name)

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
                        gdstk.Reference(self.one_hole_cell,
                                        origin=(x_loc, y_loc)))

        return gather_holes_cell

    def _subtract_holes_from_ground(
            self, diff_holes_cell: gdstk.Cell) -> Union[gdstk.Cell, None]:
        """Get reference to ground cell and then subtract the holes from
        ground. Place the difference into a new cell, which will eventually
        be added under Top.

        Args:
            diff_holes_cell ([type]): Cell which contains all the holes.

        Returns:
            Union[gdstk.Cell, None]: If worked, the new cell with
            cheesed ground, otherwise, None.
        """

        # Still need to 'not' with Top_main_1 (ground)
        top_chip_layer_name = f"TOP_{self.chip_name}_{self.layer}"
        ground_cell_name = f"ground_{self.chip_name}_{self.layer}"
        if next((c for c in self.lib.cells if c.name == top_chip_layer_name),
                None):
            ground_cell = next(
                (c for c in self.lib.cells if c.name == ground_cell_name))
            # Need to keep the depth at 0, otherwise all the
            # cell references (junctions) will be added for boolean.
            ground_cheese = gdstk.boolean(
                ground_cell.get_polygons(depth=0),
                diff_holes_cell.get_polygons(),
                "not",
                precision=self.precision,
                layer=self.layer,
                datatype=self.datatype_cheese,
            )
            ground_cheese_cell_name = (
                f"TOP_{self.chip_name}_{self.layer}_Cheese_{self.datatype_cheese}"
            )
            ground_cheese_cell = self.lib.new_cell(ground_cheese_cell_name)
            return ground_cheese_cell.add(*ground_cheese)

        self.logger.warning(
            f"The cell:{top_chip_layer_name} was not found in self.lib. "
            f"Cheesing not implemented.")
        return None

    def _move_to_under_top_chip_layer_name(self, a_cell: gdstk.Cell):
        """Move the cell to under TOP_<chip name>_<layer number>.

        Args:
            a_cell (gdstk.Cell): A GDSTK cell.
        """
        chip_only_top_chip_layer_name = f"TOP_{self.chip_name}_{self.layer}"
        chip_only_top_chip_layer_cell = next(
            (c for c in self.lib.cells
             if c.name == chip_only_top_chip_layer_name), None)
        if chip_only_top_chip_layer_cell:
            if a_cell.bounding_box() is not None:
                chip_only_top_chip_layer_cell.add(gdstk.Reference(a_cell))
            else:
                self.lib.remove(a_cell)

    def _remove_cheese_diff_cell(self):
        """For a lib, chip and layer, remove the Cheese_diff cell."""
        cell_name = f"TOP_{self.chip_name}_{self.layer}_Cheese_diff"
        cell = next((c for c in self.lib.cells if c.name == cell_name), None)
        if cell:
            self.lib.remove(cell)

    def _remove_ground_chip_layer(self):
        """[For a lib, chip and layer, remove the ground cell
        which is created for positive mask.
        """
        cell_name = f"ground_{self.chip_name}_{self.layer}"
        cell = next((c for c in self.lib.cells if c.name == cell_name), None)
        if cell:
            self.lib.remove(cell)
