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

from typing import List, Tuple, Union

import pandas as pd
from collections import defaultdict

import pyEPR as epr
from pyEPR.ansys import ureg
from pyEPR.reports import _plot_q3d_convergence_main, _plot_q3d_convergence_chi_f
from pyEPR.calcs.convert import Convert
from qiskit_metal import Dict
from qiskit_metal.renderers.renderer_ansys.ansys_renderer import QAnsysRenderer
from qiskit_metal.toolbox_metal.parsing import is_true

from .. import config
if not config.is_building_docs():
    from qiskit_metal.analyses.quantization.lumped_capacitive import extract_transmon_coupled_Noscillator


class QQ3DRenderer(QAnsysRenderer):
    """Subclass of QAnsysRenderer for running Q3D simulations.

    QAnsysRenderer Default Options:
        * Lj: '10nH' -- Lj has units of nanoHenries (nH)
        * Cj: 0 -- Cj *must* be 0 for pyEPR analysis! Cj has units of femtofarads (fF)
        * _Rj: 0 -- _Rj *must* be 0 for pyEPR analysis! _Rj has units of Ohms
        * max_mesh_length_jj: '7um' -- Maximum mesh length for Josephson junction elements
        * project_path: None -- Default project path; if None --> get active
        * project_name: None -- Default project name
        * design_name: None -- Default design name
        * ansys_file_extension: '.aedt' -- Ansys file extension for 2016 version and newer
        * x_buffer_width_mm: 0.2 -- Buffer between max/min x and edge of ground plane, in mm
        * y_buffer_width_mm: 0.2 -- Buffer between max/min y and edge of ground plane, in mm
    """

    name = 'q3d'
    """name"""

    q3d_options = Dict(material_type='pec', material_thickness='200nm')

    def __init__(self, design: 'QDesign', initiate=True, options: Dict = None):
        """Create a QRenderer for Q3D simulations, subclassed from
        QAnsysRenderer.

        Args:
            design (QDesign): Use QGeometry within QDesign to obtain elements for Ansys.
            initiate (bool, optional): True to initiate the renderer. Defaults to True.
            options (Dict, optional):  Used to override all options. Defaults to None.
        """
        super().__init__(design=design, initiate=initiate, options=options)
        QQ3DRenderer.load()

    @property
    def boundaries(self):
        """Reference to BoundarySetup in active design in Ansys.

        Returns:
            win32com.client.CDispatch: COMObject GetModule, obtained by running within pyEPR: design.GetModule("BoundarySetup")
        """
        if self.pinfo:
            if self.pinfo.design:
                return self.pinfo.design._boundaries

    def render_design(self,
                      selection: Union[list, None] = None,
                      open_pins: Union[list, None] = None,
                      box_plus_buffer: bool = True):
        """Initiate rendering of components in design contained in selection,
        assuming they're valid. Components are rendered before the chips they
        reside on, and subtraction of negative shapes is performed at the very
        end.

        First obtain a list of IDs of components to render and a corresponding case, denoted by self.qcomp_ids
        and self.case, respectively. If self.case == 1, all components in QDesign are to be rendered.
        If self.case == 0, a strict subset of components in QDesign are to be rendered. Otherwise, if
        self.case == 2, one or more component names in selection cannot be found in QDesign.

        Chip_subtract_dict consists of component names (keys) and a set of all elements within each component that
        will eventually be subtracted from the ground plane. Add objects that are perfect conductors and/or have
        meshing to self.assign_perfE and self.assign_mesh, respectively; both are initialized as empty lists. Note
        that these objects are "refreshed" each time render_design is called (as opposed to in the init function)
        to clear QAnsysRenderer of any leftover items from the last call to render_design.

        Among the components selected for export, there may or may not be unused (unconnected) pins.
        The second parameter, open_pins, contains tuples of the form (component_name, pin_name) that
        specify exactly which pins should be open rather than shorted during the simulation. Both the
        component and pin name must be specified because the latter could be shared by multiple
        components. All pins in this list are rendered with an additional endcap in the form of a
        rectangular cutout, to be subtracted from its respective plane.

        The final parameter, box_plus_buffer, determines how the chip is drawn. When set to True, it takes the
        minimum rectangular bounding box of all rendered components and adds a buffer of x_buffer_width_mm and
        y_buffer_width_mm horizontally and vertically, respectively, to the chip size. The center of the chip
        lies at the midpoint x/y coordinates of the minimum rectangular bounding box and may change depending
        on which components are rendered and how they're positioned. If box_plus_buffer is False, however, the
        chip position and dimensions are taken from the chip info dictionary found in self.design, irrespective
        of what's being rendered. While this latter option is faster because it doesn't require calculating a
        bounding box, it runs the risk of rendered components being too close to the edge of the chip or even
        falling outside its boundaries.

        Args:
            selection (Union[list, None], optional): List of components to render. Defaults to None.
            open_pins (Union[list, None], optional): List of tuples of pins that are open. Defaults to None.
            box_plus_buffer (bool, optional): Either calculate a bounding box based on the location of rendered geometries
                                     or use chip size from design class.
        """
        self.qcomp_ids, self.case = self.get_unique_component_ids(selection)

        if self.case == 2:
            self.logger.warning(
                'Unable to proceed with rendering. Please check selection.')
            return

        self.chip_subtract_dict = defaultdict(set)
        self.assign_perfE = []
        self.assign_mesh = []

        chip_list = self.get_chip_names()

        self.render_tables(skip_junction=True)
        self.add_endcaps(open_pins)

        self.render_chips(draw_sample_holder=False,
                          box_plus_buffer=box_plus_buffer)
        self.subtract_from_ground()
        self.add_mesh()

        self.assign_thin_conductor()
        self.assign_nets()

    def assign_thin_conductor(self,
                              material_type: str = 'pec',
                              thickness: str = '200 nm',
                              name: str = None):
        """Assign thin conductor property to all exported shapes. Unless
        otherwise specified, all 2-D shapes are pec's with a thickness of 200
        nm.

        Args:
            material_type (str): Material assignment.
            thickness (str): Thickness of thin conductor. Must include units.
            name (str): Name assigned to this group of thin conductors.
        """
        self.boundaries.AssignThinConductor([
            "NAME:" + (name if name else "ThinCond1"), "Objects:=",
            self.assign_perfE, "Material:=", material_type if material_type else
            self.q3d_options['material_type'], "Thickness:=",
            thickness if thickness else self.q3d_options['material_thickness']
        ])

    def assign_nets(self):
        """Auto assign nets to exported shapes."""
        self.boundaries.AutoIdentifyNets()

    def activate_q3d_setup(self, setup_name_activate: str = None):
        """
        (deprecated) use activate_ansys_setup()
        """
        self.logger.warning(
            'This method is deprecated. Change your scripts to use activate_ansys_setup()'
        )
        self.activate_ansys_setup(setup_name_activate)

    def add_q3d_setup(self,
                      name: str = None,
                      freq_ghz: float = None,
                      save_fields: bool = None,
                      enabled: bool = None,
                      max_passes: int = None,
                      min_passes: int = None,
                      min_converged_passes: int = None,
                      percent_error: float = None,
                      percent_refinement: int = None,
                      auto_increase_solution_order: bool = None,
                      solution_order: str = None,
                      solver_type: str = None,
                      *args,
                      **kwargs):
        """Create a solution setup in Ansys Q3D. If user does not provide
        arguments, they will be obtained from q3d_options dict.

        Args:
            name (str, optional): Name of solution setup. Defaults to None.
            freq_ghz (float, optional): Frequency in GHz. Defaults to None.
            save_fields (bool, optional): Whether or not to save fields. Defaults to None.
            enabled (bool, optional): Whether or not setup is enabled. Defaults to None.
            max_passes (int, optional): Maximum number of passes. Defaults to None.
            min_passes (int, optional): Minimum number of passes. Defaults to None.
            min_converged_passes (int, optional): Minimum number of converged passes. Defaults to None.
            percent_error (float, optional): Error tolerance as a percentage. Defaults to None.
            percent_refinement (int, optional): Refinement as a percentage. Defaults to None.
            auto_increase_solution_order (bool, optional): Whether or not to increase solution order automatically. Defaults to None.
            solution_order (str, optional): Solution order. Defaults to None.
            solver_type (str, optional): Solver type. Defaults to None.
        """
        su = self.default_setup.q3d

        if not name:
            name = self.parse_value(su['name'])
        if not freq_ghz:
            freq_ghz = float(self.parse_value(su['freq_ghz']))
        if not save_fields:
            save_fields = is_true(su['save_fields'])
        if not enabled:
            enabled = is_true(su['enabled'])
        if not max_passes:
            max_passes = int(self.parse_value(su['max_passes']))
        if not min_passes:
            min_passes = int(self.parse_value(su['min_passes']))
        if not min_converged_passes:
            min_converged_passes = int(
                self.parse_value(su['min_converged_passes']))
        if not percent_error:
            percent_error = float(self.parse_value(su['percent_error']))
        if not percent_refinement:
            percent_refinement = int(self.parse_value(su['percent_refinement']))
        if not auto_increase_solution_order:
            auto_increase_solution_order = is_true(
                su['auto_increase_solution_order'])
        if not solution_order:
            solution_order = self.parse_value(su['solution_order'])
        if not solver_type:
            solver_type = self.parse_value(su['solver_type'])

        if self.pinfo:
            if self.pinfo.design:
                return self.pinfo.design.create_q3d_setup(
                    freq_ghz=freq_ghz,
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

    def edit_q3d_setup(self, setup_args: Dict):
        """User can pass key/values to edit the setup for active q3d setup.

        Args:
            setup_args (Dict): a Dict with possible keys/values.

        **setup_args** dict contents:
            * freq_ghz (float, optional): Frequency in GHz. Defaults to 5..
            * name (str, optional): Name of solution setup. Defaults to "Setup".
            * max_passes (int, optional): Maximum number of passes. Defaults to 15.
            * min_passes (int, optional): Minimum number of passes. Defaults to 2.
            * percent_error (float, optional): Error tolerance as a percentage. Defaults to 0.5.

            Note, that these 7 arguments are currently NOT implemented:
            Ansys API named EditSetup requires all arguments to be passed, but
            presently have no way to read all of the setup.
            Also, self.pinfo.setup does not have all the @property variables
            used for Setup.
            * save_fields (bool, optional): Whether or not to save fields. Defaults to False.
            * enabled (bool, optional): Whether or not setup is enabled. Defaults to True.
            * min_converged_passes (int, optional): Minimum number of converged passes. Defaults to 2.
            * percent_refinement (int, optional): Refinement as a percentage. Defaults to 30.
            * auto_increase_solution_order (bool, optional): Whether or not to increase solution order automatically. Defaults to True.
            * solution_order (str, optional): Solution order. Defaults to 'High'.
            * solver_type (str, optional): Solver type. Defaults to 'Iterative'.
        """

        if self.pinfo:
            if self.pinfo.project:
                if self.pinfo.design:
                    if self.pinfo.design.solution_type == 'Q3D':
                        if self.pinfo.setup_name != setup_args.name:
                            self.design.logger.warning(
                                f'The name of active setup={self.pinfo.setup_name} does not match'
                                f'the name of of setup_args.name={setup_args.name}. '
                                f'To use this method, activate the desired Setup before editing it. '
                                f'The setup_args was not used to update the active Setup.'
                            )
                            return

                        for key, value in setup_args.items():
                            if key == "name":
                                continue  #Checked for above.
                            if key == "freq_ghz":
                                if not isinstance(value, float):
                                    self.logger.warning(
                                        'The value for min_freq_ghz should be a '
                                        f'float.  The present value is {value}.'
                                    )
                                else:
                                    ### This EditSetup works if we change all of the arguments
                                    # at the same time.  We don't always want to change all of them.
                                    # Need to have a way to read all of the arguments to
                                    # avoid overwriting arguments. Presently, will use
                                    # the variables set in pyEPR with @property.
                                    # args_editsetup = [
                                    #     f"NAME:{setup_args.name}",
                                    #     "AdaptiveFreq:=", f"{value}GHz",
                                    #     "SaveFields:=", False, "Enabled:=",
                                    #     True,
                                    #     [
                                    #         "NAME:Cap", "MaxPass:=", 15,
                                    #         "MinPass:=", 2, "MinConvPass:=", 2,
                                    #         "PerError:=", 0.5, "PerRefine:=",
                                    #         30, "AutoIncreaseSolutionOrder:=",
                                    #         True, "SolutionOrder:=", "High",
                                    #         "Solver Type:=", "Iterative"
                                    #     ]
                                    # ]
                                    # self.pinfo.design._setup_module.EditSetup(
                                    #     setup_args.name, args_editsetup)
                                    self.pinfo.setup.frequency = f"{value}GHz"
                                    continue
                            if key == 'max_passes':
                                if not isinstance(value, int):
                                    self.logger.warning(
                                        'The value for max_passes should be an int. '
                                        f'The present value is {value}.')
                                else:
                                    self.pinfo.setup.max_pass = value
                                    continue

                            if key == 'min_passes':
                                if not isinstance(value, int):
                                    self.logger.warning(
                                        'The value for min_passes should be an int. '
                                        f'The present value is {value}.')
                                else:
                                    self.pinfo.setup.min_pass = value
                                    continue

                            if key == 'percent_error':
                                if not isinstance(value, float):
                                    self.logger.warning(
                                        'The value for percent_error should be a float. '
                                        f'The present value is {value}.')
                                else:
                                    self.pinfo.setup.pct_error = value
                                    continue

                            self.design.logger.warning(
                                f'In setup_args, key={key}, value={value} is not in pinfo.setup, '
                                'the key/value pair from setup_args not added to Setup in Ansys.'
                            )

                    else:
                        self.logger.warning(
                            'The design does not have solution type as "Q3D". The Setup not updated.'
                        )
                else:
                    self.logger.warning(
                        'A design is not in active project. The Setup not updated.'
                    )
            else:
                self.logger.warning(
                    "Project not available, have you opened a project? Setup not updated."
                )
        else:
            self.logger.warning(
                "Have you run connect_ansys()?  "
                "Cannot find a reference to Ansys in QRenderer. Setup not updated. "
            )

    def analyze_setup(self, setup_name: str):
        """Run a specific solution setup in Ansys Q3D.

        Args:
            setup_name (str): Name of setup.
        """
        if self.pinfo:
            setup = self.pinfo.get_setup(setup_name)
            setup.analyze(setup_name)

    def get_capacitance_matrix(self,
                               variation: str = '',
                               solution_kind: str = 'LastAdaptive',
                               pass_number: int = 1):
        """Obtain capacitance matrix after the analysis.
        Must be executed *after* analyze_setup.

        Args:
            variation (str, optional): An empty string returns nominal variation.
                Otherwise need the list. Defaults to ''.
            solution_kind (str, optional): Solution type. Defaults to 'LastAdaptive'.
				Set to 'AdaptivePass' to return the capacitance matrix of a specific pass.
            pass_number (int, optional): Which adaptive pass to acquire the capacitance
                matrix from. Only in effect with 'AdaptivePass' chosen. Defaults to 1.

        Returns:
            pd.DataFrame, str: Capacitance matrix, and units.
        """
        if self.pinfo:
            df_cmat, user_units, _, _ = self.pinfo.setup.get_matrix(
                variation=variation,
                solution_kind=solution_kind,
                pass_number=pass_number)
            return df_cmat, user_units
        return None, None

    def get_capacitance_all_passes(self, variation: str = ''):
        """Obtain a dictionary of the capacitance matrices from each simulation pass.
        Must be executed *after* analyze_setup.

        Args:
            variation (str, optional): An empty string returns nominal variation.
                Otherwise need the list. Defaults to ''.

        Returns:
            dict, str: dict of pd.DataFrames containing the capacitance matrix
                for each simulation pass, and units.
        """
        # TODO: is there a way to get all of the matrices in one query?
        #  If yes, change get_capacitance_matrix() to get all the matrices and delete this.
        all_mtx = {}
        for i in range(1, 1000):  #1000 is an arbitrary large number
            try:
                df_cmat, user_units = self.get_capacitance_matrix(
                    variation, 'AdaptivePass', pass_number=i)
                c_units = ureg(user_units).to('farads').magnitude
                all_mtx[i] = df_cmat.values * c_units
            except pd.errors.EmptyDataError:
                break
        return all_mtx, user_units

    def lumped_oscillator_vs_passes(self, *args, **kwargs):
        """
        (deprecated) use analysis.quantitative.capacitance_lom.run_lom()
        """
        self.logger.warning(
            'This method is deprecated. Change your scripts to use'
            'analysis.quantitative.capacitance_lom.run_lom()')

    def get_convergence(self) -> bool:
        """Extracts convergence from Ansys simulation result
        """
        # If 'LastAdaptive' is used, then the pass_number won't affect anything.
        # If 'AdaptivePass' is used, then the pass_number is used.
        convergence_df, convergence_txt = self._pinfo.setup.get_convergence()
        target, current, pass_min = self._parse_text_from_q3d_convergence(
            convergence_txt)
        is_converged = self._test_if_q3d_analysis_converged(
            target, current, pass_min)

        return is_converged

    def _test_if_q3d_analysis_converged(cls, target: float, current: float,
                                        passes_min: int) -> Union[bool, None]:
        """Use solution-data from Ansys-Q3d to determine if converged.

        Args:
            target (float): Delta percentage for target. Default is None.
            current (float): Delta percentage for current. Default is None.
            passes_min (int): Regarding convergence, minimum number of passes.
              Default is None.

        Returns:
            Union[bool, None]: Had solution data converged.  Default is None.
        """

        if None not in (target, current, passes_min):
            # Confirm that all three numbers have an value.
            if current <= target and passes_min > 1:
                is_converged = True
                return is_converged
            is_converged = False
            return is_converged

        is_converged = None
        return is_converged

    def _parse_text_from_q3d_convergence(
            self,
            gui_text: str) -> Tuple[Union[None, float], Union[None, float]]:
        """Parse gui_text using a priori known formatting. Ansys-Q3D
        solution-data provides gui_text.

        Args:
            gui_text (str): From Ansys-GUI-SolutionData.

        Returns:
            1st Union[None, float]: Delta percentage for target. Default is None.
            2nd Union[None, float]: Delta percentage for current. Default is None.
        """

        text_list = gui_text.splitlines()

        # Find Target information in text.
        target_all = [string for string in text_list if 'Target' in string]

        # Find Current information in text.
        current_all = [string for string in text_list if 'Current' in string]

        # Find Minimum number of passes from solution-data.
        min_passes_all = [string for string in text_list if 'Minimum' in string]

        target = self._extract_target_delta(target_all)
        current = self._extract_current_delta(current_all)
        min_passes = self._extract_min_passes(min_passes_all)

        return target, current, min_passes

    def _extract_min_passes(self, min_passes_all: list) -> Union[None, float]:
        """Given a pre-formatted list, search and return the "Minimum Number
        Of Passes."

        Args:
            min_passes_all (list): Result of search through string returned from Ansys-Q3D.

        Returns:
            Union[None, float]: Regarding convergence, minimum number of passes.
              Default is None.
        """

        min_num_of_passes = None
        if len(min_passes_all) == 1:
            if min_passes_all[0]:
                _, _, min_passes_str = min_passes_all[0].partition(':')
                try:
                    min_num_of_passes = int(min_passes_str)
                except ValueError:
                    self.design.logger.warning(
                        f'Target={min_passes_str} in GUI is not an int.'
                        'Force Minimum Number Of Passes to be None.')
        else:
            self.design.logger.warning(
                'Either could not find Minimum Number of Passes '
                'information or too many entries in text. '
                'Force Minimum Number of Passes to be None.')
        return min_num_of_passes

    def _extract_target_delta(self, target_all: list) -> Union[None, float]:
        """Given a pre-formatted list, search and return the target-delta
        percentage for convergence.

        Args:
            target_all (list): Result of search through string returned from Ansys-Q3D.

        Returns:
            Union[None, float]: Delta percentage for target. Default is None.
        """

        target = None
        if len(target_all) == 1:
            if target_all[0]:
                _, _, target_str = target_all[0].partition(':')
                try:
                    target = float(target_str)
                except ValueError:
                    self.design.logger.warning(
                        f'Target={target_str} in GUI is not a float.'
                        'Force Target Delta to be None.')
        else:
            self.design.logger.warning(
                'Either could not find Target Delta information or too many '
                'entries in text. Force Target Delta to be None.')
        return target

    def _extract_current_delta(self, current_all: list) -> Union[None, float]:
        """Given a pre-formatted list, search and return the current-delta
        percentage for convergence.

        Args:
            current_all (list): Result of search through string returned from Ansys-Q3D.

        Returns:
            Union[None, float]: Delta percentage for current. Default is None.
        """

        current = None
        if len(current_all) == 1:
            if current_all[0]:
                _, _, current_str = current_all[0].partition(':')
                try:
                    current = float(current_str)
                except ValueError:
                    self.design.logger.warning(
                        f'Target={current_str} in GUI is not a float.'
                        'Force Current Delta to be None.')
        else:
            self.design.logger.warning(
                'Either could not find Current Delta information or too many '
                'entries in text. Force Current Delta to be None.')
        return current

    def plot_convergence_main(self, RES: pd.DataFrame):
        """Plot alpha and frequency versus pass number, as well as convergence
        of delta (in %).

        Args:
            RES (pd.DataFrame): Dictionary of capacitance matrices versus pass number, organized as pandas table.
        """
        if self._pinfo:
            eprd = epr.DistributedAnalysis(self._pinfo)
            epr.toolbox.plotting.mpl_dpi(110)
            return _plot_q3d_convergence_main(eprd, RES)

    def plot_convergence_chi(self, RES: pd.DataFrame):
        """Plot convergence of chi and g, both in MHz, as a function of pass
        number.

        Args:
            RES (pd.DataFrame): Dictionary of capacitance matrices versus pass number, organized as pandas table.
        """
        epr.toolbox.plotting.mpl_dpi(110)
        return _plot_q3d_convergence_chi_f(RES)

    def add_q3d_design(self, name: str, connect: bool = True):
        """
        (deprecated) use new_ansys_design()
        """
        self.logger.warning(
            'This method is deprecated. Change your scripts to use new_ansys_design()'
        )
        self.new_ansys_design(name, 'capacitive', connect)

    def activate_q3d_design(self, name: str = "MetalQ3ds"):
        """
        (deprecated) use activate_ansys_design()
        """
        self.logger.warning(
            'This method is deprecated. Change your scripts to use activate_ansys_design()'
        )
        self.activate_ansys_design(name, 'capacitive')
