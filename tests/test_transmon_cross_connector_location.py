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

"""Tests for ``connector_location`` on TransmonCross.

The option names the arm of the cross a connector sits on: 0 => west,
90 => north, 180 => east, 270 => south. It used to be handled by a threshold
chain that had no branch above 225, so '270' landed on the *east* arm
(issue #1052). The mapping now goes through ``connector_arm_name()``, which
snaps mod 360.
"""

import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_cross import (
    TransmonCross,
    connector_arm_name,
)
from qiskit_metal.qlibrary.qubits.transmon_cross_fl import TransmonCrossFL

#: Outward normal of the connector pin for each arm.
ARM_NORMAL = {
    "west": (-1.0, 0.0),
    "north": (0.0, 1.0),
    "east": (1.0, 0.0),
    "south": (0.0, -1.0),
}


def _make(cls=TransmonCross, **pad_overrides):
    """Build a component with a single connection pad 'a'."""
    design = designs.DesignPlanar()
    design.overwrite_enabled = True
    return cls(design, "Q", options=dict(connection_pads=dict(a=dict(**pad_overrides))))


class TestConnectorArmName(unittest.TestCase):
    """The angle -> arm mapping on its own."""

    def test_cardinal_angles(self):
        """The four documented values select the four arms."""
        for angle, arm in [(0, "west"), (90, "north"), (180, "east"), (270, "south")]:
            self.assertEqual(connector_arm_name(angle), arm)

    def test_wraps_modulo_360(self):
        """Out-of-range angles wrap instead of saturating at the top branch."""
        for angle, arm in [
            (360, "west"),
            (450, "north"),
            (-90, "south"),
            (-180, "east"),
            (720, "west"),
        ]:
            self.assertEqual(connector_arm_name(angle), arm)

    def test_half_way_angles_snap_down(self):
        """Ties snap to the lower arm, as the original threshold chain did."""
        for angle, arm in [(45, "west"), (135, "north"), (225, "east"), (315, "south")]:
            self.assertEqual(connector_arm_name(angle), arm)

    def test_accepts_strings_and_floats(self):
        """Values arrive parsed, but the helper must not care about the type."""
        self.assertEqual(connector_arm_name("270"), "south")
        self.assertEqual(connector_arm_name(269.5), "south")


class TestConnectorLocationPlacement(unittest.TestCase):
    """The option must actually move the claw and its pin."""

    def _assert_on_arm(self, component, arm):
        pin = component.pins["a"]
        normal = tuple(round(float(v)) for v in pin["normal"])
        self.assertEqual(normal, ARM_NORMAL[arm], f"pin normal not on {arm} arm")

        # The pin sits on the arm's axis: the off-axis coordinate is ~0.
        middle = pin["middle"]
        off_axis = middle[1] if arm in ("west", "east") else middle[0]
        self.assertAlmostEqual(float(off_axis), 0.0, places=9)

    def test_each_location_selects_its_arm(self):
        """Regression test for #1052: '270' must reach the south arm."""
        for location, arm in [
            ("0", "west"),
            ("90", "north"),
            ("180", "east"),
            ("270", "south"),
        ]:
            with self.subTest(connector_location=location):
                self._assert_on_arm(_make(connector_location=location), arm)

    def test_out_of_range_locations_wrap(self):
        """'360' is west, not south; '-90' is south, not west."""
        self._assert_on_arm(_make(connector_location="360"), "west")
        self._assert_on_arm(_make(connector_location="-90"), "south")

    def test_south_connector_clears_the_junction(self):
        """The south claw must not touch the junction sharing that arm."""
        component = _make(connector_location="270")
        poly = component.qgeometry_table("poly")
        arm = poly[poly["name"] == "a_connector_arm"].iloc[0].geometry
        junction = component.qgeometry_table("junction").iloc[0].geometry
        self.assertFalse(arm.intersects(junction))

    def test_gap_connector_type_also_follows_the_arm(self):
        """connector_type='1' draws a different shape, same placement."""
        self._assert_on_arm(
            _make(connector_location="270", connector_type="1"), "south"
        )


class TestFluxLineSouthArmWarning(unittest.TestCase):
    """TransmonCrossFL puts its flux line on the south arm."""

    def test_warns_when_connector_shares_the_flux_line_arm(self):
        """A '270' pad overlaps the flux line, so it must be called out."""
        with self.assertLogs("metal", level="WARNING") as captured:
            _make(TransmonCrossFL, connector_location="270")
        self.assertTrue(
            any("south" in message for message in captured.output),
            f"expected a south-arm warning, got: {captured.output}",
        )

    def test_no_warning_for_the_other_arms(self):
        """The default placements must stay quiet."""
        for location in ("0", "90", "180"):
            with self.subTest(connector_location=location):
                with self.assertNoLogs("metal", level="WARNING"):
                    _make(TransmonCrossFL, connector_location=location)

    def test_no_warning_when_the_flux_line_is_disabled(self):
        """Without a flux line there is nothing for the claw to collide with."""
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        with self.assertNoLogs("metal", level="WARNING"):
            TransmonCrossFL(
                design,
                "Q",
                options=dict(
                    make_fl=False,
                    connection_pads=dict(a=dict(connector_location="270")),
                ),
            )

    def test_south_connector_does_overlap_the_flux_line(self):
        """The warning is not hypothetical - the metal really does collide."""
        component = _make(TransmonCrossFL, connector_location="270")
        poly = component.qgeometry_table("poly")
        arm = poly[poly["name"] == "a_connector_arm"].iloc[0].geometry
        paths = component.qgeometry_table("path")
        overlaps = [
            arm.intersects(row.geometry.buffer(row.width / 2))
            for _, row in paths.iterrows()
        ]
        self.assertTrue(any(overlaps))

    def test_west_connector_clears_the_flux_line(self):
        """The default placement keeps the claw off the flux line."""
        component = _make(TransmonCrossFL, connector_location="0")
        poly = component.qgeometry_table("poly")
        arm = poly[poly["name"] == "a_connector_arm"].iloc[0].geometry
        paths = component.qgeometry_table("path")
        for _, row in paths.iterrows():
            self.assertFalse(arm.intersects(row.geometry.buffer(row.width / 2)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
