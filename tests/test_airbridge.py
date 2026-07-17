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

from qiskit_metal import designs, Dict, view
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

    def test_renders_above_base_layers_in_view(self):
        """qm.view draws higher layers on top, so the airbridge (layers 30/31)
        sits above the base metal even if created first (phase 3 z-order)."""
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib.collections import PatchCollection

        Airbridge(self.design, "ab", options=dict(bridge_layer="30", pad_layer="31"))
        self.design.rebuild()
        fig = view(self.design)
        zorders = [
            c.get_zorder()
            for c in fig.axes[0].collections
            if isinstance(c, PatchCollection)
        ]
        self.assertTrue(zorders)
        # airbridge layers (>1) render above the base layer's z-order of ~1.0
        self.assertGreater(max(zorders), 1.0)


class TestRouteAirbridges(unittest.TestCase):
    """Auto-placement of airbridges along a route (route_airbridges)."""

    def setUp(self):
        self.design = designs.DesignPlanar()

    def test_placements_along_even_and_perpendicular(self):
        """Pure-math helper: even spacing, centered, perpendicular orientation."""
        from qiskit_metal.qlibrary.tlines.airbridge import _placements_along

        # straight 1.0-long polyline, pitch 0.2, no margin -> centered, even
        pl = _placements_along([(0.0, 0.0), (1.0, 0.0)], pitch=0.2, margin=0.0)
        self.assertGreaterEqual(len(pl), 5)
        xs = [x for x, _, _ in pl]
        self.assertAlmostEqual((min(xs) + max(xs)) / 2.0, 0.5, places=9)
        diffs = [round(b - a, 9) for a, b in zip(xs, xs[1:])]
        self.assertTrue(all(d == diffs[0] for d in diffs))
        # perpendicular to a horizontal segment -> 90 deg
        self.assertTrue(all(abs(ori - 90.0) < 1e-9 for _, _, ori in pl))

    def test_placements_along_too_short_returns_empty(self):
        from qiskit_metal.qlibrary.tlines.airbridge import _placements_along

        self.assertEqual(_placements_along([(0, 0), (0.01, 0)], 0.2, 0.1), [])

    def test_fillet_centerline_rounds_corner(self):
        """A right-angle corner is rounded onto an arc off the sharp vertex."""
        from shapely.geometry import LineString, Point
        from qiskit_metal.qlibrary.tlines.airbridge import _fillet_centerline

        pts = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]  # L-shape, sharp corner (1,0)
        line = LineString(_fillet_centerline(pts, radius=0.2))
        # the filleted trace does NOT pass through the sharp corner vertex
        self.assertGreater(line.distance(Point(1.0, 0.0)), 0.05)

    def test_route_airbridges_cross_the_filleted_trace(self):
        """Regression: every bridge lands on the *filleted* trace and its span
        actually crosses the CPW — including at corners and near the ends."""
        from shapely.geometry import LineString, Point
        from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
        from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
        from qiskit_metal.qlibrary.tlines.airbridge import (
            route_airbridges,
            _fillet_centerline,
        )

        OpenToGround(self.design, "A", options=dict(pos_x="-1mm", orientation="0"))
        OpenToGround(self.design, "B", options=dict(pos_x="1mm", orientation="180"))
        cpw = RouteMeander(
            self.design,
            "cpw",
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component="A", pin="open"),
                    end_pin=Dict(component="B", pin="open"),
                ),
                total_length="8mm",
                fillet="90um",
                trace_width="10um",
                trace_gap="6um",
                meander=Dict(spacing="300um"),
            ),
        )
        self.design.rebuild()
        bridges = route_airbridges(self.design, cpw, pitch="300um", min_spacing="30um")
        self.design.rebuild()
        self.assertGreater(len(bridges), 0)

        fillet = self.design.parse_value(cpw.options.fillet)
        trace_w = self.design.parse_value(cpw.options.trace_width)
        centerline = LineString(_fillet_centerline(cpw.get_points(), fillet))
        trace = centerline.buffer(trace_w / 2.0)

        poly = self.design.qgeometry.tables["poly"]
        spans = poly[poly["name"] == "bridge"]
        self.assertEqual(len(spans), len(bridges))
        # every span must actually overlap the trace (i.e. cross the line)
        for g in spans["geometry"]:
            self.assertTrue(g.intersects(trace))
        # every bridge center sits on the filleted centerline (not the sharp one)
        for b in bridges:
            x = float(b.options["pos_x"][:-2])
            y = float(b.options["pos_y"][:-2])
            self.assertLess(centerline.distance(Point(x, y)), 1e-6)


if __name__ == "__main__":
    unittest.main()
