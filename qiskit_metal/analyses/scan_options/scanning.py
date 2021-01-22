class Scanning():
    """
        Need access to renderers which are registered in QDesign.

    """

    def __init__(self, design: 'QDesign'):
        self.design = design

    def option_value(self, a_dict, search: str) -> str:
        value = a_dict[search]
        return value

    def scan_one_option_get_capacitance_matrix(self, qcomp_name: str,
                                               option_name: str,
                                               option_scan: list,
                                               qcomp_render: list,
                                               endcaps_render: list) -> dict:
        """Ansys must be open with inserted project "Q3D Extractor Design." 

        Args:
            qcomp_name (str): A component that contains the option to be scanned.
            option_name (str): The option within qcomp_name to scan.
            option_scan (list): Each entry in the list is a value for option_name.
            qcomp_render (list): The component to render to Q3D. 
            endcaps_render (list): Identify which kind of pins. Follow the details from renderer QQ3DRenderer.render_design.

        Returns:
            dict: The key is each value of option_scan, the value is the capacitance matrix for each scan.
        """

        option_path = option_name.split('.')
        qcomp_options = self.design.components[qcomp_name].options

        a_value = qcomp_options

        # All but the last item in list.
        for name in option_path[:-1]:
            a_value = self.option_value(a_value, name)

        #Dict of all scanned information.
        all_scan = dict()

        # Last item in list.
        for index, item in enumerate(option_scan):

            a_value[option_path[-1]] = item
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
        return all_scan

    # The methods allow users to scan a variable in a components's options.