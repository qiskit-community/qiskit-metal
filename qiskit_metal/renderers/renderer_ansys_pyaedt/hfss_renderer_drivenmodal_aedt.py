#
from qiskit_metal.renderers.renderer_ansys_pyaedt.hfss_renderer_aedt import QHFSSPyaedt
from qiskit_metal.toolbox_metal.parsing import parse_entry, parse_units
from qiskit_metal import Dict
from typing import List, Tuple, Union
from collections import OrderedDict
import pandas as pd
import pyaedt
from pyaedt import settings
from pyaedt.modules.solutions import SolutionData


class QHFSSDrivenmodalPyaedt(QHFSSPyaedt):
    """Subclass of pyaedt HFSS renderer for methods unique to driven-modal solutions within HFSS.
     QPyaedt Default Options:

    """
    name = 'aedt_hfss_drivenmodal'

    default_setup = Dict(
        name="QHFSSDrivenmodalPyaedt_setup",
        SolveType='Single',
        Frequency="5.0",  # GHz
        MaxDeltaE="0.01",
        MaximumPasses="10",
        MinimumPasses="1",
        MinimumConvergedPasses="1",
        PercentRefinement="30",
        BasisOrder="1",
        MultipleAdaptiveFreqsSetup=OrderedDict([('1GHz', [0.02]),
                                                ('2GHz', [0.02]),
                                                ('5GHz', [0.02])]),
        BroadbandLowFreq="2",  # GHz
        BroadbandHighFreq="8",  # GHz
    )
    """aedt HFSS Options"""
    aedt_hfss_drivenmodal_options = Dict()

    __supported_SolveType__ = ['Single', 'MultiFrequency', 'Broadband']
    """Supported DrivenModal Solution Types"""

    def __init__(self,
                 multilayer_design: 'MultiPlanar',
                 project_name: Union[str, None] = None,
                 design_name: Union[str, None] = None,
                 initiate=False,
                 options: Dict = None):
        """Create a QRenderer for HFSS simulations using pyaedt and multiplanar design.
        QHFSSPyaedt is subclassed from QPyaedt, subclassed from QRendererAnalysis and
        subclassed from QRenderer.  The default_setup options are expected to be defined by
        child class of QHFSSPyaedt for driven-modal and eigenmode solution types.


        Args:

            multilayer_design (MultiPlanar): Use QGeometry within MultiPlanar to obtain elements for Ansys.
            project_name (Union[str, None], optional): Give a name, or one will be made based on class name of renderer.
                                            Defaults to None.
            design_name (Union[str, None], optional): Give a name, or one will be made based on class name of renderer.
                                            Defaults to None.
            initiate (bool, optional): True to initiate the renderer. Defaults to False.
            options (Dict, optional):  Used to override all options. Defaults to None.
        """

        super().__init__(multilayer_design,
                         renderer_type='HFSS_DM',
                         project_name=project_name,
                         design_name=design_name,
                         initiate=initiate,
                         options=options)

        #make a class to read in pandas table.
        self.tables = None

    def add_hfss_dm_setup(
            self,
            name: str = None,
            SolveType: str = None,
            Frequency: float = None,  # GHz
            MaxDeltaE: float = None,
            MaximumPasses: int = None,
            MinimumPasses: int = None,
            MinimumConvergedPasses: int = None,
            PercentRefinement: int = None,
            BasisOrder: int = None,
            MultipleAdaptiveFreqsSetup: dict = None,
            BroadbandLowFreq: float = None,  # GHz
            BroadbandHighFreq: float = None  # GHz
    ):
        """Create a solution setup in Ansys HFSS Driven-Modal solution type. If user does not provide
        arguments, they will be obtained from QHFSSDrivenmodalPyaedt.default_setup dict.

        Args:
            name (str, optional): _description_. Defaults to None.
            SolveType (str, optional): Solution frequency type. Accepted values are in self.__supported_SolveType__.
                                    Defaults to self.default_setup.
            Frequency (float, optional):  Minimum frequency in GHz. Defaults to self.default_setup.
            MaxDeltaE (float, optional):  This is correlated to MaxDeltaS. The definition
                                    of MaxDeltaS is, absolute value of maximum difference in
                                    scattering parameter S. Defaults to self.default_setup.
            MaximumPasses (int, optional):  Maximum number of passes. Defaults to self.default_setup.
            MinimumPasses (int, optional): Minimum number of passes.Defaults to self.default_setup.
            MinimumConvergedPasses (int, optional): Minimum number of converged passes. Defaults to self.default_setup.
            PercentRefinement (int, optional): Percent refinement. Defaults to self.default_setup.
            BasisOrder (int, optional): Basis order. Defaults to self.default_setup.
            MultipleAdaptiveFreqsSetup (dict, optional): Frequencies and their associated MaxDeltaS.
                                    Defaults to self.default_setup.
            BroadbandLowFreq (float, optional): Minimum frequency for Broadband SolveType in GHz. 
                                    Defaults to self.default_setup.
            BroadbandHighFreq (float, optional): Maximum frequency for Broadband SolveType in GHz. 
                                    Defaults to self.default_setup.

        Returns:
            new_setup (pyaedt.modules.SolveSetup.SetupHFSS): pyAEDT simulation setup object.
        """

        self.activate_user_project_design()

        dsu = self.default_setup

        if not name:
            name = self.parse_value(dsu['name'])

        if name in self.current_app.setup_names:
            self.logger.warning(
                f'The setup name already exists within '
                f'project:{self.project_name} design: {self.design_name}. '
                f'So a new setup with name={name} was NOT added to design.')
            return

        if not Frequency:
            Frequency = float(self.parse_value(dsu['Frequency']))
        if not SolveType:
            SolveType = str(self.parse_value(dsu['SolveType']))
        if not MaxDeltaE:
            MaxDeltaE = float(self.parse_value(dsu['MaxDeltaE']))
        if not MaximumPasses:
            MaximumPasses = int(self.parse_value(dsu['MaximumPasses']))
        if not MinimumPasses:
            MinimumPasses = int(self.parse_value(dsu['MinimumPasses']))
        if not MinimumConvergedPasses:
            MinimumConvergedPasses = int(
                self.parse_value(dsu['MinimumConvergedPasses']))
        if not PercentRefinement:
            PercentRefinement = int(self.parse_value(dsu['PercentRefinement']))
        if not BasisOrder:
            BasisOrder = int(self.parse_value(dsu['BasisOrder']))
        if not MultipleAdaptiveFreqsSetup:
            MultipleAdaptiveFreqsSetup = dsu['MultipleAdaptiveFreqsSetup']
        if not BroadbandLowFreq:
            BroadbandLowFreq = float(self.parse_value(dsu['BroadbandLowFreq']))
        if not BroadbandHighFreq:
            BroadbandHighFreq = float(self.parse_value(
                dsu['BroadbandHighFreq']))

        new_setup = self.current_app.create_setup(name)

        if (SolveType == 'Single'):
            new_setup.props['SolveType'] = 'Single'
            new_setup.props['Frequency'] = f'{Frequency}GHz'
            new_setup.props['MaximumPasses'] = MaximumPasses
            new_setup.props['MaxDeltaE'] = MaxDeltaE
        elif (SolveType == 'MultiFrequency'):
            new_setup.props['SolveType'] = 'MultiFrequency'
            new_setup.props[
                'MultipleAdaptiveFreqsSetup'] = MultipleAdaptiveFreqsSetup
            new_setup.props['MaximumPasses'] = MaximumPasses
        elif (SolveType == 'Broadband'):
            new_setup.enable_adaptive_setup_broadband(
                low_frequency=f'{BroadbandLowFreq}GHz',
                high_frquency=f'{BroadbandHighFreq}GHz',
                max_passes=MaximumPasses,
                max_delta_s=MaxDeltaE)
        else:
            raise ValueError(
                f'SolveType must be one of the following:{self.__supported_SolveType__}'
            )

        new_setup.props['MinimumPasses'] = MinimumPasses
        new_setup.props['MinimumConvergedPasses'] = MinimumConvergedPasses
        new_setup.props['PercentRefinement'] = PercentRefinement
        new_setup.props['BasisOrder'] = BasisOrder

        new_setup.update()

        return new_setup

    def add_sweep(self,
                  setup_name="QHFSSDrivenmodalPyaedt_setup",
                  unit="GHz",
                  start_ghz=2.0,
                  stop_ghz=8.0,
                  count=101,
                  step_ghz=None,
                  name="QHFSSDrivenmodalPyaedt_sweep",
                  type="Fast",
                  save_fields=False,
                  interpolation_tol=0.5,
                  interpolation_max_solutions=250):
        """Add a frequency sweep to a driven modal setup.

        Args:
            setup_name (str, optional): Name of driven modal simulation setup.
                                    Defaults to "QHFSSDrivenmodalPyaedt_setup".
            unit(str, optional): The units of start and stop.
            start_ghz (float, optional): Starting frequency of sweep in GHz.
                                    Defaults to 2.0.
            stop_ghz (float, optional): Ending frequency of sweep in GHz.
                                    Defaults to 8.0.
            count (int, optional): Total number of frequencies.
                                    Defaults to 101.
            step_ghz (float, optional): Difference between adjacent
                                    frequencies. Defaults to None.
            name (str, optional): Name of sweep. Defaults to "QHFSSDrivenmodalPyaedt_sweep".
            type (str, optional): Type of sweep.  Options are "Fast", "Interpolating",
                                and "Discrete". Defaults to "Fast".
            save_fields (bool, optional): Whether or not to save fields.
                                Defaults to False.
            interpolation_tol (float, optional): Error tolerance threshold 
                                     for the interpolation type sweep. Defaults to 0.5.
            interpolation_max_solutions (int, optional): Maximum number of solutions
                                     evaluted for the interpolation process. 
                                     Defaults to 250.

        Returns:
            sweep (pyaedt.modules.SolveSweeps.SweepHFSS): pyAEDT frequency sweep object.
        """

        if setup_name in self.current_app.setup_names:

            try:
                sweep = self.current_app.create_linear_count_sweep(
                    setupname=setup_name,
                    unit=unit,
                    freqstart=start_ghz,
                    freqstop=stop_ghz,
                    num_of_freq_points=count,
                    sweepname=name,
                    save_fields=save_fields,
                    sweep_type=type,
                    interpolation_tol=interpolation_tol,
                    interpolation_max_solutions=interpolation_max_solutions)
                return sweep
            except Exception as ex:
                self.design.logger.error(f' The exception is {ex}')
        else:
            self.logger.warning(
                f'Since the setup_name={setup_name} is NOT in the project/design which was used to start HFSS DrivenModal, '
                f'a new setup_name={setup_name} will be added to design with default settings for HFSS DrivenModal.'
            )
            self.add_hfss_dm_setup(setup_name)
            try:
                sweep = self.current_app.create_linear_count_sweep(
                    setupname=setup_name,
                    unit=unit,
                    freqstart=start_ghz,
                    freqstop=stop_ghz,
                    num_of_freq_points=count,
                    sweepname=name,
                    save_fields=save_fields,
                    sweep_type=type,
                    interpolation_tol=interpolation_tol,
                    interpolation_max_solutions=interpolation_max_solutions)
                return sweep
            except Exception as ex:
                self.design.logger.error(f' The exception is {ex}')

    def analyze_setup(self, setup_name: str, sweep_name: str) -> bool:
        """Run a specific solution setup in Ansys HFSS DrivenModal.

        Args:
            setup_name (str): Name of setup.
            sweep_name (str): Name of sweep.

        Returns:
            bool: Value returned from pyaedt.analyze_setup().

        """
        # Activate project_name and design_name before anything else
        self.activate_user_project_design()

        if setup_name not in self.current_app.setup_names:
            self.logger.warning(
                f'Since the setup_name is not in the project/design which was used to start HFSS DrivenModal, '
                f'a new setup will be added to design with default settings for HFSS DrivenModal.'
            )
            self.add_hfss_dm_setup(setup_name)

        if sweep_name not in self.current_app.get_sweeps(setup_name):
            self.logger.warning(
                f'Since the sweep_name is not in the setup, '
                f'a new sweep will be added to setup with default settings for HFSS DrivenModal.'
            )
            self.add_sweep(setup_name=setup_name, name=sweep_name)

        return self.current_app.analyze_setup(setup_name)

    #def get_impedance_scattering(self, setup_name:str)-> dict:
    def get_ansys_solution_data(self,
                                sweep_name: str,
                                expressions='S',
                                output_type=1) -> dict:
        # if 0 mag/phase, 1 is real/imag, 2 both
        """Get the solution data based on expressions.  Return output based on output_type.

        Args:
            sweep_name (str): Name of sweep entry within setup.
            expressions (str, optional): This expression is either passed to get_solution_data
                                        OR either S, Y or Z with port information will be
                                        gathered by renderer. The renderer will get the
                                        port names used with render_design() to create expressions.
                                        So, the user MUST execute render_design() prior to
                                        getting solution data.

                                        Defaults to 'S'. S for scattering, Y for admittance, Z for
                                        impedance.
            output_type (int, optional): 1 to return mag/phase,
                                        2 to return real/imag,
                                        3 to return mag/phase and real/imag.
                                        Defaults to 1.

        Returns:
            dict: Key is either mag, phase, real or imag based on output_type.
                The value is data from get_solution_data.
        """

        default_expressions = ['S', 's', 'Y', 'y', 'Z', 'z']
        dm_solution_data = dict()

        valid_output_types = [1, 2, 3]
        if output_type not in valid_output_types:
            self.design.logger.warning(
                f'The argument output_type={output_type} '
                f'is not part of a valid_output_types={valid_output_types}')
            return None

        if expressions in default_expressions:
            # search using combinations of the port_list and jj_to_port
            # as expressions for get_solution_data
            expressions_dm = self.generate_expressions(expressions.upper())
        else:
            # use what the user has passed for expression for get_solution_data
            expressions_dm = expressions

        if expressions_dm is None:
            self.design.logger.warning(
                f'Do not have valid string to search on for get_solution_data.')
            return None

        # Activate project_name and design_name before anything else
        self.activate_user_project_design()
        settings.enable_pandas_output = True
        dm_data = self.current_app.post.get_solution_data(
            expressions=(expressions_dm),
            setup_sweep_name=sweep_name,
            variations={"Freq": ["All"]},
            primary_sweep_variable='Freq')
        if output_type == 1:
            self.populate_mag_phase(dm_solution_data, dm_data)
        elif output_type == 2:
            self.populate_real_imag(dm_solution_data, dm_data)
        elif output_type == 3:
            self.populate_mag_phase(dm_solution_data, dm_data)
            self.populate_real_imag(dm_solution_data, dm_data)

        return dm_solution_data

    def populate_mag_phase(self, dm_solution_data: dict,
                           dm_data: pyaedt.modules.solutions.SolutionData):
        """Update dm_solution_data with magnitude and phase of dm_data.

        Args:
            dm_solution_data (dict): This method will add key value
                                    of magnitude and phase to this dict.
            dm_data (pyaedt.modules.solutions.SolutionData): This holds
                        the result of get_solution_data.
        """
        # index 0 is magnitude, 1 is phase
        dm_solution_data['mag'] = dm_data.full_matrix_mag_phase[0]
        dm_solution_data['phase'] = dm_data.full_matrix_mag_phase[1]

    def populate_real_imag(self, dm_solution_data: dict,
                           dm_data: pyaedt.modules.solutions.SolutionData):
        """Update dm_solution_data with real and imaginary format of dm_data.

        Args:
            dm_solution_data (dict): This method will add key value
                                of real and imaginary format to this dict.
            dm_data (pyaedt.modules.solutions.SolutionData): This holds
                        the result of get_solution_data.
        """
        # index 0 is real, 1 is imaginary
        dm_solution_data['real'] = dm_data.full_matrix_real_imag[0]
        dm_solution_data['imag'] = dm_data.full_matrix_real_imag[1]

    def generate_expressions(self, expressions: str) -> Union[list, None]:
        """Use the information saved within the renderer to obtain the
        port_list and jj_to_ports.  Also, confirm that jj_to_port is not
        in ignored_jjs.  Then create all permutations and combinations
        of the names.  The names will also start with either S, or Y, or Z.

        Args:
            expressions (str): Either S, Y or Z.

        Returns:
            Union[list, None]: List of all combinations of ports prepended with "expressions".
                    None if not port names not in renderer.
        """
        port_names = []
        combo_names = []

        if self.port_list_dict and self.port_list_is_valid:
            # append all names to port_names
            for comp_name, pin_name in self.port_list_dict.keys():
                # At this method, Ensure that junction is not in the ignored_jjs
                port_name = f'Port_{comp_name}_{pin_name}'
                port_names += [port_name]

        if self.jj_to_port_dict and self.jj_to_port_is_valid:
            # append all names not in ignore_jjs to port_names
            for item in self.jj_to_port_dict.keys():
                if item not in self.ignored_jjs:
                    comp_name, pin_name = item
                    comp_id = str(self.design.components[comp_name].id)
                    jj_name_port = f'JJ_rect_R_{comp_id}_{pin_name}'
                    port_names += [jj_name_port]

        if port_names:
            port_names.sort()
            for name_1 in port_names:
                for name_2 in port_names:
                    entry = f'{expressions}({name_1},{name_2})'
                    combo_names += [entry]
        if combo_names:
            return combo_names
        else:
            return None

    def render_design(self,
                      selection: Union[list, None] = None,
                      open_pins: Union[list, None] = None,
                      port_list: Union[list, None] = None,
                      jj_to_port: Union[list, None] = None,
                      ignored_jjs: Union[list, None] = None,
                      box_plus_buffer: bool = True):
        """
        This render_design will add additional logic for just drivenmodal design within project.

        Initiate rendering of components in design contained in selection,
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

        In driven modal solutions, the Ansys design must include one or more
        ports. This is done by adding all port designations and their
        respective impedances in Ohms as (qcomp, pin, impedance) to port_list.
        Note that an open endcap must separate the two sides of each pin before
        inserting a lumped port in between, so behind the scenes all pins in
        port_list are also added to open_pins. Practically, however, port_list
        and open_pins are inputted as mutually exclusive lists.

        Also in driven modal solutions, one may want to render junctions as
        lumped ports and/or inductors, or omit them altogether. To do so,
        tuples of the form (component_name, element_name, impedance)
        are added to the list jj_to_port. For example,
        ('Q1', 'rect_jj', 70) indicates that rect_jj of component Q1 is
        to be rendered as both a lumped port with an impedance of 70 Ohms.

        Alternatively for driven modal solutions, one may want to disregard
        select junctions in the Metal design altogether to simulate the
        capacitive effect while keeping the qubit in an "off" state. Such
        junctions are specified in the form (component_name, element_name)
        in the list ignored_jjs.

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
        # self.fill_info will hold the name of newly generated box,
        # along with information from layer stack
        self.fill_info = self.design.ls.get_layer_datatype_when_fill_is_true()

        super().render_design(selection, open_pins, port_list, jj_to_port,
                              ignored_jjs, box_plus_buffer)

        if self.case == 2:
            self.logger.warning(
                'Unable to proceed with rendering. Please check selection.')
            return

        self.activate_user_project_design()

        # self.assign_thin_conductor()
        # self.assign_nets()
        self.add_mesh()

        return

    def should_render_junction(self, qgeom: pd.Series, port_list: Union[list,
                                                                        None],
                               jj_to_port: Union[list, None],
                               ignored_jjs: Union[list, None]) -> bool:
        """Logic just for driven modal.

        Args:
            qgeom (pd.Series): When rendering the rows of the junction table,
                            confirm that the component and geometry element
                            is supposed to be rendered.
            port_list (Union[list, None]): Use definition from render_design.
            jj_to_port (Union[list, None]): Use definition from render_design.
            ignored_jjs (Union[list, None]): Use definition from render_design.

        Returns:
            bool: If the element in the row of junction table should be rendered.
        """

        if ignored_jjs:
            search_junction = (self.design._components[qgeom["component"]].name,
                               qgeom['name'])
            if search_junction in ignored_jjs:
                return False

        # For driven modal, if needed, add logic for port_list and jj_to_port

        return True

    def jj_to_port_list_dict_populate(self, jj_to_port: list):
        """Convert jj_to_port to a searchable dict.

        Args:
            jj_to_port (list): List of tuples with
                        format of (component_name, element_name, impedance)
                        For example ('Q1', 'rect_jj', 70)

        """
        # This should be overwritten by drivenmodal class.

        self.jj_to_port_dict = Dict()

        for comp_name, element_name, impedance in jj_to_port:
            search_junction = (comp_name, element_name)

            self.jj_to_port_dict[search_junction] = impedance

    def port_list_dict_populate(self, port_list: list):
        """Convert the port_list to a searchable dict.

        Args:
            port_list (list): Use definition from render_design.
        """
        self.port_list_dict = Dict()
        for qcomp, pin, impedance in port_list:
            search_junction = (qcomp, pin)
            self.port_list_dict[search_junction] = impedance

    def add_ports(self, port_list: list, port_list_dict: dict, layer_num: int):
        """_summary_
        Reuse the code for add_endcaps to remove small portion of dielectric.

        Args:
            port_list (list): Use definition from render_design.
            port_list_dict (dict): Reformat the port_list to search for impedance.
            layer_num (int): The layer number used in geometry table which
                        corresponds to a z coordinate in layer stack.
        """

        port_pins = port_list_dict.keys()
        self.add_endcaps(port_pins,
                         layer_num=layer_num,
                         endcap_str='port_endcap')
        self.create_ports(port_list, layer_num)

    def create_ports(self, port_list: list, layer_num: int):
        """_summary_

        Args:
            port_list (list): Use definition from render_design.
            layer_num (int): The layer number used in geometry table which
                        corresponds to a z coordinate in layer stack.
        """
        for comp_name, pin_name, impedance in port_list:
            port_name = f'Port_{comp_name}_{pin_name}'
            #self.design.logger.debug(f'Drawing a rectangle: {port_name}')

            pin_dict = self.design.components[comp_name].pins[pin_name]
            width, gap = parse_entry([pin_dict["width"], pin_dict["gap"]])
            mid, normal = parse_entry(pin_dict["middle"]), pin_dict["normal"]
            chip_name = self.design.components[comp_name].options.chip
            result = self.design.ls.get_properties_for_layer_datatype(
                ['thickness', 'z_coord', 'material', 'fill'], layer_num)
            if result:
                thickness, z_coord, material, fill = result
            else:
                self.design.ls.layer_stack_handler_pilot_error()

            start_vec_xyz = mid.tolist()
            start_vec_xyz.append(z_coord + (thickness / 2))

            end_vec_xyz = (mid + gap * normal).tolist()
            end_vec_xyz.append(z_coord + (thickness / 2))
            endpoints_3d = [start_vec_xyz, end_vec_xyz]

            poly_port = self.current_app.modeler.create_polyline(
                [endpoints_3d[0], endpoints_3d[1]],
                name=port_name,
                cover_surface=False,
                close_surface=False,
                xsection_type='Line',
                xsection_width=width)
            poly_port.show_arrow = True
            poly_port.color = (128, 0, 128)

            lumped_port = self.current_app.create_lumped_port_to_sheet(
                sheet_name=poly_port.name,
                # Name is under excitation folder, so can reuse.
                portname=poly_port.name,
                axisdir=endpoints_3d,
                impedance=impedance)

            a = 5

    def add_mesh(self):
        a = 5
