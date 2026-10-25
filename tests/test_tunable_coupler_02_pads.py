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
"""TunableCoupler02 places each circular pad ``bus_inner_length`` from the
JJ side of the bus and ``bus_outer_length`` from its pin.

The bus is drawn ``bus_inner_length + 2 * pad_radius + bus_outer_length``
long, but the pads were centred ``bus_inner_length + pad_radius / 2`` along
it, half a radius too close to the JJ: with the defaults the inner CPW was
350 um and the outer one 650 um instead of 500 um each.
"""

import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.couplers.tunable_coupler_02 import TunableCoupler02


class TestTunableCoupler02Pads(unittest.TestCase):
    def test_pads_split_the_bus_into_inner_and_outer_lengths(self):
        cases = (
            dict(),
            dict(pad_radius="0.2mm", bus_inner_length="0.3mm"),
            dict(bus_outer_length="0.8mm", bus_width="50um"),
        )
        for options in cases:
            with self.subTest(**options):
                design = designs.DesignPlanar()
                tc = TunableCoupler02(design, "TC", options=options)
                p = tc.p
                polys = tc.qgeometry_table("poly").set_index("name").geometry
                # The horizontal bus starts at the outer edge of the vertical
                # bus that holds the JJ.
                bus_start = p.JJ_length / 2 + p.bus_width
                left_x0, _, left_x1, _ = polys["poly6"].bounds
                right_x0, _, right_x1, _ = polys["poly7"].bounds
                self.assertAlmostEqual(right_x0 - bus_start, p.bus_inner_length)
                self.assertAlmostEqual(
                    tc.pins.pin1.middle[0] - right_x1, p.bus_outer_length
                )
                self.assertAlmostEqual(-bus_start - left_x1, p.bus_inner_length)
                self.assertAlmostEqual(
                    left_x0 - tc.pins.pin2.middle[0], p.bus_outer_length
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
