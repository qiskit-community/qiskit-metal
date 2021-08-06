from qiskit_metal import Dict
from typing import Tuple, Union


class Sweeper():

    def __init__(self, parent):
        """Connect to the QAnalysis child we sweeping can happen.

        Args:
            parent (QAnalysis): Will not be just QAnalysis, but a child or grandchild, etc. of QAnalysis.
        """

        # Reference to the instance (or child or grandchild) of QAnalysis.
        self.parent = parent

        #For easy access, make a reference to QDesign.
        self.design = parent.sim.design

    def run_sweep(self,
                  qcomp_name: str,
                  option_name: str,
                  option_sweep: list,
                  qcomp_render: list,
                  open_terminations: list,
                  ignored_jjs: Union[list, None] = None,
                  design_name: str = "Sweep_default",
                  box_plus_buffer: bool = True) -> Tuple[Dict, int]:
        """Ansys will be opened, if not already open, with an inserted project.  
        A design will be inserted by this method. 

        Args:
            qcomp_name (str): A component that contains the option to be swept.
            option_name (str): The option within qcomp_name to sweep.
            option_sweep (list): Each entry in the list is a value for
                        option_name.
            qcomp_render (list): The component to render to Q3D.
            open_terminations (list): Identify which kind of pins. Follow the
                        details from renderer QQ3DRenderer.render_design, or
                        QHFSSRenderer.render_design.
            design_name(str): Name of design (workspace) to use in project.
            box_plus_buffer(bool): Render the entire chip or create a
                        box_plus_buffer around the components which are rendered.

        Returns:
            Tuple[Dict, int]: The dict key is each value of option_sweep, the
            value is the solution-data for each sweep.
            The int is the observation of searching for data from arguments as
            defined below.

            * 0 Have list of capacitance matrix.
            * 1 qcomp_name not registered in design.
            * 2 option_name is empty.
            * 3 option_name is not found as key in Dict.
            * 4 option_sweep is empty, need at least one entry.
            * 5 last key in option_name is not in Dict. 
        """
        #Dict of all swept information.
        all_sweep = Dict()

        option_path, a_value, check_result = self.error_check_sweep_input(
            qcomp_name, option_name, option_sweep)
        if check_result != 0:
            return all_sweep, check_result

        len_sweep = len(option_sweep) - 1
        for index, item in enumerate(option_sweep):
            # Last item in list.
            if option_path[-1] in a_value.keys():
                a_value[option_path[-1]] = item
            else:
                self.design.logger.warning(
                    f'Key="{option_path[-1]}" is not in dict.')
                return all_sweep, 5

            self.design.rebuild()

            try:
                self.parent.run(name=design_name,
                                components=qcomp_render,
                                open_terminations=open_terminations,
                                box_plus_buffer=box_plus_buffer,
                                ignored_jjs=ignored_jjs)
            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                self.design.logger.warning(
                    f'For class {self.parent.__class__.__name__}, run() did not execute as expected: {message}'
                )

            self.populate_all_sweep(all_sweep, item, option_name)

            zz = 5  #for breakpoint
        return all_sweep, 0

    # #######  Populate all_sweep
    def populate_all_sweep(self, all_sweep: Dict, item: str, option_name: str):
        """Populate the Dict passed in all_sweep from QAnalysis.  

        Args:
            all_sweep (Dict): Reference to hold each item which corresponds
              to option_name.
            item (str): The value of each item that we want to sweep
              in option_name.
            option_name (str): The option of QComponent that we want to sweep.
        """
        sweep_values = Dict()
        sweep_values['option_name'] = option_name
        sweep_values['variables'] = self.parent._variables

        if hasattr(self.parent, 'sim'):
            sweep_values['sim_variables'] = self.parent.sim._variables

        all_sweep[item] = sweep_values

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
            Tuple[list, Dict, int]:
            The list has traversed the option Dict.
            addict.addict.Dict has the value from the dictionary of the searched key.
            The int is the observation of searching for data from arguments.

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