# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Built-in design rules.

Default thresholds follow published superconducting-chip design-rule sets
where one exists; each rule's docstring says where its number comes from and
how much to trust it. Foundries differ -- treat the defaults as a starting
point and override per process:

    from qiskit_metal.validation import validate, MetalSpacingRule
    validate(design, rules=[MetalSpacingRule(min_spacing="4um")])

References
----------
.. [GDSII2Wafer] "From GDSII to Wafer: EDA Design Flow and Data Conversion
   for Wafer-Scale Superconducting Quantum Chip Fabrication",
   arXiv:2604.11379. Tabulates a quantum-specific design-rule set; the
   minimum CPW gap (R1), minimum same-layer metal spacing (R8) and
   ground-plane continuity (R9) defaults below are taken from it.
.. [DesignConcerns] "A Review of Design Concerns in Superconducting Quantum
   Circuits", arXiv:2411.16967. Background on crosstalk mechanisms and the
   sub-lambda/4 airbridge spacing convention.
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Iterable

import numpy as np
from shapely.ops import nearest_points
from shapely.strtree import STRtree

from .core import (
    DesignRule,
    Finding,
    Severity,
    chip_bounds,
    component_geometry,
    component_geometry_by_layer,
    component_names_by_id,
    connected_component_pairs,
    representative_point,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from qiskit_metal.designs import QDesign


def _parse(design: "QDesign", value) -> float:
    """Parse a Metal length string ('2um') to design units, passing floats."""
    return (
        float(value) if isinstance(value, (int, float)) else design.parse_value(value)
    )


class MetalOverlapRule(DesignRule):
    """Metal from two different components must not overlap.

    Overlapping drawn metal on the same layer is a short. This is the check
    that catches a route crossing another route, or a route running through
    a qubit pad.

    Distinguishing a genuine overlap from two features that merely touch at
    a shared pin needs a tolerance: an abutment has ~zero area, a real
    crossing of two CPW centre conductors has hundreds of um^2.
    ``min_area`` sets that cut, in design units squared.
    """

    name = "metal-overlap"
    description = "Drawn metal of two components overlaps (short circuit)."

    def __init__(self, min_area: float = 1e-6, severity: Severity = Severity.ERROR):
        # 1e-6 mm^2 == 1 um^2. Abutting pins land far below it; the smallest
        # real crossing (two 10um traces at a right angle) is 100 um^2.
        self.min_area = min_area
        self.severity = severity

    def check(self, design: "QDesign") -> Iterable[Finding]:
        connected = connected_component_pairs(design)
        for layer, geoms in sorted(component_geometry_by_layer(design).items()):
            names = list(geoms)
            if len(names) < 2:
                continue
            shapes = [geoms[n] for n in names]
            tree = STRtree(shapes)
            seen: set[tuple[int, int]] = set()
            for i, shape in enumerate(shapes):
                for j in tree.query(shape):
                    j = int(j)
                    if i == j:
                        continue
                    pair = (min(i, j), max(i, j))
                    if pair in seen:
                        continue
                    seen.add(pair)
                    a, b = sorted((names[pair[0]], names[pair[1]]))
                    if frozenset((a, b)) in connected:
                        continue  # wired together on purpose
                    inter = geoms[a].intersection(geoms[b])
                    if inter.is_empty or inter.area <= self.min_area:
                        continue
                    yield Finding(
                        rule=self.name,
                        severity=self.severity,
                        message=(
                            f"{a} and {b} overlap by "
                            f"{inter.area * 1e6:.0f} um^2 of metal on layer {layer}"
                        ),
                        components=(a, b),
                        location=representative_point(inter),
                        value=inter.area,
                        limit=self.min_area,
                    )


class MetalSpacingRule(DesignRule):
    """Metal from two different components must stay a minimum distance apart.

    Distinct from :class:`MetalOverlapRule`: this catches the near-miss --
    features that do not touch but sit closer than the process can reliably
    resolve, where incomplete etching or metal residue bridges them.

    Default 2 um follows the minimum same-layer metal spacing (R8) in
    [GDSII2Wafer]_. Raise it to your foundry's number.

    Components that legitimately abut (a route landing on the pin of the
    component it connects to) are at distance 0 and would swamp the report,
    so touching pairs are skipped -- :class:`MetalOverlapRule` is what
    distinguishes an intended junction from a short.
    """

    name = "metal-spacing"
    description = "Metal of two components is closer than the minimum spacing."

    def __init__(self, min_spacing="2um", severity: Severity = Severity.ERROR):
        self.min_spacing = min_spacing
        self.severity = severity

    def check(self, design: "QDesign") -> Iterable[Finding]:
        limit = _parse(design, self.min_spacing)
        connected = connected_component_pairs(design)
        for _layer, geoms in sorted(component_geometry_by_layer(design).items()):
            yield from self._check_layer(geoms, limit, connected)

    def _check_layer(self, geoms, limit, connected) -> Iterable[Finding]:
        for a, b in itertools.combinations(sorted(geoms), 2):
            if frozenset((a, b)) in connected:
                continue  # wired together on purpose
            ga, gb = geoms[a], geoms[b]
            if ga.intersects(gb):
                continue  # touching/overlapping: MetalOverlapRule's business
            gap = ga.distance(gb)
            if gap < limit:
                # Midpoint of the shortest line between the two features --
                # the actual pinch point, and always well-defined (unlike
                # intersecting one against a buffer of the other, which can
                # come back empty on floating-point ties).
                pa, pb = nearest_points(ga, gb)
                yield Finding(
                    rule=self.name,
                    severity=self.severity,
                    message=(
                        f"{a} and {b} are {gap * 1000:.2f} um apart "
                        f"(minimum {limit * 1000:.2f} um)"
                    ),
                    components=(a, b),
                    location=((pa.x + pb.x) / 2.0, (pa.y + pb.y) / 2.0),
                    value=gap,
                    limit=limit,
                )


class CPWGapRule(DesignRule):
    """A CPW's gap to the ground plane must not be too narrow.

    The gap sets how much of the mode's electric field sits at the
    substrate-metal interface. Narrowing it raises the field there and with
    it the two-level-system loss, so a floor on the gap is a floor on
    achievable coherence, not a lithography limit.

    Default 3 um follows the minimum CPW gap (R1) in [GDSII2Wafer]_.

    The gap is recovered from the qgeometry tables as
    ``(etched width - conductor width) / 2``, matching how Metal's route
    components emit a ``subtract=True`` path of ``trace_width + 2*trace_gap``
    alongside the ``subtract=False`` conductor.
    """

    name = "cpw-gap"
    description = "CPW gap to ground is narrower than the minimum."

    def __init__(self, min_gap="3um", severity: Severity = Severity.WARNING):
        self.min_gap = min_gap
        self.severity = severity

    def check(self, design: "QDesign") -> Iterable[Finding]:
        limit = _parse(design, self.min_gap)
        names = component_names_by_id(design)
        tables = design.qgeometry.tables
        if "path" not in tables:
            return
        paths = tables["path"]

        # Pair each drawn conductor with the etched path of the same
        # component; their width difference is the two gaps.
        for comp_id, group in paths.groupby("component"):
            drawn = group[~group["subtract"].astype(bool)]
            etched = group[group["subtract"].astype(bool)]
            if drawn.empty or etched.empty:
                continue
            conductor_w = float(drawn["width"].max())
            etched_w = float(etched["width"].max())
            gap = (etched_w - conductor_w) / 2.0
            if gap <= 0 or gap >= limit:
                continue
            geom = drawn.iloc[0]["geometry"]
            yield Finding(
                rule=self.name,
                severity=self.severity,
                message=(
                    f"{names[comp_id]} has a {gap * 1000:.2f} um CPW gap "
                    f"(minimum {limit * 1000:.2f} um)"
                ),
                components=(names[comp_id],),
                location=representative_point(geom),
                value=gap,
                limit=limit,
            )


class ChipBoundsRule(DesignRule):
    """All geometry must lie inside the chip outline.

    Anything past the edge is silently clipped downstream -- the renderers
    cut it against the chip extent, so a launchpad hanging off the edge
    turns into a hole in the ground plane rather than an obvious error.
    """

    name = "chip-bounds"
    description = "Component geometry extends beyond the chip outline."

    def __init__(self, chip: str = "main", severity: Severity = Severity.ERROR):
        self.chip = chip
        self.severity = severity

    def check(self, design: "QDesign") -> Iterable[Finding]:
        minx, miny, maxx, maxy = chip_bounds(design, self.chip)
        geoms = component_geometry(design, subtract=None)
        for name in sorted(geoms):
            gminx, gminy, gmaxx, gmaxy = geoms[name].bounds
            over = max(gmaxx - maxx, gmaxy - maxy, minx - gminx, miny - gminy)
            if over > 0:
                yield Finding(
                    rule=self.name,
                    severity=self.severity,
                    message=(
                        f"{name} extends {over * 1000:.1f} um beyond the "
                        f"'{self.chip}' chip outline"
                    ),
                    components=(name,),
                    location=representative_point(geoms[name]),
                    value=over,
                    limit=0.0,
                )


class ShortSegmentRule(DesignRule):
    """Route segments must be long enough for the fillet they ask for.

    A corner is rounded by inscribing an arc of radius ``fillet``; that
    needs roughly the radius worth of straight run on each side. Segments
    shorter than that render as sharp, unfileted kinks, and the Gmsh path
    renderer fails outright on them. This is the design-wide form of the
    condition behind issue #1086.

    ``margin`` scales the requirement: 1.0 asks only that a segment be as
    long as the fillet radius, which is the bare geometric minimum and in
    practice still marginal, so the default asks for a little more.
    """

    name = "short-segment"
    description = "Route segment is too short for its fillet radius."

    def __init__(self, margin: float = 1.0, severity: Severity = Severity.WARNING):
        self.margin = margin
        self.severity = severity

    def check(self, design: "QDesign") -> Iterable[Finding]:
        names = component_names_by_id(design)
        tables = design.qgeometry.tables
        if "path" not in tables:
            return
        for _, row in tables["path"].iterrows():
            fillet = row.get("fillet", None)
            if fillet is None or not np.isfinite(fillet) or fillet <= 0:
                continue
            limit = float(fillet) * self.margin
            coords = np.asarray(row["geometry"].coords, dtype=float)
            if len(coords) < 3:
                continue  # no interior corner to round
            seg = np.linalg.norm(np.diff(coords, axis=0), axis=1)
            # Only interior segments sit between two corners; the first and
            # last run into an end pin and need no room on the outer side.
            for idx in range(len(seg)):
                is_interior = 0 < idx < len(seg) - 1
                needed = limit * (2.0 if is_interior else 1.0)
                if seg[idx] >= needed:
                    continue
                midpoint = (coords[idx] + coords[idx + 1]) / 2.0
                yield Finding(
                    rule=self.name,
                    severity=self.severity,
                    message=(
                        f"{names[row['component']]}.{row['name']} segment "
                        f"{idx} is {seg[idx] * 1000:.1f} um long but needs "
                        f"{needed * 1000:.1f} um for a "
                        f"{float(fillet) * 1000:.1f} um fillet"
                    ),
                    components=(names[row["component"]],),
                    location=(float(midpoint[0]), float(midpoint[1])),
                    value=float(seg[idx]),
                    limit=needed,
                )


class QubitClearanceRule(DesignRule):
    """Routes should keep clear of qubit pockets they do not connect to.

    A CPW running along a qubit's pocket edge couples to it in ways the
    lumped-element model does not capture. Unlike the other defaults in
    this module this threshold is a **project heuristic, not a published
    figure** -- the literature treats stray coupling as something to
    simulate rather than to bound with a single number. It is expressed in
    multiples of the full CPW width (conductor + both gaps) so it stays
    meaningful if the trace geometry changes, and it is a WARNING because
    a deliberately-coupled structure will trip it.

    Components named in ``connected`` for a given pocket are skipped; by
    default a route is exempt from the pocket of any component it shares a
    net with, since those are connected on purpose.
    """

    name = "qubit-clearance"
    description = "Route passes close to a qubit pocket it does not connect to."

    def __init__(
        self,
        min_clearance_cpw_widths: float = 3.0,
        pocket_geometry_name: str = "rect_pk",
        severity: Severity = Severity.WARNING,
    ):
        self.min_clearance_cpw_widths = min_clearance_cpw_widths
        self.pocket_geometry_name = pocket_geometry_name
        self.severity = severity

    def check(self, design: "QDesign") -> Iterable[Finding]:
        names = component_names_by_id(design)
        tables = design.qgeometry.tables
        if "poly" not in tables or "path" not in tables:
            return

        pockets = {
            names[row["component"]]: row["geometry"]
            for _, row in tables["poly"].iterrows()
            if row["name"] == self.pocket_geometry_name
        }
        if not pockets:
            return

        connected = connected_component_pairs(design)
        etched = tables["path"][tables["path"]["subtract"].astype(bool)]
        if etched.empty:
            return
        # The etched width is the route's full footprint: conductor + gaps.
        full_width = float(etched["width"].max())
        limit = self.min_clearance_cpw_widths * full_width

        for _, row in etched.iterrows():
            route = names[row["component"]]
            if route in pockets:
                continue
            edge = row["geometry"].buffer(row["width"] / 2.0, cap_style=2)
            for qubit in sorted(pockets):
                if route == qubit or frozenset((route, qubit)) in connected:
                    continue
                gap = pockets[qubit].distance(edge)
                if gap >= limit:
                    continue
                yield Finding(
                    rule=self.name,
                    severity=self.severity,
                    message=(
                        f"{route} passes {gap * 1000:.1f} um from {qubit}'s "
                        f"pocket ({gap / full_width:.2f}x CPW width; want "
                        f"{self.min_clearance_cpw_widths:.1f}x = "
                        f"{limit * 1000:.0f} um)"
                    ),
                    components=(route, qubit),
                    location=representative_point(edge),
                    value=gap,
                    limit=limit,
                )


#: Rules run by :func:`~qiskit_metal.validation.validate` when none are given.
DEFAULT_RULES: tuple[DesignRule, ...] = (
    MetalOverlapRule(),
    MetalSpacingRule(),
    CPWGapRule(),
    ChipBoundsRule(),
    ShortSegmentRule(),
    QubitClearanceRule(),
)
