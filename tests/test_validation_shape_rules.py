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
"""Tests for the single-path shape rules (SHAPE_RULES).

Each fixture is a minimal version of a defect that reached a real layout (a
traced 17-qubit device) with every pairwise rule passing.
"""

import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.tlines.polyline_cpw import PolylineCPW
from qiskit_metal.validation import (
    DEFAULT_RULES,
    SHAPE_RULES,
    DanglingEndRule,
    FilletStarvationRule,
    PinAlignmentRule,
    SelfIntersectionRule,
    SharpTurnRule,
    validate,
)

MEANDER = [[0, 0], [0.3, 0], [0.3, 0.2], [0.6, 0.2], [0.6, 0], [0.9, 0]]


def _run(design, rule):
    return list(rule.check(design))


class TestShapeRules(unittest.TestCase):
    """Unit tests for SelfIntersection/SharpTurn/FilletStarvation/DanglingEnd."""

    def setUp(self):
        self.design = designs.DesignPlanar()
        self.design.overwrite_enabled = True

    def line(self, name, pts, **kw):
        return PolylineCPW(self.design, name, options=dict(points=pts, **kw))

    # --- self-intersection ---------------------------------------------------
    def test_line_that_doubles_back_is_flagged(self):
        """A feedline that ran past its joint and back over itself."""
        self.line("spur", [[0, 0], [0, 0.3], [0, 0.08], [0.2, -0.1]])
        f = _run(self.design, SelfIntersectionRule())
        self.assertEqual(len(f), 1)
        self.assertIsNotNone(f[0].location)

    def test_crossing_itself_is_flagged(self):
        """A figure-of-eight crosses itself."""
        self.line("x", [[0, 0], [1, 1], [1, 0], [0, 1]])
        self.assertEqual(len(_run(self.design, SelfIntersectionRule())), 1)

    def test_meander_is_not_a_self_intersection(self):
        """Ordinary right-angle meanders are simple."""
        self.line("m", MEANDER)
        self.assertEqual(_run(self.design, SelfIntersectionRule()), [])

    # --- sharp turn ----------------------------------------------------------
    def test_hook_at_a_joint_is_flagged(self):
        """A traced line that steps out 15 um and back before heading off."""
        self.line("hook", [[0, 0], [0.1, 0], [0.085, 0.001], [0.085, -0.2]])
        f = _run(self.design, SharpTurnRule())
        self.assertTrue(f)
        self.assertGreater(f[0].value, 135)

    def test_right_angle_corners_are_fine(self):
        """90-degree corners are well inside the default limit."""
        self.line("m", MEANDER)
        self.assertEqual(_run(self.design, SharpTurnRule()), [])

    # --- fillet starvation -----------------------------------------------------
    def test_one_short_segment_starves_the_fillet(self):
        """A 10 um segment clamps a 20 um request to 5 um for the whole path."""
        self.line("s", [[0, 0], [0.5, 0], [0.51, 0], [0.51, 0.5]], fillet="20um")
        f = _run(self.design, FilletStarvationRule())
        self.assertEqual(len(f), 1)
        self.assertLess(f[0].value, f[0].limit)

    def test_fillet_that_fits_is_not_flagged(self):
        """Long segments get the full requested fillet."""
        self.line("m", MEANDER, fillet="20um")
        self.assertEqual(_run(self.design, FilletStarvationRule()), [])

    # --- dangling end ----------------------------------------------------------
    def test_unconnected_ends_are_flagged(self):
        """Both ends of a lone CPW butt the ground plane."""
        self.line("lone", [[0, 0], [1, 0]])
        f = _run(self.design, DanglingEndRule())
        self.assertEqual(len(f), 2)

    def test_terminated_end_is_not_flagged(self):
        """An end wired to an OpenToGround is terminated on purpose."""
        ln = self.line("ln", [[0, 0], [1, 0]])
        op = OpenToGround(self.design, "op", options=dict(pos_x="1mm", pos_y="0mm"))
        self.design.connect_pins(ln.id, "end", op.id, "open")
        f = _run(self.design, DanglingEndRule())
        self.assertEqual([x.location for x in f], [(0.0, 0.0)])

    def test_unconnected_tap_is_not_an_end(self):
        """Mid-line tap pins are not path ends."""
        a = self.line("a", [[0, 0], [1, 0]], taps=dict(t=[0.5, 0.2]))
        b = self.line("b", [[1, 0], [2, 0]])
        self.design.connect_pins(a.id, "end", b.id, "start")
        names = {x.location for x in _run(self.design, DanglingEndRule())}
        self.assertEqual(names, {(0.0, 0.0), (2.0, 0.0)})

    # --- pin alignment ---------------------------------------------------------
    def _joined(self, first, second):
        a = self.line("a", first)
        b = self.line("b", second)
        self.design.connect_pins(a.id, "end", b.id, "start")
        return _run(self.design, PinAlignmentRule())

    def test_straight_continuation_is_square_on(self):
        self.assertEqual(self._joined([[0, 0], [1, 0]], [[1, 0], [2, 0]]), [])

    def test_line_leaving_a_pin_at_an_angle_is_flagged(self):
        """The 17-qubit couplers left their pads 40-80 degrees off the pin."""
        f = self._joined([[0, 0], [1, 0]], [[1, 0], [1.5, 0.3]])
        self.assertTrue(f)
        self.assertTrue(all(x.rule == "pin-alignment" for x in f))
        self.assertAlmostEqual(max(x.value for x in f), 30.96, places=1)

    def test_line_starting_off_its_pin_is_flagged(self):
        f = self._joined([[0, 0], [1, 0]], [[1, 0.001], [2, 0.001]])
        self.assertTrue(any("um from" in x.message for x in f))

    def test_terminated_end_is_square_on(self):
        """OpenToGround's pin faces back into the line it terminates."""
        ln = self.line("ln", [[0, 0], [1, 0]])
        op = OpenToGround(
            self.design, "op", options=dict(pos_x="1mm", pos_y="0mm", orientation="0")
        )
        self.design.connect_pins(ln.id, "end", op.id, "open")
        self.assertEqual(_run(self.design, PinAlignmentRule()), [])

    def test_branch_off_a_tap(self):
        """A branch must leave a tap perpendicular to the line."""
        a = self.line("a", [[0, 0], [1, 0]], taps=dict(t=[0.5, 0.2]))
        square = self.line("square", [[0.5, 0], [0.5, 0.4]])
        self.design.connect_pins(a.id, "t", square.id, "start")
        self.assertEqual(_run(self.design, PinAlignmentRule()), [])
        self.design.delete_component("square")
        askew = self.line("askew", [[0.5, 0], [0.6, 0.4]])
        self.design.connect_pins(a.id, "t", askew.id, "start")
        self.assertTrue(_run(self.design, PinAlignmentRule()))

    # --- packaging -------------------------------------------------------------
    def test_shape_rules_are_opt_in(self):
        """SHAPE_RULES run alongside, not inside, the defaults."""
        default_names = {r.name for r in DEFAULT_RULES}
        self.assertFalse(default_names & {r.name for r in SHAPE_RULES})
        self.line("spur", [[0, 0], [0, 0.3], [0, 0.08], [0.2, -0.1]])
        r = validate(self.design, rules=[*DEFAULT_RULES, *SHAPE_RULES])
        self.assertIn("self-intersection", {f.rule for f in r.errors})


if __name__ == "__main__":
    unittest.main(verbosity=2)
