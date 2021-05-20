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
from pyEPR.ansys import ureg
from pyEPR.calcs.convert import Convert

from ..core import QAnalysisRenderer
from ..core import QAnalysis

from ... import Dict
from ... import config

if not config.is_building_docs():
    from .lumped_capacitive import extract_transmon_coupled_Noscillator


class CapExtraction(QAnalysisRenderer):
    """Compute Capacitance matrix using the selected renderer.
    """
    default_setup = Dict(sim=Dict(name="Setup",
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
                                  solver_type='Iterative'))
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
        """Initialize the class to extract the capacitance matrix

        Args:
            design (QDesign): pointer to the main qiskit-metal design. Used to access the Qrenderer
            renderer_name (str, optional): which renderer to use. Defaults to 'q3d'.
        """
        # set design and renderer
        super().__init__(design, renderer_name)

        # settings variables
        self.setup_name = None

        # output variables
        self._capacitance_matrix = None  # from latest simulation iteration
        self._units = None  # of the self._capacitance_matrix
        self._capacitance_all_passes = {}  # for analysis inspection

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
        Finally it recovers the output of the analysis and stores it in self.capacitance_matrix
        """
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

    def run_sim(self,
                name: str = None,
                components: Union[list, None] = None,
                open_terminations: Union[list, None] = None,
                box_plus_buffer: bool = True) -> (str, str):
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
        if not self.renderer_initialized:
            self._initialize_renderer()

        renderer_design_name = self._render(name=name,
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


class LOManalysis(QAnalysis):
    """Extracts and LOM model from a provided capacitance matrix.

    Default Setup:
        junctions (Dict)
            Lj (float): Junction inductance (in nH)
            Cj (float): Junction capacitance (in fF)
        freq_readout (float): Coupling readout frequency (in GHz).
        freq_bus (Union[list, float]): Coupling bus frequencies (in GHz).
            freq_bus can be a list with the order they appear in the capMatrix.
    """
    default_setup = Dict(lom=Dict(
        junctions=Dict(Lj=12, Cj=2), freq_readout=7.0, freq_bus=[6.0, 6.2]))
    """Default setup"""

    def __init__(self, design: 'QDesign', *args, **kwargs):
        """Initialize the analysis step to extract the LOM model from the system capacitance

        Args:
            design (QDesign): pointer to the main qiskit-metal design. Used to access the Qrenderer
        """
        # set design and renderer
        super().__init__(design, *args, **kwargs)

        # input variables
        self._capacitance_matrix = None
        self._units = None
        self._capacitance_all_passes = {}

        # output variables
        self._lom_output = None  # last pass only
        self._lom_output_all = None  # all the passes

    @property
    def capacitance_matrix(self) -> pd.DataFrame:
        """Returns the capacitance matrix as a pandas dataframe

        Returns:
            pd.DataFrame: Capacitance Matrix from the last pass
        """
        return self._capacitance_matrix

    @capacitance_matrix.setter
    def capacitance_matrix(self, cap_mtrx: pd.DataFrame):
        """Sets the capacitance matrix

        Args:
            cap_mtrx (pd.DataFrame): Capactiance Matrix to store in the Analysis instance
        """
        if isinstance(cap_mtrx, pd.DataFrame):
            self._capacitance_matrix = cap_mtrx
        else:
            self.logger.warning(
                'Unuspported type. Only accepts pandas dataframes')

    @property
    def lumped_oscillator(self) -> pd.DataFrame:
        """Stores the output of the LOM analysis

        Returns:
            dict: Pass number (keys) and their respective lump oscillator information (values)
        """
        return self._lom_output

    @lumped_oscillator.setter
    def lumped_oscillator(self, lom_dict: pd.DataFrame):
        """Allows editing the output of the LOM analysis

        Args:
            lom_dict (dict): Pass number (keys) and their respective
                lump oscillator information (values)
        """
        self._lom_output = lom_dict

    def run(self):
        """Alias for run_lom()
        """
        return self.run_lom(*args, **kwargs)

    def run_lom(self):
        """Executes the lumped oscillator extraction from the capacitance matrix,
        and based on the setup values

        Returns:
            dict: Pass numbers (keys) and their respective capacitance matrices (values)
        """
        s = self.setup.lom

        if self.capacitance_matrix is None:
            self.logger.warning(
                'Please initialize the capacitance_matrix before executing this method.'
            )
        else:
            if not self._capacitance_all_passes:
                self._capacitance_all_passes[1] = self.capacitance_matrix.values

        ic_amps = Convert.Ic_from_Lj(s.junctions.Lj, 'nH', 'A')
        cj = ureg(f'{s.junctions.Cj} fF').to('farad').magnitude
        fr = ureg(f'{s.freq_readout} GHz').to('GHz').magnitude
        fb = [ureg(f'{freq} GHz').to('GHz').magnitude for freq in s.freq_bus]

        # derive N
        N = 2
        if isinstance(fr, list):
            N += len(fr) - 1
        if isinstance(fb, list):
            N += len(fb) - 1

        # get the LOM for every pass
        all_res = {}
        for idx_cmat, df_cmat in self._capacitance_all_passes.items():
            res = extract_transmon_coupled_Noscillator(
                df_cmat[0],
                ic_amps,
                cj,
                N,
                fb,
                fr,
                g_scale=1,
                print_info=bool(idx_cmat == len(self._capacitance_all_passes)))
            all_res[idx_cmat] = res
        all_res = pd.DataFrame(all_res).transpose()
        all_res['χr MHz'] = abs(all_res['chi_in_MHz'].apply(lambda x: x[0]))
        all_res['gr MHz'] = abs(all_res['gbus'].apply(lambda x: x[0]))
        self._lom_output = all_res
        return self.lumped_oscillator

    def plot_convergence(self, *args, **kwargs):
        """Plots alpha and frequency versus pass number, as well as convergence of delta (in %).

        Args:
            It accepts the same inputs as run_lom(), to allow regenerating the LOM
            results before plotting them.
        """
        if self._lom_output is None or args or kwargs:
            self.run_lom(*args, **kwargs)
        # TODO: remove analysis plots from pyEPR and move it here
        self.renderer.plot_convergence_main(self._lom_output)

    def plot_convergence_chi(self, *args, **kwargs):
        """Plot convergence of chi and g, both in MHz, as a function of pass number.

        Args:
            It accepts the same inputs as run_lom(), to allow regenerating the LOM
            results before plotting them.
        """
        if self._lom_output is None or args or kwargs:
            self.run_lom(*args, **kwargs)
        self.renderer.plot_convergence_chi(self._lom_output)


class CapExtractAndLOM(LOManalysis, CapExtraction):
    """Compute Capacitance matrix, then derive from it the lom parameters.
    """

    def __init__(self, design: 'QDesign', renderer_name: str = 'q3d'):
        """Initialize class to simulate the capacitance matrix and extract the lom model

        Args:
            design (QDesign): pointer to the main qiskit-metal design. Used to access the Qrenderer
            renderer_name (str, optional): which renderer to use. Defaults to 'q3d'.
        """
        # set design and renderer
        super().__init__(design, renderer_name)

    def run(self, *args, **kwargs):
        """Executes sequentually the system capacitance simulation and lom extraction
        executing the methods CapExtraction.run_sim(*args, **kwargs) and LOManalysis.run_lom()
        For imput parameter, see documentation for CapExtraction.run_sim()

        Returns:
            (dict): Pass numbers (keys) and respective lump oscillator information (values)
        """
        self.run_sim(*args, **kwargs)
        return self.run_lom()
