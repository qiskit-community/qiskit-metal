from typing import Union, Optional
import os
import pandas as pd

from qiskit_metal import Dict, draw
from qiskit_metal.renderers.renderer_base import QRendererAnalysis
from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer
from qiskit_metal.renderers.renderer_elmer.elmer_runner import ElmerRunner


def load_capacitance_matrix_from_file(filename: str) -> pd.DataFrame:
    """Loads capacitance matrix from file.

    Args:
        filename (str): A '.txt' file containing the capacitance matrix.

    Returns:
        pd.DataFrame:: Table containing capacitance matrix.
    """
    return pd.read_csv(filename, delimiter=' ', index_col=0)


class QElmerRenderer(QRendererAnalysis):
    """Extends QRendererAnalysis class and imports meshes from Gmsh using the ElmerFEM python API.

    QElmerRenderer Default Options:
        * simulation_type -- Type of ElmerFEM simulation to run.
                                Default options found in elmer_configs.py under "simulations".
        * simulation_dir -- Directory to store simulation-related files.
        * mesh_file -- Name of GMSH output mesh file ending in '.msh'.
        * simulation_input_file -- Name of ElmerFEM simulation input file ending in '.sif'.
        * postprocessing_file -- Name of ElmerFEM postprocessing output file ending in '.msh'.
        * output_file -- Name of ElmerFEM results output file ending in '.result'.

    QElmerRenderer Default Setup:
        * capacitance -- Default setup for capacitance simulation:
            * Calculate_Electric_Field -- Defaults to True.
            * Calculate_Electric_Energy -- Defaults to True.
            * Calculate_Capacitance_Matrix -- Defaults to True.
            * Capacitance_Matrix_Filename -- Defaults to "cap_matrix.txt".
            * Linear_System_Solver -- Defaults to "Iterative".
            * Steady_State_Convergence_Tolerance -- Defaults to 1.0e-5.
            * Nonlinear_System_Convergence_Tolerance -- Defaults to 1.0e-7.
            * Nonlinear_System_Max_Iterations -- Defaults to 20.
            * Linear_System_Convergence_Tolerance -- Defaults to 1.0e-10.
            * Linear_System_Max_Iterations -- Defaults to 500.
            * Linear_System_Iterative_Method -- Defaults to "BiCGStab".
            * BiCGstabl_polynomial_degree -- Defaults to 2.

        * eigenmode -- Default setup for Eigenmode simulation (to be added in future).

        * materials -- Materials used in the simulation. Defaults to `["vacuum", "silicon"]`.

        * constants -- Default constants to be included in the simulation:
            * Permittivity_of_Vacuum -- Defaults to 8.8542e-12 F/m.
            * Unit_Charge -- Defaults to 1.602e-19 C.

    QGmshRenderer Default Options:
        # Buffer between max/min x and edge of ground plane, in mm
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
            BiCGstabl_polynomial_degree=2,
        ),

        # TODO: Update this later when working on eigenmode setup
        eigenmode=Dict(),
        materials=["vacuum", "silicon"],
        constants=Dict(
            Permittivity_of_Vacuum=8.8542e-12,
            Unit_Charge=1.602e-19,
        ),
    )

    name = "elmer"
    """Name"""

    def __init__(self,
                 design: 'MultiPlanar',
                 layer_types: Union[dict, None] = None,
                 initiate=True,
                 options: Dict = None):
        """
        Args:
            design ('MultiPlanar'): The design.
            layer_types (Union[dict, None]): the type of layer in the format:
                                                dict(metal=[...], dielectric=[...]).
                                                Defaults to None.
            initiate (bool): True to initiate the renderer (Default: False).
            settings (Dict, optional): Used to override default settings. Defaults to None.
        """
        default_layer_types = dict(metal=[1], dielectric=[3])
        self.layer_types = default_layer_types if layer_types is None else layer_types

        super().__init__(design=design, initiate=initiate, options=options)

    @property
    def initialized(self):
        """Abstract method. Must be implemented by the subclass.
            Is renderer ready to be used?
            Implementation must return boolean True if successful. False otherwise.
        """
        return (hasattr(self, "_elmer_runner") and self.gmsh.initialized)

    def initialize_renderer(self):
        """Initializes the Gmsh and Elmer renderer.
        NOTE TO USER: this should be used when using
        the QElmerRenderer through design.renderers.elmer instance.
        
        Example: To change one of the options exposed by QGmshRenderer,
        one has to first initiate the QElmerRenderer using this method
        and then change the property like so,

        ```
        design.renderers.elmer.initialize_renderer()
        design.renderers.elmer.gmsh.options.mesh.num_threads = 1
        ...
        ```
        """
        self.gmsh = QGmshRenderer(self.design, self.layer_types)
        self._elmer_runner = ElmerRunner()

    def _initiate_renderer(self):
        """Initializes the Gmsh and Elmer renderer.
        NOTE: This is automatically called when the USER
        specifically imports QElmerRenderer in a jupyter notebook
        and instantiates it."""
        self.gmsh = QGmshRenderer(self.design, self.layer_types)
        self._elmer_runner = ElmerRunner()
        return True

    def _close_renderer(self):
        """Finalizes the Gmsh renderer"""
        self.gmsh.close()

    def close(self):
        """Public method to close the Gmsh renderer"""
        return self._close_renderer()

    def render_design(
        self,
        selection: Union[list, None] = None,
        open_pins: Union[list, None] = None,
        box_plus_buffer: bool = True,
        draw_sample_holder: bool = True,
        skip_junctions: bool = False,
        mesh_geoms: bool = True,
        ignore_metal_volume: bool = False,
        omit_ground_for_layers: Optional[list[int]] = None,
    ):
        """Render the design in Gmsh and apply changes to modify the geometries
        according to the type of simulation. Simulation parameters provided by the user.

        Args:
            selection (Union[list, None], optional): List of selected components
                                                        to render. Defaults to None.
            open_pins (Union[list, None], optional): List of open pins that are open.
                                                        Defaults to None.
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
        # QElmerRenderer from design.renderers.elmer instance.
        if not self.initialized:
            self._initiate_renderer()

        self.gmsh.render_design(selection=selection,
                                open_pins=open_pins,
                                box_plus_buffer=box_plus_buffer,
                                draw_sample_holder=draw_sample_holder,
                                skip_junctions=skip_junctions,
                                mesh_geoms=mesh_geoms,
                                ignore_metal_volume=ignore_metal_volume,
                                omit_ground_for_layers=omit_ground_for_layers)

        self.qcomp_geom_table = self.get_qgeometry_table()
        self.nets = self.assign_nets(open_pins=open_pins)

    def get_qgeometry_table(self) -> pd.DataFrame:
        """Combines the "path" and "poly" qgeometry tables into a single table, and adds
                column containing the minimum z coordinate of the layer associated with
                each qgeometry.

        Raises:
            ValueError: Raised when component in selection of qcomponents is not in QDesign.

        Returns:
            pd.DataFrame: Table with elements in both "path" and "poly" qgeometry tables.
        """

        if self.gmsh.case == 0:
            qcomp_ids = self.gmsh.qcomp_ids
        elif self.gmsh.case == 1:
            qcomp_ids = list(set(self.design._components.keys()))
        elif self.gmsh.case == 2:
            raise ValueError("Selection provided is invalid.")

        metal_layers = self.layer_types["metal"]

        mask = lambda table: table["component"].isin(qcomp_ids) & ~table[
            "subtract"] & table["layer"].isin(metal_layers)

        min_z = lambda layer: min(
            sum(self.gmsh.get_thickness_zcoord_for_layer_datatype(layer)),
            self.gmsh.get_thickness_zcoord_for_layer_datatype(layer)[1])

        path_table = self.design.qgeometry.tables["path"]
        poly_table = self.design.qgeometry.tables["poly"]
        qcomp_paths = path_table[mask(table=path_table)]
        qcomp_polys = poly_table[mask(table=poly_table)]
        qcomp_geom_table = pd.concat([qcomp_paths, qcomp_polys],
                                     ignore_index=True)

        qcomp_geom_table['min_z'] = qcomp_geom_table['layer'].apply(min_z)
        qcomp_geom_table.sort_values(by=['min_z'],
                                     inplace=True,
                                     ignore_index=True)

        return qcomp_geom_table

    def assign_nets(
        self,
        open_pins: Union[list,
                         None] = None) -> dict[Union[str, int], list[str]]:
        """Assigns a netlist number to each galvanically connected metal region,
        and returns a dictionary with each net as a key, and the corresponding list of
        geometries associated with that net as values.

        Args:
            open_pins (Union[list, None], optional): List of tuples of pins that are open.
                                                        Defaults to None.

        Returns:
            dict[Union[str, int], list[str]]: dictionary with keys for each net, and list of
                    values with the corresponding geometries associated with that net as values.
        """

        netlists = dict()
        netlist_id = 0

        qgeom_names = self.qcomp_geom_table["name"]
        qcomp_names_for_qgeom = [
            list(self.design.components.keys())[i - 1]
            for i in self.qcomp_geom_table["component"]
        ]
        phys_grps = [
            s1 + '_' + s2 for s1, s2 in zip(qcomp_names_for_qgeom, qgeom_names)
        ]
        qgeom_idxs = list(range(len(self.qcomp_geom_table)))
        id_net_dict = {k: -1 for k in phys_grps}

        while len(qgeom_idxs) != 0:
            i = qgeom_idxs.pop(0)
            shape_i = self.qcomp_geom_table.iloc[[i]]["geometry"][i]
            chip_i = self.qcomp_geom_table.iloc[[i]]["chip"][i]
            layer_i = self.qcomp_geom_table.iloc[[i]]["layer"][i]
            thick_i, z_coord_i = self.gmsh.get_thickness_zcoord_for_layer_datatype(
                layer_i)
            id_net_dict[phys_grps[i]] = netlist_id if (
                id_net_dict[phys_grps[i]] == -1) else id_net_dict[phys_grps[i]]
            for j in qgeom_idxs:
                shape_j = self.qcomp_geom_table.iloc[[j]]["geometry"][j]
                chip_j = self.qcomp_geom_table.iloc[[j]]["chip"][j]
                layer_j = self.qcomp_geom_table.iloc[[j]]["layer"][j]
                thick_j, z_coord_j = self.gmsh.get_thickness_zcoord_for_layer_datatype(
                    layer_j)
                dist = shape_i.distance(shape_j)

                layers_touch = False
                if (layer_i == layer_j or z_coord_j == z_coord_i or
                        z_coord_i + thick_i == z_coord_j or
                        z_coord_j + thick_j == z_coord_i):
                    layers_touch = True

                if dist == 0.0 and chip_i == chip_j and layers_touch:
                    if id_net_dict[phys_grps[j]] == -1:
                        id_net_dict[phys_grps[j]] = id_net_dict[phys_grps[i]]
                    elif id_net_dict[phys_grps[j]] != id_net_dict[phys_grps[i]]:
                        net_id_i = id_net_dict[phys_grps[i]]
                        for k, v in id_net_dict.items():
                            if v == net_id_i:
                                id_net_dict[k] = id_net_dict[phys_grps[j]]

            if -1 not in id_net_dict.values():
                break

            netlist_id = max(list(id_net_dict.values())) + 1

        gnd_phys_grps = self.get_gnd_qgeoms(open_pins)
        gnd_netlist = list({
            net for (name, net) in id_net_dict.items()
            if (name in gnd_phys_grps)
        })

        netlists['gnd'] = list()
        for k, v in id_net_dict.items():
            if v in gnd_netlist:
                netlists['gnd'].append(k)
            else:
                if v not in netlists.keys():
                    netlists[v] = list()
                netlists[v].append(k)

        netlists = {
            (i - 1 if (k != 'gnd') else k): v
            for i, (k, v) in enumerate(netlists.items())
        }

        return netlists

    def get_gnd_qgeoms(self, open_pins: Union[list, None] = None) -> list[str]:
        """ Obtain a list of qgeometry names associated with pins shorted to ground.

        Args:
            open_pins (Union[list, None], optional): List of tuples of pins that are open.
                                                        Defaults to None.

        Returns:
            list[str]: Names of qgeometry components with pins connected to ground plane.
        """

        open_pins = open_pins if open_pins is not None else []
        qcomp_lst = self.design.components.keys()
        all_pins = list()
        gnd_qgeoms = set()

        for qcomp in qcomp_lst:
            qcomp_pins = self.design.components[qcomp].pins.keys()
            all_pins += list(zip([qcomp] * len(qcomp_pins), qcomp_pins))

        nets_table = self.design.net_info
        gnd_nets = list(nets_table[nets_table["pin_name"] == "short"]["net_id"])
        gnd_nets_mask = nets_table["net_id"].isin(gnd_nets)
        port_nets_table = nets_table[~gnd_nets_mask]
        port_pins_names = port_nets_table["pin_name"]
        qcomp_names_for_port_pins = [
            list(qcomp_lst)[i - 1] for i in port_nets_table["component_id"]
        ]
        port_pins = list(zip(qcomp_names_for_port_pins, port_pins_names))
        all_open_pins = list(set(port_pins + open_pins))
        gnd_pins = [pin for pin in all_pins if pin not in all_open_pins]

        for pin in gnd_pins:
            qcomp_name, qcomp_pin = pin
            pin_qcomp_id = self.design.components[qcomp_name].id

            if pin_qcomp_id in list(self.qcomp_geom_table["component"]):
                pin_qcomp_geom_table = self.qcomp_geom_table[
                    self.qcomp_geom_table["component"] == pin_qcomp_id]
                pin_point = draw.Point(
                    self.design.components[qcomp_name].pins[qcomp_pin]
                    ['middle'])

                for _, qgeom_row in pin_qcomp_geom_table.iterrows():
                    if pin_point.intersects(qgeom_row["geometry"]):
                        gnd_qgeoms.add(qcomp_name + '_' + qgeom_row["name"])

        return list(gnd_qgeoms)

    def run(self,
            sim_type: str,
            display_cap_matrix: bool = False) -> Union[None, pd.DataFrame]:
        """Runs ElmerFEM analysis.

        Args:
            sim_type (str): Type of simulation to be executed by ElmerFEM.
            display_cap_matrix (bool, optional): Whether or not to return cap matrix.
                                                    Defaults to False.

        Returns:
            Union[None, pd.DataFrame]: extracted capacitance matrix if
                            display_cap_matrix = True.
        """

        setup = self.default_setup[sim_type]
        sim_dir = self._options["simulation_dir"]
        meshfile = self._options["mesh_file"]
        sif_name = self._options["simulation_input_file"]
        if sim_type == "capacitance":
            cap_matrix_file = os.path.join(self._options["simulation_dir"],
                                           setup["Capacitance_Matrix_Filename"])

        self.logger.info("Running ElmerGrid on input mesh from Gmsh...")
        self._elmer_runner.run_elmergrid(sim_dir, meshfile)
        self.logger.info(f"Running ElmerSolver for solver type: '{sim_type}'")
        self._elmer_runner.run_elmersolver(sim_dir, sif_name)

        self.capacitance_matrix = self._get_capacitance_matrix(cap_matrix_file)
        if display_cap_matrix:
            return self.capacitance_matrix

    def save_capacitance_matrix(self, path: str):
        """Saves capacitance matrix to file.

        Args:
            path (str): path where capacitance matrix should be saved.
        """
        self.capacitance_matrix.to_csv(path, sep=' ', header=True)

    def _get_capacitance_matrix(self, filename: str) -> pd.DataFrame:
        """Reads SPICE capacitance matrix file generated by ElmerFEM, converts
        and returns Maxwell capacitance matrix

        Args:
            filename (str): Name of capacitance matrix file generated by ElmerFEM

        Returns:
             pd.DataFrame: Maxwell capacitance matrix
        """
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

        name_cap = {k: v[-1] for k, v in self.nets.items() if k != "gnd"}
        df2.rename(index=name_cap, columns=name_cap, inplace=True)

        gnd_caps = -1 * df2.sum(axis=0)
        df2.loc["ground_plane"] = gnd_caps
        df2["ground_plane"] = gnd_caps
        df2 = df2.multiply(
            self.default_setup["constants"]["Permittivity_of_Vacuum"])

        # dummy value set to high as it's shorted to ground
        df2["ground_plane"]["ground_plane"] = 300
        return df2

    def add_solution_setup(
        self,
        sim_name: str = "capacitance",
        solver_names: list[str] = ["capacitance", "postprocessing_gmsh"],
        equation_name: str = "poisson",
    ):
        """Initializes ElmerFEM analysis to run.
            Currently only supports Electrostatic capacitance extraction

        Args:
            sim_name (str, optional): Type of ElmerFEM analysis to initialize.
                                        Defaults to "capacitance".
            solver_names (list[str], optional): ElmerFEM solver to use. Defaults
                                                    to ["capacitance", "postprocessing_gmsh"].
            equation_name (str, optional): Type of equation for solver. Defaults to "poisson".
        """
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

        if cap_body == 1:
            self.logger.warning(
                "WARNING: No capacitance bodies added to the model other "
                "than those connected to ground. ElmerFEM cannot run a "
                "capacitance extraction analysis without any bodies. ")

        # Update capacitance bodies in solver
        self._elmer_runner.solver["capacitance"].update(
            {"Capacitance Bodies": cap_body - 1})

        # Write the simulation input file (SIF)
        self.write_sif()

    def define_bodies(self, setup: dict, equation: int,
                      materials: list[int]) -> list[list]:
        """Assigns bodies to simulation model.

        Args:
            setup (dict): Setup parameters to be used in simulation.
            equation (int): Type of equation for solver.
            materials (list[int]): Materials used by bodies in the design.

        Returns:
            list[list]: Information about the bodies in the design.
        """
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
                for layer, ph_geoms in self.gmsh.physical_groups.items():
                    if layer in ["global", "chips"]:
                        continue

                    sub = {
                        k: v
                        for k, v in ph_geoms.items()
                        if ("dielectric" in k) and ("_sfs" not in k)
                    }
                    substrate_geoms.update(sub)

                bodies += [
                    self._elmer_runner.add_body(name, [body], equation,
                                                materials[i])
                    for name, body in substrate_geoms.items()
                ]

        return bodies

    def define_boundaries(self) -> tuple[list[list], int]:
        """Assigns boundaries to simulation model.

        Returns:
            tuple[list[list], int]: Information about the bodies in the design,
                                        and total number of capacitance bodies.
        """

        boundaries = list()
        phys_grps_dict = dict()
        ground_planes = list()
        cap_body = 1
        for layer, ph_geoms in self.gmsh.physical_groups.items():
            if layer in ["global", "chips"]:
                continue

            for name, geom in ph_geoms.items():
                if ("ground_plane" in name) and ("sfs" in name):
                    ground_planes.append(geom)

                if "dielectric" in name:
                    continue

            phys_grps_dict.update(ph_geoms)

        for net, geom_names in self.nets.items():
            geom_id_list = [
                phys_grps_dict[f"{name}_sfs"] for name in geom_names
            ]

            if net == "gnd":
                ground_planes += geom_id_list
            else:
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
        """Write sif (simulation input file) used by ElmerFEM to run analysis"""
        filename = self._options["simulation_input_file"]
        sim_dir = self._options["simulation_dir"]
        self._elmer_runner.write_startinfo_and_sif(filename=filename,
                                                   sim_dir=sim_dir)

    def render_chips(self,
                     chips: Union[str, list[str]] = [],
                     draw_sample_holder: bool = True,
                     box_plus_buffer: bool = True):
        """Abstract method. Must be implemented by the subclass.
        Render all chips of the design.
        Calls render_chip for each chip.
        """
        pass

    def render_chip(self, chip_name: str):
        """Abstract method. Must be implemented by the subclass.
        Render the given chip.

        Args:
            name (str): chip to render
        """
        pass

    def render_layers(self,
                      draw_sample_holder: bool = True,
                      layers: Union[list[int], None] = None,
                      box_plus_buffer: bool = True):
        """Abstract method. Must be implemented by the subclass.
        Render all layers of the design.
        Calls render_layer for each layer.
        """
        self.gmsh.render_layers(draw_sample_holder, layers, box_plus_buffer)

    def render_layer(self, layer_number: str, datatype: int = 0):
        """Abstract method. Must be implemented by the subclass.
        Render the given layer.

        Args:
            name (str): layer to render
        """
        self.gmsh.render_layer(layer_number, datatype)

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
        postprocessing_file = os.path.join(self._options["simulation_dir"],
                                           self._options["postprocessing_file"])
        self.gmsh.import_post_processing_data(postprocessing_file)
