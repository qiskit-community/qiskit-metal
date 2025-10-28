# -*- coding: utf-8 -*-

from typing import List, Union
import pandas as pd
import math
import numpy as np
import inspect

from ansys.aedt.core import Desktop, Hfss, Q3d
from ansys.aedt.core.modeler.cad.primitives import Polyline

from qiskit_metal.renderers.renderer_base import QRendererAnalysis

#The below imports are for typecheck and will probably be removed if move to the open side.
from qiskit_metal.designs import QDesign
from qiskit_metal.toolbox_metal.bounds_for_path_and_poly_tables import BoundsForPathAndPolyTables
from qiskit_metal.toolbox_metal.parsing import parse_entry
from qiskit_metal.draw.utility import to_vec3D_list
from qiskit_metal import Dict

from qiskit_metal import config
if not config.is_building_docs():
    from qiskit_metal.toolbox_python.utility_functions import get_clean_name
    from qiskit_metal.toolbox_python.utility_functions import good_fillet_idxs


class QPyaedt(QRendererAnalysis):
    """  Will fill this out later.
    """

    # Get name of subclass to set project and design name
    GROUPS = ["Non Model", "Solids", "Unclassified", "Sheets", "Lines"]

    renderer_types = ['HFSS_DM', 'HFSS_EM', 'Q3D']

    # yapf: disable
    default_options = Dict(
        begin_disable_autosave = True, # If True, Ansys will execute faster.
        close_enable_autosave = True, # Before Ansys is closed, enable autosave.

        x_buffer_width_mm=0.25,  # Buffer between max/min x and edge of ground plane, in mm
        y_buffer_width_mm=0.25,  # Buffer between max/min y and edge of ground plane, in mm

        # For HFSS
        sample_holder_top='1.2mm',  # how tall is the vacuum above center_z
        sample_holder_bottom='-1.2mm',  # how tall is the vacuum below z=0

        Lj=10e-9,  # Lj has been previously with units of nanoHenries (nH), pyaedt expects (H)
        #Lj='10nH',  # Lj has units of nanoHenries (nH)
        Cj=0  # Cj *must* be 0 for pyEPR analysis! Cj has units of femtofarads (fF)
        # _Rj=0,  # _Rj *must* be 0 for pyEPR analysis! _Rj has units of Ohms
        # project_path=None,  # default project path; if None --> get active
        # project_name=project_name,  # default project name
        # design_name=design_name,  # default design name

        # bounding_box_scale_x = 1.2, # Ratio of 'main' chip width to bounding box width
        # bounding_box_scale_y = 1.2, # Ratio of 'main' chip length to bounding box length


        # wb_threshold = '400um',
        # wb_offset = '0um',
        # wb_size = 5,
        # plot_ansys_fields_options = Dict(
        #     name="NAME:Mag_E1",
        #     UserSpecifyName='0',
        #     UserSpecifyFolder='0',
        #     QuantityName= "Mag_E",
        #     PlotFolder= "E Field",
        #     StreamlinePlot= "False",
        #     AdjacentSidePlot= "False",
        #     FullModelPlot= "False",
        #     IntrinsicVar= "Phase=\'0deg\'",
        #     PlotGeomInfo_0= "1",
        #     PlotGeomInfo_1= "Surface",
        #     PlotGeomInfo_2= "FacesList",
        #     PlotGeomInfo_3= "1",
        # ),
    )
    """Default options"""
    # yapf: enable

    NAME_DELIM = r"_"
    """Name delimiter"""

    # This is expected to be populated by each child/grandchild of the renderer.
    # It will not be aggregated, just overwritten.
    default_setup = Dict()
    """Default setup."""

    # When additional columns are added to QGeometry, this is the example to populate it.
    # e.g. element_extensions = dict(
    #         base=dict(color=str, klayer=int),
    #         path=dict(thickness=float, material=str, perfectE=bool),
    #         poly=dict(thickness=float, material=str), )
    """Element extensions dictionary   element_extensions = dict() from base class"""

    # Add columns to junction table during QAnsysRenderer.load()
    # element_extensions  is now being populated as part of load().
    # Determined from element_table_data.

    # Dict structure MUST be same as  element_extensions!!!!!!
    # This dict will be used to update QDesign during init of renderer.
    # Keeping this as a cls dict so could be edited before renderer is instantiated.
    # To update component.options junction table.

    element_table_data = dict(
        path=dict(wire_bonds=False),
        junction=dict(inductance=default_options["Lj"],
                      capacitance=default_options["Cj"]),
        #resistance=default_options["_Rj"]),
    )
    """Element table data."""

    @classmethod
    def _get_child_class_name(cls) -> str:
        parents = inspect.getmro(cls)
        return parents[0].__name__

    def __init__(self,
                 design: "QDesign",
                 renderer_type: str,
                 project_name: Union[str, None] = None,
                 design_name: Union[str, None] = None,
                 initiate=False,
                 options: Dict = None):
        """_summary_

        Args:
            design (QDesign): Use QGeometry within either QDesign or MultiPlanar design to
                            obtain elements for Ansys.
            renderer_type (str): Choose string from list ['HFSS_DM', 'HFSS_EM', 'Q3D'] for the type of
                                design to insert into project.
            project_name (Union[str, None], optional):  Give a name, or one will be made based on class name of renderer.
                                            Defaults to None.
            design_name (Union[str, None], optional):Give a name, or one will be made based on class name of renderer.
                                            Defaults to None.
            initiate (bool, optional):  True to initiate the renderer. Defaults to False.
            options (Dict, optional): Used to override all options. Defaults to None.
        """
        self._desktop = None
        # Initialize renderer first so we can use self.options

        # if initiate is true then Ansys will be at self._desktop.
        super().__init__(design=design, initiate=initiate, options=options)

        # Keep this for self awareness.
        self.renderer_type = renderer_type.upper()

        self.current_app = None
        self.project_name = project_name
        self.design_name = design_name

        # _desktop only created if initiate=True
        if self._desktop:
            self.populate_project_and_design()

        self.box_plus_buffer = False  # For now, just use chip size.

        # Note, at this point, self._desktop should have pyaedt.

        # Default behavior is to render all components unless a strict subset was chosen
        self.render_everything = True
        self.qcomp_ids = []
        self.case = -1

        self.box_for_ansys = None
        self.chip_names_matched = None  # bool
        self.valid_chip_names = None  # set of valid chip names from layer_stack
        self.chip_subtract_dict = Dict()

        # For the components which were selected to render,
        # hold both path and poly dataframes concatenated.
        self.path_and_poly_with_valid_comps = None
        # hold both path, poly and dataframes concatenated.
        self.path_poly_and_junction_with_valid_comps = None

        self.bounds_handler = BoundsForPathAndPolyTables(self.design)
        # Make box for each row that has fill==True.
        self.fill_info = dict()
        # self.fill_info will hold the name of newly generated box,
        # along with information from layer stack
        # Moved to each render_design since this method was causing error when trying to make columns of qgeomtry tables.
        #self.fill_info = self.design.ls.get_layer_datatype_when_fill_is_true()

        self.open_pins_is_valid = None

        # Before opening the application, activate Pandas before opening Ansys.
        from ansys.aedt.core import settings
        settings.enable_pandas_output = True

    def initialized(self):
        """Abstract method. Must be implemented by the subclass.
        Is renderer ready to be used?
        Implementation must return boolean True if successful. False otherwise.
        """
        return True

    # pylint: disable=arguments-renamed
    def render_component(self, component):
        """Abstract method. Must be implemented by the subclass.
        Render the specified component.

        Args:
            component (QComponent): Component to render.
        """
        pass

    def render_chips(self,
                     draw_sample_holder: bool = True,
                     box_plus_buffer: bool = True):
        """Render all chips containing components in self.qcomp_ids.

        Args:
            draw_sample_holder (bool, optional): Option to draw vacuum box around chip. Defaults to True.
            box_plus_buffer (bool, optional): Whether or not to use a box plus buffer. Defaults to True.
        """
        # Abstract method. Must be implemented by the subclass.
        # Render all chips of the design.
        # Calls render_chip for each chip.

        a = 5
        pass

        chip_list = self.get_chip_names()
        for chip_name in chip_list:

            # This is done obtained at the start of render_design
            #  since the box includes all the chips and placed in self.box_for_ansys
            #  We don't do this for just one chip, as was done for planar.
            # if box_plus_buffer:
            #     # Get bounding box of components first
            #     pass
            # else:
            #     # Adhere to chip placement and dimensions in QDesign
            #     pass
            self.render_chip(chip_name, draw_sample_holder)

            if draw_sample_holder:  # HFSS
                # Fill this out when working on HFSS
                pass

    def render_chip(self, chip_name: str, draw_sample_holder: bool):
        """
        Render individual chips.

        Args:
            chip_name (str): Name of chip.
            draw_sample_holder (bool): Option to draw vacuum box around chip.
        """

        # This is for HFSS, will do later.  Also, we may want to do just once, BUT
        # not for every chip.
        a = 5
        pass

    def render_components(self, table_type: str, layer_num: int,
                          port_list: Union[list, None], jj_to_port: Union[list,
                                                                          None],
                          ignored_jjs: Union[list, None]):
        """
        Render components by breaking them down into individual elements.
        Render all components of the design.
        If selection is none, then render all components.

        Args:
            table_type (str): Table type (poly, path, or junction).
        """
        table = self.design.qgeometry.tables[table_type]

        #If user selected a subset, then need to use subset of table,
        #otherwise use the whole table.
        if self.qcomp_ids:
            mask_component = table['component'].isin(self.qcomp_ids)
            table = table[mask_component]

        mask_layer = table['layer'] == layer_num
        table_to_use = table[mask_layer]

        for _, qgeom in table_to_use.iterrows():
            self.render_element(qgeom,
                                bool(table_type == 'junction'),
                                port_list=port_list,
                                jj_to_port=jj_to_port,
                                ignored_jjs=ignored_jjs)

        # if table_type == 'path':
        #     self.auto_wirebonds(table)

    def render_element(self, qgeom: pd.Series, is_junction: bool,
                       port_list: Union[list, None],
                       jj_to_port: Union[list, None], ignored_jjs: Union[list,
                                                                         None]):
        #Use the method in the child class.
        pass

    # pylint: disable=arguments-renamed
    def render_element_path(self, qgeom: pd.Series):
        """Render one row from the qgeometry table.

        Args:
            qgeom (pd.Series): One row from the qgeometry table.
        """
        #super().render_element_path(qgeom)

        qc_name = self.design._components[qgeom["component"]].name
        qc_elt = get_clean_name(qgeom["name"])

        qc_shapely = qgeom.geometry  # shapely geom
        subtract = qgeom['subtract']  # expect a bool
        name = f"{qc_elt}{QPyaedt.NAME_DELIM}{qc_name}"

        qc_width = parse_entry(qgeom.width)

        layer = int(qgeom.layer)
        datatype = 0
        chip_name = str(qgeom.chip)
        result = self.design.ls.get_properties_for_layer_datatype(
            ['thickness', 'z_coord', 'material', 'fill'], layer, datatype)
        if result:
            thickness, z_coord, material, fill_value = result
        else:
            self.design.ls.layer_stack_handler_pilot_error()

        # LINESTRING does not have interior and exterior coords.
        points_2d = list(qc_shapely.coords)
        points_3d = to_vec3D_list(points_2d, z_coord + (thickness / 2))

        a_polyline = self.current_app.modeler.create_polyline(
            points_3d,
            name=name,
            cover_surface=False,
            close_surface=False,
            matname=material)

        # The transparency is hardcoded.  Ugh.
        # However, it was hardcoded without pyaedt, so for now, will leave it alone.
        self.current_app.modeler[name].transparency = 0.0

        # Note: Linestring does not have interior and exterior coords.
        qc_fillet = round(qgeom.fillet, 7)
        if qc_fillet > 0:
            self.add_fillet_linestring(qgeom, points_3d, qc_fillet, a_polyline)

        if subtract and not fill_value:
            self.logger.warning(
                '\nsubtract==True and Fill is False'
                '\nWe don\'t render the geometry since there is nothing to subtract from.'
                'FYI: The fill value comes from layer_stack, '
                'and the subtract value comes from component.')
            return

        if qc_width > 0:
            a_polyline_wider = self.add_linestring_width(qc_width,
                                                         a_polyline,
                                                         points_3d,
                                                         material=material)
            a_name = a_polyline_wider.name
            a_polyline_width_thickened = self.current_app.modeler.thicken_sheet(
                a_polyline_wider.id, thickness=thickness, bBothSides=True)

        else:
            # no widening, so just thicken it.
            a_polyline_width_thickened = self.current_app.modeler.thicken_sheet(
                a_polyline.id, thickness=thickness, bBothSides=True)

        # # Thicken after fillet.
        # self.q3d.modeler.thicken_sheet(a_polyline.id, thickness=thickness)

        if subtract is True and fill_value is True:
            # When doing subtract, the layer is the key to get information
            # Layer numbers MUST be unique in the layer_stack file.
            # If box_plus_buffer is False,
            # to determine ground size, chip names are gotten from layer_stack file.

            # Need to group subtract geometries by layer.
            if layer not in self.chip_subtract_dict:
                self.chip_subtract_dict[layer] = list()

            self.chip_subtract_dict[layer].append(a_polyline_width_thickened.id)

            # self.chip_subtract_dict[layer].append(
            #     self.q3d.modeler.object_id_dict[name])

    # pylint: disable=arguments-renamed
    def render_element_poly(self, qgeom: pd.Series):
        """Render a closed polygon.

        Args:
            qgeom (pd.Series): GeoSeries of element properties.
        """
        #super().render_element_poly(qgeom)
        ansys_options = dict(transparency=0.0)
        # pylint: disable=protected-access
        qc_name = self.design._components[qgeom["component"]].name
        qc_elt = get_clean_name(qgeom["name"])

        qc_shapely = qgeom.geometry  # shapely geom
        layer = int(qgeom.layer)
        datatype = 0
        chip_name = str(qgeom.chip)
        subtract = qgeom['subtract']  # expect a bool
        # qgeom.helper is ignored since the material for each layer is
        # obtained from the layer_stack.

        result = self.design.ls.get_properties_for_layer_datatype(
            ['thickness', 'z_coord', 'material', 'fill'], layer, datatype)

        if result:
            thickness, z_coord, material, fill_value = result
        else:
            self.design.ls.layer_stack_handler_pilot_error()

        if subtract and not fill_value:
            self.logger.warning(
                '\nsubtract==True and Fill is False'
                '\nWe don\'t render the geometry since there is nothing to subtract from.'
                'FYI: The fill value comes from layer_stack, '
                'and the subtract value comes from component.')
            return

        #still need to deal with fillet for polygons?????
        qc_fillet = round(qgeom.fillet, 7)

        name = f"{qc_elt}{QPyaedt.NAME_DELIM}{qc_name}"

        points_3d = to_vec3D_list(list(qc_shapely.exterior.coords),
                                  z_coord + (thickness / 2))

        a_polyline = self.current_app.modeler.create_polyline(
            points_3d,
            name=name,
            cover_surface=True,
            close_surface=True,
            matname=material)

        # Subtract interior shapes, if any
        inner_shape_ids = []
        if len(qc_shapely.interiors) > 0:
            for i, x in enumerate(qc_shapely.interiors):
                points_3d_interior = to_vec3D_list(list(x.coords),
                                                   z_coord + (thickness / 2))
                inner_shape = self.current_app.modeler.create_polyline(
                    points_3d_interior[:-1],
                    close_surface=True,
                    cover_surface=True,
                    matname=material)
                inner_shape_ids.append(inner_shape.id)
            result = self.current_app.modeler.subtract(name,
                                                       inner_shape_ids,
                                                       keepOriginals=False)
            self.current_app.modeler.thicken_sheet(name,
                                                   thickness=thickness,
                                                   bBothSides=True)
        else:  # No interiors

            self.current_app.modeler.thicken_sheet(a_polyline.id,
                                                   thickness=thickness,
                                                   bBothSides=True)

        if subtract is True and fill_value is True:
            # Need to group subtract geometries by layer from layer stack.
            # All names of geometries with different datatypes within same layer
            # will be grouped together.

            if layer not in self.chip_subtract_dict:
                self.chip_subtract_dict[layer] = list()

            self.chip_subtract_dict[layer].append(
                self.current_app.modeler.object_id_dict[name])

            # # Input chip info into self.chip_subtract_dict
            # if chip_name not in self.chip_subtract_dict:
            #     self.chip_subtract_dict[chip_name] = Dict()

            # # Need to group subtract geometries by chip and layer using z_coord from layer stack.
            # if layer not in self.chip_subtract_dict[chip_name][layer]:
            #     self.chip_subtract_dict[chip_name][layer] = set()

            # self.chip_subtract_dict[chip_name][layer].add(name)

        a = 5

    def _initiate_renderer(self):
        """
        Open a session of the default Ansys EDT.
        Establishes the connection to the App and Desktop only.
        """
        # https://aedtdocs.pyansys.com/API/_autosummary/pyaedt.Desktop.html
        # Don't need to add the version: Version of AEDT to use.
        # The default is None, in which case the active setup or latest installed version is used.
        desktop = Desktop(version=None,
                          non_graphical=False,
                          new_desktop=True,
                          close_on_exit=False,
                          student_version=False)

        self._desktop = desktop
        if self.options.begin_enable_autosave:
            self._desktop.disable_autosave()

        # with Desktop(specified_version="2021.2",
        #              non_graphical=False,
        #              new_desktop_session=True,
        #              close_on_exit=False,
        #              student_version=False) as desktop:

        #     self._desktop = desktop

        #     # Desktop is automatically released here.

    def force_exit_ansys(self):
        """This will allow user to force closing of Ansys.
        """

        self._desktop.force_close_desktop()

    def _close_renderer(self):
        """
        Step required to close the renderer after final execution.
        Close the connection to Ansys through pyaedt. Implementation must
        return boolean True if successful. False otherwise.

        Returns:
            bool: True
        """
        #Can use any one of three. In future, we may want to switch.
        #self._desktop.close_desktop
        if self.options.close_enable_autosave:
            self._desktop.enable_autosave()
        self._desktop.release_desktop(close_projects=False, close_on_exit=False)
        #self._desktop.force_close_desktop()
        #self._desktop.close_on_exit

        #Could add more logic for returning False.
        return True

    def disconnect_ansys(self):
        """Disconnect Ansys. In future, may want this to behave differently."""
        if self._desktop:
            self._close_renderer()

    def close(self):
        """Alias of _close_renderer()

        Returns:
            bool: True
        """
        return self._close_renderer()

    def save_screenshot(self, path: str = None, show: bool = True):
        """Save the screenshot.

        Args:
            path (str, optional): Path to save location.  Defaults to None.
            show (bool, optional): Whether or not to display the screenshot.  Defaults to True.

        Returns:
            pathlib.WindowsPath: path to png formatted screenshot.
        """
        pass

    # pylint: disable=arguments-differ
    def render_design(self,
                      selection: Union[List, None] = None,
                      box_plus_buffer: bool = True):
        """Must be implemented by the subclass to finish the logic for HFSS  OR Q3D within project.

        Renders all design chips and components.
        Note: This needs to be extended with additional logic for Q3D and HFSS.
        """
        # pylint: disable=attribute-defined-outside-init
        # # They are reset for each time render_design happens.
        self.box_plus_buffer = box_plus_buffer

        # Activate project_name and design_name before anything else
        self.activate_user_project_design()
        self.clean_user_design()

        self.chip_subtract_dict.clear()
        # Get from layer_stack, previously everything was a perfect E, except for junction., can't apply perfect boundary to 3d.
        self.assign_perfE = []
        self.assign_mesh = []
        self.qcomp_ids, self.case = self.get_unique_component_ids(selection)
        self.path_and_poly_with_valid_comps = None

        # Add the buffer, using options for renderer.
        x_buff = parse_entry(self._options["x_buffer_width_mm"])
        y_buff = parse_entry(self._options["y_buffer_width_mm"])

        result = self.bounds_handler.get_bounds_of_path_and_poly_tables(
            box_plus_buffer, self.qcomp_ids, self.case, x_buff, y_buff)

        self.box_for_ansys, self.path_and_poly_with_valid_comps, self.path_poly_and_junction_with_valid_comps, self.chip_names_matched, self.valid_chip_names = result

        # Possibly this could be done once, but if ALL, the geometries are all cleared within active design,
        # these boxes would need to be generated. We can move this to inti when clear_active_design is customized.
        self.create_fill_true_box()

    def create_fill_true_box(self):
        """ Create 3D box used for both fill and or as a
        subtract box for geometries when subtract==True from qgeometry table.
        """
        (minx, miny, maxx, maxy) = self.box_for_ansys

        for key, value in self.fill_info.items():
            # Don't need to close the polygon. But for now, being consistent with rendering Poly.
            fill_rect = [
                [minx, miny, value['z_coord'] + (value['thickness'] / 2)],
                [maxx, miny, value['z_coord'] + (value['thickness'] / 2)],
                [maxx, maxy, value['z_coord'] + (value['thickness'] / 2)],
                [minx, maxy, value['z_coord'] + (value['thickness'] / 2)],
                [minx, miny, value['z_coord'] + (value['thickness'] / 2)]
            ]

            box_name = f'layer_{value["layer"]}_datatype_{value["datatype"]}_plane'

            box_at_layer_datatype = self.current_app.modeler.create_polyline(
                fill_rect,
                name=box_name,
                cover_surface=True,
                close_surface=True,
                matname=value['material'])

            self.current_app.modeler.thicken_sheet(box_at_layer_datatype.id,
                                                   thickness=value['thickness'],
                                                   bBothSides=True)

            self.fill_info[key]['box_id'] = box_at_layer_datatype.id
            self.fill_info[key]['box_name'] = box_at_layer_datatype.name

    def aedt_render_by_layer_then_tables(self,
                                         open_pins: Union[list, None],
                                         port_list: Union[list, None],
                                         jj_to_port: Union[list, None],
                                         ignored_jjs: Union[list, None],
                                         skip_junction: bool = False,
                                         data_type: int = 0):
        pass

    def add_linestring_width(self, qc_width: float, a_polyline: Polyline,
                             points_3d: list, material: str) -> Polyline:
        """Determine the orthogonal vector.  Then sweep along a_polyline using qc_width.
        Then return the reference to new polyline with sweep in Ansys.

        Args:
            qc_width (float): The width of polyline to generate.
            a_polyline (Polyline): The center of desired polyline.
            points_3d (list): [[x0,y0,z0], ....[xn,yn,zn]] List of list of points used for a_polyline.
            material (str):  The material to widen.

        Returns:
            Polyline: Reference to polyline that was widened.
        """

        x0, y0, z0 = points_3d[0]
        x1, y1, z1 = points_3d[1]
        vlen = math.sqrt((x1 - x0)**2 + (y1 - y0)**2 + (z1 - z0)**2)

        # yapf: disable
        p0 = np.array([x0, y0, z0]) + qc_width / (2 * vlen) * np.array([y0 - y1, x1 - x0, 0])
        p1 = np.array([x0, y0, z0]) + qc_width / (2 * vlen) * np.array([y1 - y0, x0 - x1, 0])
        # yapf: enable

        shortline_name = f'{a_polyline.name}_shortline'
        shortline = self.current_app.modeler.create_polyline(
            [p0, p1],
            name=shortline_name,
            close_surface=False,
            matname=material)

        a_polyline_width = shortline.sweep_along_path(a_polyline)
        #a_polyline_width = a_polyline.sweep_along_path(shortline_name)
        return a_polyline_width

    def add_one_endcap(self,
                       comp_name: str,
                       pin_name: str,
                       layer: int,
                       endcap_str: str = 'endcap'):
        """ Create a rectangle, then add thickness and denote to be
        subtracted for open pin.

        Args:
            comp_name (str): Component which has the open pin.
            pin_name (str): Name of pin which in open within the component.
            layer (int): The layer which the user choose to put the component on.
            endcap_str (str): Used to name the geometry when rendered to Ansys.
        """
        pin_dict = self.design.components[comp_name].pins[pin_name]
        width, gap = parse_entry([pin_dict["width"], pin_dict["gap"]])
        mid, normal = parse_entry(pin_dict["middle"]), pin_dict["normal"]
        chip_name = self.design.components[comp_name].options.chip
        result = self.design.ls.get_properties_for_layer_datatype(
            ['thickness', 'z_coord', 'material', 'fill'], layer)
        if result:
            thickness, z_coord, material, fill = result
        else:
            self.design.ls.layer_stack_handler_pilot_error()

        endcap_name = f"{endcap_str}_{comp_name}_{pin_name}_{layer}"

        start_vec_xyz = mid.tolist()
        start_vec_xyz.append(z_coord + (thickness / 2))

        end_vec_xyz = (mid + gap * normal).tolist()
        end_vec_xyz.append(z_coord + (thickness / 2))

        #Give a vector in direction of normal and add a width.
        endcap_reference = self.current_app.modeler.create_polyline(
            [start_vec_xyz, end_vec_xyz],
            name=endcap_name,
            cover_surface=False,
            matname=material,
            close_surface=False,
            xsection_type='Line',
            xsection_width=2 * gap + width)

        thickened = self.current_app.modeler.thicken_sheet(endcap_reference.id,
                                                           thickness=thickness,
                                                           bBothSides=True)
        if fill:
            if layer not in self.chip_subtract_dict:
                self.chip_subtract_dict[layer] = list()

            self.chip_subtract_dict[layer].append(thickened.id)

    def add_endcaps(self,
                    layer_open_pins_list: list,
                    layer_num: int,
                    endcap_str: str = 'endcap'):
        """Add a list of end-caps for open pins for a specific layer ONLY.
        This method ASSUMES there is something in open_pins list.
        This method ASSUMES that the components and corresponding pins
        are within design.
        This method ASSUMES the list already corresponds to the layer number.
        This method wil make a sublist of open_pins for each the layer_num passed.


        Args:
            open_pins (list): list of tuples with (component name , pin name)  JUST
                            for the layer passed to this method.
            layer_num (int): The layer which the end-caps should be on.
            endcap_str (str): Used to name the geometry when rendered to Ansys.
        """
        if layer_open_pins_list:
            # Now add the end-caps for this layer only!
            for comp_name, pin_name in layer_open_pins_list:
                self.add_one_endcap(comp_name, pin_name, layer_num, endcap_str)

    def add_fillet_linestring(self, qgeom: pd.Series, points_3d: list,
                              qc_fillet: float, a_polyline: Polyline):
        """Determine the idx of Polyline vertices to fillet and fillet them.

        Args:
            qgeom (pd.Series): One row from QGeometry table._
            points_3d (list): Each entry is list of x,y,z vertex.
            qc_fillet (float): Radius of fillet value
            a_polyline (Polyline): A pyaetd primitive
                                                        used for linestring from qgeometry table.
        """
        qc_fillet = parse_entry(qc_fillet)
        idxs_to_fillet = good_fillet_idxs(
            points_3d,
            qc_fillet,
            precision=self.design._template_options.PRECISION,
            isclosed=False,
        )
        if idxs_to_fillet:
            vertices = a_polyline.vertices

            for idx in idxs_to_fillet:
                vertices[idx].fillet(radius=qc_fillet)

    def subtract_from_ground(self, layer_num: int, data_type: int = 0):
        """For each chip, subtract all "negative" shapes residing on its
        surface if any such shapes exist.
        Data is stored by layer, but we always assume each layer to be unique

        Need to use a rectangular for each layer, which has fill,
        has been made as part of create_fill_true_box.
        """
        # Subtract all the geometries for current layer from the fill/ground plane.
        key = (layer_num, data_type)
        if key in self.fill_info:
            self.current_app.modeler.subtract(
                self.fill_info[key]['box_name'],
                self.chip_subtract_dict[layer_num],
                keepOriginals=False)

        # if is_rectangle(qc_shapely):  # Draw as rectangle
        #     self.logger.debug(f"Drawing a rectangle: {name}")
        #     x_min, y_min, x_max, y_max = qc_shapely.bounds
        #     poly_ansys = self.modeler.draw_rect_corner(
        #         *parse_units([
        #             [x_min, y_min,
        #              self.design.get_chip_z(qgeom.chip)],
        #             x_max - x_min,
        #             y_max - y_min,
        #             0,
        #         ]),
        #         **ansys_options,
        #     )
        #     self.modeler.rename_obj(poly_ansys, name)

        # else:
        #     # Draw general closed poly
        #     poly_ansys = self.modeler.draw_polyline(points_3d[:-1],
        #                                             closed=True,
        #                                             **ansys_options)
        #     # rename: handle bug if the name of the cut already exits and is used to make a cut
        #     poly_ansys = poly_ansys.rename(name)

        # qc_fillet = round(qgeom.fillet, 7)
        # if qc_fillet > 0:
        #     qc_fillet = parse_units(qc_fillet)
        #     idxs_to_fillet = good_fillet_idxs(
        #         points,
        #         qc_fillet,
        #         precision=self.design._template_options.PRECISION,
        #         isclosed=True,
        #     )
        #     if idxs_to_fillet:
        #         self.modeler._fillet(qc_fillet, idxs_to_fillet, poly_ansys)

        # # Subtract interior shapes, if any
        # if len(qc_shapely.interiors) > 0:
        #     for i, x in enumerate(qc_shapely.interiors):
        #         interior_points_3d = to_vec3D(parse_units(list(x.coords)),
        #                                       qc_chip_z)
        #         inner_shape = self.modeler.draw_polyline(
        #             interior_points_3d[:-1], closed=True)
        #         self.modeler.subtract(name, [inner_shape])

        # # Input chip info into self.chip_subtract_dict
        # if qgeom.chip not in self.chip_subtract_dict:
        #     self.chip_subtract_dict[qgeom.chip] = set()

        # if qgeom["subtract"]:
        #     self.chip_subtract_dict[qgeom.chip].add(name)

    # Still implementing
    def auto_wirebonds(self, table):
        """
        Adds wirebonds to the Ansys model for path elements where;
        subtract = True and wire_bonds = True.

        Uses render options for determining of the:
        * wb_threshold -- the minimum distance between two vertices of a path for a
        wirebond to be added.
        * wb_offset -- offset distance for wirebond placement (along the direction
        of the cpw)
        * wb_size -- controls the width of the wirebond (wb_size * path['width'])
        """
        # norm_z = np.array([0, 0, 1])

        # wb_threshold = parse_units(self._options["wb_threshold"])
        # wb_offset = parse_units(self._options["wb_offset"])

        # # selecting only the qgeometry which meet criteria
        # wb_table = table.loc[table["hfss_wire_bonds"] == True]
        # wb_table2 = wb_table.loc[wb_table["subtract"] == True]

        # # looping through each qgeometry
        # for _, row in wb_table2.iterrows():
        #     geom = row["geometry"]
        #     width = row["width"]
        #     # looping through the linestring of the path to determine where WBs should be
        #     for index, i_p in enumerate(geom.coords[:-1], start=0):
        #         j_p = np.asarray(geom.coords[:][index + 1])
        #         vert_distance = parse_units(distance.euclidean(i_p, j_p))
        #         if vert_distance > wb_threshold:
        #             # Gets number of wirebonds to fit in section of path
        #             wb_count = int(vert_distance // wb_threshold)
        #             # finds the position vector
        #             wb_pos = (j_p - i_p) / (wb_count + 1)
        #             # gets the norm vector for finding the orthonormal of path
        #             wb_vec = wb_pos / np.linalg.norm(wb_pos)
        #             # finds the orthonormal (for orientation)
        #             wb_perp = np.cross(norm_z, wb_vec)[:2]
        #             # finds the first wirebond to place (rest are in the loop)
        #             wb_pos_step = parse_units(wb_pos + i_p) + (wb_vec *
        #                                                        wb_offset)
        #             # Other input values could be modified, kept to minimal selection for automation
        #             # for the time being. Loops to place N wirebonds based on length of path section.
        #             for wb_i in range(wb_count):
        #                 self.modeler.draw_wirebond(
        #                     pos=wb_pos_step + parse_units(wb_pos * wb_i),
        #                     ori=wb_perp,
        #                     width=parse_units(width * self._options["wb_size"]),
        #                     height=parse_units(width *
        #                                        self._options["wb_size"]),
        #                     z=0,
        #                     wire_diameter="0.015mm",
        #                     NumSides=6,
        #                     name="g_wb",
        #                     material="pec",
        #                     solve_inside=False,
        #                 )
        a = 5

    def get_chip_names(self) -> List[str]:
        """
        Obtain a list of chips on which the selection of components, if valid, resides.

        Returns:
            List[str]: Chips to render.
        """
        if self.case == 2:  # One or more components not in QDesign.
            self.logger.warning('One or more components not found.')
            return []
        chip_names = set()
        if self.case == 1:  # All components rendered.
            comps = self.design.components
            for qcomp in comps:
                if 'chip' not in comps[qcomp].options:
                    self.chip_designation_error()
                    return []
                # elif comps[qcomp].options.chip != 'main':
                #     #self.chip_not_main()
                #     return []
                chip_names.add(comps[qcomp].options.chip)
        else:  # Strict subset rendered.
            icomps = self.design._components
            for qcomp_id in self.qcomp_ids:
                if 'chip' not in icomps[qcomp_id].options:
                    self.chip_designation_error()
                    return []
                # elif icomps[qcomp_id].options.chip != 'main':
                #     #self.chip_not_main()
                #     return []
                chip_names.add(icomps[qcomp_id].options.chip)
        return list(chip_names)

    def get_open_pins_in_layer(self, open_pins: list, layer_num: int) -> list:
        """Reduce the open_pins list and only return the open_pins for layer_nums.

        Args:
            open_pins (list): The list given by user for render_design.
            layer_num (int): The layer number being rendered.

        Returns:
            list: A subset of open_pins for the denoted layer_num.
        """
        layer_open_pins_list = list()

        mask_comp_pin = self.path_and_poly_with_valid_comps[
            'layer'] == layer_num
        path_poly_layer = self.path_and_poly_with_valid_comps[mask_comp_pin]

        for comp_name, pin_name in open_pins:
            id = self.design.components[comp_name].id
            comp_pin_layer_mask = (path_poly_layer['component'] == id)
            valid_df = path_poly_layer[comp_pin_layer_mask]
            if not valid_df.empty:
                layer_open_pins_list.append((comp_name, pin_name))

        return layer_open_pins_list

    def confirm_open_pins_are_valid_names(self, open_pins: list,
                                          pair_used: list) -> bool:
        """Check if all names of components and corresponding pins are
        within design.  Otherwise log an error

        Args:
            open_pins (list): The user input for open_pins.
            pair_used (list): Passed to multiple checks to ensure (component_name, pin)
                            are not accidentally reused.

        Returns:
            bool: True if all components and pins found in design.
                 False if any one component or pin is not found in design.
        """

        for item in open_pins:
            comp_name, pin = item
            if self.qcomp_ids:
                # User wants to render a subset, ensure part of selection.
                if self.design.components[comp_name].id not in self.qcomp_ids:
                    self.design.logger.error(
                        f'You entered the component_name='
                        f'{self.design.components[comp_name].name} and the corresponding'
                        f' name is not selection.'
                        f'The geometries will not be rendered to Ansys.')
                    return False
            if comp_name not in self.design.components.keys():
                self.open_pin_names_not_valid(comp_name, pin)
                return False

            if pin not in self.design.components[comp_name].pins.keys():
                self.open_pin_names_not_valid(comp_name, pin)
                return False
            if item in pair_used:
                self.design.logger.error(
                    f'You entered the component_name={comp_name} and pin={pin} pair twice.  '
                    f'The geometries will not be rendered to Ansys.')
                return False

            pair_used.append(item)
        return True

    def activate_user_project_design(self):
        """If Ansys is not started, then start using the project and name defined by user.
        Otherwise, activate the project and design that user chose. It appears that pyaedt
        can identify the project, if needed, we can pro-actively activate the project.
        """
        try:
            if self.current_app:
                self.current_app.set_active_design(self.design_name)
            else:
                self._initiate_renderer()  # populates self._desktop
                self.populate_project_and_design()

        except Exception as ex:
            self.design.logger.error(
                f'Was not able to activate user\'s project and design name.  The exception is {ex}'
                f'\n Project Name:{self.project_name}, Design Name: {self.design_name}'
            )

    def populate_project_and_design(self):
        """Add project and design based on user input.
        """
        if self.renderer_type in self.renderer_types:
            if self.project_name is None:
                # Can use for future reference.
                #from pyaedt import generate_unique_project_name
                self.project_name = f'{self._get_child_class_name()}_project'
            if self.design_name is None:
                self.design_name = f'{self._get_child_class_name()}_design'
            if self.renderer_type == 'Q3D':
                self.current_app = Q3d(self.project_name, self.design_name)
            elif self.renderer_type == 'HFSS_DM':
                # Default solution type is driven modal.
                self.current_app = Hfss(self.project_name,
                                        self.design_name,
                                        solution_type='Modal')
            elif self.renderer_type == 'HFSS_EM':
                # need to explicitly identify a solution type
                self.current_app = Hfss(self.project_name,
                                        self.design_name,
                                        solution_type='Eigenmode')
        else:
            self.design.logger.error(
                f'Need to implement {self.renderer_type.upper()} in pyaedt_base.'
            )

        self.current_app.set_active_design(self.design_name)
        # Set project_name and design_name based off of the app that was just created
        self.project_name = self.current_app.project_name
        self.design_name = self.current_app.design_name

        self.current_app.modeler.model_units = "mm"
        self.current_app.modeler.oeditor.SetModelUnits(
            ["NAME:Units Parameter", "Units:=", "mm", "Rescale:=", False])

    def clean_user_design(self):
        """Clean the user project and design corresponding to the current_app

        Args: None

        Returns: None
        """
        if self._desktop and self.current_app:
            all_objects = []
            if self.project_name and self.design_name:
                self.activate_user_project_design()
                for group in self.GROUPS:
                    object_list = self.current_app.modeler.get_objects_in_group(
                        group)
                    if object_list:
                        all_objects.extend(object_list)
                self.current_app.modeler.delete(all_objects)

    ######### Warnings and Errors##################################################

    def chip_designation_error(self):
        """
        Warning message that appears when the Ansys renderer fails to locate a component's chip designation.
        Provides instructions for a temporary workaround until the layer stack is finalized.
        """
        self.logger.warning(
            "This component currently lacks a chip designation. Please add chip='main' to the component's default_options dictionary, restart the kernel, and try again."
        )

    def chip_not_main(self):
        """
        Warning message that appears when a component's chip designation is not 'main'.
        As of 05/10/21, all chip designations should be 'main' until the layer stack is finalized.
        Provides instructions for a temporary workaround until the layer stack is finalized.
        """
        self.logger.warning(
            "The chip designation for this component is not 'main'. Please set chip='main' in its default_options dictionary, restart the kernel, and try again."
        )

    def open_pin_names_not_valid(self, comp_name: str, pin_name: str):
        """Stop and give error if the component name or pin name from open_pins
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
            f'\n ALL tuples within open_pins will not be addressed.')

    #########PROPERTIES##################################################

    @property
    def desktop(self) -> Desktop:
        """Access to hidden variable for Ansys desktop.

        Returns:
            Desktop: easier reference to pyaedt desktop.
        """

        return self._desktop
