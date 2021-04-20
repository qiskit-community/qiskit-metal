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
import matplotlib as mpl
import matplotlib.pyplot as plt
import pyEPR as epr
from pyEPR.reports import (plot_convergence_f_vspass, plot_convergence_max_df,
                           plot_convergence_maxdf_vs_sol,
                           plot_convergence_solved_elem)

from ... import Dict
from ..base import NeedsRenderer
from ..base import QAnalysis


class EigenmodeAndEPR(QAnalysis, NeedsRenderer):
    """Compute eigenmode, then derive from it using the epr method
    """
    default_setup = Dict(name="Setup",
                         min_freq_ghz=1,
                         n_modes=1,
                         max_delta_f=0.5,
                         max_passes=10,
                         min_passes=1,
                         min_converged=1,
                         pct_refinement=30,
                         basis_order=-1,
                         Lj='10 nH',
                         Cj='0 fF')
    """Default setup"""

    def __init__(self, design: 'QDesign', renderer_name: str = 'hfss'):
        """Compute eigenmode, then derive from it using the epr method

        Args:
            design (QDesign): pointer to the main qiskit-metal design. Used to access the Qrenderer
            renderer_name (str, optional): which renderer to use. Defaults to 'hfss'.
        """
        # set design and renderer
        super().__init__(design, renderer_name)

        # create and set setup variables
        self._setup = deepcopy(self.default_setup)

        # results variables
        self._convergence_t = None
        self._convergence_f = None

        # epr variables
        self.junctions = dict()
        self.dissipatives = dict()
        self.ℰ_elec = None
        self.ℰ_mag = None
        self.ℰ_elec_sub = None

    def _render(self, **design_selection):
        """Renders the design from qiskit metal into the selected renderer.
        First it decides the tentative name of the design. Then it runs the renderer method
        that executes the design rendering. It returns the final design name.

        Returns:
            str: Final design name that the renderer used.
        """
        design_name = self.design.name + "_" + self.renderer_name
        design_name = self.renderer.execute_design(design_name,
                                                   solution_type='eigenmode',
                                                   **design_selection)
        return design_name

    def _analyze(self):
        """Executes the analysis step of the Run. First it initializes the renderer setup
        to prepare for eignemode analysis, then it executes it. Finally it recovers the
        output of the analysis and stores it in self.convergence_t and self.convergence_f.

        Returns:
            str: Name of the setup that was run.
        """
        setup_name = self.renderer.initialize_eigenmode(**self.setup)

        self.renderer.analyze_setup(setup_name)
        self.convergence_t, self.convergence_f = self.renderer.get_convergences(
        )
        return setup_name

    def run(self,
            components: Union[list, None] = None,
            open_terminations: Union[list, None] = None,
            port_list: Union[list, None] = None,
            jj_to_port: Union[list, None] = None,
            ignored_jjs: Union[list, None] = None,
            box_plus_buffer: bool = True) -> (str, str):
        """Executes the entire eigenmode analysis and convergence result export.
        First it makes sure the tool is running. Then it does the necessary to render the design.
        Finally it runs the setup defined in this class. So you need to modify the setup ahead.
        You can modify the setup by using the methods defined in the QAnalysis super-class.
        After this method concludes you can inspect the output using this class properties.

        Args:
            components (Union[list, None], optional): List of components to render.
                Defaults to None.
            open_terminations (Union[list, None], optional):
                List of tuples of pins that are open. Defaults to None.
            port_list (Union[list, None], optional): List of tuples of pins to be rendered as ports.
                Defaults to None.
            jj_to_port (Union[list, None], optional): List of tuples of jj's to be rendered as
                ports. Defaults to None.
            ignored_jjs (Union[list, None], optional): List of tuples of jj's that shouldn't be
                rendered. Defaults to None.
            box_plus_buffer (bool, optional): Either calculate a bounding box based on the location
                of rendered geometries or use chip size from design class. Defaults to True.

        Returns:
            (str, str): Name of the design and name of the setup
        """
        if not self.renderer_initialized:
            self._initialize_renderer()

        renderer_design_name = self._render(selection=components,
                                            open_pins=open_terminations,
                                            port_list=port_list,
                                            jj_to_port=jj_to_port,
                                            ignored_jjs=ignored_jjs,
                                            box_plus_buffer=box_plus_buffer)

        setup_name = self._analyze()
        return renderer_design_name, setup_name

    @property
    def convergence_f(self):
        """Convergence of the eigenmode frequency.

        Returns:
            pd.DataFrame: Convergence of the eigenmode frequency.
        """
        return self._convergence_f

    @convergence_f.setter
    def convergence_f(self, conv: pd.DataFrame):
        """Sets the convergence of the eigenmode frequency.

        Args:
            conv (pd.DataFrame): Convergence of the eigenmode frequency.
        """
        self._convergence_f = conv

    @property
    def convergence_t(self):
        """Convergence of the eigenmode frequency.

        Returns:
            pd.DataFrame: Convergence of the eigenmode frequency.
        """
        return self._convergence_t

    @convergence_t.setter
    def convergence_t(self, conv: pd.DataFrame):
        """Sets the convergence of the eigenmode frequency.

        Args:
            conv (pd.DataFrame): Convergence of the eigenmode frequency.
        """
        self._convergence_t = conv

    def recompute_convergences(self, variation: str = None):
        """convergence plots are computed as part of run(). However, in special cases
        you might need to recalculate them using a different variation.

        Args:
            variation (str, optional):  Information from pyEPR; variation should be in the form
            variation = "scale_factor='1.2001'". Defaults to None.
        """
        self.convergence_t, self.convergence_f = self.renderer.get_convergences(
            variation)

    def plot_convergences(self,
                          convergence_t: pd.DataFrame = None,
                          convergence_f: pd.DataFrame = None,
                          fig: mpl.figure.Figure = None,
                          _display: bool = True):
        """Creates 3 plots, useful to determin the convergence achieved by the renderer:
        * convergence frequency vs. pass number if fig is None.
        * delta frequency and solved elements vs. pass number.
        * delta frequency vs. solved elements.

        Args:
            convergence_t (pd.DataFrame): Convergence vs pass number of the eigenemode freqs.
            convergence_f (pd.DataFrame): Convergence vs pass number of the eigenemode freqs.
            fig (matplotlib.figure.Figure, optional): A mpl figure. Defaults to None.
            _display (bool, optional): Display the plot? Defaults to True.
        """

        if convergence_t is None:
            convergence_t = self.convergence_t
        if convergence_f is None:
            convergence_f = self.convergence_f

        if fig is None:
            fig = plt.figure(figsize=(11, 3.))

            # Grid spec and axes;    height_ratios=[4, 1], wspace=0.5
            gs = mpl.gridspec.GridSpec(1, 3, width_ratios=[1.2, 1.5, 1])
            axs = [fig.add_subplot(gs[i]) for i in range(3)]

            ax0t = axs[1].twinx()
            plot_convergence_f_vspass(axs[0], convergence_f)
            plot_convergence_max_df(axs[1], convergence_t.iloc[:, 1])
            plot_convergence_solved_elem(ax0t, convergence_t.iloc[:, 0])
            plot_convergence_maxdf_vs_sol(axs[2], convergence_t.iloc[:, 1],
                                          convergence_t.iloc[:, 0])

            fig.tight_layout(w_pad=0.1)  # pad=0.0, w_pad=0.1, h_pad=1.0)

            # if _display:
            #     from IPython.display import display
            #     display(fig)

    ##### Below methods are related to EPR

    def plot_fields(self, *args, **kwargs):
        """Plots electro(magnetic) fields in the renderer.
        Accepts as args everything parameter accepted by the homonymous renderer method.

        Returns:
            None
        """
        return self.renderer.plot_fields(*args, **kwargs)

    def clear_fields(self, names: list = None):
        """
        Delete field plots from renderer.

        Args:
            names (list, optional): Names of field plots to delete. Defaults to None.
        """
        return self.renderer.clear_fields(names)

    def add_junction(self, name: str, Lj_variable: str, rect: str, line: str,
                     Cj_variable: str):
        """
        Enumerates the Non-linear (Josephson) junctions that need to be considered during
        the EPR analysis

        Args:
            name (str): Name of the junction
            Lj_variable (str): Name of renderer variable that specifies junction inductance.
            rect (str): Name of renderer rectangle on which the lumped boundary condition is
                defined.
            line (str): Name of renderer line spanning the length of rect (voltage, orientation,
                ZPF).
            Cj_variable (str): Name of renderer variable that specifies junction capacitance.
        """
        self.junctions[name] = {
            'Lj_variable': Lj_variable,
            'rect': rect,
            'line': line,
            'Cj_variable': Cj_variable
        }

    def delete_junction(self, name: str):
        """Use to correct errors made with add_junction()

        Args:
            name (str): name of the junction to remove
        """
        del self.junctions[name]

    def add_dissipative(self, category: str, name_list: list):
        """Add a list of dissipatives. Possible categories are:
        'dielectrics_bulk', 'dielectric_surfaces', 'resistive_surfaces', 'seams'

        Args:
            category (str): category of the dissipative.
            name_list (list): names of the shapes composing that dissipative
        """
        self.dissipatives[category] = name_list

    def delete_dissipative(self, category: str):
        """Use to correct errors made with add_dissipatives()

        Args:
            category (str): category of the dissipative to remove
        """
        del self.dissipatives[category]

    # TODO: all the epr methods should not use the renderer. Now they are forced to because of the
    #  pyEPR dependency from pinfo. pinfo however is Ansys specific and cannot be generalized as-is
    #  Therefore we need to eliminate pyEPR dependency on pinfo, or re-implement in qiskit-metal

    def epr_start(self):
        """
        Initialize epr package
        """
        self.renderer.epr_start(self.junctions, self.dissipatives)

    def epr_get_stored_energy(self):
        """Calculate the energy stored in the system based on the eigenmode results
        """
        self.ℰ_elec, self.ℰ_elec_sub, self.ℰ_mag = self.renderer.epr_get_stored_energy(
        )
        print(f"""
        ℰ_elec_all       = {self.ℰ_elec}
        ℰ_elec_substrate = {self.ℰ_elec_sub}
        EPR of substrate = {self.ℰ_elec_sub / self.ℰ_elec * 100 :.1f}%

        ℰ_mag    = {self.ℰ_mag}
        """)

    def epr_run_analysis(self):
        """Short-cut to the same-name method found in renderers.ansys_renderer.py
        Eventually, the analysis code needs to be only here, and the renderer method deprecated
        """
        self.renderer.epr_run_analysis()

    def epr_spectrum_analysis(self, cos_trunc: int = 8, fock_trunc: int = 7):
        """Short-cut to the same-name method found in renderers.ansys_renderer.py
        Eventually, the analysis code needs to be only here, and the renderer method deprecated
        """
        self.renderer.epr_spectrum_analysis(cos_trunc, fock_trunc)

    def epr_report_hamiltonian(self, swp_variable, numeric=True):
        """Short-cut to the same-name method found in renderers.ansys_renderer.py
        Eventually, the analysis code needs to be only here, and the renderer method deprecated
        """
        self.renderer.epr_report_hamiltonian(swp_variable, numeric)

    def close(self):
        """Collects the operations necessary to close well the sim/analysis
        """
        self.renderer.close()
