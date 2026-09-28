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
"""Backend capabilities and the check before a simulation runs
(analyses/simulation/capabilities.py). No solver needed."""

import unittest
from unittest.mock import patch

from qiskit_metal import config, designs
from qiskit_metal.analyses.simulation import (
    EigenmodeSim,
    LumpedElementsSim,
    ScatteringImpedanceSim,
)
from qiskit_metal.analyses.simulation.capabilities import (
    BUILTIN,
    BackendCapabilityError,
    Capabilities,
    capabilities_for,
    capability_table,
    check_study,
    requirements_from_problem,
)
from qiskit_metal.analyses.simulation.problem import (
    Boundaries,
    DrivenStudy,
    EigenmodeStudy,
    ElectrostaticStudy,
    Junction,
    JunctionRef,
    LumpedPort,
    PinRef,
    SimulationProblem,
    SurfaceImpedance,
    SymmetryPlane,
    WavePort,
)


class TestRegistry(unittest.TestCase):
    def test_every_configured_renderer_is_declared(self):
        """A renderer added to config.renderers_to_load needs an entry here
        (or a ``capabilities`` class attribute), so the check can explain it."""
        self.assertEqual(set(config.renderers_to_load) - set(BUILTIN), set())

    def test_declared_attribute_wins(self):
        class Custom:
            capabilities = Capabilities(label="custom", studies=frozenset({"driven"}))

        self.assertEqual(capabilities_for("hfss", Custom()).label, "custom")
        self.assertIsNone(capabilities_for("not_a_renderer"))

    def test_table_lists_every_backend(self):
        for fmt in ("markdown", "rst"):
            table = capability_table(fmt)
            for name in BUILTIN:
                self.assertIn(name, table)
        with self.assertRaises(ValueError):
            capability_table("html")


class TestStudyCheck(unittest.TestCase):
    def test_supported_pairs_pass(self):
        for renderer, study, sim in (
            ("hfss", "eigenmode", "EigenmodeSim"),
            ("hfss", "driven", "ScatteringImpedanceSim"),
            ("q3d", "electrostatic", "LumpedElementsSim"),
            ("skeleton", "eigenmode", "EigenmodeSim"),  # declares nothing
        ):
            check_study(renderer, study, sim)

    def test_wrong_study_names_the_alternatives(self):
        with self.assertRaises(BackendCapabilityError) as caught:
            check_study("q3d", "eigenmode", "EigenmodeSim", registered=["q3d", "hfss"])
        message = str(caught.exception)
        self.assertIn("cannot run eigenmode studies", message)
        self.assertIn("'hfss' (Ansys HFSS (COM); registered in this design)", message)

    def test_direct_use_backend_says_how_to_use_it(self):
        with self.assertRaises(BackendCapabilityError) as caught:
            check_study("elmer", "electrostatic", "LumpedElementsSim")
        message = str(caught.exception)
        self.assertIn("through its own API", message)
        self.assertIn("tutorial 4.19", message)
        self.assertIn("'q3d'", message)

    def test_non_solver_renderer(self):
        with self.assertRaisesRegex(BackendCapabilityError, "runs no simulations"):
            check_study("gds", "eigenmode", "EigenmodeSim")


class TestSimulationClassesCheckFirst(unittest.TestCase):
    """The check runs at the start of run_sim, before any rendering."""

    def setUp(self):
        self.design = designs.DesignPlanar()

    def test_unsupported_renderer_fails_before_rendering(self):
        for cls, renderer in (
            (EigenmodeSim, "elmer"),
            (EigenmodeSim, "q3d"),
            (LumpedElementsSim, "hfss"),
            (ScatteringImpedanceSim, "aedt_hfss"),
        ):
            with self.subTest(cls=cls.__name__, renderer=renderer):
                sim = cls(self.design, renderer)
                with patch.object(cls, "_render") as render:
                    with self.assertRaises(BackendCapabilityError):
                        sim.run_sim()
                render.assert_not_called()

    def test_supported_renderer_passes_the_check(self):
        for cls, renderer in (
            (EigenmodeSim, "hfss"),
            (ScatteringImpedanceSim, "hfss"),
            (LumpedElementsSim, "q3d"),
        ):
            with self.subTest(cls=cls.__name__):
                cls(self.design, renderer)._check_backend()

    def test_no_renderer_is_not_checked(self):
        EigenmodeSim(self.design, renderer_name=None)._check_backend()


class TestRequirements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket

        cls.design = designs.MultiPlanar({}, overwrite_enabled=True)
        TransmonPocket(cls.design, "Q1", options=dict(connection_pads=dict(a=dict())))
        cls.design.rebuild()

    def test_eigenmode_problem(self):
        problem = SimulationProblem.from_run_args(
            self.design, port_list=[("Q1", "a", 50)]
        )
        req = requirements_from_problem(
            problem, EigenmodeStudy(), outputs={"frequencies", "junction_epr"}
        )
        self.assertEqual(req.study, "eigenmode")
        self.assertEqual(req.ports, {"lumped_sheet"})
        self.assertEqual(req.junctions, {"inductor"})  # Q1's rect_jj, by default
        self.assertEqual(req.boundaries, {"pec"})
        self.assertTrue(BUILTIN["hfss"].check(req).ok)

    def test_electrostatic_leaves_junctions_open(self):
        problem = SimulationProblem.from_run_args(self.design)
        req = requirements_from_problem(problem, ElectrostaticStudy(), {"capacitance"})
        self.assertEqual(req.junctions, {"open"})
        self.assertEqual(req.boundaries, {"pec", "open_electrostatic"})
        self.assertTrue(BUILTIN["q3d"].check(req).ok)
        self.assertTrue(BUILTIN["elmer"].check(req).ok)

    def test_missing_features_are_all_reported(self):
        problem = SimulationProblem.from_run_args(self.design)
        problem.ports.append(WavePort("x-", (0, 0), (0.1, 0.1)))
        problem.ports.append(LumpedPort(PinRef("Q1", "a"), shape="line"))
        problem.junctions[JunctionRef("Q1", "rect_jj")] = Junction("port")
        problem.boundaries = Boundaries(
            metal=SurfaceImpedance(Ls="0.5pH"),
            outer={"z+": "absorbing"},
            symmetry=[SymmetryPlane("x", 0)],
        )
        req = requirements_from_problem(problem, DrivenStudy(), {"network"})
        report = BUILTIN["hfss"].check(req)
        self.assertFalse(report.ok)
        for part in (
            "port 'wave'",
            "port 'lumped_line'",
            "boundary condition 'surface_impedance'",
            "boundary condition 'absorbing'",
            "boundary condition 'pmc_symmetry'",
        ):
            self.assertIn(part, report.missing)

    def test_changed_adaptive_settings_are_ignored_on_single_pass_backends(self):
        defaults = LumpedElementsSim.default_setup
        study = ElectrostaticStudy.from_setup(dict(defaults, max_passes=3), defaults)
        req = requirements_from_problem(
            SimulationProblem.from_run_args(self.design), study, {"capacitance"}
        )
        self.assertEqual(BUILTIN["elmer"].check(req, study).ignored, ["max_passes"])
        self.assertEqual(BUILTIN["q3d"].check(req, study).ignored, [])
        untouched = ElectrostaticStudy.from_setup(defaults, defaults)
        self.assertEqual(BUILTIN["elmer"].check(req, untouched).ignored, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
