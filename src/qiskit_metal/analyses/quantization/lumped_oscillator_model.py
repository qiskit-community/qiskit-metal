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
from typing import Optional

from qiskit_metal.designs import QDesign
from qiskit_metal.analyses.core import QAnalysis
from qiskit_metal.analyses.simulation import LumpedElementsSim
from qiskit_metal.analyses.quantization.constants import Ic_from_Lj
from qiskit_metal import Dict, config

if not config.is_building_docs():
    from .lumped_capacitive import (
        _purcell_columns_last,
        extract_transmon_coupled_Noscillator,
    )


# TODO: eliminate every reference to "renderer" in this file
class LOManalysis(QAnalysis):
    """Performs Lumped Oscillator Model analysis on a simulated or user-provided capacitance matrix.

    Default Setup:
        * junctions (Dict)
            * Lj (float): Junction inductance (in nH)
            * Cj (float): Junction capacitance (in fF)
        * freq_readout (float): Coupling readout frequency (in GHz).
        * freq_bus (Union[list, float]): Coupling bus frequencies (in GHz).
            * freq_bus can be a list with the order they appear in the capMatrix.
        * Q_res (list or None): Loaded quality factors of the resonators, in
          the order [readout, bus1, bus2, ...], for the Purcell times ``T1`` and
          ``T1bus``. None (default) uses placeholder Q's and logs a warning.
        * Z0 (float): Characteristic impedance of the resonators in ohm
          (default 50).
        * res_L4_corr (list or None): Per coupling pad, in the order
          [readout, bus1, bus2, ...], 1 if that resonator is a quarter-wave
          (lambda/4) line and 0 if it is a half-wave (lambda/2) line. None
          (default) treats all resonators as lambda/2.

    Data Labels:
        * lumped_oscillator (pd.DataFrame): Lumped oscillator result at the last simulation pass
        * lumped_oscillator_all (dict): of pd.DataFrame. Lumped oscillator resulting
            at every pass of the simulation

    """

    default_setup = Dict(
        junctions=Dict(Lj=12, Cj=2),
        freq_readout=7.0,
        freq_bus=[6.0, 6.2],
        res_L4_corr=None,
        Q_res=None,
        Z0=50.0,
    )
    """Default setup."""

    # supported labels for data generated from the simulation
    data_labels = ["lumped_oscillator", "lumped_oscillator_all"]
    """Default data labels."""

    def __init__(
        self, design: Optional["QDesign"] = None, renderer_name: str | None = None
    ):
        """Initialize the Lumped Oscillator Model analysis.

        Args:
            design (QDesign): Pointer to the main qiskit-metal design.
                Used to access the QRenderer. Defaults to None.
            renderer_name (str, optional): Which renderer to use. Valid entries: 'q3d'.
                Defaults to None.
        """
        # QAnalysis are expected to either run simulation or use pre-saved sim outputs
        # we use a Dict() to store the sim outputs previously saved. Its key names need
        # to match those found in the correspondent simulation class.
        self.sim = (
            Dict()
            if renderer_name is None
            else LumpedElementsSim(design, renderer_name)
        )
        super().__init__()

    @property
    def lumped_oscillator(self) -> dict:
        """Getter

        Returns:
            dict: Lumped oscillator result at the last simulation pass.
        """
        return self.get_data("lumped_oscillator")

    @lumped_oscillator.setter
    def lumped_oscillator(self, data: dict):
        """Setter

        Args:
            data (dict): Lumped oscillator result at the last simulation pass.
        """
        if not isinstance(data, dict):
            self.logger.warning(
                "Unsupported type %s. Only accepts dict. Please try again.",
                {type(data)},
            )
            return
        self.set_data("lumped_oscillator", data)

    @property
    def lumped_oscillator_all(self) -> pd.DataFrame:
        """Getter

        Returns:
            pd.DataFrame: each line corresponds to a simulation pass number
                and the remainder of the data is the respective lump oscillator information.
        """
        return self.get_data("lumped_oscillator_all")

    @lumped_oscillator_all.setter
    def lumped_oscillator_all(self, data: pd.DataFrame):
        """Setter

        Args:
            data (pd.DataFrame): each line corresponds to a simulation pass number
                and the remainder of the data is the respective lump oscillator information.
        """
        if not isinstance(data, pd.DataFrame):
            self.logger.warning(
                "Unsupported type %s. Only accepts pd.DataFrame. Please try again.",
                {type(data)},
            )
            return
        self.set_data("lumped_oscillator_all", data)

    def run(self, *args, **kwargs):
        """Executes sequentially the system capacitance simulation (if a renderer was provided
        at creation of this object) and lom extraction by executing the methods
        LumpedElementsSim.run_sim(`*args`, `**kwargs`) and LOManalysis.run_lom().
        For input parameter, see documentation for LumpedElementsSim.run_sim().

        Returns:
            (dict): Pass numbers (keys) and respective lump oscillator information (values).
        """
        if isinstance(self.sim, LumpedElementsSim):
            self.sim.run(*args, **kwargs)
        return self.run_lom()

    def run_lom(self):
        """Executes the lumped oscillator extraction from the capacitance matrix,
        and based on the setup values.

        Returns:
            dict: Pass numbers (keys) and their respective capacitance matrices (values).
        """
        # wipe data from the previous run (if any)
        self.clear_data()

        s = self.setup

        ureg = UnitRegistry()

        cmat = self.sim.capacitance_matrix
        if not isinstance(cmat, pd.DataFrame) or cmat.empty:
            self.logger.warning(
                "Please initialize the capacitance_matrix before executing this method. "
                "`self.sim.capacitance_matrix = pd.DataFrame(...)`"
            )
            return None
        if not self.sim.capacitance_all_passes:
            # A matrix set directly (not produced by a simulation run) has no
            # per-pass history: use it as the only pass. Per-pass matrices are
            # stored in farads (see QQ3DRenderer.get_capacitance_all_passes),
            # while capacitance_matrix is in ``sim.units`` (default fF).
            to_farad = ureg(self.sim.units or "fF").to("farad").magnitude
            self.sim.capacitance_all_passes = {1: cmat.values * to_farad}

        ic_amps = Ic_from_Lj(s.junctions.Lj, "nH", "A")
        cj = ureg(f"{s.junctions.Cj} fF").to("farad").magnitude
        fread = ureg(f"{s.freq_readout} GHz").to("GHz").magnitude
        fbus = [ureg(f"{freq} GHz").to("GHz").magnitude for freq in s.freq_bus]

        # derive number of coupling pads
        num_cpads = 2
        if isinstance(fread, list):
            num_cpads += len(fread) - 1
        if isinstance(fbus, list):
            num_cpads += len(fbus) - 1

        # get the LOM for every pass
        all_res = {}
        last_pass = list(self.sim.capacitance_all_passes)[-1]
        for idx_cmat, df_cmat in self.sim.capacitance_all_passes.items():
            res = extract_transmon_coupled_Noscillator(
                df_cmat,
                ic_amps,
                cj,
                num_cpads,
                fbus,
                fread,
                res_L4_corr=s.get("res_L4_corr"),
                g_scale=1,
                print_info=bool(idx_cmat == len(self.sim.capacitance_all_passes)),
                Q_res=s.get("Q_res"),
                Z0=s.get("Z0", 50.0),
                # warn about placeholder Q's once, not once per pass
                _warn_placeholder_q=bool(idx_cmat == last_pass),
            )
            all_res[idx_cmat] = res
        self.lumped_oscillator = all_res[len(self.sim.capacitance_all_passes)]
        all_res = pd.DataFrame(all_res).transpose()

        # ``chi_in_MHz`` / ``gbus`` are per-pass sequences of coupling-pad
        # values; take the first (readout) entry. Their concrete type shifted
        # from pandas Series to numpy.ndarray with newer numpy/pandas, so
        # ``.iloc[0]`` raised ``AttributeError`` on ndarrays. Read the first
        # element in a way that works for a Series, ndarray, or list. (#1125)
        def _first(seq):
            return seq.iloc[0] if hasattr(seq, "iloc") else seq[0]

        all_res["χr MHz"] = abs(all_res["chi_in_MHz"].apply(_first))
        all_res["gr MHz"] = abs(all_res["gbus"].apply(_first))
        self.lumped_oscillator_all = _purcell_columns_last(all_res)
        return self.lumped_oscillator_all

    def plot_convergence(self, *args, **kwargs):
        """Plots alpha and frequency versus pass number, as well as convergence of delta (in %).

        It accepts the same inputs as run_lom(), to allow regenerating the LOM
        results before plotting them.
        """
        if self.lumped_oscillator_all is None or args or kwargs:
            self.run_lom(*args, **kwargs)
        # TODO: copy plot_convergence_main() from pyEPR and move it here
        self.sim.renderer.plot_convergence_main(self.lumped_oscillator_all)

    def plot_convergence_chi(self, *args, **kwargs):
        """Plot convergence of chi and g, both in MHz, as a function of pass number.

        It accepts the same inputs as run_lom(), to allow regenerating the LOM
        results before plotting them.
        """
        if self.lumped_oscillator_all is None or args or kwargs:
            self.run_lom(*args, **kwargs)
        # TODO: copy plot_convergence_main() from pyEPR and move it here
        self.sim.renderer.plot_convergence_chi(self.lumped_oscillator_all)

    def load_simulation_data(self, data_name: str, data):
        """Load simulation data for the following analysis. This will override any data found

        Args:
            data_name (str): name of the variable
            data (Any): simulation output
        """
        self.sim[data_name] = data
