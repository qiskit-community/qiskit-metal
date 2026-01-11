from qiskit_metal import Dict
from typing import Tuple, Union


class Sweeper():
    """The methods allow users to sweep a variable in a components's options.
    Need access to renderers which are registered in QDesign."""

    def __init__(self, parent):
        """Connect to the QAnalysis child we sweeping can happen.

        Args:
            parent (QAnalysis): Will not be just QAnalysis, but a child or grandchild, etc. of QAnalysis.
        """

        # Reference to the instance (or child or grandchild) of QAnalysis.
        self.parent = parent

        #For easy access, make a reference to QDesign.
        if hasattr(self.parent, 'sim'):
            self.design = parent.sim.design
        elif hasattr(self.parent, 'design'):
            self.design = parent.design
        else:
            self.design = None

    def run_sweep(self, *args, **kwarg) -> Tuple[Dict, int]:
        """Ansys will be opened, if not already open, with an inserted project.  
        A design will be inserted by this method. 

        There are two ways to pass arguments.  You can use the previous run or 
        use updated arguments.  With both scenarios, qcomp_name, option_name, and 
        option_sweep must be passed.

        For the previous run, the arguments are all but the three required.  

        Args:
            qcomp_name (str): A component that contains the option to be swept.
            option_name (str): The option within qcomp_name to sweep.
            option_sweep (list): Each entry in the list is a value for
                        option_name.
            qcomp_render (list): The component to render to simulation software.
            open_terminations (list): Identify which kind of pins. Follow the
                        details from renderer QQ3DRenderer.render_design, or
                        QHFSSRenderer.render_design.
            port_list (list): List of tuples of jj's that shouldn't
                            be rendered.  Follow details from
                            renderer in QHFSSRenderer.render_design.
            jj_to_port (list): List of junctions (qcomp, qgeometry_name,
                                impedance, draw_ind) to render as lumped ports
                                or as lumped port in parallel with a sheet
                                inductance.    Follow details from renderer
                                in QHFSSRenderer.render_design.
            ignored_jjs (Union[list,None]): This is not used by all renderers,
                         just hfss.
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
            * 6 need to have at least three arguments
        """
        #Dict of all swept information.
        all_sweep = Dict()
        previous_run = Dict()
        clean_kwargs = Dict()
        use_previous_run = False

        # Decide if we use the previous run based on inputs given.
        if len(args) == 3 and len(kwarg) == 0:
            use_previous_run = True
            # Do not populate the previous_run if more than minimum required is passed.
            if hasattr(self.parent, 'sim'):
                if self.parent.sim.setup.run:
                    previous_run = self.parent.sim.setup.run
            elif self.parent.setup.run:
                previous_run = self.parent.setup.run

        if len(args) >= 3:
            option_path, a_value, check_result = self.error_check_sweep_input(
                args[0], args[1], args[2])
        else:
            return all_sweep, 6

        if check_result != 0:
            return all_sweep, check_result

        if len(args) > 3:
            clean_kwargs['components'] = args[3]
        if len(args) > 4:
            clean_kwargs['open_terminations'] = args[4]

        if 'design_name' in kwarg:
            #means use_previous_run=False
            clean_kwargs['name'] = kwarg['design_name']
            del kwarg['design_name']
        else:
            clean_kwargs['name'] = "Sweep_default"

        if use_previous_run and 'box_plus_buffer' not in previous_run:
            clean_kwargs['box_plus_buffer'] = True

        if not use_previous_run and 'box_plus_buffer' not in kwarg:
            clean_kwargs['box_plus_buffer'] = True

        all_dicts = {**previous_run, **clean_kwargs, **kwarg}

        all_sweep, check_result = self.iterate_option_sweep(
            args,
            all_dicts=all_dicts,
            option_path=option_path,
            a_value=a_value,
            all_sweep=all_sweep)

        return all_sweep, check_result

    def iterate_option_sweep(self, args: list, all_dicts: Dict,
                             option_path: list, a_value: Dict,
                             all_sweep: Dict) -> Tuple[Dict, int]:
        """Iterate through the values that user gave in option_sweep.  

        Args:
            args (Dict): Holds the three mandatory arguments in an expected sequence.
            all_dicts (Dict): User arguments manipulated to account for using previous_run. 
            option_path (list):  The list has traversed the option Dict.
            a_value (Dict): Has the value from the dictionary of the searched key.
            all_sweep (Dict): Will be populated during the iteration. 

        Returns:
            Tuple[Dict, int]: The dict key is each value of option_sweep, the
            value is the solution-data for each sweep.
            The int is the observation of searching for data from arguments as
            defined below.

                * 0 Have list of capacitance matrix.
                * 5 last key in option_name is not in Dict. 
        """

        for _, item in enumerate(args[2]):
            # Last item in list.
            if option_path[-1] in a_value.keys():
                a_value[option_path[-1]] = item
            else:
                self.design.logger.warning(
                    f'Key="{option_path[-1]}" is not in dict.')
                return all_sweep, 5

            self.design.rebuild()

            try:
                self.parent.run(**all_dicts)
            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                self.design.logger.warning(
                    f'For class {self.parent.__class__.__name__}, '
                    f'option_name={".".join(option_path)}, key={item}, '
                    f'run() did not execute as expected: {message}')

            self.populate_all_sweep(all_sweep, item, args[1])

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