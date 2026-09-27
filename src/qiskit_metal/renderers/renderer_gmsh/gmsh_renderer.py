from __future__ import annotations

from typing import Union, List, Optional
from collections import defaultdict
import pandas as pd
import numpy as np

# gmsh is an opt-in dependency (``quantum-metal[mesh]``, or its
# backward-compat alias ``[fem]``). Keep this module importable on
# the lite install — ``QGmshRenderer.__init__`` raises a clear
# ``ImportError`` via ``_require_gmsh`` if gmsh isn't available.
# The "renderer skipped" path in ``QDesign._start_renderers``
# catches that and logs.
try:
    import gmsh
except (ImportError, OSError):  # lite install, or gmsh's system libs missing
    gmsh = None

from qiskit_metal.renderers.renderer_gmsh.gmsh_utils import _require_gmsh
from qiskit_metal.renderers.renderer_base import QRenderer

from qiskit_metal.renderers.renderer_gmsh.gmsh_utils import (
    Vec3D,
    Vec3DArray,
    line_width_offset_pts,
    remove_degenerate_segments,
    render_path_curves,
)
from qiskit_metal.toolbox_metal.bounds_for_path_and_poly_tables import (
    BoundsForPathAndPolyTables,
)
from qiskit_metal.toolbox_metal.parsing import parse_value

from qiskit_metal import Dict

from qiskit_metal import config

if not config.is_building_docs():
    from qiskit_metal.toolbox_python.utility_functions import clean_name
    from qiskit_metal.toolbox_python.utility_functions import bad_fillet_idxs


class QGmshRenderer(QRenderer):
    """Extends QRendererAnalysis class to export designs to Gmsh using the Gmsh python API.

    Default Options:
        * x_buffer_width_mm -- Buffer between max/min x and edge of ground plane, in mm
        * y_buffer_width_mm -- Buffer between max/min y and edge of ground plane, in mm
        * mesh -- to define meshing parameters
            * max_size -- upper bound for the size of mesh node
            * min_size -- lower bound for the size of mesh node
            * max_size_jj -- maximum size of mesh nodes at jj
            * smoothing -- mesh smoothing value
            * nodes_per_2pi_curve -- number of nodes for every 2π radians of curvature
            * algorithm_3d -- value to indicate meshing algorithm used by Gmsh
            * num_threads -- number of threads for parallel meshing
            * mesh_size_fields -- specify mesh size field parameters
                * min_distance_from_edges -- min distance for mesh gradient generation
                * max_distance_from_edges -- max distance for mesh gradient generation
                * distance_delta -- delta change in distance with each consecutive step
                * gradient_delta -- delta change in gradient with each consecutive step
        * colors -- specify colors for the mesh elements, chips or layers
            * metal -- color for metallized entities
            * jj -- color for JJs
            * dielectric -- color for dielectric entity
        * outer_face_groups -- add one physical group per outer wall of the
          vacuum box (``outer_x-`` ... ``outer_z+``), for solvers that set a
          condition per wall. Off by default: the extra groups change what
          the exported mesh contains.

    Attributes:
        mesh_spec (MeshSpec, optional): refinement by role, net, component,
            junction or box, on top of the fields ``mesh`` options define
            (:class:`~qiskit_metal.analyses.simulation.problem.MeshSpec`); its
            ``max_size`` / ``min_size`` override those options. None: the
            options alone.
    """

    default_options = Dict(
        x_buffer_width_mm=0.2,
        y_buffer_width_mm=0.2,
        mesh=Dict(
            max_size="70um",
            min_size="5um",
            max_size_jj="5um",
            smoothing=10,
            nodes_per_2pi_curve=90,
            algorithm_3d=10,
            num_threads=8,
            mesh_size_fields=Dict(
                min_distance_from_edges="10um",
                max_distance_from_edges="130um",
                distance_delta="30um",
                gradient_delta="3um",
            ),
        ),
        colors=Dict(
            metal=(84, 140, 168, 255),
            jj=(84, 140, 168, 150),
            dielectric=(180, 180, 180, 255),
        ),
        outer_face_groups=False,
    )

    name = "gmsh"
    """Name"""

    def __init__(
        self,
        design: "MultiPlanar",
        layer_types: Union[dict, None] = None,
        initiate=True,
        options: Dict = None,
    ):
        """
        Args:
            design ('MultiPlanar'): The design.
            layer_types (Union[dict, None]): the type of layer in the format:
                                                dict(metal=[...], dielectric=[...]).
                                                Defaults to None.
            initiate (bool): True to initiate the renderer (Default: False).
            options (Dict, optional): Used to override default options. Defaults to None.
        """
        _require_gmsh()
        super().__init__(design=design, initiate=initiate, render_options=options)
        self._model_name = "gmsh_model"

        default_layer_types = dict(metal=[1], dielectric=[3])
        self.layer_types = default_layer_types if layer_types is None else layer_types

        self.bounds_handler = BoundsForPathAndPolyTables(self.design)

        self.mesh_spec = None

        # Filled by render_design; read by group_map.
        self._shape_sources = dict()
        self._render_selection = None
        self._render_open_pins = None
        self._group_map = None

    @property
    def initialized(self):
        """Returns boolean True if initialized successfully.
        False otherwise."""
        if gmsh.isInitialized():
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
        try:
            gmsh.model.remove()
        except Exception:
            self.logger.error("No model found in Gmsh to be removed.")

    def clear_design(self):
        """Clears the design in the current Gmsh model"""
        gmsh.clear()

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

    def get_thickness_for_layer_datatype(
        self, layer_num: int, datatype: int = 0
    ) -> float:
        """Function to get thickness of a particular layer and datatype
        from the layer stack.

        Args:
            layer_num (int): layer number in the layer stack
            datatype (int): datatype in the layer stack

        Returns:
            float: returns the thickness value
        """
        props = ["thickness"]
        ls_result = self.design.ls.get_properties_for_layer_datatype(
            properties=props, layer_number=layer_num, datatype=datatype
        )
        result = self.parse_units_gmsh(ls_result) if ls_result else None
        if result:
            return result[0]  # thickness is result[0]
        else:
            raise ValueError(
                f"Could not find {props} for the layer_number={layer_num}. "
                "Check your design and try again."
            )

    def get_thickness_zcoord_for_layer_datatype(
        self, layer_num: int, datatype: int = 0
    ) -> tuple[float, float]:
        """Function to get the thickness and z_coord of a particular layer
        and datatype from the layer stack.

        Args:
            layer_num (int): layer number in the layer stack
            datatype (int): datatype in the layer stack

        Returns:
            tuple[float, float]: returns the tuple (thickness, z_coord)
        """
        props = ["thickness", "z_coord"]
        ls_result = self.design.ls.get_properties_for_layer_datatype(
            properties=props, layer_number=layer_num, datatype=datatype
        )
        result = self.parse_units_gmsh(ls_result) if ls_result else None
        if result:
            return result
        else:
            raise ValueError(
                f"Could not find {props} for the layer_number={layer_num}. "
                "Check your design and try again."
            )

    def render_design(
        self,
        selection: Union[list, None] = None,
        open_pins: Union[list, None] = None,
        box_plus_buffer: bool = True,
        draw_sample_holder: bool = True,
        skip_junctions: bool = False,
        mesh_geoms: bool = True,
        ignore_metal_volume: bool = False,
        omit_ground_for_layers: list[int] | None = None,
    ):
        """Render the design in Gmsh and apply changes to modify the geometries
        according to the type of simulation. Simulation parameters provided by the user.

        Args:
            selection (Union[list, None], optional): List of selected components
                                                        to render. Defaults to None.
            open_pins (Union[list, None], optional): List of open pins to add
                                                        endcaps. Defaults to None.
            box_plus_buffer (bool, optional): Set to True for adding buffer to
                                                        chip dimensions. Defaults to True.
            draw_sample_holder (bool, optional): To draw the sample holder box. Defaults to True.
            skip_junctions (bool, optional): Set to True to sip rendering the
                                                        junctions. Defaults to False.
            mesh_geoms (bool, optional): Set to True for meshing the geometries.
                                                        Defaults to True.
            ignore_metal_volume (bool, optional): ignore the volume of metals and replace
                                                        it with a list of surfaces instead.
                                                        Defaults to False.
            omit_ground_for_layers (Optional[list[int]]): omit rendering the ground plane for
                                                         specified layers. Defaults to None.
        """

        # For handling the case when the user wants to use
        # QGmshRenderer from design.renderers.gmsh instance.
        if not self.initialized:
            self._initiate_renderer()

        # defaultdict: chip -- geom_tag
        self.layers_dict = defaultdict(list)

        # defaultdict: chip -- set(geom_tag)
        self.layer_subtract_dict = defaultdict(set)

        # defaultdict: chip -- dict(geom_name: geom_tag)
        self.polys_dict = defaultdict(dict)
        self.paths_dict = defaultdict(dict)
        self.juncs_dict = defaultdict(dict)
        self.physical_groups = defaultdict(dict)

        # Set by render_layers when the sample holder is drawn.
        self.vacuum_box = None

        # For group_map: which component shape each named group comes from.
        self._shape_sources = dict()
        self._render_selection = selection
        self._render_open_pins = open_pins
        self._group_map = None

        self.clear_design()

        self.draw_geometries(
            selection=selection,
            open_pins=open_pins,
            box_plus_buffer=box_plus_buffer,
            draw_sample_holder=draw_sample_holder,
            skip_junctions=skip_junctions,
            omit_ground_for_layers=omit_ground_for_layers,
        )

        self.apply_changes_for_simulation(
            ignore_metal_volume=ignore_metal_volume,
            draw_sample_holder=draw_sample_holder,
        )

        if mesh_geoms:
            try:
                self.add_mesh()  # generate mesh
            except Exception as e:
                self.logger.info(f"ERROR: Generate Mesh: {e}")

    def draw_geometries(
        self,
        draw_sample_holder: bool,
        selection: Union[list, None] = None,
        open_pins: Union[list, None] = None,
        box_plus_buffer: bool = True,
        skip_junctions: bool = False,
        omit_ground_for_layers: list[int] | None = None,
    ):
        """This function draws the raw geometries in Gmsh as taken from the
        QGeometry tables and applies thickness depending on the layer-stack.

        Args:
            selection (Union[list, None], optional): List of selected components
                                                        to render. Defaults to None.
            open_pins (Union[list, None], optional): List of open pins to add
                                                        endcaps. Defaults to None.
            box_plus_buffer (bool, optional): Set to True for adding buffer to
                                                        chip dimensions. Defaults to True.
            draw_sample_holder (bool): To draw the sample holder box.
            skip_junctions (bool, optional): Set to True to sip rendering the
                                                        junctions. Defaults to False.
            omit_ground_for_layers (Optional[list[int]]): omit rendering the ground plane for
                                                         specified layers. Defaults to None.
        """

        self.qcomp_ids, self.case = self.get_unique_component_ids(selection)

        if self.case == 2:
            self.logger.warning(
                "Unable to proceed with rendering. Please check selection."
            )
            return

        self.render_tables(skip_junction=skip_junctions)
        self.add_endcaps(open_pins=open_pins)
        self.render_layers(
            box_plus_buffer=box_plus_buffer,
            omit_layers=omit_ground_for_layers,
            draw_sample_holder=draw_sample_holder,
        )
        self.subtract_from_layers(omit_layers=omit_ground_for_layers)
        self.gmsh_occ_synchronize()

    def apply_changes_for_simulation(
        self, ignore_metal_volume: bool, draw_sample_holder: bool
    ):
        """This function fragments interfaces to fuse the boundaries and assigns
        physical groups to be used by an FEM solvers for defining bodies and
        boundary conditions.

        Args:
            ignore_metal_volume (bool, optional): ignore the volume of metals and replace
                                                        it with a list of surfaces instead.
            draw_sample_holder (bool): To draw the sample holder box.

        Raises:
            ValueError: raised when self.layer_types isn't set to a valid dictionary
        """
        if ignore_metal_volume and self.layer_types is None:
            raise ValueError(
                f"Expected dict for `layer_types`, but found {type(self.layer_types)}."
            )

        self.fragment_interfaces(draw_sample_holder=draw_sample_holder)
        self.gmsh_occ_synchronize()

        # Add physical groups
        self.assign_physical_groups(
            ignore_metal_volume=ignore_metal_volume,
            draw_sample_holder=draw_sample_holder,
        )

    def gmsh_occ_synchronize(self):
        """Synchronize Gmsh with the internal OpenCascade graphics engine"""
        gmsh.model.occ.synchronize()

    def render_tables(self, skip_junction: bool = True):
        """Render components in design grouped by table type (path, poly, or junction)."""
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
            # TODO: how to do auto wirebonds? Active issue: #841
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
            self.logger.error(f"RENDERER ERROR: Unkown element type: {table_type}")

    def make_general_surface(self, curves: list[int]) -> int:
        """Create a general Gmsh surface.

        Args:
            curves (List[int]): List of Gmsh curves to make surface

        Returns:
            int: tag of created Gmsh surface
        """
        curve_loop = gmsh.model.occ.addCurveLoop(curves)
        surface = gmsh.model.occ.addPlaneSurface([curve_loop])
        return surface

    def parse_units_gmsh(self, _input: Union[int, float, np.ndarray, list, tuple, str]):
        """Helper function to parse numbers and units

        Args:
            _input (Union[int, float, np.ndarray, list, tuple, str]): input to parse

        Returns:
            Union[int, float, np.ndarray, list, tuple, str]: parsed input value
        """
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
            return parse_value(_input, self.design.variables)
        else:
            self.logger.error(
                f"RENDERER ERROR: Expected int, str, list, np.ndarray, or tuple. Got: {type(_input)}."
            )

    def render_element_junction(self, junc: pd.Series):
        """Render an element of type: 'junction'

        Args:
            junc (pd.Series): Junction to render.
        """
        qc_shapely = junc.geometry
        qc_width = self.parse_units_gmsh(junc.width)
        qc_thickness, qc_z = self.get_thickness_zcoord_for_layer_datatype(
            layer_num=junc.layer
        )

        vecs = Vec3DArray.make_vec3DArray(
            self.parse_units_gmsh(list(qc_shapely.coords)), qc_z
        )
        qc_name = (
            self.design._components[junc["component"]].name
            + "_"
            + clean_name(junc["name"])
        )
        self._shape_sources[qc_name] = (
            self.design._components[junc["component"]].name,
            junc["name"],
        )

        # Considering JJ will always be a rectangle
        v1, v2 = line_width_offset_pts(
            vecs.points[0], vecs.path_vecs[0], qc_width, qc_z, ret_pts=False
        )
        v3, v4 = line_width_offset_pts(
            vecs.points[1], vecs.path_vecs[0], qc_width, qc_z, ret_pts=False
        )

        v1_v3 = Vec3D.get_distance(v1, v3)
        v1_v4 = Vec3D.get_distance(v1, v4)
        vecs = [v1, v2, v4, v3, v1] if v1_v3 <= v1_v4 else [v1, v2, v3, v4, v1]
        pts = [gmsh.model.occ.addPoint(v[0], v[1], qc_z) for v in vecs[:-1]]
        pts += [pts[0]]
        lines = []
        for i, p in enumerate(pts[:-1]):
            lines += [gmsh.model.occ.addLine(p, pts[i + 1])]
        curve_loop = gmsh.model.occ.addCurveLoop(lines)
        surface = gmsh.model.occ.addPlaneSurface([curve_loop])

        # Translate the junction to the middle of the layer
        gmsh.model.occ.translate([(2, surface)], dx=0, dy=0, dz=qc_thickness / 2)

        if junc.layer not in self.juncs_dict:
            self.juncs_dict[junc.layer] = dict()

        self.juncs_dict[junc.layer][qc_name] = [surface]

    def render_element_path(self, path: pd.Series):
        """Render an element of type: 'path'

        Args:
            path (pd.Series): Path to render.
        """
        qc_shapely = path.geometry
        qc_width = path.width
        qc_fillet = (
            self.parse_units_gmsh(path.fillet)
            if float(path.fillet) is not np.nan
            else 0.0
        )
        qc_thickness, qc_z = self.get_thickness_zcoord_for_layer_datatype(
            layer_num=path.layer
        )

        # Drop sub-width lead stubs (e.g. a route's short pin segments): they
        # collapse the width-offset geometry and make Gmsh reject a zero-length
        # line. Endpoints are preserved. See remove_degenerate_segments.
        coords = remove_degenerate_segments(list(qc_shapely.coords), qc_width)

        vecs = Vec3DArray.make_vec3DArray(self.parse_units_gmsh(coords), qc_z)
        qc_name = (
            self.design._components[path["component"]].name
            + "_"
            + clean_name(path["name"])
        )
        self._shape_sources[qc_name] = (
            self.design._components[path["component"]].name,
            path["name"],
        )
        bad_fillets = bad_fillet_idxs(coords, qc_fillet)
        curves = render_path_curves(vecs, qc_z, qc_fillet, qc_width, bad_fillets)
        surface = self.make_general_surface(curves)

        if path.layer not in self.layer_subtract_dict:
            self.layer_subtract_dict[path.layer] = set()

        if path.layer not in self.paths_dict:
            self.paths_dict[path.layer] = dict()

        if np.abs(qc_thickness) > 0:
            extruded_entity = gmsh.model.occ.extrude(
                [(2, surface)], dx=0, dy=0, dz=qc_thickness
            )
            volume = [tag for dim, tag in extruded_entity if dim == 3]

            if path["subtract"]:
                self.layer_subtract_dict[path.layer].add(volume[0])
            else:
                self.paths_dict[path.layer][qc_name] = [volume[0]]

        else:
            if path["subtract"]:
                self.layer_subtract_dict[path.layer].add(surface)
            else:
                self.paths_dict[path.layer][qc_name] = [surface]

    def make_poly_surface(self, points: list[np.ndarray], chip_z: float) -> int:
        """Make a Gmsh surface for creating poly type QGeometries

        Args:
            points (List[np.ndarray]): A list of 3D vectors (np.ndarray) defining polygon
            chip_z (float): z-coordinate of the chip

        Returns:
            int: tag of the created Gmsh surface
        """
        lines = []
        first_tag = -1
        prev_tag = -1
        for i, pt in enumerate(points[:-1]):
            p1 = gmsh.model.occ.addPoint(pt[0], pt[1], chip_z) if i == 0 else prev_tag
            p2 = (
                first_tag
                if i == (len(points) - 2)
                else gmsh.model.occ.addPoint(points[i + 1][0], points[i + 1][1], chip_z)
            )
            lines += [gmsh.model.occ.addLine(p1, p2)]

            prev_tag = p2
            if i == 0:
                first_tag = p1

        return self.make_general_surface(lines)

    def render_element_poly(self, poly: pd.Series):
        """Render an element of type: 'poly'

        Args:
            poly (pd.Series): Poly to render.
        """
        qc_shapely = poly.geometry
        qc_thickness, qc_z = self.get_thickness_zcoord_for_layer_datatype(
            layer_num=poly.layer
        )

        vecs = Vec3DArray.make_vec3DArray(
            self.parse_units_gmsh(list(qc_shapely.exterior.coords)), qc_z
        )
        qc_name = (
            self.design._components[poly["component"]].name
            + "_"
            + clean_name(poly["name"])
        )
        self._shape_sources[qc_name] = (
            self.design._components[poly["component"]].name,
            poly["name"],
        )

        surface = self.make_poly_surface(vecs.points, qc_z)

        if len(qc_shapely.interiors) > 0:
            pts = np.array(list(qc_shapely.interiors[0].coords))
            int_vecs = Vec3DArray.make_vec3DArray(pts, qc_z)
            int_surface = self.make_poly_surface(int_vecs.points, qc_z)
            surface = gmsh.model.occ.cut([(2, surface)], [(2, int_surface)])[0][0][1]

        if poly.layer not in self.layer_subtract_dict:
            self.layer_subtract_dict[poly.layer] = set()

        if poly.layer not in self.polys_dict:
            self.polys_dict[poly.layer] = dict()

        if np.abs(qc_thickness) > 0:
            extruded_entity = gmsh.model.occ.extrude(
                [(2, surface)], dx=0, dy=0, dz=qc_thickness
            )
            volume = [tag for dim, tag in extruded_entity if dim == 3]

            if poly["subtract"]:
                self.layer_subtract_dict[poly.layer].add(volume[0])
            else:
                self.polys_dict[poly.layer][qc_name] = [volume[0]]

        else:
            if poly["subtract"]:
                self.layer_subtract_dict[poly.layer].add(surface)
            else:
                self.polys_dict[poly.layer][qc_name] = [surface]

    def add_endcaps(self, open_pins: Union[list, None] = None):
        """Create endcaps (rectangular cutouts) for all pins in the list
        open_pins and add them to layer_subtract_dict. Each element in open_pins
        takes on the form (component_name, pin_name) and corresponds to a
        single pin.

        Args:
            open_pins (Union[list, None], optional): List of tuples of pins that are open. Defaults to None.
        """
        open_pins = open_pins if open_pins is not None else []

        for comp, pin in open_pins:
            if comp not in self.design.components:
                raise ValueError(f"Component '{comp}' not present in current design.")

            qcomp = self.design.components[comp]
            qc_layer = int(qcomp.options.layer)

            if pin not in qcomp.pins:
                raise ValueError(f"Pin '{pin}' not present in component '{comp}'.")

            pin_dict = qcomp.pins[pin]
            width, gap = self.parse_units_gmsh([pin_dict["width"], pin_dict["gap"]])
            mid, normal = self.parse_units_gmsh(pin_dict["middle"]), pin_dict["normal"]
            qc_thickness, qc_z = self.get_thickness_zcoord_for_layer_datatype(
                layer_num=qc_layer
            )

            rect_mid = mid + normal * gap / 2
            rect_vec = np.array([rect_mid[0], rect_mid[1], qc_z])
            # Assumption: pins only point in x or y directions
            # If this assumption is not satisfied, addBox() no longer works
            # Solution: must draw points, lines, and shapes manually and then extrude
            if abs(normal[0]) > abs(normal[1]):
                dx = gap
                dy = width + 2 * gap
                rect_x = rect_vec[0] - dx / 2
                rect_y = rect_vec[1] - dy / 2
                rect_z = rect_vec[2]
            else:
                dy = gap
                dx = width + 2 * gap
                rect_x = rect_vec[0] - dx / 2
                rect_y = rect_vec[1] - dy / 2
                rect_z = rect_vec[2]

            if np.abs(qc_thickness) > 0:
                endcap = gmsh.model.occ.addBox(
                    x=rect_x, y=rect_y, z=rect_z, dx=dx, dy=dy, dz=qc_thickness
                )
            else:
                endcap = gmsh.model.occ.addRectangle(
                    x=rect_x, y=rect_y, z=rect_z, dx=dx, dy=dy
                )
            self.layer_subtract_dict[qc_layer].add(endcap)

    def render_layers(
        self,
        draw_sample_holder: bool,
        omit_layers: list[int] | None = None,
        box_plus_buffer: bool = True,
    ):
        """Render all chips of the design. calls `render_chip` to render the actual geometries

        Args:
            omit_layers (Optional[List[int]]): List of layers to omit render.
                                               Renders all if [] or None is given.
                                               Defaults to None.
            draw_sample_holder (bool): To draw the sample holder box.
            box_plus_buffer (bool, optional): For adding buffer to chip dimensions.
                                              Defaults to True.
        """
        layer_list = list(set(l for l in self.design.ls.ls_df["layer"]))

        if omit_layers is not None:
            layer_list = list(l for l in layer_list if l not in omit_layers)

        for layer in layer_list:
            # Add the buffer, using options for renderer.
            x_buff = self.parse_units_gmsh(self._options["x_buffer_width_mm"])
            y_buff = self.parse_units_gmsh(self._options["y_buffer_width_mm"])

            result = self.bounds_handler.get_bounds_of_path_and_poly_tables(
                box_plus_buffer, self.qcomp_ids, self.case, x_buff, y_buff
            )

            (
                self.box_xy_bounds,
                self.path_and_poly_with_valid_comps,
                self.path_poly_and_junction_valid_comps,
                self.chip_names_matched,
                self.valid_chip_names,
            ) = result

            if not self.chip_names_matched:
                raise ValueError(
                    "The chip names in Qgeometry tables do not match with "
                    "the ones in the layer-stack. Please re-check your design."
                )

            self.render_layer(layer)

        if draw_sample_holder:
            if "sample_holder_top" in self.design.variables.keys():
                p = self.design.variables
            else:
                p = self.design._uwave_package

            vac_height = self.parse_units_gmsh(
                [p["sample_holder_top"], p["sample_holder_bottom"]]
            )

            # This tolerance is needed for Gmsh to not cut
            # the vacuum_box into two separate volumes when the
            # substrate volume is subtracted from it
            tol = self.parse_units_gmsh("1um")
            x = self.box_xy_bounds[0] - tol
            y = self.box_xy_bounds[1] - tol
            z = -vac_height[1]
            dx = (self.box_xy_bounds[2] - self.box_xy_bounds[0]) + 2 * tol
            dy = (self.box_xy_bounds[3] - self.box_xy_bounds[1]) + 2 * tol
            dz = sum(vac_height)
            self.vacuum_box = gmsh.model.occ.addBox(x, y, z, dx, dy, dz)

    def render_layer(self, layer_number: int, datatype: int = 0):
        """Render the given layer number and datatype.

        Args:
            layer_number (int): number of the layer to render
            datatype (int): number of the datatype. Defaults to 0.

        Raises:
            ValueError: if the required properties are not found
                            in the layer-stack
        """
        thickness, z_coord = self.get_thickness_zcoord_for_layer_datatype(
            layer_num=layer_number, datatype=datatype
        )

        layer_x, layer_y = self.box_xy_bounds[0:2]
        layer_wx = self.box_xy_bounds[2] - self.box_xy_bounds[0]
        layer_wy = self.box_xy_bounds[3] - self.box_xy_bounds[1]

        # Check if thickness == 0, then draw a rectangle instead
        if np.abs(thickness) > 0:
            layer_tag = gmsh.model.occ.addBox(
                layer_x, layer_y, z_coord, layer_wx, layer_wy, thickness
            )
        else:
            layer_tag = gmsh.model.occ.addRectangle(
                layer_x, layer_y, z_coord, layer_wx, layer_wy
            )

        if layer_number not in self.layers_dict:
            self.layers_dict[layer_number] = [-1]

        self.layers_dict[layer_number] = [layer_tag]

    def subtract_from_layers(self, omit_layers: list[int] | None = None):
        """Subtract the QGeometries in tables from the chip ground plane

        Args:
            omit_layers (Optional[List[int]]): List of layers to omit render.
                                               Renders all if [] or None is given.
                                               Defaults to None.
        """
        for layer_num, shapes in self.layer_subtract_dict.items():
            if omit_layers is not None and layer_num in omit_layers:
                continue

            thickness = self.get_thickness_for_layer_datatype(layer_num=layer_num)

            # Check if thickness == 0, then subtract with dim=2
            dim = 3 if np.abs(thickness) > 0 else 2
            shape_dim_tags = [(dim, s) for s in shapes]
            layer_dim_tag = (dim, self.layers_dict[layer_num][0])
            tool_dimtags = [layer_dim_tag]
            if len(shape_dim_tags) > 0:
                subtract_layer = gmsh.model.occ.cut(tool_dimtags, shape_dim_tags)

                updated_layer_geoms = []
                for i in range(len(tool_dimtags)):
                    if len(subtract_layer[1][i]) > 0:
                        updated_layer_geoms += [tag for _, tag in subtract_layer[1][i]]

                self.layers_dict[layer_num] = updated_layer_geoms

    def fragment_interfaces(self, draw_sample_holder: bool):
        """Fragment Gmsh surfaces to ensure consistent tetrahedral meshing
        across interfaces between different materials.

        Args:
            draw_sample_holder (bool): To draw the sample holder box.
        """
        all_geom_dimtags = list()
        all_layer_geoms = defaultdict(dict)
        all_dicts = (self.paths_dict, self.polys_dict)

        for d in all_dicts:
            for layer, geoms in d.items():
                if layer not in all_layer_geoms:
                    all_layer_geoms[layer] = dict()
                all_layer_geoms[layer].update(geoms)

        for layer, geom_id in self.layers_dict.items():
            if layer not in all_layer_geoms:
                all_layer_geoms[layer] = dict()

            layer_type = (
                "ground" if layer in self.layer_types["metal"] else "dielectric"
            )
            all_layer_geoms[layer].update({f"{layer_type}_layer_{layer}": geom_id})

        for layer, geoms in all_layer_geoms.items():
            # Check if thickness == 0, then fragment differently
            thickness = self.get_thickness_for_layer_datatype(layer_num=layer)
            geom_dim = 3 if np.abs(thickness) > 0 else 2
            for _, geom_ids in geoms.items():
                all_geom_dimtags += [(geom_dim, id) for id in geom_ids]

        for _, geoms in self.juncs_dict.items():
            for _, jj_sfs in geoms.items():
                all_geom_dimtags += [(2, jj) for jj in jj_sfs]

        if draw_sample_holder:
            object_dimtag = (3, self.vacuum_box)
            all_layer_geoms[-1] = dict(vacuum_box=[self.vacuum_box])
            fragmented_geoms = gmsh.model.occ.fragment(
                [object_dimtag], all_geom_dimtags
            )
            # Extract the new vacuum_box volume
            self.vacuum_box = fragmented_geoms[1][0][0][1]
        else:
            # Fragment against one of the dim=3 objects (no vacuum box here).
            dim3_dimtag = [(dim, tag) for dim, tag in all_geom_dimtags if dim == 3]
            object_dimtag = (
                dim3_dimtag[0] if len(dim3_dimtag) > 0 else all_geom_dimtags[0]
            )
            all_geom_dimtags.remove(object_dimtag)
            fragmented_geoms = gmsh.model.occ.fragment(
                [object_dimtag], all_geom_dimtags
            )

        # ``fragment`` renumbers entities. Remap each input entity to its
        # resulting tag using the output map (``fragmented_geoms[1]``, parallel
        # to the input order: the reference object first, then
        # ``all_geom_dimtags``), so the tracking dicts point at live tags. The
        # previous approach zipped the inputs against the flat result list,
        # which misaligned whenever ``fragment`` split or reordered volumes —
        # raising "(3, N) is not in list" (reference volume renumbered) or
        # "Unknown OpenCASCADE volume with tag N" (stale tag left in a dict),
        # notably for the no-sample-holder path with many metal volumes.
        input_dimtags = [object_dimtag] + all_geom_dimtags
        out_map = fragmented_geoms[1]
        all_dicts = {
            0: self.paths_dict,
            1: self.polys_dict,
            2: self.juncs_dict,
            3: self.layers_dict,
        }
        for old, children in zip(input_dimtags, out_map):
            if not children:
                continue
            new = children[0]
            if old == new:
                continue
            for i, d in all_dicts.items():
                for l, geoms in d.items():
                    if isinstance(geoms, dict):
                        for name, geom_id in geoms.items():
                            if len(geom_id) > 0 and geom_id[0] == old[1]:
                                all_dicts[i][l][name].append(new[1])
                                all_dicts[i][l][name].remove(old[1])
                    elif isinstance(geoms, list):
                        for geom_id in geoms:
                            if geom_id == old[1]:
                                all_dicts[i][l].append(new[1])
                                all_dicts[i][l].remove(old[1])

        # TODO: Do we require 3D junctions? Active issue: #842
        # all_juncs = []
        # for layer_juncs in self.juncs_dict.values():
        #     for _, surf in layer_juncs.items():
        #         all_juncs += surf

        # junc_dimtags = [(2, junc) for junc in all_juncs]
        # gmsh.model.occ.fragment([(3, self.vacuum_box)], junc_dimtags)

    def get_all_metal_surfaces(self):
        metal_geoms = list()
        surf_tags = list()
        for layer in self.layer_types["metal"]:
            thickness = self.get_thickness_for_layer_datatype(layer_num=layer)

            for _, tag in self.juncs_dict[layer].items():
                surf_tags += tag

            if thickness > 0.0:
                for _, tag in self.polys_dict[layer].items():
                    metal_geoms += tag
                for _, tag in self.paths_dict[layer].items():
                    metal_geoms += tag
                metal_geoms += self.layers_dict[layer]
            else:
                for _, tag in self.polys_dict[layer].items():
                    surf_tags += tag
                for _, tag in self.paths_dict[layer].items():
                    surf_tags += tag
                surf_tags += self.layers_dict[layer]

        for geom in metal_geoms:
            surf_tags += list(gmsh.model.occ.getSurfaceLoops(geom)[1][0])

        return surf_tags

    def assign_physical_groups(
        self, ignore_metal_volume: bool, draw_sample_holder: bool
    ):
        """Assign physical groups to classify different geometries physically.

        Args:
            ignore_metal_volume (bool, optional): ignore the volume of metals and replace
                                                        it with a list of surfaces instead.
            draw_sample_holder (bool): To draw the sample holder box.

        Raises:
            ValueError: if self.layer_types is not a dict
            ValueError: if layer number is not in self.layer_types
        """
        layer_numbers = list(set(l for l in self.design.ls.ls_df["layer"]))
        for layer in layer_numbers:
            # TODO: check if thickness == 0, then fragment differently
            layer_thickness = self.get_thickness_for_layer_datatype(layer_num=layer)
            layer_dim = 3 if np.abs(layer_thickness) > 0 else 2

            if layer not in self.physical_groups:
                self.physical_groups[layer] = dict()

            # Check if a component is drawn on that layer
            valid_layers = set(
                list(self.paths_dict.keys()) + list(self.polys_dict.keys())
            )
            if layer in valid_layers:
                # Make physical groups for components
                layer_geoms = dict(self.paths_dict[layer], **self.polys_dict[layer])
                for name, tag in layer_geoms.items():
                    if layer_dim == 3:
                        tags = gmsh.model.occ.getSurfaceLoops(tag[0])[1][0]
                        metal_layer = (
                            True if layer in self.layer_types["metal"] else False
                        )
                        if not metal_layer or (metal_layer and not ignore_metal_volume):
                            ph_vol_tag = gmsh.model.addPhysicalGroup(
                                dim=layer_dim, tags=tag, name=name
                            )
                            self.physical_groups[layer][name] = ph_vol_tag

                        ph_sfs_tag = gmsh.model.addPhysicalGroup(
                            dim=2, tags=tags, name=f"{name}_sfs"
                        )
                        self.physical_groups[layer][f"{name}_sfs"] = ph_sfs_tag
                    else:
                        ph_tag = gmsh.model.addPhysicalGroup(
                            dim=layer_dim, tags=tag, name=name
                        )
                        self.physical_groups[layer][name] = ph_tag

                # TODO: Do we require 3D junctions? Active issue: #842
                for name, tag in self.juncs_dict[layer].items():
                    ph_junc_tag = gmsh.model.addPhysicalGroup(
                        dim=2, tags=tag, name=name
                    )
                    self.physical_groups[layer][name] = ph_junc_tag

            # Make physical groups for each layer
            if self.layer_types is None:
                raise ValueError(
                    f"Expected `self.layer_types` to be a dict, found {type(self.layer_types)}"
                )
            else:
                if layer in self.layer_types["metal"]:
                    layer_type = "ground_plane"
                elif layer in self.layer_types["dielectric"]:
                    layer_type = "dielectric"
                else:
                    raise ValueError(
                        "Layer number not in the specified `self.layer_types` dict."
                    )

                layer_name = layer_type + f"_(layer {layer})"
                layer_tag = self.layers_dict[layer]
                all_metal_surfs = self.get_all_metal_surfaces()
                if len(layer_tag) > 0:
                    if layer_dim == 3:
                        layer_sfs_tags = []
                        for vol in layer_tag:
                            layer_sfs = list(gmsh.model.occ.getSurfaceLoops(vol)[1][0])

                            if layer_type == "ground_plane":
                                layer_sfs_tags += layer_sfs
                            else:
                                layer_sfs_tags += [
                                    sf for sf in layer_sfs if sf not in all_metal_surfs
                                ]

                        if layer_type != "ground_plane" or (
                            layer_type == "ground_plane" and not ignore_metal_volume
                        ):
                            ph_vol_tag = gmsh.model.addPhysicalGroup(
                                dim=layer_dim, tags=layer_tag, name=layer_name
                            )
                            self.physical_groups[layer][layer_name] = ph_vol_tag

                        ph_sfs_tag = gmsh.model.addPhysicalGroup(
                            dim=2, tags=layer_sfs_tags, name=f"{layer_name}_sfs"
                        )
                        self.physical_groups[layer][f"{layer_name}_sfs"] = ph_sfs_tag
                    else:
                        ph_tag = gmsh.model.addPhysicalGroup(
                            dim=layer_dim, tags=layer_tag, name=layer_name
                        )
                        self.physical_groups[layer][layer_name] = ph_tag

        if draw_sample_holder:
            # Make physical groups for vacuum box (volume)
            vb_name = "vacuum_box"
            ph_vb_tag = gmsh.model.addPhysicalGroup(
                dim=3, tags=[self.vacuum_box], name=vb_name
            )
            self.physical_groups["global"][vb_name] = ph_vb_tag

            # Make physical groups for vacuum box (surfaces)
            vb_sfs = list(gmsh.model.occ.getSurfaceLoops(self.vacuum_box)[1][0])
            ph_vb_sfs_tag = gmsh.model.addPhysicalGroup(
                dim=2, tags=vb_sfs, name=(vb_name + "_sfs")
            )
            self.physical_groups["global"][vb_name + "_sfs"] = ph_vb_sfs_tag

            if self._options.get("outer_face_groups"):
                for side, surfaces in self._outer_faces(vb_sfs).items():
                    name = f"outer_{side}"
                    ph_tag = gmsh.model.addPhysicalGroup(
                        dim=2, tags=surfaces, name=name
                    )
                    self.physical_groups["global"][name] = ph_tag

    def _outer_faces(self, surfaces: list[int]) -> dict[str, list[int]]:
        """Sort the vacuum box's outer surfaces by wall: ``x-`` ... ``z+``."""
        box = gmsh.model.occ.getBoundingBox(3, self.vacuum_box)
        lo, hi = box[:3], box[3:]
        tol = 1e-6 * max(h - l for l, h in zip(lo, hi))
        sides = {}
        for surface in surfaces:
            bb = gmsh.model.occ.getBoundingBox(2, surface)
            for axis, name in enumerate("xyz"):
                if abs(bb[axis + 3] - bb[axis]) > tol:
                    continue  # not flat along this axis
                if abs(bb[axis] - lo[axis]) <= tol:
                    sides.setdefault(f"{name}-", []).append(surface)
                elif abs(bb[axis] - hi[axis]) <= tol:
                    sides.setdefault(f"{name}+", []).append(surface)
        return {side: sides[side] for side in sorted(sides)}

    @property
    def group_map(self) -> "PhysicalGroupMap":
        """The physical groups of the last ``render_design``, with their roles.

        Every group in ``physical_groups`` appears once, as a
        :class:`~qiskit_metal.renderers.renderer_gmsh.groups.PhysicalGroup`
        that says what it is (conductor, ground, dielectric, vacuum,
        junction, outer wall), its component and shape, its net label
        (``<shape>_<component>`` or ``ground_<chip>_plane``, from
        :mod:`qiskit_metal.toolbox_metal.nets`) and its layer's material.
        Built on first use; it needs no running gmsh session.
        """
        if self._group_map is None:
            self._group_map = self._build_group_map()
        return self._group_map

    def _layer_materials(self) -> dict:
        """Layer number -> the layer stack's material name (datatype 0)."""
        ls = self.design.ls.ls_df
        rows = ls[ls["datatype"].astype(int) == 0]
        return {
            int(layer): str(material).strip("'\" ")
            for layer, material in zip(rows["layer"], rows["material"])
        }

    def _layer_chips(self) -> dict:
        """Layer number -> the layer stack's chip name (datatype 0)."""
        ls = self.design.ls.ls_df
        rows = ls[ls["datatype"].astype(int) == 0]
        return {
            int(layer): str(chip).strip("'\" ")
            for layer, chip in zip(rows["layer"], rows["chip_name"])
        }

    def _build_group_map(self) -> "PhysicalGroupMap":
        from qiskit_metal.renderers.renderer_gmsh.groups import (
            PhysicalGroup,
            PhysicalGroupMap,
            Role,
        )
        from qiskit_metal.toolbox_metal.nets import nets_for_design

        metal_layers = list(self.layer_types["metal"])
        netmap = nets_for_design(
            self.design,
            self._render_selection,
            self._render_open_pins,
            metal_layers,
        )
        net_of = {}
        for net in netmap.nets:
            label = netmap.label(net, "q3d")
            for member in net.members:
                net_of[(member.component, member.name)] = label

        materials = self._layer_materials()
        chips = self._layer_chips()
        groups = []
        for layer, entries in self.physical_groups.items():
            if layer == "global":
                for name, tag in entries.items():
                    if name == "vacuum_box":
                        groups.append(
                            PhysicalGroup(name, 3, tag, Role.VACUUM, material="vacuum")
                        )
                    elif name == "vacuum_box_sfs":
                        groups.append(
                            PhysicalGroup(
                                name, 2, tag, Role.OUTER_FACE, surfaces_of="vacuum_box"
                            )
                        )
                    elif name.startswith("outer_"):
                        groups.append(
                            PhysicalGroup(
                                name,
                                2,
                                tag,
                                Role.OUTER_FACE,
                                side=name[len("outer_") :],
                            )
                        )
                continue

            thickness = self.get_thickness_for_layer_datatype(layer_num=layer)
            layer_dim = 3 if np.abs(thickness) > 0 else 2
            is_metal = layer in metal_layers
            material = materials.get(int(layer))
            for name, tag in entries.items():
                surfaces = name.endswith("_sfs")
                base = name[: -len("_sfs")] if surfaces else name
                dim = 2 if surfaces else layer_dim
                surfaces_of = base if surfaces else None
                if base in self.juncs_dict.get(layer, {}):
                    comp, shape = self._shape_sources.get(base, (None, None))
                    group = PhysicalGroup(
                        name, 2, tag, Role.JUNCTION, layer, comp, shape
                    )
                elif base.startswith("ground_plane_(layer "):
                    group = PhysicalGroup(
                        name,
                        dim,
                        tag,
                        Role.GROUND,
                        layer,
                        net=f"ground_{chips.get(int(layer), 'main')}_plane",
                        material=material,
                        surfaces_of=surfaces_of,
                    )
                elif base.startswith("dielectric_(layer "):
                    group = PhysicalGroup(
                        name,
                        dim,
                        tag,
                        Role.DIELECTRIC,
                        layer,
                        material=material,
                        surfaces_of=surfaces_of,
                    )
                else:
                    comp, shape = self._shape_sources.get(base, (None, None))
                    group = PhysicalGroup(
                        name,
                        dim,
                        tag,
                        Role.CONDUCTOR if is_metal else Role.DIELECTRIC,
                        layer,
                        comp,
                        shape,
                        net=net_of.get((comp, shape)) if is_metal else None,
                        material=material,
                        surfaces_of=surfaces_of,
                    )
                groups.append(group)
        return PhysicalGroupMap(groups)

    def isometric_projection(self):
        """Set the view in Gmsh to isometric view manually."""
        gmsh.option.setNumber("General.Trackball", 0)
        gmsh.option.setNumber(
            "General.RotationX", -np.degrees(np.arcsin(np.tan(np.pi / 6)))
        )
        gmsh.option.setNumber("General.RotationY", 0)
        gmsh.option.setNumber("General.RotationZ", -45)

    def _mesh_size(self, key: str):
        """``min_size`` or ``max_size``: from ``mesh_spec`` when it sets one,
        else from the ``mesh`` options."""
        value = getattr(self.mesh_spec, key, None) if self.mesh_spec else None
        if value is None:
            value = self._options["mesh"][key]
        return self.parse_units_gmsh(value)

    def define_mesh_size_fields(self):
        """Define size fields for mesh varying the mesh density across the design."""
        min_mesh_size = self._mesh_size("min_size")
        max_mesh_size = self._mesh_size("max_size")
        min_mesh_size_jj = self.parse_units_gmsh(self._options["mesh"]["max_size_jj"])
        grad_delta = self.parse_units_gmsh(
            self._options["mesh"]["mesh_size_fields"]["gradient_delta"]
        )
        dist_min = self.parse_units_gmsh(
            self._options["mesh"]["mesh_size_fields"]["min_distance_from_edges"]
        )
        dist_max = self.parse_units_gmsh(
            self._options["mesh"]["mesh_size_fields"]["max_distance_from_edges"]
        )
        dist_delta = self.parse_units_gmsh(
            self._options["mesh"]["mesh_size_fields"]["distance_delta"]
        )
        grad_steps = int((dist_max - dist_min) / dist_delta)

        all_vols = []
        all_surfs = []
        all_dicts = (self.polys_dict, self.paths_dict)

        for d in all_dicts:
            for layer, geoms in d.items():
                thickness = self.get_thickness_for_layer_datatype(layer)
                if np.abs(thickness) > 0:
                    all_vols += [tag[0] for tag in geoms.values()]
                else:
                    all_surfs += [tag[0] for tag in geoms.values()]

        # Metal layers
        for layer in self.layer_types["metal"]:
            thickness = self.get_thickness_for_layer_datatype(layer)
            if np.abs(thickness) > 0:
                all_vols += self.layers_dict[layer]
            else:
                all_surfs += self.layers_dict[layer]

        for vol in all_vols:
            all_surfs += [surf for surf in gmsh.model.occ.getSurfaceLoops(vol)[1][0]]

        curve_loops = [gmsh.model.occ.getCurveLoops(surf) for surf in all_surfs]
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
                tf, "DistMax", dist_max - ((grad_steps - i - 1) * dist_delta)
            )
            gmsh.model.mesh.field.setNumber(tf, "Sigmoid", 1)
            gmsh.model.mesh.field.setNumber(tf, "InField", df)
            gmsh.model.mesh.field.setNumber(
                tf, "SizeMin", (i * grad_delta) + min_mesh_size
            )
            gmsh.model.mesh.field.setNumber(tf, "SizeMax", max_mesh_size)

            thresh_fields += [tf]

        jj_surfs = []
        for _, geoms in self.juncs_dict.items():
            jj_surfs += [tag[0] for tag in geoms.values()]

        jj_curve_loops = [gmsh.model.occ.getCurveLoops(surf) for surf in jj_surfs]
        jj_curves = []
        for cl in jj_curve_loops:
            for curve_tag_list in cl[1]:  # extract curves
                for curve in curve_tag_list:
                    jj_curves += [curve]

        jj_df = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(jj_df, "CurvesList", jj_curves)
        gmsh.model.mesh.field.setNumber(jj_df, "NumPointsPerCurve", 100)

        jj_tf = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(jj_tf, "DistMin", dist_min)
        gmsh.model.mesh.field.setNumber(jj_tf, "DistMax", dist_max)
        gmsh.model.mesh.field.setNumber(jj_tf, "Sigmoid", 1)
        gmsh.model.mesh.field.setNumber(jj_tf, "InField", jj_df)
        gmsh.model.mesh.field.setNumber(jj_tf, "SizeMin", min_mesh_size_jj)
        gmsh.model.mesh.field.setNumber(jj_tf, "SizeMax", max_mesh_size)
        thresh_fields += [jj_tf]
        thresh_fields += self._refinement_fields(max_mesh_size)

        min_field = gmsh.model.mesh.field.add("Min")
        gmsh.model.mesh.field.setNumbers(min_field, "FieldsList", thresh_fields)

        gmsh.model.mesh.field.setAsBackgroundMesh(min_field)

        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)

    def _refine_surfaces(self, select) -> list[int]:
        """The surfaces a ``Select`` picks, through ``group_map``."""
        from qiskit_metal.renderers.renderer_gmsh.groups import Role

        if select.port is not None:
            raise ValueError(
                f"Mesh refinement on port {select.port!r}: ports are not rendered "
                "as physical groups yet."
            )
        attrs = {}
        if select.role is not None:
            attrs["role"] = Role(select.role)
        if select.net is not None:
            attrs["net"] = select.net
        if select.component is not None:
            attrs["component"] = select.component
        if select.junction is not None:
            attrs.update(
                role=Role.JUNCTION,
                component=select.junction.component,
                qgeometry=select.junction.name,
            )
        groups = [g for g in self.group_map.select(**attrs) if g.dim == 2]
        if not groups:
            raise ValueError(f"Mesh refinement {select}: no surfaces match.")
        return sorted(
            {
                int(s)
                for g in groups
                for s in gmsh.model.getEntitiesForPhysicalGroup(2, g.tag)
            }
        )

    def _refinement_fields(self, max_mesh_size: float) -> list[int]:
        """Size fields for ``mesh_spec.refine``; the caller takes their minimum
        with the default fields."""
        if not self.mesh_spec or not self.mesh_spec.refine:
            return []
        field = gmsh.model.mesh.field
        fields = []
        for refine in self.mesh_spec.refine:
            size = self.parse_units_gmsh(refine.size)
            grow = self.parse_units_gmsh(refine.grow)
            if refine.select.box is not None:
                x0, y0, x1, y1 = self.parse_units_gmsh(list(refine.select.box))
                zlo, zhi = self._model_z_range()
                f = field.add("Box")
                for key, value in (
                    ("XMin", min(x0, x1)),
                    ("XMax", max(x0, x1)),
                    ("YMin", min(y0, y1)),
                    ("YMax", max(y0, y1)),
                    ("ZMin", zlo),
                    ("ZMax", zhi),
                    ("VIn", size),
                    ("VOut", max_mesh_size),
                    ("Thickness", grow),
                ):
                    field.setNumber(f, key, value)
                fields.append(f)
                continue
            surfaces = self._refine_surfaces(refine.select)
            if refine.shape == "ball":
                boxes = [gmsh.model.occ.getBoundingBox(2, s) for s in surfaces]
                lo = [min(b[i] for b in boxes) for i in range(3)]
                hi = [max(b[i + 3] for b in boxes) for i in range(3)]
                f = field.add("Ball")
                for key, value in (
                    ("XCenter", (lo[0] + hi[0]) / 2),
                    ("YCenter", (lo[1] + hi[1]) / 2),
                    ("ZCenter", (lo[2] + hi[2]) / 2),
                    ("Radius", grow),
                    ("VIn", size),
                    ("VOut", max_mesh_size),
                ):
                    field.setNumber(f, key, value)
                fields.append(f)
                continue
            curves = sorted(
                {
                    int(c)
                    for s in surfaces
                    for loop in gmsh.model.occ.getCurveLoops(s)[1]
                    for c in loop
                }
            )
            distance = field.add("Distance")
            field.setNumbers(distance, "CurvesList", curves)
            field.setNumber(distance, "NumPointsPerCurve", 100)
            f = field.add("Threshold")
            field.setNumber(f, "InField", distance)
            field.setNumber(f, "SizeMin", size)
            field.setNumber(f, "SizeMax", max_mesh_size)
            field.setNumber(f, "DistMin", 0.0)
            field.setNumber(f, "DistMax", grow)
            fields.append(f)
        return fields

    def _model_z_range(self) -> tuple[float, float]:
        """The z extent of the model: the vacuum box if drawn, else all volumes."""
        if getattr(self, "vacuum_box", None) is not None:
            bb = gmsh.model.occ.getBoundingBox(3, self.vacuum_box)
        else:
            bb = gmsh.model.getBoundingBox(-1, -1)
        return bb[2], bb[5]

    def define_mesh_properties(self):
        """Define properties for mesh depending on renderer options."""
        min_mesh_size = self._mesh_size("min_size")
        max_mesh_size = self._mesh_size("max_size")
        if self.mesh_spec and self.mesh_spec.refine:
            # Mesh.MeshSizeMin clamps every size field: let a refinement go
            # below the global lower bound it asks for.
            min_mesh_size = min(
                [min_mesh_size]
                + [self.parse_units_gmsh(r.size) for r in self.mesh_spec.refine]
            )
        gmsh.option.setNumber(
            "Mesh.MeshSizeFromCurvature", self._options["mesh"]["nodes_per_2pi_curve"]
        )
        gmsh.option.setNumber("Mesh.Smoothing", self._options["mesh"]["smoothing"])
        gmsh.option.setNumber("Mesh.Algorithm3D", self._options["mesh"]["algorithm_3d"])
        gmsh.option.setNumber(
            "General.NumThreads", self._options["mesh"]["num_threads"]
        )
        gmsh.option.setNumber("Mesh.MeshSizeMin", min_mesh_size)
        gmsh.option.setNumber("Mesh.MeshSizeMax", max_mesh_size)

    def add_mesh(
        self, dim: int = 3, intelli_mesh: bool = True, custom_mesh_fn: callable = None
    ):
        """Generate mesh for all geometries.

        Args:
            dim (int, optional): Specify the dimension of mesh. Defaults to 3.
            intelli_mesh (bool): Set to mesh the geometries intelligently. True by default.
            custom_mesh_fn (callable): Custom meshing function specifying mesh size fields
                                        using Gmsh python script (for advanced users only)
        """
        if intelli_mesh:
            if custom_mesh_fn is None:
                self.define_mesh_size_fields()
            else:
                self.logger.info("Applying custom meshing function...")
                custom_mesh_fn()

        self.define_mesh_properties()
        gmsh.model.mesh.generate(dim=dim)
        self.assign_mesh_color()

    def assign_mesh_color(self):
        """Assign mesh color according to the type of layer specified by
        self.layer_types and colors taken from self._options as provided by the user.
        """
        color_dict = lambda color: dict(r=color[0], g=color[1], b=color[2], a=color[3])
        metal_color = color_dict(self._options["colors"]["metal"])
        jj_color = color_dict(self._options["colors"]["jj"])
        dielectric_color = color_dict(self._options["colors"]["dielectric"])
        valid_layers = set(list(self.paths_dict.keys()) + list(self.polys_dict.keys()))

        # Assign mesh color to dielectric layer
        for layer in list(self.layers_dict.keys()):
            if layer not in self.layer_types["dielectric"]:
                continue

            thickness = self.get_thickness_for_layer_datatype(layer)

            layer_tags = self.layers_dict[layer]
            layer_dim = 3 if np.abs(thickness) > 0 else 2
            if layer_dim == 3:
                layer_sfs = []
                for vol in layer_tags:
                    layer_sfs += list(gmsh.model.occ.getSurfaceLoops(vol)[1][0])
                gmsh.model.setColor(
                    [(3, tag) for tag in layer_tags], **dielectric_color
                )
            else:
                layer_sfs = layer_tags

            gmsh.model.setColor([(2, sf) for sf in layer_sfs], **dielectric_color)

        # Assign colors to geometries and metal (ground plane) layers
        for layer in list(self.layers_dict.keys()):
            if layer in self.layer_types["dielectric"]:
                continue

            thickness = self.get_thickness_for_layer_datatype(layer)

            if layer in valid_layers:
                metal_vols = []
                metal_surfs = []
                metal_dicts = (self.polys_dict[layer], self.paths_dict[layer])

                # Component geomtries
                for d in metal_dicts:
                    for _, geoms in d.items():
                        if np.abs(thickness) > 0:
                            metal_vols += geoms
                        else:
                            metal_surfs += geoms

                # Metal layers
                if np.abs(thickness) > 0:
                    metal_vols += self.layers_dict[layer]
                else:
                    metal_surfs += self.layers_dict[layer]

                for vol in metal_vols:
                    metal_surfs += [
                        surf for surf in gmsh.model.occ.getSurfaceLoops(vol)[1][0]
                    ]

                if len(metal_vols) > 0:
                    gmsh.model.setColor(
                        [(3, metal) for metal in metal_vols], **metal_color
                    )
                gmsh.model.setColor(
                    [(2, metal) for metal in metal_surfs], **metal_color
                )

                # Junctions
                jj_surfs = []
                for _, surf in self.juncs_dict[layer].items():
                    jj_surfs += surf

                gmsh.model.setColor([(2, jj) for jj in jj_surfs], **jj_color)

    def launch_gui(self):
        """Launch Gmsh GUI for viewing the model."""
        self.isometric_projection()  # set isometric projection
        try:
            gmsh.fltk.run()
        except Exception:
            self.logger.info(
                "Encountered an error while launching the Gmsh GUI. Retrying to launch the GUI..."
            )
            gmsh.fltk.run()

    def export_mesh(self, filepath: str, scaling_factor: float = 1e-3):
        """Export mesh from Gmsh into a file.
        Supported formats: (.msh, .msh2, .mesh).

        Args:
            filepath (str): path of the file to export mesh to.
            scaling_factor (float): specify a scaling factor for the mesh. Defaults to 1e-3.
        """
        valid_file_exts = ["msh", "msh2", "mesh"]
        file_ext = filepath.split(".")[-1]
        if file_ext not in valid_file_exts:
            self.logger.error(
                "RENDERER ERROR: filename needs to have a .msh extension. Exporting failed."
            )
            return

        import os
        from pathlib import Path

        par_dir = Path(filepath).parent.absolute()
        if not os.path.exists(par_dir):
            raise ValueError(f"Directory not found: {par_dir}")

        gmsh.option.setNumber("Mesh.ScalingFactor", scaling_factor)
        gmsh.write(filepath)

    def export_geo_unrolled(self, filepath: str):
        """Export the Gmsh geometry as geo_unrolled file.
        Supported formats: .geo_unrolled

        Args:
            filepath (str): path of the file to export geometry to
        """
        valid_file_exts = ["geo_unrolled"]
        file_ext = filepath.split(".")[-1]
        if file_ext not in valid_file_exts:
            self.logger.error(
                "RENDERER ERROR: filename needs to have a .geo_unrolled extension. Exporting failed."
            )
            return

        import os
        from pathlib import Path

        par_dir = Path(filepath).parent.absolute()
        if not os.path.exists(par_dir):
            raise ValueError(f"Directory not found: {par_dir}")

        has_mesh = False if len(gmsh.model.mesh.field.list()) == 0 else True
        if has_mesh:
            self.logger.warning(
                "WARNING: The existing model contains mesh size field definitions, "
                "which will show up in your exported .geo_unrolled file. If "
                "you aren't explicitly handling the mesh size fields, we recommend "
                "to export the geometry before generating the mesh in your design as "
                "it might interfere with your .geo_unrolled file imports."
            )

        gmsh.write(filepath)

        # Prepend "SetFactory("OpenCASCADE");" in the exported file
        line = 'SetFactory("OpenCASCADE");'
        with open(filepath, "r+") as f:
            content = f.read()
            f.seek(0, 0)
            f.write(line.rstrip("\r\n") + "\n" + content)

    def import_post_processing_data(
        self,
        filename: str,
        launch_gui: bool = True,
        close_gmsh_on_closing_gui: bool = False,
    ):
        """Import the post processing data for visualization in Gmsh.

        Args:
            filename (str): a target file ending with '.msh' extension
            launch_gui (bool): launch the Gmsh GUI. Defaults to True.
            close_gmsh_on_closing_gui (bool): finalize gmsh when the GUI
                                                is closed. Defaults to True.

        Raises:
            ValueError: raises when the input file isn't a .msh file
        """
        if ".msh" not in filename:
            raise ValueError("Only .msh files supported for post processing views.")

        self.model = "post_processing"

        gmsh.open(filename)
        if launch_gui:
            self.launch_gui()

        if close_gmsh_on_closing_gui:
            self.close()

    def save_screenshot(self, path: str = None, show: bool = True):
        """Save the screenshot.

        Args:
            path (str, optional): Path to save location.  Defaults to None.
            show (bool, optional): Whether or not to display the screenshot. Defaults to True.
        """
        valid_file_exts = ["jpg", "png", "gif", "bmp"]
        file_ext = path.split(".")[-1]
        if file_ext not in valid_file_exts:
            self.logger.error(
                f"Expected png, jpg, bmp, or gif format, got .{path.split('.')[-1]}."
            )

        # FIXME: This doesn't work right now!!! Active issue: #843
        # There is no method in Gmsh python wrapper to give
        # the 'Print' command which can provide screenshot feature.
        raise NotImplementedError("""This feature is pending and depends on Gmsh
                                    general command 'Print' being available through the API.""")

    def render_component(self, component):
        pass
