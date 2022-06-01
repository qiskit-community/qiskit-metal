import pandas as pd
from typing import *
from collections import defaultdict
import gmsh
from sympy import Chi

from ..renderer_base import QRendererAnalysis
from .gmsh_utils import *
from ...draw.basic import is_rectangle

class QGmshRenderer(QRendererAnalysis):
    """Abstract base class for all Renderers intended for Analysis.
    """

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
        box_plus_buffer: bool = True
        ):

        self.qcomp_ids, self.case = self.get_unique_component_ids(selection)

        if self.case == 2:
            self.logger.warning(
                "Unable to proceed with rendering. Please check selection.")
            return

        self.chip_subtract_dict = defaultdict(set)
        self.polys_dict = defaultdict(set)
        self.paths_dict = defaultdict(set)
        self.juncs_dict = defaultdict(set)
        
        # TODO: sequence of events to perform
        self.render_tables()
        # self.add_endcaps(open_pins)

        # self.render_chips(box_plus_buffer=box_plus_buffer)
        # self.subtract_from_ground()
        # self.add_mesh()

    def render_tables(self):
        """
        Render components in design grouped by table type (path, poly, or junction).
        """
        for table_type in self.design.qgeometry.get_element_types():
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
        vecs = Vec2DArray.make_vec2DArray(self.parse_units_gmsh(list(qc_shapely.coords)))

        # Considering JJ will always be a rectangle
        # TODO: do we need functionality for arbitrary shape JJ?
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
        vecs = Vec2DArray.make_vec2DArray(self.parse_units_gmsh(list(qc_shapely.coords)))
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

    def make_poly_surface(self, points: list[Vec2D], chip_z: float) -> int:
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
        vecs = Vec2DArray.make_vec2DArray(self.parse_units_gmsh(list(qc_shapely.exterior.coords)))

        if is_rectangle(qc_shapely):
            x_min, y_min, x_max, y_max = qc_shapely.bounds
            dx, dy = np.abs(x_max - x_min), np.abs(y_max - y_min)
            surface = gmsh.model.occ.addRectangle(x_min, y_min, qc_chip_z, dx, dy)
        else:
            surface = self.make_poly_surface(vecs.points, qc_chip_z)

        if len(qc_shapely.interiors) > 0:
            int_vecs = Vec2DArray.make_vec2DArray(
                [self.parse_units_gmsh(list(coord)) for coord in qc_shapely.interiors])
            int_surface = self.make_poly_surface(int_vecs.points, qc_chip_z)
            surface = gmsh.model.occ.cut([surface], [int_surface])


        if poly.chip not in self.chip_subtract_dict:
            self.chip_subtract_dict[poly.chip] = set()

        if poly.chip not in self.polys_dict:
            self.polys_dict[poly.chip] = set()

        if poly["subtract"]:
            self.chip_subtract_dict[poly.chip].add(surface)
        else:
            self.polys_dict[poly.chip].add(surface)

    def render_chips(self):
        """Abstract method. Must be implemented by the subclass.
        Render all chips of the design.
        Calls render_chip for each chip.
        """
        pass

    def render_chip(self, name):
        """Abstract method. Must be implemented by the subclass.
        Render the given chip.

        Args:
            name (str): chip to render
        """
        pass

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