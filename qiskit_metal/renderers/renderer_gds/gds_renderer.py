from .. import config
from qiskit_metal.renderers.renderer_base import QRenderer
from ...toolbox_python.utility_functions import log_error_easy
from ...designs import QDesign
import qiskit_metal as metal
from qiskit_metal import designs, components, draw
from qiskit_metal import components as qlibrary
import logging
import sys
import pandas
import geopandas
import pandas as pd
import shapely
import gdspy
import os
import pathlib
import math

from typing import TYPE_CHECKING
from typing import Dict as Dict_
from typing import List, Tuple, Union

from operator import itemgetter

from ... import Dict


if not config.is_building_docs():
    from qiskit_metal import MetalGUI, Dict, Headings


class GDSRender(QRenderer):
    """Extends QRenderer to export GDS formatted files. The methods which a user will need for GDS export
    should be found within this class.

    layers:
        200 Emulated Chip size based on self.scaled_max_bound * max_bounds of elements on chip. 
            self.scaled_chip_poly
        201 Holds all of the qgeometries, in a cell, which have subtract as True. 
            After gdspy.boolean(), The cell is removed from lib. 
            self.q_subtract_true, cell=SUBTRACT
        202 Holds all of the qgeometries which have subtract as False.  
            self.q_subtract_false, cell=TOP

    datatype:
        * 10 Polygon
        * 11 Flexpath
    """

    def __init__(self, design: QDesign, initiate=True, bounding_box_scale: float = 1.2):
        """
        Args:
            design (QDesign): Use QGeometry within QDesign  to obtain elements for GDS file.
            initiate (bool): True to initiate the renderer. Defaults to True.
            bounding_box_scale (float): Scale box of components to render. Should be greater than 1.0.
        """
        super().__init__(design=design, initiate=initiate)

        self.gds_unit = 1.0 / self.design.parse_value('1 meter')
        self.lib = gdspy.GdsLibrary(unit=self.gds_unit)

        self.list_bounds = list()
        self.scaled_max_bound = tuple()

        self.all_subtract_true = geopandas.GeoDataFrame()
        self.all_subtract_false = geopandas.GeoDataFrame()

        # gdspy.polygon.PolygonSet is the base class.
        self.scaled_chip_poly = gdspy.Polygon([])

        # For now, say true, needs to come from options. #issue #255.
        self.ground_plane = True

        # layer and data numbers, needs to come from default options.
        # Example: self.ld_subtract = {"layer": 201, "data": 12}
        self.ld_subtract = {"layer": 201}
        self.ld_no_subtract = {"layer": 202}

        # create rectangle for layer , needs to come from default options.
        self.ld_chip = {"layer": 200, "datatype": 10}

        # needs to come from default_options, used for fillet in FlexPath
        self.bend_radius_num = 0.05
        self.corners = 'circular bend'
        self.tolerance = 0.001

        # bounding_box_scale will need to be migrated to some form of default_options
        if isinstance(bounding_box_scale, float) and bounding_box_scale >= 1.0:
            self.bounding_box_scale = bounding_box_scale
        elif isinstance(bounding_box_scale, int) and bounding_box_scale >= 1:
            self.bounding_box_scale = float(bounding_box_scale)
        else:
            self.design.logger.warning(
                f'Expected float and number greater than or equal to 1.0 for bounding_box_scale. \
                User provided bounding_box_scale = {bounding_box_scale}, using default of 1.2. .')

    def _clear_library(self):
        """Clear current library."""
        gdspy.current_library.cells.clear()

    def _can_write_to_path(self, file: str) -> int:
        """Check if can write file.

        Args:
            file (str): Has the path and/or just the file name.

        Returns:
            int: 1 if access is allowed. Else returns 0, if access not given.
        """
        directory_name = os.path.dirname(os.path.abspath(file))
        if os.access(directory_name, os.W_OK):
            return 1
        else:
            self.design.logger.warning(
                f'Not able to write to directory. File:"{file}" not written. Checked directory:"{directory_name}".')
            return 0

    def separate_subtract_qgeometry(self, table_name: str, table: geopandas.GeoSeries) -> None:
        """For each table, separate them by subtract being either True or False.

        Args:
            table_name (str): Name for "table".  Example is "poly", and "path".
            table (geopandas.GeoSeries): Table with similar qgeometries.
        """

        subtract_true = table[table['subtract'] == True]
        subtract_true['layer'] = self.ld_subtract['layer']

        subtract_false = table[table['subtract'] == False]
        subtract_false['layer'] = self.ld_no_subtract['layer']

        setattr(self, f'{table_name}_subtract_true', subtract_true)
        setattr(self, f'{table_name}_subtract_false', subtract_false)

    def get_bounds(self, gs_table: geopandas.GeoSeries) -> Tuple[float, float, float, float]:
        """Get the bounds for all of the elements in gs_table.

        Args:
            gs_table (pandas.GeoSeries): A pandas GeoSeries used to describe components in a design.

        Returns:
            Tuple[float, float, float, float]: The bounds of all of the elements in this table. [minx, miny, maxx, maxy]
        """
        if len(gs_table) == 0:
            return(0, 0, 0, 0)

        return gs_table.total_bounds

    def scale_max_bounds(self, all_bounds: list) -> Tuple[tuple, tuple]:
        """Given the list of tuples to represent all of the bounds for path, poly, etc.
        This will return the scaled using self.bounding_box_scale, and  the max bounds of the tuples provided.

        Args:
            all_bounds (list): Each tuple=(minx, miny, maxx, maxy) in list represents bounding box for poly, path, etc.

        Returns:
            tuple[tuple, tuple]: 
            first tuple: A scaled bounding box which includes all paths, polys, etc.;
            second tuple: A  bounding box which includes all paths, polys, etc.
        """

        # If given an empty list.
        if len(all_bounds) == 0:
            return (0.0, 0.0, 0.0, 0.0)

        # Get an inclusive bounding box to contain all of the tuples provided.
        minx, miny, maxx, maxy = self.inclusive_bound(all_bounds)

        # Center of inclusive bounding box
        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2

        scaled_width = (maxx - minx) * self.bounding_box_scale
        scaled_height = (maxy - miny) * self.bounding_box_scale

        # Scaled inclusive bounding box by self.bounding_box_scale.
        scaled_box = (center_x - (.5 * scaled_width),
                      center_y - (.5 * scaled_height),
                      center_x + (.5 * scaled_width),
                      center_y + (.5 * scaled_height))

        return scaled_box, (minx, miny, maxx, maxy)

    def inclusive_bound(self, all_bounds: list) -> tuple:
        """Given a list of tuples which describe corners of a box, i.e. (minx, miny, maxx, maxy).
        This method will find the box, which will include all boxes.  In another words, the smallest minx and miny;
        and the largest maxx and maxy.

        Args:
            all_bounds (list): List of bounds. Each tuple corresponds to a box.

        Returns:
            tuple: Describe a box which includes the area of each box in all_bounds.
        """

        # If given an empty list.
        if len(all_bounds) == 0:
            return (0.0, 0.0, 0.0, 0.0)

        inclusive_tuple = (min(all_bounds, key=itemgetter(0))[0],
                           min(all_bounds, key=itemgetter(1))[1],
                           max(all_bounds, key=itemgetter(2))[2],
                           max(all_bounds, key=itemgetter(3))[3])
        return inclusive_tuple

    def rect_for_ground(self) -> None:
        """Use the maximum bounds for all qgeometry on chip.  Scale the size of chip.
           Use gdspy.Polygon() because gdspy.boolean() requires it.
        """

        rectangle_points = [(self.max_bound[0], self.max_bound[1]),
                            (self.max_bound[2], self.max_bound[1]),
                            (self.max_bound[2], self.max_bound[3]),
                            (self.max_bound[0], self.max_bound[3])]
        chip_poly = gdspy.Polygon(rectangle_points, **self.ld_chip)

        self.scaled_chip_poly = chip_poly.scale(
            scalex=self.bounding_box_scale, scaley=self.bounding_box_scale)
        pass  # for breakpoint

    def create_qgeometry_for_gds(self, highlight_qcomponents: list = []) -> int:
        """Using self.design, this method does the following:

        1. Gather the QGeometries to be used to write to file.
           Duplicate names in hightlight_qcomponents will be removed without warning.

        2. Populate self.list_bounds, which contains the maximum bound for all elements to render.

        3. Calculate scaled bounding box to emulate size of chip using self.scaled_max_bound
           and place into self.scaled_max_bound.

        4. Gather Geometries to export to GDS format.

        Args:
            highlight_qcomponents (list): List of strings which denote the name of QComponents to render.
                                        If empty, render all comonents in design.
                                        If QComponent names are dupliated, duplicates will be ignored.

        Returns:
            int: 0 if all ended well. Otherwise, 1 if QComponent name not in design.
        """
        # Remove identical QComponent names.
        unique_qcomponents = list(set(highlight_qcomponents))

        # Confirm all QComponent are in design.
        for qcomp in unique_qcomponents:
            if qcomp not in self.design.name_to_id:
                self.design.logger.warning(
                    f'The component={qcomp} in highlight_qcomponents not in QDesign. The GDS data not generated.')
                return 1

        # put the QGeomtry into GDS format.
        self.list_bounds.clear()

        all_subtracts = []
        all_no_subtracts = []

        for table_name in self.design.qgeometry.get_element_types():
            # self.design.qgeometry.tables is a dict. key=table_name, value=geopandas.GeoDataFrame
            if len(unique_qcomponents) == 0:
                table = self.design.qgeometry.tables[table_name]
            else:
                table = self.design.qgeometry.tables[table_name]
                # Convert string QComponent.name  to QComponent.id
                highlight_id = [self.design.name_to_id[a_qcomponent]
                                for a_qcomponent in unique_qcomponents]

                # Remove QComponents which are not requested.
                table = table[table['component'].isin(highlight_id)]

            # Determine bound box and return scalar larger than size.
            bounds = tuple(self.get_bounds(table))
            # Add the bounds of each table to list.
            self.list_bounds.append(bounds)

            if self.ground_plane:
                self.separate_subtract_qgeometry(table_name, table)
                all_subtracts.append(
                    getattr(self, f'{table_name}_subtract_true'))
                all_no_subtracts.append(
                    getattr(self, f'{table_name}_subtract_false'))

            # polys is gdspy.Polygon;    paths is gdspy.LineString
            q_geometries = table.apply(self.qgeometry_to_gds, axis=1)
            setattr(self, f'{table_name}s', q_geometries)

        self.scaled_max_bound, self.max_bound = self.scale_max_bounds(
            self.list_bounds)

        if self.ground_plane:
            self.rect_for_ground()

            self.all_subtract_true = geopandas.GeoDataFrame(
                pd.concat(all_subtracts, ignore_index=False))
            self.all_subtract_false = geopandas.GeoDataFrame(
                pd.concat(all_no_subtracts, ignore_index=False))

            self.q_subtract_true = self.all_subtract_true.apply(
                self.qgeometry_to_gds, axis=1)

            self.q_subtract_false = self.all_subtract_false.apply(
                self.qgeometry_to_gds, axis=1)

        return 0

    def write_poly_path_to_file(self, file_name: str) -> None:
        """Using the geometries for each table name, write to a GDS file.

        -> rectangle on Y

        -> put all the 'subtract' shapes on layer X

        -> Boolean subtract X from Y and put that on Z

        -> add all the non-subtract shapes to Z as well.

        (Y = layer number 200) self.scaled_chip_poly

        (X = layer number 201) self.q_subtract_true , cell=SUBTRACT

        (Z = layer number 202) self.q_subtract_false, cell=TOP

        Args:
            file_name (str): The path and file name to write the gds file.
                             Name needs to include desired extention, i.e. "a_path_and_name.gds".
        """

        # Create a new GDS library file. It can contains multiple cells.
        self._clear_library()

        lib = gdspy.GdsLibrary(unit=self.gds_unit)

        cell = lib.new_cell('NO_EDITS', overwrite_duplicate=True)

        for table_name in self.design.qgeometry.get_element_types():
            q_geometries = getattr(self, f'{table_name}s')
            if q_geometries is None:
                self.design.logger.warning(
                    f'There are no {table_name}s to write.')
            else:
                cell.add(q_geometries)

            if q_geometries is None:
                self.design.logger.warning(
                    f'There is no table named "{table_name}s" to write.')
            else:
                cell.add(q_geometries)

        if self.ground_plane:
            # # For ground plane.
            ground_cell = lib.new_cell('TOP', overwrite_duplicate=True)
            subtract_cell = lib.new_cell('SUBTRACT', overwrite_duplicate=True)
            subtract_cell.add(self.q_subtract_true)

            '''gdspy.boolean is not documented clearly.  
            If there are multiple elements to subtract (both poly and path), 
            the way I could make it work is to put them into a cell, within lib.  
            I used the method cell_name.get_polygonsets(), which appears to convert all elements within the cell to poly.
            After the boolean(), I deleted the cell from lib.
            The memory is freed up then.
            '''
            diff_geometry = gdspy.boolean(
                self.scaled_chip_poly, subtract_cell.get_polygons(), 'not', layer=202)

            lib.remove(subtract_cell)

            if diff_geometry is None:
                self.design.logger.warning(
                    f'There is no table named diff_geometry to write.')
            else:
                ground_cell.add(diff_geometry)

            if self.q_subtract_false is None:
                self.design.logger.warning(
                    f'There is no table named self.q_subtract_false to write.')
            else:
                ground_cell.add(self.q_subtract_false)

        lib.write_gds(file_name)

    def export_to_gds(self, file_name: str, highlight_qcomponents: list = []) -> int:
        """Use the design which was used to initialize this class.
        The QGeometry element types of both "path" and "poly", will
        be used, to convert QGeometry to GDS formatted file.

        Args:
            file_name (str): File name which can also include directory path.
                             If the file exists, it will be overwritten.
            highlight_qcomponents (list): List of strings which denote the name of QComponents to render.
                                        If empty, render all comonents in design.

        Returns:
            int: 0=file_name can not be written, otherwise 1=file_name has been written
        """

        # TODO: User provide list of QComponent names to render, instead of entire design.

        if not self._can_write_to_path(file_name):
            return 0

        if (self.create_qgeometry_for_gds(highlight_qcomponents) == 0):
            self.write_poly_path_to_file(file_name)
            return 1
        else:
            return 0

    def qgeometry_to_gds(self, element: pd.Series) -> 'gdspy.polygon':
        """Convert the design.qgeometry table to format used by GDS renderer. 
        Convert the class to a series of GDSII elements.

        Args:
            element (pd.Series): Expect a shapley object.

        Returns:
            'gdspy.polygon' or 'gdspy.FlexPath': Convert the class to a series of GDSII 
            format on the input pd.Series.
        """

        """
        *NOTE:*
        GDS:
            points (array-like[N][2]) – Coordinates of the vertices of the polygon.
            layer (integer) – The GDSII layer number for this element.
            datatype (integer) – The GDSII datatype for this element (between 0 and 255).
                                  datatype=10 or 11 means only that they are from a
                                  Polygon vs. LineString.  This can be changed.
        See:
            https://gdspy.readthedocs.io/en/stable/reference.html#polygon
        """

        geom = element.geometry  # type: shapely.geometry.base.BaseGeometry

        if isinstance(geom, shapely.geometry.Polygon):

            # TODO: Handle  list(polygon.interiors)
            return gdspy.Polygon(list(geom.exterior.coords),
                                 layer=element.layer if not element['subtract'] else 0,
                                 # layer=element.layer,
                                 datatype=10,
                                 )
        elif isinstance(geom, shapely.geometry.LineString):
            '''
            class gdspy.FlexPath(points, width, offset=0, corners='natural', ends='flush', 
            bend_radius=None, tolerance=0.01, precision=0.001, max_points=199, 
            gdsii_path=False, width_transform=True, layer=0, datatype=0)

            Only fillet, if number is greater than zero.
            '''
            if math.isnan(element.fillet) or element.fillet <= 0:
                to_return = gdspy.FlexPath(list(geom.coords),
                                           width=element.width,
                                           layer=element.layer if not element['subtract'] else 0,
                                           # layer=element.layer,
                                           datatype=11)
            else:
                to_return = gdspy.FlexPath(list(geom.coords),
                                           width=element.width,
                                           layer=element.layer if not element['subtract'] else 0,
                                           # layer=element.layer,
                                           datatype=11,
                                           corners=self.corners,
                                           bend_radius=self.bend_radius_num,
                                           tolerance=self.tolerance
                                           )
            return to_return
        else:
            # TODO: Handle
            self.design.logger.warning(
                f'Unexpected shapely object geometry.'
                f'The variable element is {data(geom)}, method can currently handle Polygon and FlexPath.')
            # print(geom)
            return None
