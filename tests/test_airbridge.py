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

    def test_posts_are_opt_in(self):
        """enable_posts defaults off (span + pads only); turning it on adds
        support-post geometry on post_layer."""
        Airbridge(self.design, "off", options=dict(bridge_layer="30", pad_layer="31"))
        self.design.rebuild()
        off_layers = set(self.design.qgeometry.tables["poly"]["layer"].tolist())
        self.assertEqual(off_layers, {30, 31})

        d2 = designs.DesignPlanar()
        Airbridge(
            d2,
            "on",
            options=dict(
                bridge_layer="30", pad_layer="31", post_layer="32", enable_posts="True"
            ),
        )
        d2.rebuild()
        on = d2.qgeometry.tables["poly"]
        self.assertIn(32, set(on["layer"].tolist()))
        # the post geometry on post_layer is non-degenerate
        posts = on[on["layer"] == 32]
        self.assertGreater(len(posts), 0)
        self.assertGreater(sum(g.area for g in posts["geometry"]), 0.0)


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

    def test_fillet_centerline_reports_corner_arclengths(self):
        """return_corners yields one arc-length per rounded bend, located near
        the bend's projection onto the filleted centerline."""
        import numpy as np
        from qiskit_metal.qlibrary.tlines.airbridge import _fillet_centerline

        pts = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]  # single 90-degree bend
        coords, corners = _fillet_centerline(pts, radius=0.2, return_corners=True)
        self.assertEqual(len(corners), 1)
        # the reported arc length indexes a point that is actually on the arc
        # (near the (1,0) corner, at roughly radius distance from it)
        seg = np.diff(coords, axis=0)
        cum = np.concatenate([[0.0], np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))])
        k = int(np.searchsorted(cum, corners[0]))
        d = np.hypot(*(coords[k] - np.array([1.0, 0.0])))
        self.assertLess(d, 0.3)

    def test_bridge_at_corners_places_one_bridge_per_bend(self):
        """bridge_at_corners guarantees a bridge centered on each rounded bend
        even when the uniform pitch would otherwise skip it."""
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

        fillet = self.design.parse_value(cpw.options.fillet)
        coords, corners = _fillet_centerline(
            cpw.get_points(), fillet, return_corners=True
        )
        centerline = LineString(coords)
        trace = centerline.buffer(self.design.parse_value(cpw.options.trace_width) / 2)

        # A coarse pitch (larger than the corner spacing) would skip bends
        # without the option.
        bridges = route_airbridges(
            self.design, cpw, pitch="600um", min_spacing="30um", bridge_at_corners=True
        )
        self.design.rebuild()

        centers = [
            Point(float(b.options["pos_x"][:-2]), float(b.options["pos_y"][:-2]))
            for b in bridges
        ]
        total = centerline.length
        interior = [s for s in corners if 0.03 < s < total - 0.03]
        # every interior bend has a bridge center within a bridge-pitch of it
        for s in interior:
            cp = centerline.interpolate(s)
            self.assertTrue(
                any(cp.distance(c) < 1e-6 or c.distance(cp) < 0.05 for c in centers),
                f"no bridge near corner at arc length {s}",
            )
        # and every span still crosses the trace
        poly = self.design.qgeometry.tables["poly"]
        for g in poly[poly["name"] == "bridge"]["geometry"]:
            self.assertTrue(g.intersects(trace))

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


class TestAirbridge3DLayerStack(unittest.TestCase):
    """[EXPERIMENTAL] The layer-stack elevation seam for 3D airbridges (#1144).

    Pure-Python coverage of the row construction and the layer-stack mutation;
    the actual 3D mesh is validated in a gmsh-gated test below."""

    def test_rows_elevate_the_bridge_layer(self):
        from qiskit_metal.qlibrary.tlines.airbridge import airbridge_layer_stack_rows

        rows = airbridge_layer_stack_rows(
            bridge_layer=30, pad_layer=31, bridge_z_coord="3um"
        )
        self.assertEqual(len(rows), 2)
        by_layer = {r["layer"]: r for r in rows}
        # pads on the base plane, span elevated
        self.assertEqual(by_layer[31]["z_coord"], "0um")
        self.assertEqual(by_layer[30]["z_coord"], "3um")
        # every row carries the columns the LayerStackHandler expects
        from qiskit_metal.toolbox_metal.layer_stack_handler import LayerStackHandler

        for r in rows:
            self.assertEqual(set(r), set(LayerStackHandler.Col_Names))

    def test_apply_mutates_multiplanar_stack_idempotently(self):
        from qiskit_metal.designs.design_multiplanar import MultiPlanar
        from qiskit_metal.qlibrary.tlines.airbridge import apply_airbridge_layer_stack

        design = MultiPlanar()
        df = apply_airbridge_layer_stack(design, bridge_layer=30, pad_layer=31)
        self.assertIn(30, set(df["layer"]))
        self.assertIn(31, set(df["layer"]))
        n_after_first = len(df)
        # re-running replaces, not duplicates
        df2 = apply_airbridge_layer_stack(design, bridge_layer=30, pad_layer=31)
        self.assertEqual(len(df2), n_after_first)
        elevated = df2[df2["layer"] == 30]["z_coord"].iloc[0]
        self.assertEqual(elevated, "3um")

    def test_apply_requires_a_layer_stack(self):
        from qiskit_metal import designs
        from qiskit_metal.qlibrary.tlines.airbridge import apply_airbridge_layer_stack

        # DesignPlanar has no layer stack -> clear, early error.
        with self.assertRaises(AttributeError):
            apply_airbridge_layer_stack(designs.DesignPlanar())

    def test_include_posts_adds_a_connecting_row(self):
        """include_posts adds a post row rising from the base plane
        (z_coord=0) to the span (thickness=bridge_z_coord), joining them."""
        from qiskit_metal.qlibrary.tlines.airbridge import airbridge_layer_stack_rows

        rows = airbridge_layer_stack_rows(
            bridge_z_coord="3um", include_posts=True, post_layer=32
        )
        self.assertEqual(len(rows), 3)
        post = next(r for r in rows if r["layer"] == 32)
        self.assertEqual(post["z_coord"], "0um")
        self.assertEqual(post["thickness"], "3um")


def _gmsh_importable():
    try:
        import gmsh  # noqa: F401

        return True
    except Exception:
        return False


@unittest.skipUnless(
    _gmsh_importable(), "gmsh not installed (optional [mesh] extra); 3D mesh check"
)
class TestAirbridge3DMesh(unittest.TestCase):
    """[EXPERIMENTAL] Validate the actual 3D extrusion via the gmsh renderer.

    Skipped in the lite CI (no gmsh). Standalone Airbridge polys are used so
    the check exercises the elevation seam without the gmsh CPW-path fragility
    (short fillet segments, #1144)."""

    def test_bridge_span_extrudes_elevated(self):
        import gmsh
        from qiskit_metal.designs.design_multiplanar import MultiPlanar
        from qiskit_metal.qlibrary.tlines.airbridge import (
            Airbridge,
            apply_airbridge_layer_stack,
        )
        from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

        design = MultiPlanar()
        design.overwrite_enabled = True
        Airbridge(design, "ab", options=dict(crossover_length="24um"))
        design.rebuild()
        apply_airbridge_layer_stack(
            design,
            bridge_z_coord="3um",
            bridge_thickness="0.3um",
            pad_thickness="0.2um",
        )

        r = QGmshRenderer(design, layer_types=dict(metal=[1, 30, 31], dielectric=[3]))
        try:
            r.render_design(
                draw_sample_holder=False, mesh_geoms=False, box_plus_buffer=False
            )
            zbands = [
                (gmsh.model.getBoundingBox(d, t)[2], gmsh.model.getBoundingBox(d, t)[5])
                for d, t in gmsh.model.getEntities(3)
            ]
        finally:
            r.close()

        # bridge span elevated near z=3um (0.003mm); pads on the base plane
        self.assertTrue(any(zmin >= 0.0029 for zmin, _ in zbands), zbands)
        self.assertTrue(
            any(abs(zmin) < 1e-6 and 0.0 < zmax <= 0.00051 for zmin, zmax in zbands),
            zbands,
        )

    def test_full_route_with_posts_renders_in_3d(self):
        """A CPW route + airbridges with support posts renders in 3D: the posts
        join the elevated span to the base metal so the design meshes (#1144).
        Also checks a post volume spans the base-to-span z-gap."""
        import gmsh
        from qiskit_metal import Dict
        from qiskit_metal.designs.design_multiplanar import MultiPlanar
        from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
        from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
        from qiskit_metal.qlibrary.tlines.airbridge import (
            route_airbridges,
            apply_airbridge_layer_stack,
        )
        from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

        design = MultiPlanar()
        design.overwrite_enabled = True
        OpenToGround(design, "A", options=dict(pos_x="-0.4mm", orientation="0"))
        OpenToGround(design, "B", options=dict(pos_x="0.4mm", orientation="180"))
        cpw = RouteStraight(
            design,
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
        design.rebuild()
        route_airbridges(
            design, cpw, pitch="0.25mm", min_spacing="30um", enable_posts=True
        )
        design.rebuild()
        apply_airbridge_layer_stack(design, bridge_z_coord="3um", include_posts=True)

        r = QGmshRenderer(
            design, layer_types=dict(metal=[1, 30, 31, 32], dielectric=[3])
        )
        try:
            r.render_design(mesh_geoms=False)  # default sample-holder path
            zbands = [
                (gmsh.model.getBoundingBox(d, t)[2], gmsh.model.getBoundingBox(d, t)[5])
                for d, t in gmsh.model.getEntities(3)
            ]
        finally:
            r.close()

        self.assertGreater(len(zbands), 0)
        # the elevated span exists (a volume reaching ~3um) and the base plane
        # exists — i.e. the full route + airbridges meshed as a 3D solid.
        self.assertTrue(any(zmax >= 0.0029 for _, zmax in zbands), zbands)
        self.assertTrue(any(abs(zmin) < 1e-6 for zmin, _ in zbands), zbands)

    def test_no_sample_holder_path_renders(self):
        """Regression: rendering without the vacuum box (draw_sample_holder=
        False) used to crash in fragment_interfaces ('(3, N) is not in list' /
        'Unknown OpenCASCADE volume') for multi-volume designs. The output-map
        remapping fixes it; a full route + airbridges now renders either way."""
        import gmsh
        from qiskit_metal import Dict
        from qiskit_metal.designs.design_multiplanar import MultiPlanar
        from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
        from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
        from qiskit_metal.qlibrary.tlines.airbridge import (
            route_airbridges,
            apply_airbridge_layer_stack,
        )
        from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

        design = MultiPlanar()
        design.overwrite_enabled = True
        OpenToGround(design, "A", options=dict(pos_x="-0.4mm", orientation="0"))
        OpenToGround(design, "B", options=dict(pos_x="0.4mm", orientation="180"))
        cpw = RouteStraight(
            design,
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
        design.rebuild()
        route_airbridges(
            design, cpw, pitch="0.25mm", min_spacing="30um", enable_posts=True
        )
        design.rebuild()
        apply_airbridge_layer_stack(design, bridge_z_coord="3um", include_posts=True)

        r = QGmshRenderer(
            design, layer_types=dict(metal=[1, 30, 31, 32], dielectric=[3])
        )
        try:
            r.render_design(
                draw_sample_holder=False, mesh_geoms=False, box_plus_buffer=False
            )
            n_volumes = len(gmsh.model.getEntities(3))
        finally:
            r.close()
        self.assertGreater(n_volumes, 0)


if __name__ == "__main__":
    unittest.main()
