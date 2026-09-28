# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""The solver-neutral simulation problem (analyses/simulation/problem.py).

Pure Python, no solver: conversion to and from the simulation classes' tuple
arguments, checks against a design, values in SI units, and studies built from
the simulation classes' setups."""

import unittest

from qiskit_metal import designs
from qiskit_metal.analyses.simulation import (
    EigenmodeSim,
    LumpedElementsSim,
    ScatteringImpedanceSim,
)
from qiskit_metal.analyses.simulation.problem import (
    Boundaries,
    DrivenStudy,
    EigenmodeStudy,
    ElectrostaticStudy,
    Junction,
    JunctionRef,
    LumpedPort,
    NotExpressibleError,
    PinEnd,
    PinRef,
    Segment,
    SimulationProblem,
    SurfaceImpedance,
    Sweep,
    SymmetryPlane,
    WavePort,
    circuit_value,
    length_m,
    study_from_setup,
)

# run_sim argument lists used by the analysis tutorials (4.02, 4.03, 4.14,
# 4.16-4.18, 4.22, 4.23, A.4, A.7, and the pyaedt multiplanar notebooks).
TUTORIAL_ARGS = [
    dict(components=["Q1", "readout"], open_terminations=[("readout", "end")]),
    dict(open_terminations=[("readout", "start"), ("readout", "end")]),
    dict(open_terminations=[]),
    dict(
        components=["Q1"],
        open_terminations=[],
        port_list=[("Q1", "readout", 70)],
        jj_to_port=[("Q1", "rect_jj", 50, True)],
    ),
    dict(
        open_terminations=[],
        port_list=[("cpw_openRight", "end", 50), ("cpw_openLeft", "end", 50)],
        jj_to_port=[],
        ignored_jjs=[("Q1", "rect_jj"), ("Q2", "rect_jj")],
    ),
    dict(open_terminations=[], port_list=[("LP1", "in", 50), ("LP2", "in", 50)]),
    dict(open_terminations=[], port_list=[("LP1", "in", "50"), ("LP2", "in", "50")]),
    dict(
        open_terminations=[],
        port_list=[("cpw_openRight", "end", 50), ("cpw_openLeft", "end", 50)],
        jj_to_port=[("Q1", "rect_jj", 50, False)],
        ignored_jjs=[("Q2", "rect_jj")],
        box_plus_buffer=False,
    ),
    dict(
        components=["Q_0"],
        open_terminations=[("Q_0", "readout"), ("Q_0", "bus_01"), ("Q_0", "bus_02")],
        ignored_jjs=[("Q_0", "rect_jj"), ("Q_2", "rect_jj")],
    ),
    dict(
        open_terminations=[("Q_Main", p) for p in ("readout", "bus_01", "bus_02")],
    ),
]

PYAEDT_ARGS = dict(
    open_terminations=[],
    port_list=[("cpw_openRight", "end", 50), ("cpw_openLeft", "end", 50)],
    jj_to_port=[("Q2", "rect_jj", 51)],
    ignored_jjs=[("Q1", "rect_jj")],
)

KEYS = (
    "components",
    "open_terminations",
    "port_list",
    "jj_to_port",
    "ignored_jjs",
    "box_plus_buffer",
)


def normalized(args):
    """Empty lists are the same as None; impedances are floats."""
    out = {}
    for key in KEYS:
        value = args.get(key, True if key == "box_plus_buffer" else None)
        if isinstance(value, list):
            value = [
                tuple(float(x) if i == 2 else x for i, x in enumerate(item))
                if isinstance(item, tuple)
                else item
                for item in value
            ] or None
        out[key] = value
    return out


class TestRunArgsConversion(unittest.TestCase):
    def test_tutorial_arguments_round_trip(self):
        for args in TUTORIAL_ARGS:
            with self.subTest(args=args):
                problem = SimulationProblem.from_run_args(None, **args)
                self.assertEqual(normalized(problem.to_run_args()), normalized(args))

    def test_pyaedt_three_element_jj_to_port_round_trips(self):
        problem = SimulationProblem.from_run_args(None, **PYAEDT_ARGS)
        args = problem.to_run_args(jj_to_port_arity=3)
        self.assertEqual(normalized(args), normalized(PYAEDT_ARGS))

    def test_meaning_of_each_argument(self):
        problem = SimulationProblem.from_run_args(
            None,
            components=["Q1"],
            open_terminations=[("Q1", "bus")],
            port_list=[("Q1", "readout", "70")],
            jj_to_port=[("Q1", "rect_jj", 50, True)],
            ignored_jjs=[("Q2", "rect_jj")],
            box_plus_buffer=False,
        )
        self.assertEqual(problem.pin_end(PinRef("Q1", "bus")), PinEnd.OPEN)
        self.assertEqual(problem.pin_end(PinRef("Q1", "other")), PinEnd.SHORT)
        self.assertEqual(problem.ports, [LumpedPort(PinRef("Q1", "readout"), R=70.0)])
        self.assertEqual(
            problem.junction(JunctionRef("Q1", "rect_jj")),
            Junction("port", R=50.0, shunt_inductor=True),
        )
        self.assertEqual(problem.junction(JunctionRef("Q2", "rect_jj")).mode, "open")
        self.assertEqual(problem.junction(JunctionRef("Q3", "rect_jj")), Junction())
        self.assertFalse(problem.box.plus_buffer)
        self.assertEqual(problem.port_labels(), ["Port_Q1_readout", "Port_Q1_rect_jj"])

    def test_junction_both_port_and_ignored_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "both jj_to_port and ignored_jjs"):
            SimulationProblem.from_run_args(
                None,
                jj_to_port=[("Q1", "rect_jj", 50, False)],
                ignored_jjs=[("Q1", "rect_jj")],
            )

    def test_malformed_tuple_is_an_error(self):
        with self.assertRaisesRegex(ValueError, r"\(component, pin, impedance\)"):
            SimulationProblem.from_run_args(None, port_list=[("Q1", "readout")])

    def test_parts_without_tuple_form_raise_together(self):
        problem = SimulationProblem.from_run_args(None, port_list=[("Q1", "a", 50)])
        problem.ports.append(WavePort("x-", center=(0, 0), size=(0.1, 0.1)))
        problem.ports.append(
            LumpedPort(Segment((0, 0), (0, 0.01), "5um"), name="probe")
        )
        problem.ports.append(LumpedPort(PinRef("Q1", "b"), shape="cpw"))
        problem.junctions[JunctionRef("Q1", "rect_jj")] = Junction(L="12nH")
        problem.boundaries.metal = SurfaceImpedance(Ls="0.5pH")
        with self.assertRaises(NotExpressibleError) as caught:
            problem.to_run_args()
        message = str(caught.exception)
        for part in (
            "wave port WavePort_x-",
            "lumped port probe is not on a pin",
            "Port_Q1_b has shape 'cpw'",
            "junction Q1.rect_jj: explicit L",
            "boundary conditions",
        ):
            self.assertIn(part, message)

    def test_shunt_inductor_needs_four_element_form(self):
        problem = SimulationProblem.from_run_args(
            None, jj_to_port=[("Q1", "rect_jj", 50, True)]
        )
        with self.assertRaisesRegex(NotExpressibleError, "four-element form"):
            problem.to_run_args(jj_to_port_arity=3)


class TestValidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
        from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround

        cls.design = designs.MultiPlanar({}, overwrite_enabled=True)
        TransmonPocket(
            cls.design,
            "Q1",
            options=dict(connection_pads=dict(readout=dict(), bus=dict(loc_W=-1))),
        )
        OpenToGround(cls.design, "open1", options=dict(pos_x="1mm"))
        cls.design.rebuild()

    def problem(self, **args):
        return SimulationProblem.from_run_args(self.design, **args)

    def test_valid_problem_passes(self):
        self.problem(
            components=["Q1", "open1"],
            open_terminations=[("Q1", "bus")],
            port_list=[("Q1", "readout", 50)],
            jj_to_port=[("Q1", "rect_jj", 50, False)],
        ).validate()

    def test_every_error_is_reported(self):
        problem = self.problem(
            components=["Q1", "nope"],
            open_terminations=[("Q1", "readout"), ("Q1", "missing"), ("open1", "open")],
            port_list=[("Q1", "readout", 50), ("ghost", "a", 50)],
            jj_to_port=[("Q1", "no_such_jj", 50, False)],
        )
        problem.ports.append(LumpedPort(Segment((0, 0), (0, 0.01), "5um")))
        problem.ports.append(LumpedPort(PinRef("Q1", "bus"), name="Port_Q1_readout"))
        with self.assertRaises(ValueError) as caught:
            problem.validate()
        message = str(caught.exception)
        for part in (
            "components: no component 'nope'",
            "pin Q1.missing: no such pin",
            "component 'open1' is not in components",
            "pin ghost.a: no component 'ghost'",
            "pin Q1.readout is both open and a port",
            "junction Q1.no_such_jj: no such junction",
            "a port on a Segment needs a name",
            "repeated port names ['Port_Q1_readout']",
        ):
            self.assertIn(part, message)

    def test_needs_a_design(self):
        with self.assertRaisesRegex(ValueError, "no design"):
            SimulationProblem().validate()


class TestValues(unittest.TestCase):
    def setUp(self):
        self.design = designs.MultiPlanar({}, overwrite_enabled=True)
        self.design.variables["w"] = "10um"
        self.design.variables["Lj"] = "12nH"

    def test_length_m(self):
        self.assertAlmostEqual(length_m("2um", self.design), 2e-6)
        self.assertAlmostEqual(length_m(0.1, self.design), 1e-4)  # design units: mm
        self.assertAlmostEqual(length_m("w", self.design), 1e-5)
        with self.assertRaises(ValueError):
            length_m("10nH", self.design)

    def test_circuit_value(self):
        self.assertAlmostEqual(circuit_value("10nH", "H"), 1e-8)
        self.assertAlmostEqual(circuit_value("50", "ohm"), 50.0)
        self.assertAlmostEqual(circuit_value(2e-15, "F"), 2e-15)
        self.assertAlmostEqual(circuit_value("Lj", "H", self.design), 1.2e-8)
        self.assertAlmostEqual(
            circuit_value("Lj", "H", self.design, variables={"Lj": "9 nH"}), 9e-9
        )
        with self.assertRaises(ValueError):
            circuit_value("10um", "H")
        with self.assertRaises(ValueError):
            circuit_value("not_a_variable", "H")
        with self.assertRaises(ValueError):
            circuit_value("a", "H", variables={"a": "b", "b": "a"})


class TestBoundaries(unittest.TestCase):
    def test_outer_defaults_depend_on_the_study(self):
        b = Boundaries()
        self.assertEqual(set(b.outer_for("electrostatic").values()), {"open"})
        self.assertEqual(set(b.outer_for("eigenmode").values()), {"pec"})
        b.outer = {"z+": "absorbing"}
        walls = b.outer_for("driven")
        self.assertEqual(walls["z+"], "absorbing")
        self.assertEqual(walls["x-"], "pec")
        self.assertFalse(b.is_default)

    def test_unknown_side_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "Unknown sides"):
            Boundaries(outer={"top": "pec"}).outer_for("eigenmode")

    def test_symmetry_is_not_default(self):
        self.assertTrue(Boundaries().is_default)
        self.assertFalse(Boundaries(symmetry=[SymmetryPlane("x", 0)]).is_default)


class TestStudies(unittest.TestCase):
    def test_eigenmode_from_default_setup(self):
        defaults = EigenmodeSim.default_setup
        study = EigenmodeStudy.from_setup(defaults, defaults)
        self.assertEqual((study.n_modes, study.min_freq_ghz), (1, 1.0))
        self.assertEqual(study.adaptive.max_passes, 10)
        self.assertEqual(study.adaptive.criterion, "delta_f_pct")
        self.assertEqual(study.adaptive.tolerance, 0.5)
        self.assertEqual(study.adaptive.refine_pct, 30.0)
        self.assertEqual(set(study.backend_settings), {"basis_order", "vars"})
        self.assertEqual(study.set_keys, frozenset())

    def test_changed_keys_are_recorded(self):
        defaults = EigenmodeSim.default_setup
        setup = dict(defaults, n_modes=3, max_passes=1)
        study = EigenmodeStudy.from_setup(setup, defaults)
        self.assertEqual(study.n_modes, 3)
        self.assertEqual(study.set_keys, frozenset({"n_modes", "max_passes"}))

    def test_simulation_bookkeeping_keys_are_not_physics(self):
        sim = EigenmodeSim(design=None, renderer_name=None)
        study = study_from_setup("eigenmode", sim.setup, EigenmodeSim.default_setup)
        self.assertFalse(
            {"name", "reuse_selected_design", "reuse_setup"}
            & set(study.backend_settings)
        )
        self.assertFalse(
            {"name", "reuse_selected_design", "reuse_setup"} & study.set_keys
        )

    def test_electrostatic_from_default_setup(self):
        defaults = LumpedElementsSim.default_setup
        study = ElectrostaticStudy.from_setup(defaults, defaults)
        self.assertEqual(study.adaptive.criterion, "delta_c_pct")
        self.assertEqual(study.adaptive.min_converged, 2)
        self.assertEqual(study.adaptive.tolerance, 0.5)
        self.assertEqual(
            set(study.backend_settings),
            {
                "freq_ghz",
                "save_fields",
                "enabled",
                "auto_increase_solution_order",
                "solution_order",
                "solver_type",
            },
        )

    def test_driven_from_default_setup(self):
        defaults = ScatteringImpedanceSim.default_setup
        study = DrivenStudy.from_setup(defaults, defaults)
        self.assertEqual(study.sweep, Sweep(2.0, 8.0, 101, None, "Fast"))
        self.assertEqual(len(study.sweep.frequencies_ghz()), 101)
        self.assertEqual(study.adapt_freq_ghz, 5.0)
        self.assertEqual(study.adaptive.criterion, "delta_s")
        self.assertEqual(
            study.backend_settings["sweep_setup"],
            {"name": "Sweep", "save_fields": False},
        )
        self.assertIn("basis_order", study.backend_settings)

    def test_sweep_by_step(self):
        f = Sweep(4.0, 5.0, step_ghz=0.25).frequencies_ghz()
        self.assertEqual(list(f), [4.0, 4.25, 4.5, 4.75, 5.0])

    def test_study_from_solution_type(self):
        self.assertIsInstance(
            study_from_setup("capacitive", LumpedElementsSim.default_setup),
            ElectrostaticStudy,
        )
        with self.assertRaisesRegex(ValueError, "Unknown solution_type"):
            study_from_setup("transient", {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
