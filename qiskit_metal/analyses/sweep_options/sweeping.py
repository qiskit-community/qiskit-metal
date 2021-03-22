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

from typing import List, Tuple, Union, Any, Iterable, Dict
from qiskit_metal.renderers.renderer_ansys.hfss_renderer import QHFSSRenderer, QAnsysRenderer
from qiskit_metal.renderers.renderer_ansys.q3d_renderer import QQ3DRenderer


class Sweeping():
    """  The methods allow users to sweep a variable in a components's options.  
    Need access to renderers which are registered in QDesign.
    """

    def __init__(self, design: 'QDesign'):
        """Give QDesign to this class so Sweeping can access the registered QRenderers.

        Args:
            design (QDesign): Used to access the QRenderers. 
        """
        self.design = design

    def option_value(self, a_dict, search: str) -> str:
        """Get value from dict based on key.  This method is used for unknown depth,
        dict search, within a dict.
        
        Args:
            a_dict (dict): Dictionary to get values from
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
            qcomp_name (str): A component that contains the option to be swept.
            option_name (str): The option within qcomp_name to sweep.
            option_sweep (list): Each entry in the list is a value for option_name.

        Returns:
            list: Traverse the option Dict.  
            addict.addict.Dict: Value from the dictionary of the searched key.
            int: Observation of searching for data from arguments.

            * 0 Error not detected in the input-data.
            * 1 qcomp_name not registered in design.
            * 2 option_name is empty.
            * 3 option_name is not found as key in dict.
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

    def handle_eignmode_setup(self, a_hfss: QHFSSRenderer, setup_args: Dict):
        """User can pass arguments for method add_eigenmode_setup().  If not passed, use the options in 
        HFSS default_options.

        Args:
            a_hfss (QHFSSRenderer): Reference to instantiated  renderer to HFSS.
            setup_args (Dict): a Dict 
        """
        '''
                Args:
            name (str, optional): Name of eigenmode setup. Defaults to "Setup".
            min_freq_ghz (int, optional): Minimum frequency in GHz. Defaults to 1.
            n_modes (int, optional): Number of modes. Defaults to 1.
            max_delta_f (float, optional): Maximum difference in freq between consecutive passes. Defaults to 0.5.
            max_passes (int, optional): Maximum number of passes. Defaults to 10.
            min_passes (int, optional): Minimum number of passes. Defaults to 1.
            min_converged (int, optional): Minimum number of converged passes. Defaults to 1.
            pct_refinement (int, optional): Percent refinement. Defaults to 30.
            basis_order (int, optional): Basis order. Defaults to -1.
        '''
        if setup_args.name is None:
            # Give a new name to use.
            setup_args.name = "Sweep_em_setup"

        a_hfss.add_eigenmode_setup(**setup_args)
        a_hfss.activate_eigenmode_setup(setup_args.name)

    def sweep_one_option_get_eigenmode_solution_data(
            self,
            qcomp_name: str,
            option_name: str,
            option_sweep: list,
            qcomp_render: list,
            endcaps_render: list,
            setup_args: Dict = None,
            leave_last_design: bool = True,
            design_name: str = "Sweep_Capacitance") -> Tuple[dict, int]:
        """Ansys must be open with inserted project. A design, "HFSS Design" with eigenmode solution-type
        will be inserted by this method.

        Args:
            qcomp_name (str): A component that contains the option to be swept.
            option_name (str): The option within qcomp_name to sweep.
            option_sweep (list): Each entry in the list is a value for option_name.
            leave_last_design (bool) : In HFSS, after the last sweep, should the design be cleared?
            endcaps_render (list): Identify which kind of pins. 
                                    Follow details from renderer QAnsysRenderer.render_design.
            setup_args (Dict): Hold the arguments for  add_eigenmode_setup() as  key/values to pass to Ansys.  
                                If None, default Setup will be used.
            leave_last_design (bool) : In HFSS, after the last sweep, should the design be cleared?
            design_name (str, optional):  Name of HFSS_design to use in project. Defaults to "Sweep_Eigenmode".
            

        Returns:
            Tuple[dict, int]: 
            dict: The key is each value of option_sweep, the value is the solution-data for each sweep.
            int: Observation of searching for data from arguments.

            * 0 Have list of capacitance matrix.
            * 1 qcomp_name not registered in design.
            * 2 option_name is empty.
            * 3 option_name is not found as key in dict.
            * 4 option_sweep is empty, need at least one entry.
            * 5 last key in option_name is not in dict.
            * 6 project not in app
            * 7 design not in app

        """

        #Dict of all swept information.
        all_sweep = dict()
        option_path, a_value, check_result, = self.error_check_sweep_input(
            qcomp_name, option_name, option_sweep)
        if check_result != 0:
            return all_sweep, check_result

        a_hfss = self.design.renderers.hfss
        a_hfss.connect_ansys()
        a_hfss.activate_eigenmode_design(design_name)

        a_hfss.clean_active_design()

        self.handle_eignmode_setup(a_hfss, setup_args)

        len_sweep = len(option_sweep) - 1

        for index, item in enumerate(option_sweep):
            if option_path[-1] in a_value.keys():
                a_value[option_path[-1]] = item
            else:
                self.design.logger.warning(
                    f'Key="{option_path[-1]}" is not in dict.')
                return all_sweep, 5

            self.design.rebuild()

            a_hfss.render_design(
                selection=qcomp_render,
                open_pins=endcaps_render)  #Render the items chosen

            a_hfss.analyze_setup("Setup")  #Analyze said solution setup.
            setup = a_hfss.pinfo.setup
            solution_name = setup.solution_name
            all_solutions = setup.get_solutions()
            setup_names = all_solutions.list_variations()
            freqs, kappa_over_2pis = all_solutions.eigenmodes()

            sweep_values = dict()
            sweep_values['option_name'] = option_path[-1]
            sweep_values['frequency'] = freqs
            sweep_values['kappa_over_2pis'] = kappa_over_2pis
            sweep_values['quality_factor'] = freqs / kappa_over_2pis
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

    def sweep_one_option_get_capacitance_matrix(
            self,
            qcomp_name: str,
            option_name: str,
            option_sweep: list,
            qcomp_render: list,
            endcaps_render: list,
            leave_last_design: bool = True,
            design_name: str = "Sweep_Capacitance") -> Tuple[dict, int]:
        """Ansys must be open with inserted project.  A design, "Q3D Extractor Design", 
        will be inserted by this method. 

        Args:
            qcomp_name (str): A component that contains the option to be swept.
            option_name (str): The option within qcomp_name to sweep.
            option_sweep (list): Each entry in the list is a value for option_name.
            qcomp_render (list): The component to render to Q3D. 
            endcaps_render (list): Identify which kind of pins. Follow the details from renderer QAnsysRenderer.render_design.
            leave_last_design (bool) : In Q3d, after the last sweep, should the design be cleared?
            design_name(str): Name of q3d_design to use in project.

        Returns:
            dict: The key is each value of option_sweep, the value is the capacitance matrix for each sweep.
            int: Observation of searching for data from arguments.

            * 0 Have list of capacitance matrix.
            * 1 qcomp_name not registered in design.
            * 2 option_name is empty.
            * 3 option_name is not found as key in dict.
            * 4 option_sweep is empty, need at least one entry.
            * 5 last key in option_name is not in dict.
            * 6 project not in app
            * 7 design not in app
           
        """
        #Dict of all swept information.
        all_sweep = dict()
        option_path, a_value, check_result = self.error_check_sweep_input(
            qcomp_name, option_name, option_sweep)
        if check_result != 0:
            return all_sweep, check_result

        a_q3d = self.design.renderers.q3d
        a_q3d.connect_ansys()
        a_q3d.activate_q3d_design(design_name)

        a_q3d.clean_active_design()

        a_q3d.add_q3d_setup()  # Add a solution setup.

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

            a_q3d.analyze_setup("Setup")  #Analyze said solution setup.
            cap_matrix = a_q3d.get_capacitance_matrix()

            sweep_values = dict()
            sweep_values['option_name'] = option_path[-1]
            sweep_values['capacitance'] = cap_matrix
            all_sweep[item] = sweep_values

            #Decide if need to clean the design.
            obj_names = a_q3d.pinfo.get_all_object_names()
            if obj_names:
                if index == len_sweep and not leave_last_design:
                    a_q3d.clean_active_design()
                elif index != len_sweep:
                    a_q3d.clean_active_design()

        a_q3d.disconnect_ansys()
        return all_sweep, 0

    # The methods allow users to sweep a variable in a components's options.
