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
"""Gmsh size fields: the junction field must measure distance to the junctions.

``define_mesh_size_fields`` built the junction Distance field from every metal
surface and wrote its curves to the metal field, leaving the junction field
empty, so ``mesh.max_size_jj`` had no effect."""

import unittest


def _gmsh_importable():
    try:
        import gmsh  # noqa: F401

        return True
    except Exception:
        return False


@unittest.skipUnless(
    _gmsh_importable(), "gmsh not installed (optional [mesh] extra); size-field check"
)
class TestJunctionSizeField(unittest.TestCase):
    def test_junction_field_uses_junction_curves(self):
        import gmsh
        from qiskit_metal.designs.design_multiplanar import MultiPlanar
        from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
        from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

        design = MultiPlanar()
        design.overwrite_enabled = True
        TransmonPocket(design, "Q1")
        design.rebuild()

        r = QGmshRenderer(design)
        r.options.mesh.max_size_jj = "2um"
        try:
            r.render_design(mesh_geoms=False)
            r.define_mesh_size_fields()
            jj_surfs = [t[0] for g in r.juncs_dict.values() for t in g.values()]
            jj_curves = {
                int(c)
                for s in jj_surfs
                for loop in gmsh.model.occ.getCurveLoops(s)[1]
                for c in loop
            }
            fields = gmsh.model.mesh.field
            distance = {
                f: {int(c) for c in fields.getNumbers(f, "CurvesList")}
                for f in fields.list()
                if fields.getType(f) == "Distance"
            }
            jj_threshold_sizes = [
                fields.getNumber(f, "SizeMin")
                for f in fields.list()
                if fields.getType(f) == "Threshold"
                and distance.get(int(fields.getNumber(f, "InField"))) == jj_curves
            ]
        finally:
            r.close()

        self.assertTrue(jj_curves)
        self.assertIn(jj_curves, distance.values())
        # the metal-edge field still exists and is not the junction field
        self.assertTrue(any(c - jj_curves for c in distance.values()))
        self.assertEqual(jj_threshold_sizes, [0.002])  # 2um in mm


if __name__ == "__main__":
    unittest.main(verbosity=2)
