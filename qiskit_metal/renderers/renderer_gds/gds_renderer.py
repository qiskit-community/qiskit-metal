import logging
import sys
import pandas
import geopandas
import pandas as pd
import shapely
import gdspy
import os

from typing import TYPE_CHECKING
from typing import Dict as Dict_
from typing import List, Tuple, Union

from operator import itemgetter

from ... import Dict
from ...designs import QDesign
from ...toolbox_python.utility_functions import log_error_easy

from qiskit_metal.renderers.renderer_base import QRenderer

#from qiskit_metal.components.qubits.transmon_pocket import TransmonPocket

from .. import config
if not config.is_building_docs():
    from qiskit_metal import MetalGUI, Dict, Headings
from qiskit_metal import components as qlibrary
from qiskit_metal import designs, components, draw
import qiskit_metal as metal


class GDSRender(QRenderer):
    """Extends QRenderer to export GDS formatted files. The methods which a user will need for GDS export
    should be found within this class.
    """

    def __init__(self, design: QDesign, initiate=True, bounding_box_scale: float = 1.2):
        """
        Args:
<<<<<<< HEAD
            design (QDesign): Use QGeometry within QDesign  to obtain elements for GDS file.
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
            bounding_box_scale (float, optional): Scale box of components to render. Should be greater than 1.0.
=======
            design (QDesign): Use QGeometry within QDesign  to obtain elements for GDS file. 
            initiate (bool): True to initiate the renderer. Defaults to True.
>>>>>>> v0.2-dev
        """
        super().__init__(design=design, initiate=initiate)
        self.gds_unit = self.design.get_units()

        self.lib = gdspy.GdsLibrary(units=self.gds_unit)

        self.list_bounds = list()
        self.scaled_max_bound = tuple()

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
                f'Not able to write to directory. File not written: {directory_name}.')
            return 0

    def get_bounds(self, gs_table: geopandas.GeoSeries) -> Tuple[float, float, float, float]:
        """Get the bounds for all of the elements in gs_table.

        Args:
            gs_table (pandas.GeoSeries): A pandas GeoSeries used to describe components in a design.

        Returns:
            Tuple[float, float, float, float]: The bounds of all of the elements in this table. [minx, miny, maxx, maxy]
        """
        if len(gs_table) == 0:
            return(0, 0, 0, 0)
        else:
            return gs_table.total_bounds

    def scale_max_bounds(self, all_bounds: list) -> tuple:
        """Given the list of tuples to represent all of the bounds for path, poly, etc.
        This will return the scalar, self.bounding_box_scale, of the max bounds of the tuples provided.

        Args:
            all_bounds (list): Each tuple=(minx, miny, maxx, maxy) in list represents bounding box for poly, path, etc.

        Returns:
            tuple: A scaled bounding box which includes all paths, polys, etc.
        """

        # If given an empty list.
        if len(all_bounds) == 0:
            return (0.0, 0.0, 0.0, 0.0)
        else:
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

            return scaled_box

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
        else:
            inclusive_tuple = (min(all_bounds, key=itemgetter(0))[0],
                               min(all_bounds, key=itemgetter(1))[1],
                               max(all_bounds, key=itemgetter(2))[2],
                               max(all_bounds, key=itemgetter(3))[3])
            return inclusive_tuple

    def create_poly_path_for_gds(self, highlight_qcomponents: list = []) -> None:
        """Using self.design, this method does the following: 
        1. Gather the QGeometries to be used to write to file.
        2. Populate self.list_bounds, which contains the maximum bound for all elements to render.
        3. Calculate scaled bounding box to emulate size of chip using self.scaled_max_bound 
        and place into self.scaled_max_bound.

        Args:
            highlight_qcomponents (list): List of strings which denote the name of QComponents to render.
                                        If empty, render all comonents in design.

        """

        for table_name in self.design.qgeometry.get_element_types():

            # design.qgeometry.tables is a dict.
            # key=table_name, value=geopandas.GeoDataFrame
            if len(highlight_qcomponents) == 0:
                table = self.design.qgeometry.tables[table_name]
            else:

                table = self.design.qgeometry.tables[table_name]
                highlight_id = [self.design.name_to_id[a_qcomponent]
                                for a_qcomponent in highlight_qcomponents]

                table = table[table['component'].isin(highlight_id)]

            setattr(self, f'{table_name}_table', table)
            setattr(self, f'{table_name}_geometry', list(table.geometry))

            q_geometries = table.apply(self.qgeometry_to_gds, axis=1)
            # polys is gdspy.Polygon
            # paths is gdspy.LineString
            setattr(self, f'{table_name}s', q_geometries)

            # Determine bound box and return scalar larger than size.
            bounds = tuple(self.get_bounds(table))
            # Add the bounds of each table to list.
            self.list_bounds.append(bounds)

        self.scaled_max_bound = self.scale_max_bounds(self.list_bounds)

    def write_poly_path_to_file(self, file_name: str) -> None:
        """Using the geometries for each table name, write to a GDS file.

        Args:
            file_name (str): The path and file name to write the gds file.
                             Name needs to include desired extention, i.e. ".gds".
        """

        # Create a new GDS library file. It can contains multiple cells.
        self._clear_library()

        lib = gdspy.GdsLibrary()

        # New cell
        cell = lib.new_cell('TOP', overwrite_duplicate=True)

        for table_name in self.design.qgeometry.get_element_types():
            self.q_geometries = getattr(self, f'{table_name}s')
            if self.q_geometries is None:
                # self.design.logger(f'There are no {table_name} to write.')
                pass
            else:
                cell.add(self.q_geometries)

        # Save the library in a file.
        lib.write_gds(file_name)

    def path_and_poly_to_gds(self, file_name: str, highlight_qcomponents: list = []) -> int:
        """Use the design which was used to initialize this class.
        The QGeometry element types of both "path" and "poly", will
        be used, to convert QGeometry to GDS formatted file.

        Args:
            file_name (str): File name which can also include directory path.
            highlight_qcomponents (list): List of strings which denote the name of QComponents to render.
                                        If empty, render all comonents in design.

        Returns:
            int: 0=file_name can not be written, otherwise 1=file_name has been written
        """

        # TODO: User provide list of QComponent names to render, instead of entire design.

        if not self._can_write_to_path(file_name):
            return 0

        self.create_poly_path_for_gds(highlight_qcomponents)

        self.write_poly_path_to_file(file_name)

        return 1

    def qgeometry_to_gds(self, element: pd.Series) -> 'gdspy.polygon':
        """Convert the design.qgeometry table to format used by GDS renderer.

        Args:
            element (pd.Series): Expect a shapley object.

        Returns:
            'gdspy.polygon': GDS format on the input pd.Series.
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
                                 datatype=10,
                                 )
        elif isinstance(geom, shapely.geometry.LineString):
            width = element.width
            to_return = gdspy.FlexPath(list(geom.coords),
                                       width=element.width,
                                       layer=element.layer if not element['subtract'] else 0,
                                       datatype=11)
            return to_return
        else:
            # TODO: Handle
            print(geom)
            return None
