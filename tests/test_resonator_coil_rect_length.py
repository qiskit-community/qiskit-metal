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
"""ResonatorCoilRect draws a spiral whose centre line is ``length`` long.

``make()`` sized the spiral width with ``2 * (gap + line_width) * (2n - 1)``
where the turns it draws need ``(gap + line_width) * (2n - 1)``, so the
spiral came out ``2n(2n - 1)(gap + line_width)`` short: 1849.5 um for the
default ``length`` of 2000 um.
"""

import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.lumped.resonator_coil_rect import ResonatorCoilRect


class TestResonatorCoilRectLength(unittest.TestCase):
    def test_spiral_length_is_the_length_option(self):
        cases = (
            dict(),
            dict(n="1"),
            dict(n="5", length="4000um"),
            dict(height="100um", gap="10um", line_width="5um"),
        )
        for options in cases:
            with self.subTest(**options):
                design = designs.DesignPlanar()
                coil = ResonatorCoilRect(design, "res", options=options)
                spiral = coil.qgeometry_table("path").geometry.iloc[0]
                self.assertAlmostEqual(spiral.length, coil.p.length, places=6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
