from typing import Union, List, Tuple
from collections import defaultdict
import pandas as pd

from ..renderer_base import QRendererAnalysis
from ..renderer_gmsh.gmsh_renderer import QGmshRenderer
from ...designs.design_base import QDesign
from ... import Dict
from .elmer_runner import ElmerRunner


class QElmerRenderer(QRendererAnalysis):
    """Extends QRendererAnalysis class and imports meshes from Gmsh using the ElmerFEM python API.

    QGmshRenderer Default Options:
        * x_buffer_width_mm -- Buffer between max/min x and edge of ground plane, in mm
        * y_buffer_width_mm -- Buffer between max/min y and edge of ground plane, in mm
        * mesh -- to define meshing parameters
            * max_size -- upper bound for the size of mesh node
            * min_size -- lower bound for the size of mesh node
            * smoothing -- mesh smoothing value
            * nodes_per_2pi_curve -- number of nodes for every 2π radians of curvature
            * algorithm_3d -- value to indicate meshing algorithm used by Gmsh
            * num_threads -- number of threads for parallel meshing
            * export_dir -- path to mesh export directory
        * colors -- specify colors for the mesh elements, chips or layers
            * metal -- color for metallized entities
            * jj -- color for JJs
            * sub -- color for substrate entity

    TODO: update QElmerRenderer options docstring
    """

    default_options = Dict(
        simulation_type="steady_3D",
        simulation_dir="./simdata",
        mesh_file="out.msh",
        simulation_input_file="case.sif",
        postprocessing_file="case.msh",
        output_file="case.result",
    )

    default_setup = Dict(
        capacitance=Dict(
            Calculate_Electric_Field=True,
            Calculate_Electric_Energy=True,
            Calculate_Capacitance_Matrix=True,
            Capacitance_Matrix_Filename="cap_matrix.txt",
            Linear_System_Solver="Iterative",
            Steady_State_Convergence_Tolerance=1.0e-5,
            Nonlinear_System_Convergence_Tolerance=1.0e-7,
            Nonlinear_System_Max_Iterations=20,
            Linear_System_Convergence_Tolerance=1.0e-10,
            Linear_System_Max_Iterations=500,
            Linear_System_Iterative_Method="BiCGStab",
            BiCGstabl_Polynomial_Degree=2,
        ),

        # TODO: Update this later when working on eigenmode setup
        eigenmode=Dict(),
        materials=["vacuum", "silicon"],
        constants=Dict(
            Permittivity_of_Vacuum=8.8542e-12,
            Unit_Charge=1.602e-19,
        ),
    )

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
        return self.gmsh.initialized

    def _initiate_renderer(self):
        self.gmsh = QGmshRenderer(self.design)
        self._elmer_runner = ElmerRunner()

    def _close_renderer(self):
        self.gmsh.close()

    def close(self):
        self.gmsh.close()

    def render_design(
        self,
        selection: Union[list, None] = None,
        open_pins: Union[list, None] = None,
        box_plus_buffer: bool = True,
        mesh_geoms: bool = True,
        skip_junctions: bool = False,
    ):
        self.gmsh.render_design(selection=selection,
                                open_pins=open_pins,
                                box_plus_buffer=box_plus_buffer,
                                mesh_geoms=mesh_geoms,
                                skip_junctions=skip_junctions)

        self.nets = self.assign_nets(open_pins=open_pins)

    def assign_nets(self, open_pins: Union[list, None] = None):
        if self.gmsh.case == 0:
            qcomp_ids = self.gmsh.qcomp_ids
        elif self.gmsh.case == 1:
            qcomp_ids = list(set(self.design._components.keys()))
        elif self.gmsh.case == 2:
            raise ValueError("Selection provided is invalid.")

        def create_mask(table: pd.Series, qcomp_ids: list):
            mask = 0
            for qid in qcomp_ids:
                mask |= (table["component"] == qid)
            mask &= ~table["subtract"]
            return mask

        netlists = defaultdict(list)
        netlist_id = 0
        path_table = self.design.qgeometry.tables["path"]
        poly_table = self.design.qgeometry.tables["poly"]
        qcomp_paths = path_table[create_mask(table=path_table,
                                             qcomp_ids=qcomp_ids)]
        qcomp_polys = poly_table[create_mask(table=poly_table,
                                             qcomp_ids=qcomp_ids)]
        qcomp_geom_table = pd.concat([qcomp_paths, qcomp_polys],
                                     ignore_index=True)
        qgeom_names = qcomp_geom_table["name"]
        qcomp_names_for_qgeom = [
            list(self.design.components.keys())[i - 1]
            for i in qcomp_geom_table["component"]
        ]
        phys_grps = [
            s1 + '_' + s2 for s1, s2 in zip(qcomp_names_for_qgeom, qgeom_names)
        ]
        qgeom_idxs = [i for i in range(len(qcomp_geom_table))]
        id_net_dict = {k: -1 for k in phys_grps}

        while len(qgeom_idxs) != 0:
            i = qgeom_idxs.pop(0)
            shape_i = qcomp_geom_table.iloc[[i]]["geometry"][i]
            chip_i = qcomp_geom_table.iloc[[i]]["chip"][i]
            id_net_dict[phys_grps[i]] = netlist_id if (
                id_net_dict[phys_grps[i]] == -1) else id_net_dict[phys_grps[i]]
            for j in qgeom_idxs:
                shape_j = qcomp_geom_table.iloc[[j]]["geometry"][j]
                chip_j = qcomp_geom_table.iloc[[j]]["chip"][j]
                dist = shape_i.distance(shape_j)

                # TODO: change this to be compatible with layer-stack
                if dist == 0.0 and chip_i == chip_j:
                    if id_net_dict[phys_grps[j]] == -1:
                        id_net_dict[phys_grps[j]] = id_net_dict[phys_grps[i]]
                    else:
                        id_net_dict[phys_grps[i]] = id_net_dict[phys_grps[j]]

            if -1 not in id_net_dict.values():
                break

            netlist_id = max(list(id_net_dict.values())) + 1

        # TODO: include the ground_plane_{chip} in netlist
        # using open_pins argument
        # 1. For loop: filter by chips
        # 2. Compare with design.net_info and get left out pins
        # 3. Add ground plane to left out pins lists and merge
        #    the lists in which ground plane was added

        for k, v in id_net_dict.items():
            if v not in netlists.keys():
                netlists[v] = list()
            netlists[v].append(k)

        return netlists

    def run(self, sim_type: str, display_cap_matrix: bool = True):
        setup = self.default_setup[sim_type]
        sim_dir = self._options["simulation_dir"]
        meshfile = self._options["mesh_file"]
        sif_name = self._options["simulation_input_file"]
        postprocessing_file = self._options["postprocessing_file"]
        if sim_type == "capacitance":
            cap_matrix_file = setup["Capacitance_Matrix_Filename"]

        self.logger.info("Running ElmerGrid on input mesh from Gmsh...")
        self._elmer_runner.run_elmergrid(sim_dir, meshfile)
        self.logger.info(f"Running ElmerSolver for solver type: '{sim_type}'")
        self._elmer_runner.run_elmersolver(
            sim_dir, sif_name, [cap_matrix_file, postprocessing_file])

        if display_cap_matrix:
            self.capacitance_matrix = self.get_capacitance_matrix(
                cap_matrix_file)
            return self.capacitance_matrix

    def add_solution_setup(
        self,
        sim_name: str = "capacitance",
        solver_names: List[str] = ["capacitance", "postprocessing_gmsh"],
        equation_name: str = "poisson",
    ):
        setup = self.default_setup
        cap_setup = {
            k.replace('_', ' '): v
            for k, v in self.default_setup[sim_name].items()
        }

        # Load simulation
        self._elmer_runner.load_simulation(self._options["simulation_type"])

        # Load constants
        constants = self.default_setup["constants"]
        for k in constants.keys():
            const_str = k.replace('_', ' ')
            self._elmer_runner.add_constant(const_str, 1)

        # Load solvers
        solvers = self._elmer_runner.load_solvers(solver_names=solver_names)
        self._elmer_runner.solver["capacitance"].update(cap_setup)

        # Load materials
        materials = self._elmer_runner.load_materials(setup["materials"])

        # Add equation
        eqn = self._elmer_runner.add_equation(equation_name, solvers=solvers)

        # Add bodies
        bodies = self.define_bodies(setup, eqn, materials)

        # Add boundary conditions
        boundaries, cap_body = self.define_boundaries()

        # Update capacitance bodies in solver
        self._elmer_runner.solver["capacitance"].update(
            {"Capacitance Bodies": cap_body - 1})

        # Write the simulation input file (SIF)
        self.write_sif()

    def define_bodies(self, setup: dict, equation: int, materials: List[int]):
        bodies = []
        for i, material in enumerate(setup["materials"]):
            if material == "vacuum":
                bodies += [
                    self._elmer_runner.add_body(
                        "vacuum_box",
                        [self.gmsh.physical_groups["global"]["vacuum_box"]],
                        equation, materials[i])
                ]
            if material == "silicon":
                substrate_geoms = dict()
                for chip, ph_geoms in self.gmsh.physical_groups.items():
                    if chip in ["global", "chips"]:
                        continue

                    sub = {
                        k: v for k, v in ph_geoms.items() if "substrate" in k
                    }
                    substrate_geoms.update(sub)

                bodies += [
                    self._elmer_runner.add_body(name, [body], equation,
                                                materials[i])
                    for name, body in substrate_geoms.items()
                ]

        return bodies

    def define_boundaries(self):
        boundaries = list()
        phys_grps_dict = dict()
        ground_planes = list()
        cap_body = 1
        for chip, ph_geoms in self.gmsh.physical_groups.items():
            if chip in ["global", "chips"]:
                continue

            for name, geom in ph_geoms.items():
                if "ground_plane" in name:
                    ground_planes.append(geom)

                if "substrate" in name:
                    continue

            phys_grps_dict.update(ph_geoms)

        for _, geom_names in self.nets.items():
            geom_id_list = [phys_grps_dict[name] for name in geom_names]

            boundaries += [
                self._elmer_runner.add_boundary_condition(
                    geom_names[-1],
                    geom_id_list,
                    options={"Capacitance Body": cap_body})
            ]
            cap_body += 1

        self._elmer_runner.add_boundary_condition(
            "ground_plane", ground_planes, options={"Capacitance Body": 0})

        self._elmer_runner.add_boundary_condition(
            "FarField", [self.gmsh.physical_groups["global"]["vacuum_box_sfs"]],
            options={"Electric Infinity BC": True})

        return boundaries, cap_body

    def write_sif(self):
        filename = self._options["simulation_input_file"]
        sim_dir = self._options["simulation_dir"]
        self._elmer_runner.write_startinfo_and_sif(filename=filename,
                                                   sim_dir=sim_dir)

    def get_capacitance_matrix(self, filename: str):
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            f.close()

        new_lines = [(l.replace("  ", " ").strip() + '\n') for l in lines]

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            f.close()

        df = pd.read_csv(filename, delimiter=" ", header=None)

        # Convert from SPICE cap matrix to Maxwell cap matrix
        df2 = df.multiply(-1e15)
        row_sum = df2.sum(axis=0)
        for i, s in enumerate(row_sum):
            df2[i][i] = -s

        name_cap = {k: v[-1] for k, v in self.nets.items()}
        df2.rename(index=name_cap, columns=name_cap, inplace=True)

        gnd_caps = -1 * df2.sum(axis=0)
        df2.loc["ground_plane"] = gnd_caps
        df2["ground_plane"] = gnd_caps
        df2 = df2.multiply(
            self.default_setup["constants"]["Permittivity_of_Vacuum"])

        # dummy value set to high as it's shorted to ground
        df2["ground_plane"]["ground_plane"] = 300
        return df2

    def render_chips(self,
                     chips: Union[str, List[str]] = [],
                     draw_sample_holder: bool = True,
                     box_plus_buffer: bool = True):
        """Abstract method. Must be implemented by the subclass.
        Render all chips of the design.
        Calls render_chip for each chip.
        """
        self.gmsh.render_chips(chips, draw_sample_holder, box_plus_buffer)

    def render_chip(self, chip_name: str):
        """Abstract method. Must be implemented by the subclass.
        Render the given chip.

        Args:
            name (str): chip to render
        """
        self.gmsh.render_chip(chip_name)

    def render_components(self, table_type: str):
        """Abstract method. Must be implemented by the subclass.
        Render all components of the design.
        If selection is none, then render all components.

        Args:
            selection (QComponent): Component to render.
        """
        self.gmsh.render_components(table_type)

    def render_component(self, component):
        """Abstract method. Must be implemented by the subclass.
        Render the specified component.

        Args:
            component (QComponent): Component to render.
        """
        self.gmsh.render_component(component)

    def render_element(self, qgeom: pd.Series, table_type: str):
        """Abstract method. Must be implemented by the subclass.
        Render the specified element

        Args:
            element (Element): Element to render.
        """
        self.gmsh.render_element(qgeom, table_type)

    def render_element_path(self, path: pd.Series):
        """Abstract method. Must be implemented by the subclass.
        Render an element path.

        Args:
            path (str): Path to render.
        """
        self.gmsh.render_element_path(path)

    def render_element_junction(self, junc: pd.Series):
        """Abstract method. Must be implemented by the subclass.
        Render an element junction.

        Args:
            junc (str): Junction to render.
        """
        self.gmsh.render_element_junction(junc)

    def render_element_poly(self, poly: pd.Series):
        """Abstract method. Must be implemented by the subclass.
        Render an element poly.

        Args:
            poly (Poly): Poly to render.
        """
        self.gmsh.render_element_poly(poly)

    def save_screenshot(self, path: str = None, show: bool = True):
        """Save the screenshot.

        Args:
            path (str, optional): Path to save location.  Defaults to None.
            show (bool, optional): Whether or not to display the screenshot.  Defaults to True.

        Returns:
            pathlib.WindowsPath: path to png formatted screenshot.
        """
        self.gmsh.save_screenshot(path, show)

    def launch_gmsh_gui(self):
        """Launch Gmsh GUI for viewing the model.
        """
        self.gmsh.launch_gui()

    def export_mesh(self):
        """Export Gmsh mesh
        """
        self.gmsh.export_mesh(self._options["mesh_file"])

    def display_post_processing_data(self):
        """Import data given by ElmerFEM for Post-Processing in Gmsh
        """
        self.gmsh.import_post_processing_data(
            self._options["postprocessing_file"])
