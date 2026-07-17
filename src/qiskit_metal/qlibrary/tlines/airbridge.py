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


def _fillet_corner(vertex_start, vertex_corner, vertex_end, radius, points):
    """Arc points for a single rounded corner, or ``None`` if the fillet does
    not fit (leave the corner sharp).

    Pure port of the arc math the matplotlib renderer uses
    (``QMplRenderer._calc_fillet``), so airbridge placement sees the *same*
    filleted trace that gets rendered/exported.
    """
    vertex_start = np.asarray(vertex_start, dtype=float)
    vertex_corner = np.asarray(vertex_corner, dtype=float)
    vertex_end = np.asarray(vertex_end, dtype=float)

    sc_vec = vertex_start - vertex_corner
    ec_vec = vertex_end - vertex_corner
    sc_norm = np.linalg.norm(sc_vec)
    ec_norm = np.linalg.norm(ec_vec)
    if sc_norm == 0 or ec_norm == 0:
        return None
    sc_uvec = sc_vec / sc_norm
    ec_uvec = ec_vec / ec_norm

    end_angle = np.arccos(np.clip(np.dot(sc_uvec, ec_uvec), -1.0, 1.0))
    if end_angle == 0 or end_angle == np.pi:  # collinear -> no corner
        return None
    # Fillet circle must fit inside the corner.
    if radius / np.tan(end_angle / 2) > min(sc_norm, ec_norm):
        return None

    net_uvec = (sc_uvec + ec_uvec) / np.linalg.norm(sc_uvec + ec_uvec)
    circle_center = vertex_corner + net_uvec * radius / np.sin(end_angle / 2)

    delta_x = vertex_corner[0] - circle_center[0]
    delta_y = vertex_corner[1] - circle_center[1]
    if delta_x:
        theta_mid = np.arctan(delta_y / delta_x) + np.pi * int(delta_x < 0)
    else:
        theta_mid = np.pi * ((1 - 2 * int(delta_y < 0)) + int(delta_y < 0))

    theta_start = theta_mid - (np.pi - end_angle) / 2
    theta_end = theta_mid + (np.pi - end_angle) / 2
    p1 = circle_center + radius * np.array([np.cos(theta_start), np.sin(theta_start)])
    p2 = circle_center + radius * np.array([np.cos(theta_end), np.sin(theta_end)])
    if np.linalg.norm(vertex_start - p2) < np.linalg.norm(vertex_start - p1):
        theta_start, theta_end = theta_end, theta_start

    return np.array(
        [
            circle_center + radius * np.array([np.cos(t), np.sin(t)])
            for t in np.linspace(theta_start, theta_end, points)
        ]
    )


def _fillet_centerline(pts, radius, resolution=16):
    """Return the rounded (filleted) centerline of a route as an ``Nx2`` array.

    Rounds every interior corner that the fillet radius fits; corners that are
    too tight stay sharp. Mirrors ``QMplRenderer.fillet_path`` so placement
    matches the rendered trace.
    """
    pts = np.asarray(pts, dtype=float)
    if len(pts) <= 2 or radius <= 0:
        return pts

    out = [pts[0]]
    for start, corner, end in zip(pts, pts[1:], pts[2:]):
        arc = _fillet_corner(start, corner, end, radius, resolution)
        if arc is None:
            out.append(corner)
        else:
            out.extend(arc)
    out.append(pts[-1])
    return np.asarray(out, dtype=float)


def _placements_along(coords, pitch, margin):
    """Evenly-spaced ``(x, y, orientation_deg)`` samples along a polyline.

    Places bridges by arc length so corners (rounded into the polyline) and
    straights are handled uniformly. Bridges are centered on the path and kept
    ``margin`` clear of both ends, and each is oriented perpendicular to the
    local tangent so its span crosses the trace.
    """
    coords = np.asarray(coords, dtype=float)
    seg = np.diff(coords, axis=0)
    seg_len = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(seg_len)])
    total = float(cum[-1])

    usable = total - 2.0 * margin
    if total <= 0 or usable < 0:
        return []

    n = int(np.floor(usable / pitch)) + 1
    centers = total / 2.0 + (np.arange(n) - (n - 1) / 2.0) * pitch

    placements = []
    for s in centers:
        k = int(np.searchsorted(cum, s) - 1)
        k = min(max(k, 0), len(seg_len) - 1)
        seg_frac = (s - cum[k]) / seg_len[k] if seg_len[k] else 0.0
        point = coords[k] + seg_frac * seg[k]
        theta = np.arctan2(seg[k][1], seg[k][0])
        placements.append(
            (float(point[0]), float(point[1]), float(np.degrees(theta) + 90.0))
        )
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
    """Auto-place :class:`Airbridge` components along a route's CPW.

    The bridges are added as **real design components** (not GDS-only
    artifacts), so they render in ``qm.view`` and export through every
    renderer. Each bridge is oriented perpendicular to the local CPW direction
    and, by default, sized to span the route's ``trace_width + 2*trace_gap``.

    Placement follows the route's *filleted* centerline (the geometry that is
    actually rendered — rounded corners, not the sharp vertices), spacing
    bridges by arc length at ``pitch`` and keeping them ``min_spacing`` clear
    of the end pins. Corners are covered because the fillet arcs are part of
    that centerline; there is no special-cased corner placement.

    Args:
        design (QDesign): the design to add the airbridges to.
        route (QRoute): a routed CPW (``RouteStraight``/``RouteMeander``/...).
        pitch (str): target center-to-center spacing along the trace.
        min_spacing (str): minimum clearance from the end pins.
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

    if crossover_length is None:
        trace_width = design.parse_value(route.options.get("trace_width", "10um"))
        trace_gap = design.parse_value(route.options.get("trace_gap", "6um"))
        crossover_length = trace_width + 2.0 * trace_gap

    centerline = _fillet_centerline(route.get_points(), fillet)
    placements = _placements_along(centerline, pitch, min_spacing)

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
