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
"""
Capacitance-based analyses

@author: Marco Facchini, Dennis Wang
@date: 2020
"""

from typing import Union
from ... import Dict


class capacitance_method():

    def __init__(self, design: 'QDesign', renderer_name: str = 'q3d'):
        """Compute Capacitance matrix, then derive from it

        Args:
            design (QDesign): pointer to the main qiskit-metal design. Used to access the Qrenderer
            renderer_name (str, optional): which renderer to use. Defaults to 'q3d'.
        """
        # pointer to find renderers
        self.design = design

        # naming conventions
        self.renderer_name = renderer_name
        self.renderer = self.select_renderer(renderer_name)
        self.setup_name = "Setup"  # + renderer_name

        # create and set setup variables
        self._setup = None
        self.set_setup()

        # results variables
        self._capacitance_matrix = None
        self._lom_output = None

    def select_renderer(self, renderer_name):
        # did user select a usable renderer (registered)?
        try:
            renderer = self.design.renderers[renderer_name]
            if not renderer:
                self.design.logger.error(
                    f"Cannot find the renderer \"{renderer_name}\" registered with qiskit-metal"
                )
        except KeyError:
            self.design.logger.error(
                f"Cannot find a renderer {renderer_name} registered with qiskit-metal"
            )
        return renderer

    def _render_initialize(self):
        # turn on the tool
        self.renderer.start()

    def _render(self, **design_selection):
        # Name and create the design
        design_name = self.design.name + "_" + self.renderer_name
        design_name = self.renderer.execute_design(design_name, **design_selection)
        return design_name

    def _analyze(self):
        # send Analysis setup options to renderer
        setup_name = self.renderer.initialize_cap_extract(**self.setup)
        
        # execute analysis and extract
        self.renderer.analyze_setup(setup_name)
        self.capacitance_matrix_df = self.renderer.get_capacitance_matrix()
        return setup_name

    def run(self,
            components=None,
            open_terminations=None,
            box_plus_buffer=True):

        if not self.renderer.initialized:
            self.renderer.start()

        renderer_design_name = self._render(selection=components,
                    open_pins=open_terminations,
                    box_plus_buffer=box_plus_buffer)

        setup_name = self._analyze()
        return renderer_design_name, setup_name

    @property
    def capacitance_matrix_df(self):
        return self._capacitance_matrix

    @capacitance_matrix_df.setter
    def capacitance_matrix_df(self, cap_mtrx):
        self._capacitance_matrix = cap_mtrx

    @property
    def lumped_oscillator_dic(self):
        return self._lom_output

    @lumped_oscillator_dic.setter
    def lumped_oscillator_dic(self, lom_dict):
        self._lom_output = lom_dict

    @property
    def setup(self):
        return self._setup

    @setup.setter
    def setup(self):
        return self._setup

    def set_setup(self,
                      name: str = "Setup",
                      freq_ghz: float = 5.,
                      save_fields: bool = False,
                      enabled: bool = True,
                      max_passes: int = 15,
                      min_passes: int = 2,
                      min_converged_passes: int = 2,
                      percent_error: float = 0.5,
                      percent_refinement: int = 30,
                      auto_increase_solution_order: bool = True,
                      solution_order: str = 'High',
                      solver_type: str = 'Iterative',
                      **kwargs):
        params = locals()
        self._setup = Dict({k:params[k] for k in params if k not in ('kwargs','self')})
        if len(kwargs) > 0:
            print(f"I do not support these variables at this time: {kwargs}")

    def setup_update(self, **kwargs):
        if not self._setup:
            self.set_setup(**kwargs)
        self._setup.update(kwargs)

    def get_lumped_oscillator(self,
                              Lj_nH: float,
                              Cj_fF: float,
                              N: int,
                              fr: Union[list, float],
                              fb: Union[list, float],
                              maxPass: int,
                              variation: str = '',
                              solution_kind: str = 'AdaptivePass',
                              g_scale: float = 1) -> dict:
        self._lom_output = self.renderer.lumped_oscillator_vs_passes(
            Lj_nH, Cj_fF, N, fr, fb, maxPass, variation, solution_kind, g_scale)

    def plot_convergence_main(self, *args, **kwargs):
        if self._lom_output is None:
            self.get_lumped_oscillator(*args, **kwargs)
        self.renderer.plot_convergence_main(self._lom_output)
        
    def plot_convergence_chi(self, *args, **kwargs):
        if self._lom_output is None:
            self.get_lumped_oscillator(*args, **kwargs)
        self.renderer.plot_convergence_chi(self._lom_output)

    def close(self):
        self.renderer.stop()