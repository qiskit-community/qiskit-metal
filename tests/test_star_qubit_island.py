"""StarQubit's island has no floating fragments.

The island is a disc with one trapezoid cut per arm. With a readout arm 45
degrees from its neighbors, adjacent cuts overlap near the center but leave a
thin gap near the rim, and the subtraction used to leave two detached
triangles of island metal beside the readout pad.
"""

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


if __name__ == "__main__":
    unittest.main()
