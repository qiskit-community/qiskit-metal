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
"""Ports and junction lines in the gmsh model (solver backends, step 1.6).

Port geometry (analyses/simulation/problem.py, ``port_sheets``) is checked
with shapely alone; rendering it in QGmshRenderer needs gmsh."""

import unittest

import numpy as np

from qiskit_metal import designs
from qiskit_metal.analyses.simulation.problem import (
    LumpedPort,
    PinRef,
    Segment,
    WavePort,
    port_sheets,
)
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket


def _gmsh_importable():
    try:
        import gmsh  # noqa: F401

        return True
    except Exception:
        return False


def _design(orientation="0"):
    design = designs.MultiPlanar({}, True)
    TransmonPocket(
        design,
        "Q1",
        options=dict(
            orientation=orientation, connection_pads=dict(a=dict(loc_W=1, loc_H=1))
        ),
    )
    design.rebuild()
    return design


class TestPortSheets(unittest.TestCase):
    def test_pin_sheet_spans_the_end_gap(self):
        for orientation in ("0", "90", "45"):
            with self.subTest(orientation=orientation):
                design = _design(orientation)
                pin = design.components["Q1"].pins["a"]
                (sheet,) = port_sheets(design, LumpedPort(PinRef("Q1", "a")))
                w, g = float(pin["width"]), float(pin["gap"])
                n = np.asarray(pin["normal"], dtype=float)
                self.assertAlmostEqual(sheet.polygon.area, w * g)
                np.testing.assert_allclose(
                    np.asarray(sheet.polygon.centroid.coords[0]),
                    np.asarray(pin["middle"]) + n * g / 2,
                    atol=1e-12,
                )
                np.testing.assert_allclose(sheet.direction, n, atol=1e-12)
                np.testing.assert_allclose(
                    sheet.line[1], np.asarray(pin["middle"]) + n * g
                )

    def test_cpw_pair_fills_the_side_gaps(self):
        design = _design("45")
        pin = design.components["Q1"].pins["a"]
        w, g = float(pin["width"]), float(pin["gap"])
        n = np.asarray(pin["normal"], dtype=float)
        t = np.array([-n[1], n[0]])
        a, b = port_sheets(
            design, LumpedPort(PinRef("Q1", "a"), shape="cpw", length=0.02)
        )
        self.assertEqual((a.suffix, b.suffix), ("_a", "_b"))
        for sheet, sign in ((a, 1), (b, -1)):
            self.assertAlmostEqual(sheet.polygon.area, g * 0.02)
            np.testing.assert_allclose(sheet.direction, sign * t, atol=1e-12)
            expected = np.asarray(pin["middle"]) + sign * t * (w + g) / 2 - n * 0.01
            np.testing.assert_allclose(
                np.asarray(sheet.polygon.centroid.coords[0]), expected, atol=1e-12
            )

    def test_segment_and_line_ports(self):
        design = _design()
        (sheet,) = port_sheets(
            design, LumpedPort(Segment((0, 0), ("30um", "40um"), "10um"), name="p")
        )
        self.assertAlmostEqual(sheet.polygon.area, 0.05 * 0.01)
        np.testing.assert_allclose(sheet.direction, (0.6, 0.8))
        (line,) = port_sheets(design, LumpedPort(PinRef("Q1", "a"), shape="line"))
        self.assertIsNone(line.polygon)


@unittest.skipUnless(_gmsh_importable(), "gmsh not installed (optional [mesh] extra)")
class TestPortsInGmsh(unittest.TestCase):
    def render(self, ports=(), orientation="0", **kw):
        from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

        r = QGmshRenderer(_design(orientation))
        r.ports = list(ports)
        r.options.update(kw)
        r.render_design(mesh_geoms=False)
        return r

    def test_lumped_port_group_and_endcap(self):
        import gmsh

        from qiskit_metal.renderers.renderer_gmsh.groups import Role

        r = self.render([LumpedPort(PinRef("Q1", "a"), R=50)])
        try:
            (port,) = r.group_map.select(role=Role.PORT)
            self.assertEqual(
                (port.name, port.dim, port.port), ("port_Port_Q1_a", 2, "Port_Q1_a")
            )
            n = r.design.components["Q1"].pins["a"]["normal"]
            np.testing.assert_allclose(port.direction, n, atol=1e-12)
            self.assertTrue(gmsh.model.getEntitiesForPhysicalGroup(2, port.tag).size)
            self.assertEqual(r._endcap_pins(None), [("Q1", "a")])
        finally:
            r.close()

    def test_cpw_line_and_wave_ports(self):
        import gmsh

        from qiskit_metal.renderers.renderer_gmsh.groups import Role

        ports = [
            LumpedPort(PinRef("Q1", "a"), shape="cpw", name="feed"),
            LumpedPort(
                Segment((-0.3, -0.3), (-0.3, -0.25), "5um"), shape="line", name="probe"
            ),
            WavePort("x-", center=(0.0, 0.0), size=("0.2mm", "0.2mm"), name="w"),
        ]
        r = self.render(ports)
        try:
            names = {g.name: g for g in r.group_map.select(role=Role.PORT)}
            self.assertEqual(
                sorted(names), ["port_feed_a", "port_feed_b", "port_probe", "port_w"]
            )
            self.assertEqual(names["port_probe"].dim, 1)
            self.assertEqual((names["port_w"].side, names["port_w"].dim), ("x-", 2))
            wave = gmsh.model.getEntitiesForPhysicalGroup(2, names["port_w"].tag)
            area = sum(gmsh.model.occ.getMass(2, int(s)) for s in wave)
            self.assertAlmostEqual(area, 0.2 * 0.2, places=6)
        finally:
            r.close()

    def test_junction_lines_and_port_refinement(self):
        import gmsh

        from qiskit_metal.analyses.simulation.problem import MeshSpec, Refine, Select
        from qiskit_metal.renderers.renderer_gmsh.groups import Role

        r = self.render([LumpedPort(PinRef("Q1", "a"))], junction_lines=True)
        try:
            (line,) = r.group_map.select(role=Role.JUNCTION, dim=1)
            self.assertEqual(
                (line.name, line.component, line.qgeometry),
                ("Q1_rect_jj_line", "Q1", "rect_jj"),
            )
            self.assertTrue(gmsh.model.getEntitiesForPhysicalGroup(1, line.tag).size)
            r.mesh_spec = MeshSpec(
                refine=[Refine(Select(port="Port_Q1_a"), "2um", "20um")]
            )
            self.assertEqual(len(r._refinement_fields(0.07)), 1)
        finally:
            r.close()

    def test_oblique_endcap(self):
        import gmsh

        from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

        r = QGmshRenderer(_design())
        r._initiate_renderer()
        try:
            normal = np.array([1.0, 1.0]) / np.sqrt(2)
            vol = r._oblique_endcap(
                np.array([0.0, 0.0]), normal, 0.01, 0.006, 0.0, 0.002
            )
            gmsh.model.occ.synchronize()
            self.assertAlmostEqual(
                gmsh.model.occ.getMass(3, vol), 0.006 * 0.022 * 0.002
            )
        finally:
            r.close()

        def ground_volume(open_pins):
            r = self.render(orientation="45")
            r.render_design(open_pins=open_pins, mesh_geoms=False)
            try:
                return sum(gmsh.model.occ.getMass(3, t) for t in r.layers_dict[1])
            finally:
                r.close()

        self.assertLess(ground_volume([("Q1", "a")]), ground_volume(None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
