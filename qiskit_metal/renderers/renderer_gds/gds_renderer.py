import logging
import sys
import pandas as pd
import shapely
import gdspy
from typing import TYPE_CHECKING, List

from ... import Dict
from ...designs import QDesign
from ...toolbox_python.utility_functions import log_error_easy
#from ..renderer_base.renderer_gui_base import QRendererGui


from qiskit_metal.renderers.renderer_base import QRenderer

from PyQt5.QtWidgets import QInputDialog, QLineEdit, QTableView, QMenu, QMessageBox, QAbstractItemView
from PyQt5.QtCore import QPoint, QModelIndex
from PyQt5.QtGui import QContextMenuEvent
from PyQt5 import QtWidgets, QtCore, QtGui
from qiskit_metal.components.qubits.transmon_pocket import TransmonPocket
from qiskit_metal import MetalGUI, Dict, Headings
from qiskit_metal import components as qlibrary
from qiskit_metal import designs, components, draw
import qiskit_metal as metal


class GDSRender(QRenderer):

    def __init__(self, design: QDesign, initiate=True):
        super().__init__(design=design, initiate=initiate)
        gds_unit = .000001
        self.lib = gdspy.GdsLibrary(units=gds_unit)

    def clear_library(self):
        # Create a new GDS library file. It can contains multiple cells.
        gdspy.current_library.cells.clear()

    def path_and_poly_to_gds(self, file_name_and_path: str) -> int:
        '''
        return codes:
            file has been written
            path not there
        '''

        poly_table = design.qgeometry.tables['poly']
        print('design.qgeometry.tables[poly]')
        print(poly_table)
        print(' ')

        path_table = design.qgeometry.tables['path']
        print('design.qgeometry.tables[path]')
        print(path_table)
        print('')

        poly_geometry = list(poly_table.geometry)
        path_geometry = list(path_table.geometry)

        a_gds = GDSRender(design)

        # polys is a gdspy.Polygon
        polys = poly_table.apply(a_gds.to_gds, axis=1)

        # paths in a gdspy.?
        #paths = path_table.apply(a_gds.to_gds, axis=1)

        # Create a new GDS library file. It can contains multiple cells.
        gdspy.current_library.cells.clear()

        lib = gdspy.GdsLibrary()

        # New cell
        cell = lib.new_cell('TOP', overwrite_duplicate=True)
        cell.add(polys)
        # cell.add(paths)

        # Save the library in a file.
        lib.write_gds('Pins_Example.gds')

    def qgeometry_to_gds(self, element: pd.Series):
        """Convert the design.qgeometry table to format used by GDS renderer.

        :param element: Expect a shapley object.
        :type element: pd.Series
        :return: GDS format on the input pd.Series.
        :rtype: gdspy.polygon
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

            to_return = gdspy.Polygon(list(geom.coords),
                                      layer=element.layer if not element['subtract'] else 0,
                                      datatype=11)
            return to_return
        else:
            #TODO: Handle
            print(geom)
            return None
