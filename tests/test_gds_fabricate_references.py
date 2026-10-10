# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""``fabricate=True`` with cheesing must not leave dangling references (#1218).

``gdstk.Library.remove`` keeps references to the removed cell in their
parents, so the cheesing clean-up used to write a file referencing
``ground_main_1``, ``TOP_main_1_one_hole`` and ``TOP_main_1_Cheese_diff``,
cells it no longer contained.
"""

import os
import tempfile
import unittest
import warnings

import gdstk

from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
from qiskit_metal.renderers.renderer_gds.gds_boolean import remove_cell


def _design():
    design = designs.DesignPlanar()
    design.chips.main.size.size_x = "2mm"
    design.chips.main.size.size_y = "2mm"
    OpenToGround(
        design, "o1", options=dict(pos_x="-0.5mm", pos_y="0mm", orientation="180")
    )
    OpenToGround(
        design, "o2", options=dict(pos_x="0.5mm", pos_y="0mm", orientation="0")
    )
    RouteStraight(
        design,
        "cpw",
        options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(component="o1", pin="open"),
                end_pin=Dict(component="o2", pin="open"),
            )
        ),
    )
    design.rebuild()
    return design


def _dangling(lib):
    names = {c.name for c in lib.cells}
    return sorted(
        (c.name, r.cell.name)
        for c in lib.cells
        for r in c.references
        if not isinstance(r.cell, str) and r.cell.name not in names
    )


class TestRemoveCell(unittest.TestCase):
    def test_remove_cell_drops_references(self):
        lib = gdstk.Library()
        child = lib.new_cell("child")
        child.add(gdstk.rectangle((0, 0), (1, 1)))
        keep = lib.new_cell("keep")
        parent = lib.new_cell("parent")
        parent.add(gdstk.Reference(child), gdstk.Reference(keep))
        remove_cell(lib, child)
        self.assertEqual(sorted(c.name for c in lib.cells), ["keep", "parent"])
        self.assertEqual([r.cell.name for r in parent.references], ["keep"])


class TestFabricateReferences(unittest.TestCase):
    def _export(self, negative):
        design = _design()
        gds = design.renderers.gds
        gds.options.fabricate = "True"
        if negative:
            gds.options.negative_mask = Dict(main=[1])
        out = os.path.join(tempfile.mkdtemp(), "fab.gds")
        self.assertEqual(gds.export_to_gds(out), 1)
        return gds.lib, out

    def _check(self, negative):
        lib, out = self._export(negative)
        self.assertEqual(_dangling(lib), [])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            read = gdstk.read_gds(out)
        self.assertEqual([str(w.message) for w in caught], [])
        return read

    def test_positive_mask(self):
        read = self._check(negative=False)
        layers = {
            (p.layer, p.datatype)
            for c in read.top_level()
            for p in c.get_polygons()
            if p.layer == 1
        }
        # cheesed ground (datatype 100) still exported
        self.assertIn((1, 100), layers)

    def test_negative_mask(self):
        self._check(negative=True)


if __name__ == "__main__":
    unittest.main()
