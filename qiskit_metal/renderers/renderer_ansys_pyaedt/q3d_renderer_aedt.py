#-*- coding: utf-8 -*-

from typing import Union, Tuple

from qiskit_metal.renderers.renderer_ansys_pyaedt.pyaedt_base import QPyaedt
from qiskit_metal.toolbox_metal.parsing import is_true

from qiskit_metal import Dict
from ansys.aedt.core import settings
import pandas as pd
import numpy as np
import shapely


class QQ3DPyaedt(QPyaedt):
    """
    Subclass of pyaedt renderer for running Q3D simulations.

    QPyaedt Default Options:

    """
    name = 'aedt_q3d'

    default_setup = Dict(
        name="QQ3DPyaedt_setup",
        AdaptiveFreq="5.0",  # in GHz
        SaveFields="False",
        Enabled="True",
        MaxPass="15",
        MinPass="2",
        MinConvPass="2",
        PerError="0.5",
        PerRefine="30",
        AutoIncreaseSolutionOrder="True",
        SolutionOrder="High",
        Solver_Type="Iterative",
    )
    """Default setup."""

    aedt_q3d_options = Dict(material_type='pec', material_thickness='200nm')
    """aedt Q3D Options"""

    def __init__(self,
                 multilayer_design: 'MultiPlanar',
                 project_name: Union[str, None] = None,
                 design_name: Union[str, None] = None,
                 initiate=False,
                 options: Dict = None):
        """Create a QRenderer for Q3D simulations using pyaedt and multiplanar design.
        QQ3DPyaedt is subclassed from QPyaedt, subclassed from QRendererAnalysis and
        subclassed from QRenderer.

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

        Args:
            multilayer_design (MultiPlanar): Use QGeometry within MultiPlanar to obtain elements for Ansys.
            project_name (Union[str, None], optional): Give a name, or one will be made based on
                                            class name of renderer.  Defaults to None.
            design_name (Union[str, None], optional): Give a name, or one will be made based on
                                            class name of renderer. Defaults to None.
            initiate (bool, optional): True to initiate the renderer. Defaults to False.
            options (Dict, optional):  Used to override all options. Defaults to None.
        """
        super().__init__(multilayer_design,
                         renderer_type='Q3D',
                         project_name=project_name,
                         design_name=design_name,
                         initiate=initiate,
                         options=options)

        # QRenderer has a "cls" method called load()
        if_registered_in_design = QQ3DPyaedt.load()

        #make a class to read in pandas table.
        self.tables = None

        # Note: desktop is instantiated in the parent's init.

    #
    # Updating an existing setup would be nice, but for now,
    # pyaedt is not easy to use, right now.
    #  edit_setup appear to delete previous setup values.
    #  get_setup could get the values of a setup, then one could
    # potentially edit that and save it.
    # So will get back to this later.
    # https://aedtdocs.pyansys.com/API/_autosummary/pyaedt.modules.SolveSetup.Setup.update.html?highlight=update+setup
    # The above link used to exist, but has since been unattainable.
    #
    # def update_q3d_setup(self, q3d_setup_name: str):
    #     # Activate project_name and design_name before anything else
    #     self.activate_user_project_design()

    #     # # get the setup names
    #     # all_setup_names = list(self.current_app.setup_names)
    #     # if q3d_setup_name in all_setup_names:
    #     #     self.current_app
    #     # check if name is in design
    #     #        then enable
    #     #otherwise
    #     #        be created by the values in default_setup
    #     #        self.add_q3d_setup()

    def add_q3d_setup(self,
                      name: str = None,
                      AdaptiveFreq: float = None,
                      SaveFields: bool = None,
                      Enabled: bool = None,
                      MaxPass: int = None,
                      MinPass: int = None,
                      MinConvPass: int = None,
                      PerError: float = None,
                      PerRefine: int = None,
                      AutoIncreaseSolutionOrder: bool = None,
                      SolutionOrder: str = None,
                      Solver_Type: str = None):
        """Create a solution setup in Ansys Q3D. If user does not provide
        arguments, they will be obtained from QQ3DPyaedt.default_setup dict.

        Args:
            name (str, optional): Name of solution setup. Defaults to None.
            AdaptiveFreq (float, optional): Adaptive frequency in GHz. Defaults to None.
            SaveFields (bool, optional): Whether or not to save fields. Defaults to None.
            Enabled (bool, optional): Whether or not setup is enabled. Defaults to None.
            MaxPass (int, optional): Maximum number of passes. Defaults to None.
            MinPass (int, optional): Minimum number of passes. Defaults to None.
            MinConvPass (int, optional): Minimum number of converged passes. Defaults to None.
            PerError (float, optional): Error tolerance as a percentage. Defaults to None.
            PerRefine (int, optional): Refinement as a percentage. Defaults to None.
            AutoIncreaseSolutionOrder (bool, optional): Whether or not to increase solution order automatically. Defaults to None.
            SolutionOrder (str, optional): Solution order. Defaults to None.
            Solver_Type (str, optional): Solver type. Defaults to None.
        """
        self.activate_user_project_design()

        su = self.default_setup

        if not name:
            name = self.parse_value(su['name'])

        if name in self.current_app.setup_names:
            self.logger.warning(
                f'The setup name already exists within '
                f'project:{self.project_name} design: {self.design_name}. '
                f'So a new setup with name={name} was NOT added to design.')
            return

        if not AdaptiveFreq:
            AdaptiveFreq = float(self.parse_value(su['AdaptiveFreq']))
        if not SaveFields:
            SaveFields = is_true(su['SaveFields'])
        if not Enabled:
            Enabled = is_true(su['Enabled'])
        if not MaxPass:
            MaxPass = int(self.parse_value(su['MaxPass']))
        if not MinPass:
            MinPass = int(self.parse_value(su['MinPass']))
        if not MinConvPass:
            MinConvPass = int(self.parse_value(su['MinConvPass']))
        if not PerError:
            PerError = float(self.parse_value(su['PerError']))
        if not PerRefine:
            PerRefine = int(self.parse_value(su['PerRefine']))
        if not AutoIncreaseSolutionOrder:
            AutoIncreaseSolutionOrder = is_true(su['AutoIncreaseSolutionOrder'])
        if not SolutionOrder:
            SolutionOrder = self.parse_value(su['SolutionOrder'])
        if not Solver_Type:
            Solver_Type = self.parse_value(su['Solver_Type'])

        new_setup = self.current_app.create_setup(name)

        # yapf: disable
        new_setup.props['AdaptiveFreq'] = f'{AdaptiveFreq}GHz'
        new_setup.props['SaveFields'] = SaveFields
        new_setup.props['Enabled'] = Enabled
        new_setup.props['Cap']['MaxPass'] = MaxPass
        new_setup.props['Cap']['MinPass'] = MinPass
        new_setup.props['Cap']['MinConvPass'] = MinConvPass
        new_setup.props['Cap']['PerError'] = PerError
        new_setup.props['Cap']['PerRefine'] = PerRefine
        new_setup.props['Cap']['AutoIncreaseSolutionOrder'] = AutoIncreaseSolutionOrder
        new_setup.props['Cap']['SolutionOrder'] = SolutionOrder
        new_setup.props['Cap']['Solver Type'] = Solver_Type
        # yapf: enable
        new_setup.props.pop('AC', None)
        new_setup.props.pop('DC', None)
        new_setup.update()

    # pylint: disable=arguments-differ
    def render_design(self,
                      selection: Union[list, None] = None,
                      open_pins: Union[list, None] = None,
                      box_plus_buffer: bool = True):
        """
        This render_design will add additional logic for Q3D within project.

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

        # Draw in fill = True pieces. based on either full chip or box_plus

        # They are reset for each time render_design happens.
        super().render_design(selection, box_plus_buffer)

        if self.case == 2:
            self.logger.warning(
                'Unable to proceed with rendering. Please check selection.')
            return

        self.open_pins_is_valid = self.confirm_open_pins_are_valid_names(
            open_pins, [])
        if not self.open_pins_is_valid:
            self.logger.error(
                'Check the arguments to render_design, invalid name was probably used.'
            )
        else:
            self.activate_user_project_design()

            # Ansys default units is 'mm'?????, but metal using 'meter'.
            # pyaedt.generic.constants.SI_UNITS.Length is meter.
            if open_pins and self.open_pins_is_valid:
                self.aedt_render_by_layer_then_tables(open_pins=open_pins)
            else:
                self.aedt_render_by_layer_then_tables(open_pins=None)

            # self.add_mesh()
            # self.assign_thin_conductor()
            # self.assign_nets()

        return

    def aedt_render_by_layer_then_tables(self,
                                         open_pins: Union[list, None],
                                         data_type: int = 0):
        """_summary_

        Args:

            open_pins (Union[list, None], optional): _description_. Defaults to None.
            datatype (int, optional): _description_. Defaults to 0.
        """
        # For Q3d skip_junction is always True.
        super().aedt_render_by_layer_then_tables(skip_junction=True,
                                                 open_pins=open_pins,
                                                 port_list=None,
                                                 jj_to_port=None,
                                                 ignored_jjs=None,
                                                 data_type=data_type)

        for layer_num in sorted(
                self.design.qgeometry.get_all_unique_layers_for_all_tables(
                    self.qcomp_ids)):
            for table_type in self.design.qgeometry.get_element_types():
                if table_type != 'junction':
                    #At this point, we know table type,
                    self.render_components(table_type,
                                           layer_num,
                                           port_list=None,
                                           jj_to_port=None,
                                           ignored_jjs=None)

            #For each layer, add the endcaps and
            # add polyline to subtract to self.chip_subtract_dict[layer_num].

            if isinstance(open_pins, list):
                # Only use this method if user defines open pins.
                if open_pins:
                    #Confirm there is something in the list.
                    open_pins_subset = self.get_open_pins_in_layer(
                        open_pins, layer_num)
                    self.add_endcaps(open_pins_subset, layer_num)

            # The layer is obtained from qgeometry tables, but layer_stack
            # can have multiple data_types.  For now, the subtract will
            # happen from data_type==0.
            self.subtract_from_ground(layer_num, data_type=data_type)
        #self.current_app.modeler.sheet_names

        a = 5

    # commenting this out for now.
    # def get_data(self):
    #     self.current_app.post.get_solution_data()

    #     all_cell_names = self.current_app.matrices[0].get_sources_for_plot(

    #     a=5

    def analyze_setup(self, setup_name: str):
        """Run a specific solution setup in Ansys Q3D.

        Args:
            setup_name (str): Name of setup.
        """
        # Activate project_name and design_name before anything else
        self.activate_user_project_design()

        if setup_name in self.current_app.setup_names:
            if self.current_app.auto_identify_nets():
                self.current_app.analyze_setup(setup_name)
            else:
                self.logger.warning(
                    'Auto Identify Nets returned False. '
                    'Please review your design to see what is failing. '
                    'Within Ansys, press simulation in the tab, then validate (green check mark).'
                )
        else:
            self.logger.warning(
                'Since the setup_name is not in the project/design which was used to start Q3d, '
                'a new setup will be added with default settings for Q3D.')
            self.add_q3d_setup(setup_name)
            if self.current_app.auto_identify_nets():
                self.current_app.analyze_setup(setup_name)
            else:
                self.logger.warning(
                    'Auto Identify Nets returned False. '
                    'Please review your design to see what is failing. '
                    'Within Ansys, press simulation in the tab, then validate (green check mark).'
                )

    # Below commands are from a notebook which shows abstraction usage.
    # c2.sim.capacitance_matrix, c2.sim.units = q3d.get_capacitance_matrix()
    # c2.sim.capacitance_all_passes, _ = q3d.get_capacitance_all_passes()
    # c2.sim.capacitance_matrix

    def get_capacitance_matrix(self):
        a = 5

    def get_capacitance_all_passes(self, setup_name: str) -> Union[dict, None]:
        """ASSUME analyze_setup() has already happened.
        Get the magnitude of solution data in pandas data
        format for each pass.

        Args:
            setup_name (str): Name of setup which has already been
                            used for analyze_setup().

        Returns:
            Union[dict, None]: Key - freq in GHz  Value is a list.  The 0 th index is key, the
            1st entry is the 1st pass is a pandas dataframe of capacitance matrix. (magnitude)
            2nd entry is the 2nd pass is a pandas dataframe of capacitance matrix. (magnitude)
            etc....

            If analyze_setup has not been run, return None.

        """
        all_C_matrices = self.current_app.matrices[0].get_sources_for_plot()

        if len(all_C_matrices) == 0:
            self.design.logger.warning(
                'There are no capacitance matrixes to return.'
                'Did you execute analyze_setup()?')
            return None

        # Pandas output should have been set prior to opening Ansys,
        # however, just confirming if changed by user through GUI.
        settings.enable_pandas_output = True

        setup_sweep_name = f'{setup_name}: AdaptivePass'
        cap_data = self.current_app.post.get_solution_data(
            expressions=all_C_matrices,
            context="Original",
            setup_sweep_name=setup_sweep_name,
            variations={"Pass": ["All"]})

        c1_units = cap_data.units_data

        all_cap_data_magnitude = []
        all_cap_data_magnitude_freqs = {}

        confirm_freq = cap_data.active_intrinsic['Freq']  # Is 5.0
        # If a list is not returned, make one so can iterate through it.
        if isinstance(confirm_freq, float):
            confirm_freq = [confirm_freq]

        for freq in confirm_freq:
            all_cap_data_magnitude.append(freq)
            for item in cap_data.intrinsics['Pass']:
                #cap_real_imag = cap_data.full_matrix_real_imag
                cap_mag = cap_data.full_matrix_mag_phase[0].iloc[int(item) - 1]
                cap_mag_df = self.convert_to_dataframe(cap_mag)
                all_cap_data_magnitude.append(cap_mag_df)
            all_cap_data_magnitude_freqs[freq] = all_cap_data_magnitude
        return all_cap_data_magnitude_freqs

    def convert_to_dataframe(
        self, cap_series: pd.core.series.Series
    ) -> Union[pd.core.frame.DataFrame, None]:
        """Convert the series to a dataframe based on the column names.
        If the names are missing, then the dataframe will be None.

        Args:
            cap_series (pd.core.series.Series): Series given by pyaedt.

        Returns:
            Union[pd.core.frame.DataFrame, None]: A dataframe if there are names in columns.
                                            Otherwise, None.
        """

        df = None
        row_names, col_names = self.get_unique_row_and_col_names(cap_series)
        len_row_names = len(row_names)
        len_col_names = len(col_names)

        if len_row_names == 0 or len_col_names == 0:
            self.design.logger.warning(
                f'The dataframe for solution data was not made.'
                f'The names of rows={row_names} or columns={col_names} are empty.'
                f'The dataframe was not made and is None.')
        else:
            df = pd.DataFrame(np.empty((len_row_names, len_col_names),
                                       dtype=object),
                              index=pd.Index(row_names),
                              columns=pd.Index(col_names))

        #for series_name in cap_series.index:
        for series_name, value in cap_series.items():
            # ASSUME format from pyaedt, C(row_name , col_name)
            row_name, col_name = series_name[2:-1].split(',', 1)
            df.loc[row_name, [col_name]] = value

        return df

    def get_unique_row_and_col_names(
            self, cap_series: pd.core.series.Series) -> Tuple[list, list]:
        """Parse the names in the series and identify the unique names
        for rows and columns

        Args:
            cap_series (pd.core.series.Series): Data from pyaedt with assumed format for names:
                C(row_name , col_name)

        Returns:
            Tuple[list, list]: 1st is names of rows and second set is names of columns.
                            Should be in alphabetical order.
        """
        row_names = set()
        col_names = set()
        for series_name in cap_series.index:
            # ASSUME format from pyaedt, C(row_name , col_name)
            row_name, col_name = series_name[2:-1].split(',', 1)
            row_names.add(row_name)
            col_names.add(col_name)

        return sorted(row_names), sorted(col_names)

    def render_element(self,
                       qgeom: pd.Series,
                       is_junction: bool,
                       port_list: None = None,
                       jj_to_port: None = None,
                       ignored_jjs: None = None):
        """Render an individual shape whose properties are listed in a row of
        QGeometry table. Junction elements are handled separately from non-
        junction elements. For Q3D, junctions are not rendered.

        For Q3D, port_list, jj_to_port, and ignored_jjs are not used.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
            is_junction (bool): Whether or not qgeom belongs to junction table.
        """
        qc_shapely = qgeom.geometry

        if not is_junction:
            #Q3D doesn't render junction.
            if isinstance(qc_shapely, shapely.geometry.Polygon):
                self.render_element_poly(qgeom)
            elif isinstance(qc_shapely, shapely.geometry.LineString):
                self.render_element_path(qgeom)
