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
from pathlib import Path
import math
import geopandas
import numpy as np
import pandas as pd
from numpy.linalg import norm
from collections import defaultdict

import shapely
import pyEPR as epr
from pyEPR.ansys import parse_units

from qiskit_metal.draw.utility import to_vec3D
from qiskit_metal.draw.basic import is_rectangle
from qiskit_metal.renderers.renderer_base import QRenderer
from qiskit_metal.toolbox_python.utility_functions import toggle_numbers, bad_fillet_idxs

from qiskit_metal import Dict


def good_fillet_idxs(coords: list,
                     fradius: float,
                     precision: int = 9,
                     isclosed: bool = False):
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
        return toggle_numbers(
            bad_fillet_idxs(coords, fradius, precision, isclosed=True),
            len(coords))
    return toggle_numbers(
        bad_fillet_idxs(coords, fradius, precision, isclosed=False),
        len(coords))[1:-1]


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
        Lj='10nH',  # Lj has units of nanoHenries (nH)
        Cj=
        0,  # Cj *must* be 0 for pyEPR analysis! Cj has units of femtofarads (fF)
        _Rj=0,  # _Rj *must* be 0 for pyEPR analysis! _Rj has units of Ohms
        max_mesh_length_jj=
        '7um',  # maximum mesh length for Josephson junction elements
        project_path=None,  # default project path; if None --> get active
        project_name=None,  # default project name
        design_name=None,  # default design name
        ansys_file_extension=
        '.aedt',  # Ansys file extension for 2016 version and newer
        bounding_box_scale_x=
        1.2,  # Ratio of 'main' chip width to bounding box width
        bounding_box_scale_y=
        1.2  # Ratio of 'main' chip length to bounding box length 
    )

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

    element_table_data = dict(junction=dict(
        inductance=default_options['Lj'],
        capacitance=default_options['Cj'],
        resistance=default_options['_Rj'],
        mesh_kw_jj=parse_units(default_options['max_mesh_length_jj'])))

    def __init__(self,
                 design: 'QDesign',
                 initiate=True,
                 render_template: Dict = None,
                 render_options: Dict = None):
        """
        Create a QRenderer for Ansys.

        Args:
            design (QDesign): Use QGeometry within QDesign to obtain elements for Ansys.
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
            render_template (Dict, optional): Typically used by GUI for template options for GDS. Defaults to None.
            render_options (Dict, optional):  Used to override all options. Defaults to None.
        """
        super().__init__(design=design,
                         initiate=initiate,
                         render_template=render_template,
                         render_options=render_options)

        # Default behavior is to render all components unless a strict subset was chosen
        self.render_everything = True

        self.pinfo = None

    def open_ansys_design(self):
        """
        Open new project and design in Ansys.
        """
        import pythoncom
        try:
            self.pinfo = epr.ProjectInfo(
                project_path=self._options['project_path'],
                project_name=self._options['project_name'],
                design_name=self._options['design_name'])
        except pythoncom.com_error as error:
            print("com_error: ", error)
            hr, msg, exc, arg = error.args
            if msg == "Invalid class string":  # and hr == -2147221005 and exc is None and arg is None
                print(
                    "pyEPR cannot find the Ansys COM. Ansys installation might not have registered it. "
                    "To verify if this is the problem, execute the following: ",
                    "`print(win32com.client.Dispatch('AnsoftHfss.HfssScriptInterface'))` ",
                    "If the print-out is not `<COMObject ...>` then Ansys COM is not registered, ",
                    "and you will need to look into correcting your Ansys installation."
                )
            raise error

    @property
    def modeler(self):
        if self.pinfo:
            if self.pinfo.design:
                return self.pinfo.design.modeler

    def add_message(self, msg: str, severity: int = 0):
        """
        Add message to Message Manager box in Ansys.

        Args:
            msg (str): Message to add.
            severity (int): 0 = Informational, 1 = Warning, 2 = Error, 3 = Fatal.
        """
        self.pinfo.design.add_message(msg, severity)

    def render_design(self,
                      selection: Union[list, None] = None,
                      open_pins: Union[list, None] = None):
        """
        Initiate rendering of components in design contained in selection, assuming they're valid.
        Components are rendered before the chips they reside on, and subtraction of negative shapes
        is performed at the very end.

        Chip_subtract_dict consists of component names (keys) and a set of all elements within each component that
        will eventually be subtracted from the ground plane. Add objects that are perfect conductors and/or have
        meshing to self.assign_perfE and self.assign_mesh, respectively; both are initialized as empty lists. Note
        that these objects are "refreshed" each time render_design is called (as opposed to in the init function)
        to clear QAnsysRenderer of any leftover items from the last call to render_design.

        Among the components selected for export, there may or may not be unused (unconnected) pins.
        The second parameter, open_pins, contains tuples of the form (component_name, pin_name) that
        specify exactly which pins should be open rather than shorted during the simulation. Both the
        component and pin name must be specified because the latter could be shared by multiple
        components. All pins in this list are rendered with an additional endcap in the form of a
        rectangular cutout, to be subtracted from its respective plane.

        Args:
            selection (Union[list, None], optional): List of components to render. Defaults to None.
            open_pins (Union[list, None], optional): List of tuples of pins that are open. Defaults to None.
        """
        self.chip_subtract_dict = defaultdict(set)
        self.assign_perfE = []
        self.assign_mesh = []

        self.render_tables(selection)
        self.add_endcaps(open_pins)

        self.render_chips()
        self.subtract_from_ground()
        self.add_mesh()

    def render_tables(self, selection: Union[list, None] = None):
        """
        Render components in design grouped by table type (path, poly, or junction).

        Args:
            selection (Union[list, None], optional): List of components to render. Defaults to None.
        """
        for table_type in self.design.qgeometry.get_element_types():
            self.render_components(table_type, selection)

    def render_components(self,
                          table_type: str,
                          selection: Union[list, None] = None):
        """
        Render individual components by breaking them down into individual elements.

        Args:
            table_type (str): Table type (poly, path, or junction).
            selection (Union[list, None], optional): List of components to render. Defaults to None.
        """
        # Establish bounds for exported components and update these accordingly

        selection = selection if selection else []
        table = self.design.qgeometry.tables[table_type]

        self.min_x_main = float('inf')
        self.min_y_main = float('inf')
        self.max_x_main = float('-inf')
        self.max_y_main = float('-inf')

        if selection:
            qcomp_ids, case = self.get_unique_component_ids(selection)

            # Update bounding box (and hence main chip dimensions)
            for qcomp_id in qcomp_ids:
                min_x, min_y, max_x, max_y = self.design._components[
                    qcomp_id].qgeometry_bounds()
                self.min_x_main = min(min_x, self.min_x_main)
                self.min_y_main = min(min_y, self.min_y_main)
                self.max_x_main = max(max_x, self.max_x_main)
                self.max_y_main = max(max_y, self.max_y_main)

            if case != 1:  # Render a subset of components using mask
                mask = table['component'].isin(qcomp_ids)
                table = table[mask]
                self.render_everything = False

        else:
            for qcomp in self.design.components:
                min_x, min_y, max_x, max_y = self.design.components[
                    qcomp].qgeometry_bounds()
                self.min_x_main = min(min_x, self.min_x_main)
                self.min_y_main = min(min_y, self.min_y_main)
                self.max_x_main = max(max_x, self.max_x_main)
                self.max_y_main = max(max_y, self.max_y_main)

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
            x_min, x_max = x0 - qc_width / 2, x0 + qc_width / 2
            y_min, y_max = min(y0, y1), max(y0, y1)
        else:
            # Junction runs horizontally left/right
            x_min, x_max = min(x0, x1), max(x0, x1)
            y_min, y_max = y0 - qc_width / 2, y0 + qc_width / 2

        # Draw rectangle
        self.logger.debug(f'Drawing a rectangle: {name}')
        poly_ansys = self.modeler.draw_rect_corner([x_min, y_min, qc_chip_z],
                                                   x_max - x_min, y_max - y_min,
                                                   qc_chip_z, **ansys_options)
        axis = 'x' if abs(x1 - x0) > abs(y1 - y0) else 'y'
        self.modeler.rename_obj(poly_ansys, 'JJ_rect_' + name)
        self.assign_mesh.append('JJ_rect_' + name)

        # Draw line
        poly_jj = self.modeler.draw_polyline([endpoints_3d[0], endpoints_3d[1]],
                                             closed=False,
                                             **dict(color=(128, 0, 128)))
        poly_jj = poly_jj.rename('JJ_' + name + '_')
        poly_jj.show_direction = True

    def render_element_poly(self, qgeom: pd.Series):
        """
        Render a closed polygon.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """
        ansys_options = dict(transparency=0.0)

        qc_name = 'Q' + str(qgeom['component'])  # name of QComponent
        qc_elt = get_clean_name(
            qgeom['name'])  # name of element within QGeometry table
        qc_shapely = qgeom.geometry  # shapely geom
        qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))
        qc_fillet = round(qgeom.fillet, 7)

        name = f'{qc_name}{QAnsysRenderer.NAME_DELIM}{qc_elt}'

        points = parse_units(list(
            qc_shapely.exterior.coords))  # list of 2d point tuples
        points_3d = to_vec3D(points, qc_chip_z)

        if is_rectangle(qc_shapely):  # Draw as rectangle
            self.logger.debug(f'Drawing a rectangle: {name}')
            x_min, y_min, x_max, y_max = qc_shapely.bounds
            poly_ansys = self.modeler.draw_rect_corner(
                *parse_units([[x_min, y_min, qc_chip_z], x_max - x_min,
                              y_max - y_min, qc_chip_z]), **ansys_options)
            self.modeler.rename_obj(poly_ansys, name)

        else:
            # Draw general closed poly
            poly_ansys = self.modeler.draw_polyline(points_3d[:-1],
                                                    closed=True,
                                                    **ansys_options)
            # rename: handle bug if the name of the cut already exits and is used to make a cut
            poly_ansys = poly_ansys.rename(name)

        qc_fillet = round(qgeom.fillet, 7)
        if qc_fillet > 0:
            qc_fillet = parse_units(qc_fillet)
            idxs_to_fillet = good_fillet_idxs(
                points,
                qc_fillet,
                precision=self.design._template_options.PRECISION,
                isclosed=True)
            if idxs_to_fillet:
                self.modeler._fillet(qc_fillet, idxs_to_fillet, poly_ansys)

        # Subtract interior shapes, if any
        if len(qc_shapely.interiors) > 0:
            for i, x in enumerate(qc_shapely.interiors):
                interior_points_3d = to_vec3D(parse_units(list(x.coords)),
                                              qc_chip_z)
                inner_shape = self.modeler.draw_polyline(
                    interior_points_3d[:-1], closed=True)
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

        qc_name = 'Q' + str(qgeom['component'])  # name of QComponent
        qc_elt = get_clean_name(
            qgeom['name'])  # name of element within QGeometry table
        qc_shapely = qgeom.geometry  # shapely geom
        qc_chip_z = parse_units(self.design.get_chip_z(qgeom.chip))

        name = f'{qc_name}{QAnsysRenderer.NAME_DELIM}{qc_elt}'

        qc_width = parse_units(qgeom.width)

        points = parse_units(list(qc_shapely.coords))
        points_3d = to_vec3D(points, qc_chip_z)

        poly_ansys = self.modeler.draw_polyline(points_3d,
                                                closed=False,
                                                **ansys_options)
        poly_ansys = poly_ansys.rename(name)

        qc_fillet = round(qgeom.fillet, 7)
        if qc_fillet > 0:
            qc_fillet = parse_units(qc_fillet)
            idxs_to_fillet = good_fillet_idxs(
                points,
                qc_fillet,
                precision=self.design._template_options.PRECISION,
                isclosed=False)
            if idxs_to_fillet:
                self.modeler._fillet(qc_fillet, idxs_to_fillet, poly_ansys)

        if qc_width:
            x0, y0 = points[0]
            x1, y1 = points[1]
            vlen = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
            p0 = np.array([
                x0, y0, 0
            ]) + qc_width / (2 * vlen) * np.array([y0 - y1, x1 - x0, 0])
            p1 = np.array([
                x0, y0, 0
            ]) + qc_width / (2 * vlen) * np.array([y1 - y0, x0 - x1, 0])
            shortline = self.modeler.draw_polyline([p0, p1],
                                                   closed=False)  # sweepline
            self.modeler._sweep_along_path(shortline, poly_ansys)

        if qgeom.chip not in self.chip_subtract_dict:
            self.chip_subtract_dict[qgeom.chip] = set()

        if qgeom['subtract']:
            self.chip_subtract_dict[qgeom.chip].add(name)

        elif qgeom['width'] and (not qgeom['helper']):
            self.assign_perfE.append(name)

    def render_chips(self, draw_sample_holder: bool = True):
        """
        Render chips using info from design.get_chip_size method.

        Renders the ground plane of this chip (if one is present).
        Renders the wafer of the chip.

        Args:
            draw_sample_holder (bool, optional): Option to draw vacuum box around chip. Defaults to True.
        """
        ansys_options = dict(transparency=0.0)

        for chip_name in self.chip_subtract_dict:
            ops = self.design._chips[chip_name]
            p = self.design.get_chip_size(chip_name)
            origin = parse_units([p['center_x'], p['center_y'], p['center_z']])
            size = parse_units([p['size_x'], p['size_y'], p['size_z']])
            vac_height = parse_units(
                [p['sample_holder_top'], p['sample_holder_bottom']])
            if chip_name == 'main':
                # Draw plane, wafer, and sample holder (vacuum box)
                # x and y dimensions of the vacuum box are identical to that of the 'main' chip
                self.min_x_main = parse_units(self.min_x_main)
                self.max_x_main = parse_units(self.max_x_main)
                self.min_y_main = parse_units(self.min_y_main)
                self.max_y_main = parse_units(self.max_y_main)
                comp_center_x = (self.min_x_main + self.max_x_main) / 2
                comp_center_y = (self.min_y_main + self.max_y_main) / 2
                min_x_edge = comp_center_x - self._options[
                    'bounding_box_scale_x'] * (comp_center_x - self.min_x_main)
                max_x_edge = comp_center_x + self._options[
                    'bounding_box_scale_x'] * (self.max_x_main - comp_center_x)
                min_y_edge = comp_center_y - self._options[
                    'bounding_box_scale_y'] * (comp_center_y - self.min_y_main)
                max_y_edge = comp_center_y + self._options[
                    'bounding_box_scale_y'] * (self.max_y_main - comp_center_y)
                if self.render_everything and (
                        origin[0] - size[0] / 2 <= min_x_edge < max_x_edge <=
                        origin[0] + size[0] / 2) and (origin[1] - size[1] / 2 <=
                                                      min_y_edge < max_y_edge <=
                                                      origin[1] + size[1] / 2):
                    # All components are rendered and the overall bounding box lies within 9 X 6 chip
                    plane = self.modeler.draw_rect_center(
                        origin,
                        x_size=size[0],
                        y_size=size[1],
                        name=f'{chip_name}_plane',
                        **ansys_options)
                    whole_chip = self.modeler.draw_box_center(
                        [origin[0], origin[1], size[2] / 2],
                        [size[0], size[1], -size[2]],
                        name=chip_name,
                        material=ops['material'],
                        color=(186, 186, 205),
                        transparency=0.2,
                        wireframe=False)
                    if draw_sample_holder:
                        vacuum_box = self.modeler.draw_box_center(
                            [
                                origin[0], origin[1],
                                (vac_height[0] - vac_height[1]) / 2
                            ], [size[0], size[1],
                                sum(vac_height)],
                            name='sample_holder')
                else:
                    # A strict subset of components is rendered, or exported components extend beyond boundaries of 9 X 6 chip
                    x_width = max_x_edge - min_x_edge
                    y_width = max_y_edge - min_y_edge
                    plane = self.modeler.draw_rect_center(
                        [comp_center_x, comp_center_y, origin[2]],
                        x_size=x_width,
                        y_size=y_width,
                        name=f'{chip_name}_plane',
                        **ansys_options)
                    whole_chip = self.modeler.draw_box_center(
                        [comp_center_x, comp_center_y, size[2] / 2],
                        [x_width, y_width, -size[2]],
                        name=chip_name,
                        material=ops['material'],
                        color=(186, 186, 205),
                        transparency=0.2,
                        wireframe=False)
                    if draw_sample_holder:
                        vacuum_box = self.modeler.draw_box_center(
                            [
                                comp_center_x, comp_center_y,
                                (vac_height[0] - vac_height[1]) / 2
                            ], [x_width, y_width,
                                sum(vac_height)],
                            name='sample_holder')
            else:
                # Only draw plane and wafer
                plane = self.modeler.draw_rect_center(origin,
                                                      x_size=size[0],
                                                      y_size=size[1],
                                                      name=f'{chip_name}_plane',
                                                      **ansys_options)
                whole_chip = self.modeler.draw_box_center(
                    [origin[0], origin[1], size[2] / 2],
                    [size[0], size[1], -size[2]],
                    name=chip_name,
                    material=ops['material'],
                    color=(186, 186, 205),
                    transparency=0.2,
                    wireframe=False)
            if self.chip_subtract_dict[
                    chip_name]:  # Any layer which has subtract=True qgeometries will have a ground plane
                self.assign_perfE.append(f'{chip_name}_plane')

    def add_endcaps(self, open_pins: Union[list, None] = None):
        """
        Create endcaps (rectangular cutouts) for all pins in the list open_pins and add them to chip_subtract_dict.
        Each element in open_pins takes on the form (component_name, pin_name) and corresponds to a single pin.

        Args:
            open_pins (Union[list, None], optional): List of tuples of pins that are open. Defaults to None.
        """
        open_pins = open_pins if open_pins else []

        for comp, pin in open_pins:
            pin_dict = self.design.components[comp].pins[pin]
            width, gap = parse_units([pin_dict['width'], pin_dict['gap']])
            mid, normal = parse_units(pin_dict['middle']), pin_dict['normal']
            rect_mid = np.append(mid + normal * gap / 2, [0])
            # Assumption: pins only point in x or y directions
            # If this assumption is not satisfied, draw_rect_center no longer works -> must use draw_polyline
            endcap_name = f'endcap_{comp}_{pin}'
            if abs(normal[0]) > abs(normal[1]):
                self.modeler.draw_rect_center(rect_mid,
                                              x_size=gap,
                                              y_size=width + 2 * gap,
                                              name=endcap_name)
            else:
                self.modeler.draw_rect_center(rect_mid,
                                              x_size=width + 2 * gap,
                                              y_size=gap,
                                              name=endcap_name)
            self.chip_subtract_dict[pin_dict['chip']].add(endcap_name)

    def subtract_from_ground(self):
        """
        For each chip, subtract all "negative" shapes residing on its surface if any such shapes exist.
        """
        for chip, shapes in self.chip_subtract_dict.items():
            if shapes:
                self.modeler.subtract(chip + '_plane', list(shapes))

    def add_mesh(self):
        """
        Add mesh to all elements in self.assign_mesh.
        """
        self.modeler.mesh_length('small_mesh',
                                 self.assign_mesh,
                                 MaxLength=self._options['max_mesh_length_jj'])

<<<<<<< HEAD
    def clean_project(self):
=======
    def clean_active_design(self):
>>>>>>> main
        """
        Remove all elements from Q3 Modeler. 
        """
        project_name = self.pinfo.project_name
        design_name = self.pinfo.design_name
        select_all = ','.join(self.pinfo.get_all_object_names())

        ####Using self.pinfo.design directly seems obvious, but has segv'd.
        ####Exception has occurred: AttributeErro
        ####(note: full exception trace is shown but execution is paused at: _run_module_as_main)
        ####'HfssDesign' object has no attribute 'SetActiveEditor'
        # pinfo_editor = self.pinfo.design.SetActiveEditor("3D Modeler")

        oDesktop = self.pinfo.design.parent.parent._desktop
        oProject = oDesktop.SetActiveProject(project_name)
        oDesign = oProject.SetActiveDesign(design_name)

        # The available editors: "Layout", "3D Modeler", "SchematicEditor"
        oEditor = oDesign.SetActiveEditor("3D Modeler")

        oEditor.Delete(["NAME:Selections", "Selections:=", select_all])