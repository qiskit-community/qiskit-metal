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

from collections import defaultdict

import pyEPR as epr

from qiskit_metal.renderers.renderer_ansys.ansys_renderer import QAnsysRenderer

from qiskit_metal import Dict

class QQ3DRenderer(QAnsysRenderer):
    """
    Subclass of QAnsysRenderer for running Q3D simulations.
    """

    name = 'q3d'
    """name"""

    q3d_options = Dict(
        material_type='pec',
        material_thickness='200nm'
    )

    def __init__(self, design: 'QDesign', initiate=True, render_template: Dict = None, render_options: Dict = None):
        """
        Create a QRenderer for Q3D simulations, subclassed from QAnsysRenderer.

        Args:
            design (QDesign): Use QGeometry within QDesign to obtain elements for Ansys.
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
            render_template (Dict, optional): Typically used by GUI for template options for GDS. Defaults to None.
            render_options (Dict, optional):  Used to override all options. Defaults to None.
        """
        super().__init__(design=design, initiate=initiate,
                         render_template=render_template, render_options=render_options)
        QQ3DRenderer.load()

    @property
    def boundaries(self):
        if self.pinfo:
            return self.pinfo.design._boundaries
    
    def render_design(self, selection: Union[list, None] = None, open_pins: Union[list, None] = None):
        """
        Initiate rendering of components in design contained in selection, assuming they're valid.
        Components are rendered before the chips they reside on, and subtraction of negative shapes
        is performed at the very end.

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
        self.render_tables(selection)
        self.add_endcaps(open_pins)

        self.render_chips(draw_sample_holder=False)
        self.subtract_from_ground()

        self.assign_thin_conductor()
        self.assign_nets()

    def render_tables(self, selection: Union[list, None] = None):
        """
        Render components in design grouped by table type (path or poly, but not junction).

        Args:
            selection (Union[list, None], optional): List of components to render. Defaults to None.
        """
        for table_type in self.design.qgeometry.get_element_types():
            if table_type != 'junction':
                self.render_components(table_type, selection)

    def assign_thin_conductor(self):
        """
        Assign thin conductor property to all exported shapes.
        Unless otherwise specified, all 2-D shapes are pec's with a thickness of 200 nm.
        """
        self.boundaries.AssignThinConductor(["NAME:ThinCond1",
                                             "Objects:=", self.assign_perfE,
                                             "Material:=", self.q3d_options['material_type'],
                                             "Thickness:=", self.q3d_options['material_thickness']])

    def assign_nets(self):
        """
        Auto assign nets to exported shapes.
        """
        self.boundaries.AutoIdentifyNets()
