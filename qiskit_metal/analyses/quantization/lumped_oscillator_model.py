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

import pandas as pd
from pint import UnitRegistry

from pyEPR.calcs.convert import Convert

from qiskit_metal.designs import QDesign  # pylint: disable=unused-import
from ..core import QAnalysis, QAnalysisRenderer
from . import CapExtraction

from ... import Dict
from ... import config

if not config.is_building_docs():
    from .lumped_capacitive import extract_transmon_coupled_Noscillator


# TODO: eliminate every reference to "renderer" in this file
#  then change inheritance from QAnalysisRenderer to QAnalysis
class LOManalysis(QAnalysisRenderer):
    """Performs the LOM analysis on the user-provided capacitance matrix.

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

    def reset_variables(self):
        """Code to set and reset the output variables for this analysis class
        This is called by the QAnalysis.__init__()
        """
        # pylint: disable=attribute-defined-outside-init
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

    def run(self):  # pylint: disable=arguments-differ
        """Alias for run_lom()
        """
        return self.run_lom()

    def run_lom(self):
        """Executes the lumped oscillator extraction from the capacitance matrix,
        and based on the setup values

        Returns:
            dict: Pass numbers (keys) and their respective capacitance matrices (values)
        """
        # wipe data from the previous run (if any)
        self.reset_variables()

        s = self.setup.lom

        if self.capacitance_matrix is None:
            self.logger.warning(
                'Please initialize the capacitance_matrix before executing this method.'
            )
        else:
            if not self._capacitance_all_passes:
                self._capacitance_all_passes[1] = self.capacitance_matrix.values

        ureg = UnitRegistry()
        ic_amps = Convert.Ic_from_Lj(s.junctions.Lj, 'nH', 'A')
        cj = ureg(f'{s.junctions.Cj} fF').to('farad').magnitude
        fread = ureg(f'{s.freq_readout} GHz').to('GHz').magnitude
        fbus = [ureg(f'{freq} GHz').to('GHz').magnitude for freq in s.freq_bus]

        # derive number of coupling pads
        num_cpads = 2
        if isinstance(fread, list):
            num_cpads += len(fread) - 1
        if isinstance(fbus, list):
            num_cpads += len(fbus) - 1

        # get the LOM for every pass
        all_res = {}
        for idx_cmat, df_cmat in self._capacitance_all_passes.items():
            res = extract_transmon_coupled_Noscillator(
                df_cmat[0],
                ic_amps,
                cj,
                num_cpads,
                fbus,
                fread,
                g_scale=1,
                print_info=bool(idx_cmat == len(self._capacitance_all_passes)))
            all_res[idx_cmat] = res
        all_res = pd.DataFrame(all_res).transpose()
        all_res['χr MHz'] = abs(all_res['chi_in_MHz'].apply(lambda x: x[0]))
        all_res['gr MHz'] = abs(all_res['gbus'].apply(lambda x: x[0]))
        self.lumped_oscillator = all_res
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

    def run_sim(self, *args, **kwargs):  # pylint: disable=signature-differs
        """Overridden method to force run_sim() to also wipe the output variables of the analysis.
        """
        self.reset_variables()
        super().run_sim(*args, **kwargs)
