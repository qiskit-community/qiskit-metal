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
"""Issue #1224 -- ``ReadoutResFC`` etches the ground plane of its own layer.

The default ``layer_subtract="2"`` put the etch on layer 2 while the trace was
on layer 1, so the GDS export had the trace on layer 1 with no ground around
it and an extra layer-2 ground plane with the CPW gap cut. An empty
``layer_subtract`` (the new default) follows ``layer``; an explicit value is
still honoured.
"""

import os
import tempfile
import unittest
from collections import Counter

import gdstk

from qiskit_metal import designs
from qiskit_metal.qlibrary.resonators.readoutres_fc import ReadoutResFC


def _flipchip_with_resonator(**options):
    design = designs.DesignFlipChip()
    design.overwrite_enabled = True
    ReadoutResFC(design, "R1", options=dict(chip="C_chip", **options))
    return design


def _export_layers(design) -> Counter:
    """(layer, datatype) -> polygon count in the exported top cell."""
    gds = design.renderers.gds
    view = {"C_chip": {1: False, 2: False}, "Q_chip": {1: False}}
    gds.options.cheese.view_in_file = view
    gds.options.no_cheese.view_in_file = view
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "fc.gds")
        gds.export_to_gds(path)
        lib = gdstk.read_gds(path)
    top = lib.top_level()[0]
    return Counter((p.layer, p.datatype) for p in top.flatten().polygons)


class TestReadoutResFCLayers(unittest.TestCase):
    def test_default_etch_on_trace_layer(self):
        design = _flipchip_with_resonator()
        poly = design.qgeometry.tables["poly"]
        self.assertEqual(set(poly["layer"]), {1}, poly[["name", "layer"]])
        self.assertTrue(poly[poly["name"].str.startswith("ro_etch")]["subtract"].all())

    def test_default_gds_has_ground_with_gap_on_trace_layer(self):
        layers = _export_layers(_flipchip_with_resonator())
        self.assertEqual({layer for layer, _ in layers}, {1}, layers)
        # datatype 0 is the ground plane with the CPW gap cut, 10 the trace
        self.assertIn((1, 0), layers)
        self.assertIn((1, 10), layers)

    def test_layer_subtract_follows_layer(self):
        design = _flipchip_with_resonator(layer="3")
        self.assertEqual(set(design.qgeometry.tables["poly"]["layer"]), {3})

    def test_explicit_layer_subtract_is_honoured(self):
        design = _flipchip_with_resonator(layer_subtract="2")
        poly = design.qgeometry.tables["poly"]
        layer_of = dict(zip(poly["name"], poly["layer"]))
        self.assertEqual(layer_of["ro"], 1)
        self.assertTrue(
            all(v == 2 for k, v in layer_of.items() if k.startswith("ro_etch"))
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
