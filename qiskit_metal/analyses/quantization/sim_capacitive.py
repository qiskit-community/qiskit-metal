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
import pandas as pd
from pyEPR.ansys import ureg
from qiskit_metal.designs import QDesign  # pylint: disable=unused-import

from ..core import QAnalysisRenderer

from ... import Dict


class CapExtraction(QAnalysisRenderer):
    """Compute Capacitance matrix using the selected renderer.

    Default Setup:
        * name (str): Name of capacitive simulation setup. Defaults to "Setup".
        * freq_ghz (int): Frequency in GHz. Defaults to 5.
        * save_fields (bool): Whether or not to save fields. Defaults to False.
        * enabled (bool): Whether or not setup is enabled. Defaults to True.
        * max_passes (int): Maximum number of passes. Defaults to 15.
        * min_passes (int): Minimum number of passes. Defaults to 2.
        * min_converged_passes (int): Minimum number of converged passes.
            Defaults to 2.
        * percent_error (float): Error tolerance as a percentage. Defaults to 0.5.
        * percent_refinement (int): Refinement as a percentage. Defaults to 0.5.
        * auto_increase_solution_order (bool): Whether or not to increase
            solution order automatically. Defaults to True.
        * solution_order (str): Solution order. Defaults to 'High'.
        * solver_type (str): Solver type. Defaults to 'Iterative'.
    """
    default_setup = Dict(sim=Dict(freq_ghz=5.,
                                  save_fields=False,
                                  enabled=True,
                                  max_passes=15,
                                  min_passes=2,
                                  min_converged_passes=2,
                                  percent_error=0.5,
                                  percent_refinement=30,
                                  auto_increase_solution_order=True,
                                  solution_order='High',
                                  solver_type='Iterative'))
    """Default setup"""

    def __init__(self, design: 'QDesign', renderer_name: str = 'q3d'):
        """Initialize the class to extract the capacitance matrix.

        Args:
            design (QDesign): pointer to the main qiskit-metal design. Used to access the Qrenderer
            renderer_name (str, optional): which renderer to use. Defaults to 'q3d'.
        """
        # set design and renderer
        super().__init__(design, renderer_name)

    def reset_variables_sim(self):
        """Code to set and reset the output variables for this analysis class.
        This is called by the QAnalysis.__init__().
        """
        # pylint: disable=attribute-defined-outside-init
        # settings variables
        self.setup_name = None

        # output variables
        self._capacitance_matrix = None  # from latest simulation iteration
        self._units = None  # of the self._capacitance_matrix
        self._capacitance_all_passes = {}  # for analysis inspection

    def _analyze(self) -> str:
        """Executes the analysis step of the Run. First it initializes the renderer setup
        to prepare for the capacitance calculation, then it executes it.
        Finally it recovers the output of the analysis and stores it in self.capacitance_matrix.
        """
        # pylint: disable=attribute-defined-outside-init
        self.setup_name = self.renderer.initialize_cap_extract(**self.setup.sim)

        self.renderer.analyze_setup(self.setup_name)

        # extract main (latest) capacitance matrix
        self.capacitance_matrix, self._units = self.renderer.get_capacitance_matrix(
        )
        # extract the capacitance matrices for all passes
        for i in range(1, 1000):  #1000 is an arbitrary large number
            try:
                df_cmat, user_units = self.renderer.get_capacitance_matrix(
                    solution_kind='AdaptivePass', pass_number=i)
                c_units = ureg(user_units).to('farads').magnitude
                self._capacitance_all_passes[i] = df_cmat.values * c_units,
            except pd.errors.EmptyDataError:
                break

    def run_sim(  # pylint: disable=arguments-differ
            self,
            name: str = None,
            components: Union[list, None] = None,
            open_terminations: Union[list, None] = None,
            box_plus_buffer: bool = True) -> Tuple[str, str]:
        """Executes the capacitance matrix extraction.
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
        # save input variables to run(). This line must be the first in the method
        if components is not None:
            argm = locals()
            del argm['self']
            self.save_run_args(**argm)
        # wipe data from the previous run (if any)
        self.reset_variables_sim()

        if not self.renderer_initialized:
            self._initialize_renderer()

        renderer_design_name = self._render(name=name,
                                            solution_type='capacitive',
                                            selection=components,
                                            open_pins=open_terminations,
                                            box_plus_buffer=box_plus_buffer)

        self._analyze()
        return renderer_design_name, self.setup_name

    @property
    def capacitance_matrix(self) -> pd.DataFrame:
        """Stores the last-pass capacitance matrix after run_sim() concludes.
        It is populated by _analyze() with a pandas database.

        Returns:
            pd.DataFrame: Capacitance Matrix from the last pass
        """
        return self._capacitance_matrix

    @capacitance_matrix.setter
    def capacitance_matrix(self, cap_mtrx: pd.DataFrame):
        """Sets the capacitance matrix.

        Args:
            cap_mtrx (pd.DataFrame): Capactiance Matrix to store in the Analysis instance
        """
        if isinstance(cap_mtrx, pd.DataFrame):
            self._capacitance_matrix = cap_mtrx
        else:
            self.logger.warning(
                'Unuspported type. Only accepts pandas dataframes')
