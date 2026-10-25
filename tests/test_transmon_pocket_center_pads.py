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
"""A ``loc_W=0`` connection pad on TransmonPocket6 / TransmonPocketTeeth ends
``cpw_extend`` past the top or bottom edge of the pocket.

The vertical CPW of these centre pads was sized from ``pocket_width``, so its
pin ignored ``pocket_height``: with ``pocket_height="900um"`` and the default
650 um width the line stopped 25 um inside the pocket.
"""

import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket_6 import TransmonPocket6
from qiskit_metal.qlibrary.qubits.transmon_pocket_teeth import TransmonPocketTeeth


class TestTransmonPocketCenterPads(unittest.TestCase):
    def test_center_pad_pins_follow_pocket_height(self):
        pads = dict(top=dict(loc_W=0, loc_H=1), bot=dict(loc_W=0, loc_H=-1))
        for cls in (TransmonPocket6, TransmonPocketTeeth):
            for height in ("500um", "650um", "900um"):
                with self.subTest(cls=cls.__name__, pocket_height=height):
                    design = designs.DesignPlanar()
                    q = cls(
                        design,
                        "Q1",
                        options=dict(
                            pocket_width="650um",
                            pocket_height=height,
                            connection_pads=pads,
                        ),
                    )
                    edge = q.p.pocket_height / 2 + q.p.connection_pads.top.cpw_extend
                    self.assertAlmostEqual(q.pins.top.middle[0], 0)
                    self.assertAlmostEqual(q.pins.top.middle[1], edge)
                    self.assertAlmostEqual(q.pins.bot.middle[0], 0)
                    self.assertAlmostEqual(q.pins.bot.middle[1], -edge)


if __name__ == "__main__":
    unittest.main(verbosity=2)
