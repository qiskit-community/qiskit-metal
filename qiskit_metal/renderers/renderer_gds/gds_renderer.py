import logging
import sys
import pandas as pd
import shapely
import gdspy
import os
from typing import TYPE_CHECKING, List

from ... import Dict
from ...designs import QDesign
from ...toolbox_python.utility_functions import log_error_easy
#from ..renderer_base.renderer_gui_base import QRendererGui


from qiskit_metal.renderers.renderer_base import QRenderer

from qiskit_metal.components.qubits.transmon_pocket import TransmonPocket
from qiskit_metal import MetalGUI, Dict, Headings
from qiskit_metal import components as qlibrary
from qiskit_metal import designs, components, draw
import qiskit_metal as metal


class GDSRender(QRenderer):
    """Extends QRenderer to export GDS formatted files. The methods which a user will need for GDS export 
    should be found within this class.
    """

    def __init__(self, design: QDesign, initiate=True):
        """
        Args:
            design (QDesign): Use QGeometry within QDesign  to obtain elements for GDS file. 
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
        """
        super().__init__(design=design, initiate=initiate)
        gds_unit = .000001
        self.lib = gdspy.GdsLibrary(units=gds_unit)

    def _clear_library(self):
        """Create a new GDS library file. It can contains multiple cells."""
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
                f'Not able to write to directory. File not written.: {directory_name}')
            return 0

    # For Next feature
    # def get_bounds(self, gs_table: pandas.GeoSeries) -> Tuple[float, float, float, float]:
    #     """Get the bounds for all of the elements in gs_table.

    #     Args:
    #         gs_table (pandas.GeoSeries): A pandas GeoSeries used to describe components in a design.

    #     Returns:
    #         Tuple[float, float, float, float]: The bounds of all of the elements in this table.
    #     """
    #     if len(gs_table) == 0:
    #         return(0, 0, 0, 0)
    #     else:
    #         return gs_table.total_bounds

    def path_and_poly_to_gds(self, file_name: str) -> int:
        """Use the design which was used to initialize this class.
        The QGeometry element types of both "path" and "poly", will
        be used, to convert QGeometry to GDS formatted file.

        Args:
            file_name (str): File name which can also include directory path.

        Returns:
            int: 0=file_name can not be written, otherwise 1=file_name has been written
        """

        if not self._can_write_to_path(file_name):
            return 0

        poly_table = self.design.qgeometry.tables['poly']
        # print('design.qgeometry.tables[poly]')
        # print(poly_table)
        # print(' ')

        path_table = self.design.qgeometry.tables['path']
        # print('design.qgeometry.tables[path]')
        # print(path_table)

        # # Determine bound box and return scalar larger than size.
        # poly_bounds = self.get_bounds(poly_table)
        # path_bounds = self.get_bounds(path_table)
        # list_bounds = [poly_bounds, path_bounds]

        poly_geometry = list(poly_table.geometry)
        path_geometry = list(path_table.geometry)

        # polys is a gdspy.Polygon
        polys = poly_table.apply(self.qgeometry_to_gds, axis=1)
        # paths is a gdspy.LineString
        paths = path_table.apply(self.qgeometry_to_gds, axis=1)

        # Create a new GDS library file. It can contains multiple cells.
        gdspy.current_library.cells.clear()

        lib = gdspy.GdsLibrary()

        # New cell
        cell = lib.new_cell('TOP', overwrite_duplicate=True)
        cell.add(polys)
        cell.add(paths)

        # Save the library in a file.
        lib.write_gds(file_name)

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
            #TODO: Handle
            print(geom)
            return None
