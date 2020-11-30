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
@author: Dennis Wang
'''

from typing import Union

import numpy as np
import pandas as pd
from collections import defaultdict

import pyEPR as epr
from pyEPR.ansys import parse_units

from qiskit_metal.draw.utility import to_vec3D
from qiskit_metal.renderers.renderer_ansys.ansys_renderer import QAnsysRenderer, get_clean_name

from qiskit_metal import Dict

class QHFSSRenderer(QAnsysRenderer):
    """
    Subclass of QAnsysRenderer for running HFSS simulations.
    """

    name = 'hfss'
    """name"""

    hfss_options = Dict() # For potential future use

    def __init__(self, design: 'QDesign', initiate=True, render_template: Dict = None, render_options: Dict = None):
        """
        Create a QRenderer for HFSS simulations, subclassed from QAnsysRenderer.

        Args:
            design (QDesign): Use QGeometry within QDesign to obtain elements for Ansys.
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
            render_template (Dict, optional): Typically used by GUI for template options for GDS. Defaults to None.
            render_options (Dict, optional):  Used to override all options. Defaults to None.
        """
        super().__init__(design=design, initiate=initiate,
                         render_template=render_template, render_options=render_options)
        QHFSSRenderer.load()
    
    def render_design(self, selection: Union[list, None] = None, open_pins: Union[list, None] = None):
        """
        Initiate rendering of components in design contained in selection, assuming they're valid.
        Components are rendered before the chips they reside on, and subtraction of negative shapes
        is performed at the very end. Add the metallize() method here to turn objects in self.assign_perfE
        (see init in QAnsysRenderer class) into perfect electrical conductors.

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
        super().render_design(selection=selection, open_pins=open_pins)
        self.metallize()

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
        poly_ansys = self.modeler.draw_rect_corner(
            [x_min, y_min, qc_chip_z], x_max - x_min, y_max - y_min, qc_chip_z, **ansys_options)
        axis = 'x' if abs(x1 - x0) > abs(y1 - y0) else 'y'
        poly_ansys.make_rlc_boundary(axis,
                                     l=qgeom['hfss_inductance'],
                                     c=qgeom['hfss_capacitance'],
                                     r=qgeom['hfss_resistance'],
                                     name='Lj_' + name)
        self.modeler.rename_obj(poly_ansys, 'JJ_rect_' + name)
        self.assign_mesh.append('JJ_rect_' + name)

        # Draw line
        poly_jj = self.modeler.draw_polyline([endpoints_3d[0], endpoints_3d[1]],
                                              closed=False,
                                              **dict(color=(128, 0, 128)))
        poly_jj = poly_jj.rename('JJ_' + name + '_')
        poly_jj.show_direction = True

    def metallize(self):
        """
        Assign metallic property to all shapes in self.assign_perfE list.
        """
        self.modeler.assign_perfect_E(self.assign_perfE)
