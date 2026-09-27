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
"""Lumped Resonator, as shown in Phys. Rev. Appl. 10, 034050 (2018)."""

import numpy as np
from shapely.ops import unary_union

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent

# Points per quarter circle in the meander's arcs.
_ARC_POINTS = 500


def _arc(cx, cy, radius, start_deg, end_deg, n=_ARC_POINTS):
    """Points on a circular arc, from ``start_deg`` to ``end_deg``."""
    theta = np.radians(np.linspace(start_deg, end_deg, n))
    return np.column_stack([cx + radius * np.cos(theta), cy + radius * np.sin(theta)])


class ResonatorLumped(QComponent):
    """.. image::
        ResonatorLumped.png


    The base ResonatorLumped class
    Inherits the QComponent class

    A meandered resonator inside a rectangular metal perimeter. The trace
    starts at the middle of the bottom side (shorted to the perimeter),
    runs up ``initial``, meanders across the box with ``n_turns`` U-turns,
    and leaves through the break in the middle of the top side as the
    straight ``final`` segment.

    .. TODO: add resonator_lumped.png once asset is available for docs

    .. meta::
        :description: Lumped Resonator

    Pins:
        * ``pin_east``, ``pin_west``, ``pin_s`` -- midpoints of the east, west
          and south sides of the rectangular perimeter
        * ``pin_ne``, ``pin_nw``, ``pin_se``, ``pin_sw`` -- the four corners
        * ``pin_n`` -- open end of the ``final`` segment, outside the box when
          ``final`` is long enough to pass through the break

    Default Options:
        * pos_x: '0um' -- x-coordinate of the center of the box
        * pos_y: '0um' -- y-coordinate of the center of the box
        * orientation: '0' -- angle of rotation of the resonator
        * box_width: '5mm' -- the width of the rectangular perimeter
        * box_height: '5mm' -- the height of the rectangular perimeter
        * perimeter_thickness: '0.01mm' -- the width of the perimeter metal
        * res_width: '0.01mm' -- the width of the resonator trace
        * initial: '0.1mm' -- the length of the first straight segment, from
          the bottom of the perimeter
        * n_turns: '14' -- the number of U-turns in the meander
        * turn_radius: '0.1mm' -- the radius of the meander's bends
        * inner_space: '0.19mm' -- the gap between adjacent meander lines,
          edge to edge. The line pitch is ``inner_space + res_width``, at
          least ``2 * turn_radius``; above that, each U-turn gets a straight
          section between its two bends
        * outer_space: '0.1mm' -- the gap between the perimeter and the outer
          edge of the U-turns
        * final: '2.5mm' -- the length of the last straight segment, from the
          top of the meander up through the break
        * break_width: '0.2mm' -- the width of the break in the top of the
          perimeter
        * layer: '1' -- the layer of the component

    Previously the meander was fixed at 14 U-turns, and ``n_turns`` (then
    defaulting to 10) and ``inner_space`` had no effect. The current defaults
    reproduce that geometry.
    """

    default_options = Dict(
        pos_x="0 um",
        pos_y="0 um",
        orientation="0",
        box_width="5mm",
        box_height="5mm",
        perimeter_thickness="0.01mm",
        res_width="0.01mm",
        initial="0.1mm",
        n_turns="14",
        turn_radius="0.1mm",
        inner_space="0.19mm",
        outer_space="0.1mm",
        final="2.5mm",
        break_width="0.2mm",
        layer="1",
    )

    ##########################
    def make(self):
        """Builds the component."""
        p = self.parse_options()  # Parse the string options into numbers

        n_turns = round(p.n_turns)
        if n_turns < 1:
            raise ValueError(
                f"{self.name}: n_turns must be at least 1, got {p.n_turns}"
            )
        r = p.turn_radius
        pitch = p.inner_space + p.res_width
        if pitch < 2.0 * r * (1 - 1e-9):
            self.logger.warning(
                f"{self.name}: inner_space + res_width ({pitch:g}) is less than "
                f"2 * turn_radius ({2.0 * r:g}); using a line pitch of "
                "2 * turn_radius."
            )
        pitch = max(pitch, 2.0 * r)

        # Geometry is built with the bottom of the box at y=0 and centered in
        # x, then shifted so the box is centered on the origin.
        # draw the perimeter
        box_out = draw.rectangle(p.box_width, p.box_height, 0.0, 0.0)
        box_in = draw.rectangle(
            p.box_width - 2.0 * p.perimeter_thickness,
            p.box_height - 2.0 * p.perimeter_thickness,
            0.0,
            0.0,
        )
        perimeter = draw.subtract(box_out, box_in)
        perimeter = draw.translate(perimeter, xoff=0.0, yoff=0.5 * p.box_height)
        break_rect = draw.rectangle(p.break_width, p.break_width, 0.0, p.box_height)
        perimeter = draw.subtract(perimeter, break_rect)

        # x of the U-turn bend centers
        x_left = -0.5 * p.box_width + p.outer_space + r
        x_right = 0.5 * p.box_width - p.outer_space - r
        if x_left >= -r:
            self.logger.warning(
                f"{self.name}: box_width is too small for outer_space and "
                "turn_radius; the meander overlaps itself."
            )

        trace = {}
        y = p.perimeter_thickness + p.initial
        trace["initial"] = draw.LineString([(0.0, p.perimeter_thickness), (0.0, y)])
        # quarter turn to the left, then a half line to the left bend
        trace["arc_start"] = draw.LineString(_arc(-r, y, r, 0, 90, 2 * _ARC_POINTS))
        y += r
        trace["line_0"] = draw.LineString([(-r, y), (x_left, y)])
        for k in range(1, n_turns + 1):
            if k % 2:  # left U-turn, then head right
                pts = np.vstack(
                    [
                        _arc(x_left, y + r, r, 270, 180),
                        _arc(x_left, y + pitch - r, r, 180, 90),
                    ]
                )
            else:  # right U-turn, then head left
                pts = np.vstack(
                    [
                        _arc(x_right, y + r, r, -90, 0),
                        _arc(x_right, y + pitch - r, r, 0, 90),
                    ]
                )
            trace[f"turn_{k}"] = draw.LineString(pts)
            y += pitch
            if k < n_turns:
                trace[f"line_{k}"] = draw.LineString([(x_left, y), (x_right, y)])
        # half line back to the center, then a quarter turn up
        if n_turns % 2:
            trace[f"line_{n_turns}"] = draw.LineString([(x_left, y), (-r, y)])
            trace["arc_end"] = draw.LineString(
                _arc(-r, y + r, r, 270, 360, 2 * _ARC_POINTS)
            )
        else:
            trace[f"line_{n_turns}"] = draw.LineString([(x_right, y), (r, y)])
            trace["arc_end"] = draw.LineString(
                _arc(r, y + r, r, 270, 180, 2 * _ARC_POINTS)
            )
        y += r
        trace["final"] = draw.LineString([(0.0, y), (0.0, y + p.final)])

        self._warn_if_trace_hits_perimeter(trace, perimeter, p)
        if y + p.final <= p.box_height:
            self.logger.warning(
                f"{self.name}: the final segment ends inside the box "
                f"(final={p.final:g}); it needs to be longer than "
                f"{p.box_height - y:g} to exit through the break."
            )

        # Pins, as (inner, outer) points in the same frame as the geometry.
        w, h, t = p.box_width, p.box_height, p.perimeter_thickness
        pins = {
            "pin_east": [(0.5 * w - t, 0.5 * h), (0.5 * w, 0.5 * h)],
            "pin_ne": [(0.5 * w - t, h - t), (0.5 * w, h)],
            "pin_se": [(0.5 * w - t, t), (0.5 * w, 0.0)],
            "pin_nw": [(-0.5 * w + t, h - t), (-0.5 * w, h)],
            "pin_west": [(-0.5 * w + t, 0.5 * h), (-0.5 * w, 0.5 * h)],
            "pin_sw": [(-0.5 * w + t, t), (-0.5 * w, 0.0)],
            "pin_s": [(0.0, t), (0.0, 0.0)],
        }
        pins = {name: draw.LineString(pts) for name, pts in pins.items()}
        pins["pin_n"] = trace["final"]

        # center the box on the origin, then rotate and translate
        objects = [perimeter, trace, pins]
        objects = draw.translate(objects, 0.0, -0.5 * p.box_height)
        objects = draw.rotate(objects, p.orientation, origin=(0, 0))
        objects = draw.translate(objects, xoff=p.pos_x, yoff=p.pos_y)
        perimeter, trace, pins = objects

        self.add_qgeometry(
            "poly", {"perimeter": perimeter}, layer=p.layer, subtract=False
        )
        self.add_qgeometry(
            "path", trace, layer=p.layer, subtract=False, width=p.res_width
        )

        for name, line in pins.items():
            width = p.res_width if name == "pin_n" else 0.01
            self.add_pin(
                name, points=np.array(line.coords), width=width, input_as_norm=True
            )

    def _warn_if_trace_hits_perimeter(self, trace, perimeter, p):
        """Warn when the meander (or the final segment) overlaps the perimeter
        metal. ``initial`` is excluded: it is meant to touch the bottom side."""
        body = [line for name, line in trace.items() if name != "initial"]
        swept = unary_union(
            [line.buffer(0.5 * p.res_width, cap_style=2) for line in body]
        )
        if swept.intersection(perimeter).area > 1e-12:
            self.logger.warning(
                f"{self.name}: the resonator trace overlaps the perimeter. "
                "Increase box_width/box_height or break_width, or reduce "
                "n_turns, turn_radius, inner_space or initial."
            )
