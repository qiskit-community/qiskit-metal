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
"""``RouteMeander`` reaches ``total_length`` or says why not (#1225, #1234).

* #1234: the meander was sized from the straight-line lead lengths, while
  ``QRoute.length`` subtracts ``(2 - pi/2) * fillet`` per corner, including
  the corners of jogged leads. ``adjust_length`` could not place that slack
  when the first and last wiggles were blocked, so jogged routes came out
  short by a constant amount at any ``total_length``. ``make`` now refits the
  meander's target length when the first build misses.
* #1225: some ``(fillet, meander.spacing)`` pairs were short with no warning;
  a ``total_length`` below the shortest route crashed with an IndexError.
  ``make`` now warns whenever the drawn length differs from
  ``total_length``, and draws the shortest route (with a warning naming the
  minimum length) when the request is impossible.
"""

import logging
import unittest
from collections import OrderedDict
from unittest import mock

from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.terminations.short_to_ground import ShortToGround
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander

ZIGZAG = [["L", "300um"], ["R", "300um"], ["R", "300um"], ["L", "300um"]]
DETOUR = [["R", "500um"], ["L", "2500um"], ["L", "500um"]]


def _facing_route(total, jogs_start=None, jogs_end=None):
    """The #1234 reproduction: two opens 3 mm apart, facing away."""
    d = designs.DesignPlanar()
    d.overwrite_enabled = True
    OpenToGround(d, "A", options=dict(pos_x="-1.5mm", pos_y="0mm", orientation="180"))
    OpenToGround(d, "B", options=dict(pos_x="1.5mm", pos_y="0mm", orientation="0"))
    lead = Dict(start_straight="100um", end_straight="100um")
    if jogs_start:
        lead.start_jogged_extension = OrderedDict(enumerate(jogs_start))
    if jogs_end:
        lead.end_jogged_extension = OrderedDict(enumerate(jogs_end))
    return RouteMeander(
        d,
        "R",
        options=Dict(
            pin_inputs=Dict(
                start_pin=Dict(component="A", pin="open"),
                end_pin=Dict(component="B", pin="open"),
            ),
            lead=lead,
            fillet="99um",
            total_length=total,
            meander=Dict(spacing="200um", asymmetry="0um"),
        ),
    )


def _corner_route(total, fillet, spacing):
    """The #1225 reproduction: an open and a short at right angles."""
    d = designs.DesignPlanar()
    d.overwrite_enabled = True
    d.chips.main.size.size_x = d.chips.main.size.size_y = "5mm"
    OpenToGround(d, "A", options=dict(pos_x="0.5mm", pos_y="-0.5mm", orientation="180"))
    ShortToGround(d, "B", options=dict(pos_x="1.6mm", pos_y="1.2mm", orientation="90"))
    return RouteMeander(
        d,
        "R",
        options=Dict(
            total_length=total,
            fillet=fillet,
            lead=Dict(start_straight="150um", end_straight="100um"),
            meander=Dict(spacing=spacing, asymmetry="0um"),
            pin_inputs=Dict(
                start_pin=Dict(component="A", pin="open"),
                end_pin=Dict(component="B", pin="short"),
            ),
        ),
    )


def _mm(value: str) -> float:
    assert value.endswith("mm")
    return float(value[:-2])


class TestJoggedLeadsReachTotalLength(unittest.TestCase):
    """#1234."""

    def test_jogged_leads(self):
        for label, total, kw in [
            ("4 jogs at start", "4mm", dict(jogs_start=ZIGZAG)),
            ("4 jogs at end", "4mm", dict(jogs_end=ZIGZAG)),
            ("3 jogs at end", "5mm", dict(jogs_end=DETOUR)),
            ("3 jogs at end", "6mm", dict(jogs_end=DETOUR)),
            ("3 jogs at end", "8mm", dict(jogs_end=DETOUR)),
        ]:
            with self.subTest(label=label, total=total):
                route = _facing_route(total, **kw)
                self.assertEqual(route.status, "good")
                self.assertAlmostEqual(route.length, _mm(total), delta=1e-5)

    def test_straight_leads_are_built_once(self):
        """A route the first build gets right is not refitted, so its
        geometry is exactly what it was before the refit existed."""
        for total in ("5mm", "7mm"):
            with self.subTest(total=total):
                with mock.patch.object(
                    RouteMeander,
                    "_build_meander",
                    autospec=True,
                    side_effect=RouteMeander._build_meander,
                ) as spy:
                    route = _facing_route(total)
                self.assertEqual(spy.call_count, 1)
                self.assertAlmostEqual(route.length, _mm(total), delta=1e-5)


class TestLengthMismatchIsReported(unittest.TestCase):
    """#1225."""

    def test_fillet_spacing_pairs_reach_total_length(self):
        # 60um/250um was 18.2 um short and 90um/250um 46.5 um short, silently.
        for fillet in ("60um", "90um"):
            for spacing in ("200um", "250um", "300um"):
                with self.subTest(fillet=fillet, spacing=spacing):
                    route = _corner_route("4.1235mm", fillet, spacing)
                    self.assertEqual(route.status, "good")
                    self.assertAlmostEqual(route.length, 4.1235, delta=1e-5)

    def test_impossible_length_draws_shortest_route_with_warning(self):
        """total_length below the shortest route used to crash with
        ``IndexError: index -3 is out of bounds``."""
        with self.assertLogs("metal", level="WARNING") as cm:
            route = _corner_route("1.0mm", "50um", "150um")
        self.assertEqual(route.status, "good")
        self.assertGreater(route.length, 1.0)
        messages = [m for m in cm.output if "minimum route length" in m]
        self.assertEqual(len(messages), 1, cm.output)
        self.assertIn("total_length=1mm", messages[0])
        self.assertIn(f"{route.length:.6g}mm", messages[0])

    def test_unreachable_length_is_warned(self):
        """When the meander cannot absorb the difference the route is still
        drawn, with a warning giving both lengths."""
        d = designs.DesignPlanar()
        d.overwrite_enabled = True
        OpenToGround(d, "A", options=dict(pos_x="0mm", pos_y="0mm", orientation="270"))
        OpenToGround(
            d, "B", options=dict(pos_x="0mm", pos_y="1.81mm", orientation="90")
        )
        with self.assertLogs("metal", level="WARNING") as cm:
            route = RouteMeander(
                d,
                "R",
                options=Dict(
                    pin_inputs=Dict(
                        start_pin=Dict(component="A", pin="open"),
                        end_pin=Dict(component="B", pin="open"),
                    ),
                    lead=Dict(start_straight="180um", end_straight="180um"),
                    fillet="100um",
                    total_length="2.0mm",
                    meander=Dict(spacing="450um", asymmetry="0um"),
                ),
            )
        self.assertEqual(route.status, "good")
        self.assertGreater(abs(route.length - 2.0), 1e-4)
        messages = [m for m in cm.output if "differs from total_length=2mm" in m]
        self.assertEqual(len(messages), 1, cm.output)

    def test_no_warning_when_length_is_reached(self):
        logger = logging.getLogger("metal")
        with self.assertLogs("metal", level="WARNING") as cm:
            _corner_route("4.1235mm", "60um", "200um")
            logger.warning("sentinel")
        self.assertFalse(
            [m for m in cm.output if "total_length" in m and "sentinel" not in m],
            cm.output,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
