#
"""
Variables

from pyaedt.HFSS import HFSS
with HFSS as hfss:
     hfss["dim"] = "1mm"   # design variable
     hfss["$dim"] = "1mm"  # project variable

Modeler

# Create a box, assign variables, and assign materials.

from pyaedt.hfss import Hfss
with Hfss as hfss:
     hfss.modeler.create_box([0, 0, 0], [10, "dim", 10],
                             "mybox", "aluminum")


"""

from qiskit_metal.renderers.renderer_ansys_pyaedt.pyaedt_base import QPyaedt
from qiskit_metal.renderers.renderer_ansys.ansys_renderer import QAnsysRenderer
from qiskit_metal.draw.utility import to_vec3D, to_vec3D_list
from qiskit_metal.toolbox_metal.parsing import parse_entry, parse_units

from qiskit_metal import Dict
from typing import List, Tuple, Union
import pandas as pd
import shapely

from qiskit_metal import config
if not config.is_building_docs():
    from qiskit_metal.toolbox_python.utility_functions import get_clean_name


class QHFSSPyaedt(QPyaedt):
    """Subclass of pyaedt renderer for running HFSS simulations.

     QPyaedt Default Options:

    """

    default_setup = Dict(
        drivenmodal=Dict(
            name="Setup",
            freq_ghz="5.0",
            max_delta_s="0.1",
            max_passes="10",
            min_passes="1",
            min_converged="1",
            pct_refinement="30",
            basis_order="1",
        ),
        eigenmode=Dict(
            name="Setup",
            min_freq_ghz="1",
            n_modes="1",
            max_delta_f="0.5",
            max_passes="10",
            min_passes="1",
            min_converged="1",
            pct_refinement="30",
            basis_order="-1",
        ),
    ),
    name = 'aedt_hfss'

    aedt_hfss_options = Dict(
        # spacing between port and inductor if junction is drawn both ways
        port_inductor_gap='10um')
    """aedt HFSS Options"""

    def __init__(self,
                 multilayer_design: 'MultiPlanar',
                 renderer_type: str = 'HFSS',
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
            renderer_type (str): Choose string from list ['HFSS_DM', 'HFSS_EM', 'Q3D'] for the type of
                                design to insert into project.
            project_name (Union[str, None], optional): Give a name, or one will be made based on class name of renderer.
                                            Defaults to None.
            design_name (Union[str, None], optional): Give a name, or one will be made based on class name of renderer.
                                            Defaults to None.
            initiate (bool, optional): True to initiate the renderer. Defaults to False.
            options (Dict, optional):  Used to override all options. Defaults to None.
        """

        super().__init__(multilayer_design,
                         renderer_type=renderer_type,
                         project_name=project_name,
                         design_name=design_name,
                         initiate=initiate,
                         options=options)

        self.current_sweep = None

        # Check if user entered valid data
        self.port_list_is_valid = None  # bool
        self.jj_to_port_is_valid = None  #bool
        self.ignored_jjs_is_valid = None  #bool

        # Reformat the port_list and enter into port_list_dict
        self.port_list_dict = Dict()

        # Reformat the jj_to_port and enter int jj_to_port_dict
        self.jj_to_port_dict = Dict()

        # Keep copy of ignored_jjs to use after rendering.
        self.ignored_jjs = []

        # QRenderer has a "cls" method called load()
        if_registered_in_design = QHFSSPyaedt.load()

        #make a class to read in pandas table.
        self.tables = None

    def render_design(self,
                      selection: Union[list, None] = None,
                      open_pins: Union[list, None] = None,
                      port_list: Union[list, None] = None,
                      jj_to_port: Union[list, None] = None,
                      ignored_jjs: Union[list, None] = None,
                      box_plus_buffer: bool = True):
        """
        This render_design will add additional logic for HFSS within project.
        In particular, when used by BOTH solution types of eigenmode and drivenmodal.

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
            port_list (Union[list, None], optional): List of tuples of pins to
                                        be rendered as ports. Defaults to None.
            jj_to_port (Union[list, None], optional): List of tuples of jj's to
                                        be rendered as ports. Defaults to None.
            ignored_jjs (Union[list, None], optional): List of tuples of jj's
                                        that shouldn't be rendered.
                                        Defaults to None.
            box_plus_buffer (bool, optional): Either calculate a bounding box based on the
                                            location of rendered geometries or use chip size
                                            from design class.
        """
        # Draw in fill = True pieces. based on either full chip or box_plus

        # They are reset for each time render_design happens.
        super().render_design(selection, box_plus_buffer)

        if self.case == 2:
            self.logger.warning(
                'Unable to proceed with rendering. Please check selection.')
            return

        self.reset_hfss_arguments()
        self.ignored_jjs = ignored_jjs

        #Every time one chooses to render, we have to get the chip names since the
        #qgeometry tables can be updated between each render_design().
        chip_list = self.get_chip_names()

        if not self.valid_input_arguments(open_pins, port_list, jj_to_port,
                                          ignored_jjs):
            self.logger.error(
                f'Check the arguments to render_design, invalid name was probably used.'
            )
        else:
            # Ansys default units is 'mm'?????, but metal using 'meter'.
            # pyaedt.generic.constants.SI_UNITS.Length is meter.
            self.activate_user_project_design()

            # Add something to clear design.

            self.draw_sample_holder()

            self.aedt_render_by_layer_then_tables(skip_junction=False,
                                                  open_pins=open_pins,
                                                  port_list=port_list,
                                                  jj_to_port=jj_to_port,
                                                  ignored_jjs=ignored_jjs)

        # self.assign_thin_conductor()
        # self.assign_nets()

    def aedt_render_by_layer_then_tables(self,
                                         open_pins: Union[list, None],
                                         port_list: Union[list, None],
                                         jj_to_port: Union[list, None],
                                         ignored_jjs: Union[list, None],
                                         skip_junction: bool = False,
                                         data_type: int = 0):
        """_summary_

        Args:
            skip_junction (bool, optional): Should the renderer add junctions to HFSS.
                                            Defaults to False.
            open_pins (Union[list, None], optional): Which pins will have small rectangle of substrate
                                subtracted to be an endcap. Use definition from render_design.
                                Defaults to None.
            port_list (Union[list, None], optional): Use definition from render_design.
                                                    Defaults to None.
            jj_to_port (Union[list, None], optional): Use definition from render_design.
                                                    Defaults to None.
            ignored_jjs (Union[list, None], optional): Use definition from render_design.
                                                    Defaults to None.
            datatype (int, optional): This comes for the layer_stack file; regarding
                                                    layer and datatype. Defaults to 0.
        """

        super().aedt_render_by_layer_then_tables(skip_junction=skip_junction,
                                                 open_pins=open_pins,
                                                 port_list=port_list,
                                                 jj_to_port=jj_to_port,
                                                 ignored_jjs=ignored_jjs,
                                                 data_type=data_type)

        for layer_num in sorted(
                self.design.qgeometry.get_all_unique_layers_for_all_tables(
                    self.qcomp_ids)):

            # Create subsets per layer for  port_list, jj_to)port, and open_pins.

            result_subset = self.get_subset_based_on_layer(
                open_pins, port_list, jj_to_port, ignored_jjs, layer_num)
            open_pins_subset, port_list_subset, jj_to_port_subset, ignored_jjs_subset = result_subset

            for table_type in self.design.qgeometry.get_element_types():
                if table_type != 'junction' or not skip_junction:
                    #At this point, we know table type,
                    self.render_components(table_type, layer_num,
                                           port_list_subset, jj_to_port_subset,
                                           ignored_jjs_subset)

            #For each layer, add the endcaps and
            # add polyline to subtract to self.chip_subtract_dict[layer_num].

            if isinstance(open_pins_subset, list) and self.open_pins_is_valid:
                # Only use this method if user defines open pins.
                if open_pins_subset:
                    #Confirm there is something in the list.
                    self.add_endcaps(open_pins_subset, layer_num)

            solution_type = self.current_app.solution_type

            if solution_type == 'Modal' and self.port_list_is_valid and isinstance(
                    port_list_subset, list):

                # Only use this method if user defines drivenmodal solution_type,
                # and  port list is provided by user.
                if port_list_subset:
                    #Confirm there is something in the list.
                    self.port_list_dict_populate(port_list_subset)
                    self.add_ports(port_list_subset, self.port_list_dict,
                                   layer_num)

            # The layer is obtained from qgeometry tables, but layer_stack
            # can have multiple data_types.  For now, the subtract will
            # happen from data_type==0.
            self.subtract_from_ground(layer_num, data_type=data_type)

#yapf: disable
    def get_subset_based_on_layer(self,
                    open_pins: Union[list, None],
                    port_list: Union[list, None],
                    jj_to_port: Union[list, None],
                    ignored_jjs: Union[list,None],
                    layer_num: int) -> Tuple[
                                            Union[list, None],
                                            Union[list, None],
                                            Union[list, None],
                                            Union[list, None]]:
        #yapf: enable
        """When user adds arguments through render_design, they do not identify the layer that the
        component is on.  So This method returns a subset of the components which are to be
        rendered for the layer_num passed to this method.

        Args:
            open_pins (Union[list, None]):  Use definition from render_design.
            port_list (Union[list, None]):  Use definition from render_design.
            jj_to_port (Union[list, None]): Use definition from render_design.
            ignored_jjs (Union[list,None]):  Use definition from render_design.
            layer_num (int): Using this layer number, identify the components
                        in the remaining arguments

        Returns:
            Tuple[ Union[list, None], Union[list, None], Union[list, None], Union[list, None]]: Subset
            of the components which are to be rendered for the layer_num passed to this method.
        """
        open_pins_subset = None
        port_list_subset = None
        jj_to_port_subset = None
        ignored_jjs_subset = None

        if open_pins:
            open_pins_subset = self.get_open_pins_in_layer(open_pins, layer_num)

        if port_list:
            port_list_subset = self.get_port_list_in_layer(port_list, layer_num)

        if jj_to_port:
            jj_to_port_subset = self.get_jj_to_port_in_layer(
                jj_to_port, layer_num)

        if ignored_jjs:
            ignored_jjs_subset = self.get_ignored_jjs_in_layer(
                ignored_jjs, layer_num)

        return open_pins_subset, port_list_subset, jj_to_port_subset, ignored_jjs_subset

    def get_port_list_in_layer(self, port_list: list, layer_num: int) -> list:
        """Reduce the port_list list and only return the port_list for layer_nums.

        Args:
            port_list (list): The list given by user for render_design.
            layer_num (int): The layer number being rendered.

        Returns:
            list: A subset of port_list for the denoted layer_num.
        """
        layer_port_list = list()

        mask_comp_element = self.path_poly_and_junction_with_valid_comps[
            'layer'] == layer_num
        path_poly_junction_layer = self.path_poly_and_junction_with_valid_comps[
            mask_comp_element]

        for comp_name, element, impedance in port_list:
            id = self.design.components[comp_name].id
            comp_element_layer_mask = (
                path_poly_junction_layer['component'] == id)
            valid_df = path_poly_junction_layer[comp_element_layer_mask]
            if not valid_df.empty:
                layer_port_list.append((comp_name, element, impedance))

        return layer_port_list

    def get_jj_to_port_in_layer(self, jj_to_port: list, layer_num: int) -> list:
        """Reduce the port_list list and only return the port_list for layer_nums.
        This is very similar to get_port_list_in_layer.  This format is different
        than what was done with renderer with comm port. The inductance and creation
        of extra sheet has been dropped.

        Args:
            jj_to_port (list): Use definition from render_design.
            layer_num (int): The layer number to render.

        Returns:
            list: Use definition from render_design.
        """
        layer_jj_to_port = list()
        mask_comp_element = self.path_poly_and_junction_with_valid_comps[
            'layer'] == layer_num
        path_poly_junction_layer = self.path_poly_and_junction_with_valid_comps[
            mask_comp_element]

        for comp_name, element, impedance in jj_to_port:
            id = self.design.components[comp_name].id
            comp_element_layer_mask = (
                path_poly_junction_layer['component'] == id)
            valid_df = path_poly_junction_layer[comp_element_layer_mask]
            if not valid_df.empty:
                layer_jj_to_port.append((comp_name, element, impedance))
        return layer_jj_to_port

    def get_ignored_jjs_in_layer(self, ignored_jjs, layer_num: int) -> list:
        """Reduce the ignored_jjs list and only return the ignored_jjs for layer_nums.

        Args:
            ignored_jjs (_type_): Use definition from render_design.
            layer_num (int): The layer number to render.

        Returns:
            list: Use definition from render_design.
        """
        layer_ignored_jjs = list()
        mask_comp_element = self.path_poly_and_junction_with_valid_comps[
            'layer'] == layer_num
        path_poly_junction_layer = self.path_poly_and_junction_with_valid_comps[
            mask_comp_element]

        for comp_name, element in ignored_jjs:
            id = self.design.components[comp_name].id
            comp_element_layer_mask = (
                path_poly_junction_layer['component'] == id)
            valid_df = path_poly_junction_layer[comp_element_layer_mask]
            if not valid_df.empty:
                layer_ignored_jjs.append((comp_name, element))
        return layer_ignored_jjs

    # yapf: disable
    def render_element(self,
                        qgeom: pd.Series,
                        is_junction: bool,
                        port_list: Union[list, None],
                        jj_to_port: Union[list, None],
                        ignored_jjs: Union[list, None]):
        # yapf: enable
        """Render an individual shape whose properties are listed in a row of
        QGeometry table. Junction elements are handled separately from non-
        junction elements, as the former consist of two rendered shapes, not
        just one.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
            is_junction (bool): Whether or not qgeom belongs to junction table.
            port_list (Union[list, None], optional): _description_. Defaults to None.
            jj_to_port (Union[list, None], optional): _description_. Defaults to None.
            ignored_jjs (Union[list, None], optional): _description_. Defaults to None.
        """
        qc_shapely = qgeom.geometry
        if is_junction:
            if self.should_render_junction(qgeom, port_list, jj_to_port,
                                           ignored_jjs):
                self.render_element_junction(qgeom, port_list, jj_to_port)
        else:
            if isinstance(qc_shapely, shapely.geometry.Polygon):
                self.render_element_poly(qgeom)
            elif isinstance(qc_shapely, shapely.geometry.LineString):
                self.render_element_path(qgeom)

    def should_render_junction(self, qgeom: pd.Series, port_list: Union[list,
                                                                        None],
                               jj_to_port: Union[list, None],
                               ignored_jjs: Union[list, None]) -> bool:
        """Expected to be replaced by grandchild of this class.

        Args:
            qgeom (pd.Series): _description_
            port_list (Union[list, None]): _description_
            jj_to_port (Union[list, None]): _description_
            ignored_jjs (Union[list, None]): _description_

        Returns:
            bool: _description_
        """
        pass

    def render_element_junction(self,
                                qgeom: pd.Series,
                                port_list: Union[list, None] = None,
                                jj_to_port: Union[list, None] = None):
        """
        Render a Josephson junction consisting of
            1. A rectangle of length pad_gap and width inductor_width. Defines lumped element
               RLC boundary condition.
            2. A line that is later used to calculate the voltage in post-processing analysis.

        At this method, ASSUME that junction is not in the ignored_jjs

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """
        #ansys_options = dict(transparency=0.0)

        qc_name = "Lj_" + str(qgeom["component"])
        qc_elt = get_clean_name(qgeom["name"])
        qc_shapely = qgeom.geometry

        # Hardcode in datatype since it is not passed in qgeometry  tables.
        result = self.design.ls.get_properties_for_layer_datatype(
            ['thickness', 'z_coord', 'material', 'fill'],
            qgeom['layer'],
            datatype=0)

        if result:
            thickness, z_coord, material, fill_value = result
        else:
            self.design.ls.layer_stack_handler_pilot_error()

        qc_width = parse_entry(qgeom.width)

        name = f"{qc_name}{QAnsysRenderer.NAME_DELIM}{qc_elt}"

        endpoints = parse_entry(list(qc_shapely.coords))
        endpoints_3d = to_vec3D(endpoints, (z_coord + (thickness / 2))).tolist()
        x0, y0, z0 = endpoints_3d[0]
        x1, y1, z0 = endpoints_3d[1]

        self.assign_mesh.append("JJ_rect_" + name)

        # Draw line
        poly_jj_name = "JJ_" + name + "_"

        poly_jj = self.current_app.modeler.create_polyline(
            endpoints_3d,
            #[endpoints_3d[0], endpoints_3d[1]],
            name=poly_jj_name,
            close_surface=False)
        poly_jj.show_arrow = True
        poly_jj.color = (128, 0, 128)

        jj_name = "JJ_rect_" + name

        poly_sheet = self.current_app.modeler.create_polyline(
            endpoints_3d,
            #[endpoints_3d[0], endpoints_3d[1]],
            name=jj_name,
            close_surface=False,
            xsection_type='Line',
            xsection_width=qc_width)

        solution_type = self.current_app.solution_type

        # If junction not in the port list or ignore list, THEN sheet inductance, if not in jj_to_port.
        # At this method, ASSUME that junction is not in the ignored_jjs
        if solution_type == 'Modal' and self.jj_to_port_is_valid and isinstance(
                jj_to_port, list) and jj_to_port:
            # Only use this logic if user defines drivenmodal solution_type,
            # and  jj_to_port list is provided by user.

            self.jj_to_port_list_dict_populate(jj_to_port)
            search_junction = (self.design._components[qgeom["component"]].name,
                               qgeom['name'])
            if search_junction in self.jj_to_port_dict.keys():
                impedance = self.jj_to_port_dict[search_junction]
                jj_name_port = "JJ_rect_" + "R_" + str(
                    qgeom["component"]) + "_" + str(qgeom['name'])
                jj_to_port_boundary = self.current_app.create_lumped_port_to_sheet(
                    sheet_name=poly_sheet.name,
                    portname=jj_name_port,
                    axisdir=endpoints_3d,
                    impedance=impedance)
        else:
            # Looks QGeometry table to pull Lj and Cj
            jj_geom_table = self.design.qgeometry.tables['junction']
            jj_of_interest = jj_geom_table[jj_geom_table['name'] == qc_elt]
            Lvalue = parse_entry(jj_of_interest['aedt_hfss_inductance'][0])
            Cvalue = parse_entry(jj_of_interest['aedt_hfss_capacitance'][0])

            lumped_rlc_boundary = self.current_app.assign_lumped_rlc_to_sheet(
                sheet_name=poly_sheet.name,
                sourcename=f'rlc_{poly_sheet.name}',
                axisdir=endpoints_3d,
                Lvalue=Lvalue,
                Cvalue=Cvalue)

    def draw_sample_holder(self):
        """Adds a vacuum box to HFSS design.  The xy coordinates are determined by
        results of using box_plus_buffer.  The z coordinate of the box is determined
        by default_options of this class. This the user can update the options prior
        to render_design.

        Note: the height of the box is NOT found by going to Multiplanar Design.
        """
        if "sample_holder_top" in self.design.variables.keys():
            p = self.design.variables
        else:
            p = self.options

        top = parse_entry(p["sample_holder_top"],
                          convert_to_unit=self.current_app.modeler.model_units)
        bottom = parse_entry(
            p["sample_holder_bottom"],
            convert_to_unit=self.current_app.modeler.model_units)
        vac_height = top - bottom
        half_vac_height = (vac_height / 2)
        half_z_coord = top - half_vac_height

        (minx, miny, maxx, maxy) = self.box_for_ansys

        # yapf: disable
        vacuum_rect = [[minx, miny, half_z_coord],
                     [maxx, miny, half_z_coord],
                     [maxx, maxy, half_z_coord],
                     [minx, maxy, half_z_coord],
                     [minx, miny, half_z_coord]]
        # yapf: enable

        box_name = "vacuum_box"

        sample_holder_rectangle = self.current_app.modeler.create_polyline(
            vacuum_rect,
            name=box_name,
            cover_surface=True,
            close_surface=True,
            matname="vacuum")

        self.current_app.modeler.thicken_sheet(sample_holder_rectangle.id,
                                               thickness=vac_height,
                                               bBothSides=True)

    def add_ports(self, port_list: list, port_list_dict: dict, layer_num: int):
        # Should be overwritten by drivenmodal, since eigenmode does not have ports.
        pass

    def add_jj_to_ports(self, jj_to_port: list, jj_to_port_dict: dict,
                        layer_num: int):
        # Should be overwritten by drivenmodal, since eigenmode does not have ports.
        pass


# yapf: disable
    def valid_input_arguments(self,
                            open_pins: Union[list, None],
                            port_list: Union[list, None],
                            jj_to_port: Union[list, None],
                            ignored_jjs: Union[list, None]):
        """The arguments should be valid names in design.  Also (component, pin)
        pairs can not be repeated within the four arguments.

        Args:
            open_pins (Union[list, None]): _description_
            port_list (Union[list, None]): _description_
            jj_to_port (Union[list, None]): _description_
            ignored_jjs (Union[list, None]): _description_

        Returns:
            _type_: _description_
        """
        # yapf: enable

        pair_used = list()

        if open_pins:
            self.open_pins_is_valid = self.confirm_open_pins_are_valid_names(
                open_pins, pair_used)
            if self.open_pins_is_valid == False:
                self.logger.error(f'Arguments are not in Design for open_pins.')
        else:
            self.open_pins_is_valid = True

        if port_list:
            self.port_list_is_valid = self.confirm_port_list_have_valid_request(
                port_list, pair_used)
            if self.port_list_is_valid == False:
                self.logger.error(f'Arguments are not in Design for port_list.')
        else:
            self.port_list_is_valid == True

        if jj_to_port:
            self.jj_to_port_is_valid = self.confirm_jj_to_port_has_valid_request(
                jj_to_port, pair_used)
            if self.jj_to_port_is_valid == False:
                self.logger.error(
                    f'Arguments are not in Design for jj_to_port.')
        else:
            self.jj_to_port_is_valid == True

        if ignored_jjs:
            self.ignored_jjs_is_valid = self.confirm_ignored_jjs_has_valid_request(
                ignored_jjs, pair_used)
            if self.ignored_jjs_is_valid == False:
                self.logger.error(
                    f'Arguments are not in Design for ignored_jjs.')
        else:
            self.ignored_jjs_is_valid = True

        if self.open_pins_is_valid == False or self.port_list_is_valid == False or self.jj_to_port_is_valid == False or self.ignored_jjs_is_valid == False:
            return False
        else:
            return True

    def reset_hfss_arguments(self):
        """Reset the value to None each time render_design is started.
        """
        self.open_pins_is_valid = None
        self.port_list_is_valid = None
        self.jj_to_port_is_valid = None
        self.ignored_jjs_is_valid = None
        self.ignored_jjs = []

    def confirm_jj_to_port_has_valid_request(self, jj_to_port: list,
                                             pair_used: list) -> bool:
        """ The jj_to_port, make sure the component_nam and element type are in design.

        Args:
            jj_to_port (list): List of tuples denoted (component_name, element_name, impedance).
            pair_used (list): Passed to multiple checks to ensure (component_name, pin)
                            are not accidentally reused.

        Returns:
            bool: True if pair in junction table.
                False if  any entry in list not found in design.
        """
        # (component_name, element_name, impedance)
        # are added to the list jj_to_port. For example,
        # ('Q1', 'rect_jj', 70)

        for component_name, element_name, impedance in jj_to_port:
            if self.qcomp_ids:
                # User wants to render a subset, ensure part of selection.
                if not self.design.components[
                        component_name].id in self.qcomp_ids:
                    self.design.logger.error(
                        f'You entered the component_name='
                        f'{self.design.components[component_name].name} and the corresponding'
                        f' name is not selection.'
                        f'The geometries will not be rendered to Ansys.')
                    return False
            junction_table = self.design.qgeometry.tables['junction']
            if self.design.components[component_name]:
                comp_id = self.design.components[component_name].id
            else:
                return False

            mask_comp_element = (junction_table['component'] == comp_id) & (
                junction_table['name'] == element_name)
            result_found_df = junction_table[mask_comp_element]

            if len(result_found_df) == 0:
                return False

            if not (isinstance(impedance, int) or isinstance(impedance, float)):
                self.logger.error(f'Impedance should be either float or int. '
                                  f'You have impedance={impedance}')
                return False
            item = (component_name, element_name)
            if item in pair_used:
                self.logger.error(
                    f'You entered the component_name={component_name} and element_name={element_name} pair twice.  '
                    f'The geometries will not be rendered to Ansys.')
                return False

            pair_used.append(item)

        return True

    def confirm_ignored_jjs_has_valid_request(self, ignored_jjs: list,
                                              pair_used: list) -> bool:
        """Check within the qgeometry junction table to confirm the component_name
        and element_name are paired on a row.

        Args:
            ignored_jjs (list): List of tuples of (component name, element_name)
            pair_used (list): Passed to multiple checks to ensure (component_name, pin)
                            are not accidentally reused.

        Returns:
            bool: True if pair in junction table.
                False if  any entry in list not found in design.
        """

        for item in ignored_jjs:
            component_name, element_name = item
            if self.qcomp_ids:
                # User wants to render a subset, ensure part of selection.
                if not self.design.components[
                        component_name].id in self.qcomp_ids:
                    self.design.logger.error(
                        f'You entered the component_name='
                        f'{self.design.components[component_name].name} and the corresponding'
                        f' name is not selection.'
                        f'The geometries will not be rendered to Ansys.')
                    return False
            junction_table = self.design.qgeometry.tables['junction']
            if self.design.components[component_name]:
                comp_id = self.design.components[component_name].id
            else:
                return False
            mask_comp_element = (junction_table['component'] == comp_id) & (
                junction_table['name'] == element_name)
            result_found_df = junction_table[mask_comp_element]

            if len(result_found_df) == 0:
                return False
            if item in pair_used:
                self.logger.error(
                    f'You entered the component_name={component_name} and element_name={element_name} pair twice.  '
                    f'The geometries will not be rendered to Ansys.')
                return False

            pair_used.append(item)
        return True

    def confirm_port_list_have_valid_request(self, port_list: list,
                                             pair_used: list) -> bool:
        """Check if all names of ports are within design.  Otherwise log an error.

        Args:
            port_list (list): The user input for ports. List of tuples of pins to
                            be rendered as ports.
            pair_used (list): Passed to multiple checks to ensure (component_name, pin)
                            are not accidentally reused.

        Returns:
            bool: True if all ports found in design.
                 False if any one component or pin is not found in design.
        """
        for comp_name, pin, impedance in port_list:
            if self.qcomp_ids:
                # User wants to render a subset, ensure part of selection.
                if not self.design.components[comp_name].id in self.qcomp_ids:
                    self.design.logger.error(
                        f'You entered the component_name='
                        f'{self.design.components[comp_name].name} and the corresponding'
                        f' name is not selection.'
                        f'The geometries will not be rendered to Ansys.')
                    return False
            if comp_name not in self.design.components.keys():
                self.port_list_names_not_valid(comp_name, pin)
                return False
            if pin not in self.design.components[comp_name].pins.keys():
                self.port_list_names_not_valid(comp_name, pin)
                return False
            if not (isinstance(impedance, int) or isinstance(impedance, float)):
                self.logger.error(f'Impedance should be either float or int. '
                                  f'You have impedance={impedance}')
                return False
            search_item = (comp_name, pin)
            if search_item in pair_used:
                self.logger.error(
                    f'You entered the component_name={comp_name} and pin={pin} pair twice.  '
                    f'The geometries will not be rendered to Ansys.')
                return False

            pair_used.append(search_item)

        return True

    def port_list_dict_populate(self, port_list: list):
        """Convert the port_list to a searchable dict.

        Args:
            port_list (list): _description_
        """
        # This should be overwritten by drivenmodal class.
        pass

    def jj_to_port_list_dict_populate(self, jj_to_port: list):
        """Convert jj_to_port to a searchable dict.

        Args:
            jj_to_port (list): _description_
        """
        # This should be overwritten by drivenmodal class.
        pass

    def set_variable(self, name: str, value: str):
        """
        Sets project-level variable in ANSYS.

        Example usage:
                self.set_variable('Lj_1', '10nH')
                self.set_variable('Cj', '0fF')
                self.set_variable('dimensionless', 1/137)

        Args:
            name (str): Name of variable.
            value (str): Amount and unit associated w/ variable.
                
        """
        variable_manager = self.current_app._variable_manager
        variable_manager[name] = value

    ######### Warnings and Errors##################################################

    def port_list_names_not_valid(self, comp_name: str, pin_name: str):
        """Stop and give error if the component name or pin name from port_list
        are not valid within design.

        Args:
            comp_name (str): Name of component which should have an open pin.
            pin_name (str): Name of pin which should be open.
        """
        self.logger.error(
            f'\n The component name or pin name within list'
            f'\nprovided to render_design are not valid.'
            f'\nYou provided: {comp_name} and {pin_name}'
            f'\n Valid components: {self.design.components.keys()}'
            f'\n Valid pins:{self.design.components[comp_name].pins.keys()}'
            f'\n ALL tuples within port_list will not be addressed.')