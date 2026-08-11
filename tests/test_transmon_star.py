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

"""Tests for TransmonStar.

A connector's ``arm_index`` must place its pin on that arm's own angle, not
180 deg opposite it -- the connector geometry is built pointing toward -x
before rotation (the same convention `TransmonCross` uses), so the rotation
has to add the extra 180 deg back on. Caught visually once already; these
pin-normal checks are the regression test.
"""

import math
import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_star import TransmonStar
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight


def _make(num_points=6, **kwargs):
    design = designs.DesignPlanar()
    design.overwrite_enabled = True
    return TransmonStar(
        design, "Q", options=dict(num_points=num_points, **kwargs)
    ), design


class TestArmPlacement(unittest.TestCase):
    """A connector's pin must sit on its own arm, not the opposite one."""

    def _assert_pin_on_arm(self, component, pin_name, num_points, arm_index):
        expected_angle = math.radians(360.0 * arm_index / num_points)
        expected_normal = (math.cos(expected_angle), math.sin(expected_angle))
        normal = tuple(float(v) for v in component.pins[pin_name]["normal"])
        for got, want in zip(normal, expected_normal):
            self.assertAlmostEqual(got, want, places=6)

    def test_each_arm_index_places_its_own_pin(self):
        for num_points in (4, 5, 6, 7):
            for arm_index in range(num_points):
                with self.subTest(num_points=num_points, arm_index=arm_index):
                    component, _ = _make(
                        num_points=num_points,
                        connection_pads=dict(a=dict(arm_index=arm_index)),
                    )
                    self._assert_pin_on_arm(component, "a", num_points, arm_index)

    def test_gap_connector_type_also_follows_its_arm(self):
        component, _ = _make(
            num_points=6,
            connection_pads=dict(a=dict(arm_index=2, connector_type="1")),
        )
        self._assert_pin_on_arm(component, "a", 6, 2)


class TestDanglingArms(unittest.TestCase):
    """Arms not named in connection_pads stay bare -- no pad, no pin."""

    def test_unconnected_arms_have_no_pin(self):
        component, _ = _make(num_points=6, connection_pads=dict(a=dict(arm_index=0)))
        self.assertEqual(set(component.pins.keys()), {"a"})

    def test_no_connection_pads_builds_fine(self):
        component, _ = _make(num_points=6)
        self.assertEqual(dict(component.pins), {})


class TestJunctionPlacement(unittest.TestCase):
    """The junction sits on its own designated arm and clears other arms'
    connectors."""

    def test_junction_does_not_overlap_a_connector_on_another_arm(self):
        component, _ = _make(
            num_points=6,
            junction_arm_index=0,
            connection_pads=dict(a=dict(arm_index=3)),  # opposite arm
        )
        poly = component.qgeometry_table("poly")
        arm = poly[poly["name"] == "a_connector_arm"].iloc[0].geometry
        junction = component.qgeometry_table("junction").iloc[0].geometry
        self.assertFalse(arm.intersects(junction))


class TestRouting(unittest.TestCase):
    """A pin should be usable by a real route, end to end."""

    def test_two_star_transmons_can_be_routed_together(self):
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        TransmonStar(
            design,
            "Q1",
            options=dict(
                pos_x="-1mm",
                num_points=6,
                connection_pads=dict(a=dict(arm_index=0)),
            ),
        )
        TransmonStar(
            design,
            "Q2",
            options=dict(
                pos_x="1mm",
                orientation="180",
                num_points=6,
                connection_pads=dict(a=dict(arm_index=0)),
            ),
        )
        RouteStraight(
            design,
            "cpw1",
            options=dict(
                pin_inputs=dict(
                    start_pin=dict(component="Q1", pin="a"),
                    end_pin=dict(component="Q2", pin="a"),
                )
            ),
        )
        design.rebuild()
        self.assertIn("cpw1", design.components)


if __name__ == "__main__":
    unittest.main(verbosity=2)
