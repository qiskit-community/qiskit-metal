from typing import Union
from collections import defaultdict
import pandas as pd
import gmsh
import numpy as np

from ..renderer_base import QRendererAnalysis
from ...designs.design_base import QDesign
from .gmsh_utils import Vec3D, Vec3DArray, line_width_offset_pts, render_path_curves
from ...draw.basic import is_rectangle
from ..utils import get_min_bounding_box  # TODO: remove and put the new one written by @PritiShah
from ...toolbox_metal.parsing import parse_value
from ...toolbox_python.utility_functions import clean_name
from ... import Dict


class QGmshRenderer(QRendererAnalysis):
    """Extends QRendererAnalysis class to export designs to Gmsh using the Gmsh python API.

    Default Options:
        * x_buffer_width_mm -- Buffer between max/min x and edge of ground plane, in mm
        * y_buffer_width_mm -- Buffer between max/min y and edge of ground plane, in mm
        * mesh -- to define meshing parameters
            * max_size -- upper bound for the size of mesh node
            * min_size -- lower bound for the size of mesh node
            * smoothing -- mesh smoothing value
            * nodes_per_2pi_curve -- number of nodes for every 2π radians of curvature
            * algorithm_3d -- value to indicate meshing algorithm used by Gmsh
            * mesh_size_fields -- specify mesh size field parameters
                * min_distance_from_edges -- min distance for mesh gradient generation
                * max_distance_from_edges -- max distance for mesh gradient generation
                * distance_delta -- delta change in distance with each consecutive step
                * gradient_delta -- delta change in gradient with each consecutive step
            * num_threads -- number of threads for parallel meshing
            * export_dir -- path to mesh export directory
        * colors -- specify colors for the mesh elements, chips or layers
            * metal -- color for metallized entities
            * jj -- color for JJs
            * sub -- color for substrate entity
    """

    default_options = Dict(
        # Buffer between max/min x and edge of ground plane, in mm
        x_buffer_width_mm=0.2,
        # Buffer between max/min y and edge of ground plane, in mm
        y_buffer_width_mm=0.2,
        mesh=Dict(max_size="100um",
                  min_size="3um",
                  smoothing=10,
                  nodes_per_2pi_curve=90,
                  algorithm_3d=10,
                  mesh_size_fields=Dict(min_distance_from_edges="10um",
                                        max_distance_from_edges="130um",
                                        distance_delta="30um",
                                        gradient_delta="3um"),
                  num_threads=8,
                  export_dir="."),
        colors=Dict(
            metal=(84, 140, 168, 255),
            jj=(84, 140, 168, 150),
            sub=(180, 180, 180, 255),
        ))

    def __init__(self, design: QDesign, initiate=True, options: Dict = None):
        """
        Args:
            design (QDesign): The design.
            initiate (bool): True to initiate the renderer (Default: False).
            settings (Dict, optional): Used to override default settings. Defaults to None.
        """
        super().__init__(design=design, initiate=initiate, options=options)

    @property
    def initialized(self):
        """Abstract method. Must be implemented by the subclass.
        Is renderer ready to be used?
        Implementation must return boolean True if successful. False otherwise.
        """
        if self.model == self._model_name:
            return True
        return False

    @property
    def modeler(self):
        """Returns an instance to the Gmsh modeler"""
        return gmsh.model

    @property
    def model(self):
        """Returns the name of the current model"""
        return gmsh.model.getCurrent()

    @model.setter
    def model(self, name: str):
        """Sets the name of the current model. If not already present,
            adds a new model with the given name.
        """
        print_info = False
        try:
            gmsh.model.setCurrent(name)
        except Exception:
            gmsh.model.add(name)
            self._model_name = name
            print_info = True

        if print_info:
            self.logger.info(f"Added new model '{name}' and set as current.")

    def remove_current_model(self):
        """Removes the current Gmsh model"""
        gmsh.model.remove()

    def _initiate_renderer(self):
        """Initializes the Gmsh renderer"""
        gmsh.initialize()
        return True

    def _close_renderer(self):
        """Finalizes the Gmsh renderer"""
        gmsh.clear()
        gmsh.finalize()
        return True

    def close(self):
        """Public method to close the Gmsh renderer"""
        return self._close_renderer()

    def render_design(
        self,
        selection: Union[list, None] = None,
        open_pins: Union[list, None] = None,
        box_plus_buffer: bool = True,
        mesh_geoms: bool = True,
        skip_junctions: bool = False,
    ):
        """_summary_

        Args:
            selection (Union[list, None], optional): List of selected components to render. Defaults to None.
            open_pins (Union[list, None], optional): List of open pins to add end caps. Defaults to None.
            box_plus_buffer (bool, optional): Set to True for adding buffer to chip dimensions. Defaults to True.
            mesh_geoms (bool, optional): Set to True for meshing the geometries. Defaults to True.
            skip_junctions (bool, optional): Set to True to sip rendering the junctions. Defaults to False.
        """

        self.qcomp_ids, self.case = self.get_unique_component_ids(selection)

        if self.case == 2:
            self.logger.warning(
                "Unable to proceed with rendering. Please check selection.")
            return

        # defaultdict: chip -- geom_tag
        self.gnd_plane_dict = defaultdict(int)
        self.substrate_dict = defaultdict(int)

        # defaultdict: chip -- dict(geom_name: geom_tag)
        self.chip_subtract_dict = defaultdict(set)
        self.polys_dict = defaultdict(dict)
        self.paths_dict = defaultdict(dict)
        self.juncs_dict = defaultdict(dict)

        # TODO: sequence of events to perform
        self.render_tables(skip_junction=skip_junctions)
        self.add_endcaps(open_pins=open_pins)

        self.render_chips(box_plus_buffer=box_plus_buffer)

        gmsh.model.occ.synchronize()

        self.subtract_from_ground()
        self.fragment_interfaces()

        gmsh.model.occ.synchronize()

        self.assign_physical_groups()  # add physical groups

        if mesh_geoms:
            self.add_mesh()  # generate mesh

    def render_tables(self, skip_junction: bool = True):
        """Render components in design grouped by table type (path, poly, or junction).
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
        """Render the specified element

        Args:
            qgeom (pd.Series): QGeometry element to be rendered
            table_type (str): Table type (poly, path, or junction).
        """
        if table_type == "junction":
            self.render_element_junction(qgeom)
        elif table_type == "path":
            self.render_element_path(qgeom)
        elif table_type == "poly":
            self.render_element_poly(qgeom)
        else:
            self.logger.error(
                f'RENDERER ERROR: Unkown element type: {table_type}')

    def make_general_surface(self, curves: list[int]) -> int:
        """Create a general Gmsh surface.

        Args:
            curves (list[int]): List of Gmsh curves to make surface

        Returns:
            int: tag of created Gmsh surface
        """
        curve_loop = gmsh.model.occ.addCurveLoop(curves)
        surface = gmsh.model.occ.addPlaneSurface([curve_loop])
        return surface

    def parse_units_gmsh(
            self, _input: Union[int, float, np.ndarray, list, tuple,
                                str]) -> float:
        """Helper function to parse numbers and units

        Args:
            _input (Union[int, float, np.ndarray, list, tuple, str]): input to parse

        Returns:
            float: parsed input value
        """
        _units = {"cm": 10**3, "mm": 1, "um": 10**-3, "nm": 10**-6}
        if isinstance(_input, (int, float)):
            return _input
        elif isinstance(_input, (np.ndarray)):
            output = []
            for i in _input:
                output += [self.parse_units_gmsh(i)]
            return np.array(output)
        elif isinstance(_input, (list, tuple)):
            output = []
            for i in _input:
                output += [self.parse_units_gmsh(i)]
            return type(_input)(output)
        elif isinstance(_input, str):
            # FIXME: is this correct usage?
            return parse_value(_input, self.design.variables)
        else:
            self.logger.error(
                f"RENDERER ERROR: Expected int, str, list, np.ndarray, or tuple. Got: {type(_input)}."
            )

    def render_element_junction(self, junc: pd.Series):
        """Render an element junction.

        Args:
            junc (pd.Series): Junction to render.
        """
        qc_shapely = junc.geometry
        qc_width = self.parse_units_gmsh(junc.width)
        qc_chip_z = self.parse_units_gmsh(self.design.get_chip_z(junc.chip))
        vecs = Vec3DArray.make_vec3DArray(
            self.parse_units_gmsh(list(qc_shapely.coords)), qc_chip_z)
        qc_name = self.design._components[
            junc["component"]].name + '_' + clean_name(junc["name"])

        # Considering JJ will always be a rectangle
        v1, v2 = line_width_offset_pts(vecs.points[0],
                                       vecs.path_vecs[0],
                                       qc_width,
                                       qc_chip_z,
                                       ret_pts=False)
        v3, v4 = line_width_offset_pts(vecs.points[1],
                                       vecs.path_vecs[0],
                                       qc_width,
                                       qc_chip_z,
                                       ret_pts=False)

        v1_v3 = v1.dist(v3)
        v1_v4 = v1.dist(v4)
        vecs = [v1, v2, v4, v3, v1] if v1_v3 <= v1_v4 else [v1, v2, v3, v4, v1]
        pts = [gmsh.model.occ.addPoint(v.x, v.y, qc_chip_z) for v in vecs[:-1]]
        pts += [pts[0]]
        lines = []
        for i, p in enumerate(pts[:-1]):
            lines += [gmsh.model.occ.addLine(p, pts[i + 1])]
        curve_loop = gmsh.model.occ.addCurveLoop(lines)
        surface = gmsh.model.occ.addPlaneSurface([curve_loop])

        if junc.chip not in self.juncs_dict:
            self.juncs_dict[junc.chip] = dict()

        self.juncs_dict[junc.chip][qc_name] = surface

    def render_element_path(self, path: pd.Series):
        """Render an element path.

        Args:
            path (pd.Series): Path to render.
        """
        qc_shapely = path.geometry
        qc_width = path.width
        qc_fillet = self.parse_units_gmsh(path.fillet) if float(
            path.fillet) is not np.nan else 0.0
        qc_chip_z = self.parse_units_gmsh(self.design.get_chip_z(path.chip))
        vecs = Vec3DArray.make_vec3DArray(
            self.parse_units_gmsh(list(qc_shapely.coords)), qc_chip_z)
        curves = render_path_curves(vecs, qc_chip_z, qc_fillet, qc_width)
        surface = self.make_general_surface(curves)
        qc_name = self.design._components[
            path["component"]].name + '_' + clean_name(path["name"])

        if path.chip not in self.chip_subtract_dict:
            self.chip_subtract_dict[path.chip] = set()

        if path.chip not in self.paths_dict:
            self.paths_dict[path.chip] = dict()

        if path["subtract"]:
            self.chip_subtract_dict[path.chip].add(surface)
        else:
            self.paths_dict[path.chip][qc_name] = surface

    def make_poly_surface(self, points: list[Vec3D], chip_z: float) -> int:
        """Make a Gmsh surface for creating poly type QGeometries

        Args:
            points (list[Vec3D]): A list of 3D vectors (Vec3D) defining polygon
            chip_z (float): z-coordinate of the chip

        Returns:
            int: tag of the created Gmsh surface
        """
        lines = []
        first_tag = -1
        prev_tag = -1
        for i, pt in enumerate(points[:-1]):
            p1 = gmsh.model.occ.addPoint(pt.x, pt.y,
                                         chip_z) if i == 0 else prev_tag
            p2 = first_tag if i == (len(points) -
                                    2) else gmsh.model.occ.addPoint(
                                        points[i + 1].x, points[i +
                                                                1].y, chip_z)
            lines += [gmsh.model.occ.addLine(p1, p2)]

            prev_tag = p2
            if i == 0:
                first_tag = p1

        return self.make_general_surface(lines)

    def render_element_poly(self, poly: pd.Series):
        """Render an element poly.

        Args:
            poly (pd.Series): Poly to render.
        """
        qc_shapely = poly.geometry
        qc_chip_z = self.parse_units_gmsh(self.design.get_chip_z(poly.chip))
        vecs = Vec3DArray.make_vec3DArray(
            self.parse_units_gmsh(list(qc_shapely.exterior.coords)), qc_chip_z)
        qc_name = self.design._components[
            poly["component"]].name + '_' + clean_name(poly["name"])

        if is_rectangle(qc_shapely):
            x_min, y_min, x_max, y_max = qc_shapely.bounds
            dx, dy = np.abs(x_max - x_min), np.abs(y_max - y_min)
            surface = gmsh.model.occ.addRectangle(x_min, y_min, qc_chip_z, dx,
                                                  dy)
        else:
            surface = self.make_poly_surface(vecs.points, qc_chip_z)

        if len(qc_shapely.interiors) > 0:
            pts = np.array(list(qc_shapely.interiors[0].coords))
            int_vecs = Vec3DArray.make_vec3DArray(pts, qc_chip_z)
            int_surface = self.make_poly_surface(int_vecs.points, qc_chip_z)
            surface = gmsh.model.occ.cut([(2, surface)],
                                         [(2, int_surface)])[0][0][1]

        if poly.chip not in self.chip_subtract_dict:
            self.chip_subtract_dict[poly.chip] = set()

        if poly.chip not in self.polys_dict:
            self.polys_dict[poly.chip] = dict()

        if poly["subtract"]:
            self.chip_subtract_dict[poly.chip].add(surface)
        else:
            self.polys_dict[poly.chip][qc_name] = surface

    def add_endcaps(self, open_pins: Union[list, None] = None):
        """Create endcaps (rectangular cutouts) for all pins in the list
        open_pins and add them to chip_subtract_dict. Each element in open_pins
        takes on the form (component_name, pin_name) and corresponds to a
        single pin.

        Args:
            open_pins (Union[list, None], optional): List of tuples of pins that are open. Defaults to None.
        """
        open_pins = open_pins if open_pins is not None else []

        for comp, pin in open_pins:
            pin_dict = self.design.components[comp].pins[pin]
            width, gap = self.parse_units_gmsh(
                [pin_dict["width"], pin_dict["gap"]])
            mid, normal = self.parse_units_gmsh(
                pin_dict["middle"]), pin_dict["normal"]
            chip_name = self.design.components[comp].options.chip
            qc_chip_z = self.parse_units_gmsh(self.design.get_chip_z(chip_name))
            rect_mid = mid + normal * gap / 2
            rect_vec = Vec3D(np.array([rect_mid[0], rect_mid[1], qc_chip_z]))
            # Assumption: pins only point in x or y directions
            # If this assumption is not satisfied, draw_rect_center no longer works -> must use draw_polyline
            if abs(normal[0]) > abs(normal[1]):
                dx = gap
                dy = width + 2 * gap
                rect_x = rect_vec.x - dx / 2
                rect_y = rect_vec.y - dy / 2
                rect_z = rect_vec.z  # TODO: For 3D this will change
            else:
                dy = gap
                dx = width + 2 * gap
                rect_x = rect_vec.x - dx / 2
                rect_y = rect_vec.y - dy / 2
                rect_z = rect_vec.z  # TODO: For 3D this will change

            endcap = gmsh.model.occ.addRectangle(x=rect_x,
                                                 y=rect_y,
                                                 z=rect_z,
                                                 dx=dx,
                                                 dy=dy)
            self.chip_subtract_dict[chip_name].add(endcap)

    def render_chips(self,
                     chips: Union[str, list[str]] = [],
                     draw_sample_holder: bool = True,
                     box_plus_buffer: bool = True):
        """Render all chips of the design. calls `render_chip` to render the actual geometries

        Args:
            chips (Union[str, list[str]], optional): List of chips to render.
                                Renders all if [] or "all" is given. Defaults to [].
            draw_sample_holder (bool, optional): To draw the sample holder box. Defaults to True.
            box_plus_buffer (bool, optional): For adding buffer to chip dimensions. Defaults to True.

        Raises:
            TypeError: _description_
        """
        chip_list = []
        if isinstance(chips, str):
            if chips == "all":
                chip_list = list(self.design.chips.keys())
            else:
                raise TypeError(
                    "Expected list of chip names 'list[str]', found 'str'.")
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
                # TODO: Use gmsh.model.getBoundingBox() when shifting to 3D like so:
                # xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox()
                min_x, min_y, max_x, max_y = self.parse_units_gmsh(
                    get_min_bounding_box(self.design, self.qcomp_ids, self.case,
                                         self.logger))
                self.cw_x.update({chip_name: max_x - min_x
                                 })  # chip width along x
                self.cw_y.update({chip_name: max_y - min_y
                                 })  # chip width along y
                self.cw_x[chip_name] += 2 * self.parse_units_gmsh(
                    self._options["x_buffer_width_mm"])
                self.cw_y[chip_name] += 2 * self.parse_units_gmsh(
                    self._options["y_buffer_width_mm"])
                self.cc_x.update({chip_name:
                    (max_x + min_x) / 2})  # x coord of chip center
                self.cc_y.update({chip_name:
                    (max_y + min_y) / 2})  # y coord of chip center
            else:  # Adhere to chip placement and dimensions in QDesign
                p = self.design.get_chip_size(
                    chip_name)  # x/y center/width same for all chips
                self.cw_x.update(
                    {chip_name: self.parse_units_gmsh(p["size_x"])})
                self.cw_y.update(
                    {chip_name: self.parse_units_gmsh(p["size_y"])})
                self.cc_x.update(
                    {chip_name: self.parse_units_gmsh(p["center_x"])})
                self.cc_y.update(
                    {chip_name: self.parse_units_gmsh(p["center_y"])})
                # self.cw_x, self.cw_y, _ = self.parse_units_gmsh(
                #    [p['size_x'], p['size_y'], p['size_z']])
                # self.cc_x, self.cc_y, _ = parse_units(
                #    [p['center_x'], p['center_y'], p['center_z']])
            self.render_chip(chip_name)  #, draw_sample_holder)

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

            tolerance = self.parse_units_gmsh("1um")
            x = cc_x_left - tolerance
            y = cc_y_left - tolerance
            z = -vac_height[1]
            dx = (cc_x_right - cc_x_left) + 2 * tolerance
            dy = (cc_y_right - cc_y_left) + 2 * tolerance
            dz = sum(vac_height)
            self.vacuum_box = gmsh.model.occ.addBox(x, y, z, dx, dy, dz)

    def render_chip(self, chip_name: str):
        """Render the given chip.

        Args:
            chip_name (str): name of the chip to render
        """
        chip_dims = self.design.get_chip_size(chip_name)
        cc_z, height = self.parse_units_gmsh(
            [chip_dims["center_z"], chip_dims["size_z"]])

        chip_x = self.cc_x[chip_name] - self.cw_x[chip_name] / 2
        chip_y = self.cc_y[chip_name] - self.cw_y[chip_name] / 2
        chip_wx, chip_wy = self.cw_x[chip_name], self.cw_y[chip_name]
        gnd_plane = gmsh.model.occ.addRectangle(chip_x, chip_y, cc_z, chip_wx,
                                                chip_wy)

        substrate = gmsh.model.occ.addBox(chip_x, chip_y, cc_z, chip_wx,
                                          chip_wy, height)

        if chip_name not in self.gnd_plane_dict:
            self.gnd_plane_dict[chip_name] = -1

        if chip_name not in self.substrate_dict:
            self.substrate_dict[chip_name] = -1

        self.gnd_plane_dict[chip_name] = gnd_plane
        self.substrate_dict[chip_name] = substrate

    def subtract_from_ground(self):
        """Subtract the QGeometries in tables from the chip ground plane"""
        for chip_name, shapes in self.chip_subtract_dict.items():
            dim = 2  # TODO: extend this to 3D in the future
            shape_dim_tags = [(dim, s) for s in shapes]
            gnd_plane_dim_tag = (2, self.gnd_plane_dict[chip_name])
            subtract_gnd = gmsh.model.occ.cut([gnd_plane_dim_tag],
                                              shape_dim_tags)
            self.gnd_plane_dict[chip_name] = subtract_gnd[0][0][1]

    def fragment_interfaces(self):
        """Fragment Gmsh surfaces to ensure consistent tetrahedral meshing
        across interfaces between different materials.
        """
        chips = list(self.design.chips.keys())
        # all_metals = []
        for chip in chips:
            metals_and_gnd = list(self.polys_dict[chip].values(
            )) + list(self.paths_dict[chip].values()) + list(
                self.juncs_dict[chip].values()) + [self.gnd_plane_dict[chip]]
            dielectric = self.substrate_dict[chip]
            gmsh.model.occ.fragment([(3, dielectric)],
                                    [(2, geom) for geom in metals_and_gnd])
            # all_metals += [(2, geom) for geom in metals_and_gnd]

            # TODO: for 3D, maybe we'll need to cut metal from vacuum-box before meshing
            gmsh.model.occ.fragment([(3, self.substrate_dict[chip])],
                                    [(3, self.vacuum_box)])

    def assign_physical_groups(self):
        """Assign physical groups to classify different geometries physically.
        """
        chip_names = list(self.design.chips.keys())
        self.physical_groups = defaultdict(dict)
        all_sfs = []
        for chip in chip_names:
            if chip not in self.physical_groups:
                self.physical_groups[chip] = dict()

            # TODO: extend metal geoms to dim=3
            chip_geoms = dict(self.paths_dict[chip], **self.polys_dict[chip])
            chip_geoms.update(self.juncs_dict[chip])

            # Make physical groups for components
            for name, tag in chip_geoms.items():
                ph_tag = gmsh.model.addPhysicalGroup(2, [tag], name=name)
                self.physical_groups[chip][name] = ph_tag
                all_sfs += [tag]

            # Make physical groups for ground plane
            ph_gnd_name = "ground_plane"
            gnd_tag = self.gnd_plane_dict[chip]
            all_sfs += [gnd_tag]
            ph_gnd_tag = gmsh.model.addPhysicalGroup(2, [gnd_tag],
                                                     name=ph_gnd_name)
            self.physical_groups[chip][ph_gnd_name] = ph_gnd_tag

            # Make physical groups for substrate (volume)
            ph_sub_name = "dielectric_substrate"
            sub_tag = self.substrate_dict[chip]
            ph_sub_tag = gmsh.model.addPhysicalGroup(3, [sub_tag],
                                                     name=ph_sub_name)
            self.physical_groups[chip][ph_sub_name] = ph_sub_tag

            # Make physical groups for substrate (surfaces)
            all_sub_sfs = gmsh.model.occ.getSurfaceLoops(sub_tag)[1][0]
            all_sfs += list(all_sub_sfs)

        # Make physical groups for vacuum box (volume)
        vb_name = "vacuum_box"
        ph_vb_tag = gmsh.model.addPhysicalGroup(3, [self.vacuum_box],
                                                name=vb_name)
        self.physical_groups["global"][vb_name] = ph_vb_tag

        # Make physical groups for vacuum box (surfaces)
        vb_sfs = list(gmsh.model.occ.getSurfaceLoops(self.vacuum_box)[1][0])
        ph_vb_sfs_tag = gmsh.model.addPhysicalGroup(2,
                                                    vb_sfs,
                                                    name=(vb_name + "_sfs"))
        self.physical_groups["global"][vb_name + "_sfs"] = ph_vb_sfs_tag

    def isometric_projection(self):
        """Set the view in Gmsh to isometric view manually.
        """
        gmsh.option.setNumber("General.Trackball", 0)
        gmsh.option.setNumber("General.RotationX",
                              -np.degrees(np.arcsin(np.tan(np.pi / 6))))
        gmsh.option.setNumber("General.RotationY", 0)
        gmsh.option.setNumber("General.RotationZ", -45)

    def define_mesh_size_fields(self):
        """Define size fields for mesh size.
        """
        min_mesh_size = self.parse_units_gmsh(self._options["mesh"]["min_size"])
        max_mesh_size = self.parse_units_gmsh(self._options["mesh"]["max_size"])
        grad_delta = self.parse_units_gmsh(
            self._options["mesh"]["mesh_size_fields"]["gradient_delta"])
        dist_min = self.parse_units_gmsh(
            self._options["mesh"]["mesh_size_fields"]
            ["min_distance_from_edges"])
        dist_max = self.parse_units_gmsh(
            self._options["mesh"]["mesh_size_fields"]
            ["max_distance_from_edges"])
        dist_delta = self.parse_units_gmsh(
            self._options["mesh"]["mesh_size_fields"]["distance_delta"])
        grad_steps = int((dist_max - dist_min) / dist_delta)
        print(grad_steps)

        all_geoms = []
        poly_chips = [chip for chip in self.polys_dict.keys()]
        path_chips = [chip for chip in self.paths_dict.keys()]
        junc_chips = [chip for chip in self.juncs_dict.keys()]

        for chip in poly_chips:
            all_geoms += list(self.polys_dict[chip].values())
        for chip in path_chips:
            all_geoms += list(self.paths_dict[chip].values())
        for chip in junc_chips:
            all_geoms += list(self.juncs_dict[chip].values())

        all_geoms += list(self.gnd_plane_dict.values())

        curve_loops = [gmsh.model.occ.getCurveLoops(geom) for geom in all_geoms]
        curves = []
        for cl in curve_loops:
            for curve_tag_list in cl[1]:  # extract curves
                for curve in curve_tag_list:
                    curves += [curve]

        thresh_fields = []
        df = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(df, "CurvesList", curves)
        gmsh.model.mesh.field.setNumber(df, "NumPointsPerCurve", 100)

        for i in range(grad_steps):
            tf = gmsh.model.mesh.field.add("Threshold")
            gmsh.model.mesh.field.setNumber(tf, "DistMin", dist_min)
            gmsh.model.mesh.field.setNumber(
                tf, "DistMax", dist_max - ((grad_steps - i - 1) * dist_delta))
            gmsh.model.mesh.field.setNumber(tf, "Sigmoid", 1)
            gmsh.model.mesh.field.setNumber(tf, "InField", df)
            gmsh.model.mesh.field.setNumber(tf, "SizeMin",
                                            (i * grad_delta) + min_mesh_size)
            gmsh.model.mesh.field.setNumber(tf, "SizeMax", max_mesh_size)

            thresh_fields += [tf]

        min_field = gmsh.model.mesh.field.add("Min")
        gmsh.model.mesh.field.setNumbers(min_field, "FieldsList", thresh_fields)

        gmsh.model.mesh.field.setAsBackgroundMesh(min_field)

        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)

    def define_mesh_properties(self):
        """Define properties for mesh depending on renderer options.
        """
        min_mesh_size = self.parse_units_gmsh(self._options["mesh"]["min_size"])
        max_mesh_size = self.parse_units_gmsh(self._options["mesh"]["max_size"])
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature",
                              self._options["mesh"]["nodes_per_2pi_curve"])
        gmsh.option.setNumber("Mesh.Smoothing",
                              self._options["mesh"]["smoothing"])
        gmsh.option.setNumber("Mesh.Algorithm3D",
                              self._options["mesh"]["algorithm_3d"])
        gmsh.option.setNumber("General.NumThreads",
                              self._options["mesh"]["num_threads"])
        gmsh.option.setNumber("Mesh.MeshSizeMin", min_mesh_size)
        gmsh.option.setNumber("Mesh.MeshSizeMax", max_mesh_size)

    def add_mesh(self,
                 dim: int = 3,
                 intelli_mesh: bool = True,
                 custom_mesh_fn: callable = None):
        """Generate mesh for all geometries.

        Args:
            dim (int, optional): Specify the dimension of mesh. Defaults to 3.
        """
        if intelli_mesh:
            if custom_mesh_fn is None:
                self.define_mesh_size_fields()
            else:
                custom_mesh_fn()

        self.define_mesh_properties()
        gmsh.model.mesh.generate(dim=dim)

        color_dict = lambda color: dict(
            r=color[0], g=color[1], b=color[2], a=color[3])
        metal_color = color_dict(self._options["colors"]["metal"])
        jj_color = color_dict(self._options["colors"]["jj"])
        sub_color = color_dict(self._options["colors"]["sub"])

        for chip in list(self.design.chips.keys()):
            all_metal = list(self.polys_dict[chip].values()) + list(
                self.paths_dict[chip].values()) + [self.gnd_plane_dict[chip]]

            jjs = list(self.juncs_dict[chip].values())
            substrate = self.substrate_dict[chip]
            sub_surfaces = list(gmsh.model.occ.getSurfaceLoops(substrate)[1][0])

            gmsh.model.setColor([(3, substrate)], **sub_color)
            gmsh.model.setColor([(2, sub_surf) for sub_surf in sub_surfaces],
                                **sub_color)
            gmsh.model.setColor([(2, metal) for metal in all_metal],
                                **metal_color)
            gmsh.model.setColor([(2, jj) for jj in jjs], **jj_color)

    def launch_gui(self):
        """Launch Gmsh GUI for viewing the model.
        """
        self.isometric_projection()  # set isometric projection
        gmsh.fltk.run()

    def export_mesh(self, filename: str):
        """Export mesh from Gmsh into a file.

        Args:
            filename (str): name of the file to be exported to.
        """
        # TODO: Can gmsh support other mesh exporting formats?
        if ".msh" not in filename:
            self.logger.error(
                "RENDERER ERROR: filename needs to have a .msh extension. Exporting failed."
            )
            return

        import os
        mesh_export_dir = self._options["mesh"]["export_dir"]
        path = mesh_export_dir + '/' + filename
        if not os.path.exists(mesh_export_dir):
            os.mkdir(mesh_export_dir)

        gmsh.write(path)

    # FIXME: This doesn't work right now!!!
    def save_screenshot(self, path: str = None, show: bool = True):
        """Save the screenshot.

        Args:
            path (str, optional): Path to save location.  Defaults to None.
            show (bool, optional): Whether or not to display the screenshot.  Defaults to True.
        """
        if ".png" in path:
            gmsh.write(path)
        else:
            self.logger.error(
                f"Expected .png format, got .{path.split('.')[-1]}.")

    def render_component(self, component):
        pass