# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

'''
@date: 2020
@author: Dennis Wang, Zlatko Minev
'''

from typing import List, Tuple, Union

import re
import math
import geopandas
import numpy as np
import pandas as pd
from numpy.linalg import norm
from collections import defaultdict

import shapely
import pyEPR as epr
from pyEPR.ansys import parse_units # TODO: Check this works with design UNITS

from qiskit_metal.draw.utility import to_vec3D
from qiskit_metal.draw.basic import is_rectangle
from qiskit_metal.renderers.renderer_base import QRenderer
from qiskit_metal.toolbox_python.utility_functions import toggle_numbers, bad_fillet_idxs

from qiskit_metal import Dict

def good_fillet_idxs(coords: list, fradius: float, precision: int = 9, isclosed: bool = False):
    """
    Get list of vertex indices in a linestring (isclosed = False) or polygon (isclosed = True) that can be filleted based on
    proximity to neighbors.

    Args:
        coords (list): Ordered list of tuples of vertex coordinates.
        fradius (float): User-specified fillet radius from QGeometry table.
        precision (int, optional): Digits of precision used for round(). Defaults to 9.
        isclosed (bool, optional): Boolean denoting whether the shape is a linestring or polygon. Defaults to False.

    Returns:
        list: List of indices of vertices that can be filleted.
    """
    if isclosed:
        return toggle_numbers(bad_fillet_idxs(coords, fradius, precision, isclosed = True), len(coords))
    return toggle_numbers(bad_fillet_idxs(coords, fradius, precision, isclosed = False), len(coords))[1:-1]

def get_clean_name(name: str) -> str:
    """
    Create a valid variable name from the given one by removing having it begin with a letter or underscore
    followed by an unlimited string of letters, numbers, and underscores.

    Args:
        name (str): Initial, possibly unusable, string to be modified.

    Returns:
        str: Variable name consistent with Python naming conventions.
    """
    # Remove invalid characters
    name = re.sub('[^0-9a-zA-Z_]', '', name)
    # Remove leading characters until we find a letter or underscore
    name = re.sub('^[^a-zA-Z_]+', '', name)
    return name

class QAnsysRenderer(QRenderer):
    """
    Extends QRenderer to export designs to Ansys using pyEPR.
    The methods which a user will need for Ansys export should be found within this class.
    """

    #: Default options, over-written by passing ``options` dict to render_options.
    #: Type: Dict[str, str]
    default_options = Dict(
        # Maximum mesh length for Josephson junction elements
        max_mesh_length_jj='7um',
        Lj=10, # Lj has units of nanoHenries (nH)
        Cj=0, # Cj *must* be 0 for pyEPR analysis! Cj has units of femtofarads (fF)
        _Rj=0) # _Rj *must* be 0 for pyEPR analysis! _Rj has units of Ohms

    NAME_DELIM = r'_'

    name = 'ansys'
    """name"""

    # When additional columns are added to QGeometry, this is the example to populate it.
    # e.g. element_extensions = dict(
    #         base=dict(color=str, klayer=int),
    #         path=dict(thickness=float, material=str, perfectE=bool),
    #         poly=dict(thickness=float, material=str), )
    """element extensions dictionary   element_extensions = dict() from base class"""

    # Add columns to junction table during QAnsysRenderer.load()
    # element_extensions  is now being populated as part of load().
    # Determined from element_table_data.

    # Dict structure MUST be same as  element_extensions!!!!!!
    # This dict will be used to update QDesign during init of renderer.
    # Keeping this as a cls dict so could be edited before renderer is instantiated.
    # To update component.options junction table.

    element_table_data = dict(
        junction=dict(inductance=default_options['Lj'],
                      capacitance=default_options['Cj'],
                      resistance=default_options['_Rj'],
                      mesh_kw_jj=parse_units(default_options['max_mesh_length_jj']))
    )

    def __init__(self, design: 'QDesign', initiate=True, render_template: Dict = None, render_options: Dict = None):
        """
        Create a QRenderer for Ansys.

        Args:
            design (QDesign): Use QGeometry within QDesign to obtain elements for Ansys.
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
            render_template (Dict, optional): Typically used by GUI for template options for GDS. Defaults to None.
            render_options (Dict, optional):  Used to override all options. Defaults to None.
        """
        super().__init__(design=design, initiate=initiate,
                         render_template=render_template, render_options=render_options)
        QAnsysRenderer.load()

    @property
    def open_ansys_design(self):
        """
        Create new project and design in Ansys.
        """
        self.pinfo = epr.ProjectInfo(project_path=None, project_name=None, design_name=None)
        self.modeler = self.pinfo.design.modeler

    def add_message(self, msg: str, severity: int=0):
        """
        Add message to Message Manager box in Ansys.

        Args:
            msg (str): Message to add.
            severity (int): 0 = Informational, 1 = Warning, 2 = Error, 3 = Fatal.
        """
        self.pinfo.design.add_message(msg, severity)

    def render_design(self, selection: Union[list, None] = None):
        """
        Initiate rendering of components in design contained in selection, assuming they're valid.
        Components are rendered before the chips they reside on, and subtraction of negative shapes
        is performed at the very end. Chip_subtract_dict consists of component names (keys) and
        a set of all elements within each component that will be eventually be subtracted from the
        ground plane. All components are rendered by default if selection is empty or not specified.

        Args:
            selection (Union[list, None], optional): List of components to render. Defaults to None.
        """

        self.chip_subtract_dict = defaultdict(set) # TODO: address warning
        self.assign_perfE = []
        self.render_tables(selection)
        self.render_chips()
        self.subtract_from_ground()
        self.metallize()

    def render_tables(self, selection: Union[list, None] = None): #  # TODO: address warning
        """
        Render components in design grouped by table type (path, poly, or junction).

        Args:
            selection (Union[list, None], optional): List of components to render. Defaults to None.
        """

        for table_type in self.design.qgeometry.get_element_types():
            self.render_components(table_type, selection)

    def render_components(self, table_type: str, selection: Union[list, None] = None): # TODO: address warning
        """
        Render individual components by breaking them down into individual elements.

        Args:
            table_type (str): Table type (poly, path, or junction).
            selection (Union[list, None], optional): List of components to render. Defaults to None.
        """

        selection = selection if selection else []
        table = self.design.qgeometry.tables[table_type]

        if selection:
            qcomp_ids, case = self.get_unique_component_ids(selection)
            if case != 1:  # Render a subset of components using mask
                mask = table['component'].isin(qcomp_ids)
                table = table[mask]

        for _, qgeom in table.iterrows():
            self.render_element(qgeom, bool(table_type == 'junction'))

    def render_element(self, qgeom: pd.Series, is_junction: bool):
        """
        Render an individual shape whose properties are listed in a row of QGeometry table.
        Junction elements are handled separately from non-junction elements, as the former
        consist of two rendered shapes, not just one.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
            is_junction (bool): Whether or not qgeom belongs to junction table.
        """

        qc_shapely = qgeom.geometry
        if is_junction:
            self.render_element_junction(qgeom)
        else:
            if isinstance(qc_shapely, shapely.geometry.Polygon):
                self.render_element_poly(qgeom)
            elif isinstance(qc_shapely, shapely.geometry.LineString):
                self.render_element_path(qgeom)

    def render_element_junction(self, qgeom: pd.Series):
        """
        Render a Josephson junction consisting of
        1. A rectangle of length pad_gap and width inductor_width. Defines lumped element
           RLC boundary condition.
        2. A line that is later used to calculate the voltage in post-processing analysis.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """

        ansys_options = dict(transparency=0.0)

        qc_name = 'Lj_' + str(qgeom['component'])
        qc_elt = get_clean_name(qgeom['name'])
        qc_shapely = qgeom.geometry
        qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))
        qc_width = parse_units(qgeom.width)

        name = f'{qc_name}{QAnsysRenderer.NAME_DELIM}{qc_elt}'

        endpoints = parse_units(list(qc_shapely.coords))
        endpoints_3d = to_vec3D(endpoints, qc_chip_z)
        x0, y0, z0 = endpoints_3d[0]
        x1, y1, z0 = endpoints_3d[1]
        if abs(y1 - y0) > abs(x1 - x0):
            # Junction runs vertically up/down
            points_3d = np.array([[x0 - qc_width / 2, y0, z0],
                                  [x0 - qc_width / 2, y1, z0],
                                  [x0 + qc_width / 2, y1, z0],
                                  [x0 + qc_width / 2, y0, z0],
                                  [x0 - qc_width / 2, y0, z0]])
            x_min, x_max = x0 - qc_width / 2, x0 + qc_width / 2
            y_min, y_max = min(y0, y1), max(y0, y1)
        else:
            # Junction runs horizontally left/right
            points_3d = np.array([[x0, y0 - qc_width / 2, z0],
                                  [x0, y0 + qc_width / 2, z0],
                                  [x1, y0 + qc_width / 2, z0],
                                  [x1, y0 - qc_width / 2, z0],
                                  [x0, y0 - qc_width / 2, z0]])
            x_min, x_max = min(x0, x1), max(x0, x1)
            y_min, y_max = y0 - qc_width / 2, y0 + qc_width / 2

        # Draw rectangle
        self.logger.debug(f'Drawing a rectangle: {name}')
        poly_ansys = self.modeler.draw_rect_corner(
            [x_min, y_min, qc_chip_z], x_max - x_min, y_max - y_min, qc_chip_z, **ansys_options)
        axis = int(self.design._components[qgeom['component']].options.orientation)
        axis = {0: 'y', 90: 'x', 180: 'y', 270: 'x'}.get(axis, axis)
        axis = axis.lower()
        poly_ansys.make_rlc_boundary(axis,
                                     l=qgeom['ansys_inductance'],
                                     c=qgeom['ansys_capacitance'],
                                     r=qgeom['ansys_resistance'],
                                     name='Lj_' + name)

        # Draw line
        start, end = poly_ansys.make_center_line(axis)
        poly_jj = self.modeler.draw_polyline([start, end], closed=False, **dict(color=(128, 0, 128)))
        poly_jj = poly_jj.rename('JJ_' + name + '_')
        poly_jj.show_direction = True

    def render_element_poly(self, qgeom: pd.Series):
        """
        Render a closed polygon.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """

        ansys_options = dict(transparency=0.0)

        qc_name = 'Q' + str(qgeom['component']) # name of QComponent
        qc_elt = get_clean_name(qgeom['name']) # name of element within QGeometry table
        qc_shapely = qgeom.geometry  # shapely geom
        qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))
        qc_fillet = round(qgeom.fillet, 7)

        name = f'{qc_name}{QAnsysRenderer.NAME_DELIM}{qc_elt}'

        points = parse_units(list(qc_shapely.exterior.coords))  # list of 2d point tuples
        points_3d = to_vec3D(points, qc_chip_z)

        if is_rectangle(qc_shapely):  # Draw as rectangle
            self.logger.debug(f'Drawing a rectangle: {name}')
            x_min, y_min, x_max, y_max = qc_shapely.bounds
            poly_ansys = self.modeler.draw_rect_corner(*parse_units(
                [[x_min, y_min, qc_chip_z], x_max - x_min, y_max - y_min, qc_chip_z]), **ansys_options)
            self.modeler.rename_obj(poly_ansys, name)

        else:
            # Draw general closed poly
            poly_ansys = self.modeler.draw_polyline(points_3d[:-1], closed=True, **ansys_options)
            # rename: handle bug if the name of the cut already exits and is used to make a cut
            poly_ansys = poly_ansys.rename(name)

        qc_fillet = round(qgeom.fillet, 7)
        if qc_fillet > 0:
            qc_fillet = parse_units(qc_fillet)
            idxs_to_fillet = good_fillet_idxs(points,
                                             qc_fillet,
                                             precision=self.design._template_options.PRECISION,
                                             isclosed=True)
            if idxs_to_fillet:
                self.modeler._fillet(qc_fillet, idxs_to_fillet, poly_ansys)

        # Subtract interior shapes, if any
        if len(qc_shapely.interiors) > 0:
            for i, x in enumerate(qc_shapely.interiors):
                interior_points_3d = to_vec3D(parse_units(list(x.coords)), qc_chip_z)
                inner_shape = self.modeler.draw_polyline(interior_points_3d[:-1], closed=True)
                self.modeler.subtract(name, [inner_shape])

        # Input chip info into self.chip_subtract_dict
        if qgeom.chip not in self.chip_subtract_dict:
            self.chip_subtract_dict[qgeom.chip] = set()

        if qgeom['subtract']:
            self.chip_subtract_dict[qgeom.chip].add(name)

        # Potentially add to list of elements to metallize
        elif not qgeom['helper']:
            self.assign_perfE.append(name)

    def render_element_path(self, qgeom: pd.Series):
        """
        Render a path-type element.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """

        ansys_options = dict(transparency=0.0)

        qc_name = 'Q' + str(qgeom['component']) # name of QComponent
        qc_elt = get_clean_name(qgeom['name']) # name of element within QGeometry table
        qc_shapely = qgeom.geometry  # shapely geom
        qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))

        name = f'{qc_name}{QAnsysRenderer.NAME_DELIM}{qc_elt}'

        qc_width = parse_units(qgeom.width)

        points = parse_units(list(qc_shapely.coords))
        points_3d = to_vec3D(points, qc_chip_z)

        poly_ansys = self.modeler.draw_polyline(points_3d, closed=False, **ansys_options)
        poly_ansys = poly_ansys.rename(name)

        qc_fillet = round(qgeom.fillet, 7)
        if qc_fillet > 0:
            qc_fillet = parse_units(qc_fillet)
            idxs_to_fillet = good_fillet_idxs(points,
                                            qc_fillet,
                                            precision=self.design._template_options.PRECISION,
                                            isclosed=False)
            if idxs_to_fillet:
                self.modeler._fillet(qc_fillet, idxs_to_fillet, poly_ansys)

        if qc_width:
            x0, y0 = points[0]
            x1, y1 = points[1]
            vlen = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            p0 = np.array([x0, y0, 0]) + qc_width / (2 * vlen) * np.array([y0 - y1, x1 - x0, 0])
            p1 = np.array([x0, y0, 0]) + qc_width / (2 * vlen) * np.array([y1 - y0, x0 - x1, 0])
            shortline = self.modeler.draw_polyline([p0, p1], closed=False)  # sweepline
            self.modeler._sweep_along_path(shortline, poly_ansys)

        if qgeom.chip not in self.chip_subtract_dict:
            self.chip_subtract_dict[qgeom.chip] = set()

        if qgeom['subtract']:
            self.chip_subtract_dict[qgeom.chip].add(name)

        elif qgeom['width'] and (not qgeom['helper']):
            self.assign_perfE.append(name)

    def render_chips(self):
        """
        Render chips using info from design.get_chip_size method.

        Renders the ground plane of this chip (if one is present).
        Renders the wafer of the chip.
        """

        ansys_options = dict(transparency=0.0)

        for chip_name in self.chip_subtract_dict:
            ops = self.design._chips[chip_name]
            p = self.design.get_chip_size(chip_name)
            origin = parse_units([p['center_x'], p['center_y'], p['center_z']])
            size = parse_units([p['size_x'], p['size_y'], p['size_z']])
            vac_height = parse_units([p['sample_holder_top'], p['sample_holder_bottom']])
            if chip_name == 'main': # Create only a single vacuum box, centered around 'main' chip
                vacuum_box = self.modeler.draw_box_center([origin[0], origin[1], (vac_height[0] - vac_height[1]) / 2],
                                                        [size[0], size[1], sum(vac_height)],
                                                        name='sample_holder')
            plane = self.modeler.draw_rect_center(origin, x_size=size[0], y_size=size[1], name=f'{chip_name}_plane', **ansys_options)
            if self.chip_subtract_dict[chip_name]: # Any layer which has subtract=True qgeometries will have a ground plane
                self.assign_perfE.append(f'{chip_name}_plane')
            # if self.chip_subtract_dict[chip_name]:
            #     ground_plane = self.modeler.draw_rect_center(origin, x_size=size[0], y_size=size[1], name=f'{chip_name}_ground', **ansys_options)
            whole_chip = self.modeler.draw_box_center([origin[0], origin[1], size[2] / 2],
                                                 [size[0], size[1], -size[2]],
                                                 name=chip_name,
                                                 material=ops['material'],
                                                 color=(186, 186, 205),
                                                 transparency=0.2,
                                                 wireframe=False)

    def subtract_from_ground(self):
        """
        For each chip, subtract all "negative" shapes residing on its surface if any such shapes exist.
        """

        for chip, shapes in self.chip_subtract_dict.items():
            if shapes:
                self.modeler.subtract(chip + '_plane', list(shapes))

    def metallize(self):
        """
        Assign metallic property to all shapes in self.assign_perfE list.
        """
        self.modeler.assign_perfect_E(self.assign_perfE)
