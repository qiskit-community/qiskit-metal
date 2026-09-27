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
"""QGmshRenderer.mesh_spec: refinement by role, net, junction or box on top of
the size fields the ``mesh`` options define. Needs gmsh; skipped without."""

import unittest


def _gmsh_importable():
    try:
        import gmsh  # noqa: F401

        return True
    except Exception:
        return False


OPEN = [("Q1", "coupler1"), ("Q1", "coupler2"), ("Q1", "readout")]


def _renderer():
    from qiskit_metal import designs
    from qiskit_metal.qlibrary.qubits.transmon_pocket_6 import TransmonPocket6
    from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

    design = designs.MultiPlanar({}, True)
    TransmonPocket6(
        design,
        "Q1",
        options=dict(
            connection_pads=dict(
                readout=dict(loc_W=0, loc_H=-1),
                coupler1=dict(loc_W=-1, loc_H=1),
                coupler2=dict(loc_W=1, loc_H=1),
            )
        ),
    )
    design.rebuild()
    renderer = QGmshRenderer(design)
    renderer.options.mesh.num_threads = 1
    return renderer


_FIELD_KEYS = {
    "Distance": ["CurvesList", "NumPointsPerCurve"],
    "Threshold": ["InField", "SizeMin", "SizeMax", "DistMin", "DistMax", "Sigmoid"],
    "Min": ["FieldsList"],
    "Ball": ["XCenter", "YCenter", "ZCenter", "Radius", "VIn", "VOut"],
    "Box": ["XMin", "XMax", "YMin", "YMax", "ZMin", "ZMax", "VIn", "VOut", "Thickness"],
}
_LIST_KEYS = {"CurvesList", "FieldsList"}


def _fields():
    """Every size field: its type and its parameters."""
    import gmsh

    field = gmsh.model.mesh.field
    out = []
    for f in field.list():
        kind = field.getType(f)
        params = {}
        for key in _FIELD_KEYS.get(kind, []):
            if key in _LIST_KEYS:
                value = list(field.getNumbers(f, key))
            else:
                value = [field.getNumber(f, key)]
            params[key] = [round(v, 12) for v in value]
        out.append((kind, params))
    return out


@unittest.skipUnless(_gmsh_importable(), "gmsh not installed (optional [mesh] extra)")
class TestMeshSpec(unittest.TestCase):
    def fields_with(self, spec):
        r = _renderer()
        r.mesh_spec = spec
        try:
            r.render_design(open_pins=OPEN, mesh_geoms=False)
            r.define_mesh_size_fields()
            return _fields(), r.group_map, r
        except Exception:
            r.close()
            raise

    def test_no_spec_and_empty_spec_give_the_same_fields(self):
        from qiskit_metal.analyses.simulation.problem import MeshSpec

        plain, _, r = self.fields_with(None)
        r.close()
        empty, _, r = self.fields_with(MeshSpec())
        r.close()
        self.assertEqual(plain, empty)

    def test_net_refinement_adds_a_distance_field_on_its_edges(self):
        import gmsh

        from qiskit_metal.analyses.simulation.problem import MeshSpec, Refine, Select

        spec = MeshSpec(refine=[Refine(Select(net="pad_top_Q1"), "2um", "50um")])
        fields, gm, r = self.fields_with(spec)
        try:
            surfaces = gmsh.model.getEntitiesForPhysicalGroup(
                2, gm.get("Q1_pad_top_sfs").tag
            )
            curves = sorted(
                {
                    int(c)
                    for s in surfaces
                    for loop in gmsh.model.occ.getCurveLoops(s)[1]
                    for c in loop
                }
            )
        finally:
            r.close()
        threshold = [
            p
            for kind, p in fields
            if kind == "Threshold" and p.get("SizeMin") == [0.002]
        ]
        self.assertEqual(len(threshold), 1)
        self.assertEqual(threshold[0]["DistMax"], [0.05])
        source = fields[int(threshold[0]["InField"][0]) - 1]
        self.assertEqual(source[1]["CurvesList"], curves)
        min_field = fields[-1][1]["FieldsList"]
        self.assertIn(
            float(len(fields) - 1), min_field
        )  # the new threshold is in the Min

    def test_junction_ball_and_box(self):
        from qiskit_metal.analyses.simulation.problem import (
            JunctionRef,
            MeshSpec,
            Refine,
            Select,
        )

        spec = MeshSpec(
            refine=[
                Refine(
                    Select(junction=JunctionRef("Q1", "rect_jj")), "1um", "30um", "ball"
                ),
                Refine(
                    Select(box=("-0.1mm", "-0.1mm", "0.1mm", "0.1mm")), "3um", "20um"
                ),
            ]
        )
        fields, _, r = self.fields_with(spec)
        r.close()
        kinds = [kind for kind, _ in fields]
        self.assertIn("Ball", kinds)
        self.assertIn("Box", kinds)
        ball = next(p for kind, p in fields if kind == "Ball")
        self.assertEqual((ball["Radius"], ball["VIn"]), ([0.03], [0.001]))
        box = next(p for kind, p in fields if kind == "Box")
        self.assertEqual(
            (box["XMin"], box["XMax"], box["VIn"]), ([-0.1], [0.1], [0.003])
        )

    def test_global_sizes_override_the_options(self):
        import gmsh

        from qiskit_metal.analyses.simulation.problem import MeshSpec

        _, _, r = self.fields_with(MeshSpec(max_size="100um"))
        try:
            r.define_mesh_properties()
            self.assertAlmostEqual(gmsh.option.getNumber("Mesh.MeshSizeMax"), 0.1)
        finally:
            r.close()

    def test_unmatched_selection_is_an_error(self):
        from qiskit_metal.analyses.simulation.problem import MeshSpec, Refine, Select

        for select in (Select(net="no_such_net"), Select(port="Port_Q1_readout")):
            with self.subTest(select=select):
                with self.assertRaises(ValueError):
                    self.fields_with(MeshSpec(refine=[Refine(select, "2um", "50um")]))

    def test_refined_mesh_is_finer(self):
        """Meshing with a refinement runs, and adds nodes (one small
        rectangle, coarse sizes, to stay fast)."""
        import gmsh

        from qiskit_metal import designs
        from qiskit_metal.analyses.simulation.problem import MeshSpec, Refine, Select
        from qiskit_metal.qlibrary.sample_shapes.rectangle import Rectangle
        from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

        design = designs.MultiPlanar({}, True)
        Rectangle(design, "R1", options=dict(width="200um", height="200um"))
        design.rebuild()
        counts = []
        for spec in (
            None,
            MeshSpec(refine=[Refine(Select(component="R1"), "25um", "50um")]),
        ):
            r = QGmshRenderer(design)
            r.options.mesh.update(min_size="50um", max_size="400um", num_threads=1)
            r.mesh_spec = spec
            try:
                r.render_design(mesh_geoms=True, draw_sample_holder=False)
                counts.append(len(gmsh.model.mesh.getNodes()[0]))
            finally:
                r.close()
        self.assertGreater(counts[1], counts[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
