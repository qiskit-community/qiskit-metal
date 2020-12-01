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

from typing import List, Union

import pyEPR as epr
from qiskit_metal import Dict
from qiskit_metal.renderers.renderer_ansys.ansys_renderer import QAnsysRenderer


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

        self.assign_thin_conductor(self.assign_perfE)
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

    def assign_thin_conductor(self, objects: List[str], material_type: str = None, thickness: str = None, name: str = None):
        """
        Assign thin conductor property to all exported shapes.
        Unless otherwise specified, all 2-D shapes are pec's with a thickness of 200 nm.

        Args:
            objects (List[str]): List of components that are thin conductors with the given properties.
            material_type (str): Material assignment.
            thickness (str): Thickness of thin conductor. Must include units.
            name (str): Name assigned to this group of thin conductors.
        """
        self.boundaries.AssignThinConductor(["NAME:" + (name if name else "ThinCond1"),
                                             "Objects:=", objects,
                                             "Material:=", material_type if material_type else self.q3d_options[
                                                 'material_type'],
                                             "Thickness:=", thickness if thickness else self.q3d_options[
                                                 'material_thickness']
                                             ])

    def assign_nets(self):
        """
        Auto assign nets to exported shapes.
        """
        self.boundaries.AutoIdentifyNets()

    def add_q3d_setup(self, freq_ghz: float = 5.,
                            name: str = "Setup",
                            save_fields: bool = False,
                            enabled: bool = True,
                            max_passes: int = 15,
                            min_passes: int = 2,
                            min_converged_passes: int = 2,
                            percent_error: float = 0.5,
                            percent_refinement: int = 30,
                            auto_increase_solution_order: bool = True,
                            solution_order: str = 'High',
                            solver_type: str = 'Iterative'):
        # TODO: Move arguments to default options.
        """
        Create a solution setup in Ansys Q3D.

        Args:
            freq_ghz (float, optional): Frequency in GHz. Defaults to 5..
            name (str, optional): Name of solution setup. Defaults to "Setup".
            save_fields (bool, optional): Whether or not to save fields. Defaults to False.
            enabled (bool, optional): Whether or not setup is enabled. Defaults to True.
            max_passes (int, optional): Maximum number of passes. Defaults to 15.
            min_passes (int, optional): Minimum number of passes. Defaults to 2.
            min_converged_passes (int, optional): Minimum number of converged passes. Defaults to 2.
            percent_error (float, optional): Error tolerance as a percentage. Defaults to 0.5.
            percent_refinement (int, optional): Refinement as a percentage. Defaults to 30.
            auto_increase_solution_order (bool, optional): Whether or not to increase solution order automatically. Defaults to True.
            solution_order (str, optional): Solution order. Defaults to 'High'.
            solver_type (str, optional): Solver type. Defaults to 'Iterative'.
        """
        if self.pinfo:
            if self.pinfo.design:
                self.pinfo.design.create_q3d_setup(freq_ghz=freq_ghz, 
                                                   name=name, 
                                                   save_fields=save_fields, 
                                                   enabled=enabled,
                                                   max_passes=max_passes, 
                                                   min_passes=min_passes, 
                                                   min_converged_passes=min_converged_passes, 
                                                   percent_error=percent_error,
                                                   percent_refinement=percent_refinement, 
                                                   auto_increase_solution_order=auto_increase_solution_order, 
                                                   solution_order=solution_order,
                                                   solver_type=solver_type)

    def analyze_setup(self, setup_name: str):
        """
        Run a specific solution setup in Ansys Q3D.

        Args:
            setup_name (str): Name of setup.
        """
        if self.pinfo:
            setup = self.pinfo.get_setup(setup_name)
            setup.analyze()

    def get_capacitance_matrix(self, variation: str = '', solution_kind: str = 'AdaptivePass', pass_number: int = 3):
        # TODO: Move arguments to default_options.
        """
        Obtain capacitance matrix in a dataframe format, as well as user units and other information.
        Must be executed *after* analyze_setup.

        Args:
            variation (str, optional): [description]. Defaults to ''.
            solution_kind (str, optional): [description]. Defaults to 'AdaptivePass'.
            pass_number (int, optional): [description]. Defaults to 3.
        """
        if self.pinfo:
            df_cmat, user_units, _, _ = self.pinfo.setup.get_matrix(variation=variation, solution_kind = solution_kind, pass_number=pass_number)
            return df_cmat
