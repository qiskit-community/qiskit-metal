from dataclasses import dataclass
import typing as ty
import yaml
import os
import subprocess
import shutil
from collections import defaultdict
import platform

from ... import Dict
from .elmer_configs import materials, simulations, solvers


@dataclass
class Body:
    target_bodies: ty.List[int]
    equation: int
    material: int
    body_force: ty.Union[int, None]
    initial_condition: ty.Union[int, None]


@dataclass
class Boundary:
    target_boundaries: ty.List[int]
    other_opts: dict


class ElmerRunner:
    """TODO: complete class docstring
    """

    def __init__(self) -> None:
        self.header = 'Header\n  CHECK KEYWORDS "Warn"\n  Mesh DB "." "."\nEnd\n\n'
        self.simulation = defaultdict(dict)
        self.constant = dict()
        self.solver = defaultdict(dict)
        self.equation = defaultdict(list)
        self.material = defaultdict(dict)
        self.body_force = defaultdict(dict)
        self.initial_condition = defaultdict(dict)
        self.body = defaultdict(Body)
        self.boundary_condition = defaultdict(Boundary)

    @property
    def solver_info(self):
        return list(self.solver.keys())

    @property
    def simulation_info(self):
        return list(self.simulation.keys())

    @property
    def equation_info(self):
        return list(self.equation.keys())

    def add_setup_options(
        self,
        setup_param: Dict,
        new_opt: ty.Dict[str, ty.Any],
    ):
        modified_new_opt = {k.replace(' ', '_'): v for k, v in new_opt.items()}
        setup_param.update(modified_new_opt)

    def init_simulation(self, name: str, options: dict):
        if len(self.simulation.keys()) > 1:
            raise RuntimeError(
                "There can only be one simulation instance at a time.")

        self.simulation.update({name: options})

    def add_equation(self, name: str, solvers: list):
        self.equation.update({name: solvers})
        return len(self.equation)

    def add_constant(self, name: str, value: str):
        self.constant.update({name: value})

    def add_solver(self, name: str, options: dict):
        self.solver.update({name: options})
        return len(self.solver)

    def add_material(self, name: str, options: dict):
        self.material.update({name: options})
        return len(self.material)

    def add_body(self,
                 name: str,
                 target_bodies: ty.List[int],
                 equation: int,
                 material: int,
                 body_force: ty.Union[int, None] = None,
                 initial_condition: ty.Union[int, None] = None):
        sim_body = Body(target_bodies, equation, material, body_force,
                        initial_condition)
        self.body.update({name: sim_body})
        return len(self.body)

    def add_body_force(self, name: str, options: dict):
        self.body_force.update({name: options})
        return len(self.material)

    def add_boundary_condition(self, name: str, target_boundaries: ty.List[int],
                               options: dict):
        sim_boundary = Boundary(target_boundaries, options)
        self.boundary_condition.update({name: sim_boundary})
        return len(self.boundary_condition)

    def add_initial_condition(self, name: str, options: dict):
        self.initial_condition.update({name: options})
        return len(self.initial_condition)

    def _update_solver_setup(self, yaml_setup_dict: dict,
                             new_setup_params: dict):
        yaml_setup_dict.update(new_setup_params)
        return yaml_setup_dict

    def _read_yaml_to_dict(self, filename: str):
        with open(filename, "r", encoding="utf-8") as f:
            yaml_setup = yaml.safe_load(f)
            f.close()
            return yaml_setup

    def load_simulation(self, name: str, config_file: str = None):
        if config_file is not None:
            opts = self._read_yaml_to_dict(config_file)
        else:
            opts = simulations
        if name not in opts.keys():
            raise ValueError(
                "Simulation not defined in the provided config file. "
                "Either add it to your config file, or use `init_simulation` "
                "to manually add new simulation to the configuration.")
        self.init_simulation(name=name, options=opts[name])

    def load_solvers(self, solver_names: ty.List[str], config_file: str = None):
        if config_file is not None:
            opts = self._read_yaml_to_dict(config_file)
        else:
            opts = solvers
        for name in solver_names:
            if name not in opts.keys():
                raise ValueError(
                    "Solver not defined in the provided config file. "
                    "Either add it to your config file, or use `add_solver` "
                    "to manually add new solver to the simulation.")
            self.add_solver(name=name, options=opts[name])

        return [i + 1 for i in range(len(self.solver))]

    def load_materials(self,
                       material_names: ty.List[str],
                       config_file: str = None):

        if config_file is not None:
            opts = self._read_yaml_to_dict(config_file)
        else:
            opts = materials
        for name in material_names:
            if name not in opts.keys():
                raise ValueError(
                    "Material not defined in the provided config file. "
                    "Either add it to your config file, or use `add_material` "
                    "to manually add new material to the simulation.")
            self.add_material(name=name, options=opts[name])

        return [i + 1 for i in range(len(self.material))]

    def _write_sif_simulation(self):
        section_string = ""
        if len(self.simulation) > 0:
            section_string += f"! {list(self.simulation.keys())[0]}\n"
            section_string += "Simulation\n"
            for k, v in list(self.simulation.values())[0].items():
                section_string += f"  {k} = {v}\n"
            section_string += "End\n\n"
        return section_string

    def _write_sif_constants(self):
        section_string = ""
        if len(self.constant) > 0:
            section_string += "Constants\n"
            for k, v in self.constant.items():
                section_string += f"  {k} = {v}\n"
            section_string += "End\n\n"
        return section_string

    def _write_sif_equation(self):
        section_string = ""
        if len(self.equation) > 0:
            for i, k in enumerate(self.equation):
                section_string += f"! {k}\n"
                section_string += f"Equation {i+1}\n"
                solvers = [
                    list(self.solver.keys())[i - 1] for i in self.equation[k]
                ]
                active_solvers = ""
                for i, solver in enumerate(solvers):
                    section_string += f"  ! {i+1}: {solver}\n"
                    active_solvers += f" {i+1}"

                section_string += f"  Active Solvers({len(solvers)}) =" + active_solvers + '\n'
                section_string += "End\n\n"
            section_string += '\n'
        return section_string

    def _write_sif_solver(self):
        section_string = ""
        if len(self.solver) > 0:
            for i, k in enumerate(self.solver):
                section_string += f"! {k}\n"
                section_string += f"Solver {i+1}\n"
                for key, val in self.solver[k].items():
                    section_string += f"  {key} = {val}\n"
                section_string += "End\n\n"
            section_string += '\n'
        return section_string

    def _write_sif_material(self):
        section_string = ""
        if len(self.material) > 0:
            for i, k in enumerate(self.material):
                section_string += f"! {k}\n"
                section_string += f"Material {i+1}\n"
                for key, val in self.material[k].items():
                    section_string += f"  {key} = {val}\n"
                section_string += "End\n\n"
            section_string += '\n'
        return section_string

    def _write_sif_body(self):
        section_string = ""
        if len(self.body) > 0:
            for i, k in enumerate(self.body):
                section_string += f"! {k}\n"
                section_string += f"Body {i+1}\n"
                body_obj = self.body[k]
                trgt_bds = ""
                for tb in body_obj.target_bodies:
                    trgt_bds += f" {tb}"
                section_string += f"  Target Bodies({len(body_obj.target_bodies)}) =" + trgt_bds + '\n'
                section_string += f"  Equation = {body_obj.equation} ! {list(self.equation.items())[body_obj.equation-1][0]}\n"
                section_string += f"  Material = {body_obj.material} ! {list(self.material.items())[body_obj.material-1][0]}\n"
                if body_obj.body_force is not None:
                    section_string += (
                        f"  Body Force = {body_obj.body_force}"
                        f" ! {list(self.body_force.items())[body_obj.body_force-1][0]}\n"
                    )
                if body_obj.initial_condition is not None:
                    section_string += (
                        f"  Initial Condition = {body_obj.initial_condition}"
                        f" ! {list(self.initial_condition.items())[body_obj.initial_condition-1][0]}\n"
                    )
                section_string += "End\n\n"
            section_string += '\n'
        return section_string

    def _write_sif_boundary_condition(self):
        section_string = ""
        if len(self.boundary_condition) > 0:
            for i, k in enumerate(self.boundary_condition):
                section_string += f"! {k}\n"
                section_string += f"Boundary Condition {i+1}\n"
                bdry_obj = self.boundary_condition[k]
                trgt_bds = ""
                for tb in bdry_obj.target_boundaries:
                    trgt_bds += f" {tb}"
                section_string += f"  Target Boundaries({len(bdry_obj.target_boundaries)}) =" + trgt_bds + '\n'
                for k, v in bdry_obj.other_opts.items():
                    section_string += f"  {k} = {v}\n"
                section_string += "End\n\n"
            section_string += '\n'
        return section_string

    def _write_sif_initial_condition(self):
        section_string = ""
        if len(self.initial_condition) > 0:
            for i, k in enumerate(self.initial_condition):
                section_string += f"! {k}\n"
                section_string += f"Initial Condition {i+1}\n"
                for key, val in self.initial_condition[k].items():
                    section_string += f"  {key} = {val}\n"
                section_string += "End\n\n"
            section_string += '\n'
        return section_string

    def write_startinfo_and_sif(self, filename: str, sim_dir: str):
        if not os.path.exists(sim_dir):
            os.mkdir(sim_dir)

        startinfo_path = os.path.join(sim_dir, "ELMERSOLVER_STARTINFO")
        with open(startinfo_path, "w+", encoding="utf-8") as startinfo:
            startinfo.write(filename)
            startinfo.close()

        file_path = os.path.join(sim_dir, filename)
        with open(file_path, "w+", encoding="utf-8") as sif:
            sif_data = self.header
            sif_data += self._write_sif_simulation()
            sif_data += self._write_sif_constants()
            sif_data += self._write_sif_equation()
            sif_data += self._write_sif_solver()
            sif_data += self._write_sif_material()
            sif_data += self._write_sif_body()
            sif_data += self._write_sif_boundary_condition()
            sif_data += self._write_sif_initial_condition()

            sif.write(sif_data)
            sif.close()

    def run_elmergrid(self,
                      sim_dir: str,
                      meshfile: str,
                      elmergrid: str = None,
                      options: list = []):

        os_platform = platform.system()
        if elmergrid is None:
            # On Windows ElmerGrid.exe is not found once gmsh.initialize() was executed.
            # Try to use abs-path instead.
            if os_platform == 'Windows' and os.path.exists(
                    "C:/Program Files/Elmer 9.0-Release/bin/ElmerGrid.exe"):
                elmergrid = "C:/Program Files/Elmer 9.0-Release/bin/ElmerGrid.exe"
            else:
                elmergrid = "ElmerGrid"

        args = [elmergrid, "14", "2", os.path.join("..", meshfile)] + options
        with open(os.path.join(sim_dir, "elmergrid.log"),
                  "w+",
                  encoding="utf-8") as f:
            subprocess.run(args, cwd=sim_dir, stdout=f, stderr=f)

        mesh_dir = meshfile.split(".")[-2]
        files = os.listdir(mesh_dir)

        if not os.path.exists(sim_dir):
            os.mkdir(sim_dir)

        for f in files:
            if os.path.exists(os.path.join(sim_dir, f)):
                os.remove(os.path.join(sim_dir, f))
            shutil.move(os.path.join(mesh_dir, f), sim_dir)
        shutil.rmtree(mesh_dir)

    def run_elmersolver(self,
                        sim_dir: str,
                        sif_file: str,
                        out_files: ty.List[str],
                        elmersolver: str = None,
                        options: list = []):

        os_platform = platform.system()
        if elmersolver is None:
            # On Windows ElmerSolver.exe is not found once gmsh.initialize() was executed.
            # Try to use abs-path instead.
            if os_platform == 'Windows' and os.path.exists(
                    "C:/Program Files/Elmer 9.0-Release/bin/ElmerSolver.exe"):
                elmersolver = "C:/Program Files/Elmer 9.0-Release/bin/ElmerSolver.exe"
            else:
                elmersolver = "ElmerSolver"

            args = [elmersolver, sif_file] + options
            with open(os.path.join(sim_dir, "elmersolver.log"),
                      "w+",
                      encoding="utf=8") as f:
                subprocess.run(args, cwd=sim_dir, stdout=f, stderr=f)

            for f in out_files:
                out_file = os.path.join(sim_dir, f)
                if os.path.exists(os.path.join(".", f)):
                    os.remove(os.path.join(".", f))
                shutil.move(out_file, ".")

    # def run_elmersolver_mpi(self,
    #                     sim_dir: str,
    #                     sif_file: str,
    #                     elmersolver: str = None,
    #                     num_procs: int = 8,
    #                     options: list = []):

    #     os_platform = platform.system()
    #     if elmersolver is None:
    #         # On Windows ElmerSolver.exe is not found once gmsh.initialize() was executed.
    #         # Try to use abs-path instead.
    #         if os_platform == 'Windows' and os.path.exists(
    #                 "C:/Program Files/Elmer 9.0-Release/bin/ElmerSolver_mpi.exe"):
    #             elmersolver = "C:/Program Files/Elmer 9.0-Release/bin/ElmerSolver_mpi.exe"
    #         else:
    #             elmersolver = "ElmerSolver_mpi"

    #         # TODO: how to specify number of processes?
    #         args = [elmersolver, sif_file] + options
    #         with open(os.path.join(sim_dir, "elmersolver.log", "w+"),
    #                   encoding="utf=8") as f:
    #             subprocess.run(args, cwd=sim_dir, stdout=f, stderr=f)