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
"""Idempotency tests for ``QComponent.make()``.

``QComponent.rebuild()`` is expected to be deterministic and
side-effect-free: calling it twice on the same component with the same
options must produce the same set of geometry rows. Violations are
silent bugs (component reads from internal state instead of
``self.options``, uses an unseeded random call, depends on render
order, etc.) that would silently break HFSS/Q3D analyses by perturbing
geometry between runs.

These tests parametrize via ``subTest`` over every ``qlibrary``
component that instantiates cleanly on ``DesignPlanar`` with default
options. Routes are intentionally excluded — they require pre-existing
pin connections; an idempotency test for them is a separate piece of
plumbing.
"""

import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.couplers.cap_n_interdigital_tee import CapNInterdigitalTee
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee
from qiskit_metal.qlibrary.couplers.line_tee import LineTee
from qiskit_metal.qlibrary.lumped.cap_3_interdigital import Cap3Interdigital
from qiskit_metal.qlibrary.lumped.cap_n_interdigital import CapNInterdigital
from qiskit_metal.qlibrary.lumped.resonator_coil_rect import ResonatorCoilRect
from qiskit_metal.qlibrary.qubits.JJ_Dolan import jj_dolan
from qiskit_metal.qlibrary.qubits.JJ_Manhattan import jj_manhattan
from qiskit_metal.qlibrary.qubits.SQUID_loop import SQUID_LOOP
from qiskit_metal.qlibrary.qubits.star_qubit import StarQubit
from qiskit_metal.qlibrary.qubits.transmon_concentric import TransmonConcentric
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from qiskit_metal.qlibrary.qubits.transmon_cross_fl import TransmonCrossFL
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.qubits.transmon_pocket_6 import TransmonPocket6
from qiskit_metal.qlibrary.qubits.transmon_pocket_cl import TransmonPocketCL
from qiskit_metal.qlibrary.qubits.transmon_pocket_teeth import TransmonPocketTeeth
from qiskit_metal.qlibrary.sample_shapes.circle_caterpillar import CircleCaterpillar
from qiskit_metal.qlibrary.sample_shapes.circle_raster import CircleRaster
from qiskit_metal.qlibrary.sample_shapes.n_gon import NGon
from qiskit_metal.qlibrary.sample_shapes.n_square_spiral import NSquareSpiral
from qiskit_metal.qlibrary.sample_shapes.rectangle import Rectangle
from qiskit_metal.qlibrary.sample_shapes.rectangle_hollow import RectangleHollow
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.terminations.launchpad_wb_coupled import (
    LaunchpadWirebondCoupled,
)
from qiskit_metal.qlibrary.terminations.launchpad_wb_driven import (
    LaunchpadWirebondDriven,
)
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.terminations.short_to_ground import ShortToGround

# Every component that instantiates cleanly on DesignPlanar with
# (design, name) and no extra options. Routes are excluded — they need
# pin connections that aren't available in default options.
COMPONENTS_UNDER_TEST = [
    # Sample shapes
    Rectangle,
    RectangleHollow,
    NGon,
    NSquareSpiral,
    CircleRaster,
    CircleCaterpillar,
    # Terminations
    OpenToGround,
    ShortToGround,
    LaunchpadWirebond,
    LaunchpadWirebondCoupled,
    LaunchpadWirebondDriven,
    # Qubit family
    TransmonConcentric,
    TransmonPocket,
    TransmonPocketCL,
    TransmonPocket6,
    TransmonPocketTeeth,
    TransmonCross,
    TransmonCrossFL,
    StarQubit,
    SQUID_LOOP,
    jj_dolan,
    jj_manhattan,
    # Lumped
    CapNInterdigital,
    Cap3Interdigital,
    ResonatorCoilRect,
    # Couplers
    LineTee,
    CapNInterdigitalTee,
    CoupledLineTee,
]


def _snapshot_geometry(design) -> dict:
    """Return a deterministic, comparable representation of every
    geometry row in every table.

    The snapshot is a dict ``{table_name: [row_tuple, ...]}`` where
    each row tuple is a sorted, stringified projection of the row's
    contents. ``shapely`` geometries are converted to WKT so they're
    stable across comparison ops; everything else is ``repr()``-ed
    (stable for scalars and ``addict.Dict``).
    """
    out = {}
    for table_name, table in design.qgeometry.tables.items():
        rows = []
        for _, row in table.iterrows():
            row_tuple = tuple(
                (col, (row[col].wkt if hasattr(row[col], "wkt") else repr(row[col])))
                for col in sorted(table.columns)
            )
            rows.append(row_tuple)
        # Sort: only the *set* of geometry rows produced by make()
        # matters, not their insertion order.
        out[table_name] = sorted(rows)
    return out


class TestQComponentIdempotency(unittest.TestCase):
    """Each component's ``make()`` must produce identical geometry on
    a second ``rebuild()`` call."""

    def test_rebuild_is_idempotent(self):
        """Calling ``component.rebuild()`` a second time must not
        change the resulting geometry.

        Catches:
          * ``make()`` mutating ``self.options`` so the second call
            sees different inputs
          * ``make()`` accumulating state across calls instead of
            clearing it
          * Position drift from un-seeded randomness in ``make()``
        """
        for component_cls in COMPONENTS_UNDER_TEST:
            with self.subTest(component=component_cls.__name__):
                design = designs.DesignPlanar()
                component = component_cls(design, f"test_{component_cls.__name__}")
                first = _snapshot_geometry(design)
                component.rebuild()
                second = _snapshot_geometry(design)
                self.assertEqual(
                    first,
                    second,
                    f"{component_cls.__name__}.make() is not idempotent: "
                    f"the second rebuild() produced different geometry.",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
