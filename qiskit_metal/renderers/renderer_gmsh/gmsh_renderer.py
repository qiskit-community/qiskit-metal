import pandas as pd
from typing import *
from collections import defaultdict
import gmsh

from ..renderer_base import QRendererAnalysis
from .gmsh_utils import *
from ...draw.basic import is_rectangle
from ... import Dict

class QGmshRenderer(QRendererAnalysis):
    """Extends QRendererAnalysis class to export designs to Gmsh using the Gmsh python API.

    Default Options:
    TODO: complete the list of default options
    """

    default_options = Dict(
        x_buffer_width_mm=0.2,  # Buffer between max/min x and edge of ground plane, in mm
        y_buffer_width_mm=0.2,  # Buffer between max/min y and edge of ground plane, in mm
    )

    def __init__(self, design: 'QDesign', initiate=True, options: Dict = None):
        """
        Args:
            design (QDesign): The design.
            initiate (bool): True to initiate the renderer (Default: False).
            settings (Dict, optional): Used to override default settings. Defaults to None.
        """
        super().__init__(design=design,
                         initiate=initiate,
                         options=options)

        self.render_everything = True

    @property
    def initialized(self):
        """Abstract method. Must be implemented by the subclass.
        Is renderer ready to be used?
        Implementation must return boolean True if successful. False otherwise.
        """
        if self.get_current_model() == self._model_name:
            return True
        return False

    @property
    def modeler(self):
        return gmsh.model

    @property
    def model(self):
        return gmsh.model.getCurrent()

    @model.setter
    def model(self, name:str):
        print_info = False
        try:
            gmsh.model.setCurrent(name)
        except Exception:
            gmsh.model.add(name)
            self._model_name = name
            print_info = True

        if print_info:
            self.logger.info(f"Added new model '{name}' and set as current.")

    def _initiate_renderer(self):
        gmsh.initialize()
        return True

    def _close_renderer(self):
        gmsh.finalize()
        return True

    def close(self):
        return self._close_renderer()

    def remove_current_model(self):
        gmsh.model.remove()

    def get_chip_names(self):
        if self.case == 2:  # One or more components not in QDesign.
            self.logger.warning("One or more components not found.")
            return []
        chip_names = set()
        if self.case == 1:  # All components rendered.
            comps = self.design.components
            for qcomp in comps:
                if "chip" not in comps[qcomp].options:
                    self.chip_designation_error()
                    return []
                chip_names.add(comps[qcomp].options.chip)
        else:  # Strict subset rendered.
            icomps = self.design._components
            for qcomp_id in self.qcomp_ids:
                if "chip" not in icomps[qcomp_id].options:
                    self.chip_designation_error()
                    return []
                chip_names.add(icomps[qcomp_id].options.chip)

        for unique_name in chip_names:
            if unique_name not in self.design.chips:
                self.chip_not_in_design_error(unique_name)

        return list(chip_names)

    def chip_designation_error(self):
        """
        Warning message that appears when the Ansys renderer fails to locate a component's chip designation.
        Provides instructions for a temporary workaround until the layer stack is finalized.
        """
        self.logger.warning(
            "This component currently lacks a chip designation. Please add chip='main' to the component's default_options dictionary, restart the kernel, and try again."
        )

    def chip_not_in_design_error(self, missing_chip: str):
        """
        Warning message that appears when the Ansys renderer fails to locate a component's chip designation in DesignPlanar (or any child of QDesign).
        Provides instructions for a temporary workaround until the layer stack is finalized.
        """
        self.logger.warning(
            f'This component currently lacks a chip designation in DesignPlanar, or any child of QDesign. '
            f'Please add dict for chip=\'{missing_chip}\' in DesignPlanar, or child of QDesign. Then restart the kernel, and try again.'
        )

    def render_design(
        self,
        selection: Union[list, None] = None,
        open_pins: Union[list, None] = None,
        box_plus_buffer: bool = True,
        ):

        self.qcomp_ids, self.case = self.get_unique_component_ids(selection)

        if self.case == 2:
            self.logger.warning(
                "Unable to proceed with rendering. Please check selection.")
            return

        self.chip_subtract_dict = defaultdict(set)
        self.gnd_plane_dict = defaultdict(int)
        self.substrate_dict = defaultdict(set)
        self.polys_dict = defaultdict(set)
        self.paths_dict = defaultdict(set)
        self.juncs_dict = defaultdict(set)

        # TODO: sequence of events to perform
        self.render_tables()

        # TODO: fill in stuff to add_endcaps
        # self.add_endcaps(open_pins)

        self.render_chips(box_plus_buffer=box_plus_buffer)
        self.subtract_from_ground()

        # self.generate_physical_groups() # add physical groups
        self.isometric_projection() # set isometric projection

        # Finalize the renderer
        gmsh.model.occ.synchronize()

        # self.add_mesh() # generate mesh


    def render_tables(self, skip_junction:bool = False):
        """
        Render components in design grouped by table type (path, poly, or junction).
        """
        for table_type in self.design.qgeometry.get_element_types():
            if not (skip_junction and table_type == "junction"):
                self.render_components(table_type)

    def render_components(self, table_type: str):
        """
        Render components by breaking them down into individual elements.

        Args:
            table_type (str): Table type (poly, path, or junction).
        """
        table = self.design.qgeometry.tables[table_type]

        if self.case == 0:
            mask = table["component"].isin(self.qcomp_ids)
            table = table[mask]

        for _, qgeom in table.iterrows():
            self.render_element(qgeom, table_type)

        if table_type == "path":
            # TODO: how to do auto wirebonds? (ON HOLD for now)
            # Make a function to render wire bonds manually?
            pass

    def render_element(self, qgeom: pd.Series, table_type: str):
        """Abstract method. Must be implemented by the subclass.
        Render the specified element

        Args:
            element (Element): Element to render.
        """
        if table_type == "junction":
            self.render_element_junction(qgeom)
        elif table_type == "path":
            self.render_element_path(qgeom)
        elif table_type == "poly":
            self.render_element_poly(qgeom)
        else:
           self.logger.error(f'RENDERER ERROR: Unkown element type: {table_type}')

    def make_general_surface(self, curves: list[int]) -> int:
        curve_loop = gmsh.model.occ.addCurveLoop(curves)
        surface = gmsh.model.occ.addPlaneSurface([curve_loop])
        return surface

    def parse_units_gmsh(self, _input):
        _units = {"cm": 10**3, "mm": 1, "um": 10**-3, "nm": 10**-6}
        if isinstance(_input, (int, float)):
            return _input
        elif isinstance(_input, (list, tuple)):
            output = []
            for i in _input:
                output += [self.parse_units_gmsh(i)]
            return type(_input)(output)
        elif isinstance(_input, str):
            # TODO: make this more robust. Might be error prone in the future
            if 'm' in _input:
                digits = float(_input[:-2].strip())
                unit = _input[-2:].strip()
                try:
                    value = digits*_units[unit]
                except KeyError:
                    value = 0.0
                    self.logger.error(f"RENDERER ERROR: Unknown unit: {unit}. Use either 'cm', 'mm', 'um', or 'nm'.")
            else:
                value = float(_input)
            return value
        else:
            self.logger.error(f"RENDERER ERROR: Expected int, str, list, or tuple. Got: {type(_input)}.")

    def render_element_junction(self, junc: pd.Series):
        """Render an element junction.

        Args:
            junc (str): Junction to render.
        """
        qc_shapely = junc.geometry
        qc_width  = self.parse_units_gmsh(junc.width)
        qc_chip_z = self.parse_units_gmsh(self.design.get_chip_z(junc.chip))
        vecs = Vec3DArray.make_vec3DArray(self.parse_units_gmsh(list(qc_shapely.coords)), qc_chip_z)

        # Considering JJ will always be a rectangle
        v1, v2 = line_width_offset_pts(vecs.points[0], vecs.path_vecs[0], qc_width, qc_chip_z, ret_pts=False)
        v3, v4 = line_width_offset_pts(vecs.points[1], vecs.path_vecs[0], qc_width, qc_chip_z, ret_pts=False)

        v1_v3 = v1.dist(v3); v1_v4 = v1.dist(v4)
        vecs = [v1, v2, v4, v3, v1] if v1_v3 <= v1_v4 else [v1, v2, v3, v4, v1]
        pts = [gmsh.model.occ.addPoint(v.x, v.y, qc_chip_z) for v in vecs[:-1]]
        pts += [pts[0]]; lines = []
        for i,p in enumerate(pts[:-1]):
            lines += [gmsh.model.occ.addLine(p, pts[i+1])]
        curve_loop = gmsh.model.occ.addCurveLoop(lines)
        surface = gmsh.model.occ.addPlaneSurface([curve_loop])

        if junc.chip not in self.juncs_dict:
            self.juncs_dict[junc.chip] = set()

        self.juncs_dict[junc.chip].add(surface)

    def render_element_path(self, path: pd.Series):
        """Render an element path.

        Args:
            path (str): Path to render.
        """
        qc_shapely = path.geometry
        qc_width = path.width
        qc_fillet = self.parse_units_gmsh(path.fillet) if float(path.fillet) is not np.nan else 0.0
        qc_chip_z = self.parse_units_gmsh(self.design.get_chip_z(path.chip))
        vecs = Vec3DArray.make_vec3DArray(self.parse_units_gmsh(list(qc_shapely.coords)), qc_chip_z)
        curves = render_path_curves(vecs, qc_chip_z, qc_fillet, qc_width)
        surface = self.make_general_surface(curves)

        if path.chip not in self.chip_subtract_dict:
            self.chip_subtract_dict[path.chip] = set()

        if path.chip not in self.paths_dict:
            self.paths_dict[path.chip] = set()

        if path["subtract"]:
            self.chip_subtract_dict[path.chip].add(surface)
        else:
            self.paths_dict[path.chip].add(surface)

    def make_poly_surface(self, points: list[Vec3D], chip_z: float) -> int:
        lines = []
        first_tag = -1
        prev_tag = -1
        for i,pt in enumerate(points[:-1]):
            p1 = gmsh.model.occ.addPoint(pt.x, pt.y, chip_z) if i == 0 else prev_tag
            p2 = first_tag if i == (len(points)-2) else \
                gmsh.model.occ.addPoint(points[i+1].x, points[i+1].y, chip_z)
            lines += [gmsh.model.occ.addLine(p1, p2)]

            prev_tag = p2
            if i == 0:
                first_tag = p1

        return self.make_general_surface(lines)

    def render_element_poly(self, poly: pd.Series):
        """Render an element poly.

        Args:
            poly (Poly): Poly to render.
        """
        qc_shapely = poly.geometry
        qc_chip_z = self.parse_units_gmsh(self.design.get_chip_z(poly.chip))
        vecs = Vec3DArray.make_vec3DArray(self.parse_units_gmsh(list(qc_shapely.exterior.coords)), qc_chip_z)

        if is_rectangle(qc_shapely):
            x_min, y_min, x_max, y_max = qc_shapely.bounds
            dx, dy = np.abs(x_max - x_min), np.abs(y_max - y_min)
            surface = gmsh.model.occ.addRectangle(x_min, y_min, qc_chip_z, dx, dy)
        else:
            surface = self.make_poly_surface(vecs.points, qc_chip_z)

        if len(qc_shapely.interiors) > 0:
            int_vecs = Vec3DArray.make_vec3DArray(
                [self.parse_units_gmsh(list(coord)) for coord in qc_shapely.interiors], qc_chip_z)
            int_surface = self.make_poly_surface(int_vecs.points, qc_chip_z)
            surface = gmsh.model.occ.cut([(2, surface)], [(2, int_surface)])


        if poly.chip not in self.chip_subtract_dict:
            self.chip_subtract_dict[poly.chip] = set()

        if poly.chip not in self.polys_dict:
            self.polys_dict[poly.chip] = set()

        if poly["subtract"]:
            self.chip_subtract_dict[poly.chip].add(surface)
        else:
            self.polys_dict[poly.chip].add(surface)

    def get_min_bounding_box(self) -> Tuple[float]:
        """
        Determine the max/min x/y coordinates of the smallest rectangular, axis-aligned
        bounding box that will enclose a selection of components to render, given by
        self.qcomp_ids. This method is only used when box_plus_buffer is True.

        Returns:
            Tuple[float]: min x, min y, max x, and max y coordinates of bounding box.
        """
        min_x_main = min_y_main = float("inf")
        max_x_main = max_y_main = float("-inf")
        if self.case == 2:  # One or more components not in QDesign.
            self.logger.warning("One or more components not found.")
        elif self.case == 1:  # All components rendered.
            for qcomp in self.design.components:
                min_x, min_y, max_x, max_y = self.design.components[
                    qcomp].qgeometry_bounds()
                min_x_main = min(min_x, min_x_main)
                min_y_main = min(min_y, min_y_main)
                max_x_main = max(max_x, max_x_main)
                max_y_main = max(max_y, max_y_main)
        else:  # Strict subset rendered.
            for qcomp_id in self.qcomp_ids:
                min_x, min_y, max_x, max_y = self.design._components[
                    qcomp_id].qgeometry_bounds()
                min_x_main = min(min_x, min_x_main)
                min_y_main = min(min_y, min_y_main)
                max_x_main = max(max_x, max_x_main)
                max_y_main = max(max_y, max_y_main)
        return min_x_main, min_y_main, max_x_main, max_y_main

    def render_chips(self,
                     chips: Union[str, list[str]] = [],
                     draw_sample_holder: bool = True,
                     box_plus_buffer: bool = True):
        """Render all chips of the design.
        Calls render_chip for each chip.
        """
        chip_list = []
        if isinstance(chips, str):
            if chips == "all":
                chip_list = list(self.design.chips.keys())
            else:
                raise TypeError("Expected list of chip names 'list[str]', found 'str'.")
        else:
            if len(chips) == 0:
                chip_list = list(self.design.chips.keys())
            else:
                chip_list = set()
                chips_in_design = self.design.chips.keys()
                for chip_name in chips:
                    if chip_name in chips_in_design:
                        chip_list.add(chip_name)

        self.cw_x, self.cw_y = Dict(), Dict()
        self.cc_x, self.cc_y = Dict(), Dict()

        for chip_name in chip_list:
            if box_plus_buffer:  # Get bounding box of components first
                min_x_main, min_y_main, max_x_main, max_y_main = self.parse_units_gmsh(
                    self.get_min_bounding_box())
                self.cw_x.update({chip_name: max_x_main - min_x_main
                                 })  # chip width along x
                self.cw_y.update({chip_name: max_y_main - min_y_main
                                 })  # chip width along y
                self.cw_x[chip_name] += 2 * self.parse_units_gmsh(
                    self._options["x_buffer_width_mm"])
                self.cw_y[chip_name] += 2 * self.parse_units_gmsh(
                    self._options["y_buffer_width_mm"])
                self.cc_x.update({chip_name:
                    (max_x_main + min_x_main) / 2})  # x coord of chip center
                self.cc_y.update({chip_name:
                    (max_y_main + min_y_main) / 2})  # y coord of chip center
            else:  # Adhere to chip placement and dimensions in QDesign
                p = self.design.get_chip_size(
                    chip_name)  # x/y center/width same for all chips
                self.cw_x.update({chip_name: self.parse_units_gmsh(p["size_x"])})
                self.cw_y.update({chip_name: self.parse_units_gmsh(p["size_y"])})
                self.cc_x.update({chip_name: self.parse_units_gmsh(p["center_x"])})
                self.cc_y.update({chip_name: self.parse_units_gmsh(p["center_y"])})
                # self.cw_x, self.cw_y, _ = self.parse_units_gmsh(
                #    [p['size_x'], p['size_y'], p['size_z']])
                # self.cc_x, self.cc_y, _ = parse_units(
                #    [p['center_x'], p['center_y'], p['center_z']])
            self.render_chip(chip_name) #, draw_sample_holder)

        if draw_sample_holder:
            if "sample_holder_top" in self.design.variables.keys():
                p = self.design.variables
            else:
                p = self.design.get_chip_size(chip_list[0])
            vac_height = self.parse_units_gmsh(
                [p["sample_holder_top"], p["sample_holder_bottom"]])
            # very simple algorithm to build the vacuum box. It could be made better in the future
            # assuming that both
            cc_x = np.array([item for item in self.cc_x.values()])
            cc_y = np.array([item for item in self.cc_y.values()])
            cw_x = np.array([item for item in self.cw_x.values()])
            cw_y = np.array([item for item in self.cw_y.values()])

            cc_x_left, cc_x_right = np.min(cc_x - cw_x / 2), np.max(cc_x +
                                                                    cw_x / 2)
            cc_y_left, cc_y_right = np.min(cc_y - cw_y / 2), np.max(cc_y +
                                                                    cw_y / 2)

            x = cc_x_left; y = cc_y_left; z = -vac_height[1]
            dx = (cc_x_right - cc_x_left)
            dy = (cc_y_right - cc_y_left)
            dz = sum(vac_height)
            self.vacuum_box = gmsh.model.occ.addBox(x, y, z, dx, dy, dz)

    def render_chip(self, chip_name: str):
        """Abstract method. Must be implemented by the subclass.
        Render the given chip.

        Args:
            name (str): chip to render
        """
        chip_dims = self.design.get_chip_size(chip_name)
        cc_z, height = self.parse_units_gmsh([chip_dims["center_z"], chip_dims["size_z"]])

        chip_x = self.cc_x[chip_name] - self.cw_x[chip_name]/2
        chip_y = self.cc_y[chip_name] - self.cw_y[chip_name]/2
        chip_wx, chip_wy = self.cw_x[chip_name], self.cw_y[chip_name]
        gnd_plane = gmsh.model.occ.addRectangle(chip_x, chip_y, cc_z, chip_wx, chip_wy)

        substrate = gmsh.model.occ.addBox(chip_x, chip_y, cc_z,
                                          chip_wx, chip_wy, height)

        if chip_name not in self.gnd_plane_dict:
            self.gnd_plane_dict[chip_name] = -1

        if chip_name not in self.substrate_dict:
            self.substrate_dict[chip_name] = set()

        self.gnd_plane_dict[chip_name] = gnd_plane
        self.substrate_dict[chip_name].add(substrate)

    def subtract_from_ground(self):
        for chip_name, shapes in self.chip_subtract_dict.items():
            dim = 2 # TODO: extend this to 3D in the future
            shape_dim_tags = [(dim, s) for s in shapes]
            gnd_plane_dim_tag = (2, self.gnd_plane_dict[chip_name])
            subtract_gnd = gmsh.model.occ.cut([gnd_plane_dim_tag], shape_dim_tags)
            self.gnd_plane_dict[chip_name] = subtract_gnd

    def isometric_projection(self):
        gmsh.option.setNumber("General.Trackball", 0)
        gmsh.option.setNumber("General.RotationX", -np.degrees(np.arcsin(np.tan(np.pi/6))))
        gmsh.option.setNumber("General.RotationY", 0)
        gmsh.option.setNumber("General.RotationZ", -45)

    def launch_gui(self):
        gmsh.fltk.run()

    def render_component(self, component):
        """Abstract method. Must be implemented by the subclass.
        Render the specified component.

        Args:
            component (QComponent): Component to render.
        """
        pass

    def save_screenshot(self, path: str = None, show: bool = True):
        """Save the screenshot.

        Args:
            path (str, optional): Path to save location.  Defaults to None.
            show (bool, optional): Whether or not to display the screenshot.  Defaults to True.

        Returns:
            pathlib.WindowsPath: path to png formatted screenshot. 
        """
        pass