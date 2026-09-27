# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Elmer mesh and ElmerGrid paths.

run_elmergrid() passed ElmerGrid "../<mesh_file>" from inside simulation_dir,
so the mesh had to sit exactly one level above it, and derived the output
folder with meshfile.split(".")[-2]. With simulation_dir set to a temporary
directory (as tests/test_airbridge_elmer.py does) the solve failed with
FileNotFoundError: 'out'. A fake ElmerGrid stands in for the real one here.
"""

import os
import stat
import sys
import tempfile
import unittest

from qiskit_metal.renderers.renderer_elmer.elmer_runner import ElmerRunner

# ElmerGrid 14 2 <mesh.msh>: writes <mesh>/mesh.header next to the input.
_FAKE_ELMERGRID = """#!{python}
import os, sys
mesh = sys.argv[3]
assert os.path.isabs(mesh), "ElmerGrid must be given an absolute mesh path"
out = os.path.splitext(mesh)[0]
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "mesh.header"), "w").write("fake")
"""


@unittest.skipIf(sys.platform.startswith("win"), "fake binary is a shebang script")
class TestRunElmerGrid(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.fake = os.path.join(self.tmp, "ElmerGrid")
        with open(self.fake, "w") as f:
            f.write(_FAKE_ELMERGRID.format(python=sys.executable))
        os.chmod(self.fake, os.stat(self.fake).st_mode | stat.S_IEXEC)

    def _run(self, sim_dir, meshfile):
        ElmerRunner.run_elmergrid(
            ElmerRunner.__new__(ElmerRunner), sim_dir, meshfile, elmergrid=self.fake
        )

    def test_mesh_inside_a_temporary_simulation_dir(self):
        sim_dir = os.path.join(self.tmp, "sim.v1")  # a dot in the path, too
        os.makedirs(sim_dir)
        mesh = os.path.join(sim_dir, "out.msh")
        open(mesh, "w").write("mesh")
        self._run(sim_dir, mesh)
        self.assertTrue(os.path.exists(os.path.join(sim_dir, "mesh.header")))
        self.assertFalse(os.path.exists(os.path.join(sim_dir, "out")))

    def test_mesh_anywhere_else(self):
        sim_dir = os.path.join(self.tmp, "a", "b", "sim")
        elsewhere = os.path.join(self.tmp, "meshes")
        os.makedirs(elsewhere)
        mesh = os.path.join(elsewhere, "cell.msh")
        open(mesh, "w").write("mesh")
        self._run(sim_dir, mesh)
        self.assertTrue(os.path.exists(os.path.join(sim_dir, "mesh.header")))

    def test_failed_conversion_says_where_to_look(self):
        sim_dir = os.path.join(self.tmp, "sim")
        failing = os.path.join(self.tmp, "ElmerGridFail")
        with open(failing, "w") as f:
            f.write(f"#!{sys.executable}\nimport sys; sys.exit(1)\n")
        os.chmod(failing, os.stat(failing).st_mode | stat.S_IEXEC)
        with self.assertRaises(FileNotFoundError) as caught:
            ElmerRunner.run_elmergrid(
                ElmerRunner.__new__(ElmerRunner),
                sim_dir,
                os.path.join(self.tmp, "missing.msh"),
                elmergrid=failing,
            )
        self.assertIn("elmergrid.log", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
