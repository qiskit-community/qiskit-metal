# -*- coding: utf-8 -*-

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
"""Tests for the Airbridge QComponent."""

import unittest

from qiskit_metal import designs, Dict
from qiskit_metal.qlibrary.tlines.airbridge import Airbridge


class TestAirbridge(unittest.TestCase):
    """Airbridge renders as first-class QGeometry (not a GDS-only artifact)."""

    def setUp(self):
        self.design = designs.DesignPlanar()

    def test_instantiate(self):
        """It builds and registers on the design."""
        ab = Airbridge(self.design, "ab")
        self.assertIn("ab", self.design.components)
        self.assertIsInstance(ab, Airbridge)

    def test_default_options(self):
        """The documented default options are present."""
        opts = Airbridge.default_options
        for key in (
            "crossover_length",
            "bridge_width",
            "pad_width",
            "pad_length",
            "bridge_layer",
            "pad_layer",
        ):
            self.assertIn(key, opts)

    def test_qgeometry_on_two_layers(self):
        """make() emits real poly QGeometry: span on bridge_layer, feet on
        pad_layer — so it renders in qm.view and every renderer, unlike the
        old GDS-export-only approach."""
        Airbridge(self.design, "ab", options=dict(bridge_layer="30", pad_layer="31"))
        self.design.rebuild()

        poly = self.design.qgeometry.tables["poly"]
        self.assertGreater(len(poly), 0)

        layers = set(poly["layer"].tolist())
        self.assertIn(30, layers)  # bridge span
        self.assertIn(31, layers)  # landing pads

        # All emitted geometry is non-degenerate.
        for geom in poly["geometry"]:
            self.assertGreater(geom.area, 0.0)

    def test_orientation_and_position_applied(self):
        """pos_x/pos_y/orientation reposition the whole crossover."""
        Airbridge(
            self.design,
            "ab",
            options=dict(pos_x="0.2mm", pos_y="0.1mm", orientation="90"),
        )
        self.design.rebuild()
        poly = self.design.qgeometry.tables["poly"]
        # Union bounds should sit around the requested (0.2, 0.1) mm center.
        minx = poly["geometry"].apply(lambda g: g.bounds[0]).min()
        maxx = poly["geometry"].apply(lambda g: g.bounds[2]).max()
        miny = poly["geometry"].apply(lambda g: g.bounds[1]).min()
        maxy = poly["geometry"].apply(lambda g: g.bounds[3]).max()
        self.assertAlmostEqual((minx + maxx) / 2.0, 0.2, places=3)
        self.assertAlmostEqual((miny + maxy) / 2.0, 0.1, places=3)


class TestRouteAirbridges(unittest.TestCase):
    """Auto-placement of airbridges along a route (route_airbridges)."""

    def setUp(self):
        self.design = designs.DesignPlanar()

    def test_segment_placements_even_and_perpendicular(self):
        """Pure-math helper: even spacing, centered, perpendicular orientation."""
        from qiskit_metal.qlibrary.tlines.airbridge import _segment_placements

        # horizontal 1.0-long segment, pitch 0.2, no margin -> 6 bridges centered
        pl = _segment_placements((0.0, 0.0), (1.0, 0.0), pitch=0.2, margin=0.0)
        self.assertEqual(len(pl), 6)
        xs = [x for x, _, _ in pl]
        # centered about the midpoint 0.5 and evenly spaced
        self.assertAlmostEqual((min(xs) + max(xs)) / 2.0, 0.5, places=9)
        diffs = [round(b - a, 9) for a, b in zip(xs, xs[1:])]
        self.assertTrue(all(d == diffs[0] for d in diffs))
        # perpendicular to a horizontal segment -> 90 deg
        self.assertTrue(all(abs(ori - 90.0) < 1e-9 for _, _, ori in pl))

    def test_segment_too_short_returns_empty(self):
        from qiskit_metal.qlibrary.tlines.airbridge import _segment_placements

        self.assertEqual(_segment_placements((0, 0), (0.01, 0), 0.2, 0.1), [])

    def test_route_airbridges_are_components_on_centerline(self):
        """Bridges are real components, added to the design, on the CPW path."""
        from shapely.geometry import LineString, Point
        from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
        from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
        from qiskit_metal.qlibrary.tlines.airbridge import route_airbridges

        OpenToGround(self.design, "A", options=dict(pos_x="-0.5mm", orientation="0"))
        OpenToGround(self.design, "B", options=dict(pos_x="0.5mm", orientation="180"))
        cpw = RouteStraight(
            self.design,
            "cpw",
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component="A", pin="open"),
                    end_pin=Dict(component="B", pin="open"),
                ),
                trace_width="10um",
                trace_gap="6um",
            ),
        )
        self.design.rebuild()
        bridges = route_airbridges(self.design, cpw, pitch="200um", min_spacing="20um")
        self.assertGreater(len(bridges), 0)
        for b in bridges:
            self.assertIsInstance(b, Airbridge)
            self.assertIn(b.name, self.design.components)
        # every bridge center lies on the CPW centerline
        path = LineString(cpw.get_points())
        for b in bridges:
            x = float(b.options["pos_x"][:-2])
            y = float(b.options["pos_y"][:-2])
            self.assertLess(path.distance(Point(x, y)), 1e-9)


if __name__ == "__main__":
    unittest.main()
