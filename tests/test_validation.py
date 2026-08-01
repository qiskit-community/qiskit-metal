# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Tests for :mod:`qiskit_metal.validation`.

Each rule is exercised against geometry that is deliberately broken in the
way that rule exists to catch, and against geometry that is fine, so a rule
that always fires (or never does) fails here.
"""

import unittest
import warnings

from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
from qiskit_metal.validation import (
    ChipBoundsRule,
    CPWGapRule,
    DesignRuleViolation,
    GroundContinuityRule,
    MetalOverlapRule,
    MetalSpacingRule,
    Severity,
    ShortSegmentRule,
    validate,
)


def _design(size="6mm"):
    design = designs.DesignPlanar()
    design.overwrite_enabled = True
    design._chips["main"]["size"]["size_x"] = size
    design._chips["main"]["size"]["size_y"] = size
    return design


def _route(design, name, a, b, ori_a, ori_b, **route_opts):
    """A straight CPW between two fresh OpenToGround terminations."""
    OpenToGround(
        design, f"{name}_A", options=dict(pos_x=a[0], pos_y=a[1], orientation=ori_a)
    )
    OpenToGround(
        design, f"{name}_B", options=dict(pos_x=b[0], pos_y=b[1], orientation=ori_b)
    )
    return RouteStraight(
        design,
        name,
        options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(component=f"{name}_A", pin="open"),
                end_pin=Dict(component=f"{name}_B", pin="open"),
            ),
            **route_opts,
        ),
    )


class TestMetalOverlapRule(unittest.TestCase):
    """Two components' metal overlapping on one layer is a short."""

    def test_crossing_routes_are_flagged(self):
        design = _design()
        _route(design, "horiz", ("-1.5mm", "0mm"), ("1.5mm", "0mm"), "180", "0")
        _route(design, "vert", ("0mm", "-1.5mm"), ("0mm", "1.5mm"), "270", "90")
        design.rebuild()

        findings = list(MetalOverlapRule().check(design))
        crossing = [f for f in findings if set(f.components) == {"horiz", "vert"}]
        self.assertEqual(
            len(crossing),
            1,
            msg=f"expected exactly one horiz/vert overlap, got {findings}",
        )
        self.assertIs(crossing[0].severity, Severity.ERROR)
        # They cross at the origin.
        self.assertAlmostEqual(crossing[0].location[0], 0.0, places=3)
        self.assertAlmostEqual(crossing[0].location[1], 0.0, places=3)

    def test_parallel_routes_are_not_flagged(self):
        design = _design()
        _route(design, "a", ("-1.5mm", "0.5mm"), ("1.5mm", "0.5mm"), "180", "0")
        _route(design, "b", ("-1.5mm", "-0.5mm"), ("1.5mm", "-0.5mm"), "180", "0")
        design.rebuild()
        self.assertEqual(list(MetalOverlapRule().check(design)), [])

    def test_connected_components_are_not_flagged(self):
        """A route abuts the pin it connects to -- that is not a short."""
        design = _design()
        _route(design, "r", ("-1mm", "0mm"), ("1mm", "0mm"), "180", "0")
        design.rebuild()
        findings = list(MetalOverlapRule().check(design))
        self.assertEqual(
            findings, [], msg="route/termination junctions must not report as shorts"
        )


class TestMetalSpacingRule(unittest.TestCase):
    """Near-misses that do not touch but are too close to fabricate."""

    def test_routes_closer_than_minimum_are_flagged(self):
        design = _design()
        # Centrelines 20um apart; each conductor is 10um wide, so the metal
        # edges are only ~10um apart -- inside a 20um rule.
        _route(design, "a", ("-1.5mm", "0.010mm"), ("1.5mm", "0.010mm"), "180", "0")
        _route(design, "b", ("-1.5mm", "-0.010mm"), ("1.5mm", "-0.010mm"), "180", "0")
        design.rebuild()

        findings = [
            f
            for f in MetalSpacingRule(min_spacing="20um").check(design)
            if set(f.components) == {"a", "b"}
        ]
        self.assertEqual(len(findings), 1, msg=f"got {findings}")
        self.assertLess(findings[0].value, findings[0].limit)

    def test_well_separated_routes_pass(self):
        design = _design()
        _route(design, "a", ("-1.5mm", "1mm"), ("1.5mm", "1mm"), "180", "0")
        _route(design, "b", ("-1.5mm", "-1mm"), ("1.5mm", "-1mm"), "180", "0")
        design.rebuild()
        findings = [
            f
            for f in MetalSpacingRule(min_spacing="20um").check(design)
            if set(f.components) == {"a", "b"}
        ]
        self.assertEqual(findings, [])


class TestCPWGapRule(unittest.TestCase):
    """The CPW gap sets interface field strength, so it has a floor."""

    def test_narrow_gap_is_flagged(self):
        design = _design()
        _route(
            design,
            "narrow",
            ("-1mm", "0mm"),
            ("1mm", "0mm"),
            "180",
            "0",
            trace_width="10um",
            trace_gap="1um",
        )
        design.rebuild()
        findings = [
            f
            for f in CPWGapRule(min_gap="3um").check(design)
            if "narrow" in f.components
        ]
        self.assertEqual(len(findings), 1, msg=f"got {findings}")
        self.assertAlmostEqual(findings[0].value, 0.001, places=6)

    def test_standard_gap_passes(self):
        design = _design()
        _route(
            design,
            "ok",
            ("-1mm", "0mm"),
            ("1mm", "0mm"),
            "180",
            "0",
            trace_width="10um",
            trace_gap="6um",
        )
        design.rebuild()
        findings = [
            f for f in CPWGapRule(min_gap="3um").check(design) if "ok" in f.components
        ]
        self.assertEqual(findings, [])


class TestChipBoundsRule(unittest.TestCase):
    """Geometry off the chip is silently clipped downstream."""

    def test_component_outside_chip_is_flagged(self):
        design = _design(size="2mm")  # half-extent 1mm
        TransmonPocket(design, "Q_far", options=dict(pos_x="5mm", pos_y="0mm"))
        design.rebuild()
        findings = [
            f for f in ChipBoundsRule().check(design) if "Q_far" in f.components
        ]
        self.assertEqual(len(findings), 1, msg=f"got {findings}")
        self.assertGreater(findings[0].value, 0)

    def test_component_inside_chip_passes(self):
        design = _design(size="6mm")
        TransmonPocket(design, "Q_near", options=dict(pos_x="0mm", pos_y="0mm"))
        design.rebuild()
        self.assertEqual(list(ChipBoundsRule().check(design)), [])


class TestShortSegmentRule(unittest.TestCase):
    """Segments shorter than the fillet radius render as sharp kinks."""

    def _bent_route(self, design, name, reach, fillet):
        """An L-shaped route whose two legs are ``reach`` long.

        A straight route has no interior corner, so nothing to fillet and
        nothing for this rule to say -- the defect only exists where a
        segment has to host a corner arc.
        """
        OpenToGround(
            design,
            f"{name}_A",
            options=dict(pos_x=f"-{reach}", pos_y="0mm", orientation="180"),
        )
        OpenToGround(
            design,
            f"{name}_B",
            options=dict(pos_x="0mm", pos_y=f"{reach}", orientation="90"),
        )
        return RoutePathfinder(
            design,
            name,
            options=Dict(
                fillet=fillet,
                pin_inputs=Dict(
                    start_pin=Dict(component=f"{name}_A", pin="open"),
                    end_pin=Dict(component=f"{name}_B", pin="open"),
                ),
            ),
        )

    def test_segment_shorter_than_fillet_is_flagged(self):
        design = _design()
        # 100um legs asked to round their corner with a 150um radius.
        self._bent_route(design, "tight", reach="0.1mm", fillet="150um")
        design.rebuild()
        findings = [
            f for f in ShortSegmentRule().check(design) if "tight" in f.components
        ]
        self.assertTrue(findings, "a 100um segment cannot host a 150um fillet")
        self.assertIs(findings[0].severity, Severity.WARNING)
        self.assertLess(findings[0].value, findings[0].limit)

    def test_generous_segment_passes(self):
        design = _design()
        self._bent_route(design, "roomy", reach="2mm", fillet="50um")
        design.rebuild()
        findings = [
            f for f in ShortSegmentRule().check(design) if "roomy" in f.components
        ]
        self.assertEqual(findings, [])

    def test_straight_route_has_no_corner_to_check(self):
        """A 2-point route cannot violate this rule at any fillet."""
        design = _design()
        _route(
            design,
            "straight",
            ("-0.1mm", "0mm"),
            ("0.1mm", "0mm"),
            "180",
            "0",
            fillet="150um",
        )
        design.rebuild()
        findings = [
            f for f in ShortSegmentRule().check(design) if "straight" in f.components
        ]
        self.assertEqual(findings, [])


class TestValidateAPI(unittest.TestCase):
    """The top-level entry point and result object."""

    def _crossed_design(self):
        design = _design()
        _route(design, "horiz", ("-1.5mm", "0mm"), ("1.5mm", "0mm"), "180", "0")
        _route(design, "vert", ("0mm", "-1.5mm"), ("0mm", "1.5mm"), "270", "90")
        design.rebuild()
        return design

    def test_clean_design_is_truthy_and_reports_pass(self):
        design = _design()
        _route(design, "solo", ("-1mm", "0mm"), ("1mm", "0mm"), "180", "0")
        design.rebuild()
        result = validate(design)
        self.assertTrue(result.ok)
        self.assertTrue(result)
        self.assertIn("passed", result.report())

    def test_broken_design_is_falsy_and_lists_errors(self):
        result = validate(self._crossed_design())
        self.assertFalse(result.ok)
        self.assertFalse(result)
        self.assertTrue(result.errors)
        self.assertIn("metal-overlap", result.report())

    def test_strict_raises(self):
        with self.assertRaises(DesignRuleViolation):
            validate(self._crossed_design(), strict=True)

    def test_raise_if_errors_chains_on_success(self):
        design = _design()
        _route(design, "solo", ("-1mm", "0mm"), ("1mm", "0mm"), "180", "0")
        design.rebuild()
        result = validate(design)
        self.assertIs(result.raise_if_errors(), result)

    def test_rules_subset_is_honoured(self):
        result = validate(self._crossed_design(), rules=[ChipBoundsRule()])
        self.assertEqual(result.rules_run, ("chip-bounds",))
        # The crossing is real but ChipBoundsRule is not looking for it.
        self.assertTrue(result.ok)

    def test_thresholds_are_configurable(self):
        """The same geometry passes or fails depending on the rule's limit."""
        design = _design()
        _route(design, "a", ("-1.5mm", "0.015mm"), ("1.5mm", "0.015mm"), "180", "0")
        _route(design, "b", ("-1.5mm", "-0.015mm"), ("1.5mm", "-0.015mm"), "180", "0")
        design.rebuild()

        loose = [
            f
            for f in validate(design, rules=[MetalSpacingRule(min_spacing="2um")])
            if set(f.components) == {"a", "b"}
        ]
        strict = [
            f
            for f in validate(design, rules=[MetalSpacingRule(min_spacing="50um")])
            if set(f.components) == {"a", "b"}
        ]
        self.assertEqual(loose, [])
        self.assertTrue(strict)


class TestAirbridgeLayerSeparation(unittest.TestCase):
    """An airbridge crossing a CPW is the point of an airbridge."""

    def test_airbridge_over_cpw_is_not_a_short(self):
        from qiskit_metal.qlibrary.tlines.airbridge import route_airbridges

        design = _design()
        route = _route(design, "cpw", ("-1.5mm", "0mm"), ("1.5mm", "0mm"), "180", "0")
        design.rebuild()
        bridges = route_airbridges(design, route, pitch="500um")
        design.rebuild()
        self.assertTrue(bridges, "expected airbridges to be placed")

        findings = list(MetalOverlapRule().check(design))
        crossings = [f for f in findings if "cpw" in f.components]
        self.assertEqual(
            crossings,
            [],
            msg="airbridge spans sit on their own layer and must not "
            f"report as shorts against the CPW they cross: {crossings}",
        )


class TestGroundContinuityRule(unittest.TestCase):
    """A CPW that reaches both chip edges cuts the ground plane in two."""

    def test_chip_spanning_route_splits_the_ground(self):
        design = _design()
        # Over-runs both edges so the etched footprint reaches the chip
        # boundary; a route that stops short leaves a ground bridge.
        _route(design, "cut", ("-4mm", "0mm"), ("4mm", "0mm"), "180", "0")
        design.rebuild()

        findings = list(GroundContinuityRule().check(design))
        self.assertEqual(len(findings), 1, msg=f"expected one split: {findings}")
        self.assertIn("2 disconnected regions", findings[0].message)
        self.assertEqual(findings[0].severity, Severity.WARNING)

    def test_route_that_stops_short_keeps_ground_connected(self):
        design = _design()
        _route(design, "stub", ("-1mm", "0mm"), ("1mm", "0mm"), "180", "0")
        design.rebuild()

        self.assertEqual(list(GroundContinuityRule().check(design)), [])

    def test_void_check_is_off_by_default(self):
        """A transmon pocket is a deliberate void far wider than 50 um."""
        design = _design()
        TransmonPocket(design, "Q", options=dict(pos_x="0mm", pos_y="0mm"))
        design.rebuild()

        self.assertEqual(list(GroundContinuityRule().check(design)), [])

    def test_void_check_flags_wide_voids_when_enabled(self):
        design = _design()
        TransmonPocket(design, "Q", options=dict(pos_x="0mm", pos_y="0mm"))
        design.rebuild()

        findings = list(GroundContinuityRule(max_void_size="50um").check(design))
        self.assertTrue(findings, "pocket is far wider than 50 um")
        self.assertTrue(all("parasitic mode" in f.message for f in findings))


class TestQDesignCheckDeprecation(unittest.TestCase):
    """The predecessor still works, but points at its replacement."""

    def test_construction_warns(self):
        from qiskit_metal.qlibrary.core.design_check import QDesignCheck

        design = _design()
        with self.assertWarns(DeprecationWarning) as caught:
            QDesignCheck(design)
        self.assertIn("qiskit_metal.validation", str(caught.warning))

    def test_still_runs(self):
        """Deprecated does not mean broken -- the API stays until removal."""
        from qiskit_metal.qlibrary.core.design_check import QDesignCheck

        design = _design()
        _route(design, "horiz", ("-1.5mm", "0mm"), ("1.5mm", "0mm"), "180", "0")
        _route(design, "vert", ("0mm", "-1.5mm"), ("0mm", "1.5mm"), "270", "90")
        design.rebuild()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            checker = QDesignCheck(design)
            checker.update_design(design)
            checker.overlap_tester()  # prints; asserted only not to raise


if __name__ == "__main__":
    unittest.main(verbosity=2)
