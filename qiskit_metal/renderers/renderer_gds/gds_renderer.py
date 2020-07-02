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

        # From jupyter notebook.
        # self.

    def to_gds(self, element: pd.Series):
        """Convert the design.elements table to format used by GDS renderer.

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
        else:
            #TODO: Handle
            print(geom)
            return None
