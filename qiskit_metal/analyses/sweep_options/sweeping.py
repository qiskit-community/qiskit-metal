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
""" Sweep a qcomponent option, and get results of analysis."""
# pylint: disable=too-many-lines
from typing import Tuple, Union
import pandas as pd

from qiskit_metal import Dict
# pylint: disable=unused-import
# QHFSSRenderer used to describe types in arguments.
from qiskit_metal.renderers.renderer_ansys.hfss_renderer import QHFSSRenderer


class Sweeping():
    """The methods allow users to sweep a variable in a components's options.
    Need access to renderers which are registered in QDesign."""

    def __init__(self, design: 'QDesign'):
        """Give QDesign to this class so Sweeping can access the registered
        QRenderers.

        Args:
            design (QDesign): Used to access the QRenderers.
        """
        self.design = design

    @classmethod
    def option_value(cls, a_dict: Dict, search: str) -> str:
        """Get value from dict based on key.  This method is used for unknown
        depth, dict search, within a dict.

        Args:
            a_dict (Dict): Dictionary to get values from
            search (str): String to search for

        Returns:
            str: Value from the dictionary of the searched term.
        """
        value = a_dict[search]
        return value

    def error_check_sweep_input(self, qcomp_name: str, option_name: str,
                                option_sweep: list) -> Tuple[list, Dict, int]:
        """ Implement error checking of data for sweeping.

        Args:
            qcomp_name (str): Component that contains the option to be swept.
            option_name (str): The option within qcomp_name to sweep.
            option_sweep (list): Each entry in the list is a value
                                for option_name.

        Returns:
            list: Traverse the option Dict.
            addict.addict.Dict: Value from the dictionary of the searched key.
            int: Observation of searching for data from arguments.

            * 0 Error not detected in the input-data.
            * 1 qcomp_name not registered in design.
            * 2 option_name is empty.
            * 3 option_name is not found as key in Dict.
            * 4 option_sweep is empty, need at least one entry.
        """
        option_path = None
        a_value = None

        if len(option_sweep) == 0:
            return option_path, a_value, 4

        if option_name:
            option_path = option_name.split('.')
        else:
            return option_path, a_value, 2

        if qcomp_name in self.design.components.keys():
            qcomp_options = self.design.components[qcomp_name].options
        else:
            return option_path, a_value, 1

        a_value = qcomp_options

        # All but the last item in list.
        for name in option_path[:-1]:
            if name in a_value:
                a_value = self.option_value(a_value, name)
            else:
                self.design.logger.warning(f'Key="{name}" is not in dict.')
                return option_path, a_value, 3

        return option_path, a_value, 0

    def prep_drivenmodal_setup(self, setup_args: Dict) -> int:
        """User can pass arguments for method drivenmodal setup.  If not passed,
        method will use the options in HFSS default_options. The name of setup
        will be "Sweep_dm_setup".  If a setup named "Sweep_dm_setup" exists
        in the project, it will be deleted, and a new setup will be added
        with the arguments from setup_args.

        Assume: Error checking has already occurred for existence of Ansys,
        project, and HFSS eigenmode design has been connected to pinfo.

        Args:
            setup_args (Dict):  Maximum  keys used in setup_args.

        **setup_args** dict contents:
            * freq_ghz (float, optional): Frequency in GHz.  Defaults to 5.
            * max_delta_s (float, optional): Absolute value of maximum
                    difference in scattering parameter S. Defaults to 0.1.
            * max_passes (int, optional): Maximum number of passes.
              Defaults to 10.
            * min_passes (int, optional): Minimum number of passes.
              Defaults to 1.
            * min_converged (int, optional): Minimum number of converged
              passes.  Defaults to 1.
            * pct_refinement (int, optional): Percent refinement.
              Defaults to 30.
            * basis_order (int, optional): Basis order. Defaults to 1.

        Returns:
            int: The return code of status.
                * 0 Setup of "Sweep_dm_setup" added to design with setup_args.
                * 1 Look at warning message to determine which argument was of
                  the wrong data type.
                * 2 Look at warning message, a key in setup_args that was
                  not expected.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements

        a_hfss = self.design.renderers.hfss
        setup_args.name = "Sweep_dm_setup"
        a_hfss.pinfo.design.delete_setup(setup_args.name)

        for key, value in setup_args.items():
            if key == "name":
                continue  #For this method, "Sweep_dm_setup" used.
            if key == "freq_ghz":
                if isinstance(value, float) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "float")
                return 1
            if key == "max_delta_s":
                if isinstance(value, float) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "float")
                return 1
            if key == 'max_passes':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'min_passes':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'min_converged':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'basis_order':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'pct_refinement':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1

            self.design.logger.warning(
                f'The key={key} is not expected.  Do you have a typo?  '
                f'The setup was not added to design. '
                f'Sweep will not be implemented.')
            return 2

        a_hfss.add_drivenmodal_setup(**setup_args)
        a_hfss.activate_drivenmodal_setup(setup_args.name)
        return 0

    def prep_eigenmode_setup(self, setup_args: Dict) -> int:
        """User can pass arguments for method eigenmode setup.  If not passed,
        method will use the options in HFSS default_options. The name of setup
        will be "Sweep_em_setup".  If a setup named "Sweep_em_setup" exists
        in the project, it will be deleted, and a new setup will be added
        with the arguments from setup_args.

        Assume: Error checking has already occurred for existence of Ansys,
        project, and HFSS eigenmode design has been connected to pinfo.

        Args:
            setup_args (Dict):  Maximum  keys used in setup_args.

        **setup_args** dict contents:
            * min_freq_ghz (int, optional): Minimum frequency in GHz.
              Defaults to 1.
            * n_modes (int, optional): Number of modes. Defaults to 1.
            * max_delta_f (float, optional): Maximum difference in
              freq between consecutive passes.
              Defaults to 0.5.
            * max_passes (int, optional): Maximum number of passes.
              Defaults to 10.
            * min_passes (int, optional): Minimum number of passes.
              Defaults to 1.
            * min_converged (int, optional): Minimum number of converged
              passes.  Defaults to 1.
            * pct_refinement (int, optional): Percent refinement.
              Defaults to 30.
            * basis_order (int, optional): Basis order. Defaults to -1.

        Returns:
            int: The return code of status.
                * 0 Setup of "Sweep_em_setup" added to design with setup_args.
                * 1 Look at warning message to determine which argument was of
                  the wrong data type.
                * 2 Look at warning message, a key in setup_args that was
                  not expected.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements

        a_hfss = self.design.renderers.hfss
        setup_args.name = "Sweep_em_setup"
        a_hfss.pinfo.design.delete_setup(setup_args.name)

        for key, value in setup_args.items():
            if key == "name":
                continue  #For this method, "Sweep_em_setup" used.
            if key == "min_freq_ghz":
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == "n_modes":
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == "max_delta_f":
                if isinstance(value, float) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "float")
                return 1
            if key == 'max_passes':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'min_passes':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'min_converged':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'basis_order':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'pct_refinement':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1

            self.design.logger.warning(
                f'The key={key} is not expected.  Do you have a typo?  '
                f'The setup was not added to design. '
                f'Sweep will not be implemented.')
            return 2

        a_hfss.add_eigenmode_setup(**setup_args)
        a_hfss.activate_eigenmode_setup(setup_args.name)
        return 0

    def warning_for_setup(self, setup_args: Dict, key: str, data_type: str):
        """Give a warning based on key/value of Dict.

        Args:
            setup_args (Dict): Holds the key/value of setup arguments
                        that are of interest.
            key (str): Name of setup argument.
            data_type (str): The data type the argument should be.
        """
        self.design.logger.warning(
            f'The value for {key} should be a {data_type}. '
            f'The present value is {setup_args[key]}.  '
            f'Sweep will not be implemented.')

    def prep_q3d_setup(self, setup_args: Dict) -> int:
        """User can pass arguments for method q3d setup.  If not passed,
        method will use the options in Q3D renderer default_options.
        The name of setup will be "Sweep_q3d_setup".  If a setup named
        "Sweep_q3d_setup" exists in the project, it will be deleted, and
        a new setup will be added with the arguments from setup_args.

        Assume: Error checking has already occurred for existence of Ansys,
        project, and Q3d Extractor design has been connected to pinfo.

        Args:
            setup_args (Dict): Maximum  keys used in setup_args.

        **setup_args** dict contents:
            * freq_ghz (float, optional): Frequency in GHz. Defaults to 5..
            * name (str, optional): Name of solution setup.
                        Defaults to "Setup".
            * max_passes (int, optional): Maximum number of passes.
                        Defaults to 15.
            * min_passes (int, optional): Minimum number of passes.
                        Defaults to 2.
            * percent_error (float, optional): Error tolerance as percentage.
                        Defaults to 0.5.
            * save_fields (bool, optional): Whether or not to save fields.
                        Defaults to False.
            * enabled (bool, optional): Whether or not setup is enabled.
                        Defaults to True.
            * min_converged_passes (int, optional): Minimum number of
                        converged passes. Defaults to 2.
            * percent_refinement (int, optional): Refinement as a percentage.
                        Defaults to 30.
            * auto_increase_solution_order (bool, optional): Whether or not
                        to increase solution order automatically.
                        Defaults to True.
            * solution_order (str, optional): Solution order.
                        Defaults to 'High'.
            * solver_type (str, optional): Solver type.
                        Defaults to 'Iterative'.

        Returns:
            int:  The return code of status.
                * 0 Setup of "Sweep_q3d_setup" added to design with setup_args.
                * 1 Look at warning message to determine which argument was
                        of the wrong data type.
                * 2 Look at warning message, a key in setup_args that was not
                        expected.
        """
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements

        a_q3d = self.design.renderers.q3d
        setup_args.name = "Sweep_q3d_setup"
        a_q3d.pinfo.design.delete_setup(setup_args.name)

        for key, value in setup_args.items():
            if key == "name":
                continue  #For this method, "Sweep_q3d_setup" used.
            if key == "freq_ghz":
                if isinstance(value, float) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "float")
                return 1
            if key == 'max_passes':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'min_passes':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'percent_error':
                if isinstance(value, float) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "float")
                return 1
            if key == 'save_fields':
                if isinstance(value, bool) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "bool")
                return 1
            if key == 'enabled':
                if isinstance(value, bool) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "bool")
                return 1
            if key == 'min_converged_passes':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'percent_refinement':
                if isinstance(value, int) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "int")
                return 1
            if key == 'auto_increase_solution_order':
                if isinstance(value, bool) or value is None:
                    continue
                self.warning_for_setup(setup_args, key, "bool")
                return 1
            if key == 'solution_order':
                if (isinstance(value, str) and
                        value in ["High", "Normal", "Higher", "Highest"
                                 ]) or value is None:
                    continue
                self.design.logger.warning(
                    f'The value for solution_order should be a str '
                    f'in ["High", "Normal", "Higher", "Highest"]. '
                    f'The present value is {value}.  '
                    f'Sweep will not be implemented.')
                return 1
            if key == 'solver_type':
                if isinstance(value, str) or value is None:
                    continue

                self.warning_for_setup(setup_args, key, "str")
                return 1

            self.design.logger.warning(
                f'The key={key} is not expected.  Do you have a typo?  '
                f'The setup was not added to design. '
                f'Sweep will not be implemented.')
            return 2

        a_q3d.add_q3d_setup(**setup_args)
        a_q3d.activate_q3d_setup(setup_args.name)
        return 0

    def sweep_one_option_get_eigenmode_solution_data(
            self,
            qcomp_name: str,
            option_name: str,
            option_sweep: list,
            qcomp_render: list,
            endcaps_render: list,
            ignored_jjs_render: list,
            box_plus_buffer_render: bool = True,
            setup_args: Dict = None,
            leave_last_design: bool = True,
            design_name: str = "Sweep_Eigenmode") -> Tuple[Dict, int]:
        """
        Ansys must be open with inserted project. A design, "HFSS Design"
        with eigenmode solution-type will be inserted by this method.

        Args:
            qcomp_name (str): A component that contains the option to be
                                swept. Assume qcomp_name is in qcomp_render.
            option_name (str): The option within qcomp_name to sweep.
                                Follow details from
                                renderer in QHFSSRenderer.render_design.
            option_sweep (list): Each entry in the list is a value for
                                option_name.
            qcomp_render(list): List of components to render to Ansys.
            endcaps_render (list): Identify which kind of pins.
                                    Follow details from renderer in
                                    QHFSSRenderer.render_design.
            ignored_jjs_render (list): List of tuples of jj's that shouldn't
                                    be rendered.  Follow details from
                                    renderer in QHFSSRenderer.render_design.
            box_plus_buffer_render (bool): Either calculate a bounding box
                                    based on the location of rendered
                                    geometries or use chip size from design
                                    class.  Follow details from renderer in
                                    QHFSSRenderer.render_design.
                                    Default is True.
            setup_args (Dict): Hold the arguments for  Hfss eigenmode setup()
                                    as  key/values to pass to Ansys.
                                    If None, default Setup will be used.
            leave_last_design (bool): In HFSS, after the last sweep,
                                    should the design be cleared?
                                    Default is True.
            design_name (str, optional):  Name of HFSS_design to use in
                                    project. Defaults to "Sweep_Eigenmode".

        Returns:
            Tuple[Dict, int]: The dict key is each value of option_sweep, the
            value is the solution-data for each sweep.
            The int is the observation of searching for data from arguments as
            defined below.

            * 0 Have list of capacitance matrix.
            * 1 qcomp_name not registered in design.
            * 2 option_name is empty.
            * 3 option_name is not found as key in dict.
            * 4 option_sweep is empty, need at least one entry.
            * 5 last key in option_name is not in dict.
            * 6 project not in app
            * 7 design not in app
            * 8 setup not implement, check the setup_args.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-arguments

        #Dict of all swept information.
        all_sweep = Dict()
        option_path, a_value, check_result, = self.error_check_sweep_input(
            qcomp_name, option_name, option_sweep)
        if check_result != 0:
            return all_sweep, check_result

        a_hfss = self.design.renderers.hfss
        # Assume Ansys is open, with a project open.
        a_hfss.connect_ansys()
        a_hfss.activate_eigenmode_design(design_name)

        a_hfss.clean_active_design()

        if self.prep_eigenmode_setup(setup_args) != 0:
            self.design.logger.warning(
                'The setup was not implemented, look at warning messages.')
            return all_sweep, 8

        len_sweep = len(option_sweep) - 1

        for index, item in enumerate(option_sweep):
            if option_path[-1] in a_value.keys():
                a_value[option_path[-1]] = item
            else:
                self.design.logger.warning(
                    f'Key="{option_path[-1]}" is not in dict.')
                return all_sweep, 5

            self.design.rebuild()

            a_hfss.render_design(selection=qcomp_render,
                                 open_pins=endcaps_render,
                                 ignored_jjs=ignored_jjs_render,
                                 box_plus_buffer=box_plus_buffer_render
                                )  #Render the items chosen

            a_hfss.analyze_setup(
                a_hfss.pinfo.setup.name)  #Analyze said solution setup.
            setup = a_hfss.pinfo.setup
            #solution_name = setup.solution_name
            all_solutions = setup.get_solutions()
            #setup_names = all_solutions.list_variations()
            freqs, kappa_over_2pis = all_solutions.eigenmodes()
            df_t, df_f, _, convergence = self.hfss_em_get_convergence(a_hfss)

            if not convergence:
                self.design.logger.warning(
                    f'Heads-Up: {option_name}={item} Failed to converge.  ')

            sweep_values = Dict()

            sweep_values['convergence'] = convergence
            sweep_values['option_name'] = option_path[-1]
            sweep_values['frequency'] = freqs
            sweep_values['kappa_over_2pis'] = kappa_over_2pis
            sweep_values['quality_factor'] = self.get_quality_factor(
                freqs, kappa_over_2pis)

            sweep_values['convergence_eig_f'] = df_f
            sweep_values['convergence_t'] = df_t
            all_sweep[item] = sweep_values

            #Decide if need to clean the design.
            obj_names = a_hfss.pinfo.get_all_object_names()
            if obj_names:
                if index == len_sweep and not leave_last_design:
                    a_hfss.clean_active_design()
                elif index != len_sweep:
                    a_hfss.clean_active_design()

        a_hfss.disconnect_ansys()
        return all_sweep, 0

    def hfss_em_get_convergence(
        self,
        a_hfss: 'QHFSSRenderer',
        variation: str = None
    ) -> Tuple[pd.core.frame.DataFrame, pd.core.frame.DataFrame, str, bool]:
        """Use QHFSSRenderer to get convergence data from Ansys for eigenmode.

        Args:
            a_hfss (QHFSSRenderer): Reference to renderer to Ansys.
            variation (str, optional): Information from pyEPR; variation should
                        be in the form variation = "scale_factor='1.2001'".
                        Defaults to None.

        Returns:
            Tuple[pd.core.frame.DataFrame, pd.core.frame.DataFramestr, str, str]:
            1st DataFrame: Convergence_t
            2nd DataFrame: Convergence_f
            3rd list: Text from GUI of solution data.
            4th bool: If data converged.
        """
        convergence_t, convergence_f, gui_text = a_hfss.get_convergences(
            variation)

        text_list, convergence = self.parse_text_from_hfss_convergence(gui_text)

        return convergence_t, convergence_f, text_list, convergence

    def parse_text_from_hfss_convergence(self,
                                         gui_text: str) -> Tuple[list, bool]:
        """Parse the text obtained from hfss after analysis.

        Args:
            gui_text (str): Text from GUI of solution data.

        Returns:
            Tuple[list, bool]: All parsed information
            1st list: Text from GUI of solution data.
            2nd bool: If data converged.
        """
        text_list = gui_text.splitlines()

        # Find convergence information in text.
        convergence_bool = [
            string for string in text_list if 'Converged' in string
        ]
        if len(convergence_bool) == 1:
            if 'Yes' in convergence_bool[0]:
                convergence = True
            else:
                convergence = False
        else:
            convergence = False
            self.design.logger.warning(
                'Either could not find Converged information or too many '
                'entries in text. Force convergence to be False.')
        return text_list, convergence

    def hfss_dm_get_convergence(
            self,
            a_hfss: 'QHFSSRenderer',
            variation: str = None) -> Tuple[pd.core.frame.DataFrame, str, bool]:
        """Use QHFSSRenderer to get convergence data from Ansys for drivenmodal.

        Args:
            a_hfss (QHFSSRenderer): Reference to renderer to Ansys.
            variation (str, optional): Information from pyEPR; variation should
                            be in the form variation = "scale_factor='1.2001'".
                            Defaults to None.

        Returns:
            Tuple[pd.core.frame.DataFrame, str, bool]:
            1st DataFrame: Convergence_t
            2nd list: Text from GUI of solution data.
            3rd bool: If data converged.
        """

        convergence_t, _, gui_text = a_hfss.get_convergences(variation)
        text_list, convergence = self.parse_text_from_hfss_convergence(gui_text)
        return convergence_t, text_list, convergence

    def sweep_one_option_get_drivenmodal_solution_data(
            self,
            qcomp_name: str,
            option_name: str,
            option_sweep: list,
            dm_render_args: Dict,
            dm_add_sweep_args: Dict,
            setup_args: Dict = None,
            leave_last_design: bool = True,
            design_name: str = "Sweep_DrivenModal") -> Tuple[Dict, int]:
        """
        Ansys must be open with inserted project. A design, "HFSS Design"
        with Driven Modal solution-type will be inserted by this method.

        Args:
            qcomp_name (str): A component that contains the option to be
                                swept. Assume qcomp_name is in qcomp_render.
            option_name (str): The option within qcomp_name to sweep.
            option_sweep (list): Each entry in the list is a value for
                                option_name.
            dm_render_args (Dict): Arguments to pass to render_design().
                                Next six items are key/value pairs.
            *selection(list): List of components to render to Ansys.
            *open_pins (list): Identify which kind of pins.
                                    Follow details from renderer in
                                    QHFSSRenderer.render_design.
            *port_list (list): List of tuples of jj's that shouldn't
                                    be rendered.  Follow details from
                                    renderer in QHFSSRenderer.render_design.
            *jj_to_port (list): List of junctions (qcomp, qgeometry_name,
                                impedance, draw_ind) to render as lumped ports
                                or as lumped port in parallel with a sheet
                                inductance.    Follow details from renderer
                                in QHFSSRenderer.render_design.
            *ignored_jjs (list): List of junctions (qcomp, qgeometry_name) to
                                omit altogether during rendering.   Follow
                                details from renderer in
                                QHFSSRenderer.render_design.
            *box_plus_buffer (bool): Either calculate a bounding box
                                    based on the location of rendered
                                    geometries or use chip size from design
                                    class.  Follow details from renderer in
                                    QHFSSRenderer.render_design.
                                    Default is True.
            dm_add_sweep_args(Dict): Arguments to pass to insert_sweep() in
                                    pyEPR, through add_sweep in QHFSSRenderer.
                                    Next 7 items are key/value pairs, if passed
                                    will be used. start_ghz and
                                    stop_ghz must be passed. Follow details from
                                    insert_sweep()  in pyEPR.  If an allowable key is not
                                    passed, the default will be used.  You can
                                    provide either step_ghz OR count when
                                    inserting an HFSS driven model freq sweep.
                                    DO NOT provide both OR neither!

            *start_ghz (float): Starting frequency of sweep in GHz.
            *stop_ghz (float):  Ending frequency of sweep in GHz.
            *count(int):  Total number of frequencies.  Defaults to 101.
            step_ghz ([type]): Difference between adjacent frequencies.
                            Defaults to None.
            *name (str): Name of sweep. Defaults to "Sweep_options__dm_sweep".
            *type(str): Type of sweep.   Defaults to "Fast". Choose from
                        'Fast', 'Interpolating', 'Discrete'.
            *save_fields (bool): Whether or not to save fields.
                                 Defaults to False.

            setup_args (Dict): Hold the arguments for  Hfss driven-modal setup()
                                    as  key/values to pass to Ansys.
                                    If None, default Setup will be used.

            leave_last_design (bool): In HFSS, after the last sweep,
                                    should the design be cleared?
                                    Default is True.
            design_name (str, optional):  Name of HFSS_design to use in
                                    project. Defaults to "Sweep_DrivenModal".

        Returns:
            Tuple[Dict, int]: The dict key is each value of option_sweep, the
            value is the solution-data for each sweep.
            There is a pandas dataframe for Scatter matrix, Impedance matrix,
            and Admittance matrix.

            The int is the observation of searching for data from arguments as
            defined below.

            * 0 Have list of capacitance matrix.
            * 1 qcomp_name not registered in design.
            * 2 option_name is empty.
            * 3 option_name is not found as key in Dict.
            * 4 option_sweep is empty, need at least one entry.
            * 5 last key in option_name is not in Dict.
            * 6 project not in app
            * 7 design not in app
            * 8 setup not implement, check the setup_args.
            * 9 dm_render_args is missing keys in the Dict.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-arguments

        #Dict of all swept information.
        all_sweep = Dict()
        option_path, a_value, check_result, = self.error_check_sweep_input(
            qcomp_name, option_name, option_sweep)
        if check_result != 0:
            return all_sweep, check_result

        a_hfss = self.design.renderers.hfss
        # Assume Ansys is open, with a project open.
        a_hfss.connect_ansys()
        a_hfss.activate_drivenmodal_design(design_name)

        a_hfss.clean_active_design()

        if self.prep_drivenmodal_setup(setup_args) != 0:
            self.design.logger.warning(
                'The setup was not implemented, look at warning messages.')
            return all_sweep, 8

        if self.error_check_render_design_args(dm_render_args) != 0:
            return all_sweep, 9

        len_sweep = len(option_sweep) - 1

        for index, item in enumerate(option_sweep):
            if option_path[-1] in a_value.keys():
                a_value[option_path[-1]] = item
            else:
                self.design.logger.warning(
                    f'Key="{option_path[-1]}" is not in dict.')
                return all_sweep, 5

            self.design.rebuild()

            a_hfss.render_design(selection=dm_render_args.selection,
                                 open_pins=dm_render_args.open_pins,
                                 port_list=dm_render_args.port_list,
                                 jj_to_port=dm_render_args.jj_to_port,
                                 ignored_jjs=dm_render_args.ignored_jjs,
                                 box_plus_buffer=dm_render_args.box_plus_buffer)

            #To insert a "frequency sweep" within setup,
            # the pin/ports have to be rendered.
            self.error_check_and_insert_sweep(a_hfss, setup_args.name,
                                              dm_add_sweep_args)

            matrix_size = self.get_size_of_matrix(dm_render_args)

            self.populate_dm_all_sweep(all_sweep, a_hfss, dm_add_sweep_args,
                                       setup_args, matrix_size, item,
                                       option_name)
            #Decide if need to clean the design.
            obj_names = a_hfss.pinfo.get_all_object_names()
            if obj_names:
                if index == len_sweep and not leave_last_design:
                    a_hfss.clean_active_design()
                elif index != len_sweep:
                    a_hfss.clean_active_design()

        a_hfss.disconnect_ansys()
        return all_sweep, 0

    def populate_dm_all_sweep(self, all_sweep: Dict, a_hfss: 'QHFSSRenderer',
                              dm_add_sweep_args: Dict, setup_args: Dict,
                              matrix_size: int, item: str, option_name: str):
        """The Dict all_sweep holds three matrices for each iteration of a
        option in Metal.

        Args:
            all_sweep (Dict): To hold the output for each iteration of option
                             from Metal.
            a_hfss (QHFSSRenderer): Reference to Metal Ansys renderer.
            dm_add_sweep_args (Dict): Has name of sweep in setup.
            setup_args (Dict): Has name of setup.
            matrix_size (int): Size of matrix to retreive from Ansys sweep.
            item (str): Each value of option in Metal to iterate through.
            option_name (str): The option within qcomp_name to sweep.
        """
        sweep_values = Dict()
        if matrix_size == 0:
            sweep_values['s_matrix'] = None
            sweep_values['y_matrix'] = None
            sweep_values['z_matrix'] = None
        else:
            a_hfss.analyze_sweep(dm_add_sweep_args.name, setup_args.name)
            # pylint: disable=invalid-name
            s_Pparms, y_Pparams, z_Pparams = a_hfss.get_all_Pparms_matrices(
                matrix_size)

            convergence_t, dummy_text_list, convergence = self.hfss_dm_get_convergence(
                a_hfss, variation=None)
            sweep_values['option_name'] = option_name
            sweep_values['convergence'] = convergence
            sweep_values['s_matrix'] = s_Pparms
            sweep_values['y_matrix'] = y_Pparams
            sweep_values['z_matrix'] = z_Pparams
            sweep_values['convergence_t'] = convergence_t
        all_sweep[item] = sweep_values

    @classmethod
    def get_size_of_matrix(cls, dm_render_args: Dict) -> int:
        """Determine the size of s_matrix, y_matrix, z_matrix.
        s_matrix =
        size of list of pins to render to lumped port +
        size of list of junctions to render as lumped port.

        size of matrix = size of 3rd parameter + size of fourth parfameter

        List of arguments for render_design:
            - First parameter: List of components to render
                            (empty list if rendering whole Metal design)
            - Second parameter: List of pins (qcomp, pin) with open endcaps
            - Third parameter: List of pins (qcomp, pin, impedance) to render as lumped ports
            - Fourth parameter: List of junctions (qcomp, qgeometry_name, impedance, draw_ind)
               to render as lumped ports or as lumped port in parallel with a sheet inductance
            - Fifth parameter: List of junctions (qcomp, qgeometry_name) to
                            omit altogether during rendering
            - Sixth parameter: Whether to render chip via box plus buffer or fixed chip size

        Args:
            dm_render_args (Dict): Holds the arguments used for render_design.

        Returns:
            int: Size of expected S-matrix.
        """
        matrix_size = 0
        if dm_render_args.port_list:
            matrix_size += len(dm_render_args.port_list)
        if dm_render_args.jj_to_port:
            matrix_size += len(dm_render_args.jj_to_port)

        return matrix_size

    def error_check_and_insert_sweep(
            self,
            a_hfss: 'QHFSSRenderer',
            setup_name: str,
            dm_add_sweep_args: Dict,
            dm_sweep_name: str = 'Sweep_options__dm_sweep'):
        """To insert an Ansys sweep to the named setup.  The Dict
        dm_add_sweep_args comes from user. They are arguments to pass to
        add sweep to Ansys.  If there are unexpected arguments, they will
        be removed.

        Args:
            a_hfss (QHFSSRenderer): Reference to Ansys renderer.
            setup_name (str): Name of active setup in active project.
            dm_add_sweep_args (Dict): Arguments to pass to
                        QHFSSRenderer.add_sweep.  If key is not in Dict, the
                        default value will be used.  The keys have to match
                        arguments which are passed to insert_sweep() in pyEPR,
                        through add_sweep in QHFSSRenderer.
            dm_sweep_name (str, optional): Name of inserted Ansys sweep.
                                    qDefaults to 'Sweep_options__dm_sweep'.
        """
        if 'name' not in dm_add_sweep_args.keys():
            dm_add_sweep_args['name'] = dm_sweep_name

        allowed_keys = {
            'start_ghz', 'stop_ghz', 'count', 'step_ghz', 'name', 'type',
            'save_fields'
        }
        unexpected_keys = set(dm_add_sweep_args.keys()) - allowed_keys

        if unexpected_keys:
            #[dm_add_sweep_args.pop(key) for key in unexpected_keys]
            self.design.logger.warning(
                f'Removed keys: {unexpected_keys} from '
                'dm_add_sweep_args Dict before using it. ')

        # pylint: disable=protected-access
        all_sweep_names = a_hfss.pinfo.setup._setup_module.GetSweeps(setup_name)
        if dm_add_sweep_args.name not in all_sweep_names:
            a_hfss.add_sweep(setup_name=setup_name, **dm_add_sweep_args)

    def error_check_render_design_args(self, dm_render_args: Dict) -> int:  # pylint: disable=too-many-return-statements
        """To render to Ansys, we need every argument in render_design.
        This method confirms all arguments are present.

        Args:
            dm_render_args (Dict): Dict that has the key=argument name,
                        value=data for argument.

        Returns:
            int: Return code.
            * 0 All the expected keys in Dict.
            * 1 A key is missing in dm_render_args Dict, look at warning message.
        """
        all_keys = dm_render_args.keys()

        if 'selection' not in all_keys:
            self.design.logger.warning(
                'The key selection is missing in Dict dm_render_args. '
                'Method render_design() NOT implemented.')
            return 1
        if 'open_pins' not in all_keys:
            self.design.logger.warning(
                'The key open_pins is missing in Dict dm_render_args. '
                'Method render_design() NOT implemented.')
            return 1
        if 'port_list' not in all_keys:
            self.design.logger.warning(
                'The key port_list is missing in Dict dm_render_args. '
                'Method render_design() NOT implemented.')
            return 1
        if 'jj_to_port' not in all_keys:
            self.design.logger.warning(
                'The key jj_to_port is missing in Dict dm_render_args. '
                'Method render_design() NOT implemented.')
            return 1
        if 'ignored_jjs' not in all_keys:
            self.design.logger.warning(
                'The key ignored_jjs is missing in Dict dm_render_args. '
                'Method render_design() NOT implemented.')
            return 1
        if 'box_plus_buffer' not in all_keys:
            self.design.logger.warning(
                'The key box_plus_buffer is missing in Dict dm_render_args. '
                'Method render_design() NOT implemented.')
            return 1
        return 0

    def get_quality_factor(
            self,
            freqs: Union[list, None] = None,
            kappa_over_2pis: Union[list, None] = None) -> Union[list, None]:
        """Calculate Quality Factor = freqs/kappa_over_2pis.  Before division,
        some error checking.

        Args:
            freqs (Union[list, None], optional): The eigenmode frequency.
                                                Defaults to None.
            kappa_over_2pis (Union[list, None], optional): The kappa/(2*pi).
                                                Defaults to None.

        Returns:
            Union[list, None]: Calculate freqs/kappa_over_2pis
        """

        quality_factor = None
        if kappa_over_2pis is None:
            return quality_factor

        # Assume both are lists or None since method:  eigenmodes()
        #                              in pyEPR returns a list or None.
        if len(freqs) == len(kappa_over_2pis):
            quality_factor = [
                float(ff) / float(kk) for ff, kk in zip(freqs, kappa_over_2pis)
            ]
            return quality_factor

        self.design.logger.warning(
            'The Quality factor not calculated since size of freqs'
            ' and kappa_over_2pis are not identical')
        return quality_factor

    def sweep_one_option_get_capacitance_matrix(
            self,
            qcomp_name: str,
            option_name: str,
            option_sweep: list,
            qcomp_render: list,
            endcaps_render: list,
            setup_args: Dict = None,
            leave_last_design: bool = True,
            design_name: str = "Sweep_Capacitance") -> Tuple[Dict, int]:
        """Ansys must be open with an inserted project.  A design,
        "Q3D Extractor Design", will be inserted by this method.

        Args:
            qcomp_name (str): A component that contains the option to be swept.
            option_name (str): The option within qcomp_name to sweep.
            option_sweep (list): Each entry in the list is a value for
                        option_name.
            qcomp_render (list): The component to render to Q3D.
            endcaps_render (list): Identify which kind of pins. Follow the
                        details from renderer QQ3DRenderer.render_design.
            setup_args (Dict): Hold the arguments for  Q3d setup() as
                        key/values to pass to Ansys.
                        If None, default Setup will be used.
            leave_last_design (bool) : In Q3d, after the last sweep, should
                        the design be cleared?
            design_name(str): Name of q3d_design to use in project.

        Returns:
            Dict or int: If dict, the key is each value of option_sweep, the
            value is the capacitance matrix for each sweep.
            If int, observation of searching for data from arguments as
            defined below:

            * 0 Have list of capacitance matrix.
            * 1 qcomp_name not registered in design.
            * 2 option_name is empty.
            * 3 option_name is not found as key in Dict.
            * 4 option_sweep is empty, need at least one entry.
            * 5 last key in option_name is not in Dict.
            * 6 project not in app
            * 7 design not in app
            * 8 setup not implement, check the setup_args.

        """
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals

        #Dict of all swept information.
        all_sweep = Dict()
        option_path, a_value, check_result = self.error_check_sweep_input(
            qcomp_name, option_name, option_sweep)
        if check_result != 0:
            return all_sweep, check_result

        a_q3d = self.design.renderers.q3d
        # Assume Ansys is open, with a project open.
        a_q3d.connect_ansys()
        a_q3d.activate_q3d_design(design_name)

        a_q3d.clean_active_design()

        # Add a solution setup.
        if self.prep_q3d_setup(setup_args) != 0:
            self.design.logger.warning('The setup was not implemented, '
                                       'please look at warning messages.')
            return all_sweep, 8

        len_sweep = len(option_sweep) - 1

        # Last item in list.
        for index, item in enumerate(option_sweep):
            if option_path[-1] in a_value.keys():
                a_value[option_path[-1]] = item
            else:
                self.design.logger.warning(
                    f'Key="{option_path[-1]}" is not in dict.')
                return all_sweep, 5

            self.design.rebuild()

            a_q3d.render_design(
                selection=qcomp_render,
                open_pins=endcaps_render)  #Render the items chosen

            self.populate_q3d_all_sweep(all_sweep, a_q3d, item, option_name)

            #Decide if need to clean the design.
            obj_names = a_q3d.pinfo.get_all_object_names()
            if obj_names:
                if index == len_sweep and not leave_last_design:
                    a_q3d.clean_active_design()
                elif index != len_sweep:
                    a_q3d.clean_active_design()

        a_q3d.disconnect_ansys()
        return all_sweep, 0

    def populate_q3d_all_sweep(self, all_sweep: Dict, a_q3d: 'QQ3DRenderer',
                               item: str, option_name: str):
        """Analyze the setup, get convergence and capacitance information,
        populate all_sweep for each item which corresponds to option_name.

        Args:
            all_sweep (Dict): Reference to hold each item which corresponds
              to option_name.
            a_q3d (QQ3DRenderer): Reference to Ansys-Q3D renderer.
            item (str): The value of each item that we want to sweep
              in option_name.
            option_name (str): The option of QComponent that we want to sweep.
        """

        #Analyze said solution setup.
        a_q3d.analyze_setup(a_q3d.pinfo.setup.name)

        # If 'LastAdaptive' is used, then the pass_number won't affect anything.
        # If 'AdaptivePass' is used, then the pass_number is used.
        convergence_df, convergence_txt = a_q3d.pinfo.setup.get_convergence()
        target, current, pass_min = self._parse_text_from_q3d_convergence(
            convergence_txt)
        is_converged = self._test_if_q3d_analysis_converged(
            target, current, pass_min)
        cap_matrix = a_q3d.get_capacitance_matrix(variation='',
                                                  solution_kind='LastAdaptive',
                                                  pass_number=1)

        sweep_values = Dict()
        sweep_values['option_name'] = option_name
        #sweep_values['option_name'] = option_path[-1]
        sweep_values['convergence_target'] = target
        sweep_values['convergence_current'] = current
        sweep_values['min_number_passes'] = pass_min
        sweep_values['is_convergence'] = is_converged
        sweep_values['capacitance'] = cap_matrix
        sweep_values['convergence_data'] = convergence_df
        all_sweep[item] = sweep_values

    @classmethod
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
        """Parse gui_text using apriori known formatting. Ansys-Q3D
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


# The methods allow users to sweep a variable in a components's options.
