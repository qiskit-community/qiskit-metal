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
"""Issue #1226 -- a connection pad added to an existing qubit gets the class
defaults on rebuild.

``BaseQubit`` merged ``_default_connection_pads`` into each pad only in
``__init__``. A pad added afterwards had no ``pad_width``, ``cpw_width``, ...
and ``rebuild()`` failed with a TypeError inside ``make_connection_pad``.
"""

import unittest

from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket


def _geometry(design, name):
    """Sorted (table, element name, WKT) of a component's qgeometry."""
    comp = design.components[name]
    out = []
    for table in ("poly", "path", "junction"):
        df = design.qgeometry.tables[table]
        rows = df[df["component"] == comp.id]
        out += [(table, n, g.wkt) for n, g in zip(rows["name"], rows["geometry"])]
    return sorted(out)


class TestAddConnectionPadAfterConstruction(unittest.TestCase):
    def _check(self, cls, pad_a, pad_b):
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        q = cls(design, "Q1", options=dict(connection_pads=dict(a=pad_a)))
        q.options.connection_pads.b = Dict(pad_b)
        design.rebuild()
        self.assertEqual(q.status, "good")
        self.assertEqual(sorted(q.pins), ["a", "b"])

        ref = designs.DesignPlanar()
        cls(ref, "Q1", options=dict(connection_pads=dict(a=pad_a, b=pad_b)))
        self.assertEqual(_geometry(design, "Q1"), _geometry(ref, "Q1"))
        self.assertEqual(
            q.options.connection_pads.to_dict(),
            ref.components["Q1"].options.connection_pads.to_dict(),
        )

    def test_transmon_pocket(self):
        self._check(TransmonPocket, dict(loc_W=1, loc_H=1), dict(loc_W=-1, loc_H=-1))

    def test_transmon_cross(self):
        self._check(
            TransmonCross,
            dict(connector_location="0"),
            dict(connector_location="180", claw_length="40um"),
        )

    def test_user_values_are_kept(self):
        """Filling defaults must not overwrite keys the user set."""
        design = designs.DesignPlanar()
        q = TransmonPocket(design, "Q1", options=dict(connection_pads=dict(a={})))
        q.options.connection_pads.b = Dict(loc_W=-1, pad_width="77um")
        q.rebuild()
        self.assertEqual(q.options.connection_pads.b.pad_width, "77um")
        self.assertEqual(q.options.connection_pads.b.loc_W, -1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
