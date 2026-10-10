# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Cheese holes that straddle the no-cheese keep-out are dropped (#1214).

Subtracting the keep-out from the hole grid used to trim edge holes into
etched slivers 1-1.5 um wide (below the 2 um spacing rule) whenever the
grid fell just inside the keep-out edge.
"""

import os
import tempfile
import unittest

import numpy as np
import shapely

from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight


def _export(y0):
    design = designs.DesignPlanar()
    design.chips.main.size.update(size_x="2mm", size_y="2mm")
    OpenToGround(
        design, "A", options=dict(pos_x="-0.5mm", pos_y=f"{y0}mm", orientation="180")
    )
    OpenToGround(
        design, "B", options=dict(pos_x="0.5mm", pos_y=f"{y0}mm", orientation="0")
    )
    RouteStraight(
        design,
        "L",
        options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(component="A", pin="open"),
                end_pin=Dict(component="B", pin="open"),
            )
        ),
    )
    design.rebuild()
    gds = design.renderers.gds
    out = os.path.join(tempfile.mkdtemp(), "c.gds")
    assert gds.export_to_gds(out) == 1
    cells = {c.name: c for c in gds.lib.cells}
    holes = [
        shapely.Polygon(p.points) for p in cells["TOP_main_1_Cheese_diff"].polygons
    ]
    keepout = shapely.union_all(
        [shapely.Polygon(p.points) for p in cells["TOP_main_1_NoCheese_99"].polygons]
    )
    hole_side = float(design.parse_value(gds.options.cheese.cheese_0_x))
    return holes, keepout, hole_side


class TestCheeseKeepoutEdge(unittest.TestCase):
    def test_no_trimmed_holes_when_grid_straddles_keepout(self):
        # y0 = 24.5 um puts a row of holes 1 um inside the keep-out edge.
        holes, keepout, side = _export(0.0245)
        self.assertTrue(holes)
        areas = np.array([h.area for h in holes])
        np.testing.assert_allclose(areas, side**2, rtol=1e-6)
        overlap = [h.intersection(keepout).area for h in holes]
        self.assertLess(max(overlap), 1e-12)

    def test_holes_clear_of_keepout_are_kept(self):
        # Holes that sit outside the keep-out are unaffected by the change.
        aligned, _, _ = _export(0.0)
        shifted, _, _ = _export(0.0245)
        self.assertEqual(len(aligned), 245)
        self.assertEqual(len(shifted), 245)


if __name__ == "__main__":
    unittest.main()
