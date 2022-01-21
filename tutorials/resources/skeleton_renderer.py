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

from qiskit_metal import Dict
import math
from scipy.spatial import distance
import os
import gdspy
import geopandas
import shapely

from shapely.geometry import LineString as LineString
from copy import deepcopy
from operator import itemgetter
from typing import TYPE_CHECKING
from typing import Dict as Dict_
from typing import List, Tuple, Union, Any, Iterable
import pandas as pd
from pandas.api.types import is_numeric_dtype

import numpy as np

from qiskit_metal.renderers.renderer_base import QRenderer
from qiskit_metal.toolbox_metal.parsing import is_true

from qiskit_metal import config
if not config.is_building_docs():
    from qiskit_metal.toolbox_python.utility_functions import can_write_to_path
    from qiskit_metal.toolbox_python.utility_functions import get_range_of_vertex_to_not_fillet

if TYPE_CHECKING:
    # For linting typechecking, import modules that can't be loaded here under normal conditions.
    # For example, I can't import QDesign, because it requires Qrenderer first. We have the
    # chicken and egg issue.
    from qiskit_metal.designs import QDesign


class QSkeletonRenderer(QRenderer):
    """Extends QRenderer to create new Skeleton QRenderer.

    This QRenderer will print to a file the number_of_bones and the
    names of QGeometry tables that will be used to export the
    QComponents the user highlighted.
    """

    #: Default options, over-written by passing ``options` dict to render_options.
    #: Type: Dict[str, str]
    default_options = Dict(
        # An option unique to QSkeletonRenderer.
        number_of_bones='206',
        # Default file name for geometry table names.
        file_geometry_tables='./simple_output_default_name.txt')
    """Default options"""

    name = 'skeleton'
    """Name used in Metal code to refer to this QRenderer."""

    # When additional columns are added to QGeometry, this is the example to populate it.
    # e.g. element_extensions = dict(
    #         base=dict(color=str, klayer=int),
    #         path=dict(thickness=float, material=str, perfectE=bool),
    #         poly=dict(thickness=float, material=str), )

    # Add columns to junction table during QGDSRenderer.load()
    # element_extensions  is now being populated as part of load().
    # Determined from element_table_data.

    # Dict structure MUST be same as  element_extensions!!!!!!
    # This dict will be used to update QDesign during init of renderer.
    # Keeping this as a cls dict so could be edited before renderer is instantiated.
    # To update component.options junction table.

    element_table_data = dict(
        # Example of adding a column named "skeleton_a_column_name"
        # with default values of "a_default_value" to the junction table.
        # Note: QSkeletonRenderer.name is prefixed to "a_column_name" when the table is appended by QComponents.
        junction=dict(a_column_name='a_default_value'))
    """element extensions dictionary   element_extensions = dict() from base class"""

    def __init__(self,
                 design: 'QDesign',
                 initiate=True,
                 render_template: Dict = None,
                 render_options: Dict = None):
        """Create a QRenderer for GDS interface: export and import.

        Args:
            design (QDesign): Use QGeometry within QDesign  to obtain elements.
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
            render_template (Dict, optional): Typically used by GUI for template options for GDS.  Defaults to None.
            render_options (Dict, optional):  Used to overide all options. Defaults to None.
        """

        super().__init__(design=design,
                         initiate=initiate,
                         render_template=render_template,
                         render_options=render_options)
        QSkeletonRenderer.load()

        # Updated each time write_qgeometry_table_names_to_file() is called.
        self.chip_info = dict()

    # For a skeleton_renderer user, this is kept to exemplify self.logger.warning.

    def _initiate_renderer(self):
        """Not used by the skeleton renderer at this time. only returns True.
        """
        return True

    def _close_renderer(self):
        """Not used by the skeleton renderer at this time. only returns True.
        """
        return True

    def render_design(self):
        """Export the design to Skeleton."""
        self.write_qgeometry_table_names_to_file(
            file_name=self.options.file_geometry_tables,
            highlight_qcomponents=[])

    def _can_write_to_path(self, file: str) -> int:
        """Check if can write file.

        Args:
            file (str): Has the path and/or just the file name.

        Returns:
            int: 1 if access is allowed. Else returns 0, if access not given.
        """
        status, directory_name = can_write_to_path(file)
        if status:
            return 1

        self.logger.warning(f'Not able to write to directory.'
                            f'File:"{file}" not written.'
                            f' Checked directory:"{directory_name}".')
        return 0

    def check_qcomps(self,
                     highlight_qcomponents: list = []) -> Tuple[list, int]:
        """Confirm the list doesn't have names of componentes repeated. Comfirm
        that the name of component exists in QDesign.

        Args:
            highlight_qcomponents (list, optional): List of strings which denote the name of QComponents to render.
                                                     Defaults to []. Empty list means to render entire design.

        Returns:
            Tuple[list, int]:
            list: Unique list of QComponents to render.
            int: 0 if all ended well. Otherwise, 1 if QComponent name not in design.
        """
        # Remove identical QComponent names.
        unique_qcomponents = list(set(highlight_qcomponents))

        # Confirm all QComponent are in design.
        for qcomp in unique_qcomponents:
            if qcomp not in self.design.name_to_id:
                self.logger.warning(
                    f'The component={qcomp} in highlight_qcomponents not'
                    ' in QDesign. The GDS data not generated.')
                return unique_qcomponents, 1

        # For Subtraction bounding box.
        # If list passed to export is the whole chip, then want to use the bounding box from design planar.
        # If list is subset of chip, then caluclate a custom bounding box and scale it.

        if len(unique_qcomponents) == len(self.design._components):
            # Since user wants all of the chip to be rendered, use the design.planar bounding box.
            unique_qcomponents[:] = []

        return unique_qcomponents, 0

    def get_qgeometry_tables_for_skeleton(self,
                                          highlight_qcomponents: list = []
                                         ) -> Tuple[int, list]:
        """Using self.design, this method does the following:

        1. Gather the QGeometries to be used to write to file.
           Duplicate names in hightlight_qcomponents will be removed without warning.

        Args:
            highlight_qcomponents (list): List of strings which denote the name of QComponents to render.
                                        If empty, render all comonents in design.
                                        If QComponent names are dupliated, duplicates will be ignored.

        Returns:
            Tuple[int, list]:
            int: 0 if all ended well. Otherwise, 1 if QComponent name(s) not in design.
            list: The names of QGeometry tables used for highlight_qcomponentes.
        """
        unique_qcomponents, status = self.check_qcomps(highlight_qcomponents)
        table_names_for_highlight = list()

        if status == 1:
            return 1, table_names_for_highlight
        for chip_name in self.chip_info:
            for table_name in self.design.qgeometry.get_element_types():
                # Get table for chip and table_name, and reduce to keep just the list of unique_qcomponents.
                table = self.get_table(table_name, unique_qcomponents,
                                       chip_name)

                # A place where a logic can happen, for each table, within a chip.

                # Demo for skeleton QRenderer.
                if len(table) != 0:
                    table_names_for_highlight.append(table_name + '\n')

        return 0, table_names_for_highlight

    def get_table(self, table_name: str, unique_qcomponents: list,
                  chip_name: str) -> geopandas.GeoDataFrame:
        """If unique_qcomponents list is empty, get table using table_name from
        QGeometry tables for all elements with table_name.  Otherwise, return a
        table with fewer elements, for just the qcomponents within the
        unique_qcomponents list.

        Args:
            table_name (str): Can be "path", "poly", etc. from the QGeometry tables.
            unique_qcomponents (list): User requested list of component names to export to GDS file.

        Returns:
            geopandas.GeoDataFrame: Table of elements within the QGeometry.
        """

        # self.design.qgeometry.tables is a dict. key=table_name, value=geopandas.GeoDataFrame
        if len(unique_qcomponents) == 0:
            table = self.design.qgeometry.tables[table_name]
        else:
            table = self.design.qgeometry.tables[table_name]
            # Convert string QComponent.name  to QComponent.id
            highlight_id = [
                self.design.name_to_id[a_qcomponent]
                for a_qcomponent in unique_qcomponents
            ]

            # Remove QComponents which are not requested.
            table = table[table['component'].isin(highlight_id)]

        table = table[table['chip'] == chip_name]

        return table

    def write_qgeometry_table_names_to_file(self,
                                            file_name: str,
                                            highlight_qcomponents: list = []
                                           ) -> int:
        """Obtain the names of the QGeometry Pandas tables and write them to a
        file. The names will be for qcomponents that were selected or all of
        the qcomponents within the qdesign.

        Args:
            file_name (str): File name which can also include directory path.
                             If the file exists, it will be overwritten.
            highlight_qcomponents (list): List of strings which denote the name of QComponents to render.
                                        If empty, render all qcomponents in qdesign.

        Returns:
            int: 0=file_name can not be written, otherwise 1=file_name has been written
        """

        if not self._can_write_to_path(file_name):
            return 0

        self.chip_info.clear()

        # Just for demo, a new plug-in may not need this.
        self.chip_info.update(self.get_chip_names())

        status, table_names_used = self.get_qgeometry_tables_for_skeleton(
            highlight_qcomponents)

        # The method parse_value, returns a float.
        total_bones = str(int(self.parse_value(self.options.number_of_bones)))

        total_bones_text = 'Number of bones:  ' + total_bones + '\n'

        if (status == 0):
            skeleton_out = open(file_name, 'w')
            skeleton_out.writelines(total_bones_text)
            skeleton_out.writelines(table_names_used)
            skeleton_out.close()
            return 1
        else:
            return 0

    def get_chip_names(self) -> Dict:
        """Returns a dict of unique chip names for ALL tables within QGeometry.
        In another words, for every "path" table, "poly" table ... etc, this
        method will search for unique chip names and return a dict of unique
        chip names from QGeometry table.

        Returns:
            Dict: dict with key of chip names and value of empty dict to hold things for renderers.
        """
        chip_names = Dict()
        for table_name in self.design.qgeometry.get_element_types():
            table = self.design.qgeometry.tables[table_name]
            names = table['chip'].unique().tolist()
            chip_names += names
        unique_list = list(set(chip_names))

        unique_dict = Dict()
        for chip in unique_list:
            unique_dict[chip] = Dict()
        return unique_dict
