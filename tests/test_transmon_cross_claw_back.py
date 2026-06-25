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

"""Tests for the non-uniform claw options of TransmonCross.

``claw_width_back`` and ``ground_spacing_back`` let the back of a claw
connector (the side facing the incoming CPW) use a different width / ground
spacing than the sides. Both default to ``None``, in which case they fall back
to ``claw_width`` / ``ground_spacing`` so existing designs are unchanged.
"""

import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross


def _arm_area(component, pad="a"):
    """Area of the named claw connector_arm polygon."""
    table = component.qgeometry_table("poly")
    row = table[table["name"] == f"{pad}_connector_arm"]
    return float(row.iloc[0].geometry.area)


class TestTransmonCrossClawBack(unittest.TestCase):
    """Backward-compatibility and effect of the *_back claw options."""

    @staticmethod
    def _make(**pad_overrides):
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        return TransmonCross(
            design, "Q", options=dict(connection_pads=dict(a=dict(**pad_overrides)))
        )

    def test_defaults_unchanged_when_back_options_none(self):
        """A claw built with the defaults must be identical to one that sets
        the *_back options equal to their front counterparts."""
        default_arm = _arm_area(self._make())
        explicit_arm = _arm_area(
            self._make(claw_width_back="10um", ground_spacing_back="5um")
        )
        self.assertAlmostEqual(default_arm, explicit_arm, places=12)

    def test_claw_width_back_changes_geometry(self):
        """Setting a different back width must change the connector geometry."""
        default_arm = _arm_area(self._make())
        wide_back_arm = _arm_area(self._make(claw_width_back="30um"))
        self.assertNotAlmostEqual(default_arm, wide_back_arm, places=12)

    def test_rectangle_connector_still_builds(self):
        """connector_type='1' (rectangle) must still build without error."""
        comp = self._make(connector_type="1")
        self.assertIn("a_connector_arm", set(comp.qgeometry_table("poly")["name"]))


if __name__ == "__main__":
    unittest.main()
