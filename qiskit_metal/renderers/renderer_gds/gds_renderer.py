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
""" This module has a QRenderer to export QDesign to a GDS file."""
# pylint: disable=too-many-lines

from copy import deepcopy
from operator import itemgetter
from typing import TYPE_CHECKING
#from typing import Dict as Dict_
from typing import Tuple, Union
#from typing import List, Any, Iterable
import math
import os
from shapely.geometry import LineString
#from pandas.api.types import is_numeric_dtype

import gdspy
import geopandas
import shapely
from scipy.spatial import distance
import pandas as pd
import numpy as np

from qiskit_metal.renderers.renderer_base import QRenderer
from qiskit_metal.renderers.renderer_gds.airbridge import Airbridge_forGDS
from qiskit_metal.renderers.renderer_gds.make_airbridge import Airbridging
from qiskit_metal.renderers.renderer_gds.make_cheese import Cheesing
from qiskit_metal.toolbox_metal.parsing import is_true
from qiskit_metal import draw

from ... import Dict

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
    """Extends QRenderer to export GDS formatted files. The methods which a
    user will need for GDS export should be found within this class.

    All chips within design should be exported to one gds file.
    For the "subtraction box":
    1. If user wants to export the entire design, AND if the base class of
    QDesign._chips[chip_name]['size'] has dict following below example:
    {'center_x': 0.0, 'center_y': 0.0, 'size_x': 9, 'size_y': 6}
    then this box will be used for every layer within a chip.

    2. If user wants to export entire design, BUT there is no information in
    QDesign._chips[chip_name]['size'], then the renderer will calculate the
    size of all of the components and use that size for the "subtraction box"
    for every layer within a chip.

    3. If user wants to export a list of explicit components, the bounding
    box will be calculated by size of QComponents in the QGeometry table.
    Then be scaled by bounding_box_scale_x and bounding_box_scale_y.

    4. Note: When using the Junction table, the cell for Junction should
    be "x-axis" aligned and then GDS rotates based on LineString given
    in Junction table.


    datatype:
        * 10 Polygon
        * 11 Flexpath

    Default Options:
        * short_segments_to_not_fillet: 'True'
        * check_short_segments_by_scaling_fillet: '2.0'
        * gds_unit: '1'
        * ground_plane: 'True'
        * negative_mask: Dict(main=[])
        * corners: 'circular bend'
        * tolerance: '0.00001'
        * precision: '0.000000001'
        * width_LineString: '10um'
        * path_filename: '../resources/Fake_Junctions.GDS'
        * junction_pad_overlap: '5um'
        * max_points: '199'
        * fabricate: 'False'
        * airbridge: Dict
            * geometry: Dict
                qcomponent_base: Airbridge_forGDS
                options: Dict(crossover_length='22um')
            * bridge_pitch: '100um'
            * bridge_minimum_spacing: '5um'
            * datatype: '0'
        * cheese: Dict
            * datatype: '100'
            * shape: '0'
            * cheese_0_x: '50um'
            * cheese_0_y: '50um'
            * cheese_1_radius: '100um'
            * delta_x='100um',
            * delta_y='100um',
            * edge_nocheese='200um',
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

    # Default options, over-written by passing ``options` dict to
    # render_options.
    # Type: Dict[str, str]
    default_options = Dict(

        # Before converting LINESTRING to FlexPath for GDS, check for fillet
        # errors for LINESTRINGS in QGeometry in QGeometry due to short
        # segments.  If true, break up the LINESTRING so any segment which is
        # shorter than the scaled-fillet by "fillet_scale_factor" will be
        # separated so the short segment will not be fillet'ed.
        short_segments_to_not_fillet='True',
        check_short_segments_by_scaling_fillet='2.0',

        # DO NOT MODIFY `gds_unit`. Gets overwritten by ``set_units``.
        # gdspy unit is 1 meter.  gds_units appear to ONLY be used during
        # write_gds().  Note that gds_unit will be overwritten from the design
        # units, during init().
        # WARNING: this cannot be changed since it is only used during the
        # init once.
        gds_unit='1',  # 1m

        # Implement creating a ground plane which is scaled from largest
        # bounding box, then QGeometry which is marked as subtract will be
        # removed from ground_plane.  Then the balance of QGeometry will be
        # placed placed in same layer as ground_plane.
        ground_plane='True',

        # By default, export_to_gds() will create a positive_mask for every
        # chip and layer.  Within the Dict, there needs to be an entry for each
        # chip.  Each chip has a list of layers that should export as a
        # negative mask.  If layer number in list, the mask will be negative
        # for that layer.  If user wants to export to a negative_mask for all
        # layers, every layer_number MUST be in list.
        negative_mask=Dict(main=[]),

        # For the gds file, Show/Don't Show intermediate steps?
        # If false, show the intermediate steps in the exported gds file.
        # If true, show the geometries on either neg_datatype_fabricate or pos_datatype_fabricate.
        #   Example:  # denotes the layer number
        #           delete for negative mask: TOP_main_#_NoCheese_99, TOP_main_#_one_hole
        #           delete for positive mask: TOP_main_#_NoCheese_99, TOP_main_#_one_hole,
        #                                       ground_main_#
        fabricate='False',

        # corners: ('natural', 'miter', 'bevel', 'round', 'smooth',
        # 'circular bend', callable, list)
        # Type of joins. A callable must receive 6 arguments
        # (vertex and direction vector from both segments being joined,
        # the center and width of the path)
        # and return a list of vertices that make the join.
        # A list can be used to define the join for each parallel path.
        corners='circular bend',

        # tolerance > precision
        # Precision used for gds lib, boolean operations and FlexPath should
        # likely be kept the same.  They can be different, but increases odds
        # of weird artifacts or misalignment.  Some of this occurs regardless
        # (might be related to offset of a curve when done as a
        # boolean vs. rendered), but they are <<1nm, which isn't even picked
        # up by any fab equipment (so can be ignored).  Numerical errors start
        # to pop up if set precision too fine,
        # but 1nm seems to be the finest precision we use anyhow.
        # FOR NOW SPECIFY IN METERS.
        tolerance='0.00001',  # 10.0 um

        # With input from fab people, any of the weird artifacts
        # (like unwanted gaps) that are less than 1nm in size can be ignored.
        # They don't even show up in the fabricated masks.
        # So, the precision of e-9 (so 1 nm) should be good as a default.
        # FOR NOW SPECIFY IN METERS.
        precision='0.000000001',  # 1.0 nm

        # Since Qiskit Metal GUI, does not require a width for LineString, GDS,
        # will provide a default value.
        width_LineString='10um',

        # The file is expected to be in GDS format.  The cell will be placed
        # into gds Metal output without being edited. The name of the cell can
        # be placed as options for a component, i.e. placing within a qubit.
        # During export, the cell will NOT be edited, just imported.
        path_filename='../resources/Fake_Junctions.GDS',

        # For junction table, when cell from default_options.path_filename does
        # not fit into linestring, QGDSRender will create two pads and add to
        # junction to fill the location of lineString.  The junction_pad_overlap
        # is from the junction cell to the newly created pads.
        junction_pad_overlap='5um',

        # Vertex limit for FlexPath
        # max_points (integer) – If the number of points in the polygonal path
        # boundary is greater than max_points, it will be fractured in smaller
        # polygons with at most max_points each. If max_points is zero,
        # no fracture will occur. GDSpy uses 199 as the default. The historical
        # max value of vertices for a poly/path was 199 (fabrication equipment
        # restrictions).  The hard max limit that a GDSII file can
        # handle is 8191.
        max_points='199',

        # Airbriding
        airbridge=Dict(
            # GDS datatype of airbridges.
            datatype='0',

            # Setup geometrical style of airbridge
            geometry=Dict(
                # Skeleton of airbridge in QComponent form,
                # meaning this is a child of QComponents.
                qcomponent_base=Airbridge_forGDS,
                # These options are plugged into the qcomponent_base.
                # Think of it as calling qcomponent_base(design, name, options=options).
                options=Dict(crossover_length='22um')),
            # Spacing between centers of each airbridge.
            bridge_pitch='100um',

            # Minimum spacing between each airbridge,
            # this number usually comes from fabrication guidelines.
            bridge_minimum_spacing='5um'),

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

            # Identify which layers to view in gds output file, for each chip
            view_in_file=Dict(main={1: True}),

            # delta spacing between holes
            delta_x='100um',
            delta_y='100um',

            # Keep a buffer around the perimeter of chip, that will
            # not need cheesing.
            edge_nocheese='200um'),

        # Think of this as a keep-out region for cheesing.
        no_cheese=Dict(
            # For every layer, if there is a ground plane, do cheesing and
            # place the output on the datatype number (sub-layer number)
            datatype='99',
            buffer='25um',

            #The styles of caps are specified by integer values:
            # 1 (round), 2 (flat), 3 (square).
            cap_style='2',

            # The styles of joins between offset segments are specified by
            # integer values:
            # 1 (round), 2 (mitre), and 3 (bevel).
            join_style='2',

            # Identify which layers to view in gds output file, for each chip
            view_in_file=Dict(main={1: True}),
        ),

        # (float): Scale box of components to render.
        # Should be greater than 1.0.  For benefit of the GUI, keep this the
        # last entry in the dict.  GUI shows a note regarding bound_box.
        bounding_box_scale_x='1.2',
        bounding_box_scale_y='1.2',
    )
    """Default options"""

    name = 'gds'
    """Name"""

    # When additional columns are added to QGeometry,
    # this is the example to populate it.
    # e.g. element_extensions = dict(
    #         base=dict(color=str, klayer=int),
    #         path=dict(thickness=float, material=str, perfectE=bool),
    #         poly=dict(thickness=float, material=str), )
    # """element extensions dictionary from base class:
    #    element_extensions = dict() """

    # Add columns to junction table during QGDSRenderer.load()
    # element_extensions  is now being populated as part of load().
    # Determined from element_table_data.

    # Dict structure MUST be same as  element_extensions!!!!!!
    # This dict will be used to update QDesign during init of renderer.
    # Keeping this as a cls dict so could be edited before renderer is
    # instantiated.  To update component.options junction table.

    element_table_data = dict(
        # Cell_name must exist in gds file with: path_filename
        junction=dict(cell_name='my_other_junction'),
        path=dict(make_airbridge=False))
    """Element table data"""

    def __init__(self,
                 design: 'QDesign',
                 initiate=True,
                 render_template: Dict = None,
                 render_options: Dict = None):
        """Create a QRenderer for GDS interface: export and import.

        Args:
            design (QDesign): Use QGeometry within QDesign  to obtain elements
                            for GDS file.
            initiate (bool, optional): True to initiate the renderer.
                                        Defaults to True.
            render_template (Dict, optional): Typically used by GUI for
                                template options for GDS.  Defaults to None.
            render_options (Dict, optional): Used to override all options.
                                            Defaults to None.
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
        self._check_bounding_box_scale()

        # if imported, hold the path to file name, otherwise None.
        self.imported_junction_gds = None

        QGDSRenderer.load()

    def _initiate_renderer(self):
        """Not used by the gds renderer at this time. only returns True.
        """
        return True

    def _close_renderer(self):
        """Not used by the gds renderer at this time. only returns True.
        """
        return True

    def render_design(self):
        """Export the design to GDS."""
        self.export_to_gds(file_name=self.design.name, highlight_qcomponents=[])

    def _check_bounding_box_scale(self):
        """Some error checking for bounding_box_scale_x and
        bounding_box_scale_y numbers."""
        bounding_box_scale_x = self.parse_value(
            self.options.bounding_box_scale_x)
        bounding_box_scale_y = self.parse_value(
            self.options.bounding_box_scale_y)

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
                'Expected float and number greater than or equal to 1.0 for '
                'bounding_box_scale_y.  User provided '
                f'bounding_box_scale_y = {bounding_box_scale_y}, '
                'using default_options.bounding_box_scale_y.')

    @staticmethod
    def _clear_library():
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

        self.logger.warning('Not able to write to directory.'
                            f'File:"{file}" not written.'
                            f' Checked directory:"{directory_name}".')
        return 0

    def _update_units(self):
        """Update the options in the units.

        Warning: DOES NOT CHANGE THE CURRENT LIB
        """
        self.options['gds_unit'] = 1.0 / self.design.parse_value('1 meter')

    def _separate_subtract_shapes(self, chip_name: str, table_name: str,
                                  table: geopandas.GeoSeries) -> None:
        """For each chip and table, separate them by subtract being either True
        or False. Names of chip and table should be same as the QGeometry
        tables.

        Args:
            chip_name (str): Name of "chip".  Example is "main".
            table_name (str): Name for "table".  Example is "poly", and "path".
            table (geopandas.GeoSeries): Table with similar qgeometries.
        """
        # pylint: disable=singleton-comparison
        subtract_true = table[table['subtract'] == True]

        subtract_false = table[table['subtract'] == False]

        setattr(self, f'{chip_name}_{table_name}_subtract_true', subtract_true)
        setattr(self, f'{chip_name}_{table_name}_subtract_false',
                subtract_false)

    @staticmethod
    def _get_bounds(
            gs_table: geopandas.GeoDataFrame
    ) -> Tuple[float, float, float, float]:
        """Get the bounds for all of the elements in gs_table.

        Args:
            gs_table (geopandas.GeoDataFrame): A GeoPandas GeoDataFrame used to describe
                                        components in a design.

        Returns:
            Tuple[float, float, float, float]: The bounds of all of the
            elements in this table. [minx, miny, maxx, maxy]
        """
        if len(gs_table) == 0:
            return (0, 0, 0, 0)

        return gs_table.total_bounds

    @staticmethod
    def _inclusive_bound(all_bounds: list) -> tuple:
        """Given a list of tuples which describe corners of a box, i.e. (minx,
        miny, maxx, maxy). This method will find the box, which will include
        all boxes.  In another words, the smallest minx and miny; and the
        largest maxx and maxy.

        Args:
            all_bounds (list): List of bounds. Each tuple corresponds to a box.

        Returns:
            tuple: Describe a box which includes the area of each box
            in all_bounds.
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
    def _midpoint_xy(x_1: float, y_1: float, x_2: float,
                     y_2: float) -> Tuple[float, float]:
        """Calculate the center of a line segment with endpoints (x1,y1) and
        (x2,y2).

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
        midx = (x_1 + x_2) / 2
        midy = (y_1 + y_2) / 2

        return midx, midy

    def _scale_max_bounds(self, chip_name: str,
                          all_bounds: list) -> Tuple[tuple, tuple]:
        """Given the list of tuples to represent all of the bounds for path,
        poly, etc. This will return the scaled using self.bounding_box_scale_x
        and self.bounding_box_scale_y, and the max bounds of the tuples
        provided.

        Args:
            chip_name (str): Name of chip.
            all_bounds (list): Each tuple=(minx, miny, maxx, maxy) in list
                            represents bounding box for poly, path, etc.

        Returns:
            tuple[tuple, tuple]:
            first tuple: A scaled bounding box which includes all paths, polys, etc.;
            second tuple: A  bounding box which includes all paths, polys, etc.
        """
        # If given an empty list.
        if len(all_bounds) == 0:
            return (0.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0)

        # Get an inclusive bounding box to contain all of the tuples provided.
        minx, miny, maxx, maxy = self._inclusive_bound(all_bounds)

        # Center of inclusive bounding box
        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2

        scaled_width = (maxx - minx) * \
            self.parse_value(self.options.bounding_box_scale_x)
        scaled_height = (maxy - miny) * \
            self.parse_value(self.options.bounding_box_scale_y)

        # Scaled inclusive bounding box by self.options.bounding_box_scale_x
        #  and self.options.bounding_box_scale_y.
        scaled_box = (center_x - (.5 * scaled_width),
                      center_y - (.5 * scaled_height),
                      center_x + (.5 * scaled_width),
                      center_y + (.5 * scaled_height))

        self.dict_bounds[chip_name]['scaled_box'] = scaled_box
        self.dict_bounds[chip_name]['inclusive_box'] = (minx, miny, maxx, maxy)

        return scaled_box, (minx, miny, maxx, maxy)

    def _check_qcomps(self,
                      highlight_qcomponents: list = None) -> Tuple[list, int]:
        """Confirm the list doesn't have names of components repeated. Confirm
        that the name of component exists in QDesign.

        Args:
            highlight_qcomponents (list, optional): List of strings which
                                        denote the name of QComponents to render.
                                        Empty list means to render entire design.
                                        Defaults to [].

        Returns:
            Tuple[list, int]:
            list: Unique list of QComponents to render.
            int: 0 if all ended well. Otherwise,
            1 if QComponent name not in design.
        """
        if highlight_qcomponents is None:
            highlight_qcomponents = []

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
        # If list passed to export is the whole chip, then want to use the
        # bounding box from design planar.  If list is subset of chip, then
        # calculate a custom bounding box and scale it.

        # pylint: disable=protected-access
        if len(unique_qcomponents) == len(self.design._components):
            # Since user wants all of the chip to be rendered, use the
            # design.planar bounding box.
            unique_qcomponents[:] = []

        return unique_qcomponents, 0

    def _create_qgeometry_for_gds(self,
                                  highlight_qcomponents: list = None) -> int:
        """Using self.design, this method does the following:

        1. Gather the QGeometries to be used to write to file.
           Duplicate names in highlight_qcomponents will be removed without
           warning.

        2. Populate self.dict_bounds, for each chip, contains the maximum bound
           for all elements to render.

        3. Calculate scaled bounding box to emulate size of chip using
           self.bounding_box_scale(x and y) and place into
           self.dict_bounds[chip_name]['for_subtract'].

        4. Gather Geometries to export to GDS format.

        Args:
            highlight_qcomponents (list): List of strings which denote the name
                            of QComponents to render.
                            If empty, render all components in design.
                            If QComponent names are duplicated,
                            duplicates will be ignored.

        Returns:
            int: 0 if all ended well.
            Otherwise, 1 if QComponent name(s) not in design.
        """
        if highlight_qcomponents is None:
            highlight_qcomponents = []
        unique_qcomponents, status = self._check_qcomps(highlight_qcomponents)
        if status == 1:
            return 1
        self.dict_bounds.clear()

        for chip_name, _ in self.chip_info.items():
            # put the QGeometry into GDS format.
            # There can be more than one chip in QGeometry.
            # They all export to one gds file.
            self.chip_info[chip_name]['all_subtract'] = []
            self.chip_info[chip_name]['all_no_subtract'] = []

            self.dict_bounds[chip_name] = Dict()
            self.dict_bounds[chip_name]['gather'] = []
            self.dict_bounds[chip_name]['for_subtract'] = tuple()
            all_table_subtracts = []
            all_table_no_subtracts = []

            for table_name in self.design.qgeometry.get_element_types():

                # Get table for chip and table_name, and reduce
                # to keep just the list of unique_qcomponents.
                table = self._get_table(table_name, unique_qcomponents,
                                        chip_name)

                if table_name == 'junction':
                    self.chip_info[chip_name]['junction'] = deepcopy(table)
                else:
                    # For every chip, and layer, separate the "subtract"
                    # and "no_subtract" elements and gather bounds.
                    # self.dict_bounds[chip_name] = list_bounds
                    self._gather_subtract_elements_and_bounds(
                        chip_name, table_name, table, all_table_subtracts,
                        all_table_no_subtracts)

            # If list of QComponents provided, use the
            # bounding_box_scale(x and y), otherwise use self._chips.
            scaled_max_bound, max_bound = self._scale_max_bounds(
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
                        f'design.get_x_y_for_chip() did NOT return a good '
                        f'code for chip={chip_name},for ground subtraction-box'
                        f' using the size calculated from QGeometry, '
                        f'({max_bound}) will be used. ')
            if is_true(self.options.ground_plane):
                self._handle_ground_plane(chip_name, all_table_subtracts,
                                          all_table_no_subtracts)

        return 0

    def _handle_ground_plane(self, chip_name: str, all_table_subtracts: list,
                             all_table_no_subtracts: list):
        """Place all the subtract geometries for one chip into
        self.chip_info[chip_name]['all_subtract_true'].

        For LINESTRING within table that has a value for fillet, check if any
        segment is shorter than fillet radius.  If so, then break the
        LINESTRING so that shorter segments do not get fillet'ed and longer
        segments get fillet'ed.  Add the multiple LINESTRINGS back to table.
        Also remove "bad" LINESTRING from table.

        Then use _qgeometry_to_gds() to convert the QGeometry elements to gdspy
        elements.  The gdspy elements are placed in
        self.chip_info[chip_name]['q_subtract_true'].

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
                self._fix_short_segments_within_table(chip_name, chip_layer,
                                                      'all_subtract_true')
                self._fix_short_segments_within_table(chip_name, chip_layer,
                                                      'all_subtract_false')

            self.chip_info[chip_name][chip_layer][
                'q_subtract_true'] = self.chip_info[chip_name][chip_layer][
                    'all_subtract_true'].apply(self._qgeometry_to_gds, axis=1)

            self.chip_info[chip_name][chip_layer][
                'q_subtract_false'] = self.chip_info[chip_name][chip_layer][
                    'all_subtract_false'].apply(self._qgeometry_to_gds, axis=1)

    # Handling Fillet issues.

    def _fix_short_segments_within_table(self, chip_name: str, chip_layer: int,
                                         all_sub_true_or_false: str):
        """Update self.chip_info geopandas.GeoDataFrame.

        Will iterate through the rows to examine the LineString.
        Then determine if there is a segment that is shorter than the criteria
        based on default_options. If so, then remove the row, and append
        shorter LineString with no fillet, within the dataframe.

        Args:
            chip_name (str): The name of chip.
            chip_layer (int): The layer within the chip to be evaluated.
            all_sub_true_or_false (str): To be used within self.chip_info:
                                'all_subtract_true' or 'all_subtract_false'.
        """
        # pylint: disable=too-many-locals
        data_frame = self.chip_info[chip_name][chip_layer][
            all_sub_true_or_false]
        df_fillet = data_frame[-data_frame['fillet'].isnull()]

        if not df_fillet.empty:
            # Don't edit the table when iterating through the rows.
            # Save info in dict and then edit the table.
            edit_index = dict()
            for index, row in df_fillet.iterrows():
                # print(
                #     f'With parse_value: {self.parse_value(row.fillet)}, '
                #     f'row.fillet: {row.fillet}')
                status, all_shapelys = self._check_length(
                    row.geometry, row.fillet)
                if status > 0:
                    edit_index[index] = all_shapelys

            df_copy = self.chip_info[chip_name][chip_layer][
                all_sub_true_or_false].copy(deep=True)
            for del_key, the_shapes in edit_index.items():
                # copy row "index" into a new data-frame "status" times.
                # Then replace the LONG shapely with all_shapelys.
                # For any entries in edit_index, edit table here.
                orig_row = df_copy.loc[del_key].copy(deep=True)
                df_copy = df_copy.drop(index=del_key)

                for dummy_new_row, short_shape in the_shapes.items():
                    orig_row['geometry'] = short_shape['line']
                    orig_row['fillet'] = short_shape['fillet']
                    # Keep ignore_index=False, otherwise,
                    # the other del_key will not be found.
                    df_copy = df_copy.append(orig_row, ignore_index=False)

            self.chip_info[chip_name][chip_layer][
                all_sub_true_or_false] = df_copy.copy(deep=True)

    def _check_length(self, a_shapely: shapely.geometry.LineString,
                      a_fillet: float) -> Tuple[int, Dict]:
        """Determine if a_shapely has short segments based on scaled fillet
        value.

        Use check_short_segments_by_scaling_fillet to determine the criteria
        for flagging a segment.  Return Tuple with flagged segments.

        The "status" returned in int:
            * -1: Method needs to update the return code.
            * 0: No issues, no short segments found
            * int: The number of shapelys returned. New shapelys, should
                    replace the ones provided in a_shapely

        The "shorter_lines" returned in dict:
        key: Using the index values from list(a_shapely.coords)
        value: dict() for each new, shorter, LineString

        The dict()
        key: fillet, value: can be float from before, or undefined to
                            denote no fillet.
        key: line, value: shorter LineString

        Args:
            a_shapely (shapely.geometry.LineString): A shapely object that
                                                    needs to be evaluated.
            a_fillet (float): From component developer.

        Returns:
            Tuple[int, Dict]:
            int: Number of short segments that should not have fillet.
            Dict: The key is an index into a_shapely. The value is a dict with
            fillet and shorter LineString.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches

        # Holds all of the index of when a segment is too short.
        idx_bad_fillet = list()
        status = -1  # Initialize to meaningless value.
        coords = list(a_shapely.coords)
        len_coords = len(coords)

        all_idx_bad_fillet = dict()

        self._identify_vertex_not_to_fillet(coords, a_fillet,
                                            all_idx_bad_fillet)

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
                    # At last tuple, and and start at first index,
                    # and the stop is not last index of coords.
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

    def _identify_vertex_not_to_fillet(self, coords: list, a_fillet: float,
                                       all_idx_bad_fillet: dict):
        """Use coords to denote segments that are too short.  In particular,
        when fillet'd, they will cause the appearance of incorrect fillet when
        graphed.

        Args:
            coords (list): User provide a list of tuples.
                    The tuple is (x,y) location for a vertex.
                    The list represents a LineString.
            a_fillet (float): The value provided by component developer.
            all_idx_bad_fillet (dict): An empty dict which will be
                                        populated by this method.

        Dictionary:
            Key 'reduced_idx' will hold list of tuples.
                    The tuples correspond to index for list named "coords".
            Key 'midpoints' will hold list of tuples.
                    The index of a tuple corresponds to two index within coords.
            For example, a index in midpoints is x,
            that corresponds midpoint of segment x-1 to x.
        """

        # Depreciated since there is no longer a scale factor
        # given to QCheckLength.
        # fillet_scale_factor = self.parse_value(
        #     self.options.check_short_segments_by_scaling_fillet)

        # precision = float(self.parse_value(self.options.precision))

        # For now, DO NOT allow the user of GDS to provide the precision.
        # user_precision = int(np.abs(np.log10(precision)))

        qdesign_precision = self.design.template_options.PRECISION

        all_idx_bad_fillet['reduced_idx'] = get_range_of_vertex_to_not_fillet(
            coords, a_fillet, qdesign_precision, add_endpoints=True)

        midpoints = list()
        midpoints = [
            QGDSRenderer._midpoint_xy(coords[idx - 1][0], coords[idx - 1][1],
                                      vertex2[0], vertex2[1])
            for idx, vertex2 in enumerate(coords)
            if idx > 0
        ]
        all_idx_bad_fillet['midpoints'] = midpoints

    # Move data around to be useful for GDS

    def _gather_subtract_elements_and_bounds(self, chip_name: str,
                                             table_name: str,
                                             table: geopandas.GeoDataFrame,
                                             all_subtracts: list,
                                             all_no_subtracts: list):
        """For every chip, and layer, separate the "subtract" and "no_subtract"
        elements and gather bounds for all the elements in qgeometries. Use
        format: f'{chip_name}_{table_name}s'.

        Args:
            chip_name (str): Name of chip.  Example is 'main'.
            table_name (str): There are multiple tables in QGeometry table.
                                Example: 'path' and 'poly'.
            table (geopandas.GeoDataFrame): Actual table for the name.
            all_subtracts (list): Pass by reference so method can update
                                    this list.
            all_no_subtracts (list): Pass by reference so method can update
                                    this list.
        """

        # Determine bound box and return scalar larger than size.
        bounds = tuple(self._get_bounds(table))

        # Add the bounds of each table to list.
        self.dict_bounds[chip_name]['gather'].append(bounds)

        if is_true(self.options.ground_plane):
            self._separate_subtract_shapes(chip_name, table_name, table)

            all_subtracts.append(
                getattr(self, f'{chip_name}_{table_name}_subtract_true'))
            all_no_subtracts.append(
                getattr(self, f'{chip_name}_{table_name}_subtract_false'))

        # Done because ground plane option may be false.
        # This is not used anywhere currently.
        # Keep this depreciated code.
        # polys use gdspy.Polygon;    paths use gdspy.LineString

        #q_geometries = table.apply(self._qgeometry_to_gds, axis=1)
        #setattr(self, f'{chip_name}_{table_name}s', q_geometries)

    def _get_table(self, table_name: str, unique_qcomponents: list,
                   chip_name: str) -> geopandas.GeoDataFrame:
        """If unique_qcomponents list is empty, get table using table_name from
        QGeometry tables for all elements with table_name.  Otherwise, return a
        table with fewer elements, for just the qcomponents within the
        unique_qcomponents list.

        Args:
            table_name (str): Can be "path", "poly", etc. from the
                            QGeometry tables.
            unique_qcomponents (list): User requested list of qcomponent
                            names to export to GDS file.

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
        """Creates a new GDS Library. Deletes the old. Create a new GDS library
        file. It can contains multiple cells.

        Returns:
            gdspy.GdsLibrary: GDS library which can contain multiple cells.
        """

        self._update_units()

        if self.lib:
            self._clear_library()

        # Create a new GDS library file. It can contains multiple cells.
        self.lib = gdspy.GdsLibrary(
            unit=float(self.parse_value(self.options.gds_unit)),
            precision=float(self.parse_value(self.options.precision)))

        return self.lib

    ### Start of Airbridging

    def _populate_airbridge(self):
        """
        Main function to make airbridges. This is called in `self.export_to_gds()`.
        """
        for chip_name in self.chip_info:
            layers_in_chip = self.design.qgeometry.get_all_unique_layers(
                chip_name)

            chip_box, status = self.design.get_x_y_for_chip(chip_name)
            if status == 0:
                minx, miny, maxx, maxy = chip_box

                # Right now this code assumes airbridges will look
                # the same across all CPWs. If you want to change that,
                # add an if/else statement here to check for custom behavior.
                # You will also have to update the self.default_options.
                self._make_uniform_airbridging_df(minx, miny, maxx, maxy,
                                                  chip_name)

    def _make_uniform_airbridging_df(self, minx: float, miny: float,
                                     maxx: float, maxy: float, chip_name: str):
        """
        Apply airbridges to all `path` elements which have 
        options.gds_make_airbridge = True. This is a 
        wrapper for Airbridging.make_uniform_airbridging_df(...).

        Args:
            minx (float): Chip minimum x location.
            miny (float): Chip minimum y location.
            maxx (float): Chip maximum x location.
            maxy (float): chip maximum y location.
            chip_name (str): User defined chip name.
        """
        # Warning / limitations
        if (self.options.corners != 'circular bend'):
            self.logger.warning(
                'Uniform airbridging is designed for `self.options.corners = "circular bend"`. You might experience unexpected behavior.'
            )

        # gdspy objects
        top_cell = self.lib.cells[f'TOP_{chip_name}']
        lib_cell = self.lib.new_cell(f'TOP_{chip_name}_ab')
        datatype = int(self.parse_value(self.options.airbridge.datatype))
        no_cheese_buffer = float(self.parse_value(
            self.options.no_cheese.buffer))

        # Airbridge Options
        self.options.airbridge.qcomponent_base
        self.options.airbridge.options
        airbridging = Airbridging(design=self.design,
                                  lib=self.lib,
                                  minx=minx,
                                  miny=miny,
                                  maxx=maxx,
                                  maxy=maxy,
                                  chip_name=chip_name,
                                  precision=self.options.precision)
        airbridges_df = airbridging.make_uniform_airbridging_df(
            custom_qcomponent=self.options.airbridge.geometry.qcomponent_base,
            qcomponent_options=self.options.airbridge.geometry.options,
            bridge_pitch=self.options.airbridge.bridge_pitch,
            bridge_minimum_spacing=self.options.airbridge.bridge_minimum_spacing
        )

        # Get all MultiPolygons and render to gds file
        for _, row in airbridges_df.iterrows():
            ab_component_multi_poly = row['MultiPoly']
            ab_component_layer = row['layer']
            airbridge_gds = self._multipolygon_to_gds(
                multi_poly=ab_component_multi_poly,
                layer=ab_component_layer,
                data_type=datatype,
                no_cheese_buffer=no_cheese_buffer)

            lib_cell.add(airbridge_gds)
            top_cell.add(gdspy.CellReference(lib_cell))

    ### End of Airbridging

    ### Start of Cheesing

    def _check_cheese(self, chip: str, layer: int) -> int:
        """Examine the option for cheese_view_in_file.

        Args:
            chip (str): User defined chip name.
            layer (int): Layer used in chip.

        Returns:
            int: Observation of option based on chip and layer information.

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

    def _check_no_cheese(self, chip: str, layer: int) -> int:
        """Examine the option for no_cheese_view_in_file.

        Args:
            chip (str): User defined chip name.
            layer (int): Layer used in chip.

        Returns:
            int: Observation of option based on chip and layer information.

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

    def _check_either_cheese(self, chip: str, layer: int) -> int:
        """Use methods to check two options and give review of values for
        no_cheese_view_in_file and cheese_view_in_file.

        Args:
            chip (str): User defined chip name.
            layer (int): Layer used in chip.

        Returns:
            int: Observation of options based on chip and layer information.

            * 0 This is the initialization state.
            * 1 Show the layer in both cheese and no cheese
            * 2 Show the layer in just the cheese
            * 3 Show the no-cheese, but not the cheese
            * 4 Do NOT show the layer in neither cheese
            * 5 The chip is not in the default option.
            * 6 The layer is not in the chip dict.
        """
        # pylint: disable=too-many-return-statements
        code = 0
        no_cheese_code = self._check_no_cheese(chip, layer)
        cheese_code = self._check_cheese(chip, layer)

        if no_cheese_code == 0 or cheese_code == 0:
            self.logger.warning('Not able to get no_cheese_view_in_file or '
                                'cheese_view_in_file from self.options.')
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
                f'Chip={chip} is not either in no_cheese_view_in_file '
                f'or cheese_view_in_file from self.options.')
            return code
        if no_cheese_code == 4 or cheese_code == 4:
            code = 6
            self.logger.warning(
                f'layer={layer} is not in chip={chip} either in '
                f'no_cheese_view_in_file or cheese_view_in_file from self.options.'
            )
            return code

        return code

    def _populate_cheese(self):
        """Iterate through each chip, then layer to determine the cheesing
        geometry."""

        # lib = self.lib
        cheese_sub_layer = int(self.parse_value(self.options.cheese.datatype))
        nocheese_sub_layer = int(
            self.parse_value(self.options.no_cheese.datatype))

        for chip_name in self.chip_info:
            layers_in_chip = self.design.qgeometry.get_all_unique_layers(
                chip_name)

            for chip_layer in layers_in_chip:
                code = self._check_cheese(chip_name, chip_layer)
                if code == 1:
                    chip_box, status = self.design.get_x_y_for_chip(chip_name)
                    if status == 0:
                        minx, miny, maxx, maxy = chip_box

                        self._cheese_based_on_shape(minx, miny, maxx, maxy,
                                                    chip_name, chip_layer,
                                                    cheese_sub_layer,
                                                    nocheese_sub_layer)

    def _cheese_based_on_shape(self, minx: float, miny: float, maxx: float,
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
            cheese_sub_layer (int):  User defined datatype, considered a
                    sub-layer number for where to place the cheese output.
            nocheese_sub_layer (int): User defined datatype, considered a
                    sub-layer number for where to place the NO_cheese output.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-arguments

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
        is_neg_mask = self._is_negative_mask(chip_name, chip_layer)
        fab = is_true(self.options.fabricate)

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
                                is_neg_mask,
                                cheese_sub_layer,
                                nocheese_sub_layer,
                                fab,
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
                                is_neg_mask,
                                cheese_sub_layer,
                                nocheese_sub_layer,
                                fab,
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
            dummy_a_lib = a_cheese.apply_cheesing()

    def _populate_no_cheese(self):
        """Iterate through every chip and layer.  If options choose to have
        either cheese or no-cheese, a MultiPolygon is placed
        self.chip_info[chip_name][chip_layer]['no_cheese'].

        If user selects to view the no-cheese, the method placed the
        cell with no-cheese at
        f'TOP_{chip_name}_{chip_layer}_NoCheese_{sub_layer}'.  The sub_layer
        is data_type and denoted in the options.
        """

        # pylint: disable=too-many-nested-blocks

        no_cheese_buffer = float(self.parse_value(
            self.options.no_cheese.buffer))
        sub_layer = int(self.parse_value(self.options.no_cheese.datatype))
        lib = self.lib

        fab = is_true(self.options.fabricate)

        for chip_name, _ in self.chip_info.items():
            layers_in_chip = self.design.qgeometry.get_all_unique_layers(
                chip_name)

            for chip_layer in layers_in_chip:
                code = self._check_either_cheese(chip_name, chip_layer)

                if code in (1, 2, 3):
                    if len(self.chip_info[chip_name][chip_layer]
                           ['all_subtract_true']) != 0:

                        sub_df = self.chip_info[chip_name][chip_layer][
                            'all_subtract_true']
                        no_cheese_multipolygon = self._cheese_buffer_maker(
                            sub_df, chip_name, no_cheese_buffer)

                        if no_cheese_multipolygon is not None:
                            self.chip_info[chip_name][chip_layer][
                                'no_cheese'] = no_cheese_multipolygon
                            sub_layer = int(
                                self.parse_value(
                                    self.options.no_cheese.datatype))
                            all_nocheese_gds = self._multipolygon_to_gds(
                                no_cheese_multipolygon, chip_layer, sub_layer,
                                no_cheese_buffer)
                            self.chip_info[chip_name][chip_layer][
                                'no_cheese_gds'] = all_nocheese_gds

                            # If fabricate.fab is true, then
                            # do not put nocheese in gds file.
                            if self._check_no_cheese(
                                    chip_name, chip_layer) == 1 and not fab:
                                no_cheese_subtract_cell_name = (
                                    f'TOP_{chip_name}_{chip_layer}'
                                    f'_NoCheese_{sub_layer}')
                                no_cheese_cell = lib.new_cell(
                                    no_cheese_subtract_cell_name,
                                    overwrite_duplicate=True)

                                no_cheese_cell.add(all_nocheese_gds)

                                # Keep the cell out to layer, it becomes part of ground.
                                chip_only_top_name = f'TOP_{chip_name}'

                                if no_cheese_cell.get_bounding_box(
                                ) is not None:
                                    lib.cells[chip_only_top_name].add(
                                        gdspy.CellReference(no_cheese_cell))
                                else:
                                    lib.remove(no_cheese_cell)

    def _cheese_buffer_maker(
        self, sub_df: geopandas.GeoDataFrame, chip_name: str,
        no_cheese_buffer: float
    ) -> Union[None, shapely.geometry.multipolygon.MultiPolygon]:
        """For each layer in each chip, and if it has a ground plane
        (subtract==True), determine the no-cheese buffer and return a shapely
        object. Before the buffer is created for no-cheese, the LineStrings and
        Polygons are all combined.

        Args:
            sub_df (geopandas.GeoDataFrame): The subset of QGeometry tables
                for each chip, and layer, and only if the layer has a ground plane.
            chip_name (str): Name of chip.
            no_cheese_buffer (float): Will be used for fillet and
                size of buffer.

        Returns:
            Union[None, shapely.geometry.multipolygon.MultiPolygon]: The
            shapely which combines the polygons and linestrings and creates
            buffer as specified through default_options.
        """
        # pylint: disable=too-many-locals
        style_cap = int(self.parse_value(self.options.no_cheese.cap_style))
        style_join = int(self.parse_value(self.options.no_cheese.join_style))

        poly_sub_df = sub_df[sub_df.geometry.apply(
            lambda x: isinstance(x, shapely.geometry.polygon.Polygon))]
        poly_sub_geo = poly_sub_df['geometry'].tolist()

        path_sub_df = sub_df[sub_df.geometry.apply(
            lambda x: isinstance(x, shapely.geometry.linestring.LineString))]
        path_sub_geo = path_sub_df['geometry'].tolist()
        path_sub_width = path_sub_df['width'].tolist()
        #for n in range(len(path_sub_geo)):
        for index, _ in enumerate(path_sub_geo):
            path_sub_geo[index] = path_sub_geo[index].buffer(
                path_sub_width[index] / 2,
                cap_style=style_cap,
                join_style=style_join)

        #  Need to add buffer_size, cap style, and join style to default options
        combo_list = path_sub_geo + poly_sub_geo
        combo_shapely = draw.union(combo_list)

        if not combo_shapely.is_empty:
            #Can return either Multipolygon or just one polygon.
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
                    f'for _cheese_buffer_maker.  The chip boundary will not be tested.'
                )

            # The type of combo_shapely will be
            # <class 'shapely.geometry.multipolygon.MultiPolygon'>
            return combo_shapely
        return None  # Need explicitly to avoid lint warnings.

    ### End of Cheesing

    def _get_rectangle_points(self, chip_name: str) -> Tuple[list, list]:
        """There can be more than one chip in QGeometry. All chips export to
        one gds file. Each chip uses its own subtract rectangle.

        Args:
            chip_name (str): Name of chip to render.

        Returns:
            Tuple[list, list]: The subtract-rectangle for the chip_name.
        """
        layers_in_chip = self.design.qgeometry.get_all_unique_layers(chip_name)

        minx, miny, maxx, maxy = self.dict_bounds[chip_name]['for_subtract']
        rectangle_points = [(minx, miny), (maxx, miny), (maxx, maxy),
                            (minx, maxy)]

        return layers_in_chip, rectangle_points

    def _populate_poly_path_for_export(self):
        """Using the geometries for each table name in QGeometry, populate
        self.lib to eventually write to a GDS file.

        For every layer within a chip, use the same "subtraction box" for the
        elements that have subtract as true.  Every layer within a chip will
        have cell named:  f'TOP_{chip_name}_{chip_layer}'.

        Args:
            file_name (str): The path and file name to write the gds file.
                             Name needs to include desired extension,
                             i.e. "a_path_and_name.gds".
        """

        precision = float(self.parse_value(self.options.precision))
        max_points = int(self.parse_value(self.options.max_points))

        lib = self.new_gds_library()

        if is_true(self.options.ground_plane):
            all_chips_top_name = 'TOP'
            all_chips_top = lib.new_cell(all_chips_top_name,
                                         overwrite_duplicate=True)
            for chip_name, _ in self.chip_info.items():
                chip_only_top_name = f'TOP_{chip_name}'
                chip_only_top = lib.new_cell(chip_only_top_name,
                                             overwrite_duplicate=True)

                layers_in_chip, rectangle_points = self._get_rectangle_points(
                    chip_name)

                for chip_layer in layers_in_chip:
                    self._handle_photo_resist(lib, chip_only_top, chip_name,
                                              chip_layer, rectangle_points,
                                              precision, max_points)

                # If junction table, import the cell and cell to chip_only_top
                if 'junction' in self.chip_info[chip_name]:
                    self._import_junctions_to_one_cell(chip_name, lib,
                                                       chip_only_top,
                                                       layers_in_chip)

                # put all chips into TOP
                if chip_only_top.get_bounding_box() is not None:
                    all_chips_top.add(gdspy.CellReference(chip_only_top))
                else:
                    lib.remove(chip_only_top)

    def _handle_photo_resist(self, lib: gdspy.GdsLibrary,
                             chip_only_top: gdspy.library.Cell, chip_name: str,
                             chip_layer: int, rectangle_points: list,
                             precision: float, max_points: int):
        """Handle the positive vs negative mask.

        Args:
            lib (gdspy.GdsLibrary): The gdspy library to export.
            chip_only_top (gdspy.library.Cell): The gdspy cell for top.
            chip_name (str): Name of chip to render.
            chip_layer (int): Layer of the chip to render.
            rectangle_points (list): The rectangle to denote the ground
                                    for each layer.
            precision (float): Used for gdspy.
            max_points (int): Used for gdspy. GDSpy uses 199 as the default.
        """

        self.chip_info[chip_name]['subtract_poly'] = gdspy.Polygon(
            rectangle_points, chip_layer)

        ground_cell_name = f'TOP_{chip_name}_{chip_layer}'
        ground_cell = lib.new_cell(ground_cell_name, overwrite_duplicate=True)

        if self._is_negative_mask(chip_name, chip_layer):
            self._negative_mask(lib, chip_only_top, ground_cell, chip_name,
                                chip_layer, precision, max_points)
        else:
            self._positive_mask(lib, chip_only_top, ground_cell, chip_name,
                                chip_layer, precision, max_points)

    def _is_negative_mask(self, chip: str, layer: int) -> bool:
        """Check options to see if negative mask is requested for the
        chip and layer.

        Args:
            chip (str): Chip name to search for in options.
            layer (int): Layer to search for within chip.  Determine if this
                         layer should have negative mask.

        Returns:
            bool: If there should be a negative mask for this chip and layer.
        """
        if chip in self.options.negative_mask.keys():
            if layer in self.options.negative_mask[chip]:
                return True

        return False

    def _negative_mask(self, lib: gdspy.GdsLibrary,
                       chip_only_top: gdspy.library.Cell,
                       ground_cell: gdspy.library.Cell, chip_name: str,
                       chip_layer: int, precision: float, max_points: int):
        """Apply logic for negative_mask.

        Args:
            lib (gdspy.GdsLibrary): The gdspy library to export.
            chip_only_top (gdspy.library.Cell): The gdspy cell for top.
            ground_cell (gdspy.library.Cell): Cell created for each layer.
            chip_name (str): Name of chip to render.
            chip_layer (int): Layer of the chip to render.
            precision (float): Used for gdspy.
            max_points (int): Used for gdspy. GDSpy uses 199 as the default.
        """
        if len(self.chip_info[chip_name][chip_layer]['q_subtract_true']) != 0:

            # When subtract==True for chip and layer.
            subtract_true_cell_name = f'SUBTRACT_true_{chip_name}_{chip_layer}'
            subtract_true_cell = lib.new_cell(subtract_true_cell_name,
                                              overwrite_duplicate=True)
            subtract_true_cell.add(
                self.chip_info[chip_name][chip_layer]['q_subtract_true'])

            #When subtract==False for chip and layer.
            subtract_false_cell_name = f'SUBTRACT_false_{chip_name}_{chip_layer}'
            subtract_false_cell = lib.new_cell(subtract_false_cell_name,
                                               overwrite_duplicate=True)
            subtract_false_cell.add(
                self.chip_info[chip_name][chip_layer]['q_subtract_false'])

            # Difference for True-False.
            diff_geometry = gdspy.boolean(subtract_true_cell.get_polygons(),
                                          subtract_false_cell.get_polygons(),
                                          'not',
                                          max_points=max_points,
                                          precision=precision,
                                          layer=chip_layer)

            lib.remove(subtract_true_cell)
            lib.remove(subtract_false_cell)

            if diff_geometry is None:
                self.design.logger.warning(
                    'There is no table named diff_geometry to write.')
            else:
                ground_cell.add(diff_geometry)

        QGDSRenderer._add_groundcell_to_chip_only_top(lib, chip_only_top,
                                                      ground_cell)

    def _positive_mask(self, lib: gdspy.GdsLibrary,
                       chip_only_top: gdspy.library.Cell,
                       ground_cell: gdspy.library.Cell, chip_name: str,
                       chip_layer: int, precision: float, max_points: int):
        """Apply logic for positive mask.

        Args:
            lib (gdspy.GdsLibrary): The gdspy library to export.
            chip_only_top (gdspy.library.Cell): The gdspy cell for top.
            ground_cell (gdspy.library.Cell): Cell created for each layer.
            chip_name (str): Name of chip to render.
            chip_layer (int): Layer of the chip to render.
            precision (float): Used for gdspy.
            max_points (int): Used for gdspy. GDSpy uses 199 as the default.
        """
        if len(self.chip_info[chip_name][chip_layer]['q_subtract_true']) != 0:
            subtract_cell_name = f'SUBTRACT_{chip_name}_{chip_layer}'
            subtract_cell = lib.new_cell(subtract_cell_name,
                                         overwrite_duplicate=True)
            subtract_cell.add(
                self.chip_info[chip_name][chip_layer]['q_subtract_true'])

            # gdspy.boolean() is not documented clearly.  If there are multiple
            # elements to subtract (both poly & path), the way I could
            # make it work is to put them into a cell, within lib. I used
            # the method cell_name.get_polygons(), which appears to convert
            # all elements within the cell to poly. After the boolean(),
            # I deleted the cell from lib. The memory is freed up then.
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
                    'There is no table named diff_geometry to write.')
            else:
                ground_chip_layer_name = f'ground_{chip_name}_{chip_layer}'
                ground_chip_layer = lib.new_cell(ground_chip_layer_name)
                #diff_geometry is a polygon set. So put into it's own cell.
                ground_chip_layer.add(diff_geometry)
                ground_cell.add(gdspy.CellReference(ground_chip_layer))

        self._handle_q_subtract_false(chip_name, chip_layer, ground_cell)
        QGDSRenderer._add_groundcell_to_chip_only_top(lib, chip_only_top,
                                                      ground_cell)

    def _handle_q_subtract_false(self, chip_name: str, chip_layer: int,
                                 ground_cell: gdspy.library.Cell):
        """For each layer, add the subtract=false components to ground.

        Args:
            chip_name (str): Name of chip to render.
            chip_layer (int): Name of layer to render.
            ground_cell (gdspy.library.Cell): The cell in lib to add to.
                                            Cell created for each layer.
        """
        if self.chip_info[chip_name][chip_layer]['q_subtract_false'] is None:
            self.logger.warning(f'There is no table named '
                                f'self.chip_info[{chip_name}][q_subtract_false]'
                                f' to write.')
        else:
            if len(self.chip_info[chip_name][chip_layer]
                   ['q_subtract_false']) != 0:
                ground_cell.add(
                    self.chip_info[chip_name][chip_layer]['q_subtract_false'])

    @classmethod
    def _add_groundcell_to_chip_only_top(cls, lib: gdspy.GdsLibrary,
                                         chip_only_top: gdspy.library.Cell,
                                         ground_cell: gdspy.library.Cell):
        """Add the ground cell to the top of cell for chip.

        Args:
            lib (gdspy.GdsLibrary): Holds all of the chips to export to gds.
            chip_only_top (gdspy.library.Cell): Cell which for a single chip.
            ground_cell (gdspy.library.Cell): The ground cell to add to
                                    chip_only_top. Cell created for each layer.
        """
        # put all cells into TOP_chipname, if not empty.
        # When checking for bounding box, gdspy will return None if empty.

        if ground_cell.get_bounding_box() is not None:
            chip_only_top.add(gdspy.CellReference(ground_cell))
        else:
            lib.remove(ground_cell)

    def _get_linestring_characteristics(
            self, row: 'pd.Pandas') -> Tuple[Tuple, float, float]:
        """Given a row in the Junction table, give the characteristics of
        LineString in row.geometry.

        Args:
            row (pd.Pandas): A row from Junction table of QGeometry.

        Returns:
            Tuple:
            * 1st entry is Tuple[float,float]: The midpoint of Linestring from
            row.geometry in format (x,y).
            * 2nd entry is float: The angle in degrees of Linestring from
            row.geometry.
            * 3rd entry is float: Is the magnitude of Linestring from
            row.geometry.
        """
        precision = float(self.parse_value(self.options.precision))
        for_rounding = int(np.abs(np.log10(precision)))

        [(minx, miny), (maxx, maxy)] = row.geometry.coords[:]

        center = QGDSRenderer._midpoint_xy(minx, miny, maxx, maxy)
        rotation = math.degrees(math.atan2((maxy - miny), (maxx - minx)))
        magnitude = np.round(
            distance.euclidean(row.geometry.coords[0], row.geometry.coords[1]),
            for_rounding)

        return center, rotation, magnitude

    def _give_rotation_center_twopads(
            self, row: 'pd.Pandas', a_cell_bounding_box: 'np.ndarray') -> Tuple:
        """Calculate the angle for rotation, center of LineString in
        row.geometry, and if needed create two pads to connect the junction to
        qubit.

        Args:
            row (pd.Pandas): A row from Junction table of QGeometry.
            a_cell_bounding_box (numpy.ndarray): Give the bounding box of cell
                used in row.gds_cell_name.

        Returns:
            Tuple:
            * 1st entry is float: The angle in degrees of Linestring from
            row.geometry.
            * 2nd entry is Tuple[float,float]: The midpoint of Linestring
            from row.geometry in format (x,y).
            * 3rd entry is gdspy.polygon.Rectangle: None if Magnitude of
            LineString is smaller than width of cell from row.gds_cell_name.
            Otherwise the rectangle for pad on LEFT of row.gds_cell_name.
            * 4th entry is gdspy.polygon.Rectangle: None if Magnitude of
            LineString is smaller than width of cell from row.gds_cell_name.
            Otherwise the rectangle for pad on RIGHT of row.gds_cell_name.
        """
        # pylint: disable=too-many-locals
        junction_pad_overlap = float(
            self.parse_value(self.options.junction_pad_overlap))

        pad_height = row.width
        center, rotation, magnitude = self._get_linestring_characteristics(row)
        [(jj_minx, jj_miny), (jj_maxx, jj_maxy)] = a_cell_bounding_box[0:2]

        pad_left = None
        pad_right = None
        jj_x_width = abs(jj_maxx - jj_minx)
        jj_y_height = abs(jj_maxy - jj_miny)

        #jj_center_x = (jj_x_width / 2) + jj_minx
        jj_center_y = (jj_y_height / 2) + jj_miny

        pad_height = row.width

        if pad_height < jj_y_height:
            # pylint: disable=protected-access
            text_id = self.design._components[row.component]._name
            self.logger.warning(
                f'In junction table, component={text_id} with name={row.name} '
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

    def _import_junction_gds_file(self, lib: gdspy.library,
                                  directory_name: str) -> bool:
        """Import the file which contains all junctions for design.
        If the file has already been imported, just return True.

        When the design has junctions on multiple chips,
        we only need to import file once to get ALL of the junctions.

        Args:
            lib (gdspy.library): The library used to export the entire QDesign.
            directory_name (str): The path of directory to read file with junctions.

        Returns:
            bool: True if file imported to GDS lib or previously imported.
                   False if file not found.
        """

        if self.imported_junction_gds is not None:
            return True

        if os.path.isfile(self.options.path_filename):
            lib.read_gds(self.options.path_filename, units='convert')
            self.imported_junction_gds = self.options.path_filename
            return True
        else:
            message_str = (
                f'Not able to find file:"{self.options.path_filename}".  '
                f'Not used to replace junction.'
                f' Checked directory:"{directory_name}".')
            self.logger.warning(message_str)
            return False

    def _import_junctions_to_one_cell(self, chip_name: str, lib: gdspy.library,
                                      chip_only_top: gdspy.library.Cell,
                                      layers_in_chip: list):
        """Given lib, import the gds file from default options.  Based on the
        cell name in QGeometry table, import the cell from the gds file and
        place it in hierarchy of chip_only_top. In addition, the linestring
        should be two vertexes, and denotes two things.
        1. The midpoint of
        segment is the the center of cell.

        2. The angle made by second tuple - fist tuple  for delta y/ delta x
        is used to rotate the cell.

        Args:
            chip_name (str): The name of chip.
            lib (gdspy.library): The library used to export the entire QDesign.
            chip_only_top (gdspy.library.Cell): The cell used for
                                                just chip_name.
            layers_in_chip (list):  List of all layers in chip.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-nested-blocks

        # Make sure the file exists, before trying to read it.
        dummy_status, directory_name = can_write_to_path(
            self.options.path_filename)
        layers_in_junction_table = set(
            self.chip_info[chip_name]['junction']['layer'])

        if self._import_junction_gds_file(lib=lib,
                                          directory_name=directory_name):

            for iter_layer in layers_in_chip:
                if self._is_negative_mask(chip_name, iter_layer):
                    # Want to export negative mask
                    # Gather the pads into hold_all_pads_cell for same layer.
                    if iter_layer in layers_in_junction_table:
                        chip_only_top_layer_name = f'TOP_{chip_name}_{iter_layer}'
                        if chip_only_top_layer_name in lib.cells.keys():
                            chip_only_top_layer = lib.cells[
                                chip_only_top_layer_name]
                            hold_all_pads_name = f'r_l_hold_all_pads_{iter_layer}'
                            hold_all_pads_cell = lib.new_cell(
                                hold_all_pads_name, overwrite_duplicate=True)
                            chip_only_top_layer.add(
                                gdspy.CellReference(hold_all_pads_cell))

                            # Put all junctions into one cell for same layer.
                            hold_all_jj_cell_name = f'all_jj_imported_{iter_layer}'
                            hold_all_jj_cell = lib.new_cell(
                                hold_all_jj_cell_name, overwrite_duplicate=True)

                            self._add_negative_extension_to_jj(
                                chip_name, iter_layer, lib, chip_only_top,
                                chip_only_top_layer, hold_all_pads_cell,
                                hold_all_jj_cell)
                else:
                    # By default, make a positive mask.
                    for row in self.chip_info[chip_name]['junction'].itertuples(
                    ):
                        chip_layer = int(row.layer)
                        ground_cell_name = f'TOP_{chip_name}_{chip_layer}'

                        if ground_cell_name in lib.cells.keys(
                        ) and chip_layer == iter_layer:
                            chip_layer_cell = lib.cells[ground_cell_name]

                            if row.gds_cell_name in lib.cells.keys():
                                # When positive mask, just add the pads to chip_only_top
                                self._add_positive_extension_to_jj(
                                    lib, row, chip_layer_cell)
                            else:
                                self.logger.warning(
                                    f'From the "junction" table, the cell named'
                                    f' "{row.gds_cell_name}"",  is not in '
                                    f'file: {self.options.path_filename}.'
                                    f' The cell was not used.')

    def _add_negative_extension_to_jj(self, chip_name: str, jj_layer: int,
                                      lib: gdspy.library,
                                      chip_only_top: gdspy.library.Cell,
                                      chip_only_top_layer: gdspy.library.Cell,
                                      hold_all_pads_cell: gdspy.library.Cell,
                                      hold_all_jj_cell: gdspy.library.Cell):
        """Manipulate existing geometries for the layer that the junctions need
         to be added.  Since boolean subtraction is computationally intensive,
         the method will gather the pads for a layer, and do the boolean just
         once. Then add the junctions to difference.

        Args:
            chip_name (str): The name of chip.
            jj_layer (int): The layer the
            lib (gdspy.library): The library used to export the entire QDesign.
            chip_only_top (gdspy.library.Cell): The cell used for
                                                just chip_name.
            chip_only_top_layer (gdspy.library.Cell): Cell under chip,
                                                    with specific layer.
            hold_all_pads_cell (gdspy.library.Cell): Collect all the pads with movement.
            hold_all_jj_cell (gdspy.library.Cell): Collect all the jj's with movement.
        """

        boolean_by_layer = self.chip_info[chip_name]['junction'][
            'layer'] == jj_layer
        for row in self.chip_info[chip_name]['junction'][
                boolean_by_layer].itertuples():

            if row.gds_cell_name in lib.cells.keys():
                # For negative mask, collect the pads to subtract per layer,
                # and subtract from chip_only_top_layer
                self._gather_negative_extension_for_jj(lib, row,
                                                       hold_all_pads_cell,
                                                       hold_all_jj_cell)
            else:
                self.logger.warning(
                    f'From the "junction" table, the cell named'
                    f' "{row.gds_cell_name}",  is not in file: '
                    f'{self.options.path_filename}. The cell was not used.')

        diff_r_l_pads_name = f'r_l_pads_diff_{jj_layer}'
        diff_pad_cell_layer = lib.new_cell(diff_r_l_pads_name,
                                           overwrite_duplicate=True)
        #chip_only_top_layer.add(gdspy.CellReference(diff_pad_cell_layer))
        chip_only_top.add(gdspy.CellReference(diff_pad_cell_layer))

        precision = self.parse_value(self.options.precision)
        max_points = int(self.parse_value(self.options.max_points))

        # Make sure  the pads to hold_all_pads_cell is not empty

        if chip_only_top_layer.get_bounding_box() is not None:
            jj_minus_pads = gdspy.boolean(chip_only_top_layer.get_polygons(),
                                          hold_all_pads_cell.get_polygons(),
                                          'not',
                                          max_points=max_points,
                                          precision=precision)
            diff_pad_cell_layer.add(jj_minus_pads)
        if hold_all_jj_cell.get_bounding_box() is not None:
            diff_pad_cell_layer.add(gdspy.CellReference(hold_all_jj_cell))

        self._clean_hierarchy(lib, chip_only_top, chip_only_top_layer,
                              diff_pad_cell_layer, hold_all_pads_cell)

    @classmethod
    def _clean_hierarchy(cls, lib, chip_only_top, chip_only_top_layer,
                         diff_pad_cell_layer, hold_all_pads_cell):
        """Delete cell that doesn't have pad nor jjs.  Then use same
        name for correct cell.  Also, get rid of cell that had the pads
        since subtraction happened and we don't need it any more.

        Args:
            lib (gdspy.library): [The library used to export the entire QDesign.
            chip_only_top (gdspy.library.Cell): [description]
            chip_only_top_layer (gdspy.library.Cell): Cell under chip,
                                        with specific layer.
            diff_pad_cell_layer (gdspy.library.Cell): Holds result of top_layer - pads + jjs.
            hold_all_pads_cell (gdspy.library.Cell): Collect all the jj's with movement.
        """
        hold_name = chip_only_top_layer.name
        lib.remove(hold_name)
        lib.rename_cell(diff_pad_cell_layer, hold_name)

        #Add to hierarchy only if cell is not empty.
        if diff_pad_cell_layer.get_bounding_box() is not None:
            chip_only_top.add(gdspy.CellReference(diff_pad_cell_layer))
        else:
            lib.remove(diff_pad_cell_layer)
        # remove the sub libs before removing hold_all_pads_cells
        for _, value in enumerate(hold_all_pads_cell.references):
            lib.remove(value.ref_cell.name)
        lib.remove(hold_all_pads_cell)

    def _gather_negative_extension_for_jj(
            self, lib: gdspy.library, row: 'pd.core.frame.Pandas',
            hold_all_pads_cell: gdspy.library.Cell,
            hold_all_jj_cell: gdspy.library.Cell):
        """Gather the pads and jjs and put them in separate cells.  The
        the pads can be boolean'd 'not' just once. After boolean for pads, then
        the jjs will be added to result.  The boolean is very
        time intensive, so just want to do it once.

        Args:
            lib (gdspy.library): The library used to export the entire QDesign.
            row (pd.core.frame.Pandas): Each row is from the qgeometry junction table.
            hold_all_pads_cell (gdspy.library.Cell): Collect all the pads with movement.
            hold_all_jj_cell (gdspy.library.Cell): Collect all the jj's with movement.
        """

        a_cell = lib.extract(row.gds_cell_name)
        a_cell_bounding_box = a_cell.get_bounding_box()

        rotation, center, pad_left, pad_right = self._give_rotation_center_twopads(
            row, a_cell_bounding_box)

        # String for JJ combined with pad Right and pad Left
        jj_pad_r_l_name = f'{row.gds_cell_name}_QComponent_is_{row.component}_Name_is_{row.name}_name_is_{row.name}'
        temp_cell = lib.new_cell(jj_pad_r_l_name, overwrite_duplicate=True)

        if pad_left is not None:
            temp_cell.add(pad_left)
        if pad_right is not None:
            temp_cell.add(pad_right)

        hold_all_jj_cell.add(
            gdspy.CellReference(a_cell, origin=center, rotation=rotation))
        hold_all_pads_cell.add(
            gdspy.CellReference(temp_cell, origin=center, rotation=rotation))

    def _add_positive_extension_to_jj(self, lib: gdspy.library,
                                      row: 'pd.core.frame.Pandas',
                                      chip_only_top_layer: gdspy.library.Cell):
        """Get the extension pads, then add or subtract to extracted cell based on
        positive or negative mask.

        Args:
            lib (gdspy.library): The library used to export the entire QDesign.
            row (pd.core.frame.Pandas): Each row is from the qgeometry
                                            junction table.
            chip_only_top_layer (gdspy.library.Cell): The cell used for
                                            chip_name and layer_num.
        """
        a_cell = lib.extract(row.gds_cell_name)
        a_cell_bounding_box = a_cell.get_bounding_box()

        rotation, center, pad_left, pad_right = self._give_rotation_center_twopads(
            row, a_cell_bounding_box)

        # String for JJ combined with pad Right and pad Left
        jj_pad_r_l_name = f'pads_{row.gds_cell_name}_QComponent_is_{row.component}_name_is_{row.name}'
        temp_cell = lib.new_cell(jj_pad_r_l_name, overwrite_duplicate=True)
        chip_only_top_layer.add(
            gdspy.CellReference(a_cell, origin=center, rotation=rotation))

        if pad_left is not None:
            # chip_only_top_layer.add(
            #     gdspy.CellReference(pad_left, origin=center, rotation=rotation))

            temp_cell.add(pad_left)

        if pad_right is not None:
            # chip_only_top_layer.add(
            #     gdspy.CellReference(pad_right, origin=center,
            #                         rotation=rotation))

            temp_cell.add(pad_right)

        # "temp_cell" is kept in the lib.
        if temp_cell.get_bounding_box() is not None:
            chip_only_top_layer.add(
                gdspy.CellReference(temp_cell, origin=center,
                                    rotation=rotation))
        else:
            lib.remove(temp_cell)

    def export_to_gds(self,
                      file_name: str,
                      highlight_qcomponents: list = None) -> int:
        """Use the design which was used to initialize this class. The
        QGeometry element types of both "path" and "poly", will be used, to
        convert QGeometry to GDS formatted file.

        Args:
            file_name (str): File name which can also include directory path.
                             If the file exists, it will be overwritten.
            highlight_qcomponents (list): List of strings which denote
                                        the name of QComponents to render.
                                        If empty, render all components in design.

        Returns:
            int: 0=file_name can not be written, otherwise 1=file_name has been written
        """
        if highlight_qcomponents is None:
            highlight_qcomponents = []

        if not self._can_write_to_path(file_name):
            return 0

        # There can be more than one chip in QGeometry.
        # They all export to one gds file.
        # Each chip will hold the rectangle for subtract for each layer so:
        # chip_info[chip_name][subtract_box][(min_x,min_y,max_x,max_y)]
        # chip_info[chip_name][layer_number][all_subtract_elements]
        # chip_info[chip_name][layer_number][all_no_subtract_elements]
        self.chip_info.clear()
        self.chip_info.update(self._get_chip_names())

        # if imported, hold the path to file name, otherwise None.
        self.imported_junction_gds = None

        if self._create_qgeometry_for_gds(highlight_qcomponents) == 0:
            # Create self.lib and populate path and poly.
            self._populate_poly_path_for_export()

            # Adds airbridges to CPWs w/ options.gds_make_airbridge = True
            # Options for these airbridges are in self.options.airbridge
            self._populate_airbridge()

            # Add no-cheese MultiPolygon to
            # self.chip_info[chip_name][chip_layer]['no_cheese'],
            # if self.options requests the layer.
            self._populate_no_cheese()

            # Use self.options  to decide what to put for export
            # into self.chip_info[chip_name][chip_layer]['cheese'].
            # Not finished.
            self._populate_cheese()

            # Export the file to disk from self.lib
            self.lib.write_gds(file_name)

            return 1

        return 0

    def _multipolygon_to_gds(
            self, multi_poly: shapely.geometry.multipolygon.MultiPolygon,
            layer: int, data_type: int, no_cheese_buffer: float) -> list:
        """Convert a shapely MultiPolygon to corresponding gdspy.

        Args:
            multi_poly (shapely.geometry.multipolygon.MultiPolygon): The
                                shapely geometry of no-cheese boundary.
            layer (int): The layer of the input multipolygon.
            data_type (int): Used as a "sub-layer" to place the no-cheese
                                gdspy output.
            no_cheese_buffer (float): Used for both fillet and buffer size.

        Returns:
            list: Each entry is converted to GDSII.
        """
        # pylint: disable=too-many-locals

        dummy_keep_for_future_use = no_cheese_buffer
        precision = self.parse_value(self.options.precision)
        max_points = int(self.parse_value(self.options.max_points))

        all_polys = list(multi_poly.geoms)
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
                # Poly fracturing leading to a funny shape. Leave this out of gds output for now.
                # a_poly.fillet(no_cheese_buffer,
                #               points_per_2pi=128,
                #               max_points=max_points,
                #               precision=precision)
                all_gds.append(a_poly)
            else:
                # Poly fracturing leading to a funny shape. Leave this out of gds output for now.
                # exterior_poly.fillet(no_cheese_buffer,
                #                      points_per_2pi=128,
                #                      max_points=max_points,
                #                      precision=precision)
                all_gds.append(exterior_poly)
        return all_gds

    def _qgeometry_to_gds(
        self, qgeometry_element: pd.Series
    ) -> Union['gdspy.polygon', 'gdspy.FlexPath', None]:
        """Convert the design.qgeometry table to format used by GDS renderer.
        Convert the class to a series of GDSII elements.

        Args:
            qgeometry_element (pd.Series): Expect a shapely object.

        Returns:
            Union['gdspy.polygon' or 'gdspy.FlexPath' or None]: Convert the
            class to a series of GDSII format on the input pd.Series.


        *NOTE:*
        GDS:
            points (array-like[N][2]) – Coordinates of the vertices of
                                        the polygon.
            layer (integer) – The GDSII layer number for this
                                        qgeometry_element.
            datatype (integer) – The GDSII datatype for this qgeometry_element
                                (between 0 and 255).
                                datatype=10 or 11 means only that they are
                                from a Polygon vs. LineString.
                                This can be changed.

        See:
            https://gdspy.readthedocs.io/en/stable/reference.html#polygon
        """

        # pylint: disable=too-many-locals

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
                                       precision=precision,
                                       layer=qgeometry_element.layer,
                                       datatype=10)
                return a_poly

            exterior_poly = exterior_poly.fracture(max_points=max_points,
                                                   precision=precision)
            return exterior_poly
        if isinstance(geom, shapely.geometry.LineString):
            #class gdspy.FlexPath(points, width, offset=0, corners='natural',
            #ends='flush', bend_radius=None, tolerance=0.01, precision=0.001,
            #max_points=199, gdsii_path=False, width_transform=True, layer=0,
            #datatype=0)

            #Only fillet, if number is greater than zero.

            use_width = self.parse_value(self.options.width_LineString)

            if math.isnan(qgeometry_element.width):
                qcomponent_id = self.parse_value(qgeometry_element.component)
                name = self.parse_value(qgeometry_element['name'])
                layer_num = self.parse_value(qgeometry_element.layer)
                width = self.parse_value(qgeometry_element.width)
                self.logger.warning(
                    f'Since width:{width} for a Path is not a number, '
                    f'it will be exported using width_LineString:'
                    f' {use_width}.  The component_id is:{qcomponent_id},'
                    f' name is:{name}, layer is: {layer_num}')
            else:
                use_width = qgeometry_element.width

            if 'fillet' in qgeometry_element:

                if (math.isnan(qgeometry_element.fillet) or
                        qgeometry_element.fillet <= 0 or
                        qgeometry_element.fillet < qgeometry_element.width):

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

            # Could be junction table with a linestring.
            # Look for gds_path_filename in column.
            self.logger.warning(f'Linestring did not have fillet in column. '
                                f'The qgeometry_element was not drawn.\n'
                                f'The qgeometry_element within table is:\n'
                                f'{qgeometry_element}')
            return None  # Need explicitly to avoid lint warnings.

        self.logger.warning(
            f'Unexpected shapely object geometry.'
            f'The variable qgeometry_element is {type(geom)}, '
            f'method can currently handle Polygon and FlexPath.')
        return None

    def _get_chip_names(self) -> Dict:
        """Returns a dict of unique chip names for ALL tables within QGeometry.
        In another words, for every "path" table, "poly" table ... etc, this
        method will search for unique chip names and return a dict of unique
        chip names from QGeometry table.

        Returns:
            Dict: dict with key of chip names and value of empty
            dict to hold things for renderers.
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
