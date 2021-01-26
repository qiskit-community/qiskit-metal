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

from typing import List, Tuple, Union, Any, Iterable


class Scanning():
    """
        Need access to renderers which are registered in QDesign.

    """

    def __init__(self, design: 'QDesign'):
        """Give QDesign to this class so Scanning can access the registered QRenderers.

        Args:
            design (QDesign): Used to access the QRenderers. 
        """
        self.design = design

    def option_value(self, a_dict, search: str) -> str:
        """Get value from dict based on key.  This method is used for unknown depth, dict search, within a dict."""
        value = a_dict[search]
        return value

    def scan_one_option_get_capacitance_matrix(
            self, qcomp_name: str, option_name: str, option_scan: list,
            qcomp_render: list, endcaps_render: list) -> Tuple[dict, int]:
        """Ansys must be open with inserted project "Q3D Extractor Design." 

        Args:
            qcomp_name (str): A component that contains the option to be scanned.
            option_name (str): The option within qcomp_name to scan.
            option_scan (list): Each entry in the list is a value for option_name.
            qcomp_render (list): The component to render to Q3D. 
            endcaps_render (list): Identify which kind of pins. Follow the details from renderer QQ3DRenderer.render_design.

        Returns:
            dict: The key is each value of option_scan, the value is the capacitance matrix for each scan.
            int: Observation of searching for data from agrguments.

            * 0 Have list of capacitance matrix.
            * 1 qcomp_name not registered in design.
            * 2 option_name is empty.
            * 3 option_name is not found as key in dict.
            * 4 last key in option_name is not in dict.
            * 5 option_scan is empty, need at least one entry.

           
        """
        #Dict of all scanned information.
        all_scan = dict()

        if len(option_scan) == 0:
            return all_scan, 5

        if option_name:
            option_path = option_name.split('.')
        else:
            return all_scan, 2

        if qcomp_name in self.design.components.keys():
            qcomp_options = self.design.components[qcomp_name].options
        else:
            return all_scan, 1

        a_value = qcomp_options

        # All but the last item in list.
        for name in option_path[:-1]:
            if name in a_value:
                a_value = self.option_value(a_value, name)
            else:
                self.design.logger.warning(f'Key="{name}" is not in dict.')
                return all_scan, 3

        # Last item in list.
        for index, item in enumerate(option_scan):
            if option_path[-1] in a_value.keys():
                a_value[option_path[-1]] = item
            else:
                self.design.logger.warning(
                    f'Key="{option_path[-1]}" is not in dict.')
                return all_scan, 4

            self.design.rebuild()

            a_q3d = self.design.renderers.q3d
            if index == 0:
                #Only need to open just one time.
                a_q3d.open_ansys_design()

            a_q3d.render_design(
                selection=qcomp_render,
                open_pins=endcaps_render)  #Render the items chosen

            a_q3d.add_q3d_setup()  # Add a solution setup.
            a_q3d.analyze_setup("Setup")  #Analyze said solution setup.
            cap_matrix = a_q3d.get_capacitance_matrix()

            scan_values = dict()
            scan_values['option_name'] = option_path[-1]
            scan_values['capacitance'] = cap_matrix
            all_scan[item] = scan_values
            a_q3d.clean_project()
        return all_scan, 0

    # The methods allow users to scan a variable in a components's options.