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
"""Tests for CapFingerInFrame."""

import unittest

import numpy as np

from qiskit_metal import designs
from qiskit_metal.qlibrary.lumped.cap_finger_in_frame import CapFingerInFrame
from qiskit_metal.qlibrary.tlines.polyline_cpw import PolylineCPW
from qiskit_metal.validation import validate


class TestCapFingerInFrame(unittest.TestCase):
    """Unit tests for the CapFingerInFrame component."""

    def setUp(self):
        self.design = designs.DesignPlanar()
        self.design.overwrite_enabled = True

    def _polys(self, c):
        t = self.design.qgeometry.tables["poly"]
        rows = t[t["component"] == c.id]
        return {r["name"]: r.geometry for _, r in rows.iterrows()}

    def test_pins_on_outer_edges_facing_out(self):
        """Frame pin faces -x, finger pin +x, both on the frame's outer edge."""
        c = CapFingerInFrame(self.design, "c", options=dict(frame_width="0.072"))
        np.testing.assert_allclose(c.pins["frame"]["middle"], [-0.036, 0], atol=1e-9)
        np.testing.assert_allclose(c.pins["finger"]["middle"], [0.036, 0], atol=1e-9)
        np.testing.assert_allclose(c.pins["frame"]["normal"], [-1, 0], atol=1e-9)
        np.testing.assert_allclose(c.pins["finger"]["normal"], [1, 0], atol=1e-9)

    def test_pins_follow_orientation(self):
        """Rotating the cell rotates both pins and their normals."""
        c = CapFingerInFrame(self.design, "c", options=dict(orientation="90"))
        np.testing.assert_allclose(c.pins["finger"]["normal"], [0, 1], atol=1e-9)
        np.testing.assert_allclose(c.pins["frame"]["normal"], [0, -1], atol=1e-9)

    def test_electrodes_separated_by_cap_gap_everywhere(self):
        """The finger never touches the frame: minimum spacing is cap_gap."""
        c = CapFingerInFrame(self.design, "c", options=dict(cap_gap="0.008"))
        g = self._polys(c)
        self.assertAlmostEqual(g["frame"].distance(g["finger"]), 0.008, places=9)

    def test_finger_is_derived_from_frame_and_gap(self):
        """Finger = opening inside the frame less cap_gap on every side."""
        c = CapFingerInFrame(
            self.design,
            "c",
            options=dict(
                frame_length="0.2",
                frame_width="0.07",
                frame_trace="0.015",
                cap_gap="0.01",
                finger_cpw_width="0.01",
            ),
        )
        bar = self._polys(c)["finger"].bounds
        # bar spans x in [-0.01, +0.01] then the stub runs to the frame edge 0.035
        self.assertAlmostEqual(bar[0], -0.01, places=9)
        self.assertAlmostEqual(bar[2], 0.035, places=9)
        self.assertAlmostEqual(bar[3] - bar[1], 0.2 - 2 * 0.015 - 2 * 0.01, places=9)

    def test_rejects_a_frame_with_no_room_for_the_finger(self):
        """Impossible dimensions raise instead of drawing overlapping metal."""
        with self.assertRaises(ValueError):
            CapFingerInFrame(
                self.design,
                "c",
                options=dict(frame_width="0.04", frame_trace="0.015", cap_gap="0.01"),
            )

    def test_inline_in_a_cpw_passes_drc(self):
        """Wired inline between two CPWs, the cell is a clean series capacitor."""
        c = CapFingerInFrame(self.design, "c")
        a = PolylineCPW(
            self.design,
            "a",
            options=dict(points=[[-0.5, 0], list(c.pins["frame"]["middle"])]),
        )
        b = PolylineCPW(
            self.design,
            "b",
            options=dict(points=[list(c.pins["finger"]["middle"]), [0.5, 0]]),
        )
        self.design.connect_pins(a.id, "end", c.id, "frame")
        self.design.connect_pins(c.id, "finger", b.id, "start")
        self.assertEqual(validate(self.design).errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
