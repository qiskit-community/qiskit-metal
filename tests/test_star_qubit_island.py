"""StarQubit's island has no floating fragments.

The island is a disc with one trapezoid cut per arm. With a readout arm 45
degrees from its neighbors, adjacent cuts overlap near the center but leave a
thin gap near the rim, and the subtraction used to leave two detached
triangles of island metal beside the readout pad.
"""

import math
import unittest

from shapely.geometry import Point

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.star_qubit import StarQubit

# The arm geometry of the 17-qubit surface-code example, which showed the bug.
SCALED = dict(
    radius="160um",
    center_radius="53um",
    gap_couplers="13um",
    gap_readout="6um",
    connector_length="40um",
    trap_offset="11um",
    junc_h="53um",
    number_of_connectors="4",
    resolution="16",
    rotation_cpl1="90",
    rotation_cpl2="180",
    rotation_rdout="135",
    rotation_cpl3="270",
    rotation_cpl4="0",
)


def _island_parts(design, qubit):
    tbl = design.qgeometry.tables["poly"]
    rows = tbl[(tbl.component == qubit.id) & tbl.name.str.startswith("circle_inner")]
    return list(rows.geometry)


class TestStarQubitIsland(unittest.TestCase):
    def test_no_sliver_fragments(self):
        design = designs.DesignPlanar()
        q = StarQubit(design, "Q", options=SCALED)
        parts = _island_parts(design, q)
        center = Point(0, 0)
        island = [g for g in parts if g.contains(center)]
        self.assertEqual(len(island), 1)
        # Anything else is a junction lead (gap_couplers x center_radius),
        # never a sliver.
        lead_area = 0.013 * 0.053
        for g in parts:
            if g is not island[0]:
                self.assertAlmostEqual(g.area, lead_area, places=9)

    def test_default_geometry_unchanged(self):
        design = designs.DesignPlanar()
        q = StarQubit(design, "Q")
        parts = _island_parts(design, q)
        self.assertEqual(len(parts), 1)
        self.assertTrue(parts[0].contains(Point(0, 0)))


def _junction(design, qubit):
    tbl = design.qgeometry.tables["junction"]
    return tbl[tbl.component == qubit.id].geometry.iloc[0]


class TestStarQubitJunctionRotation(unittest.TestCase):
    def test_auto_matches_previous_placement(self):
        design = designs.DesignPlanar()
        auto = StarQubit(design, "A")
        explicit = StarQubit(design, "B", options=dict(rotation_jj="180"))
        # Default rotation_cpl1 is 0: 'auto' is the old "opposite coupler 1".
        self.assertTrue(
            _junction(design, auto).equals_exact(_junction(design, explicit), 1e-12)
        )

    def test_junction_lands_at_theta_for_theta_plus_90(self):
        for theta in (45, 135, 225, 315):
            design = designs.DesignPlanar()
            q = StarQubit(design, "Q", options=dict(rotation_jj=str(theta + 90)))
            c = _junction(design, q).centroid
            angle = math.degrees(math.atan2(c.y, c.x)) % 360
            self.assertAlmostEqual(angle, theta, delta=1.0, msg=f"theta={theta}")

    def test_leads_touch_the_island_between_arms(self):
        # On the scaled chip qubit the free diagonal is 225 degrees.
        design = designs.DesignPlanar()
        q = StarQubit(design, "Q", options=dict(SCALED, rotation_jj="315"))
        parts = _island_parts(design, q)
        self.assertEqual(len(parts), 1, "junction leads float off the island")


if __name__ == "__main__":
    unittest.main()
