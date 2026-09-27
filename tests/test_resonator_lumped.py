# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""ResonatorLumped geometry: one connected trace, options that take effect."""

import unittest
import unittest.mock

import numpy as np
from shapely.ops import linemerge, unary_union

from qiskit_metal import designs
from qiskit_metal.qlibrary.resonators.resonator_lumped import ResonatorLumped


def _build(**options):
    design = designs.DesignPlanar()
    comp = ResonatorLumped(design, "R", options=options)
    paths = design.qgeometry.tables["path"]
    lines = list(paths[paths.component == comp.id].geometry)
    return comp, linemerge(unary_union(lines))


def _pieces(trace):
    return len(trace.geoms) if hasattr(trace, "geoms") else 1


class TestDefaultGeometryUnchanged(unittest.TestCase):
    """The defaults reproduce the geometry drawn before n_turns took effect
    (reference values from the previous, hard-coded implementation)."""

    def test_trace(self):
        _, trace = _build()
        self.assertEqual(_pieces(trace), 1)
        self.assertAlmostEqual(trace.length, 71.51238713663422, places=5)
        np.testing.assert_allclose(
            trace.bounds, (-2.399999876, -2.49, 2.399999876, 3.11), atol=1e-6
        )

    def test_pin_n_at_end_of_final(self):
        comp, _ = _build()
        np.testing.assert_allclose(comp.pins.pin_n.middle, (0.0, 3.11), atol=1e-9)
        np.testing.assert_allclose(comp.pins.pin_n.normal, (0.0, 1.0), atol=1e-9)


class TestTraceStaysConnected(unittest.TestCase):
    """The meander lines were offset by res_width while the bends used
    perimeter_thickness, and the last bend assumed initial == turn_radius,
    so changing any of them split the trace into pieces."""

    def test_options_that_used_to_split_the_trace(self):
        for options in (
            {"res_width": "0.03mm"},
            {"perimeter_thickness": "0.05mm"},
            {"initial": "0.3mm"},
        ):
            with self.subTest(**options):
                _, trace = _build(**options)
                self.assertEqual(_pieces(trace), 1)


class TestOptionsTakeEffect(unittest.TestCase):
    def test_n_turns_sets_the_length(self):
        # Each extra U-turn adds one full line plus the pitch of the turn.
        lengths = {n: _build(n_turns=str(n))[1].length for n in (4, 5, 6)}
        self.assertLess(lengths[4], lengths[5])
        self.assertAlmostEqual(
            lengths[6] - lengths[5], lengths[5] - lengths[4], places=6
        )

    def test_odd_and_even_n_turns_end_at_the_center(self):
        for n in (3, 4):
            with self.subTest(n_turns=n):
                comp, trace = _build(n_turns=str(n), final="5mm")
                self.assertEqual(_pieces(trace), 1)
                self.assertAlmostEqual(comp.pins.pin_n.middle[0], 0.0, places=9)

    def test_inner_space_sets_the_pitch(self):
        # 14 U-turns; 0.1 mm more pitch raises the top of the meander 1.4 mm.
        base, _ = _build()
        wider, _ = _build(inner_space="0.29mm")
        self.assertAlmostEqual(
            wider.pins.pin_n.middle[1] - base.pins.pin_n.middle[1], 1.4, places=6
        )


class TestWarnings(unittest.TestCase):
    def _warnings(self, **options):
        design = designs.DesignPlanar()
        comp = ResonatorLumped(design, "R", options={"n_turns": "1"})
        comp.options.update(options)
        with unittest.mock.patch.object(comp.logger, "warning") as warn:
            comp.rebuild()
        return " ".join(str(c.args[0]) for c in warn.call_args_list)

    def test_defaults_are_silent(self):
        design = designs.DesignPlanar()
        with unittest.mock.patch.object(design.logger, "warning") as warn:
            ResonatorLumped(design, "R")
        warn.assert_not_called()

    def test_final_inside_the_box(self):
        self.assertIn("ends inside the box", self._warnings(n_turns="14", final="1mm"))

    def test_trace_overlaps_perimeter(self):
        self.assertIn(
            "overlaps the perimeter", self._warnings(n_turns="14", box_height="3mm")
        )

    def test_pitch_below_bend_diameter(self):
        self.assertIn(
            "2 * turn_radius", self._warnings(n_turns="14", inner_space="0.1mm")
        )

    def test_n_turns_below_one_raises(self):
        with self.assertRaises(ValueError):
            ResonatorLumped(designs.DesignPlanar(), "R", options={"n_turns": "0"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
