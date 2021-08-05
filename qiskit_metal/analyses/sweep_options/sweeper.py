from qiskit_metal import logger, Dict
from typing import Tuple, Union


class Sweeper():

    def __init__(self, parent):
        self.parent = parent

        #For easy access, make a reference to QDesign.
        self.design = parent.sim.design
        zz = 5  #for breakpoint

    def run_sweep(self,
                  qcomp_name: str,
                  option_name: str,
                  option_sweep: list,
                  qcomp_render: list,
                  endcaps_render: list,
                  setup_args: Dict = None,
                  leave_last_design: bool = True,
                  design_name: str = "Sweep_Capacitance",
                  simulation='q3d') -> Tuple[Dict, int]:
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
            simulation(str): The renderer that is registered in Metal to get simulation information.

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
         
        """
        """
        These may not be used.
            * 5 last key in option_name is not in Dict.
            * 6 project not in app
            * 7 design not in app
            * 8 setup not implement, check the setup_args.
        """
        #Dict of all swept information.
        all_sweep = Dict()

        option_path, a_value, check_result = self.error_check_sweep_input(
            qcomp_name, option_name, option_sweep)
        if check_result != 0:
            return all_sweep, check_result

        # Deal with setup here.

        # For every entry in option_sweep, go through this loop and get
        # data to return.
        # Note: Analysis interface will prepare the workspace and if the
        #       workspace exist, the workspace will be cleared.

        zz = 5  #for breakpoint

        return all_sweep, 0

    # ####### Error checking user input.

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