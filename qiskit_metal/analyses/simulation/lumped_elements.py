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
from qiskit_metal import Dict
from qiskit_metal.analyses.core import QSimulation


class LumpedElementsSim(QSimulation):
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

    Data Labels:
        * cap_matrix (pd.DataFrame): Capacitance matrix from the last iteration.
        * units (str): Units of the values in 'cap_matrix' and 'cap_all_passess'.
        * cap_all_passes (list of pd.DataFrame): intermediate value, for inspection.

    """
    default_setup = Dict(freq_ghz=5.,
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
    """Default setup."""

    # supported labels for data generated from the simulation
    data_labels = ['cap_matrix', 'cap_all_passes', 'units', 'is_converged']
    """Default data labels."""

    def __init__(self, design: 'QDesign' = None, renderer_name: str = 'q3d'):
        """Initialize the class to extract the capacitance matrix.

        Args:
            design (QDesign): Pointer to the main qiskit-metal design.
                Used to access the QRenderer. Defaults to None.
            renderer_name (str, optional): Which renderer to use. Defaults to 'q3d'.
        """
        # set design and renderer
        super().__init__(design, renderer_name)

    def _analyze(self):
        """Executes the analysis step of the Run. First it initializes the renderer setup
        to prepare for the capacitance calculation, then it executes it.
        Finally it calls _get_results_from_renderer to recovers the simulation output.
        """
        # pylint: disable=attribute-defined-outside-init
        self.sim_setup_name = self.renderer.initialize_cap_extract(**self.setup)
        self.renderer.analyze_setup(self.sim_setup_name)
        self._get_results_from_renderer()

    def _get_results_from_renderer(self):
        """Recovers the output of the analysis and stores it in self.capacitance_matrix
        """
        if self.renderer_initialized:
            # pylint: disable=attribute-defined-outside-init
            # extract main (latest) capacitance matrix
            self.capacitance_matrix, self.units = self.renderer.get_capacitance_matrix(
            )
            # extract the capacitance matrices for all passes
            self.capacitance_all_passes, _ = self.renderer.get_capacitance_all_passes(
            )
            # extract convergence
            self.is_converged = self.renderer.get_convergence()
        else:
            self.logger.error(
                "Please initialize renderer before trying to load the simulation results."
                " Consider using the method self.renderer._initiate_renderer()"
                " if you did not already connect qiskit-metal to the renderer.")

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
            name (str): reference name for the components selection. If None,
                it will use the design.name. Defaults to None.
            components (Union[list, None], optional): List of components to render.
                Defaults to None.
            open_terminations (Union[list, None], optional):
                List of tuples of pins that are open. Defaults to None.
            box_plus_buffer (bool, optional): Either calculate a bounding box based on the location
                of rendered geometries or use chip size from design class. Defaults to True.

        Returns:
            (str, str): Name of the design and name of the setup.
        """
        # save input variables to run(). This line must be the first in the method
        if components is not None:
            argm = dict(locals())
            del argm['self']
            self.save_run_args(**argm)
        # wipe data from the previous run (if any)
        self.clear_data()

        if not self.renderer_initialized:
            self._initialize_renderer()

        renderer_design_name = self._render(name=name,
                                            solution_type='capacitive',
                                            selection=components,
                                            open_pins=open_terminations,
                                            box_plus_buffer=box_plus_buffer,
                                            vars_to_initialize=Dict())

        self._analyze()
        return renderer_design_name, self.sim_setup_name

    @property
    def capacitance_matrix(self) -> pd.DataFrame:
        """Getter

        Returns:
            pd.DataFrame: Capacitance matrix data, typically generated by run_sim().
        """
        return self.get_data('cap_matrix')

    @capacitance_matrix.setter
    def capacitance_matrix(self, data: pd.DataFrame):
        """Setter

        Args:
            data (pd.DataFrame): Capacitance matrix data, typically generated by run_sim().
        """
        if not isinstance(data, pd.DataFrame):
            self.logger.warning(
                'Unsupported type %s. Only accepts pandas dataframes. Please try again.',
                {type(data)})
            return
        self.set_data('cap_matrix', data)

    @property
    def capacitance_all_passes(self) -> dict:
        """Getter

        Returns:
            dict: of pd.DataFrame. For each pass of the incremental mash refinements,
                it retains the capacitance matrix at that pass.
        """
        return self.get_data('cap_all_passes')

    @capacitance_all_passes.setter
    def capacitance_all_passes(self, data: dict):
        """Setter

        Args:
            data (dict): of pd.DataFrame. For each pass of the incremental mash refinements,
                it retains the capacitance matrix at that pass.
        """
        if not isinstance(data, dict):
            self.logger.warning(
                'Unsupported type %s. Only accepts dicts of pandas dataframes. Please try again.',
                {type(data)})
            return
        self.set_data('cap_all_passes', data)

    @property
    def units(self) -> str:
        """Getter

        Returns:
            str: Capacitance matrix units.
        """
        return self.get_data('units')

    @units.setter
    def units(self, data: str):
        """Setter

        Args:
            data (str): Capacitance matrix units.
        """
        if not isinstance(data, str):
            self.logger.warning(
                'Unsupported type %s. Only accepts str. Please try again.',
                {type(data)})
            return
        self.set_data('units', data)

    @property
    def is_converged(self) -> bool:
        """Getter

        Returns:
            bool: Boolean indicating whether simulation has converged
        """
        return self.get_data('is_converged')

    @is_converged.setter
    def is_converged(self, data: bool):
        """Setter

        Args:
            data (bool): Sets convergence of simulation for
        """
        if not isinstance(data, bool):
            self.logger.warning(
                'Unsupported type %s. Only accepts boolean. Please try again.',
                {type(data)})
            return
        self.set_data('is_converged', data)
