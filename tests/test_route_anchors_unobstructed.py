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

"""Regression tests for RouteAnchors.unobstructed (issues #1036 and #1010).

A segment whose endpoints both lie inside a component's bounding box does not
cross any bounding-box edge. The original obstacle check only tested for edge
crossings, so such a segment skipped the contour check and was wrongly reported
as unobstructed even when it cut through a (non-rectangular) component.

The contour check itself assumed the obstacle union was a single polygon.
GeoSeries.exterior is None for a MultiPolygon or GeometryCollection, so a tee
whose buffered paths stay separate raised AttributeError: 'NoneType' object
has no attribute 'coords'.
"""

import unittest
from collections import OrderedDict

import numpy as np

from qiskit_metal import designs
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee
from qiskit_metal.qlibrary.couplers.line_tee import LineTee
from qiskit_metal.qlibrary.sample_shapes.n_gon import NGon
from qiskit_metal.qlibrary.tlines.anchored_path import RouteAnchors
from qiskit_metal.qlibrary.tlines.mixed_path import RouteMixed


class TestRouteAnchorsUnobstructed(unittest.TestCase):
    """Check obstacle detection for segments contained in a bounding box."""

    @staticmethod
    def _design_with_circle_obstacle():
        """A ~circular obstacle (24-gon, radius 0.5 mm) at the origin, whose
        bounding box ([-0.5, 0.5] in x and y) is strictly larger than its
        contour. Returns (design, route)."""
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        NGon(
            design,
            "obstacle",
            options=dict(n="24", radius="0.5mm", pos_x="0mm", pos_y="0mm"),
        )
        # make=False: we only need the unobstructed() helper, not a routed path.
        route = RouteAnchors(design, "r", options=dict(), make=False)
        return design, route

    def test_contained_segment_crossing_contour_is_obstructed(self):
        """Both endpoints inside the bbox but outside the circle, with the chord
        cutting through the circle -> obstructed (regression for #1036)."""
        _, route = self._design_with_circle_obstacle()
        segment = [np.array([-0.45, 0.45]), np.array([0.45, 0.45])]
        self.assertFalse(route.unobstructed(segment))

    def test_segment_clear_of_obstacle_is_unobstructed(self):
        """A segment well outside the bounding box stays unobstructed."""
        _, route = self._design_with_circle_obstacle()
        segment = [np.array([2.0, 2.0]), np.array([3.0, 2.0])]
        self.assertTrue(route.unobstructed(segment))

    def test_route_mixed_into_linetee_builds(self):
        """Smoke test for the issue #1010 setup: RouteMixed between LineTee
        second_end pins, with anchors and avoid_collision, builds and stores a
        trace. This also passes without the fix; the regression test is
        test_segment_missing_multipart_rings_is_unobstructed."""
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        LineTee(design, "Lt1", options=dict(pos_x="500um"))
        LineTee(design, "Lt2", options=dict(pos_x="-500um"))
        LineTee(
            design,
            "Lt3",
            options=dict(orientation="90", pos_x="-2500um"),
        )
        LineTee(
            design,
            "Lt4",
            options=dict(orientation="270", pos_x="2500um"),
        )
        anchors = OrderedDict()
        anchors[0] = np.array([1.5, 1.0])
        anchors[1] = np.array([0.0, 2.0])
        anchors[2] = np.array([3.0, 3.0])
        between_anchors = OrderedDict()
        between_anchors[0] = "S"
        between_anchors[1] = "M"
        between_anchors[2] = "S"
        between_anchors[3] = "S"
        line = RouteMixed(
            design,
            "line",
            options=dict(
                pin_inputs=dict(
                    start_pin=dict(component="Lt2", pin="second_end"),
                    end_pin=dict(component="Lt3", pin="second_end"),
                ),
                total_length="2mm",
                chip="main",
                layer="1",
                trace_width="cpw_width",
                step_size="0.25mm",
                anchors=anchors,
                between_anchors=between_anchors,
                advanced=dict(avoid_collision="true"),
                meander=dict(spacing="200um", asymmetry="0um"),
                snap="true",
                lead=dict(start_straight="0.3mm", end_straight="0.3mm"),
            ),
        )
        self.assertEqual(line.status, "good")
        paths = line.qgeometry_table("path")
        self.assertGreater(len(paths.index), 0)
        self.assertTrue(any(geom.length > 0 for geom in paths.geometry))

    def test_linetee_bbox_segment_does_not_raise(self):
        """Smoke test: a segment across a LineTee bounding box returns a bool;
        one far from the tee stays unobstructed. This also passes without the
        #1010 fix; the regression test is
        test_segment_missing_multipart_rings_is_unobstructed."""
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        LineTee(design, "tee")
        route = RouteAnchors(design, "r", options=dict(), make=False)
        crossed = route.unobstructed([np.array([-0.2, 0.0]), np.array([0.2, 0.0])])
        self.assertIsInstance(crossed, bool)
        self.assertFalse(crossed)
        # Inside the bounding box, beside the stub: misses every exterior ring.
        self.assertTrue(
            route.unobstructed([np.array([-0.04, -0.04]), np.array([-0.02, -0.04])])
        )
        self.assertTrue(
            route.unobstructed([np.array([2.0, 2.0]), np.array([3.0, 2.0])])
        )

    def test_segment_missing_multipart_rings_is_unobstructed(self):
        """Buffered paths that union to more than one polygon must not raise
        'NoneType' object has no attribute 'coords'. A segment that only clips
        the bounding box and misses every exterior ring stays unobstructed."""
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        # The hanger is separated from the primary CPW by coupling_space, so
        # the buffered union is a MultiPolygon.
        CoupledLineTee(design, "tee")
        route = RouteAnchors(design, "r", options=dict(), make=False)
        # Through the primary trace: crosses one exterior ring.
        self.assertFalse(
            route.unobstructed([np.array([-0.2, 0.0]), np.array([0.2, 0.0])])
        )
        # In the coupling gap: inside the bounding box, between the two rings.
        self.assertTrue(
            route.unobstructed([np.array([-0.03, -0.0125]), np.array([0.02, -0.0125])])
        )


if __name__ == "__main__":
    unittest.main()
