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
"""Geometry/topology tests for the SNAIL qlibrary component.

A SNAIL (Superconducting Nonlinear Asymmetric Inductive eLement) is
distinguished from an ordinary two-junction SQUID by its loop topology:
three large Josephson junctions in series on one arm and a single smaller
junction on the other. These tests assert that the drawn geometry actually
realises that topology — i.e. that the conducting metal is broken into the
right number of islands by the right number of junction gaps — rather than
just that the component instantiates (covered by the standard qlibrary
suite).
"""

import unittest

from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.SNAIL import SNAIL


def _islands(component):
    """Return the disconnected conducting islands of a component's poly
    geometry as a list of shapely polygons. Each island is a piece of
    metal galvanically isolated from the others by a junction gap."""
    geoms = list(component.qgeometry_table("poly")["geometry"])
    merged = unary_union(geoms)
    if isinstance(merged, MultiPolygon):
        return list(merged.geoms)
    return [merged]


class TestSNAILGeometry(unittest.TestCase):
    """Topology and dimensional checks for SNAIL."""

    def setUp(self):
        self.design = designs.DesignPlanar()

    def test_four_islands_three_large_one_small_junctions(self):
        """A SNAIL loop is broken by four junctions (three large + one
        small) into exactly four superconducting islands: the left node,
        two intermediate islands between the large junctions, and the
        right node. This is what distinguishes it from a SQUID (two
        islands / two junctions)."""
        snail = SNAIL(self.design, "S1")
        islands = _islands(snail)
        self.assertEqual(
            len(islands),
            4,
            "SNAIL should resolve into 4 conducting islands "
            "(3 large + 1 small junction); got %d" % len(islands),
        )

    def test_all_geometry_valid(self):
        """Every drawn polygon must be a valid (non-self-intersecting)
        shapely geometry so downstream renderers/GDS export don't choke."""
        snail = SNAIL(self.design, "S1")
        for geom in snail.qgeometry_table("poly")["geometry"]:
            self.assertTrue(geom.is_valid)

    def test_loop_closes_on_common_connector(self):
        """The (longer) upper arm and the (shorter, padded) lower arm must
        both terminate on the same vertical connector so the loop closes.
        With default options the right node is a single connected island,
        which is only true if both arms reach it."""
        snail = SNAIL(self.design, "S1")
        p = snail.parse_options()
        islands = _islands(snail)

        # Right edge of the whole device = far edge of plate2.
        device_right = max(isl.bounds[2] for isl in islands)
        # The island that touches the far right edge is the "right node".
        right_node = max(islands, key=lambda isl: isl.bounds[2])

        # The right node must span the full loop height (both arms feed
        # into it), i.e. its vertical extent must exceed the squid_gap.
        miny, maxy = right_node.bounds[1], right_node.bounds[3]
        self.assertGreater(
            maxy - miny,
            p.squid_gap,
            "Right node does not span both arms — loop did not close.",
        )
        self.assertAlmostEqual(device_right, right_node.bounds[2])

    def test_realistic_footprint_dimensions(self):
        """Sanity check on the realistic dimensions: with default options
        the overall device is on the order of tens of microns and the loop
        encloses a finite area (needed for flux tunability)."""
        snail = SNAIL(self.design, "S1")
        islands = _islands(snail)
        full = unary_union(islands)
        minx, miny, maxx, maxy = full.bounds

        width_um = (maxx - minx) * 1e3  # internal units are mm
        height_um = (maxy - miny) * 1e3
        # Realistic SNAIL footprint: tens of microns across.
        self.assertGreater(width_um, 30.0)
        self.assertLess(width_um, 200.0)
        self.assertGreater(height_um, 20.0)
        self.assertLess(height_um, 200.0)

    def test_custom_junction_count_spacing_preserves_topology(self):
        """Changing junction gaps / island lengths must not change the
        four-island topology — the lower arm is auto-padded to keep the
        loop closed for any reasonable choice of dimensions."""
        snail = SNAIL(
            self.design,
            "S2",
            options=dict(
                JJ_gap="0.25um",
                JJ_gap_small="0.15um",
                segment_ab_length="3um",
                segment_b_length="8um",
            ),
        )
        self.assertEqual(len(_islands(snail)), 4)

    def test_large_small_junction_gap_keeps_loop_closed(self):
        """Regression: a large ``JJ_gap_small`` (small junction wider than
        the upper-arm tail) must not silently break the loop. The small
        junction is centred on the lower arm, so the loop stays a single
        closed ring of exactly four islands instead of spawning an extra
        inverted/degenerate piece."""
        snail = SNAIL(
            self.design,
            "S4",
            options=dict(
                segment_a_length="3um",
                segment_ab_length="2um",
                segment_b_length="2um",
                JJ_gap="0.3um",
                JJ_gap_small="6um",
            ),
        )
        islands = _islands(snail)
        self.assertEqual(
            len(islands),
            4,
            "Large small-junction gap broke the loop topology; got %d "
            "islands" % len(islands),
        )
        for isl in islands:
            self.assertTrue(isl.is_valid)
            self.assertGreater(isl.area, 0.0)

    def test_rotation_and_translation(self):
        """The component must build cleanly when rotated/translated and
        keep its topology (regression against union/translate dropping
        geometry)."""
        snail = SNAIL(
            self.design,
            "S3",
            options=dict(pos_x="0.5mm", pos_y="-0.2mm", orientation="90"),
        )
        islands = _islands(snail)
        self.assertEqual(len(islands), 4)
        for isl in islands:
            self.assertTrue(isl.is_valid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
