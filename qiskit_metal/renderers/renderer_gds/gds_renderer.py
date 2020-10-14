from ... import Dict
from qiskit_metal.toolbox_python.utility_functions import get_range_of_vertex_to_not_fillet, can_write_to_path
from qiskit_metal.toolbox_python.utility_functions import can_write_to_path
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
from typing import List, Tuple, Union


import pandas as pd
from pandas.api.types import is_numeric_dtype

import numpy as np

from qiskit_metal.renderers.renderer_base import QRenderer
from qiskit_metal.toolbox_metal.parsing import is_true

if TYPE_CHECKING:
    # For linting typechecking, import modules that can't be loaded here under normal conditions.
    # For example, I can't import QDesign, because it requires Qrenderer first. We have the
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
    then the renderer will calcuate the size of all of the components
    and use that size for the "subtraction box" for every layer within a chip.

    3. If user wants to export a list of explicit components, the bounding box will be calculated by size of
    QComponents in the QGeometry table. Then be scaled by bounding_box_scale_x and bounding_box_scale_y.


    datatype:
        * 10 Polygon
        * 11 Flexpath
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
        # Some of this occours regardless (might be related to offset of a curve when done as a boolean vs. rendered),
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
        precision='0.000000001',   # 1.0 nm

        # Since Qiskit Metal GUI, does not require a width for LineString, GDS, will provide a default value.
        width_LineString='10um',


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
    """element extentions dictionary   element_extensions = dict() from base class"""

    # Add columns to junction table during QGDSRenderer.load()
    # element_extensions  is now being populated as part of load().
    # Determined from element_table_data.

    # Dict structure MUST be same as  element_extensions!!!!!!
    # This dict will be used to update QDesign during init of renderer.
    # Keeping this as a cls dict so could be edited before renderer is instantiated.
    # To update component.options junction table.
    element_table_data = dict(
        junction=dict(path_filename='Need_a_path_and_file')
    )

    def __init__(self, design: 'QDesign', initiate=True, render_template: Dict = None, render_options: Dict = None):
        """Create a QRenderer for GDS interface: export and import.

        Args:
            design (QDesign): Use QGeometry within QDesign  to obtain elements for GDS file.
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
            render_template (Dict, optional): Typically used by GUI for template options for GDS.  Defaults to None.
            render_options (Dict, optional):  Used to overide all options. Defaults to None.
        """

        super().__init__(design=design, initiate=initiate,
                         render_template=render_template, render_options=render_options)

        self.lib = None  # type: gdspy.GdsLibrary
        self.new_gds_library()

        self.dict_bounds = Dict()

        # Updated each time export_to_gds() is called.
        self.chip_info = dict()

        # check the scale
        self.check_bounding_box_scale()

        QGDSRenderer.load()

    def parse_value(self, value: 'Anything') -> 'Anything':
        """Same as design.parse_value. See design for help.

        Returns:
            Parsed value of input.
        """
        return self.design.parse_value(value)

    def check_bounding_box_scale(self):
        """
        Some error checking for bounding_box_scale_x and bounding_box_scale_y numbers.
        """
        p = self.options
        bounding_box_scale_x = self.parse_value(p.bounding_box_scale_x)
        bounding_box_scale_y = self.parse_value(p.bounding_box_scale_y)

        if bounding_box_scale_x < 1:
            self.options['bounding_box_scale_x'] = QGDSRenderer.default_options.bounding_box_scale_x
            self.logger.warning('Expected float and number greater than or equal to'
                                ' 1.0 for bounding_box_scale_x. User'
                                f'provided bounding_box_scale_x = {bounding_box_scale_x}'
                                ', using default_options.bounding_box_scale_x.')

        if bounding_box_scale_y < 1:
            self.options['bounding_box_scale_y'] = QGDSRenderer.default_options.bounding_box_scale_y
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

        setattr(
            self, f'{chip_name}_{table_name}_subtract_true', subtract_true)
        setattr(
            self, f'{chip_name}_{table_name}_subtract_false', subtract_false)

    @staticmethod
    def get_bounds(gs_table: geopandas.GeoSeries) -> Tuple[float, float, float, float]:
        """Get the bounds for all of the elements in gs_table.

        Args:
            gs_table (pandas.GeoSeries): A pandas GeoSeries used to describe components in a design.

        Returns:
            Tuple[float, float, float, float]: The bounds of all of the elements in this table. [minx, miny, maxx, maxy]
        """
        if len(gs_table) == 0:
            return(0, 0, 0, 0)

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
    def midpoint_xy(x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
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
        midx = (x1+x2) / 2
        midy = (y1+y2) / 2

        return midx, midy

    def scale_max_bounds(self, chip_name: str, all_bounds: list) -> Tuple[tuple, tuple]:
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

    def check_qcomps(self, highlight_qcomponents: list = []) -> Tuple[list, int]:
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
                self.logger.warning(f'The component={qcomp} in highlight_qcomponents not'
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

            # all_subtract and all_no_subtract may be depreciated in future..
            self.chip_info[chip_name]['all_subtract'] = []
            self.chip_info[chip_name]['all_no_subtract'] = []

            self.dict_bounds[chip_name] = Dict()
            self.dict_bounds[chip_name]['gather'] = []
            self.dict_bounds[chip_name]['for_subtract'] = tuple()
            all_table_subtracts = []
            all_table_no_subtracts = []

            for table_name in self.design.qgeometry.get_element_types():

                # Get table for chip and table_name, and reduce to keep just the list of unique_qcomponents.
                table = self.get_table(
                    table_name, unique_qcomponents, chip_name)

                # For every chip, and layer, separate the "subtract" and "no_subtract" elements and gather bounds.
                # dict_bounds[chip_name] = list_bounds
                self.gather_subtract_elements_and_bounds(
                    chip_name, table_name, table, all_table_subtracts, all_table_no_subtracts)

            # If list of QComponents provided, use the bounding_box_scale(x and y),
            # otherwise use self._chips
            scaled_max_bound, max_bound = self.scale_max_bounds(chip_name,
                                                                self.dict_bounds[chip_name]['gather'])
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
                        f'for ground subtraction-box using the size calculated from QGeometry, ({max_bound}) will be used. ')
            if is_true(self.options.ground_plane):
                self.handle_ground_plane(chip_name,
                                         all_table_subtracts, all_table_no_subtracts)

        return 0

    def handle_ground_plane(self, chip_name: str, all_table_subtracts: list, all_table_no_subtracts: list):
        """Place all the subtract geometries for one chip into self.chip_info[chip_name]['all_subtract_true']

        For LINESTRING within table that has a value for fillet, check if any segment is shorter than fillet radius.
        If so, then break the LINESTRING so that shorter segments do not get fillet'ed and longer segments get fillet'ed.
        Add the mulitiple LINESTRINGS back to table.
        Also remove "bad" LINESTRING from table.

        Then use qgeometry_to_gds() to convert the QGeometry elements to gdspy elements.  The gdspy elements
        are place in self.chip_info[chip_name]['q_subtract_true'].

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
                item.drop(item.index[item['layer'] !=
                                     chip_layer], inplace=True)

            for item_no in copy_no_subtract:
                item_no.drop(item_no.index[item_no['layer'] !=
                                           chip_layer], inplace=True)

            self.chip_info[chip_name][chip_layer]['all_subtract_true'] = geopandas.GeoDataFrame(
                pd.concat(copy_subtract, ignore_index=False))

            self.chip_info[chip_name][chip_layer]['all_subtract_false'] = geopandas.GeoDataFrame(
                pd.concat(copy_no_subtract, ignore_index=False))

            self.chip_info[chip_name][chip_layer]['all_subtract_true'].reset_index(
                inplace=True)
            self.chip_info[chip_name][chip_layer]['all_subtract_false'].reset_index(
                inplace=True)

            if is_true(fix_short_segments):
                self.fix_short_segments_within_table(
                    chip_name, chip_layer, 'all_subtract_true')
                self.fix_short_segments_within_table(
                    chip_name, chip_layer, 'all_subtract_false')

            self.chip_info[chip_name][chip_layer]['q_subtract_true'] = self.chip_info[chip_name][chip_layer]['all_subtract_true'].apply(
                self.qgeometry_to_gds, axis=1)

            self.chip_info[chip_name][chip_layer]['q_subtract_false'] = self.chip_info[chip_name][chip_layer]['all_subtract_false'].apply(
                self.qgeometry_to_gds, axis=1)

    def fix_short_segments_within_table(self, chip_name: str, chip_layer: int, all_sub_true_or_false: str):
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

            df_copy = self.chip_info[chip_name][chip_layer][all_sub_true_or_false].copy(
                deep=True)
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

            self.chip_info[chip_name][chip_layer][all_sub_true_or_false] = df_copy.copy(
                deep=True)

    def check_length(self, a_shapely: shapely.geometry.LineString, a_fillet: float) -> Tuple[int, Dict]:
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

        self.identify_vertex_not_to_fillet(
            coords, a_fillet, all_idx_bad_fillet, len_coords)

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
                    no_fillet_vertices = coords[start:stop+1]
                    no_fillet_vertices.append(midpoints[stop])
                    shorter_lines[stop] = dict({'line': LineString(no_fillet_vertices),
                                                'fillet': float('NaN')})
                elif idx == status-1 and stop == len_coords-1:
                    # The last segment
                    no_fillet_vertices = coords[start:stop+1]
                    no_fillet_vertices.insert(0, midpoints[start-1])
                    shorter_lines[stop] = dict({'line': LineString(no_fillet_vertices),
                                                'fillet': float('NaN')})
                else:
                    # Segment in between first and last segment.
                    no_fillet_vertices = coords[start:stop+1]
                    no_fillet_vertices.insert(0, midpoints[start-1])
                    no_fillet_vertices.append(midpoints[stop])
                    shorter_lines[stop] = dict({'line': LineString(no_fillet_vertices),
                                                'fillet': float('NaN')})
            # Gather the fillet segments.
            at_vertex = 0
            for idx, (start, stop) in enumerate(idx_bad_fillet):
                fillet_vertices.clear()
                if idx == 0 and start == 0:
                    pass    # just update at_vertex
                if idx == 0 and start == 1:
                    init_tuple = coords[0]
                    fillet_vertices = [init_tuple, midpoints[start-1]]
                    shorter_lines[start] = dict({'line': LineString(fillet_vertices),
                                                 'fillet': a_fillet})
                if idx == 0 and start > 1:
                    fillet_vertices = coords[0:start]
                    fillet_vertices.append(midpoints[start-1])
                    shorter_lines[start] = dict({'line': LineString(fillet_vertices),
                                                 'fillet': a_fillet})
                    if idx == status-1 and stop != len_coords-1:
                        # Extra segment after the last no-fillet.
                        fillet_vertices.clear()
                        fillet_vertices = coords[stop+1:len_coords]
                        fillet_vertices.insert(0, midpoints[stop])
                        shorter_lines[len_coords] = dict({'line': LineString(fillet_vertices),
                                                          'fillet': a_fillet})
                elif idx == status-1 and stop != len_coords-1:
                    fillet_vertices = coords[at_vertex+1:start]
                    fillet_vertices.insert(0, midpoints[at_vertex])
                    fillet_vertices.append(midpoints[start-1])
                    shorter_lines[start] = dict({'line': LineString(fillet_vertices),
                                                 'fillet': a_fillet})
                    # Extra segment after the last no-fillet.
                    fillet_vertices.clear()
                    fillet_vertices = coords[stop+1:len_coords]
                    fillet_vertices.insert(0, midpoints[stop])
                    shorter_lines[len_coords] = dict({'line': LineString(fillet_vertices),
                                                      'fillet': a_fillet})
                else:
                    if (start-at_vertex) > 1:
                        fillet_vertices = coords[at_vertex+1:start]
                        fillet_vertices.insert(0, midpoints[at_vertex])
                        fillet_vertices.append(midpoints[start-1])
                        shorter_lines[start] = dict({'line': LineString(fillet_vertices),
                                                     'fillet': a_fillet})
                at_vertex = stop  # Need to update for every loop.
        else:
            # No short segments.
            shorter_lines[len_coords-1] = a_shapely
        return status, shorter_lines

    def identify_vertex_not_to_fillet(self, coords: list, a_fillet: float, all_idx_bad_fillet: dict, len_coords: int):
        """Use coords to denote segments that are too short.  In particular,
        when fillet'd, they will cause the appearance of incorrect fillet when graphed.

        Args:
            coords (list): User provide a list of tuples.  The tuple is (x,y) location for a vertex.
            The list represents a LineString.

            a_fillet (float): The value provided by component developer.

            all_idx_bad_fillet (dict): An empty dict which will be populated by this method.
            Key 'reduced_idx' will hold list of tuples.  The tuples correspond to index for list named "coords".
            Key 'midpoints' will hold list of tuples. The index of a tuple corresponds to two index within coords.
            For example, a index in midpoints is x, that coresponds midpoint of segment x-1 to x.

            len_coords (int): The length of list coords.
        """

        fillet_scale_factor = self.parse_value(
            self.options.check_short_segments_by_scaling_fillet)
        precision = float(self.parse_value(self.options.precision))
        for_rounding = int(np.abs(np.log10(precision)))

        all_idx_bad_fillet['reduced_idx'] = get_range_of_vertex_to_not_fillet(
            coords, a_fillet, for_rounding)

        midpoints = list()
        midpoints = [QGDSRenderer.midpoint_xy(coords[idx-1][0], coords[idx-1][1], vertex2[0], vertex2[1])
                     for idx, vertex2 in enumerate(coords) if idx > 0]
        all_idx_bad_fillet['midpoints'] = midpoints

    def gather_subtract_elements_and_bounds(self, chip_name: str, table_name: str, table: geopandas.GeoDataFrame,
                                            all_subtracts: list, all_no_subtracts: list):
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

    def get_table(self, table_name: str, unique_qcomponents: list, chip_name: str) -> geopandas.GeoDataFrame:
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
            highlight_id = [self.design.name_to_id[a_qcomponent]
                            for a_qcomponent in unique_qcomponents]

            # Remove QComponents which are not requested.
            table = table[table['component'].isin(highlight_id)]

        table = table[table['chip'] == chip_name]

        return table

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
        self.lib = gdspy.GdsLibrary(unit=float(
            self.parse_value(self.options.gds_unit)))

        return self.lib

    def write_poly_path_to_file(self, file_name: str) -> None:
        """Using the geometries for each table name in QGeometry, write to a GDS file.

        For every layer within a chip, use the same "subtraction box" for the elements that
        have subtract as true.  Every layer within a chip will have cell named:
        f'TOP_{chip_name}_{chip_layer}'.

        Args:
            file_name (str): The path and file name to write the gds file.
                             Name needs to include desired extention, i.e. "a_path_and_name.gds".
        """

        precision = float(self.parse_value(self.options.precision))

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
            all_chips_top = lib.new_cell(
                all_chips_top_name, overwrite_duplicate=True)
            for chip_name in self.chip_info:
                chip_only_top_name = f'TOP_{chip_name}'
                chip_only_top = lib.new_cell(
                    chip_only_top_name, overwrite_duplicate=True)

                # There can be more than one chip in QGeometry.
                # All chips export to one gds file.
                # Each chip uses its own subtract rectangle.
                layers_in_chip = self.design.qgeometry.get_all_unique_layers(
                    chip_name)

                minx, miny, maxx, maxy = self.dict_bounds[chip_name]['for_subtract']
                rectangle_points = [(minx, miny), (maxx, miny),
                                    (maxx, maxy), (minx, maxy)]

                for chip_layer in layers_in_chip:

                    self.chip_info[chip_name]['subtract_poly'] = gdspy.Polygon(
                        rectangle_points, chip_layer)

                    ground_cell_name = f'TOP_{chip_name}_{chip_layer}'
                    ground_cell = lib.new_cell(
                        ground_cell_name, overwrite_duplicate=True)

                    if len(self.chip_info[chip_name][chip_layer]['q_subtract_true']) != 0:
                        subtract_cell_name = f'SUBTRACT_{chip_name}_{chip_layer}'
                        subtract_cell = lib.new_cell(
                            subtract_cell_name, overwrite_duplicate=True)
                        subtract_cell.add(
                            self.chip_info[chip_name][chip_layer]['q_subtract_true'])

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
                            precision=precision,
                            layer=chip_layer)

                        lib.remove(subtract_cell)

                        if diff_geometry is None:
                            self.design.logger.warning(
                                f'There is no table named diff_geometry to write.')
                        else:
                            ground_cell.add(diff_geometry)

                    if self.chip_info[chip_name][chip_layer]['q_subtract_false'] is None:
                        self.logger.warning(
                            f'There is no table named self.chip_info[{chip_name}][q_subtract_false] to write.')
                    else:
                        if len(self.chip_info[chip_name][chip_layer]['q_subtract_false']) != 0:
                            ground_cell.add(
                                self.chip_info[chip_name][chip_layer]['q_subtract_false'])
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

        lib.write_gds(file_name)

    def export_to_gds(self, file_name: str, highlight_qcomponents: list = []) -> int:
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

        if not can_write_to_path(file_name):
            return 0

        # There can be more than one chip in QGeometry.  They all export to one gds file.
        # Each chip will hold the rectangle for subtract for each layer so:
        # chip_info[chip_name][subtract_box][(min_x,min_y,max_x,max_y)]
        # chip_info[chip_name][layer_number][all_subtract_elements]
        # chip_info[chip_name][layer_number][all_no_subtract_elements]
        self.chip_info.clear()
        self.chip_info.update(self.get_chip_names())

        if (self.create_qgeometry_for_gds(highlight_qcomponents) == 0):
            self.write_poly_path_to_file(file_name)
            return 1
        else:
            return 0

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
        # TODO: change to actual parsing and unit conversion
        tolerance = float(self.options.tolerance)
        # TODO: Check it works as desired
        precision = float(self.options.precision)

        geom = qgeometry_element.geometry  # type: shapely.geometry.base.BaseGeometry

        if isinstance(geom, shapely.geometry.Polygon):
            exterior_poly = gdspy.Polygon(list(geom.exterior.coords),
                                          layer=qgeometry_element.layer,
                                          datatype=10,
                                          )
            # If polygons have a holes, need to remove it for gdspy.
            all_interiors = list()
            if geom.interiors:
                for hole in geom.interiors:
                    interior_coords = list(hole.coords)
                    all_interiors.append(interior_coords)
                a_poly_set = gdspy.PolygonSet(
                    all_interiors, layer=qgeometry_element.layer, datatype=10)
                a_poly = gdspy.boolean(
                    exterior_poly, a_poly_set, 'not', layer=qgeometry_element.layer, datatype=10)
                return a_poly
            else:
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
                    f'The component_id is:{qcomponent_id}, name is:{name}, layer is: {layer_num}')
            else:
                use_width = qgeometry_element.width

            if 'fillet' in qgeometry_element:
                if math.isnan(qgeometry_element.fillet) or qgeometry_element.fillet <= 0 or qgeometry_element.fillet < qgeometry_element.width:
                    to_return = gdspy.FlexPath(list(geom.coords),
                                               use_width,
                                               layer=qgeometry_element.layer,
                                               datatype=11)
                else:
                    to_return = gdspy.FlexPath(list(geom.coords),
                                               use_width,
                                               layer=qgeometry_element.layer,
                                               datatype=11,
                                               corners=corners,
                                               bend_radius=qgeometry_element.fillet,
                                               tolerance=tolerance,
                                               precision=precision
                                               )
                return to_return
            else:
                # Could be junction table with a linestring.
                # Look for gds_path_filename in column.
                self.logger.warning(
                    f'Linestring did not have fillet in column. The qgeometry_element was not drawn.\n'
                    f'The qgeometry_element within table is:\n'
                    f'{qgeometry_element}'
                )
        else:
            # TODO: Handle
            self.logger.warning(
                f'Unexpected shapely object geometry.'
                f'The variable qgeometry_element is {type(geom)}, method can currently handle Polygon and FlexPath.')
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
