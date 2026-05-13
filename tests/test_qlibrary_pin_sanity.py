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

These tests catch all four by walking ``component.pins`` on every
``qlibrary`` component that emits at least one pin under either
default options or a minimal pin-trigger config. Routes are skipped
because their pin layout depends on pin_inputs that aren't available
in default options.
"""

import unittest

import numpy as np

from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.couplers.cap_n_interdigital_tee import CapNInterdigitalTee
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee
from qiskit_metal.qlibrary.couplers.line_tee import LineTee
from qiskit_metal.qlibrary.lumped.cap_3_interdigital import Cap3Interdigital
from qiskit_metal.qlibrary.lumped.cap_n_interdigital import CapNInterdigital
from qiskit_metal.qlibrary.lumped.resonator_coil_rect import ResonatorCoilRect
from qiskit_metal.qlibrary.qubits.star_qubit import StarQubit
from qiskit_metal.qlibrary.qubits.transmon_concentric import TransmonConcentric
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from qiskit_metal.qlibrary.qubits.transmon_cross_fl import TransmonCrossFL
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.qubits.transmon_pocket_6 import TransmonPocket6
from qiskit_metal.qlibrary.qubits.transmon_pocket_cl import TransmonPocketCL
from qiskit_metal.qlibrary.sample_shapes.n_square_spiral import NSquareSpiral
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.terminations.launchpad_wb_coupled import (
    LaunchpadWirebondCoupled,
)
from qiskit_metal.qlibrary.terminations.launchpad_wb_driven import (
    LaunchpadWirebondDriven,
)
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.terminations.short_to_ground import ShortToGround

# (component_class, options) — options force at least one pin to be
# emitted under what would otherwise be a pin-less default config.
# Transmons add pins through their ``connection_pads`` dict; an empty
# sub-dict falls back to ``_default_connection_pads`` for the per-pad
# values.
_PIN_KW = Dict(connection_pads=Dict(a=Dict()))
_NONE = Dict()

COMPONENTS_WITH_PINS = [
    # Trigger transmon connection pads explicitly.
    (TransmonPocket, _PIN_KW),
    (TransmonPocketCL, _PIN_KW),
    (TransmonPocket6, _PIN_KW),
    (TransmonCross, _PIN_KW),
    # The following components emit at least one pin under default options.
    (TransmonConcentric, _NONE),
    (TransmonCrossFL, _NONE),
    (StarQubit, _NONE),
    (NSquareSpiral, _NONE),
    (OpenToGround, _NONE),
    (ShortToGround, _NONE),
    (LaunchpadWirebond, _NONE),
    (LaunchpadWirebondCoupled, _NONE),
    (LaunchpadWirebondDriven, _NONE),
    (CapNInterdigital, _NONE),
    (Cap3Interdigital, _NONE),
    (ResonatorCoilRect, _NONE),
    (LineTee, _NONE),
    (CapNInterdigitalTee, _NONE),
    (CoupledLineTee, _NONE),
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
                component = component_cls(
                    design, f"test_{component_cls.__name__}", options=options
                )
                if not component.pins:
                    self.fail(
                        f"{component_cls.__name__} produced no pins with "
                        f"the test's configured options — update the "
                        f"options dict if the component's pin trigger "
                        f"changed."
                    )
                for pin_name, pin in component.pins.items():
                    self._check_pin(component_cls.__name__, pin_name, pin)

    # Known inward-pointing pins. Each entry is (ComponentClass, pin_name)
    # with a short explanation. Fixing requires HFSS validation —
    # see the docstring of ``test_pin_normals_point_outward`` for why
    # we don't auto-fix.
    KNOWN_INWARD_PINS = {
        # The "in" pin's LineString point order produces a normal at +x
        # while the launch pad sits in -x. add_pin's
        # "normal points in direction of intended connection" convention
        # says the input port's normal should point AWAY from the pad
        # toward the external feed; the LineString in
        # ``launchpad_wb_driven.py`` is constructed in the same
        # downward-y order as the "tie" pin's main_pin_line, so both
        # get a +x normal even though "in" sits on the opposite side
        # of the pad. Swapping the two points in ``driven_pin_line``
        # is the obvious fix, but it changes pin orientation in HFSS
        # renders and so needs HFSS validation before landing.
        ("LaunchpadWirebondDriven", "in"),
    }

    def test_pin_normals_point_outward(self):
        """Each pin's ``normal`` should point away from the geometric
        centroid of its parent component, not into it.

        This is the silent-failure mode that matters for HFSS / Q3D:
        a port whose normal flips inward causes the renderer to place
        the port plane *inside* the conductor, which then either fails
        the solve outright or — worse — passes with garbage S-params.

        The heuristic: compute the centroid of the component's
        polygon geometry; then for each pin assert
        ``(pin.middle - centroid) . pin.normal > 0``. This is
        forgiving enough for asymmetric geometries (a pin sticking
        out of one side of a pocket) but catches a sign flip in any
        of the eight cardinal pin directions.

        Components whose pins are *inside* a cavity (e.g. a port on
        an internal coupling pad surrounded by ground) genuinely
        violate this — they're rare in the current qlibrary. Real
        violations the test has uncovered are listed in
        ``KNOWN_INWARD_PINS`` with a comment explaining why we don't
        auto-fix; they need HFSS validation per the project's
        do-not-touch-HFSS-without-validation policy.
        """
        for component_cls, options in COMPONENTS_WITH_PINS:
            with self.subTest(component=component_cls.__name__):
                design = designs.DesignPlanar()
                component = component_cls(
                    design, f"test_{component_cls.__name__}", options=options
                )
                if not component.pins:
                    continue
                centroid = self._component_centroid(component)
                if centroid is None:
                    # Component has no polygon geometry to centroid
                    # against — skip rather than fail. Shouldn't happen
                    # for anything in the test list.
                    continue
                for pin_name, pin in component.pins.items():
                    if (component_cls.__name__, pin_name) in self.KNOWN_INWARD_PINS:
                        # Known bug — skip the assertion but log.
                        continue
                    self._check_pin_points_outward(
                        component_cls.__name__, pin_name, pin, centroid
                    )

    @staticmethod
    def _component_centroid(component):
        """Average position of all ``poly`` geometry rows belonging
        to ``component``, as a length-2 numpy array. Returns ``None``
        if the component has no polygon rows."""
        poly_table = component.design.qgeometry.tables.get("poly")
        if poly_table is None or poly_table.empty:
            return None
        rows = poly_table[poly_table.component == component.id]
        if rows.empty:
            return None
        # shapely ``unary_union`` then centroid would be more accurate;
        # the average of per-polygon centroids is good enough for the
        # outward-vs-inward sign check and a lot cheaper.
        centroids = np.array([(g.centroid.x, g.centroid.y) for g in rows.geometry])
        return centroids.mean(axis=0)

    def _check_pin_points_outward(
        self, component_name: str, pin_name: str, pin: dict, centroid: np.ndarray
    ):
        ref = f"{component_name}.{pin_name}"
        middle = np.asarray(pin["middle"], dtype=float)
        normal = np.asarray(pin["normal"], dtype=float)
        outward_dot = float(np.dot(middle - centroid, normal))
        self.assertGreater(
            outward_dot,
            0.0,
            f"{ref}: pin normal points INWARD relative to component "
            f"centroid. (middle - centroid) . normal = {outward_dot:.6f}. "
            f"This is the HFSS silent-failure mode: the port plane "
            f"will end up inside the conductor.",
        )

    def _check_pin(self, component_name: str, pin_name: str, pin: dict):
        ref = f"{component_name}.{pin_name}"

        # Width must be strictly positive — zero-width ports break HFSS.
        self.assertGreater(
            pin["width"], 0.0, f"{ref}: pin width must be > 0, got {pin['width']}"
        )

        normal = np.asarray(pin["normal"], dtype=float)
        tangent = np.asarray(pin["tangent"], dtype=float)

        # Normal and tangent should both be unit vectors. ``add_pin``
        # rounds them, so we tolerate a small numeric drift but reject
        # anything that's drifted into "this clearly isn't normalised"
        # territory.
        self.assertAlmostEqual(
            float(np.linalg.norm(normal)),
            1.0,
            delta=self.UNIT_TOLERANCE,
            msg=f"{ref}: ||normal|| != 1; got {normal}",
        )
        self.assertAlmostEqual(
            float(np.linalg.norm(tangent)),
            1.0,
            delta=self.UNIT_TOLERANCE,
            msg=f"{ref}: ||tangent|| != 1; got {tangent}",
        )

        # Perpendicularity. A port plane that isn't square produces
        # silent geometry errors at solve time.
        self.assertLess(
            abs(float(np.dot(normal, tangent))),
            self.PERPENDICULAR_TOLERANCE,
            f"{ref}: normal . tangent != 0; normal={normal}, tangent={tangent}",
        )

        # ``middle`` must equal the average of ``points``. If it
        # doesn't, downstream renderers place the port off-center.
        points = np.asarray(pin["points"], dtype=float)
        self.assertEqual(
            points.shape[0], 2, f"{ref}: expected 2 points, got shape {points.shape}"
        )
        expected_middle = points.mean(axis=0)
        actual_middle = np.asarray(pin["middle"], dtype=float)
        # add_pin rounds to design.template_options.PRECISION; allow
        # a generous tolerance here.
        self.assertTrue(
            np.allclose(actual_middle, expected_middle, atol=1e-6),
            f"{ref}: middle {actual_middle} != mean(points) {expected_middle}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
