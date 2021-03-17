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

from typing import List, Tuple, Union, Any, Iterable


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
            str: Value from the dictionary of the searched term
        """
        value = a_dict[search]
        return value

    '''all_sweeps, return_code = sweep.sweep_one_option_get_eigenmode_solution_data(
    q2.name,
    'connection_pads.c.pad_width', 
    ['100um', '110um', '120um'],
    design_name="GetCapacitance")'''

    def sweep_one_option_get_eigenmode_solution_data(
            self,
            qcomp_name: str,
            option_name: str,
            option_sweep: list,
            qcomp_render: list,
            endcaps_render: list,
            leave_last_design: bool = True,
            design_name: str = "Sweep_Capacitance") -> Tuple[dict, int]:
        """Ansys must be open with inserted project. A design, "HFSS Design" with eigenmode solution-type
        will be inserted by this method.

        Args:
            qcomp_name (str): A component that contains the option to be swept.
            option_name (str): The option within qcomp_name to sweep.
            option_sweep (list): Each entry in the list is a value for option_name.
            leave_last_design (bool) : In HFSS, after the last sweep, should the design be cleared?
            endcaps_render (list): Identify which kind of pins. Follow the details from renderer QAnsysRenderer.render_design.
            leave_last_design (bool) : In HFSS, after the last sweep, should the design be cleared?
            design_name (str, optional):  Name of hfss_design to use in project. Defaults to "Sweep_Eigenmode".
            

        Returns:
            Tuple[dict, int]: 
            dict: The key is each value of option_sweep, the value is the solution-data for each sweep.
            int: Observation of searching for data from arguments.

            * 0 Have list of capacitance matrix.
            * 1 qcomp_name not registered in design.
            * 2 option_name is empty.
            * 3 option_name is not found as key in dict.
            * 4 last key in option_name is not in dict.
            * 5 option_sweep is empty, need at least one entry.
            * 6 project not in app
            * 7 design not in app

        """

        #Dict of all swept information.
        all_sweep = dict()

        if len(option_sweep) == 0:
            return all_sweep, 5

        if option_name:
            option_path = option_name.split('.')
        else:
            return all_sweep, 2

        if qcomp_name in self.design.components.keys():
            qcomp_options = self.design.components[qcomp_name].options
        else:
            return all_sweep, 1

        a_value = qcomp_options

        # All but the last item in list.
        for name in option_path[:-1]:
            if name in a_value:
                a_value = self.option_value(a_value, name)
            else:
                self.design.logger.warning(f'Key="{name}" is not in dict.')
                return all_sweep, 3

        a_hfss = self.design.renderers.hfss
        a_hfss.connect_ansys()
        a_hfss.activate_eigenmode_design(design_name)

        obj_names = a_hfss.pinfo.get_all_object_names()
        if obj_names:
            a_hfss.clean_active_design()

        a_hfss.activate_eigenmode_setup()  # Add a default solution setup.

        len_sweep = len(option_sweep) - 1

        for index, item in enumerate(option_sweep):
            if option_path[-1] in a_value.keys():
                a_value[option_path[-1]] = item
            else:
                self.design.logger.warning(
                    f'Key="{option_path[-1]}" is not in dict.')
                return all_sweep, 4

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
            * 4 last key in option_name is not in dict.
            * 5 option_sweep is empty, need at least one entry.
            * 6 project not in app
            * 7 design not in app
           
        """
        #Dict of all swept information.
        all_sweep = dict()

        if len(option_sweep) == 0:
            return all_sweep, 5

        if option_name:
            option_path = option_name.split('.')
        else:
            return all_sweep, 2

        if qcomp_name in self.design.components.keys():
            qcomp_options = self.design.components[qcomp_name].options
        else:
            return all_sweep, 1

        a_value = qcomp_options

        # All but the last item in list.
        for name in option_path[:-1]:
            if name in a_value:
                a_value = self.option_value(a_value, name)
            else:
                self.design.logger.warning(f'Key="{name}" is not in dict.')
                return all_sweep, 3

        a_q3d = self.design.renderers.q3d
        a_q3d.connect_ansys()
        a_q3d.activate_q3d_design(design_name)

        obj_names = a_q3d.pinfo.get_all_object_names()
        if obj_names:
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
                return all_sweep, 4

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
