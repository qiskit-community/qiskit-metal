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

import logging

import numpy as np

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent
from qiskit_metal.toolbox_metal.parsing import is_true

logger = logging.getLogger(__name__)


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
        * enable_posts: 'False' -- Emit two support-post feet on ``post_layer``
          where the span meets each pad. In a planar view these coincide with
          the pad/span overlap; their purpose is the 3D mesh, where the posts
          (on a layer stacked between pad and span heights) join the elevated
          span to the base metal into one connected conductor.
        * post_layer: '32' -- Layer of the support posts (used only when
          ``enable_posts``).
    """

    default_options = Dict(
        crossover_length="22um",
        bridge_width="7.5um",
        pad_width="11um",
        pad_length="11um",
        bridge_layer="30",
        pad_layer="31",
        enable_posts="False",
        post_layer="32",
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

        # Optional support posts: the span-over-pad overlap, emitted on their
        # own layer so a 3D layer stack can bridge the z-gap between the base
        # pads and the elevated span (see route_airbridges / the 3D helpers).
        posts = None
        if is_true(p.enable_posts):
            left_post = draw.rectangle(pad_length, bridge_width, -pad_offset, 0)
            right_post = draw.rectangle(pad_length, bridge_width, +pad_offset, 0)
            posts = draw.union(left_post, right_post)

        # Reposition the whole crossover.
        geom = [span, pads] + ([posts] if posts is not None else [])
        geom = draw.rotate(geom, p.orientation, origin=(0, 0))
        geom = draw.translate(geom, p.pos_x, p.pos_y)
        if posts is not None:
            span, pads, posts = geom
        else:
            span, pads = geom

        self.add_qgeometry(
            "poly", {"bridge": span}, layer=p.bridge_layer, subtract=False
        )
        self.add_qgeometry("poly", {"pads": pads}, layer=p.pad_layer, subtract=False)
        if posts is not None:
            self.add_qgeometry(
                "poly", {"posts": posts}, layer=p.post_layer, subtract=False
            )


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


def _fillet_centerline(pts, radius, resolution=16, return_corners=False):
    """Return the rounded (filleted) centerline of a route as an ``Nx2`` array.

    Rounds every interior corner that the fillet radius fits; corners that are
    too tight stay sharp. Mirrors ``QMplRenderer.fillet_path`` so placement
    matches the rendered trace.

    If ``return_corners`` is true, also return a list of the arc-length
    positions (measured along the returned centerline) of the midpoint of each
    rounded bend — used to guarantee an airbridge sits on every corner.
    """
    pts = np.asarray(pts, dtype=float)
    if len(pts) <= 2 or radius <= 0:
        return (pts, []) if return_corners else pts

    out = [pts[0]]
    corner_idx = []  # index into `out` of each rounded bend's arc midpoint
    for start, corner, end in zip(pts, pts[1:], pts[2:]):
        arc = _fillet_corner(start, corner, end, radius, resolution)
        if arc is None:
            out.append(corner)
        else:
            corner_idx.append(len(out) + len(arc) // 2)
            out.extend(arc)
    out.append(pts[-1])
    out = np.asarray(out, dtype=float)

    if not return_corners:
        return out
    _, _, _, cum = _arclength_frame(out)
    corners = [float(cum[i]) for i in corner_idx]
    return out, corners


def _arclength_frame(coords):
    """Cumulative arc-length bookkeeping ``(coords, seg, seg_len, cum)`` for a
    polyline, shared by every arc-length sampler below."""
    coords = np.asarray(coords, dtype=float)
    seg = np.diff(coords, axis=0)
    seg_len = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(seg_len)])
    return coords, seg, seg_len, cum


def _sample_at(frame, s):
    """``(x, y, orientation_deg)`` at arc-length ``s`` along a polyline.

    Orientation is perpendicular to the local tangent so a bridge span placed
    here crosses the trace.
    """
    coords, seg, seg_len, cum = frame
    k = int(np.searchsorted(cum, s) - 1)
    k = min(max(k, 0), len(seg_len) - 1)
    seg_frac = (s - cum[k]) / seg_len[k] if seg_len[k] else 0.0
    point = coords[k] + seg_frac * seg[k]
    theta = np.arctan2(seg[k][1], seg[k][0])
    return (float(point[0]), float(point[1]), float(np.degrees(theta) + 90.0))


def _uniform_arclengths(total, pitch, margin):
    """Evenly-spaced, path-centered arc-length positions kept ``margin`` clear
    of both ends. Empty if the usable span is shorter than needed."""
    usable = total - 2.0 * margin
    if total <= 0 or usable < 0:
        return []
    n = int(np.floor(usable / pitch)) + 1
    return list(total / 2.0 + (np.arange(n) - (n - 1) / 2.0) * pitch)


def _placements_along(coords, pitch, margin):
    """Evenly-spaced ``(x, y, orientation_deg)`` samples along a polyline.

    Places bridges by arc length so corners (rounded into the polyline) and
    straights are handled uniformly. Bridges are centered on the path and kept
    ``margin`` clear of both ends, and each is oriented perpendicular to the
    local tangent so its span crosses the trace.
    """
    frame = _arclength_frame(coords)
    total = float(frame[3][-1])
    return [_sample_at(frame, s) for s in _uniform_arclengths(total, pitch, margin)]


def route_airbridges(
    design,
    route,
    pitch="100um",
    min_spacing="5um",
    crossover_length=None,
    bridge_at_corners=False,
    enable_posts=False,
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
        bridge_at_corners (bool): if true, guarantee one bridge centered on
            every rounded bend (in addition to the uniform-pitch bridges). A
            uniform bridge that would land within half a pitch of a corner
            bridge is dropped so the two do not bunch up. Corners within
            ``min_spacing`` of an end are skipped. Defaults to false (uniform
            pitch only — bends are still covered wherever a pitch sample lands
            on the fillet arc).
        enable_posts (bool): emit support posts on each airbridge (the
            ``Airbridge`` ``enable_posts`` option) so a 3D layer stack can join
            the elevated span to the base metal. Defaults to false. Pair with
            :func:`apply_airbridge_layer_stack` ``include_posts=True``.
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
    if enable_posts:
        ab_options.setdefault("enable_posts", "True")
    name = name or f"{route.name}_ab"

    fillet = 0.0
    if "fillet" in route.options:
        fillet = design.parse_value(route.options.fillet)

    if crossover_length is None:
        trace_width = design.parse_value(route.options.get("trace_width", "10um"))
        trace_gap = design.parse_value(route.options.get("trace_gap", "6um"))
        crossover_length = trace_width + 2.0 * trace_gap

    centerline, corners = _fillet_centerline(
        route.get_points(), fillet, return_corners=True
    )
    frame = _arclength_frame(centerline)
    total = float(frame[3][-1])
    s_values = _uniform_arclengths(total, pitch, min_spacing)

    if bridge_at_corners:
        # Corner bridges are mandatory; add them first, then keep only the
        # uniform samples that are at least half a pitch (in arc length) from
        # every corner bridge so bridges do not overlap at bends.
        kept = [s for s in corners if min_spacing <= s <= total - min_spacing]
        for s in s_values:
            if all(abs(s - cs) >= 0.5 * pitch for cs in kept):
                kept.append(s)
        s_values = sorted(kept)

    placements = [_sample_at(frame, s) for s in s_values]

    # Idempotent re-runs: clear airbridges this helper previously placed under
    # ``name`` before re-placing (so re-executing a cell / re-routing doesn't
    # raise on name collisions or leave stale bridges behind).
    stale = [
        n
        for n in list(design.components)
        if n.startswith(f"{name}_") and n[len(name) + 1 :].isdigit()
    ]
    for n in stale:
        design.delete_component(n)

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


# ---------------------------------------------------------------------------
# EXPERIMENTAL — 3D airbridges via layer-stack elevation
#
# See issue #1144. The 2D crossover above renders flat (z=0). Metal's 3D FEM
# renderers (``renderer_gmsh`` today; AWS Palace / Ansys as follow-ons) extrude
# every filled ``(layer, datatype)`` in the design's layer stack by its
# ``thickness`` at its ``z_coord`` (see ``toolbox_metal/layer_stack_handler.py``
# and ``renderer_gmsh/gmsh_renderer.py``). Elevating the ``bridge_layer`` in the
# layer stack is therefore all it takes to lift the flat span into a real 3D
# bridge — no renderer code, and the same rows feed whichever 3D backend runs.
# ---------------------------------------------------------------------------


def airbridge_layer_stack_rows(
    bridge_layer=30,
    pad_layer=31,
    bridge_z_coord="3um",
    bridge_thickness="0.3um",
    pad_thickness="0.2um",
    material="pec",
    chip_name="main",
    datatype=0,
    include_posts=False,
    post_layer=32,
):
    """[EXPERIMENTAL] Layer-stack rows giving an :class:`Airbridge` a 3D form.

    Returns the :class:`~qiskit_metal.toolbox_metal.layer_stack_handler.LayerStackHandler`
    rows that make the airbridge stand up for FEM meshing: the landing pads sit
    on the base plane (``z_coord="0um"``) and the span sits ``bridge_z_coord``
    above it, each extruded by its ``thickness``.

    With ``include_posts`` a third row is added for the support posts, extruded
    from the base plane up to the span (``thickness=bridge_z_coord``) so the
    elevated span is joined to the base metal into one connected conductor —
    required for the 3D mesh of a full CPW + airbridges to render (the span
    otherwise floats and the boolean fragmentation fails). Pair it with
    ``Airbridge(..., enable_posts=True)`` (or ``route_airbridges(...,
    enable_posts=True)``) so post *geometry* exists on ``post_layer``.

    .. warning::

        **Experimental.** The elevated + connected geometry renders and meshes
        through ``renderer_gmsh``, but has **not** been validated against a live
        FEM solve. Treat it as a starting point, not a simulation-ready result.
        Tracking: https://github.com/qiskit-community/qiskit-metal/issues/1144

    Args:
        bridge_layer (int): layer the elevated span lives on (matches the
            ``Airbridge`` ``bridge_layer`` option). Defaults to 30.
        pad_layer (int): layer the base landing pads live on. Defaults to 31.
        bridge_z_coord (str): elevation of the span above the base plane.
        bridge_thickness (str): thickness of the elevated span metal.
        pad_thickness (str): thickness of the base landing-pad metal.
        material (str): layer-stack material name. Defaults to ``"pec"``.
        chip_name (str): chip the layers belong to. Defaults to ``"main"``.
        datatype (int): datatype for both rows. Defaults to 0.
        include_posts (bool): also add a support-post row (see above).
        post_layer (int): layer the posts live on (matches ``Airbridge``
            ``post_layer``). Defaults to 32.

    Returns:
        list[dict]: rows keyed by ``LayerStackHandler.Col_Names`` — pads at the
        base plane, the elevated span, and (if ``include_posts``) the posts.
    """
    rows = [
        dict(
            chip_name=chip_name,
            layer=int(pad_layer),
            datatype=int(datatype),
            material=material,
            thickness=pad_thickness,
            z_coord="0um",
            fill="true",
        ),
        dict(
            chip_name=chip_name,
            layer=int(bridge_layer),
            datatype=int(datatype),
            material=material,
            thickness=bridge_thickness,
            z_coord=bridge_z_coord,
            fill="true",
        ),
    ]
    if include_posts:
        # Posts rise from the base plane to the span bottom, connecting them.
        rows.append(
            dict(
                chip_name=chip_name,
                layer=int(post_layer),
                datatype=int(datatype),
                material=material,
                thickness=bridge_z_coord,
                z_coord="0um",
                fill="true",
            )
        )
    return rows


def apply_airbridge_layer_stack(design, replace=True, **kwargs):
    """[EXPERIMENTAL] Register the 3D airbridge layer rows on a design's stack.

    Appends the rows from :func:`airbridge_layer_stack_rows` to a
    ``DesignMultiPlanar`` layer stack (``design.ls.ls_df``) so the gmsh (and
    future Palace / Ansys) mesh renders the span elevated. This is the
    renderer-agnostic seam: no renderer code changes, the same rows feed any 3D
    backend.

    .. note::

        The gmsh renderer also classifies layers as metal vs dielectric via its
        ``layer_types`` argument. Register the airbridge layers as metal, e.g.
        ``QGmshRenderer(design, layer_types=dict(metal=[1, 30, 31],
        dielectric=[3]))``, or ``assign_physical_groups`` raises. (Rendering a
        full CPW route in 3D separately hits a known gmsh path-fillet fragility
        with short lead segments — see #1144.)

    .. warning::

        Experimental — see :func:`airbridge_layer_stack_rows`. The elevated
        geometry renders in gmsh, but no live FEM solve has validated it.
        Tracking: https://github.com/qiskit-community/qiskit-metal/issues/1144

    Args:
        design (DesignMultiPlanar): a design exposing a layer stack at
            ``design.ls`` (i.e. ``DesignMultiPlanar``).
        replace (bool): if True (default), drop any existing rows for the
            ``bridge_layer`` / ``pad_layer`` before appending, so re-running is
            idempotent.
        **kwargs: forwarded to :func:`airbridge_layer_stack_rows`.

    Returns:
        pandas.DataFrame: the updated ``design.ls.ls_df``.

    Raises:
        AttributeError: if ``design`` has no layer stack (``design.ls``), e.g.
            a plain ``DesignPlanar``.
    """
    import pandas as pd

    logger.warning(
        "apply_airbridge_layer_stack is EXPERIMENTAL: the 3D airbridge mesh has "
        "not been validated against a live FEM solve (see issue #1144)."
    )

    ls = getattr(design, "ls", None)
    if ls is None or getattr(ls, "ls_df", None) is None:
        raise AttributeError(
            "3D airbridges need a design with a layer stack (DesignMultiPlanar); "
            f"{type(design).__name__} exposes none."
        )

    rows = airbridge_layer_stack_rows(**kwargs)
    df = ls.ls_df
    if replace:
        drop_layers = {r["layer"] for r in rows}
        df = df[~df["layer"].isin(drop_layers)]
    ls.ls_df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    return ls.ls_df
