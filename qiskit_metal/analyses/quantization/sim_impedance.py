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

from typing import Union, Tuple

from qiskit_metal.designs import QDesign  # pylint: disable=unused-import

from ... import Dict
from ..core import QAnalysisRenderer


class ImpedanceAnalysis(QAnalysisRenderer):
    """Uses drivenmodal simulation to extract the impedance

    Default Setup:
        name (str): Name of driven modal setup. Defaults to "Setup".
        freq_ghz (int): Frequency in GHz. Defaults to 5.
        max_delta_s (float): Absolute value of maximum difference in
            scattering parameter S. Defaults to 0.1.
        max_passes (int): Maximum number of passes. Defaults to 10.
        min_passes (int): Minimum number of passes. Defaults to 1.
        min_converged (int): Minimum number of converged passes. Defaults to 1.
        pct_refinement (int): Percent refinement. Defaults to 30.
        basis_order (int): Basis order. Defaults to 1.
        vars (Dict): Variables (key) and values (value) to define in the renderer.
        sweep_setup (Dict): Description of the drivenmodal sweep
            name (str): Name of sweep. Defaults to "Sweep".
            start_ghz (float): Starting frequency of sweep in GHz. Defaults to 2.0.
            stop_ghz (float): Ending frequency of sweep in GHz. Defaults to 8.0.
            count (int): Total number of frequencies. Defaults to 101.
            step_ghz (float): Difference between adjacent frequencies. Defaults to None.
            type (str): Type of sweep. Defaults to "Fast".
            save_fields (bool): Whether or not to save fields. Defaults to False.
    """
    default_setup = Dict(sim=Dict(name="Setup",
                                  freq_ghz=5,
                                  max_delta_s=0.1,
                                  max_passes=10,
                                  min_passes=1,
                                  min_converged=1,
                                  pct_refinement=30,
                                  basis_order=1,
                                  vars=Dict(Lj='10 nH', Cj='0 fF'),
                                  sweep_setup=Dict(name="Sweep",
                                                   start_ghz=2.0,
                                                   stop_ghz=8.0,
                                                   count=101,
                                                   step_ghz=None,
                                                   type="Fast",
                                                   save_fields=False)))
    """Default setup"""

    def __init__(self, design: 'QDesign', renderer_name: str = 'hfss'):
        """Compute drivenmodal and then extracts impedance, admittance and scattering paramters

        Args:
            design (QDesign): pointer to the main qiskit-metal design. Used to access the Qrenderer
            renderer_name (str, optional): which renderer to use. Defaults to 'hfss'.
        """
        # set design and renderer
        super().__init__(design, renderer_name)

        # settings variables
        self.setup_name = None
        self.sweep_name = None

        # output variables
        self._params_z = None
        self._params_y = None
        self._params_s = None

    def _render(self, **design_selection):
        """Renders the design from qiskit metal into the selected renderer.
        First it decides the tentative name of the design. Then it runs the renderer method
        that executes the design rendering. It returns the final design name.

        Returns:
            str: Final design name that the renderer used.
        """
        # TODO: move to QAnalysisRender? solution_type='drivenmodal' is the only difference.
        # TODO: also move the default_setup['sim']['name']
        base_name = self.design.name
        if "name" in design_selection:
            if design_selection["name"] is not None:
                base_name = design_selection["name"]
                del design_selection["name"]
        design_name = base_name + "_" + self.renderer_name
        design_name = self.renderer.execute_design(design_name,
                                                   solution_type='drivenmodal',
                                                   **design_selection)
        return design_name

    def _analyze(self):
        """Executes the analysis step of the Run. First it initializes the renderer setup
        to prepare for drivenmodal analysis, then it executes it. Finally it recovers the
        output of the analysis and stores it in self._params_z/_params_y/_params_s.
        """
        self.setup_name, self.sweep_name = self.renderer.initialize_drivenmodal(
            **self.setup.sim)

        self.renderer.analyze_sweep(self.sweep_name, self.setup_name)
        # TODO: return the impedance, admittance and scattering matrices for later use

    def get_impedance(self, param_name: list = ['Z11', 'Z21']):  # pylint: disable=dangerous-default-value
        """Create the impedence plot

        Args:
            param_name (list): List of strings describing which impedance values
                to return. Defaults to ['Z11', 'Z21'].
        """
        # TODO: move the plot-making to this analysis module. Renderer should recover full data
        return self.renderer.plot_params(param_name)

    def get_admittance(self, param_name: list = ['Y11', 'Y21']):  # pylint: disable=dangerous-default-value
        """Create the impedence plot

        Args:
            param_name (list): List of strings describing which admittance values
                to return. Defaults to ['Y11', 'Y21'].
        """
        # TODO: move the plot in this analysis module. Renderer should recover the entire data
        return self.renderer.plot_params(param_name)

    def get_scattering(self, param_name: list = ['S11', 'S21', 'S22']):  # pylint: disable=dangerous-default-value
        """Create the scattering plot

        Args:
            param_name (list): List of strings describing which scattering values
                to return. Defaults to ['S11', 'S21', 'S22'].
        """
        # TODO: move the plot in this analysis module. Renderer should recover the entire data
        return self.renderer.plot_params(param_name)

    def run_sim(  # pylint: disable=arguments-differ
            self,
            name: str = None,
            components: Union[list, None] = None,
            open_terminations: Union[list, None] = None,
            port_list: Union[list, None] = None,
            jj_to_port: Union[list, None] = None,
            ignored_jjs: Union[list, None] = None,
            box_plus_buffer: bool = True) -> Tuple[str, str]:
        """Executes the entire drivenmodal analysis and convergence result export.
        First it makes sure the tool is running. Then it does what's necessary to render the design.
        Finally it runs the setup and sweep defined in this class. You need to modify the setup
        ahead. You can modify the setup by using the methods defined in the QAnalysis super-class.
        After this method concludes you can inspect the output using this class properties.

        Args:
            name (str): reference name for the somponents selection. If None,
                it will use the design.name. Defaults to None.
            components (Union[list, None], optional): List of components to render.
                Defaults to None.
            open_terminations (Union[list, None], optional):
                List of tuples of pins that are open. Defaults to None.
            port_list (Union[list, None], optional): List of tuples of pins to be rendered as ports.
                Format element: (component_name, pin_name, impedance (float)). Defaults to None.
            jj_to_port (Union[list, None], optional): List of tuples of jj's to be rendered as
                ports. Format element: (component_name(str), element_name(str), impedance(float),
                draw_ind(bool)). If draw_ind=True, a 10nH Inductance is draw, else it is omitted.
                Defaults to None.
            ignored_jjs (Union[list, None], optional): List of tuples of jj's that shouldn't be
                rendered. Defaults to None.
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
                                            port_list=port_list,
                                            jj_to_port=jj_to_port,
                                            ignored_jjs=ignored_jjs,
                                            box_plus_buffer=box_plus_buffer)

        self._analyze()
        return renderer_design_name, self.setup_name
