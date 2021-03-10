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
from qiskit_metal.renderers.renderer_gds.make_cheese import Cheesing
from qiskit_metal.toolbox_metal.parsing import is_true
from qiskit_metal import draw

from .. import config
if not config.is_building_docs():
    from qiskit_metal.toolbox_python.utility_functions import can_write_to_path
    from qiskit_metal.toolbox_python.utility_functions import get_range_of_vertex_to_not_fillet

if TYPE_CHECKING:
    # For linting typechecking, import modules that can't be loaded here under normal conditions.
    # For example, I can't import QDesign, because it requires QRenderer first. We have the
    # chicken and egg issue.
    from qiskit_metal.designs import QDesign


class QGDSRenderer(QRenderer):
    """Extends QRenderer to export GDS formatted files. The methods which a user will need for GDS export
    should be found within this class.

    All chips within design should be exported to one gds file. For the "subtraction box":
    1. If user wants to export the entire design, AND if the base class of QDesign._chips[chip_name]['size']
    has dict following below example:
    {'center_x': 0.0, 'center_y': 0.0, 'size_x': 9, 'size_y': 6}
    then this box will be used for every layer within a chip.

    2. If user wants to export entire design, BUT there is not information in QDesign._chips[chip_name]['size'],
    then the renderer will calculate the size of all of the components
    and use that size for the "subtraction box" for every layer within a chip.

    3. If user wants to export a list of explicit components, the bounding box will be calculated by size of
    QComponents in the QGeometry table. Then be scaled by bounding_box_scale_x and bounding_box_scale_y.

    4. Note: When using the Junction table, the cell for Junction should be "x-axis" aligned and then GDS rotates
    based on LineString given in Junction table.


    datatype:
        * 10 Polygon
        * 11 Flexpath

    Default Options:
        * short_segments_to_not_fillet: 'True'
        * check_short_segments_by_scaling_fillet: '2.0'
        * gds_unit: '1'
        * ground_plane: 'True'
        * corners: 'circular bend'
        * tolerance: '0.00001'
        * precision: '0.000000001'
        * width_LineString: '10um'
        * path_filename: '../resources/Fake_Junctions.GDS'
        * junction_pad_overlap: '5um'
        * max_points: '199'
        * cheese: Dict
            * datatype: '100'
            * shape: '0'
            * cheese_0_x: '50um'
            * cheese_0_y: '50um'
            * cheese_1_radius: '100um'
            * delta_x='100um',
            * delta_y='100um',
            * edge_nocheese='10um',
            * view_in_file: Dict(main={1: True})
        * no_cheese: Dict
            * datatype: '99'
            * buffer: '25um'
            * cap_style: '2'
            * join_style: '2'
            * view_in_file: Dict(main={1: True})
        * bounding_box_scale_x: '1.2'
        * bounding_box_scale_y: '1.2'
    """

    #: Default options, over-written by passing ``options` dict to render_options.
    #: Type: Dict[str, str]
    default_options = Dict(

        # Before converting LINESTRING to FlexPath for GDS, check for fillet errors
        # for LINESTRINGS in QGeometry in QGeometry due to short segments.
        # If true, break up the LINESTRING so any segment which is shorter than the scaled-fillet
        # by "fillet_scale_factor" will be separated so the short segment will not be fillet'ed.
        short_segments_to_not_fillet='True',
        check_short_segments_by_scaling_fillet='2.0',

        # DO NOT MODIFY `gds_unit`. Gets overwritten by ``set_units``.
        # gdspy unit is 1 meter.  gds_units appear to ONLY be used during write_gds().
        # Note that gds_unit will be overwritten from the design units, during init().
        # WARNING: this cannot be changed. since it is only used during the init once.
        # TODO: Maybe hide form user and document use of this function: what is the effect?
        gds_unit='1',  # 1m

        # Implement creating a ground plane which is scaled from largest bounding box,
        # then QGeometry which is marked as subtract will be removed from ground_plane.
        # Then the balance of QGeometry will be placed placed in same layer as ground_plane.
        ground_plane='True',

        # corners ('natural', 'miter', 'bevel', 'round', 'smooth', 'circular bend', callable, list)
        # Type of joins. A callable must receive 6 arguments
        # (vertex and direction vector from both segments being joined, the center and width of the path)
        # and return a list of vertices that make the join.
        # A list can be used to define the join for each parallel path.
        corners='circular bend',

        # tolerance > precision
        # Precision used for gds lib, boolean operations and FlexPath should likely be kept the same.
        # They can be different, but increases odds of weird artifacts or misalignment.
        # Some of this occurs regardless (might be related to offset of a curve when done as a boolean vs. rendered),
        # but they are <<1nm, which isn't even picked up by any fab equipment (so can be ignored)
        # Numerical errors start to pop up if set precision too fine,
        # but 1nm seems to be the finest precision we use anyhow.
        # FOR NOW SPECIFY IN METERS. # TODO: Add parsing of actual units here
        tolerance='0.00001',  # 10.0 um

        # With input from fab people, any of the weird artifacts (like unwanted gaps)
        # that are less than 1nm in size can be ignored.
        # They don't even show up in the fabricated masks.
        # So, the precision of e-9 (so 1 nm) should be good as a default.
        # FOR NOW SPECIFY IN METERS. # TODO: Add parsing of actual units here
        precision='0.000000001',  # 1.0 nm

        # Since Qiskit Metal GUI, does not require a width for LineString, GDS, will provide a default value.
        width_LineString='10um',
        path_filename='../resources/Fake_Junctions.GDS',

        # For junction table, when cell from default_options.path_filename does not fit into linestring,
        # QGDSRender will create two pads and add to junction to fill the location of lineString.
        # The junction_pad_overlap is from the junction cell to the newly created pads.
        junction_pad_overlap='5um',

        # Vertex limit for FlexPath
        # max_points (integer) – If the number of points in the polygonal path boundary is greater than
        # max_points, it will be fractured in smaller polygons with at most max_points each. If max_points
        # is zero, no fracture will occur. GDSpy uses 199 as the default. The historical max value of vertices
        # for a poly/path was 199 (fabrication equipment restrictions).  The hard max limit that a GDSII file
        # can handle is 8191.
        max_points='199',

        # Cheesing is denoted by each chip and layer.
        cheese=Dict(
            #Cheesing is NOT completed
            datatype='100',

            # Expect to mostly cheese a square, but allow for expansion.
            # 0 is rectangle, 1 is circle
            shape='0',
            # rectangle
            cheese_0_x='25um',
            cheese_0_y='25um',
            # circle
            cheese_1_radius='100um',

            #identify which layers to view in gds output file, for each chip
            view_in_file=Dict(main={1: True}),

            #delta spacing between holes
            delta_x='100um',
            delta_y='100um',

            #Keep a buffer around the perimeter of chip, that will not need cheesing.
            edge_nocheese='10um'),

        # Think of this as a keep-out region for cheesing.
        no_cheese=Dict(
            # For every layer, if there is a ground plane, do cheesing and
            # place the output on the datatype number (sub-layer number)
            datatype='99',
            buffer='25um',

            #The styles of caps are specified by integer values:
            # 1 (round), 2 (flat), 3 (square).
            cap_style='2',

            #The styles of joins between offset segments are specified by integer values:
            # 1 (round), 2 (mitre), and 3 (bevel).
            join_style='2',

            #identify which layers to view in gds output file, for each chip
            view_in_file=Dict(main={1: True}),
        ),

        # (float): Scale box of components to render. Should be greater than 1.0.
        # For benifit of the GUI, keep this the last entry in the dict.  GUI shows a note regarding bound_box.
        bounding_box_scale_x='1.2',
        bounding_box_scale_y='1.2',
    )
    """Default options"""

    name = 'gds'
    """name"""

    # When additional columns are added to QGeometry, this is the example to populate it.
    # e.g. element_extensions = dict(
    #         base=dict(color=str, klayer=int),
    #         path=dict(thickness=float, material=str, perfectE=bool),
    #         poly=dict(thickness=float, material=str), )
    """element extensions dictionary   element_extensions = dict() from base class"""

    # Add columns to junction table during QGDSRenderer.load()
    # element_extensions  is now being populated as part of load().
    # Determined from element_table_data.

    # Dict structure MUST be same as  element_extensions!!!!!!
    # This dict will be used to update QDesign during init of renderer.
    # Keeping this as a cls dict so could be edited before renderer is instantiated.
    # To update component.options junction table.

    element_table_data = dict(
        # Cell_name must exist in gds file with: path_filename
        junction=dict(cell_name='my_other_junction'))

    def __init__(self,
                 design: 'QDesign',
                 initiate=True,
                 render_template: Dict = None,
                 render_options: Dict = None):
        """Create a QRenderer for GDS interface: export and import.

        Args:
            design (QDesign): Use QGeometry within QDesign  to obtain elements for GDS file.
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
            render_template (Dict, optional): Typically used by GUI for template options for GDS.  Defaults to None.
            render_options (Dict, optional):  Used to overide all options. Defaults to None.
        """

        super().__init__(design=design,
                         initiate=initiate,
                         render_template=render_template,
                         render_options=render_options)

        self.lib = None  # type: gdspy.GdsLibrary
        self.new_gds_library()

        self.dict_bounds = Dict()

        # Updated each time export_to_gds() is called.
        self.chip_info = dict()

        # check the scale
        self.check_bounding_box_scale()

        QGDSRenderer.load()

    def check_bounding_box_scale(self):
        """
        Some error checking for bounding_box_scale_x and bounding_box_scale_y numbers.
        """
        p = self.options
        bounding_box_scale_x = self.parse_value(p.bounding_box_scale_x)
        bounding_box_scale_y = self.parse_value(p.bounding_box_scale_y)

        if bounding_box_scale_x < 1:
            self.options[
                'bounding_box_scale_x'] = QGDSRenderer.default_options.bounding_box_scale_x
            self.logger.warning(
                'Expected float and number greater than or equal to'
                ' 1.0 for bounding_box_scale_x. User'
                f'provided bounding_box_scale_x = {bounding_box_scale_x}'
                ', using default_options.bounding_box_scale_x.')

        if bounding_box_scale_y < 1:
            self.options[
                'bounding_box_scale_y'] = QGDSRenderer.default_options.bounding_box_scale_y
            self.logger.warning(
                f'Expected float and number greater than or equal to 1.0 for bounding_box_scale_y.'
                'User provided bounding_box_scale_y = {bounding_box_scale_y}, '
                'using default_options.bounding_box_scale_y.')

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
        status, directory_name = can_write_to_path(file)
        if status:
            return 1

        self.logger.warning(f'Not able to write to directory.'
                            f'File:"{file}" not written.'
                            f' Checked directory:"{directory_name}".')
        return 0

    def update_units(self):
        """Update the options in the units.
        Warning: DOES NOT CHANGE THE CURRENT LIB
        """
        self.options['gds_unit'] = 1.0 / self.design.parse_value('1 meter')

    def separate_subtract_shapes(self, chip_name: str, table_name: str,
                                 table: geopandas.GeoSeries) -> None:
        """For each chip and table, separate them by subtract being either True or False.
           Names of chip and table should be same as the QGeometry tables.

        Args:
            chip_name (str): Name of "chip".  Example is "main".
            table_name (str): Name for "table".  Example is "poly", and "path".
            table (geopandas.GeoSeries): Table with similar qgeometries.
        """

        subtract_true = table[table['subtract'] == True]

        subtract_false = table[table['subtract'] == False]

        setattr(self, f'{chip_name}_{table_name}_subtract_true', subtract_true)
        setattr(self, f'{chip_name}_{table_name}_subtract_false',
                subtract_false)

    @staticmethod
    def get_bounds(
            gs_table: geopandas.GeoSeries) -> Tuple[float, float, float, float]:
        """Get the bounds for all of the elements in gs_table.

        Args:
            gs_table (pandas.GeoSeries): A pandas GeoSeries used to describe components in a design.

        Returns:
            Tuple[float, float, float, float]: The bounds of all of the elements in this table. [minx, miny, maxx, maxy]
        """
        if len(gs_table) == 0:
            return (0, 0, 0, 0)

        return gs_table.total_bounds

    @staticmethod
    def inclusive_bound(all_bounds: list) -> tuple:
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

    @staticmethod
    def midpoint_xy(x1: float, y1: float, x2: float,
                    y2: float) -> Tuple[float, float]:
        """Calculate the center of a line segment with endpoints (x1,y1) and (x2,y2).

        Args:
            x1 (float): x of endpoint (x1,y1)
            y1 (float): y of endpoint (x1,y1)
            x2 (float): x of endpoint (x2,y2)
            y2 (float): y of endpoint (x2,y2)

        Returns:
            Tuple[float, float]:
            1st float: x for midpoint
            2nd float: y for midpoint
        """
        midx = (x1 + x2) / 2
        midy = (y1 + y2) / 2

        return midx, midy

    def scale_max_bounds(self, chip_name: str,
                         all_bounds: list) -> Tuple[tuple, tuple]:
        """Given the list of tuples to represent all of the bounds for path, poly, etc.
        This will return the scaled using self.bounding_box_scale_x and self.bounding_box_scale_y,
        and the max bounds of the tuples provided.

        Args:
            chip_name (str): Name of chip.
            all_bounds (list): Each tuple=(minx, miny, maxx, maxy) in list represents bounding box for poly, path, etc.

        Returns:
            tuple[tuple, tuple]:
            first tuple: A scaled bounding box which includes all paths, polys, etc.;
            second tuple: A  bounding box which includes all paths, polys, etc.
        """
        # If given an empty list.
        if len(all_bounds) == 0:
            return (0.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0)

        # Get an inclusive bounding box to contain all of the tuples provided.
        minx, miny, maxx, maxy = self.inclusive_bound(all_bounds)

        # Center of inclusive bounding box
        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2

        scaled_width = (maxx - minx) * \
            self.parse_value(self.options.bounding_box_scale_x)
        scaled_height = (maxy - miny) * \
            self.parse_value(self.options.bounding_box_scale_y)

        # Scaled inclusive bounding box by self.options.bounding_box_scale_x and self.options.bounding_box_scale_y.
        scaled_box = (center_x - (.5 * scaled_width),
                      center_y - (.5 * scaled_height),
                      center_x + (.5 * scaled_width),
                      center_y + (.5 * scaled_height))

        self.dict_bounds[chip_name]['scaled_box'] = scaled_box
        self.dict_bounds[chip_name]['inclusive_box'] = (minx, miny, maxx, maxy)

        return scaled_box, (minx, miny, maxx, maxy)

    def check_qcomps(self,
                     highlight_qcomponents: list = []) -> Tuple[list, int]:
        """Confirm the list doesn't have names of componentes repeated.
        Comfirm that the name of component exists in QDesign.

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

    def create_qgeometry_for_gds(self, highlight_qcomponents: list = []) -> int:
        """Using self.design, this method does the following:

        1. Gather the QGeometries to be used to write to file.
           Duplicate names in hightlight_qcomponents will be removed without warning.

        2. Populate self.dict_bounds, for each chip, contains the maximum bound for all elements to render.

        3. Calculate scaled bounding box to emulate size of chip using self.bounding_box_scale(x and y)
           and place into self.dict_bounds[chip_name]['for_subtract'].

        4. Gather Geometries to export to GDS format.

        Args:
            highlight_qcomponents (list): List of strings which denote the name of QComponents to render.
                                        If empty, render all comonents in design.
                                        If QComponent names are dupliated, duplicates will be ignored.

        Returns:
            int: 0 if all ended well. Otherwise, 1 if QComponent name(s) not in design.
        """
        unique_qcomponents, status = self.check_qcomps(highlight_qcomponents)
        if status == 1:
            return 1
        self.dict_bounds.clear()

        for chip_name in self.chip_info:
            # put the QGeometry into GDS format.
            # There can be more than one chip in QGeometry.  They all export to one gds file.
            self.chip_info[chip_name]['all_subtract'] = []
            self.chip_info[chip_name]['all_no_subtract'] = []

            self.dict_bounds[chip_name] = Dict()
            self.dict_bounds[chip_name]['gather'] = []
            self.dict_bounds[chip_name]['for_subtract'] = tuple()
            all_table_subtracts = []
            all_table_no_subtracts = []

            for table_name in self.design.qgeometry.get_element_types():

                # Get table for chip and table_name, and reduce to keep just the list of unique_qcomponents.
                table = self.get_table(table_name, unique_qcomponents,
                                       chip_name)

                if table_name == 'junction':
                    self.chip_info[chip_name]['junction'] = deepcopy(table)
                else:
                    # For every chip, and layer, separate the "subtract" and "no_subtract" elements and gather bounds.
                    # dict_bounds[chip_name] = list_bounds
                    self.gather_subtract_elements_and_bounds(
                        chip_name, table_name, table, all_table_subtracts,
                        all_table_no_subtracts)

            # If list of QComponents provided, use the bounding_box_scale(x and y),
            # otherwise use self._chips
            scaled_max_bound, max_bound = self.scale_max_bounds(
                chip_name, self.dict_bounds[chip_name]['gather'])
            if highlight_qcomponents:
                self.dict_bounds[chip_name]['for_subtract'] = scaled_max_bound
            else:
                chip_box, status = self.design.get_x_y_for_chip(chip_name)
                if status == 0:
                    self.dict_bounds[chip_name]['for_subtract'] = chip_box
                else:
                    self.dict_bounds[chip_name]['for_subtract'] = max_bound
                    self.logger.warning(
                        f'design.get_x_y_for_chip() did NOT return a good code for chip={chip_name},'
                        f'for ground subtraction-box using the size calculated from QGeometry, ({max_bound}) will be used. '
                    )
            if is_true(self.options.ground_plane):
                self.handle_ground_plane(chip_name, all_table_subtracts,
                                         all_table_no_subtracts)

        return 0

    def handle_ground_plane(self, chip_name: str, all_table_subtracts: list,
                            all_table_no_subtracts: list):
        """Place all the subtract geometries for one chip into self.chip_info[chip_name]['all_subtract_true']

        For LINESTRING within table that has a value for fillet, check if any segment is shorter than fillet radius.
        If so, then break the LINESTRING so that shorter segments do not get fillet'ed and longer segments get fillet'ed.
        Add the mulitiple LINESTRINGS back to table.
        Also remove "bad" LINESTRING from table.

        Then use qgeometry_to_gds() to convert the QGeometry elements to gdspy elements.  The gdspy elements
        are placed in self.chip_info[chip_name]['q_subtract_true'].

        Args:
            chip_name (str): Chip_name that is being processed.
            all_table_subtracts (list): Add to self.chip_info by layer number.
            all_table_no_subtracts (list): Add to self.chip_info by layer number.
        """

        fix_short_segments = self.parse_value(
            self.options.short_segments_to_not_fillet)
        all_layers = self.design.qgeometry.get_all_unique_layers(chip_name)

        for chip_layer in all_layers:
            copy_subtract = []
            copy_no_subtract = []
            copy_subtract = deepcopy(all_table_subtracts)
            copy_no_subtract = deepcopy(all_table_no_subtracts)

            for item in copy_subtract:
                item.drop(item.index[item['layer'] != chip_layer], inplace=True)

            for item_no in copy_no_subtract:
                item_no.drop(item_no.index[item_no['layer'] != chip_layer],
                             inplace=True)

            self.chip_info[chip_name][chip_layer][
                'all_subtract_true'] = geopandas.GeoDataFrame(
                    pd.concat(copy_subtract, ignore_index=False))

            self.chip_info[chip_name][chip_layer][
                'all_subtract_false'] = geopandas.GeoDataFrame(
                    pd.concat(copy_no_subtract, ignore_index=False))

            self.chip_info[chip_name][chip_layer][
                'all_subtract_true'].reset_index(inplace=True)
            self.chip_info[chip_name][chip_layer][
                'all_subtract_false'].reset_index(inplace=True)

            if is_true(fix_short_segments):
                self.fix_short_segments_within_table(chip_name, chip_layer,
                                                     'all_subtract_true')
                self.fix_short_segments_within_table(chip_name, chip_layer,
                                                     'all_subtract_false')

            self.chip_info[chip_name][chip_layer][
                'q_subtract_true'] = self.chip_info[chip_name][chip_layer][
                    'all_subtract_true'].apply(self.qgeometry_to_gds, axis=1)

            self.chip_info[chip_name][chip_layer][
                'q_subtract_false'] = self.chip_info[chip_name][chip_layer][
                    'all_subtract_false'].apply(self.qgeometry_to_gds, axis=1)

    # Handling Fillet issues.

    def fix_short_segments_within_table(self, chip_name: str, chip_layer: int,
                                        all_sub_true_or_false: str):
        """Update self.chip_info geopandas.GeoDataFrame.

        Will iterate through the rows to examine the LineString.
        Then determine if there is a segment that is shorter than the critera based on default_options.
        If so, then remove the row, and append shorter LineString with no fillet, within the dataframe.

        Args:
            chip_name (str): The name of chip.
            chip_layer (int): The layer within the chip to be evaluated.
            all_sub_true_or_false (str): To be used within self.chip_info: 'all_subtract_true' or 'all_subtract_false'.
        """
        df = self.chip_info[chip_name][chip_layer][all_sub_true_or_false]
        df_fillet = df[-df['fillet'].isnull()]

        if not df_fillet.empty:
            # Don't edit the table when iterating through the rows.
            # Save info in dict and then edit the table.
            edit_index = dict()
            for index, row in df_fillet.iterrows():
                # print(
                #     f'With parse_value: {self.parse_value(row.fillet)}, row.fille: {row.fillet}')
                status, all_shapelys = self.check_length(
                    row.geometry, row.fillet)
                if status > 0:
                    edit_index[index] = all_shapelys

            df_copy = self.chip_info[chip_name][chip_layer][
                all_sub_true_or_false].copy(deep=True)
            for del_key, the_shapes in edit_index.items():
                # copy row "index" into a new df "status" times.  Then replace the LONG shapely with all_shapleys
                # For any entries in edit_index, edit table here.
                orig_row = df_copy.loc[del_key].copy(deep=True)
                df_copy = df_copy.drop(index=del_key)

                for new_row, short_shape in the_shapes.items():
                    orig_row['geometry'] = short_shape['line']
                    orig_row['fillet'] = short_shape['fillet']
                    # Keep ignore_index=False, otherwise, the other del_key will not be found.
                    df_copy = df_copy.append(orig_row, ignore_index=False)

            self.chip_info[chip_name][chip_layer][
                all_sub_true_or_false] = df_copy.copy(deep=True)

    def check_length(self, a_shapely: shapely.geometry.LineString,
                     a_fillet: float) -> Tuple[int, Dict]:
        """Determine if a_shapely has short segments based on scaled fillet value.

        Use check_short_segments_by_scaling_fillet to determine the critera for flagging a segment.
        Return Tuple with flagged segments.

        The "status" returned in int:
            * -1: Method needs to update the return code.
            * 0: No issues, no short segments found
            * int: The number of shapelys returned. New shapeleys, should replace the ones provided in a_shapley

        The "shorter_lines" returned in dict:
        key: Using the index values from list(a_shapely.coords)
        value: dict() for each new, shorter, LineString

        The dict()
        key: fillet, value: can be float from before, or undefined to denote no fillet.
        key: line, value: shorter LineString

        Args:
            a_shapely (shapely.geometry.LineString): A shapley object that needs to be evaluated.
            a_fillet (float): From component developer.

        Returns:
            Tuple[int, Dict]:
            int: Number of short segments that should not have fillet.
            Dict: Key: index into a_shapely, Value: dict with fillet and shorter LineString
        """
        # Holds all of the index of when a segment is too short.
        idx_bad_fillet = list()
        status = -1  # Initalize to meaningless value.
        coords = list(a_shapely.coords)
        len_coords = len(coords)

        all_idx_bad_fillet = dict()

        self.identify_vertex_not_to_fillet(coords, a_fillet, all_idx_bad_fillet)

        shorter_lines = dict()

        idx_bad_fillet = sorted(all_idx_bad_fillet['reduced_idx'])
        status = len(idx_bad_fillet)

        if status:
            midpoints = all_idx_bad_fillet['midpoints']
            no_fillet_vertices = list()
            fillet_vertices = list()

            # Gather the no-fillet segments
            for idx, (start, stop) in enumerate(idx_bad_fillet):
                no_fillet_vertices.clear()
                if idx == 0 and start == 0:
                    # The first segment.
                    if stop == len_coords - 1:
                        # Every vertex should not be fillet'd
                        no_fillet_vertices = coords[start:len_coords]
                        shorter_lines[stop] = dict({
                            'line': LineString(no_fillet_vertices),
                            'fillet': float('NaN')
                        })
                    else:
                        no_fillet_vertices = coords[start:stop + 1]
                        no_fillet_vertices.append(midpoints[stop])
                        shorter_lines[stop] = dict({
                            'line': LineString(no_fillet_vertices),
                            'fillet': float('NaN')
                        })
                elif idx == status - 1 and stop == len_coords - 1:
                    # The last segment
                    no_fillet_vertices = coords[start:stop + 1]
                    no_fillet_vertices.insert(0, midpoints[start - 1])
                    shorter_lines[stop] = dict({
                        'line': LineString(no_fillet_vertices),
                        'fillet': float('NaN')
                    })
                else:
                    # Segment in between first and last segment.
                    no_fillet_vertices = coords[start:stop + 1]
                    no_fillet_vertices.insert(0, midpoints[start - 1])
                    no_fillet_vertices.append(midpoints[stop])
                    shorter_lines[stop] = dict({
                        'line': LineString(no_fillet_vertices),
                        'fillet': float('NaN')
                    })
            # Gather the fillet segments.
            at_vertex = 0
            for idx, (start, stop) in enumerate(idx_bad_fillet):
                fillet_vertices.clear()
                if idx == 0 and start == 0:
                    pass  # just update at_vertex
                if idx == 0 and start == 1:
                    init_tuple = coords[0]
                    fillet_vertices = [init_tuple, midpoints[start - 1]]
                    shorter_lines[start] = dict({
                        'line': LineString(fillet_vertices),
                        'fillet': a_fillet
                    })
                if idx == 0 and start > 1:
                    fillet_vertices = coords[0:start]
                    fillet_vertices.append(midpoints[start - 1])
                    shorter_lines[start] = dict({
                        'line': LineString(fillet_vertices),
                        'fillet': a_fillet
                    })
                    if idx == status - 1 and stop != len_coords - 1:
                        # Extra segment after the last no-fillet.
                        fillet_vertices.clear()
                        fillet_vertices = coords[stop + 1:len_coords]
                        fillet_vertices.insert(0, midpoints[stop])
                        shorter_lines[len_coords] = dict({
                            'line': LineString(fillet_vertices),
                            'fillet': a_fillet
                        })
                elif idx == status - 1 and start == 0 and stop != len_coords - 1:
                    # At last tuple, and and start at first index, and  the stop is not last index of coords.
                    fillet_vertices = coords[stop + 1:len_coords]
                    fillet_vertices.insert(0, midpoints[stop])
                    shorter_lines[start] = dict({
                        'line': LineString(fillet_vertices),
                        'fillet': a_fillet
                    })
                elif idx == status - 1 and stop != len_coords - 1:
                    # At last tuple, and the stop is not last index of coords.
                    fillet_vertices = coords[at_vertex + 1:start]
                    fillet_vertices.insert(0, midpoints[at_vertex])
                    fillet_vertices.append(midpoints[start - 1])
                    shorter_lines[start] = dict({
                        'line': LineString(fillet_vertices),
                        'fillet': a_fillet
                    })
                    # Extra segment after the last no-fillet.
                    fillet_vertices.clear()
                    fillet_vertices = coords[stop + 1:len_coords]
                    fillet_vertices.insert(0, midpoints[stop])
                    shorter_lines[len_coords] = dict({
                        'line': LineString(fillet_vertices),
                        'fillet': a_fillet
                    })
                else:
                    if (start - at_vertex) > 1:
                        fillet_vertices = coords[at_vertex + 1:start]
                        fillet_vertices.insert(0, midpoints[at_vertex])
                        fillet_vertices.append(midpoints[start - 1])
                        shorter_lines[start] = dict({
                            'line': LineString(fillet_vertices),
                            'fillet': a_fillet
                        })
                at_vertex = stop  # Need to update for every loop.
        else:
            # No short segments.
            shorter_lines[len_coords - 1] = a_shapely
        return status, shorter_lines

    def identify_vertex_not_to_fillet(self, coords: list, a_fillet: float,
                                      all_idx_bad_fillet: dict):
        """Use coords to denote segments that are too short.  In particular,
        when fillet'd, they will cause the appearance of incorrect fillet when graphed.

        Args:
            coords (list): User provide a list of tuples.  The tuple is (x,y) location for a vertex.
              The list represents a LineString.
            a_fillet (float): The value provided by component developer.
            all_idx_bad_fillet (dict): An empty dict which will be populated by this method.

        Dictionary:
            Key 'reduced_idx' will hold list of tuples.  The tuples correspond to index for list named "coords".
            Key 'midpoints' will hold list of tuples. The index of a tuple corresponds to two index within coords.
            For example, a index in midpoints is x, that coresponds midpoint of segment x-1 to x.
        """

        # Depreciated since there is no longer a scale factor  given to QCheckLength.
        # fillet_scale_factor = self.parse_value(
        #     self.options.check_short_segments_by_scaling_fillet)

        precision = float(self.parse_value(self.options.precision))

        # For now, DO NOT allow the user of GDS to provide the precision.
        # user_precision = int(np.abs(np.log10(precision)))

        qdesign_precision = self.design.template_options.PRECISION

        all_idx_bad_fillet['reduced_idx'] = get_range_of_vertex_to_not_fillet(
            coords, a_fillet, qdesign_precision, add_endpoints=True)

        midpoints = list()
        midpoints = [
            QGDSRenderer.midpoint_xy(coords[idx - 1][0], coords[idx - 1][1],
                                     vertex2[0], vertex2[1])
            for idx, vertex2 in enumerate(coords)
            if idx > 0
        ]
        all_idx_bad_fillet['midpoints'] = midpoints

    # Move data around to be useful for GDS

    def gather_subtract_elements_and_bounds(self, chip_name: str,
                                            table_name: str,
                                            table: geopandas.GeoDataFrame,
                                            all_subtracts: list,
                                            all_no_subtracts: list):
        """For every chip, and layer, separate the "subtract" and "no_subtract" elements
        and gather bounds for all the elements in qgeometries..
        Use format: f'{chip_name}_{table_name}s'

        Args:
            chip_name (str): Name of chip.  Example is 'main'.
            table_name (str): There are multiple tables in QGeometry table.  Example: 'path' and 'poly'.
            table (geopandas.GeoDataFrame): Actual table for the name.
            all_subtracts (list): Pass by reference so method can update this list.
            all_no_subtracts (list): Pass by reference so method can update this list.

        """

        # Determine bound box and return scalar larger than size.
        bounds = tuple(self.get_bounds(table))

        # Add the bounds of each table to list.
        self.dict_bounds[chip_name]['gather'].append(bounds)

        if is_true(self.options.ground_plane):
            self.separate_subtract_shapes(chip_name, table_name, table)

            all_subtracts.append(
                getattr(self, f'{chip_name}_{table_name}_subtract_true'))
            all_no_subtracts.append(
                getattr(self, f'{chip_name}_{table_name}_subtract_false'))

        # Done because ground plane option may be false.
        # This is not used anywhere currently.
        # Keep this depreciated code.
        # polys use gdspy.Polygon;    paths use gdspy.LineString
        '''
        q_geometries = table.apply(self.qgeometry_to_gds, axis=1)
        setattr(self, f'{chip_name}_{table_name}s', q_geometries)
        '''

    def get_table(self, table_name: str, unique_qcomponents: list,
                  chip_name: str) -> geopandas.GeoDataFrame:
        """If unique_qcomponents list is empty, get table using table_name from QGeometry tables
            for all elements with table_name.  Otherwise, return a table with fewer elements, for just the
            qcomponents within the unique_qcomponents list.

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

    # To export the data.

    def new_gds_library(self) -> gdspy.GdsLibrary:
        """Creates a new GDS Library. Deletes the old.
           Create a new GDS library file. It can contains multiple cells.

           Returns:
            gdspy.GdsLibrary: GDS library which can contain multiple celles.
        """

        self.update_units()

        if self.lib:
            self._clear_library()

        # Create a new GDS library file. It can contains multiple cells.
        self.lib = gdspy.GdsLibrary(
            unit=float(self.parse_value(self.options.gds_unit)))

        return self.lib

    def check_cheese(self, chip: str, layer: int) -> int:
        """Examine the option for cheese_view_in_file.

        Args:
            chip (str): User defined chip name.
            layer (int): Layer used in chip.

        Returns:
            int: Oberservation of option based on chip and layer information.

            * 0 This is the initialization state.
            * 1 The layer is in the chip and cheese is True.
            * 2 The layer is in the chip and cheese is False.
            * 3 The chip is not in dict, so can't give answer.
            * 4 The layer is not in the chip, so can't give answer.
        """
        code = 0

        cheese_option = self.parse_value(self.options.cheese.view_in_file)

        if chip in cheese_option:
            if layer in cheese_option[chip]:
                if is_true(cheese_option[chip][layer]):
                    code = 1
                else:
                    code = 2
            else:
                code = 4
        else:
            code = 3

        return code

    def check_no_cheese(self, chip: str, layer: int) -> int:
        """Examine the option for no_cheese_view_in_file.

        Args:
            chip (str): User defined chip name.
            layer (int): Layer used in chip.

        Returns:
            int: Oberservation of option based on chip and layer information.

            * 0 This is the initialization state.
            * 1 The layer is in the chip and viewing no-cheese is True.
            * 2 The layer is in the chip and viewing no-cheese is False.
            * 3 The chip is not in dict, so can't give answer.
            * 4 The layer is not in the chip, so can't give answer.
        """

        code = 0

        no_cheese_option = self.parse_value(self.options.no_cheese.view_in_file)

        if chip in no_cheese_option:
            if layer in no_cheese_option[chip]:
                if is_true(no_cheese_option[chip][layer]):
                    code = 1
                else:
                    code = 2
            else:
                code = 4
        else:
            code = 3

        return code

    def check_either_cheese(self, chip: str, layer: int) -> int:
        """Use methods to check two options and give review of values 
        for no_cheese_view_in_file and cheese_view_in_file.

        Args:
            chip (str): User defined chip name.
            layer (int): Layer used in chip.

        Returns:
            int: Oberservation of options based on chip and layer information.

            * 0 This is the initialization state.
            * 1 Show the layer in both cheese and no cheese
            * 2 Show the layer in just the cheese
            * 3 Show the no-cheese, but not the cheese
            * 4 Do NOT show the layer in neither cheese
            * 5 The chip is not in the default option.
            * 6 The layer is not in the chip dict.
        """
        code = 0
        no_cheese_code = self.check_no_cheese(chip, layer)
        cheese_code = self.check_cheese(chip, layer)

        if no_cheese_code == 0 or cheese_code == 0:
            self.logger.warning(
                f'Not able to get no_cheese_view_in_file or cheese_view_in_file from self.options.'
            )
            code = 0
            return code
        if no_cheese_code == 1 and cheese_code == 1:
            code = 1
            return code
        if no_cheese_code == 2 and cheese_code == 1:
            code = 2
            return code
        if no_cheese_code == 1 and cheese_code == 2:
            code = 3
            return code
        if no_cheese_code == 2 and cheese_code == 2:
            code = 4
            return code
        if no_cheese_code == 3 or cheese_code == 3:
            code = 5
            self.logger.warning(
                f'Chip={chip} is not either in no_cheese_view_in_file or cheese_view_in_file from self.options.'
            )
            return code
        if no_cheese_code == 4 or cheese_code == 4:
            code = 6
            self.logger.warning(
                f'layer={layer} is not in chip={chip} either in no_cheese_view_in_file or cheese_view_in_file from self.options.'
            )
            return code

        return code

    def populate_cheese(self):
        """ Iterate through each chip, then layer to determine the cheesing geometry.
        """

        lib = self.lib
        cheese_sub_layer = int(self.parse_value(self.options.cheese.datatype))
        nocheese_sub_layer = int(
            self.parse_value(self.options.no_cheese.datatype))

        for chip_name in self.chip_info:
            layers_in_chip = self.design.qgeometry.get_all_unique_layers(
                chip_name)

            for chip_layer in layers_in_chip:
                code = self.check_cheese(chip_name, chip_layer)
                if code == 1:
                    chip_box, status = self.design.get_x_y_for_chip(chip_name)
                    if status == 0:
                        minx, miny, maxx, maxy = chip_box

                        cheesed = self.cheese_based_on_shape(
                            minx, miny, maxx, maxy, chip_name, chip_layer,
                            cheese_sub_layer, nocheese_sub_layer)

    def cheese_based_on_shape(self, minx: float, miny: float, maxx: float,
                              maxy: float, chip_name: str, chip_layer: int,
                              cheese_sub_layer: int, nocheese_sub_layer: int):
        """Instantiate class to do cheesing.
        Args:
            minx (float): Chip minimum x location.
            miny (float): Chip minimum y location.
            maxx (float): Chip maximum x location.
            maxy (float): chip maximum y location.
            chip_name (str): User defined chip name.
            layer (int): Layer number for calculating the cheese.
            cheese_sub_layer (int):  User defined datatype, considered a sub-layer number for where to place the cheese output.
            nocheese_sub_layer (int): User defined datatype, considered a sub-layer number for where to place the NO_cheese output.
        """

        max_points = int(self.parse_value(self.options.max_points))
        cheese_shape = int(self.parse_value(self.options.cheese.shape))
        all_nocheese = self.chip_info[chip_name][chip_layer]['no_cheese']
        all_nocheese_gds = self.chip_info[chip_name][chip_layer][
            'no_cheese_gds']
        delta_x = float(self.parse_value(self.options.cheese.delta_x))
        delta_y = float(self.parse_value(self.options.cheese.delta_y))
        edge_nocheese = float(
            self.parse_value(self.options.cheese.edge_nocheese))
        precision = float(self.parse_value(self.options.precision))

        if cheese_shape == 0:
            cheese_x = float(self.parse_value(self.options.cheese.cheese_0_x))
            cheese_y = float(self.parse_value(self.options.cheese.cheese_0_y))
            a_cheese = Cheesing(all_nocheese,
                                all_nocheese_gds,
                                self.lib,
                                minx,
                                miny,
                                maxx,
                                maxy,
                                chip_name,
                                edge_nocheese,
                                chip_layer,
                                cheese_sub_layer,
                                nocheese_sub_layer,
                                self.logger,
                                max_points,
                                precision,
                                cheese_shape=cheese_shape,
                                shape_0_x=cheese_x,
                                shape_0_y=cheese_y,
                                delta_x=delta_x,
                                delta_y=delta_y)
        elif cheese_shape == 1:
            cheese_radius = float(
                self.parse_value(self.options.cheese.cheese_1_radius))
            a_cheese = Cheesing(all_nocheese,
                                all_nocheese_gds,
                                self.lib,
                                minx,
                                miny,
                                maxx,
                                maxy,
                                chip_name,
                                edge_nocheese,
                                chip_layer,
                                cheese_sub_layer,
                                nocheese_sub_layer,
                                self.logger,
                                max_points,
                                precision,
                                cheese_shape=cheese_shape,
                                shape_1_radius=cheese_radius,
                                delta_x=delta_x,
                                delta_y=delta_y)
        else:
            self.logger.warning(
                f'The cheese_shape={cheese_shape} is unknown in QGDSRenderer.')
            a_cheese = None

        if a_cheese is not None:
            a_lib = a_cheese.apply_cheesing()

        return

    def populate_no_cheese(self):
        """Iterate through every chip and layer.  If options choose to have either cheese or no-cheese,
        a MultiPolygon is placed self.chip_info[chip_name][chip_layer]['no_cheese'].  

        If user selects to view the no-cheese, the method placed the cell with no-cheese
        at f'NoCheese_{chip_name}_{chip_layer}_{sub_layer}'.  The sub_layer is data_type and denoted
        in the options. 
        """
        no_cheese_buffer = float(self.parse_value(
            self.options.no_cheese.buffer))
        sub_layer = int(self.parse_value(self.options.no_cheese.datatype))
        lib = self.lib

        for chip_name in self.chip_info:
            layers_in_chip = self.design.qgeometry.get_all_unique_layers(
                chip_name)

            for chip_layer in layers_in_chip:
                code = self.check_either_cheese(chip_name, chip_layer)

                if code == 1 or code == 2 or code == 3:
                    if len(self.chip_info[chip_name][chip_layer]
                           ['all_subtract_true']) != 0:

                        sub_df = self.chip_info[chip_name][chip_layer][
                            'all_subtract_true']
                        no_cheese_multipolygon = self.cheese_buffer_maker(
                            sub_df, chip_name, no_cheese_buffer)

                        if no_cheese_multipolygon is not None:
                            self.chip_info[chip_name][chip_layer][
                                'no_cheese'] = no_cheese_multipolygon
                            sub_layer = int(
                                self.parse_value(
                                    self.options.no_cheese.datatype))
                            all_nocheese_gds = self.multipolygon_to_gds(
                                no_cheese_multipolygon, chip_layer, sub_layer,
                                no_cheese_buffer)
                            self.chip_info[chip_name][chip_layer][
                                'no_cheese_gds'] = all_nocheese_gds

                            if self.check_no_cheese(chip_name, chip_layer) == 1:
                                no_cheese_subtract_cell_name = f'TOP_{chip_name}_{chip_layer}_NoCheese_{sub_layer}'
                                no_cheese_cell = lib.new_cell(
                                    no_cheese_subtract_cell_name,
                                    overwrite_duplicate=True)

                                no_cheese_cell.add(all_nocheese_gds)

                                # chip_only_top_layer_name = f'TOP_{chip_name}_{chip_layer}'
                                chip_only_top_layer_name = f'TOP_{chip_name}'

                                if no_cheese_cell.get_bounding_box(
                                ) is not None:
                                    lib.cells[chip_only_top_layer_name].add(
                                        gdspy.CellReference(no_cheese_cell))
                                else:
                                    lib.remove(no_cheese_cell)
        return

    def cheese_buffer_maker(
        self, sub_df: geopandas.GeoDataFrame, chip_name: str,
        no_cheese_buffer: float
    ) -> Union[None, shapely.geometry.multipolygon.MultiPolygon]:
        """For each layer in each chip, and if it has a ground plane (subtract==True), 
        determine the no-cheese buffer and return a shapely object. Before the buffer is
        created for no-cheese, the LineStrings and Polygons are all combined. 

        Args:
            sub_df (geopandas.GeoDataFrame): The subset of QGeometry tables for each chip, and layer, 
            and only if the layer has a ground plane.
            chip_name (str): Name of chip.
            no_cheese_buffer (float) :  Will be used for fillet and size of buffer. 

        Returns:
            Union[None, shapely.geometry.multipolygon.MultiPolygon]: The shapely which combines the 
            polygons and linestrings and creates buffer as specificed through default_options.
        """

        style_cap = int(self.parse_value(self.options.no_cheese.cap_style))
        style_join = int(self.parse_value(self.options.no_cheese.join_style))

        poly_sub_df = sub_df[sub_df.geometry.apply(
            lambda x: isinstance(x, shapely.geometry.polygon.Polygon))]
        poly_sub_geo = poly_sub_df['geometry'].tolist()

        path_sub_df = sub_df[sub_df.geometry.apply(
            lambda x: isinstance(x, shapely.geometry.linestring.LineString))]
        path_sub_geo = path_sub_df['geometry'].tolist()
        path_sub_width = path_sub_df['width'].tolist()
        for n in range(len(path_sub_geo)):
            path_sub_geo[n] = path_sub_geo[n].buffer(path_sub_width[n] / 2,
                                                     cap_style=style_cap,
                                                     join_style=style_join)

        #  Need to add buffer_size, cap style, and join style to default options
        combo_list = path_sub_geo + poly_sub_geo
        combo_shapely = draw.union(combo_list)

        if not combo_shapely.is_empty:
            #Can return either Multipolgon or just one polygon.
            combo_shapely = combo_shapely.buffer(no_cheese_buffer,
                                                 cap_style=style_cap,
                                                 join_style=style_join)
            if isinstance(combo_shapely, shapely.geometry.polygon.Polygon):
                combo_shapely = shapely.geometry.MultiPolygon([combo_shapely])

            # Check if the buffer went past the chip size.
            chip_box, status = self.design.get_x_y_for_chip(chip_name)
            if status == 0:
                minx, miny, maxx, maxy = chip_box
                c_minx, c_miny, c_maxx, c_maxy = combo_shapely.bounds
                if (c_minx < minx or c_miny < miny or c_maxx > maxx or
                        c_maxy > maxy):
                    self.logger.warning(
                        f'The bounding box for no-cheese is outside of chip size.\n'
                        f'Bounding box for chip is {chip_box}.\n'
                        f'Bounding box with no_cheese buffer is {combo_shapely.bounds}.'
                    )
            else:
                self.logger.warning(
                    f'design.get_x_y_for_chip() did NOT return a good code for chip={chip_name},'
                    f'for cheese_buffer_maker.  The chip boundary will not be tested.'
                )

            # The type of combo_shapely will be  <class 'shapely.geometry.multipolygon.MultiPolygon'>
            return combo_shapely
        else:
            return None

    def populate_poly_path_for_export(self):
        """Using the geometries for each table name in QGeometry, 
        populate self.lib to eventually write to a GDS file.

        For every layer within a chip, use the same "subtraction box" for the elements that
        have subtract as true.  Every layer within a chip will have cell named:
        f'TOP_{chip_name}_{chip_layer}'.

        Args:
            file_name (str): The path and file name to write the gds file.
                             Name needs to include desired extension, i.e. "a_path_and_name.gds".

        """

        precision = float(self.parse_value(self.options.precision))
        max_points = int(self.parse_value(self.options.max_points))

        lib = self.new_gds_library()

        # Keep this to demo how to pass to gds without subtraction
        # Need to add the chipnames to this depreciated code.
        # The NO_EDITS cell is for testing of development code.
        # cell = lib.new_cell('NO_EDITS', overwrite_duplicate=True)

        # for table_name in self.design.qgeometry.get_element_types():
        #     q_geometries = getattr(self, f'{table_name}s')
        #     if q_geometries is None:
        #         self.logger.warning(
        #             f'There are no {table_name}s to write.')
        #     else:
        #         cell.add(q_geometries)

        #     if q_geometries is None:
        #         self.logger.warning(
        #             f'There is no table named "{table_name}s" to write.')
        #     else:
        #        cell.add(q_geometries)

        if is_true(self.options.ground_plane):
            all_chips_top_name = 'TOP'
            all_chips_top = lib.new_cell(all_chips_top_name,
                                         overwrite_duplicate=True)
            for chip_name in self.chip_info:
                chip_only_top_name = f'TOP_{chip_name}'
                chip_only_top = lib.new_cell(chip_only_top_name,
                                             overwrite_duplicate=True)

                # If junction table, import the cell and cell to chip_only_top
                if 'junction' in self.chip_info[chip_name]:
                    self.import_junctions_to_one_cell(chip_name, lib,
                                                      chip_only_top)

                # There can be more than one chip in QGeometry.
                # All chips export to one gds file.
                # Each chip uses its own subtract rectangle.
                layers_in_chip = self.design.qgeometry.get_all_unique_layers(
                    chip_name)

                minx, miny, maxx, maxy = self.dict_bounds[chip_name][
                    'for_subtract']
                rectangle_points = [(minx, miny), (maxx, miny), (maxx, maxy),
                                    (minx, maxy)]

                for chip_layer in layers_in_chip:

                    self.chip_info[chip_name]['subtract_poly'] = gdspy.Polygon(
                        rectangle_points, chip_layer)

                    ground_cell_name = f'TOP_{chip_name}_{chip_layer}'
                    ground_cell = lib.new_cell(ground_cell_name,
                                               overwrite_duplicate=True)

                    if len(self.chip_info[chip_name][chip_layer]
                           ['q_subtract_true']) != 0:
                        subtract_cell_name = f'SUBTRACT_{chip_name}_{chip_layer}'
                        subtract_cell = lib.new_cell(subtract_cell_name,
                                                     overwrite_duplicate=True)
                        subtract_cell.add(self.chip_info[chip_name][chip_layer]
                                          ['q_subtract_true'])
                        '''gdspy.boolean() is not documented clearly.
                        If there are multiple elements to subtract (both poly and path),
                        the way I could make it work is to put them into a cell, within lib.
                        I used the method cell_name.get_polygons(),
                        which appears to convert all elements within the cell to poly.
                        After the boolean(), I deleted the cell from lib.
                        The memory is freed up then.
                        '''
                        diff_geometry = gdspy.boolean(
                            self.chip_info[chip_name]['subtract_poly'],
                            subtract_cell.get_polygons(),
                            'not',
                            max_points=max_points,
                            precision=precision,
                            layer=chip_layer)

                        lib.remove(subtract_cell)

                        if diff_geometry is None:
                            self.design.logger.warning(
                                f'There is no table named diff_geometry to write.'
                            )
                        else:
                            ground_cell.add(diff_geometry)

                    if self.chip_info[chip_name][chip_layer][
                            'q_subtract_false'] is None:
                        self.logger.warning(
                            f'There is no table named self.chip_info[{chip_name}][q_subtract_false] to write.'
                        )
                    else:
                        if len(self.chip_info[chip_name][chip_layer]
                               ['q_subtract_false']) != 0:
                            ground_cell.add(self.chip_info[chip_name]
                                            [chip_layer]['q_subtract_false'])
                    # put all cells into TOP_chipname, if not empty.
                    # When checking for bounding box, gdspy will return None if empty.
                    if ground_cell.get_bounding_box() is not None:
                        chip_only_top.add(gdspy.CellReference(ground_cell))
                    else:
                        lib.remove(ground_cell)

                # put all chips into TOP
                if chip_only_top.get_bounding_box() is not None:
                    all_chips_top.add(gdspy.CellReference(chip_only_top))
                else:
                    lib.remove(chip_only_top)

    def get_linestring_characteristics(
            self,
            row: 'pandas.core.frame.Pandas') -> Tuple[Tuple, float, float]:
        """Given a row in the Junction table, give the characteristics of LineString in
        row.geometry.

        Args:
            row (pandas.core.frame.Pandas): A row from Junction table of QGeometry.

        Returns:
            Tuple:
            * 1st entry is Tuple[float,float]: The midpoint of Linestring from row.geometry in format (x,y).
            * 2nd entry is float: The angle in degrees of Linestring from row.geometry.
            * 3rd entry is float: Is the magnitude of Linestring from row.geometry.
        """
        precision = float(self.parse_value(self.options.precision))
        for_rounding = int(np.abs(np.log10(precision)))

        [(minx, miny), (maxx, maxy)] = row.geometry.coords[:]

        center = QGDSRenderer.midpoint_xy(minx, miny, maxx, maxy)
        rotation = math.degrees(math.atan2((maxy - miny), (maxx - minx)))
        magnitude = np.round(
            distance.euclidean(row.geometry.coords[0], row.geometry.coords[1]),
            for_rounding)

        return center, rotation, magnitude

    def give_rotation_center_twopads(
            self, row: 'pandas.core.frame.Pandas',
            a_cell_bounding_box: 'numpy.ndarray') -> Tuple:
        """Calculate the angle for rotation, center of LineString in row.geometry, and
        if needed create two pads to connect the junction to qubit.

        Args:
            row (pandas.core.frame.Pandas): A row from Junction table of QGeometry.
            a_cell_bounding_box (numpy.ndarray): Give the bounding box of cell used in row.gds_cell_name.

        Returns:
            Tuple:
            * 1st entry is float: The angle in degrees of Linestring from row.geometry.
            * 2nd entry is Tuple[float,float]: The midpoint of Linestring from row.geometry in format (x,y).
            * 3rd entry is gdspy.polygon.Rectangle: None if Magnitude of LineString is smaller than width
              of cell from row.gds_cell_name. Otherwise the rectangle for pad on LEFT of row.gds_cell_name.
            * 4th entry is gdspy.polygon.Rectangle: None if Magnitude of LineString is smaller than width
              of cell from row.gds_cell_name. Otherwise the rectangle for pad on RIGHT of row.gds_cell_name.
        """

        junction_pad_overlap = float(
            self.parse_value(self.options.junction_pad_overlap))

        pad_height = row.width
        center, rotation, magnitude = self.get_linestring_characteristics(row)
        [(jj_minx, jj_miny), (jj_maxx, jj_maxy)] = a_cell_bounding_box[0:2]

        pad_left = None
        pad_right = None
        jj_x_width = abs(jj_maxx - jj_minx)
        jj_y_height = abs(jj_maxy - jj_miny)

        jj_center_x = (jj_x_width / 2) + jj_minx
        jj_center_y = (jj_y_height / 2) + jj_miny

        pad_height = row.width

        if pad_height < jj_y_height:
            text_id = self.design._components[row.component]._name
            self.logger.warning(
                f'In junction table, component={text_id} with key={row.key} '
                f'has width={pad_height} smaller than cell dimension={jj_y_height}.'
            )

        if jj_x_width < magnitude:
            pad_x_size_minus_overlap = (magnitude - jj_x_width) / 2
            pad_miny = jj_center_y - (pad_height / 2)
            pad_left = gdspy.Rectangle(
                (jj_minx - pad_x_size_minus_overlap, pad_miny),
                (jj_minx + junction_pad_overlap, pad_miny + pad_height),
                layer=int(row.layer),
                datatype=10)

            pad_right = gdspy.Rectangle(
                (jj_maxx - junction_pad_overlap, pad_miny),
                (jj_maxx + pad_x_size_minus_overlap, pad_miny + pad_height),
                layer=int(row.layer),
                datatype=10)

        return rotation, center, pad_left, pad_right


############

    def import_junctions_to_one_cell(self, chip_name: str, lib: gdspy.library,
                                     chip_only_top: gdspy.library.Cell):
        """Given lib, import the gds file from default options.  Based on the cell name in QGeometry table,
        import the cell from the gds file and place it in hierarchy of chip_only_top. In addition, the linestring
        should be two vertexes, and denotes two things.  1. The midpoint of segment is the the center of cell.
        2. The angle made by second tuple - fist tuple  for delta y/ delta x is used to rotate the cell.

        Args:
            chip_name (str): The name of chip.
            lib (gdspy.library): The library used to export the entire QDesign.
            chip_only_top (gdspy.library.Cell):  The cell used for just chip_name.
        """
        # Make sure the file exists, before trying to read it.
        max_points = int(self.parse_value(self.options.max_points))

        status, directory_name = can_write_to_path(self.options.path_filename)

        if os.path.isfile(self.options.path_filename):
            lib.read_gds(self.options.path_filename, units='convert')
            for row in self.chip_info[chip_name]['junction'].itertuples():
                layer_num = int(row.layer)
                if row.gds_cell_name in lib.cells.keys():
                    a_cell = lib.extract(row.gds_cell_name)
                    a_cell_bounding_box = a_cell.get_bounding_box()

                    rotation, center, pad_left, pad_right = self.give_rotation_center_twopads(
                        row, a_cell_bounding_box)

                    # String for JJ combined with pad Right and pad Left
                    jj_pad_RL_name = f'{row.gds_cell_name}_component{row.component}_name{row.name}'
                    temp_cell = lib.new_cell(jj_pad_RL_name,
                                             overwrite_duplicate=True)
                    temp_cell.add(a_cell)

                    if pad_left is not None:
                        temp_cell.add(pad_left)
                    if pad_right is not None:
                        temp_cell.add(pad_right)

                    chip_only_top.add(
                        gdspy.CellReference(temp_cell,
                                            origin=center,
                                            rotation=rotation))
                    deleteme = 5
                else:
                    self.logger.warning(
                        f'From the "junction" table, the cell named'
                        f' "{row.gds_cell_name}"",  is not in file: {self.options.path_filename}.'
                        f' The cell was not used.')

        else:
            self.logger.warning(
                f'Not able to find file:"{self.options.path_filename}".  '
                f'Not used to replace junction.'
                f' Checked directory:"{directory_name}".')

    def export_to_gds(self,
                      file_name: str,
                      highlight_qcomponents: list = []) -> int:
        """Use the design which was used to initialize this class.
        The QGeometry element types of both "path" and "poly", will
        be used, to convert QGeometry to GDS formatted file.

        Args:
            file_name (str): File name which can also include directory path.
                             If the file exists, it will be overwritten.
            highlight_qcomponents (list): List of strings which denote the name of QComponents to render.
                                        If empty, render all components in design.

        Returns:
            int: 0=file_name can not be written, otherwise 1=file_name has been written
        """

        if not self._can_write_to_path(file_name):
            return 0

        # There can be more than one chip in QGeometry.  They all export to one gds file.
        # Each chip will hold the rectangle for subtract for each layer so:
        # chip_info[chip_name][subtract_box][(min_x,min_y,max_x,max_y)]
        # chip_info[chip_name][layer_number][all_subtract_elements]
        # chip_info[chip_name][layer_number][all_no_subtract_elements]
        self.chip_info.clear()
        self.chip_info.update(self.get_chip_names())

        if (self.create_qgeometry_for_gds(highlight_qcomponents) == 0):
            # Create self.lib and populate path and poly.
            self.populate_poly_path_for_export()

            # Add no-cheese MultiPolygon to self.chip_info[chip_name][chip_layer]['no_cheese'],
            # if self.options requests the layer.
            self.populate_no_cheese()

            # Use self.options  to decide what to put for export
            # into self.chip_info[chip_name][chip_layer]['cheese'].
            # Not finished.
            self.populate_cheese()

            # Export the file to disk from self.lib
            self.lib.write_gds(file_name)

            return 1
        else:
            return 0

    def multipolygon_to_gds(
            self, multi_poly: shapely.geometry.multipolygon.MultiPolygon,
            layer: int, data_type: int, no_cheese_buffer: float) -> list:
        """Convert a shapely MultiPolygon to corresponding gdspy 

        Args:
            multi_poly (shapely.geometry.multipolygon.MultiPolygon): The shapely geometry of no-cheese boundary.
            layer (int): The layer of the input multipolygon.
            data_type (int): Used as a "sub-layer" to place the no-cheese gdspy output.
            no_cheese_buffer (float): Used for both fillet and buffer size. 

        Returns:
            list: Each entry is converted to GDSII.
        """
        precision = self.parse_value(self.options.precision)
        max_points = int(self.parse_value(self.options.max_points))

        all_polys = list(multi_poly)
        all_gds = list()
        for poly in all_polys:
            exterior_poly = gdspy.Polygon(
                list(poly.exterior.coords),
                layer=layer,
                datatype=data_type,
            )

            all_interiors = list()
            if poly.interiors:
                for hole in poly.interiors:
                    interior_coords = list(hole.coords)
                    all_interiors.append(interior_coords)
                a_poly_set = gdspy.PolygonSet(all_interiors,
                                              layer=layer,
                                              datatype=data_type)
                a_poly = gdspy.boolean(exterior_poly,
                                       a_poly_set,
                                       'not',
                                       max_points=max_points,
                                       layer=layer,
                                       datatype=data_type,
                                       precision=precision)
                # Poly facturing leading to a funny shape. Leave this out of gds output for now.
                # a_poly.fillet(no_cheese_buffer,
                #               points_per_2pi=128,
                #               max_points=max_points,
                #               precision=precision)
                all_gds.append(a_poly)
            else:
                # Poly facturing leading to a funny shape. Leave this out of gds output for now.
                # exterior_poly.fillet(no_cheese_buffer,
                #                      points_per_2pi=128,
                #                      max_points=max_points,
                #                      precision=precision)
                all_gds.append(exterior_poly)
        return all_gds

    def qgeometry_to_gds(self, qgeometry_element: pd.Series) -> 'gdspy.polygon':
        """Convert the design.qgeometry table to format used by GDS renderer.
        Convert the class to a series of GDSII elements.

        Args:
            qgeometry_element (pd.Series): Expect a shapley object.

        Returns:
            'gdspy.polygon' or 'gdspy.FlexPath': Convert the class to a series of GDSII
            format on the input pd.Series.
        """
        """
        *NOTE:*
        GDS:
            points (array-like[N][2]) – Coordinates of the vertices of the polygon.
            layer (integer) – The GDSII layer number for this qgeometry_element.
            datatype (integer) – The GDSII datatype for this qgeometry_element (between 0 and 255).
                                  datatype=10 or 11 means only that they are from a
                                  Polygon vs. LineString.  This can be changed.
        See:
            https://gdspy.readthedocs.io/en/stable/reference.html#polygon
        """
        corners = self.options.corners
        tolerance = self.parse_value(self.options.tolerance)
        precision = self.parse_value(self.options.precision)
        max_points = int(self.parse_value(self.options.max_points))

        geom = qgeometry_element.geometry  # type: shapely.geometry.base.BaseGeometry

        if isinstance(geom, shapely.geometry.Polygon):
            exterior_poly = gdspy.Polygon(
                list(geom.exterior.coords),
                layer=qgeometry_element.layer,
                datatype=10,
            )

            # If polygons have a holes, need to remove it for gdspy.
            all_interiors = list()
            if geom.interiors:
                for hole in geom.interiors:
                    interior_coords = list(hole.coords)
                    all_interiors.append(interior_coords)
                a_poly_set = gdspy.PolygonSet(all_interiors,
                                              layer=qgeometry_element.layer,
                                              datatype=10)
                # Since there is max_points in boolean, don't need to do this twice.
                # a_poly_set = a_poly_set.fracture(max_points=max_points)
                # exterior_poly = exterior_poly.fracture(max_points=max_points)
                a_poly = gdspy.boolean(exterior_poly,
                                       a_poly_set,
                                       'not',
                                       max_points=max_points,
                                       layer=qgeometry_element.layer,
                                       datatype=10)
                return a_poly
            else:
                exterior_poly = exterior_poly.fracture(max_points=max_points)
                return exterior_poly
        elif isinstance(geom, shapely.geometry.LineString):
            '''
            class gdspy.FlexPath(points, width, offset=0, corners='natural', ends='flush',
            bend_radius=None, tolerance=0.01, precision=0.001, max_points=199,
            gdsii_path=False, width_transform=True, layer=0, datatype=0)

            Only fillet, if number is greater than zero.
            '''
            use_width = self.parse_value(self.options.width_LineString)

            if math.isnan(qgeometry_element.width):
                qcomponent_id = self.parse_value(qgeometry_element.component)
                name = self.parse_value(qgeometry_element['name'])
                layer_num = self.parse_value(qgeometry_element.layer)
                width = self.parse_value(qgeometry_element.width)
                self.logger.warning(
                    f'Since width:{width} for a Path is not a number, '
                    f'it will be exported using width_LineString: {use_width}.  '
                    f'The component_id is:{qcomponent_id}, name is:{name}, layer is: {layer_num}'
                )
            else:
                use_width = qgeometry_element.width

            if 'fillet' in qgeometry_element:
                if math.isnan(
                        qgeometry_element.fillet
                ) or qgeometry_element.fillet <= 0 or qgeometry_element.fillet < qgeometry_element.width:
                    to_return = gdspy.FlexPath(list(geom.coords),
                                               use_width,
                                               layer=qgeometry_element.layer,
                                               max_points=max_points,
                                               datatype=11)
                else:
                    to_return = gdspy.FlexPath(
                        list(geom.coords),
                        use_width,
                        layer=qgeometry_element.layer,
                        datatype=11,
                        max_points=max_points,
                        corners=corners,
                        bend_radius=qgeometry_element.fillet,
                        tolerance=tolerance,
                        precision=precision)
                return to_return
            else:
                # Could be junction table with a linestring.
                # Look for gds_path_filename in column.
                self.logger.warning(
                    f'Linestring did not have fillet in column. The qgeometry_element was not drawn.\n'
                    f'The qgeometry_element within table is:\n'
                    f'{qgeometry_element}')
        else:
            # TODO: Handle
            self.logger.warning(
                f'Unexpected shapely object geometry.'
                f'The variable qgeometry_element is {type(geom)}, method can currently handle Polygon and FlexPath.'
            )
            # print(geom)
            return None

    def get_chip_names(self) -> Dict:
        """ Returns a dict of unique chip names for ALL tables within QGeometry.
        In another words, for every "path" table, "poly" table ... etc, this method will search for unique
        chip names and return a dict of unique chip names from QGeometry table.

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
