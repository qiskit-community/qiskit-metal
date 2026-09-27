# This code is part of Quantum Metal.
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
"""A CPW drawn along an explicit list of points."""

from qiskit_metal import Dict, draw
from qiskit_metal.qlibrary.core import QComponent


class PolylineCPW(QComponent):
    """A coplanar waveguide drawn along an explicit polyline.

    Inherits `QComponent` class.

    .. image::
        PolylineCPW.png

    .. meta::
        :description: CPW along an explicit list of points

    Every other waypoint-taking component in this package is a
    :class:`~qiskit_metal.qlibrary.core.QRoute` subclass, and so routes *for*
    you: it decides the path between the points you give it, via
    ``QRoute.connect_simple()``, which tries four fixed Manhattan shapes
    (``^|_``, ``^^|``, ``__|``, ``_|^``) between consecutive points and raises
    :class:`~qiskit_metal.toolbox_metal.exceptions.QiskitMetalDesignError` when
    none of them fits.

    That is the right behaviour when you know the endpoints and want a path
    found. It is the wrong behaviour when you already *have* the path -- a
    geometry traced off a micrograph, a centreline exported from another tool,
    or any non-Manhattan (45 degree, curved, octilinear) run that the four
    shapes cannot express. This component does no routing and no collision
    avoidance. It draws the points you give it, in order.

    Points are in design units and absolute (not relative to ``pos_x``/
    ``pos_y``), matching how anchors are specified for
    :class:`~qiskit_metal.qlibrary.tlines.anchored_path.RouteAnchors`.

    Pins ``start`` and ``end`` sit at the two ends, so this can be wired to
    other components with :meth:`~qiskit_metal.designs.QDesign.connect_pins`.

    **Taps** add named pins partway along the line, for anything that branches
    off it -- a coupler stub, a capacitor, a tee. Give ``taps`` a mapping of
    ``{pin_name: [x, y]}``: each pin lands at the point on the line nearest
    ``[x, y]``, with its normal perpendicular to the line and pointing toward
    ``[x, y]`` (so ``[x, y]`` just has to be somewhere on the side the branch
    leaves from, e.g. where the branch goes). Connecting the branch to a tap
    with ``connect_pins`` registers the joint as one net, which is what lets
    the design-rule check treat the overlapping metal as intended rather than
    a short. Without taps a mid-line joint has no pin to connect, and every
    such joint needs a DRC waiver instead.

    A tap is an ordinary pin. Leave it unconnected and nothing is drawn for it,
    but do not list it in a renderer's ``open_pins`` -- that would cut an open
    end into the middle of the line.

    Default Options:
        * points: '[]' -- Ordered list of (x, y) vertices; at least two
        * trace_width: 'cpw_width' -- Width of the centre conductor
        * trace_gap: 'cpw_gap' -- Width of the gap either side
        * fillet: '0' -- Corner radius; '0' keeps corners sharp
        * min_segment: '0' -- Drop vertices closer than this to their
          predecessor. A fillet larger than half a segment cannot be drawn, so
          set this to about ``2 * fillet`` when filleting a densely sampled
          path.
        * taps: '{}' -- ``{pin_name: [x, y]}`` pins partway along the line;
          see above.
    """

    default_options = Dict(
        points=[],
        trace_width="cpw_width",
        trace_gap="cpw_gap",
        fillet="0",
        min_segment="0",
        taps=Dict(),
    )
    """Default options"""

    component_metadata = Dict(short_name="poly", _qgeometry_table_path="True")
    """Component metadata"""

    TOOLTIP = """CPW drawn along an explicit polyline."""

    def make(self):
        """Build the component."""
        p = self.p

        pts = [(float(x), float(y)) for x, y in p.points]
        if len(pts) < 2:
            raise ValueError(
                f"{self.name}: PolylineCPW needs at least two points, got {len(pts)}"
            )

        if p.min_segment > 0:
            kept = [pts[0]]
            for q in pts[1:-1]:
                if draw.LineString([kept[-1], q]).length >= p.min_segment:
                    kept.append(q)
            # The final vertex is never dropped -- it is an endpoint, and a
            # route that stops short of where it was asked to end is worse than
            # one short segment. But keeping it can leave that short segment at
            # the end, and because the fillet below is clamped to half the
            # SHORTEST segment, one short stub quietly shrinks the fillet for
            # the whole line. So drop the preceding interior vertex instead,
            # until the last segment is long enough (or only the start remains).
            while (
                len(kept) > 1
                and draw.LineString([kept[-1], pts[-1]]).length < p.min_segment
            ):
                kept.pop()
            kept.append(pts[-1])
            pts = kept

        line = draw.LineString(pts)

        # Filleting a corner needs room on both of its segments; asking for more
        # than half the shortest segment produces self-intersecting geometry and
        # trips the renderer's short-segment check.
        shortest = min(
            draw.LineString([a, b]).length for a, b in zip(pts[:-1], pts[1:])
        )
        fillet = min(p.fillet, shortest / 2.0)

        self.add_qgeometry(
            "path",
            {"trace": line},
            width=p.trace_width,
            fillet=fillet,
            layer=p.layer,
            chip=p.chip,
        )
        self.add_qgeometry(
            "path",
            {"cut": line},
            width=p.trace_width + 2 * p.trace_gap,
            fillet=fillet,
            subtract=True,
            layer=p.layer,
            chip=p.chip,
        )

        # A pin sits at the midpoint of the two-point line it is given, so the
        # line has to be a short stub at the very end of the path -- handing it
        # the whole first segment would park the pin halfway down the route.
        # Coords run inward-to-outward so each normal points away from the trace.
        self.add_pin("start", _face(pts[1], pts[0], p.trace_width), width=p.trace_width)
        self.add_pin("end", _face(pts[-2], pts[-1], p.trace_width), width=p.trace_width)

        for name, target in (p.taps or {}).items():
            if name in ("start", "end"):
                raise ValueError(f"{self.name}: tap name {name!r} is reserved")
            tx, ty = float(target[0]), float(target[1])
            d = line.project(draw.Point(tx, ty))
            foot = line.interpolate(d)
            # Local direction from a short chord around the foot; at a vertex
            # this is the chord across the corner, i.e. the bisector direction.
            eps = min(1e-4, line.length / 4)
            a = line.interpolate(max(d - eps, 0.0))
            b = line.interpolate(min(d + eps, line.length))
            tdx, tdy = b.x - a.x, b.y - a.y
            n = (tdx * tdx + tdy * tdy) ** 0.5 or 1.0
            nx, ny = -tdy / n, tdx / n
            ox, oy = tx - foot.x, ty - foot.y
            if (ox * ox + oy * oy) ** 0.5 < 1e-9:
                raise ValueError(
                    f"{self.name}: tap {name!r} target lies on the line; give a "
                    "point on the side the branch leaves toward"
                )
            if ox * nx + oy * ny < 0:
                nx, ny = -nx, -ny
            self.add_pin(
                name,
                _face((foot.x - nx, foot.y - ny), (foot.x, foot.y), p.trace_width),
                width=p.trace_width,
            )


def _face(inner, tip, width):
    """Pin cross-section at `tip`, oriented so its normal points away from `inner`.

    ``add_pin`` takes the line *across* the conductor, not one along it, and
    derives the outward normal from that line's direction -- the same
    convention ``LaunchpadWirebond`` uses for its ``tie`` pin.
    """
    dx, dy = tip[0] - inner[0], tip[1] - inner[1]
    n = (dx * dx + dy * dy) ** 0.5 or 1.0
    px, py = -dy / n * width / 2.0, dx / n * width / 2.0
    return draw.LineString(
        [(tip[0] + px, tip[1] + py), (tip[0] - px, tip[1] - py)]
    ).coords
