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
"""TransmonConcentric draws its pocket on ``layer`` like the rest of it.

The pocket cut-out was added with a hard-coded ``layer=1``, so with
``layer="2"`` the pads, lines and junctions went to layer 2 while the pocket
was cut from the layer 1 ground plane.
"""

import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_concentric import TransmonConcentric


class TestTransmonConcentricLayer(unittest.TestCase):
    def test_every_qgeometry_row_is_on_the_layer_option(self):
        for layer in ("1", "2", "5"):
            with self.subTest(layer=layer):
                design = designs.DesignPlanar()
                q = TransmonConcentric(design, "Q1", options=dict(layer=layer))
                for table in ("poly", "path", "junction"):
                    rows = q.qgeometry_table(table)
                    for name, row_layer in zip(rows["name"], rows["layer"]):
                        self.assertEqual(
                            int(row_layer), int(layer), msg=f"{table} {name}"
                        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
