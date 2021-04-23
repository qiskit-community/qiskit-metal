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

from typing import Union
from copy import deepcopy
import pandas as pd

from ..base import NeedsRenderer
from ..base import QAnalysis

from ... import Dict


class CapMatrixAndLOM(QAnalysis, NeedsRenderer):
    """Compute Capacitance matrix, then derive from it the lom parameters.
    """
    default_setup = Dict(name="Setup",
                         freq_ghz=5.,
                         save_fields=False,
                         enabled=True,
                         max_passes=15,
                         min_passes=2,
                         min_converged_passes=2,
                         percent_error=0.5,
                         percent_refinement=30,
                         auto_increase_solution_order=True,
                         solution_order='High',
                         solver_type='Iterative')
    """Default setup"""

    # TODO: add type check to the setup.setter. redefine above to support types
    # def set_setup(self,
    #                   name: str = "Setup",
    #                   freq_ghz: float = 5.,
    #                   save_fields: bool = False,
    #                   enabled: bool = True,
    #                   max_passes: int = 15,
    #                   min_passes: int = 2,
    #                   min_converged_passes: int = 2,
    #                   percent_error: float = 0.5,
    #                   percent_refinement: int = 30,
    #                   auto_increase_solution_order: bool = True,
    #                   solution_order: str = 'High',
    #                   solver_type: str = 'Iterative',
    #                   **kwargs):
    #     params = locals()
    #     self._setup = Dict({k:params[k] for k in params if k not in ('kwargs','self')})
    #     if len(kwargs) > 0:
    #         print(f"I do not support these variables at this time: {kwargs}")

    def __init__(self, design: 'QDesign', renderer_name: str = 'q3d'):
        """Compute Capacitance matrix, then derive from it the lom parameters

        Args:
            design (QDesign): pointer to the main qiskit-metal design. Used to access the Qrenderer
            renderer_name (str, optional): which renderer to use. Defaults to 'q3d'.
        """
        # set design and renderer
        super().__init__(design, renderer_name)

        # create and set setup variables
        self._setup = deepcopy(self.default_setup)

        # result variables
        self._capacitance_matrix = None
        self._lom_output = None

    def _render(self, **design_selection) -> str:
        """Renders the design from qiskit metal into the selected renderer.
        First it decides the tentative name of the design. Then it runs the renderer method
        that executes the design rendering. It returns the final design name.

        Returns:
            str: Final design name that the renderer used
        """
        base_name = self.design.name
        if "name" in design_selection:
            if design_selection["name"] is not None:
                base_name = design_selection["name"]
                del design_selection["name"]
        design_name = base_name + "_" + self.renderer_name
        design_name = self.renderer.execute_design(design_name,
                                                   solution_type='capacitance',
                                                   **design_selection)
        return design_name

    def _analyze(self) -> str:
        """Executes the analysis step of the Run. First it initializes the renderer setup
        to prepare for the capacitance calculation, then it executes it.
        Finally it recovers the output of the analysis and stores it in self.capacitance_matrix_df

        Returns:
            str: Name of the setup that was run
        """
        setup_name = self.renderer.initialize_cap_extract(**self.setup)

        self.renderer.analyze_setup(setup_name)
        self.capacitance_matrix_df = self.renderer.get_capacitance_matrix()
        return setup_name

    def run(self,
            name: str = None,
            components: Union[list, None] = None,
            open_terminations: Union[list, None] = None,
            box_plus_buffer: bool = True) -> (str, str):
        """Executes the entire capacitance matrix extraction.
        First it makes sure the tool is running. Then it does the necessary to render the design.
        Finally it runs the setup defined in this class. So you need to modify the setup ahead.
        You can modify the setup by using the methods defined in the QAnalysis super-class.
        After this method concludes you can inspect the output using this class properties.

        Args:
            name (str): reference name for the somponents selection. If None,
                it will use the design.name. Defaults to None.
            components (Union[list, None], optional): List of components to render.
                Defaults to None.
            open_terminations (Union[list, None], optional):
                List of tuples of pins that are open. Defaults to None.
            box_plus_buffer (bool, optional): Either calculate a bounding box based on the location
                of rendered geometries or use chip size from design class. Defaults to True.

        Returns:
            (str, str): Name of the design and name of the setup
        """
        if not self.renderer_initialized:
            self._initialize_renderer()

        renderer_design_name = self._render(name=name,
                                            selection=components,
                                            open_pins=open_terminations,
                                            box_plus_buffer=box_plus_buffer)

        setup_name = self._analyze()
        return renderer_design_name, setup_name

    @property
    def capacitance_matrix_df(self) -> pd.DataFrame:
        """Stores the last-pass capacitance matrix after run() concludes.
        It is populated by _analyze()

        Returns:
            pd.DataFrame: Capacitance Matrix from the last pass
        """
        return self._capacitance_matrix

    @capacitance_matrix_df.setter
    def capacitance_matrix_df(self, cap_mtrx: pd.DataFrame):
        """Sets the capacitance matrix.

        Args:
            cap_mtrx (pd.DataFrame): Capactiance Matrix to store in the Analysis instance
        """
        self._capacitance_matrix = cap_mtrx

    @property
    def lumped_oscillator_dic(self) -> dict:
        """Stores the output of the LOM analysis

        Returns:
            dict: Pass number (keys) and their respective capacitance matrices (values)
        """
        return self._lom_output

    @lumped_oscillator_dic.setter
    def lumped_oscillator_dic(self, lom_dict: dict):
        """Allows editing the output of the LOM analysis

        Args:
            lom_dict (dict): Pass number (keys) and their respective capacitance matrices (values)
        """
        self._lom_output = lom_dict

    def get_lumped_oscillator(self,
                              Lj_nH: float,
                              Cj_fF: float,
                              N: int,
                              fr: Union[list, float],
                              fb: Union[list, float],
                              maxPass: int,
                              variation: str = '',
                              solution_kind: str = 'AdaptivePass',
                              g_scale: float = 1):
        """Executes the lumped oscillator extraction from the simulation

        Args:
            Lj_nH (float): Junction inductance (in nH)
            Cj_fF (float): Junction capacitance (in fF)
            N (int): Coupling pads (1 readout, N - 1 bus)
            fr (Union[list, float]): Coupling bus and readout frequencies (in GHz).
                fr can be a list with the order they appear in the capMatrix.
            fb (Union[list, float]): Coupling bus and readout frequencies (in GHz).
                fb can be a list with the order they appear in the capMatrix.
            maxPass (int): maximum number of passes. Ignored for 'LastAdaptive' solutions types.
                Defaults to 1.
            variation (str, optional): An empty string returns nominal variation.
                Otherwise need the list. Defaults to ''.
            solution_kind (str, optional): Solution type ('AdaptivePass' or 'LastAdaptive').
                Defaults to 'LastAdaptive'.
            g_scale (float, optional): Scale factor. Defaults to 1.
        """
        self._lom_output = self.renderer.lumped_oscillator_vs_passes(
            Lj_nH, Cj_fF, N, fr, fb, maxPass, variation, solution_kind, g_scale)

    def plot_convergence_main(self, *args, **kwargs):
        """Plots alpha and frequency versus pass number, as well as convergence of delta (in %).

        Args:
            It accepts the same inputs as get_lumped_oscillator(), to allow regenerating the LOM
            results before plotting them.
        """
        if self._lom_output is None or args or kwargs:
            self.get_lumped_oscillator(*args, **kwargs)
        # TODO: remove analysis plots from pyEPR and move it here
        self.renderer.plot_convergence_main(self._lom_output)

    def plot_convergence_chi(self, *args, **kwargs):
        """Plot convergence of chi and g, both in MHz, as a function of pass number.

        Args:
            It accepts the same inputs as get_lumped_oscillator(), to allow regenerating the LOM
            results before plotting them.
        """
        if self._lom_output is None or args or kwargs:
            self.get_lumped_oscillator(*args, **kwargs)
        self.renderer.plot_convergence_chi(self._lom_output)
