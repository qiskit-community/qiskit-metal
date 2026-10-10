# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Core types for the design-rule-check (DRC) framework.

See :mod:`qiskit_metal.validation` for the user-facing entry point.
"""

from __future__ import annotations

import enum
import itertools
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable, Sequence

from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

if TYPE_CHECKING:  # pragma: no cover - typing only
    from qiskit_metal.designs import QDesign


class Severity(enum.Enum):
    """How much a rule violation matters.

    ``ERROR`` marks geometry that is wrong regardless of intent -- shorted
    nets, features off the chip. ``WARNING`` marks geometry that is legal
    but very likely unintended, or that trades against a physical budget
    (loss, crosstalk) rather than breaking outright.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Finding:
    """A single rule violation.

    Attributes:
        rule (str): identifier of the rule that produced this, e.g.
            ``"metal-overlap"``.
        severity (Severity): see :class:`Severity`.
        message (str): human-readable one-line description.
        components (tuple): names of the components involved, in a stable
            order so findings compare equal across runs.
        location (tuple): ``(x, y)`` in design units (mm) representative of
            the violation, or None if it isn't localised.
        value (float): the measured quantity, in design units.
        limit (float): the threshold ``value`` was compared against.
    """

    rule: str
    severity: Severity
    message: str
    components: tuple[str, ...] = ()
    location: tuple[float, float] | None = None
    value: float | None = None
    limit: float | None = None

    def __str__(self) -> str:
        where = ""
        if self.location is not None:
            where = f"  @ ({self.location[0]:.4f}, {self.location[1]:.4f})"
        return f"[{self.severity}] {self.rule}: {self.message}{where}"


@dataclass(frozen=True)
class Waiver:
    """A documented exemption for findings you have decided are correct.

    Real designs contain geometry that a same-layer geometric check must flag
    and a designer knows is intended. The honest way to handle those is not to
    widen a threshold until the report goes quiet -- that blinds the rule to
    genuine violations of the same kind -- but to waive the specific finding and
    say why.

    A waiver never hides anything: waived findings are moved to
    :attr:`ValidationResult.waived` and still listed in
    :meth:`ValidationResult.report`, with their reason. They simply stop
    counting as errors, so ``result.ok`` and
    :meth:`~ValidationResult.raise_if_errors` reflect the design's real state.

    ``reason`` is required and comes first, because a waiver without one is
    indistinguishable from a bug someone got tired of.

    Matching is an AND over whichever fields are set; an all-default waiver
    matches everything, so set at least one.

    Args:
        reason (str): why this finding is acceptable. Required.
        rule (str): only waive findings from this rule, e.g. ``"metal-overlap"``.
        components (Iterable[str]): only waive findings whose component set is
            exactly these names (order-insensitive).
        component_pattern (str): only waive findings where some involved
            component name matches this :mod:`fnmatch` pattern, e.g.
            ``"AB_*"``.
        max_value (float): only waive when the finding's ``value`` is at or
            below this, so a waiver written for a 256 um^2 overlap does not
            silently cover a 5000 um^2 one later.

    Example:
        Two flux lines cross couplings and are carried over on airbridges::

            Waiver("carried over on an airbridge, see fab notes",
                   rule="metal-overlap", component_pattern="FLUX_D5",
                   max_value=400e-6)
    """

    reason: str
    rule: str | None = None
    components: tuple[str, ...] | None = None
    component_pattern: str | None = None
    max_value: float | None = None

    def __post_init__(self):
        if not str(self.reason).strip():
            raise ValueError("Waiver needs a reason")
        if self.components is not None:
            object.__setattr__(self, "components", tuple(self.components))
        if (
            self.rule is None
            and self.components is None
            and self.component_pattern is None
            and self.max_value is None
        ):
            raise ValueError(
                "Waiver matches every finding; set rule, components, "
                "component_pattern, or max_value"
            )

    def matches(self, finding: Finding) -> bool:
        """Does this waiver cover `finding`?"""
        import fnmatch

        if self.rule is not None and finding.rule != self.rule:
            return False
        if self.components is not None and set(finding.components) != set(
            self.components
        ):
            return False
        if self.component_pattern is not None and not any(
            fnmatch.fnmatch(c, self.component_pattern) for c in finding.components
        ):
            return False
        if self.max_value is not None:
            if finding.value is None or finding.value > self.max_value:
                return False
        return True


@dataclass(frozen=True)
class WaivedFinding:
    """A :class:`Finding` matched by a :class:`Waiver`, kept for the report."""

    finding: Finding
    waiver: Waiver

    def __str__(self) -> str:
        return f"{self.finding}\n      waived: {self.waiver.reason}"


@dataclass
class ValidationResult:
    """Everything :func:`~qiskit_metal.validation.validate` found.

    Truthy when no ERROR-severity findings are present, so
    ``if validate(design): ...`` reads naturally. Use :attr:`errors` /
    :attr:`warnings` to filter, or :meth:`raise_if_errors` to turn a failed
    check into an exception (what a CI gate or a build script wants).
    """

    findings: list[Finding] = field(default_factory=list)
    rules_run: tuple[str, ...] = ()
    waived: list[WaivedFinding] = field(default_factory=list)
    unused_waivers: tuple[Waiver, ...] = ()

    @property
    def errors(self) -> list[Finding]:
        """Findings with ERROR severity."""
        return [f for f in self.findings if f.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        """Findings with WARNING severity."""
        return [f for f in self.findings if f.severity is Severity.WARNING]

    @property
    def ok(self) -> bool:
        """True when nothing of ERROR severity was found."""
        return not self.errors

    def __bool__(self) -> bool:
        return self.ok

    def __len__(self) -> int:
        return len(self.findings)

    def __iter__(self):
        return iter(self.findings)

    def raise_if_errors(self) -> "ValidationResult":
        """Raise :class:`DesignRuleViolation` if any ERROR findings exist.

        Returns self otherwise, so it chains: ``validate(d).raise_if_errors()``.
        """
        if self.errors:
            raise DesignRuleViolation(self)
        return self

    def report(self, include: Severity | None = None) -> str:
        """Render a readable multi-line report.

        Args:
            include (Severity): if given, only findings of this severity.
        """
        chosen = [f for f in self.findings if include is None or f.severity is include]
        if not chosen:
            head = (
                f"Design rules passed ({len(self.rules_run)} rules ran, no findings)."
            )
            lines = [head]
        else:
            lines = [
                f"{len(chosen)} finding(s) from {len(self.rules_run)} rule(s): "
                f"{len(self.errors)} error(s), {len(self.warnings)} warning(s)"
            ]
            lines += [f"  {f}" for f in chosen]
        # Waived findings are always shown. A waiver is a documented decision,
        # not a way to make the report shorter.
        if self.waived:
            lines.append(f"{len(self.waived)} waived:")
            lines += [f"  {w}" for w in self.waived]
        if self.unused_waivers:
            lines.append(
                f"{len(self.unused_waivers)} waiver(s) matched nothing "
                "(stale -- the design may have moved on):"
            )
            lines += [f"  {w.reason}" for w in self.unused_waivers]
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.report()


class DesignRuleViolation(Exception):
    """Raised by :meth:`ValidationResult.raise_if_errors`."""

    def __init__(self, result: ValidationResult):
        self.result = result
        super().__init__(result.report())


class DesignRule:
    """Base class for a check.

    Subclasses set :attr:`name` and implement :meth:`check`, yielding a
    :class:`Finding` per violation. Rules are plain objects so thresholds
    can be set per instance -- process design kits differ, and the defaults
    here are literature values, not universal truths.
    """

    name: str = "unnamed-rule"
    #: One-line description used in listings and docs.
    description: str = ""

    def check(self, design: "QDesign") -> Iterable[Finding]:
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<{type(self).__name__} {self.name!r}>"


# --- shared geometry helpers -------------------------------------------------
#
# The qgeometry tables store a route's centreline plus a width, and record
# the etched (subtract=True) footprint separately from the drawn metal. Every
# rule needs the same two derived views, so they live here rather than being
# re-derived slightly differently in each rule.


def component_names_by_id(design: "QDesign") -> dict[int, str]:
    """Map component id -> component name for the current design."""
    return {comp.id: name for name, comp in design.components.items()}


def _rows(design: "QDesign", table: str):
    """Yield qgeometry rows for ``table``, tolerating a missing table."""
    tables = design.qgeometry.tables
    if table not in tables:
        return
    yield from tables[table].iterrows()


def _row_chip(row) -> str:
    """The chip a qgeometry row is on (``"main"`` if the column is absent)."""
    chip = row.get("chip", None)
    return (
        "main"
        if chip is None or (isinstance(chip, float) and math.isnan(chip))
        else chip
    )


def geometry_chips(
    design: "QDesign", tables: Sequence[str] = ("path", "poly")
) -> list[str]:
    """Sorted names of the chips that hold any qgeometry in ``tables``."""
    chips = {_row_chip(row) for table in tables for _, row in _rows(design, table)}
    return sorted(chips)


def component_geometry(
    design: "QDesign",
    *,
    subtract: bool | None = False,
    tables: Sequence[str] = ("path", "poly"),
    chip: str | None = None,
) -> dict[str, MultiPolygon]:
    """Union each component's qgeometry into one polygon per component.

    Args:
        design (QDesign): the design to read.
        subtract (bool): ``False`` (default) keeps only drawn metal --
            centre conductors, pads, junctions. ``True`` keeps only the
            etched footprint (a CPW's trace + both gaps, a qubit's pocket).
            ``None`` keeps everything.
        tables (Sequence[str]): which qgeometry tables to read.
        chip (str): keep only rows on this chip. ``None`` (default) keeps
            every chip.

    Returns:
        dict: component name -> unioned geometry. Components contributing
        no geometry are omitted.
    """
    names = component_names_by_id(design)
    parts: dict[str, list] = {}
    for table in tables:
        for _, row in _rows(design, table):
            if subtract is not None and bool(row["subtract"]) != subtract:
                continue
            if chip is not None and _row_chip(row) != chip:
                continue
            geom = row["geometry"]
            if geom is None or geom.is_empty:
                continue
            if table == "path":
                # A path is a centreline; its metal is that line broadened to
                # the recorded width. flat caps (cap_style=2) so a route does
                # not appear to extend half a width past its end pin.
                geom = geom.buffer(row["width"] / 2.0, cap_style=2)
            parts.setdefault(names[row["component"]], []).append(geom)
    return {name: unary_union(geoms) for name, geoms in parts.items()}


def component_geometry_by_layer(
    design: "QDesign",
    *,
    subtract: bool | None = False,
    tables: Sequence[str] = ("path", "poly"),
    chip: str | None = None,
) -> dict[int, dict[str, MultiPolygon]]:
    """Like :func:`component_geometry`, but keyed by layer first.

    Rules about metal touching metal -- shorts, minimum spacing -- are only
    meaningful within a single layer. An airbridge span (layer 30) passing
    over a CPW (layer 1) overlaps in projection and is the whole point of
    an airbridge; comparing across layers reports every one of them as a
    short. The same holds across chips: layer 1 of two facing chips of a
    flip-chip design is two separate planes, so pass ``chip`` (see
    :func:`geometry_chips`) to compare one chip at a time.

    Returns:
        dict: layer -> {component name -> unioned geometry}.
    """
    names = component_names_by_id(design)
    parts: dict[int, dict[str, list]] = {}
    for table in tables:
        for _, row in _rows(design, table):
            if subtract is not None and bool(row["subtract"]) != subtract:
                continue
            if chip is not None and _row_chip(row) != chip:
                continue
            geom = row["geometry"]
            if geom is None or geom.is_empty:
                continue
            if table == "path":
                geom = geom.buffer(row["width"] / 2.0, cap_style=2)
            layer = int(row["layer"])
            parts.setdefault(layer, {}).setdefault(names[row["component"]], []).append(
                geom
            )
    return {
        layer: {name: unary_union(geoms) for name, geoms in by_name.items()}
        for layer, by_name in parts.items()
    }


def connected_component_pairs(design: "QDesign") -> set[frozenset]:
    """Component-name pairs that share a net, and so are meant to touch.

    A route landing on the pin of the component it connects to abuts that
    component's metal by construction. Without this, every intended
    connection reports as a short or a spacing violation.
    """
    pairs: set[frozenset] = set()
    nets = getattr(design, "net_info", None)
    if nets is None or len(nets) == 0:
        return pairs
    names = component_names_by_id(design)
    for _, group in nets.groupby("net_id"):
        members = {names.get(cid) for cid in group["component_id"]}
        members.discard(None)
        for a, b in itertools.combinations(sorted(members), 2):
            pairs.add(frozenset((a, b)))
    return pairs


def chip_bounds(
    design: "QDesign", chip: str = "main"
) -> tuple[float, float, float, float]:
    """Return ``(minx, miny, maxx, maxy)`` of a chip, in design units."""
    size = design._chips[chip]["size"]
    half_x = design.parse_value(size["size_x"]) / 2.0
    half_y = design.parse_value(size["size_y"]) / 2.0
    center_x = design.parse_value(size.get("center_x", "0um"))
    center_y = design.parse_value(size.get("center_y", "0um"))
    return (
        center_x - half_x,
        center_y - half_y,
        center_x + half_x,
        center_y + half_y,
    )


def representative_point(geom) -> tuple[float, float]:
    """A point inside ``geom``, for reporting where a violation is."""
    pt = geom.representative_point() if not geom.is_empty else geom.centroid
    return (float(pt.x), float(pt.y))
