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
"""Pin-data sanity checks for components in ``qlibrary``.

Every pin emitted by ``QComponent.add_pin()`` populates a dict with
geometric metadata used by the renderer dispatch (HFSS/Q3D port
placement, GDS port markers). Bad pin metadata causes silent
mis-renders that only surface during an Ansys solve:

* zero or negative width -> Ansys can't place a port
* non-unit ``normal`` -> port orientation is rotated by the magnitude
* ``normal`` not perpendicular to ``tangent`` -> port plane is skewed
* ``middle`` not at the midpoint of ``points`` -> port offset

These tests catch all four by walking ``component.pins`` on a small
set of representative components. The transmon family is the highest
priority because that's where coupler pins live; routes are skipped
because their pin layout depends on pin_inputs that aren't available
in default options.
"""

import unittest

import numpy as np

from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.lumped.cap_n_interdigital import CapNInterdigital
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.qubits.transmon_pocket_6 import TransmonPocket6
from qiskit_metal.qlibrary.qubits.transmon_pocket_cl import TransmonPocketCL

# (component_class, options) — options force at least one pin to be
# emitted under what would otherwise be a pin-less default config.
# Transmons add pins through their ``connection_pads`` dict; an empty
# sub-dict falls back to ``_default_connection_pads`` for the per-pad
# values.
_PIN_KW = Dict(connection_pads=Dict(a=Dict()))
COMPONENTS_WITH_PINS = [
    (TransmonPocket, _PIN_KW),
    (TransmonPocketCL, _PIN_KW),
    (TransmonPocket6, _PIN_KW),
    (TransmonCross, _PIN_KW),
    (CapNInterdigital, Dict()),  # adds two pins by default
]


class TestQComponentPinSanity(unittest.TestCase):
    """Each emitted pin must have well-formed geometric metadata."""

    UNIT_TOLERANCE = 1e-6
    PERPENDICULAR_TOLERANCE = 1e-6

    def test_pin_geometry_invariants(self):
        """For each pin: width > 0, ``normal`` and ``tangent`` are unit
        vectors and mutually perpendicular, and ``middle`` is the
        midpoint of ``points``."""
        for component_cls, options in COMPONENTS_WITH_PINS:
            with self.subTest(component=component_cls.__name__):
                design = designs.DesignPlanar()
                component = component_cls(design,
                                          f"test_{component_cls.__name__}",
                                          options=options)
                if not component.pins:
                    self.fail(
                        f"{component_cls.__name__} produced no pins with "
                        f"the test's configured options — update the "
                        f"options dict if the component's pin trigger "
                        f"changed.")
                for pin_name, pin in component.pins.items():
                    self._check_pin(component_cls.__name__, pin_name, pin)

    def _check_pin(self, component_name: str, pin_name: str, pin: dict):
        ref = f"{component_name}.{pin_name}"

        # Width must be strictly positive — zero-width ports break HFSS.
        self.assertGreater(
            pin["width"], 0.0,
            f"{ref}: pin width must be > 0, got {pin['width']}")

        normal = np.asarray(pin["normal"], dtype=float)
        tangent = np.asarray(pin["tangent"], dtype=float)

        # Normal and tangent should both be unit vectors. ``add_pin``
        # rounds them, so we tolerate a small numeric drift but reject
        # anything that's drifted into "this clearly isn't normalised"
        # territory.
        self.assertAlmostEqual(
            float(np.linalg.norm(normal)), 1.0, delta=self.UNIT_TOLERANCE,
            msg=f"{ref}: ||normal|| != 1; got {normal}")
        self.assertAlmostEqual(
            float(np.linalg.norm(tangent)), 1.0, delta=self.UNIT_TOLERANCE,
            msg=f"{ref}: ||tangent|| != 1; got {tangent}")

        # Perpendicularity. A port plane that isn't square produces
        # silent geometry errors at solve time.
        self.assertLess(
            abs(float(np.dot(normal, tangent))),
            self.PERPENDICULAR_TOLERANCE,
            f"{ref}: normal . tangent != 0; "
            f"normal={normal}, tangent={tangent}")

        # ``middle`` must equal the average of ``points``. If it
        # doesn't, downstream renderers place the port off-center.
        points = np.asarray(pin["points"], dtype=float)
        self.assertEqual(
            points.shape[0], 2,
            f"{ref}: expected 2 points, got shape {points.shape}")
        expected_middle = points.mean(axis=0)
        actual_middle = np.asarray(pin["middle"], dtype=float)
        # add_pin rounds to design.template_options.PRECISION; allow
        # a generous tolerance here.
        self.assertTrue(
            np.allclose(actual_middle, expected_middle, atol=1e-6),
            f"{ref}: middle {actual_middle} != mean(points) "
            f"{expected_middle}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
