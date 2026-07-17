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
"""Airbridge — a ground-plane crossover that hops over a CPW trace."""

import numpy as np

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent


class Airbridge(QComponent):
    """A single airbridge: two base-metal landing pads joined by an elevated
    bridge span that crosses over a CPW.

    Unlike a GDS-export-only helper, this is a first-class ``QComponent`` — its
    geometry lives in the design's QGeometry, so it renders in ``qm.view`` and
    is exported by every renderer (GDS today; a 3D/Ansys span is tracked
    separately). The bridge metal and the landing pads are emitted on separate
    layers so the two-step fabrication (base metal + bridge metal) is
    representable.

    .. image::
        Airbridge.png

    The geometry is intentionally factored as an *elevated crossover* (a span
    that sits above the base layer, joining two feet). Only the airbridge uses
    it today; the same shape could back other elevated interconnects in future
    without changing this class.

    Default Options:
        * crossover_length: '22um' -- Gap the bridge spans, foot-to-foot.
          Usually about ``cpw_width + 2 * cpw_gap`` of the CPW being crossed.
        * bridge_width: '7.5um' -- Width of the elevated bridge span.
        * pad_width: '11um' -- Width of each base landing pad (across the CPW).
        * pad_length: '11um' -- Length of each base landing pad (along the CPW).
        * bridge_layer: '30' -- Layer of the elevated bridge span.
        * pad_layer: '31' -- Layer of the two base landing pads.
    """

    default_options = Dict(
        crossover_length="22um",
        bridge_width="7.5um",
        pad_width="11um",
        pad_length="11um",
        bridge_layer="30",
        pad_layer="31",
    )
    """Default drawing options"""

    component_metadata = Dict(short_name="airbridge", _qgeometry_table_poly="True")
    """Component metadata"""

    TOOLTIP = """Ground-plane crossover (airbridge) that hops over a CPW."""

    def make(self):
        """Convert self.options into QGeometry."""
        p = self.parse_options()

        crossover_length = p.crossover_length
        bridge_width = p.bridge_width
        pad_width = p.pad_width
        pad_length = p.pad_length

        # Center-to-center distance between the two landing pads.
        pad_offset = crossover_length / 2.0 + pad_length / 2.0

        # Two base landing pads (feet), one on each side of the crossing.
        left_pad = draw.rectangle(pad_length, pad_width, -pad_offset, 0)
        right_pad = draw.rectangle(pad_length, pad_width, +pad_offset, 0)
        pads = draw.union(left_pad, right_pad)

        # Elevated span. Length reaches both pad centers so it overlaps the
        # feet and forms a single connected conductor once fabricated.
        span = draw.rectangle(crossover_length + pad_length, bridge_width, 0, 0)

        # Reposition the whole crossover.
        geom = [span, pads]
        geom = draw.rotate(geom, p.orientation, origin=(0, 0))
        geom = draw.translate(geom, p.pos_x, p.pos_y)
        span, pads = geom

        self.add_qgeometry(
            "poly", {"bridge": span}, layer=p.bridge_layer, subtract=False
        )
        self.add_qgeometry("poly", {"pads": pads}, layer=p.pad_layer, subtract=False)


def _segment_placements(p0, p1, pitch, margin):
    """Evenly-spaced airbridge centers along one straight CPW segment.

    Args:
        p0, p1 (np.ndarray): segment endpoints (x, y), in design units.
        pitch (float): target center-to-center spacing between bridges.
        margin (float): keep-out distance from each segment end (so bridges
            do not land on pins or fillet corners).

    Returns:
        list[tuple[float, float, float]]: ``(x, y, orientation_deg)`` per
        bridge, oriented perpendicular to the segment so the span crosses it.
        Empty if the segment is too short to hold a bridge clear of both ends.
    """
    v = np.asarray(p1, dtype=float) - np.asarray(p0, dtype=float)
    length = float(np.hypot(v[0], v[1]))
    usable = length - 2.0 * margin
    if usable < 0:
        return []

    theta = np.arctan2(v[1], v[0])
    orientation = np.degrees(theta) + 90.0  # span crosses the trace
    # n bridges, evenly spaced and centered on the segment midpoint.
    n = int(np.floor(usable / pitch)) + 1
    midpoint = (np.asarray(p0, dtype=float) + np.asarray(p1, dtype=float)) / 2.0
    # Symmetric offsets about 0: e.g. n=3 -> [-pitch, 0, +pitch].
    offsets = (np.arange(n) - (n - 1) / 2.0) * pitch
    direction = np.array([np.cos(theta), np.sin(theta)])

    placements = []
    for off in offsets:
        c = midpoint + off * direction
        placements.append((float(c[0]), float(c[1]), float(orientation)))
    return placements


def route_airbridges(
    design,
    route,
    pitch="100um",
    min_spacing="5um",
    crossover_length=None,
    name=None,
    ab_options=None,
):
    """Auto-place :class:`Airbridge` components along a route's CPW centerline.

    The bridges are added as **real design components** (not GDS-only
    artifacts), so they render in ``qm.view`` and export through every
    renderer. Each bridge is oriented perpendicular to the local CPW direction
    and, by default, sized to span the route's ``trace_width + 2*trace_gap``.

    Placement covers every straight segment of ``route.get_points()``, evenly
    spaced by ``pitch`` and kept ``max(fillet, min_spacing)`` clear of each
    corner/pin, plus one bridge at each interior corner oriented along the
    turn's bisector.

    Args:
        design (QDesign): the design to add the airbridges to.
        route (QRoute): a routed CPW (``RouteStraight``/``RouteMeander``/...).
        pitch (str): target center-to-center spacing along straights.
        min_spacing (str): minimum clearance from corners/pins.
        crossover_length (str, optional): bridge span. Defaults to the route's
            ``trace_width + 2*trace_gap`` so the span crosses trace and gaps.
        name (str, optional): prefix for the created components. Defaults to
            ``f"{route.name}_ab"``.
        ab_options (dict, optional): extra options forwarded to each
            :class:`Airbridge`.

    Returns:
        list[Airbridge]: the components created (also added to ``design``).
    """
    pitch = design.parse_value(pitch)
    min_spacing = design.parse_value(min_spacing)
    ab_options = dict(ab_options or {})
    name = name or f"{route.name}_ab"

    fillet = 0.0
    if "fillet" in route.options:
        fillet = design.parse_value(route.options.fillet)
    margin = max(fillet, min_spacing)

    if crossover_length is None:
        trace_width = design.parse_value(route.options.get("trace_width", "10um"))
        trace_gap = design.parse_value(route.options.get("trace_gap", "6um"))
        crossover_length = trace_width + 2.0 * trace_gap

    pts = np.asarray(route.get_points(), dtype=float)

    placements = []
    # Straight segments.
    for i in range(len(pts) - 1):
        placements.extend(_segment_placements(pts[i], pts[i + 1], pitch, margin))

    # Interior corners: one bridge on the turn bisector.
    for j in range(1, len(pts) - 1):
        v_in = pts[j] - pts[j - 1]
        v_out = pts[j + 1] - pts[j]
        theta_in = np.arctan2(v_in[1], v_in[0])
        theta_out = np.arctan2(v_out[1], v_out[0])
        # Skip a straight-through vertex (no real turn).
        if abs(
            np.arctan2(np.sin(theta_out - theta_in), np.cos(theta_out - theta_in))
        ) < np.radians(1.0):
            continue
        avg = np.arctan2(
            np.sin(theta_in) + np.sin(theta_out), np.cos(theta_in) + np.cos(theta_out)
        )
        placements.append(
            (float(pts[j][0]), float(pts[j][1]), float(np.degrees(avg) + 90.0))
        )

    made = []
    for k, (x, y, ori) in enumerate(placements):
        opts = dict(
            pos_x=f"{x}mm",
            pos_y=f"{y}mm",
            orientation=ori,
            crossover_length=f"{crossover_length}mm",
            **ab_options,
        )
        made.append(Airbridge(design, f"{name}_{k}", options=opts))
    return made
