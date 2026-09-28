# This code is part of Quantum Metal.
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
"""Tests for PolylineCPW."""

import unittest

import numpy as np

from qiskit_metal import designs
from qiskit_metal.qlibrary.tlines.polyline_cpw import PolylineCPW

SQUARE_ISH = [[0, 0], [1, 0], [1.7, 0.7], [2.5, 0.7]]


class TestPolylineCPW(unittest.TestCase):
    """Unit tests for the PolylineCPW component."""

    def setUp(self):
        self.design = designs.DesignPlanar()
        self.design.overwrite_enabled = True

    def test_draws_the_points_it_is_given(self):
        """Geometry follows the polyline, including a non-Manhattan segment."""
        c = PolylineCPW(self.design, "p", options=dict(points=SQUARE_ISH))
        geom = self.design.qgeometry.tables["path"]
        trace = geom[geom["component"] == c.id].iloc[0].geometry
        self.assertAlmostEqual(trace.length, 1 + np.hypot(0.7, 0.7) + 0.8, places=6)

    def test_pins_sit_at_the_ends_and_face_outward(self):
        """start/end pins land on the terminal vertices, normals pointing away."""
        c = PolylineCPW(self.design, "p", options=dict(points=SQUARE_ISH))
        np.testing.assert_allclose(c.pins["start"]["middle"], [0, 0], atol=1e-9)
        np.testing.assert_allclose(c.pins["end"]["middle"], [2.5, 0.7], atol=1e-9)
        np.testing.assert_allclose(c.pins["start"]["normal"], [-1, 0], atol=1e-9)
        np.testing.assert_allclose(c.pins["end"]["normal"], [1, 0], atol=1e-9)

    def test_min_segment_drops_crowded_vertices_but_keeps_the_last(self):
        """Short hops are removed; the final vertex always survives.

        The endpoint is kept by dropping the interior vertex BEFORE it, so no
        segment -- including the last -- ends up shorter than min_segment.
        """
        pts = [[0, 0], [0.01, 0], [0.02, 0], [1, 0], [1.005, 0]]
        c = PolylineCPW(self.design, "p", options=dict(points=pts, min_segment="0.1"))
        np.testing.assert_allclose(c.pins["end"]["middle"], [1.005, 0], atol=1e-9)
        geom = self.design.qgeometry.tables["path"]
        trace = np.array(geom[geom["component"] == c.id].iloc[0].geometry.coords)
        np.testing.assert_allclose(trace, [[0, 0], [1.005, 0]], atol=1e-9)
        self.assertGreaterEqual(
            np.linalg.norm(np.diff(trace, axis=0), axis=1).min(), 0.1
        )

    def test_short_final_hop_does_not_starve_the_fillet(self):
        """One short last segment must not shrink the fillet for the whole line.

        The fillet is clamped to half the shortest segment. Keeping a short
        final hop used to cut a 20 um request to ~11 um on a real resonator.
        """
        pts = [[0, 0], [0.2, 0], [0.2, 0.2], [0.4, 0.2], [0.405, 0.2]]
        c = PolylineCPW(
            self.design,
            "p",
            options=dict(points=pts, fillet="0.02", min_segment="0.045"),
        )
        geom = self.design.qgeometry.tables["path"]
        self.assertAlmostEqual(geom[geom["component"] == c.id].iloc[0].fillet, 0.02)
        np.testing.assert_allclose(c.pins["end"]["middle"], [0.405, 0.2], atol=1e-9)

    def test_fillet_clamped_to_half_the_shortest_segment(self):
        """An over-large fillet is reduced rather than producing bad geometry."""
        c = PolylineCPW(
            self.design,
            "p",
            options=dict(points=[[0, 0], [0.2, 0], [0.2, 1]], fillet="0.5"),
        )
        geom = self.design.qgeometry.tables["path"]
        self.assertLessEqual(geom[geom["component"] == c.id].iloc[0].fillet, 0.1)

    def test_tap_sits_on_the_line_and_faces_the_target(self):
        """A tap lands at the nearest point on the line, normal toward the target."""
        c = PolylineCPW(
            self.design,
            "p",
            options=dict(points=[[0, 0], [1, 0]], taps=dict(branch=[0.4, 0.3])),
        )
        np.testing.assert_allclose(c.pins["branch"]["middle"], [0.4, 0], atol=1e-9)
        np.testing.assert_allclose(c.pins["branch"]["normal"], [0, 1], atol=1e-9)
        c2 = PolylineCPW(
            self.design,
            "q",
            options=dict(points=[[0, 0], [1, 0]], taps=dict(branch=[0.4, -0.3])),
        )
        np.testing.assert_allclose(c2.pins["branch"]["normal"], [0, -1], atol=1e-9)

    def test_branch_on_a_tap_needs_no_waiver(self):
        """Connecting a stub to a tap registers the joint, so DRC sees no short.

        This is what taps are for: without one, a stub joined to the middle of
        a line reports as a metal-overlap error that has to be waived.
        """
        from qiskit_metal.validation import validate

        line = PolylineCPW(
            self.design,
            "line",
            options=dict(points=[[0, 0], [1, 0]], taps=dict(t=[0.5, 0.2])),
        )
        stub = PolylineCPW(
            self.design,
            "stub",
            options=dict(points=[list(line.pins["t"]["middle"]), [0.5, 0.2]]),
        )
        unconnected = validate(self.design)
        self.assertTrue(any(f.rule == "metal-overlap" for f in unconnected.errors))
        self.design.connect_pins(line.id, "t", stub.id, "start")
        self.assertFalse(
            any(f.rule == "metal-overlap" for f in validate(self.design).errors)
        )

    def test_tap_rejects_reserved_names_and_on_line_targets(self):
        """'start'/'end' are taken; a target on the line gives no side."""
        with self.assertRaises(ValueError):
            PolylineCPW(
                self.design,
                "p",
                options=dict(points=[[0, 0], [1, 0]], taps=dict(start=[0.5, 0.2])),
            )
        with self.assertRaises(ValueError):
            PolylineCPW(
                self.design,
                "q",
                options=dict(points=[[0, 0], [1, 0]], taps=dict(t=[0.5, 0.0])),
            )

    def test_needs_at_least_two_points(self):
        """A single point is not a path."""
        with self.assertRaises(ValueError):
            PolylineCPW(self.design, "p", options=dict(points=[[0, 0]]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
