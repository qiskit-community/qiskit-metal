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
"""Tests for DRC waivers."""

import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.tlines.polyline_cpw import PolylineCPW
from qiskit_metal.validation import (
    DesignRuleViolation,
    Severity,
    Waiver,
    validate,
)


def _crossing_design():
    """Two CPWs on the same layer crossing at right angles -- one overlap."""
    design = designs.DesignPlanar()
    design.overwrite_enabled = True
    PolylineCPW(design, "A", options=dict(points=[[0, 0], [1, 0]]))
    PolylineCPW(design, "B", options=dict(points=[[0.5, -0.5], [0.5, 0.5]]))
    return design


class TestWaiver(unittest.TestCase):
    """Unit tests for Waiver matching and reporting."""

    def setUp(self):
        self.design = _crossing_design()
        self.baseline = validate(self.design)
        self.assertEqual(len(self.baseline.errors), 1)

    def test_waiver_clears_the_error_without_hiding_it(self):
        """A waived finding stops counting but stays in the report."""
        r = validate(
            self.design,
            waivers=[Waiver("carried on an airbridge", rule="metal-overlap")],
        )
        self.assertTrue(r.ok)
        self.assertEqual(r.errors, [])
        self.assertEqual(len(r.waived), 1)
        self.assertIn("carried on an airbridge", r.report())

    def test_strict_does_not_raise_on_waived_errors(self):
        """strict=True gates on real errors only."""
        with self.assertRaises(DesignRuleViolation):
            validate(self.design, strict=True)
        validate(
            self.design,
            strict=True,
            waivers=[Waiver("known good", rule="metal-overlap")],
        )

    def test_non_matching_waiver_leaves_the_finding(self):
        """Wrong rule, wrong components, or too small a cap: no match."""
        for w in (
            Waiver("wrong rule", rule="cpw-gap"),
            Waiver("wrong components", components=["A", "Z"]),
            Waiver("wrong pattern", component_pattern="FLUX_*"),
            Waiver("value cap too tight", rule="metal-overlap", max_value=1e-12),
        ):
            r = validate(self.design, waivers=[w])
            self.assertEqual(len(r.errors), 1, msg=w.reason)
            self.assertEqual(r.waived, [])

    def test_matching_by_components_and_pattern(self):
        """Exact component set and glob pattern both match."""
        for w in (
            Waiver("exact set", components=["B", "A"]),
            Waiver("pattern", component_pattern="A"),
        ):
            self.assertTrue(validate(self.design, waivers=[w]).ok, msg=w.reason)

    def test_max_value_bounds_the_waiver(self):
        """A waiver written for a small overlap does not cover a large one."""
        value = self.baseline.errors[0].value
        tight = Waiver("small only", rule="metal-overlap", max_value=value / 2)
        loose = Waiver("small only", rule="metal-overlap", max_value=value * 2)
        self.assertFalse(validate(self.design, waivers=[tight]).ok)
        self.assertTrue(validate(self.design, waivers=[loose]).ok)

    def test_stale_waivers_are_reported(self):
        """A waiver matching nothing is surfaced, not silently ignored."""
        r = validate(
            self.design, waivers=[Waiver("nothing like this here", rule="chip-bounds")]
        )
        self.assertEqual(len(r.unused_waivers), 1)
        self.assertIn("matched nothing", r.report())

    def test_waiver_requires_a_reason_and_a_criterion(self):
        """No blank reasons, and no waiver that silences everything."""
        with self.assertRaises(ValueError):
            Waiver("  ")
        with self.assertRaises(ValueError):
            Waiver("covers the world")

    def test_warnings_can_be_waived_too(self):
        """Waivers are not error-specific."""
        r = validate(
            self.design,
            waivers=[
                Waiver("single ground plane is fine here", rule="ground-continuity")
            ],
        )
        self.assertFalse(
            any(
                f.severity is Severity.WARNING and f.rule == "ground-continuity"
                for f in r.findings
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
