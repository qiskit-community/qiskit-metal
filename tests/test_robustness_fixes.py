# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Regression tests for gmsh loading, Elmer, layer-stack and qgeometry fixes."""

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
import unittest.mock

import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiPolygon, box

from qiskit_metal import designs
from qiskit_metal.designs.design_multiplanar import MultiPlanar
from qiskit_metal.qlibrary.core import QComponent

TEST_DATA = Path(__file__).parent / "test_data"


class TestGmshSystemLibraryMissing(unittest.TestCase):
    """gmsh installed but its shared library can't load (e.g. no libGLU)."""

    def test_design_still_constructs(self):
        # Run in a subprocess: the failure happens at import time.
        code = textwrap.dedent(
            """
            import importlib.abc, sys

            class _Broken(importlib.abc.MetaPathFinder):
                def find_spec(self, name, path=None, target=None):
                    if name == "gmsh":
                        raise OSError("libGLU.so.1: cannot open shared object file")
                    return None

            sys.meta_path.insert(0, _Broken())
            from qiskit_metal import designs
            design = designs.DesignPlanar()
            print("gmsh renderer loaded:", "gmsh" in design.renderers)

            from qiskit_metal.renderers.renderer_gmsh.gmsh_utils import _require_gmsh
            try:
                _require_gmsh()
            except ImportError as exc:
                print("message:", exc)
            """
        )
        env = dict(os.environ, QISKIT_METAL_HEADLESS="1")
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        self.assertIn("gmsh renderer loaded: False", proc.stdout)
        self.assertIn("installed but failed to load", proc.stdout)
        self.assertIn("libGLU", proc.stdout)


def _elmer_renderer():
    try:
        from qiskit_metal.renderers.renderer_elmer.elmer_renderer import (
            QElmerRenderer,
        )

        return QElmerRenderer(MultiPlanar({}, True), initiate=False)
    except ImportError as exc:  # pragma: no cover - lite install
        raise unittest.SkipTest(f"Elmer renderer unavailable: {exc}")


class TestElmerCapacitanceMatrix(unittest.TestCase):
    """_get_capacitance_matrix converts ElmerSolver's SPICE matrix correctly."""

    # SPICE-style matrix in farads, as written by ElmerSolver.
    SPICE = np.array(
        [
            [100e-15, -30e-15, -20e-15],
            [-30e-15, 90e-15, -25e-15],
            [-20e-15, -25e-15, 80e-15],
        ]
    )

    def _expected(self, eps0):
        m = -self.SPICE * 1e15
        for i in range(3):
            m[i, i] = -m[:, i].sum()
        names = ["pad_a", "pad_b", "readout"]
        df = pd.DataFrame(m, index=names, columns=names)
        gnd = -df.sum(axis=0)
        df.loc["ground_plane"] = gnd
        df["ground_plane"] = gnd
        df = df * eps0
        df.loc["ground_plane", "ground_plane"] = 300
        return df

    def _run(self):
        r = _elmer_renderer()
        r.nets = {
            "gnd": ["ground"],
            1: ["Q1", "pad_a"],
            2: ["Q1", "pad_b"],
            3: ["Q1", "readout"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cap_matrix.txt")
            np.savetxt(path, self.SPICE, delimiter=" ")
            got = r._get_capacitance_matrix(path)
        eps0 = r.default_setup["constants"]["Permittivity_of_Vacuum"]
        return got, self._expected(eps0)

    def test_matches_reference(self):
        got, expected = self._run()
        np.testing.assert_allclose(got.values, expected.values)
        self.assertEqual(got.loc["ground_plane", "ground_plane"], 300)

    def test_matches_reference_under_copy_on_write(self):
        # pandas 3 enables Copy-on-Write by default; chained assignment then
        # silently does nothing. Simulate it on pandas 2.x.
        if not hasattr(pd.options.mode, "copy_on_write"):
            self.skipTest("pandas without Copy-on-Write option")
        with pd.option_context("mode.copy_on_write", True):
            got, expected = self._run()
        np.testing.assert_allclose(got.values, expected.values)
        self.assertFalse(got.isna().any().any())


class TestElmerRequiresRenderDesign(unittest.TestCase):
    def test_add_solution_setup_without_render_design(self):
        r = _elmer_renderer()
        with self.assertRaises(RuntimeError) as ctx:
            r.add_solution_setup("capacitance")
        self.assertIn("render_design", str(ctx.exception))

    def test_run_without_render_design(self):
        r = _elmer_renderer()
        with self.assertRaises(RuntimeError):
            r.run("capacitance")


class TestElmerSolverExitCode(unittest.TestCase):
    def _run_solver(self, returncode):
        from qiskit_metal.renderers.renderer_elmer import elmer_runner

        runner = elmer_runner.ElmerRunner()

        def fake_run(args, cwd, stdout, stderr):
            stdout.write("ELMER SOLVER STARTED\nProgram received signal SIGSEGV\n")
            return subprocess.CompletedProcess(args, returncode)

        with tempfile.TemporaryDirectory() as tmp:
            with (
                unittest.mock.patch.object(
                    elmer_runner, "_resolve_elmer_binary", return_value="ElmerSolver"
                ),
                unittest.mock.patch.object(elmer_runner.subprocess, "run", fake_run),
            ):
                runner.run_elmersolver(tmp, "case.sif")

    def test_crash_raises_with_log(self):
        with self.assertRaises(RuntimeError) as ctx:
            self._run_solver(-11)
        msg = str(ctx.exception)
        self.assertIn("exited with code -11", msg)
        self.assertIn("elmersolver.log", msg)
        self.assertIn("SIGSEGV", msg)

    def test_success_is_silent(self):
        self._run_solver(0)


class TestLayerStackMiss(unittest.TestCase):
    def setUp(self):
        self.design = MultiPlanar(
            metadata={},
            overwrite_enabled=True,
            layer_stack_filename=TEST_DATA / "planar_chip.txt",
        )

    def test_missing_layer_returns_none_and_warns(self):
        with self.assertLogs(self.design.ls.logger, level="WARNING") as logs:
            result = self.design.ls.get_properties_for_layer_datatype(
                ["thickness", "z_coord"], 99, 0
            )
        self.assertIsNone(result)
        self.assertIn("layer=99", "\n".join(logs.output))

    def test_existing_layer_unchanged(self):
        result = self.design.ls.get_properties_for_layer_datatype(
            ["material", "thickness"], 1, 0
        )
        self.assertEqual(result[0], "pec")
        self.assertAlmostEqual(result[1], 0.002)


class _IntKeyComponent(QComponent):
    def make(self):
        self.add_qgeometry("junction", {0: LineString([(0, 0), (0.01, 0)])}, width=0.01)
        self.add_qgeometry(
            "poly",
            {1: MultiPolygon([box(0, 0, 0.1, 0.1), box(0.2, 0, 0.3, 0.1)])},
        )


class TestQGeometryNamesAreStrings(unittest.TestCase):
    def test_non_string_keys_are_coerced(self):
        design = designs.DesignPlanar()
        comp = _IntKeyComponent(design, "custom")
        tables = design.qgeometry.tables
        junc = tables["junction"][tables["junction"]["component"] == comp.id]
        poly = tables["poly"][tables["poly"]["component"] == comp.id]
        self.assertEqual(list(junc["name"]), ["0"])
        self.assertEqual(sorted(poly["name"]), ["1_0", "1_1"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
