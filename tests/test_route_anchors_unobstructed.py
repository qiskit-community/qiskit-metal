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

"""Regression tests for RouteAnchors.unobstructed (issue #1036).

A segment whose endpoints both lie inside a component's bounding box does not
cross any bounding-box edge. The original obstacle check only tested for edge
crossings, so such a segment skipped the contour check and was wrongly reported
as unobstructed even when it cut through a (non-rectangular) component.
"""

import unittest

import numpy as np

from qiskit_metal import designs
from qiskit_metal.qlibrary.sample_shapes.n_gon import NGon
from qiskit_metal.qlibrary.tlines.anchored_path import RouteAnchors


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


if __name__ == "__main__":
    unittest.main()
