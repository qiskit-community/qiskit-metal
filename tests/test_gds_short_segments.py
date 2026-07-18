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
"""Regression tests for GDS export of routes with short segments (#1141)."""

import os
import tempfile
import unittest

import gdstk

from qiskit_metal import designs, Dict
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander


class TestGdsShortSegments(unittest.TestCase):
    """A meander whose lead segments are shorter than the fillet exercises
    `_fix_short_segments_within_table`. Before #1141 this raised — first a
    pandas-2 `DataFrame.append` AttributeError, then a `gdstk.boolean` error
    from positional indexing of a duplicate-labelled pandas Series."""

    def _meander_design(self, fillet):
        design = designs.DesignPlanar()
        OpenToGround(design, "A", options=dict(pos_x="-1mm", orientation="0"))
        OpenToGround(design, "B", options=dict(pos_x="1mm", orientation="180"))
        RouteMeander(
            design,
            "cpw",
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component="A", pin="open"),
                    end_pin=Dict(component="B", pin="open"),
                ),
                total_length="8mm",
                fillet=fillet,
                trace_width="10um",
                trace_gap="6um",
                meander=Dict(spacing="0.3mm"),
            ),
        )
        design.rebuild()
        return design

    def test_meander_with_short_segments_exports(self):
        design = self._meander_design("90um")
        path = os.path.join(tempfile.mkdtemp(), "m.gds")
        design.renderers.gds.export_to_gds(path)  # raised before #1141
        self.assertTrue(os.path.exists(path))
        self.assertGreater(os.path.getsize(path), 0)

        lib = gdstk.read_gds(path)
        polys = sum(len(c.polygons) for c in lib.cells)
        self.assertGreater(polys, 0)

    def test_area_matches_low_fillet_control(self):
        """The short-segment path must produce the same geometry (to within
        the fillet's small area change) as a design that avoids it."""

        def total_area(design):
            path = os.path.join(tempfile.mkdtemp(), "x.gds")
            design.renderers.gds.export_to_gds(path)
            lib = gdstk.read_gds(path)
            return sum(abs(p.area()) for c in lib.cells for p in c.polygons)

        a_short = total_area(self._meander_design("90um"))
        a_ctrl = total_area(self._meander_design("30um"))
        self.assertGreater(a_short, 0)
        self.assertAlmostEqual(a_short, a_ctrl, delta=0.01 * a_ctrl)


if __name__ == "__main__":
    unittest.main()
