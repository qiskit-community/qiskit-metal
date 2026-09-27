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
"""Solver-neutral description of a simulation.

Before any solver runs it must be told where current enters or leaves the
circuit (ports), how each Josephson junction is modeled, which pins end in an
open gap, what the metal surfaces and the outer walls are, where the mesh must
be fine, and what to solve for. :class:`SimulationProblem` holds those facts in
one place for every backend; the study classes (:class:`EigenmodeStudy`,
:class:`ElectrostaticStudy`, :class:`DrivenStudy`) hold what to solve for.

The simulation classes' tuple arguments convert both ways:

========================================  ===============================================
``open_terminations=[(c, p)]``            ``pins[PinRef(c, p)] = PinEnd.OPEN``
``port_list=[(c, p, Z)]``                 ``LumpedPort(PinRef(c, p), R=Z)``
``jj_to_port=[(c, j, Z, draw_ind)]``      ``junctions[JunctionRef(c, j)] = Junction("port",
                                          R=Z, shunt_inductor=draw_ind)``
``ignored_jjs=[(c, j)]``                  ``Junction("open")``
any other junction                        ``Junction("inductor")``: values from the
                                          junction's ``<renderer>_inductance`` column
                                          or ``setup.vars``
========================================  ===============================================

Values follow Metal's conventions: a length is a string with units, a design
variable, or a number in the design's units (as in component options); an R,
L or C is a string with units, a variable, or a number in SI units. Use
:func:`length_m` and :func:`circuit_value` to get SI floats.

Design and rationale: ``docs/architecture/solver_backends.md``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Union

import numpy as np

from qiskit_metal.toolbox_metal.parsing import UREG

if TYPE_CHECKING:
    from qiskit_metal.designs import QDesign

__all__ = [
    "PEC",
    "Adaptive",
    "Boundaries",
    "Box",
    "Conductivity",
    "DrivenStudy",
    "EigenmodeStudy",
    "ElectrostaticStudy",
    "Junction",
    "JunctionRef",
    "LossInterface",
    "LumpedPort",
    "MeshSpec",
    "NotExpressibleError",
    "PinEnd",
    "PinRef",
    "Refine",
    "Segment",
    "Select",
    "SimulationProblem",
    "SurfaceImpedance",
    "Sweep",
    "SymmetryPlane",
    "WavePort",
    "circuit_value",
    "length_m",
    "study_from_setup",
]

Value = Union[float, int, str]
"""A number or a Metal value string: ``"2um"``, ``"10nH"``, a variable name."""

Side = Literal["x-", "x+", "y-", "y+", "z-", "z+"]
SIDES: tuple[str, ...] = ("x-", "x+", "y-", "y+", "z-", "z+")

# ---------------------------------------------------------------------------
# Values


def _design_unit_m(design: "QDesign") -> float:
    return float(UREG.Quantity(1.0, design.get_units()).to("m").magnitude)


def length_m(value: Value, design: "QDesign") -> float:
    """A Metal length in meters.

    Args:
        value (Value): a string with units (``"2um"``), a design variable, or a
            number in the design's units, as in component options.
        design (QDesign): the design whose variables and units apply.

    Returns:
        float: the length in meters.

    Raises:
        ValueError: if ``value`` is not a length.
    """
    parsed = design.parse_value(value) if isinstance(value, str) else value
    if isinstance(parsed, str) or parsed is None:
        raise ValueError(f"{value!r} is not a length.")
    return float(parsed) * _design_unit_m(design)


def circuit_value(
    value: Value,
    unit: str,
    design: "QDesign | None" = None,
    variables: Mapping[str, Any] | None = None,
) -> float:
    """An R, L or C value in SI units.

    Args:
        value (Value): a number in SI units, a string with units (``"10nH"``,
            ``"50 ohm"``, ``"50"``), or the name of a variable in
            ``variables`` (e.g. ``setup.vars``) or in the design.
        unit (str): the SI unit to return, e.g. ``"ohm"``, ``"H"``, ``"F"``.
        design (QDesign, optional): looked up for variable names.
        variables (Mapping, optional): looked up first for variable names.

    Returns:
        float: the value in ``unit``.

    Raises:
        ValueError: if the value has the wrong dimension, or is a name that
            is neither a unit expression nor a known variable.
    """
    v = value
    seen = set()
    while isinstance(v, str):
        s = v.strip()
        if s in seen:
            raise ValueError(f"Variable {value!r} refers to itself.")
        seen.add(s)
        if variables is not None and s in variables:
            v = variables[s]
            continue
        if design is not None and s in design.variables:
            v = design.variables[s]
            continue
        try:
            q = UREG(s)
            # A bare number: pint <= 0.25.2 returns it as is, 0.25.3 as a
            # dimensionless Quantity.
            if not hasattr(q, "to"):
                return float(q)
            if q.dimensionless:
                return float(q.magnitude)
            return float(q.to(unit).magnitude)
        except Exception as e:  # pint: undefined unit, wrong dimension
            raise ValueError(
                f"{value!r} is not a value in {unit} or a known variable ({e})."
            ) from e
    return float(v)


def _number(x: Any) -> float:
    """Tuple arguments may carry impedances as strings (``"50"``)."""
    return circuit_value(x, "ohm") if isinstance(x, str) else float(x)


# ---------------------------------------------------------------------------
# Where things are


class PinEnd(str, Enum):
    """How a pin that is not a port ends."""

    SHORT = "short"
    """Default: the trace meets the ground plane."""
    OPEN = "open"
    """An endcap is cut into the ground plane: the pin ends in an open gap."""


@dataclass(frozen=True)
class PinRef:
    """A pin of a component."""

    component: str
    pin: str


@dataclass(frozen=True)
class JunctionRef:
    """A row of the design's ``junction`` qgeometry table."""

    component: str
    name: str


@dataclass(frozen=True)
class Segment:
    """An explicit port location: the segment from ``p0`` to ``p1`` (x, y) with
    a width, on a layer. The voltage is taken from ``p0`` to ``p1``."""

    p0: tuple[Value, Value]
    p1: tuple[Value, Value]
    width: Value
    layer: int = 1


Anchor = Union[PinRef, Segment]

# ---------------------------------------------------------------------------
# Ports and junctions

PortShape = Literal["sheet", "line", "cpw"]


@dataclass(frozen=True)
class LumpedPort:
    """A lumped port: a circuit element (R, L, C in parallel) or a driven
    port across a gap. A junction becomes a port through
    ``Junction("port")``, not through this class.

    Attributes:
        at (PinRef | Segment): where it sits. On a pin, the port spans the
            pin's gap from ``middle`` to ``middle + gap * normal``.
        R (Value, optional): resistance; for a driven study, the port's
            reference impedance. Defaults to 50 ohm.
        L (Value, optional): inductance. Defaults to None.
        C (Value, optional): capacitance. Defaults to None.
        shape (str): ``"sheet"`` (a rectangle), ``"line"`` (an edge chain,
            for edge-element solvers) or ``"cpw"`` (two sheets across a CPW's
            side gaps, driven with opposite signs). Defaults to ``"sheet"``.
        name (str, optional): defaults to ``Port_<component>_<pin>`` on a
            pin. Required on a :class:`Segment`.
    """

    at: Anchor
    R: Value | None = 50.0
    L: Value | None = None
    C: Value | None = None
    shape: PortShape = "sheet"
    name: str | None = None

    @property
    def label(self) -> str | None:
        """The port's name, given or derived from where it sits."""
        if self.name:
            return self.name
        if isinstance(self.at, PinRef):
            return f"Port_{self.at.component}_{self.at.pin}"
        return None


@dataclass(frozen=True)
class WavePort:
    """A wave port on an outer face of the model (driven studies).

    Attributes:
        face (str): ``"x-"``, ``"x+"``, ``"y-"``, ``"y+"``, ``"z-"`` or ``"z+"``.
        center (tuple): the port's center, in the face's two in-plane
            coordinates.
        size (tuple): the port's extent along those two coordinates.
        n_modes (int): number of port modes. Defaults to 1.
        name (str, optional): defaults to ``WavePort_<face>``.
    """

    face: Side
    center: tuple[Value, Value]
    size: tuple[Value, Value]
    n_modes: int = 1
    name: str | None = None

    @property
    def label(self) -> str:
        """The port's name, given or derived from the face."""
        return self.name or f"WavePort_{self.face}"


JunctionMode = Literal["inductor", "port", "open"]


@dataclass(frozen=True)
class Junction:
    """How a Josephson junction is modeled.

    Attributes:
        mode (str): ``"inductor"`` (a lumped L, with C and R if given: for
            eigenmodes and EPR), ``"port"`` (a lumped port: for impedance and
            scattering), or ``"open"`` (left out: the junction's gap is
            empty). Defaults to ``"inductor"``.
        L (Value, optional): inductance. None: the junction's
            ``<renderer>_inductance`` column, which may name a variable of
            ``setup.vars``.
        C (Value, optional): capacitance. None: the junction's
            ``<renderer>_capacitance`` column.
        R (Value, optional): for ``"port"``, the port's reference impedance;
            for ``"inductor"``, a resistance in parallel. None: the junction's
            ``<renderer>_resistance`` column (``"inductor"``) or 50 ohm
            (``"port"``).
        shunt_inductor (bool): for ``"port"``, keep the junction inductor
            beside the port (``draw_ind`` of ``jj_to_port``). Defaults to False.
    """

    mode: JunctionMode = "inductor"
    L: Value | None = None
    C: Value | None = None
    R: Value | None = None
    shunt_inductor: bool = False

    def __post_init__(self):
        if self.mode not in ("inductor", "port", "open"):
            raise ValueError(
                f"Junction mode must be 'inductor', 'port' or 'open', got {self.mode!r}."
            )


# ---------------------------------------------------------------------------
# Boundary conditions


@dataclass(frozen=True)
class PEC:
    """A perfect electric conductor (tangential E = 0)."""


@dataclass(frozen=True)
class SurfaceImpedance:
    """A metal surface with sheet impedance ``Rs + j w Ls`` (per square).

    ``Ls`` is the kinetic inductance, in H per square; ``Rs`` in ohm per square.
    """

    Ls: Value = 0.0
    Rs: Value = 0.0


@dataclass(frozen=True)
class Conductivity:
    """A normal-metal surface of conductivity ``sigma`` (S/m), optionally of a
    finite ``thickness``."""

    sigma: Value
    thickness: Value | None = None


MetalBC = Union[PEC, SurfaceImpedance, Conductivity]
OuterBC = Literal["pec", "pmc", "absorbing", "open"]


@dataclass(frozen=True)
class SymmetryPlane:
    """A mirror plane that cuts the model: ``"pmc"`` keeps the modes whose
    electric field is tangential to the plane, ``"pec"`` those whose field is
    normal to it."""

    axis: Literal["x", "y"]
    position: Value
    kind: Literal["pmc", "pec"] = "pmc"


@dataclass(frozen=True)
class LossInterface:
    """A thin lossy layer at a surface (metal-air, substrate-air, or
    metal-substrate), for surface participation ratios. No defaults."""

    thickness: Value
    eps_r: float
    tan_delta: float


@dataclass
class Boundaries:
    """Boundary conditions on metal surfaces and on the model's outer walls.

    Attributes:
        metal (PEC | SurfaceImpedance | Conductivity): every metal surface.
            Defaults to PEC.
        per_net (dict): overrides by net label.
        outer (dict, optional): side -> ``"pec"``, ``"pmc"``, ``"absorbing"``
            or ``"open"``. Sides not given take the study's default
            (:meth:`outer_for`).
        symmetry (list): mirror planes that cut the model.
        interfaces (dict): ``"MA"``, ``"SA"``, ``"MS"`` -> :class:`LossInterface`.
    """

    metal: MetalBC = field(default_factory=PEC)
    per_net: dict[str, MetalBC] = field(default_factory=dict)
    outer: dict[str, str] | None = None
    symmetry: list[SymmetryPlane] = field(default_factory=list)
    interfaces: dict[str, LossInterface] = field(default_factory=dict)

    def outer_for(self, study_kind: str) -> dict[str, str]:
        """The condition on each outer side for a study.

        Unset sides default to ``"open"`` for electrostatics and ``"pec"``
        (a closed package) otherwise.
        """
        default = "open" if study_kind == "electrostatic" else "pec"
        given = dict(self.outer or {})
        bad = set(given) - set(SIDES)
        if bad:
            raise ValueError(f"Unknown sides {sorted(bad)}; use {list(SIDES)}.")
        return {side: given.get(side, default) for side in SIDES}

    @property
    def is_default(self) -> bool:
        """True when nothing differs from PEC metal and default walls."""
        return (
            isinstance(self.metal, PEC)
            and not self.per_net
            and not self.outer
            and not self.symmetry
            and not self.interfaces
        )


# ---------------------------------------------------------------------------
# Mesh


@dataclass(frozen=True)
class Select:
    """What a mesh refinement targets. Set one or more fields; a target must
    match all that are set."""

    role: str | None = None
    net: str | None = None
    component: str | None = None
    port: str | None = None
    junction: JunctionRef | None = None
    box: tuple[Value, Value, Value, Value] | None = None  # x0, y0, x1, y1


@dataclass(frozen=True)
class Refine:
    """Element size ``size`` on the target, growing to the bulk size over the
    distance ``grow`` (``shape="distance"``), or inside a ball of radius
    ``grow`` around it (``shape="ball"``)."""

    select: Select
    size: Value
    grow: Value
    shape: Literal["distance", "ball"] = "distance"


@dataclass
class MeshSpec:
    """Where the mesh must be fine. None fields keep the renderer's own
    options."""

    max_size: Value | None = None
    min_size: Value | None = None
    refine: list[Refine] = field(default_factory=list)


# ---------------------------------------------------------------------------
# The problem


class NotExpressibleError(ValueError):
    """The problem holds something the simulation classes' tuple arguments
    cannot express."""


@dataclass
class Box:
    """The extent of the model: the bounding box of the rendered components
    plus the renderer's buffer (``plus_buffer=True``), or the chip size."""

    plus_buffer: bool = True


@dataclass
class SimulationProblem:
    """What a solver needs to know about the design, independent of the solver.

    Attributes:
        design (QDesign): the design.
        components (list, optional): components to render; None: all.
        box (Box): the model's extent.
        pins (dict): pins that are not ports and end open; others are shorted.
        junctions (dict): junctions not modeled as the default inductor.
        ports (list): lumped and wave ports, in order.
        boundaries (Boundaries): metal and outer-wall conditions.
        materials (dict): material options for this problem, by name.
        mesh (MeshSpec): mesh refinement.
    """

    design: "QDesign | None" = None
    components: list[str] | None = None
    box: Box = field(default_factory=Box)
    pins: dict[PinRef, PinEnd] = field(default_factory=dict)
    junctions: dict[JunctionRef, Junction] = field(default_factory=dict)
    ports: list[LumpedPort | WavePort] = field(default_factory=list)
    boundaries: Boundaries = field(default_factory=Boundaries)
    materials: dict[str, Any] = field(default_factory=dict)
    mesh: MeshSpec = field(default_factory=MeshSpec)

    # -- conversion from and to the simulation classes' arguments ----------

    @classmethod
    def from_run_args(
        cls,
        design: "QDesign | None" = None,
        components: list | None = None,
        open_terminations: list | None = None,
        port_list: list | None = None,
        jj_to_port: list | None = None,
        ignored_jjs: list | None = None,
        box_plus_buffer: bool = True,
    ) -> "SimulationProblem":
        """Build a problem from the arguments of ``run_sim``.

        Args:
            design (QDesign, optional): the design.
            components (list, optional): components to render; None: all.
            open_terminations (list, optional): ``(component, pin)`` pins that
                end open.
            port_list (list, optional): ``(component, pin, impedance)`` ports.
            jj_to_port (list, optional): ``(component, junction, impedance,
                draw_ind)`` junctions rendered as ports; the three-element
                form of the pyaedt renderers is accepted too.
            ignored_jjs (list, optional): ``(component, junction)`` junctions
                left out.
            box_plus_buffer (bool): see :class:`Box`. Defaults to True.

        Returns:
            SimulationProblem: the problem. Names are not checked against the
            design here; see :meth:`validate`.

        Raises:
            ValueError: on a malformed tuple, or a junction listed both as a
                port and as ignored.
        """
        problem = cls(
            design=design,
            components=list(components) if components is not None else None,
            box=Box(plus_buffer=bool(box_plus_buffer)),
        )
        for item in open_terminations or []:
            comp, pin = _unpack(item, 2, "open_terminations", "(component, pin)")
            problem.pins[PinRef(comp, pin)] = PinEnd.OPEN
        for item in port_list or []:
            comp, pin, z = _unpack(item, 3, "port_list", "(component, pin, impedance)")
            problem.ports.append(LumpedPort(PinRef(comp, pin), R=_number(z)))
        for item in jj_to_port or []:
            if len(item) == 3:
                comp, name, z = item
                draw_ind = False
            else:
                comp, name, z, draw_ind = _unpack(
                    item, 4, "jj_to_port", "(component, junction, impedance, draw_ind)"
                )
            problem.junctions[JunctionRef(comp, name)] = Junction(
                "port", R=_number(z), shunt_inductor=bool(draw_ind)
            )
        for item in ignored_jjs or []:
            comp, name = _unpack(item, 2, "ignored_jjs", "(component, junction)")
            ref = JunctionRef(comp, name)
            if ref in problem.junctions:
                raise ValueError(
                    f"Junction {comp}.{name} is in both jj_to_port and ignored_jjs."
                )
            problem.junctions[ref] = Junction("open")
        return problem

    def to_run_args(self, jj_to_port_arity: Literal[3, 4] = 4) -> dict[str, Any]:
        """The ``run_sim`` arguments for this problem (for the Ansys renderers).

        Mesh refinement and material options have no tuple form: backends
        that cannot use them report them as ignored settings. Everything else
        that the tuples cannot express raises.

        Args:
            jj_to_port_arity (int): 4 for the COM renderers, 3 for the pyaedt
                renderers. Defaults to 4.

        Returns:
            dict: ``components``, ``open_terminations``, ``port_list``,
            ``jj_to_port``, ``ignored_jjs`` (None when empty) and
            ``box_plus_buffer``.

        Raises:
            NotExpressibleError: listing every part with no tuple form.
        """
        problems = []
        port_list = []
        for port in self.ports:
            if isinstance(port, WavePort):
                problems.append(f"wave port {port.label}")
            elif not isinstance(port.at, PinRef):
                problems.append(f"lumped port {port.label or port.at} is not on a pin")
            elif port.shape != "sheet" or port.L is not None or port.C is not None:
                problems.append(
                    f"lumped port {port.label} has shape {port.shape!r} or an L or C"
                )
            elif port.R is None:
                problems.append(f"lumped port {port.label} has no impedance")
            else:
                port_list.append((port.at.component, port.at.pin, _number(port.R)))

        jj_to_port, ignored_jjs = [], []
        for ref, jj in self.junctions.items():
            where = f"junction {ref.component}.{ref.name}"
            if jj.mode == "open":
                ignored_jjs.append((ref.component, ref.name))
            elif jj.mode == "port":
                if jj.L is not None or jj.C is not None:
                    problems.append(f"{where}: a port with its own L or C")
                    continue
                z = 50.0 if jj.R is None else _number(jj.R)
                if jj_to_port_arity == 3:
                    if jj.shunt_inductor:
                        problems.append(
                            f"{where}: shunt_inductor needs the four-element form"
                        )
                        continue
                    jj_to_port.append((ref.component, ref.name, z))
                else:
                    jj_to_port.append(
                        (ref.component, ref.name, z, bool(jj.shunt_inductor))
                    )
            elif any(v is not None for v in (jj.L, jj.C, jj.R)):
                problems.append(
                    f"{where}: explicit L, C or R (the tuples take them from the "
                    "junction's <renderer>_inductance / _capacitance / _resistance)"
                )

        if not self.boundaries.is_default:
            problems.append(
                "boundary conditions other than PEC metal and default walls"
            )
        if problems:
            raise NotExpressibleError(
                "No run_sim argument form for: " + "; ".join(problems) + "."
            )

        open_terminations = [
            (ref.component, ref.pin)
            for ref, end in self.pins.items()
            if end == PinEnd.OPEN
        ]
        return dict(
            components=list(self.components) if self.components is not None else None,
            open_terminations=open_terminations or None,
            port_list=port_list or None,
            jj_to_port=jj_to_port or None,
            ignored_jjs=ignored_jjs or None,
            box_plus_buffer=self.box.plus_buffer,
        )

    # -- queries -----------------------------------------------------------

    def junction(self, ref: JunctionRef) -> Junction:
        """How a junction is modeled: its entry, else the default inductor."""
        return self.junctions.get(ref, Junction())

    def pin_end(self, ref: PinRef) -> PinEnd:
        """How a pin that is not a port ends."""
        return self.pins.get(ref, PinEnd.SHORT)

    def port_labels(self) -> list[str | None]:
        """Port names: the lumped and wave ports in order, then the junctions
        modeled as ports (``Port_<component>_<junction>``)."""
        return [port.label for port in self.ports] + [
            f"Port_{ref.component}_{ref.name}"
            for ref, jj in self.junctions.items()
            if jj.mode == "port"
        ]

    # -- checks ------------------------------------------------------------

    def validate(self) -> None:
        """Check the problem against the design.

        Raises:
            ValueError: listing every unknown component, pin or junction, every
                reference to a component outside ``components``, pins that are
                both open and a port, and missing or repeated port names.
        """
        design = self.design
        if design is None:
            raise ValueError("The problem has no design to check against.")
        errors = []
        selected = set(self.components) if self.components is not None else None

        def check_component(name: str, what: str) -> bool:
            if name not in design.components:
                errors.append(f"{what}: no component {name!r}")
                return False
            if selected is not None and name not in selected:
                errors.append(f"{what}: component {name!r} is not in components")
            return True

        for name in self.components or []:
            if name not in design.components:
                errors.append(f"components: no component {name!r}")

        port_pins = [
            port.at
            for port in self.ports
            if isinstance(port, LumpedPort) and isinstance(port.at, PinRef)
        ]
        for ref in dict.fromkeys(list(self.pins) + port_pins):
            what = f"pin {ref.component}.{ref.pin}"
            if check_component(ref.component, what):
                if ref.pin not in design.components[ref.component].pins:
                    errors.append(f"{what}: no such pin")
        for ref in self.pins:
            if self.pins[ref] == PinEnd.OPEN and ref in port_pins:
                errors.append(
                    f"pin {ref.component}.{ref.pin} is both open and a port "
                    "(a port's pin is cut open already)"
                )

        table = design.qgeometry.tables.get("junction")
        for ref in self.junctions:
            what = f"junction {ref.component}.{ref.name}"
            if not check_component(ref.component, what):
                continue
            comp_id = design.components[ref.component].id
            rows = (
                table[(table["component"] == comp_id) & (table["name"] == ref.name)]
                if table is not None
                else []
            )
            if len(rows) == 0:
                errors.append(f"{what}: no such junction in the junction table")

        labels = self.port_labels()
        if any(label is None for label in labels):
            errors.append("a port on a Segment needs a name")
        named = [label for label in labels if label is not None]
        repeated = sorted({label for label in named if named.count(label) > 1})
        if repeated:
            errors.append(f"repeated port names {repeated}")

        if errors:
            raise ValueError("Invalid simulation problem: " + "; ".join(errors) + ".")


def _unpack(item, n: int, arg: str, form: str) -> tuple:
    if not isinstance(item, (tuple, list)) or len(item) != n:
        raise ValueError(f"Each entry of {arg} must be {form}, got {item!r}.")
    return tuple(item)


# ---------------------------------------------------------------------------
# Studies


_BOOKKEEPING = frozenset({"name", "reuse_selected_design", "reuse_setup"})
"""QSimulation keys that name and reuse setups; not part of the physics."""


@dataclass(frozen=True)
class Adaptive:
    """Adaptive mesh refinement: refine and re-solve until ``criterion`` falls
    below ``tolerance`` on ``min_converged`` consecutive passes, within
    ``min_passes`` to ``max_passes`` passes, refining ``refine_pct`` percent of
    the elements each pass."""

    max_passes: int
    min_passes: int = 1
    min_converged: int = 1
    tolerance: float | None = None
    criterion: str | None = None  # "delta_f_pct", "delta_c_pct", "delta_s"
    refine_pct: float | None = None


def _adaptive(
    s: Mapping, converged_key: str, tol_key: str, criterion: str, refine_key: str
) -> Adaptive | None:
    if s.get("max_passes") is None:
        return None
    return Adaptive(
        max_passes=int(float(s["max_passes"])),
        min_passes=int(float(s.get("min_passes", 1))),
        min_converged=int(float(s.get(converged_key, 1))),
        tolerance=None if s.get(tol_key) is None else float(s[tol_key]),
        criterion=criterion,
        refine_pct=None if s.get(refine_key) is None else float(s[refine_key]),
    )


def _split(
    setup: Mapping, defaults: Mapping | None, used: set
) -> tuple[dict, frozenset]:
    """Keys no neutral field uses, and keys that differ from the defaults."""
    s = dict(setup)
    d = dict(defaults or {})
    rest = {k: v for k, v in s.items() if k not in used and k not in _BOOKKEEPING}
    set_keys = frozenset(
        k for k, v in s.items() if k not in _BOOKKEEPING and (k not in d or d[k] != v)
    )
    return rest, set_keys


_ADAPTIVE_EIG = {
    "max_passes",
    "min_passes",
    "min_converged",
    "max_delta_f",
    "pct_refinement",
}
_ADAPTIVE_CAP = {
    "max_passes",
    "min_passes",
    "min_converged_passes",
    "percent_error",
    "percent_refinement",
}
_ADAPTIVE_DRV = {
    "max_passes",
    "min_passes",
    "min_converged",
    "max_delta_s",
    "pct_refinement",
}


@dataclass
class EigenmodeStudy:
    """Find ``n_modes`` modes above ``min_freq_ghz``.

    Attributes:
        n_modes (int): number of modes.
        min_freq_ghz (float): modes are sought above this frequency.
        order (int, optional): element order, where the backend lets you
            choose.
        adaptive (Adaptive, optional): adaptive refinement settings.
        backend_settings (dict): setup keys with no neutral meaning (e.g.
            ``basis_order``, ``vars``), for the backend that knows them.
        set_keys (frozenset): setup keys that differ from the simulation
            class's defaults.
    """

    kind: ClassVar[str] = "eigenmode"
    n_modes: int = 1
    min_freq_ghz: float = 1.0
    order: int | None = None
    adaptive: Adaptive | None = None
    backend_settings: dict = field(default_factory=dict)
    set_keys: frozenset = frozenset()

    @classmethod
    def from_setup(
        cls, setup: Mapping, defaults: Mapping | None = None
    ) -> "EigenmodeStudy":
        """From ``EigenmodeSim.setup``; ``defaults`` is its ``default_setup``."""
        used = {"n_modes", "min_freq_ghz"} | _ADAPTIVE_EIG
        rest, set_keys = _split(setup, defaults, used)
        return cls(
            n_modes=int(float(setup.get("n_modes", 1))),
            min_freq_ghz=float(setup.get("min_freq_ghz", 1.0)),
            adaptive=_adaptive(
                setup, "min_converged", "max_delta_f", "delta_f_pct", "pct_refinement"
            ),
            backend_settings=rest,
            set_keys=set_keys,
        )


@dataclass
class ElectrostaticStudy:
    """Find the Maxwell capacitance matrix between the nets.

    Attributes: as :class:`EigenmodeStudy`, less the mode search.
    """

    kind: ClassVar[str] = "electrostatic"
    order: int | None = None
    adaptive: Adaptive | None = None
    backend_settings: dict = field(default_factory=dict)
    set_keys: frozenset = frozenset()

    @classmethod
    def from_setup(
        cls, setup: Mapping, defaults: Mapping | None = None
    ) -> "ElectrostaticStudy":
        """From ``LumpedElementsSim.setup``; ``defaults`` is its
        ``default_setup``. ``freq_ghz`` (Q3D's adaptive frequency) and the
        solver choices stay in ``backend_settings``."""
        rest, set_keys = _split(setup, defaults, _ADAPTIVE_CAP)
        return cls(
            adaptive=_adaptive(
                setup,
                "min_converged_passes",
                "percent_error",
                "delta_c_pct",
                "percent_refinement",
            ),
            backend_settings=rest,
            set_keys=set_keys,
        )


@dataclass(frozen=True)
class Sweep:
    """Frequencies from ``start_ghz`` to ``stop_ghz``: ``count`` points, or a
    step of ``step_ghz`` when that is set (as in the Ansys renderers)."""

    start_ghz: float
    stop_ghz: float
    count: int | None = None
    step_ghz: float | None = None
    kind: str | None = None  # e.g. "Fast", "Discrete", "Interpolating"

    def frequencies_ghz(self) -> np.ndarray:
        """The sweep's frequencies."""
        if self.step_ghz:
            n = math.floor((self.stop_ghz - self.start_ghz) / self.step_ghz + 1e-9)
            return self.start_ghz + self.step_ghz * np.arange(n + 1)
        if not self.count:
            raise ValueError("A sweep needs count or step_ghz.")
        return np.linspace(self.start_ghz, self.stop_ghz, int(self.count))


@dataclass
class DrivenStudy:
    """Solve at the frequencies of ``sweep`` with the ports driven.

    Attributes:
        sweep (Sweep): the frequencies.
        adapt_freq_ghz (float, optional): where adaptive refinement runs.
        excite (list): names of the driven ports; empty: every port.
        order, adaptive, backend_settings, set_keys: as
            :class:`EigenmodeStudy`.
    """

    kind: ClassVar[str] = "driven"
    sweep: Sweep | None = None
    adapt_freq_ghz: float | None = None
    excite: list[str] = field(default_factory=list)
    order: int | None = None
    adaptive: Adaptive | None = None
    backend_settings: dict = field(default_factory=dict)
    set_keys: frozenset = frozenset()

    @classmethod
    def from_setup(
        cls, setup: Mapping, defaults: Mapping | None = None
    ) -> "DrivenStudy":
        """From ``ScatteringImpedanceSim.setup``; ``defaults`` is its
        ``default_setup``."""
        used = {"freq_ghz", "sweep_setup"} | _ADAPTIVE_DRV
        rest, set_keys = _split(setup, defaults, used)
        sw = setup.get("sweep_setup")
        sweep = None
        if sw:
            sweep = Sweep(
                start_ghz=float(sw["start_ghz"]),
                stop_ghz=float(sw["stop_ghz"]),
                count=None if sw.get("count") is None else int(sw["count"]),
                step_ghz=None if sw.get("step_ghz") is None else float(sw["step_ghz"]),
                kind=sw.get("type"),
            )
            extra = {k: v for k, v in sw.items() if k in ("name", "save_fields")}
            if extra:
                rest["sweep_setup"] = extra
        return cls(
            sweep=sweep,
            adapt_freq_ghz=(
                None if setup.get("freq_ghz") is None else float(setup["freq_ghz"])
            ),
            adaptive=_adaptive(
                setup, "min_converged", "max_delta_s", "delta_s", "pct_refinement"
            ),
            backend_settings=rest,
            set_keys=set_keys,
        )


_STUDY_BY_SOLUTION_TYPE = {
    "eigenmode": EigenmodeStudy,
    "capacitive": ElectrostaticStudy,
    "drivenmodal": DrivenStudy,
}


def study_from_setup(
    solution_type: str, setup: Mapping, defaults: Mapping | None = None
) -> EigenmodeStudy | ElectrostaticStudy | DrivenStudy:
    """The study for a simulation class's ``solution_type`` and ``setup``.

    Args:
        solution_type (str): ``"eigenmode"``, ``"capacitive"`` or
            ``"drivenmodal"``, as the simulation classes pass to the renderer.
        setup (Mapping): the simulation's ``setup``.
        defaults (Mapping, optional): the class's ``default_setup``, to tell
            which keys the user changed.

    Returns:
        EigenmodeStudy | ElectrostaticStudy | DrivenStudy: the study.
    """
    try:
        cls = _STUDY_BY_SOLUTION_TYPE[solution_type]
    except KeyError:
        raise ValueError(
            f"Unknown solution_type {solution_type!r}; "
            f"use one of {sorted(_STUDY_BY_SOLUTION_TYPE)}."
        ) from None
    return cls.from_setup(setup, defaults)
