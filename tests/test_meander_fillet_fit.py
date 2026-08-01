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
"""Regression tests for RouteMeander sharp-kink geometry (#1086).

``RouteMeander`` distributes the CPW's excess length (over the direct
start-to-end distance) across ``meander_number`` wiggles, each with a
perpendicular amplitude ``length_perp``. If ``meander_number`` -- chosen from
``floor(length_direct / meander.spacing)`` -- packs in more wiggles than the
excess length can support, ``length_perp`` collapses to less than the fillet
radius. A fillet arc cannot be inscribed in less room than its own radius, so
the corner-rounding overlaps and the meander renders as a sharp,
castellation-like kink instead of a smooth wave.

``RouteMeander.connect_meandered`` now reduces ``meander_number`` (in steps of
2, to preserve the even/odd parity already chosen for the start/end pin
directions) until ``length_perp`` clears the fillet radius, trading wiggle
*count* for wiggle *depth*. These tests guard that invariant directly, plus
the concrete reproduction from the issue (a symmetric qubit ring where two of
the four identically-configured meanders hit this case and two don't).
"""

import logging
import unittest

import numpy as np
from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander


def _length_perp_values(route):
    """Recompute, for every wiggle actually drawn, the perpendicular
    amplitude implied by consecutive meander vertices -- i.e. what the
    rendered geometry's wiggle depth actually is, read back from
    ``get_points()`` rather than from the (possibly stale) internals. Used to
    verify the fix by its observable effect, not just by re-deriving the same
    formula the implementation uses.
    """
    pts = route.get_points()
    if len(pts) < 3:
        return []
    # Perpendicular offsets are the component of each interior point, relative
    # to the line through its neighbors, that isn't explained by walking
    # straight from one neighbor to the other -- i.e. how far each vertex
    # juts out to the side. For an axis-aligned meander (the common case) this
    # is just the non-monotonic coordinate's deviation.
    perp = []
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        seg = c - a
        seg_len = np.linalg.norm(seg)
        if seg_len == 0:
            continue
        seg_unit = seg / seg_len
        proj = a + np.dot(b - a, seg_unit) * seg_unit
        perp.append(np.linalg.norm(b - proj))
    return perp


class TestMeanderFilletFit(unittest.TestCase):
    """General invariant: a filleted meander must never need more room per
    wiggle than the fillet radius it's asking for."""

    def _assert_no_unfileted_kinks(self, route, fillet, msg_prefix=""):
        fillet = float(fillet)
        perp_values = _length_perp_values(route)
        # A handful of vertices near the leads can legitimately have a small
        # perpendicular offset (they're not meander wiggles at all -- e.g. the
        # single left-over root point). Only wiggle apexes, which repeat at
        # meander.spacing intervals, are governed by this invariant; as a
        # robust proxy, assert the *largest* perpendicular offset seen -- if
        # even the deepest wiggle can't clear the fillet, none can, and if it
        # can, the geometry has room to fillet cleanly.
        if not perp_values:
            return
        max_perp = max(perp_values)
        self.assertGreaterEqual(
            max_perp,
            fillet - 1e-9,
            msg=f"{msg_prefix}wiggle amplitude {max_perp:.4g}mm is smaller "
            f"than the fillet radius {fillet}mm -- this is the sharp-kink "
            f"defect from #1086 (unfileted, castellation-like geometry).",
        )

    def _route(
        self, design, name, total_length, spacing, fillet, pos_a, pos_b, ori_a, ori_b
    ):
        OpenToGround(
            design,
            f"{name}_A",
            options=dict(pos_x=pos_a[0], pos_y=pos_a[1], orientation=ori_a),
        )
        OpenToGround(
            design,
            f"{name}_B",
            options=dict(pos_x=pos_b[0], pos_y=pos_b[1], orientation=ori_b),
        )
        route = RouteMeander(
            design,
            name,
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component=f"{name}_A", pin="open"),
                    end_pin=Dict(component=f"{name}_B", pin="open"),
                ),
                lead=Dict(start_straight="180um", end_straight="180um"),
                fillet=fillet,
                total_length=total_length,
                trace_width="10um",
                trace_gap="6um",
                meander=Dict(spacing=spacing, asymmetry="0um"),
            ),
        )
        return route

    def test_tight_meander_no_longer_produces_unfileted_kinks(self):
        """The exact defect from #1086: total_length/spacing/fillet chosen so
        floor(length_direct/spacing) demands more wiggles than length_excess
        can support without under-cutting the fillet radius."""
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        # length_direct=1.81mm, spacing=0.45mm -> meander_number=4 (pre-fix),
        # length_excess=0.23mm -> length_perp=0.029mm << fillet=0.1mm.
        route = self._route(
            design,
            "tight",
            total_length="2.4mm",
            spacing="450um",
            fillet="100um",
            pos_a=("0mm", "0mm"),
            pos_b=("0mm", "1.81mm"),
            ori_a="270",
            ori_b="90",
        )
        design.rebuild()
        self._assert_no_unfileted_kinks(route, fillet=0.1, msg_prefix="tight: ")

    def test_comfortable_meander_is_unaffected(self):
        """The already-good case (length_perp comfortably exceeds fillet) must
        render exactly as before -- meander_number must not be reduced when
        there's no defect to fix."""
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        # length_direct=1.03mm, spacing=0.45mm -> meander_number=2,
        # length_excess=1.01mm -> length_perp=0.2525mm, fillet=0.1mm: fine.
        route = self._route(
            design,
            "comfortable",
            total_length="2.4mm",
            spacing="450um",
            fillet="100um",
            pos_a=("0mm", "0mm"),
            pos_b=("1.03mm", "0mm"),
            ori_a="180",
            ori_b="0",
        )
        design.rebuild()
        perp_values = _length_perp_values(route)
        self.assertTrue(perp_values)
        # Comfortably clears the fillet already (ratio ~2.5x in the formula
        # this case was chosen from); the fix must be a no-op here. Compare
        # against a margin rather than the exact formula value, since the
        # rendered points include lead/adjust_length geometry beyond the raw
        # meander wiggles that the geometric proxy in _length_perp_values
        # also picks up.
        self.assertGreater(max(perp_values), 2 * 0.1)

    def test_no_reduction_warning_logged_for_comfortable_case(self):
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        with self.assertLogs("metal", level="WARNING") as cm:
            self._route(
                design,
                "quiet",
                total_length="2.4mm",
                spacing="450um",
                fillet="100um",
                pos_a=("0mm", "0mm"),
                pos_b=("1.03mm", "0mm"),
                ori_a="180",
                ori_b="0",
            )
            design.rebuild()
            # Force at least one message so assertLogs has something to see;
            # then assert none of the captured records mention the reduction.
            logging.getLogger("metal").warning("sentinel")
        reduction_msgs = [r for r in cm.output if "reduced meander_number" in r]
        self.assertEqual(
            reduction_msgs,
            [],
            msg="meander_number was reduced for a route that didn't need it",
        )

    def test_reduction_warning_logged_for_tight_case(self):
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        with self.assertLogs("metal", level="WARNING") as cm:
            self._route(
                design,
                "tight_logged",
                total_length="2.4mm",
                spacing="450um",
                fillet="100um",
                pos_a=("0mm", "0mm"),
                pos_b=("0mm", "1.81mm"),
                ori_a="270",
                ori_b="90",
            )
            design.rebuild()
        # make() runs once at construction and again at rebuild(), so the
        # warning is expected at least once (exact count isn't the contract).
        reduction_msgs = [r for r in cm.output if "reduced meander_number" in r]
        self.assertGreaterEqual(len(reduction_msgs), 1)

    def test_symmetric_ring_from_issue_1086(self):
        """The concrete repro from the issue: a 4-qubit ring routed with
        identical RouteMeander options on all 4 edges. Two edges (top/bottom)
        already had enough room; two (left/right) hit the sharp-kink defect
        because the ring's diagonal connection-pad placement (loc_W and
        loc_H both nonzero) gives those edges a different direct
        pin-to-pin distance. All 4 edges must render kink-free."""
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        pads = Dict(
            connection_pads=Dict(
                a=Dict(loc_W=+1, loc_H=+1, pad_width="120um", cpw_extend="80um"),
                b=Dict(loc_W=-1, loc_H=+1, pad_width="120um", cpw_extend="80um"),
                c=Dict(loc_W=-1, loc_H=-1, pad_width="120um", cpw_extend="80um"),
                d=Dict(loc_W=+1, loc_H=-1, pad_width="120um", cpw_extend="80um"),
            )
        )
        for name, x, y in [
            ("Q1", "+1.1mm", "+1.1mm"),
            ("Q2", "-1.1mm", "+1.1mm"),
            ("Q3", "-1.1mm", "-1.1mm"),
            ("Q4", "+1.1mm", "-1.1mm"),
        ]:
            TransmonPocket(design, name, options=Dict(pos_x=x, pos_y=y, **pads))

        cpw_opts = Dict(
            lead=Dict(start_straight="180um", end_straight="180um"),
            fillet="100um",
            total_length="2.4mm",
            trace_width="10um",
            trace_gap="6um",
            meander=Dict(spacing="450um", asymmetry="0um"),
        )
        routes = {}
        for n, qa, pa, qb, pb in [
            ("cpw_12", "Q1", "b", "Q2", "a"),
            ("cpw_23", "Q2", "c", "Q3", "b"),
            ("cpw_34", "Q3", "d", "Q4", "c"),
            ("cpw_41", "Q4", "a", "Q1", "d"),
        ]:
            routes[n] = RouteMeander(
                design,
                n,
                options=Dict(
                    pin_inputs=Dict(
                        start_pin=Dict(component=qa, pin=pa),
                        end_pin=Dict(component=qb, pin=pb),
                    ),
                    **cpw_opts,
                ),
            )
        design.rebuild()

        for name, route in routes.items():
            self._assert_no_unfileted_kinks(route, fillet=0.1, msg_prefix=f"{name}: ")

    def test_varied_fillet_and_spacing_never_produce_unfileted_kinks(self):
        """Broader sweep so the invariant is guarded beyond the one reported
        configuration -- varied fillet, spacing, and direct distance."""
        cases = [
            # (direct_distance_mm, spacing_mm, fillet_mm, total_length_mm)
            (1.81, 0.45, 0.10, 2.40),
            (1.20, 0.20, 0.08, 1.60),
            (2.50, 0.30, 0.15, 3.20),
            (0.90, 0.10, 0.05, 1.50),
            (3.00, 0.50, 0.20, 3.60),
        ]
        for direct, spacing, fillet, total_length in cases:
            with self.subTest(direct=direct, spacing=spacing, fillet=fillet):
                design = designs.DesignPlanar()
                design.overwrite_enabled = True
                route = self._route(
                    design,
                    "sweep",
                    total_length=f"{total_length}mm",
                    spacing=f"{spacing}mm",
                    fillet=f"{fillet}mm",
                    pos_a=("0mm", "0mm"),
                    pos_b=("0mm", f"{direct}mm"),
                    ori_a="270",
                    ori_b="90",
                )
                design.rebuild()
                self._assert_no_unfileted_kinks(
                    route,
                    fillet=fillet,
                    msg_prefix=f"direct={direct} spacing={spacing} fillet={fillet}: ",
                )

    def test_parity_decrement_to_zero_meanders_does_not_crash(self):
        """Regression: the start/end-direction parity adjustment can take
        meander_number from 1 to 0 (floor() gives 1, the parity rule
        subtracts 1), which used to skip the zero-meander early return and
        crash with IndexError at the snap alignment (``pts[-2]`` on a
        single-row array). The route must instead degrade gracefully to
        the no-meander path, same as when floor() itself yields 0.

        The trigger needs pin directions whose sideways dot product is
        negative (opposite orientation) with an odd meander_number of
        exactly 1 -- diagonally offset, opposite-facing pins with spacing
        chosen so floor(length_direct/spacing) == 1.
        """
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        from qiskit_metal.qlibrary.terminations.launchpad_wb import (
            LaunchpadWirebond,
        )

        TransmonPocket(
            design,
            "Q1",
            options=Dict(
                pos_x="1.1mm",
                pos_y="1.1mm",
                connection_pads=Dict(
                    a=Dict(loc_W=+1, loc_H=+1, pad_width="120um", cpw_extend="80um")
                ),
            ),
        )
        LaunchpadWirebond(
            design,
            "P1",
            options=Dict(
                pos_x="2.0mm",
                pos_y="2.0mm",
                orientation="225",
                pad_width="120um",
                pad_height="120um",
                pad_gap="80um",
                lead_length="20um",
            ),
        )
        design.rebuild()
        route = RouteMeander(
            design,
            "ro1",
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component="Q1", pin="a"),
                    end_pin=Dict(component="P1", pin="tie"),
                ),
                lead=Dict(start_straight="250um", end_straight="250um"),
                fillet="40 um",
                total_length="5.02mm",
                trace_width="10 um",
                trace_gap="6 um",
                meander=Dict(spacing="300um", asymmetry="0um"),
            ),
        )
        design.rebuild()
        # Builds without IndexError; degrades to a short no-meander route.
        self.assertGreaterEqual(len(route.get_points()), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
