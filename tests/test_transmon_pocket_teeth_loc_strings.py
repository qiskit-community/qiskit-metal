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
"""TransmonPocketTeeth draws its teeth for a ``loc_W=0, loc_H=+1`` pad however
the position is written.

``_default_connection_pads`` gives ``loc_W`` and ``loc_H`` as the strings
``"+1"``. ``make_connection_pad`` reads them with ``float()``. The teeth check
in ``make_pocket`` compared the raw options with ``0`` and ``+1``. A position
written as a string got no teeth and no warning. Neither did a pad that kept
the default ``loc_H``.
"""

import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket_teeth import TransmonPocketTeeth


def shapes(readout):
    """The top pad and the readout connector pad for one ``readout`` pad."""
    design = designs.DesignPlanar()
    TransmonPocketTeeth(
        design, "Q1", options=dict(connection_pads=dict(readout=readout))
    )
    poly = design.qgeometry.tables["poly"].set_index("name")["geometry"]
    return poly["pad_top"], poly["readout_connector_pad"]


class TestTransmonPocketTeethLocStrings(unittest.TestCase):
    def test_teeth_for_any_spelling_of_the_top_centre(self):
        with_teeth, connector = shapes(dict(loc_W=0, loc_H=1))
        without_teeth, _ = shapes(dict(loc_W=1, loc_H=1))
        self.assertGreater(with_teeth.bounds[3], without_teeth.bounds[3])
        for readout in (
            dict(loc_W="0", loc_H="+1"),
            dict(loc_W=0, loc_H="+1"),
            dict(loc_W=0),
            dict(loc_W="0.0", loc_H="1.0"),
        ):
            with self.subTest(**readout):
                pad_top, readout_pad = shapes(readout)
                self.assertTrue(pad_top.equals(with_teeth))
                self.assertTrue(readout_pad.equals(connector))

    def test_no_teeth_elsewhere(self):
        without_teeth, _ = shapes(dict(loc_W=1, loc_H=1))
        for readout in (
            dict(loc_W="+1", loc_H="+1"),
            dict(loc_W="-1", loc_H="+1"),
            dict(loc_W="0", loc_H="-1"),
        ):
            with self.subTest(**readout):
                self.assertTrue(shapes(readout)[0].equals(without_teeth))


if __name__ == "__main__":
    unittest.main(verbosity=2)
