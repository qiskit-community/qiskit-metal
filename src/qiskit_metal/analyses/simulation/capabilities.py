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
"""What each simulation backend can do, and the check before a run.

Backends differ: HFSS solves eigenmodes and driven problems, Q3D and ElmerFEM
capacitance matrices; some take wave ports or kinetic inductance and some do
not; some are driven by the simulation classes (``EigenmodeSim`` and
friends) and some are used directly. Each backend declares this in a
:class:`Capabilities` record, and a simulation checks it before it renders
anything, failing with a message that names the backends that can do the job.

A renderer declares its capabilities with a class attribute ``capabilities``;
the renderers that predate this module are described in :data:`BUILTIN`, which
records what their code does today (the renderers themselves are unchanged).

Design and rationale: ``docs/architecture/solver_backends.md``, section 3.11.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from qiskit_metal.analyses.simulation.problem import SimulationProblem

__all__ = [
    "BUILTIN",
    "BackendCapabilityError",
    "Capabilities",
    "CapabilityReport",
    "Requirements",
    "capabilities_for",
    "capability_table",
    "check_study",
    "requirements_from_problem",
]

STUDIES = ("eigenmode", "electrostatic", "driven", "magnetostatic")
_ADAPTIVE_KEYS = frozenset(
    {
        "max_passes",
        "min_passes",
        "min_converged",
        "min_converged_passes",
        "max_delta_f",
        "max_delta_s",
        "percent_error",
        "pct_refinement",
        "percent_refinement",
    }
)


class BackendCapabilityError(ValueError):
    """The chosen backend cannot run what was asked."""


@dataclass(frozen=True)
class Capabilities:
    """What a backend can do.

    Attributes:
        label (str): a short human-readable name.
        studies (frozenset): ``"eigenmode"``, ``"electrostatic"``,
            ``"driven"``, ``"magnetostatic"``.
        simulation_classes (bool): True when ``EigenmodeSim``,
            ``LumpedElementsSim`` and ``ScatteringImpedanceSim`` can drive it;
            False when it is used through its own API.
        direct_use (str): where to look when it is used directly.
        ports (frozenset): ``"lumped_sheet"``, ``"lumped_line"``,
            ``"lumped_cpw"``, ``"wave"``.
        junctions (frozenset): ``"inductor"``, ``"port"``, ``"open"``.
        boundaries (frozenset): ``"pec"``, ``"pmc_wall"``, ``"absorbing"``,
            ``"open_electrostatic"``, ``"surface_impedance"``,
            ``"conductivity"``, ``"pmc_symmetry"``, ``"pec_symmetry"``.
        outputs (frozenset): ``"frequencies"``, ``"q"``, ``"junction_epr"``,
            ``"surface_epr"``, ``"capacitance"``, ``"network"``,
            ``"convergence_history"``, ``"fields"``.
        geometry (frozenset): ``"ground_cutouts"``, ``"sheet_metal"``,
            ``"thick_metal"``, ``"multi_layer"``, ``"flip_chip"``,
            ``"any_pin_angle"``.
        materials (frozenset): ``"options"`` (Metal's material options reach
            the solver), ``"from_layer_stack"``, ``"loss_tangent"``,
            ``"anisotropic"``.
        element_orders (tuple): orders the user can choose; empty when the
            backend chooses.
        adaptive_refinement (bool): refines the mesh itself between passes.
        parallel (str): ``"none"``, ``"threads"``, ``"mpi"``.
        requires (tuple): what must be installed, in words.
        notes (str): anything else a user should know.
    """

    label: str
    studies: frozenset = frozenset()
    simulation_classes: bool = False
    direct_use: str = ""
    ports: frozenset = frozenset()
    junctions: frozenset = frozenset()
    boundaries: frozenset = frozenset()
    outputs: frozenset = frozenset()
    geometry: frozenset = frozenset()
    materials: frozenset = frozenset()
    element_orders: tuple = ()
    adaptive_refinement: bool = False
    parallel: Literal["none", "threads", "mpi"] = "none"
    requires: tuple = ()
    notes: str = ""

    def check(self, requirements: "Requirements", study=None) -> "CapabilityReport":
        """Compare a problem's requirements with this backend.

        Args:
            requirements (Requirements): what the problem needs.
            study (optional): the study; its settings that this backend does
                not honor are reported as ignored when the user changed them
                (``study.set_keys``).

        Returns:
            CapabilityReport: what is missing (an error) and what is ignored
            (a warning).
        """
        missing = []
        if requirements.study and requirements.study not in self.studies:
            missing.append(f"study '{requirements.study}'")
        for kind, needed, have in (
            ("port", requirements.ports, self.ports),
            ("junction model", requirements.junctions, self.junctions),
            ("boundary condition", requirements.boundaries, self.boundaries),
            ("output", requirements.outputs, self.outputs),
        ):
            for item in sorted(set(needed) - set(have)):
                missing.append(f"{kind} '{item}'")

        ignored = []
        if study is not None:
            set_keys = set(getattr(study, "set_keys", ()))
            if not self.adaptive_refinement:
                ignored += sorted(set_keys & _ADAPTIVE_KEYS)
            order = getattr(study, "order", None)
            if order is not None and order not in self.element_orders:
                ignored.append(f"order={order}")
        return CapabilityReport(missing=missing, ignored=ignored)


@dataclass(frozen=True)
class Requirements:
    """What a problem needs from a backend."""

    study: str | None = None
    ports: frozenset = frozenset()
    junctions: frozenset = frozenset()
    boundaries: frozenset = frozenset()
    outputs: frozenset = frozenset()


@dataclass
class CapabilityReport:
    """The result of :meth:`Capabilities.check`."""

    missing: list = field(default_factory=list)
    ignored: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when nothing is missing."""
        return not self.missing


# ---------------------------------------------------------------------------
# The renderers that predate this module, as their code behaves today.

_ANSYS_COM = ("Ansys AEDT with a license, on Windows (COM)", "quantum-metal[ansys]")
_ANSYS_PYAEDT = ("Ansys AEDT with a license", "quantum-metal[ansys] (pyaedt)")

BUILTIN: dict[str, Capabilities] = {
    "hfss": Capabilities(
        label="Ansys HFSS (COM)",
        studies=frozenset({"eigenmode", "driven"}),
        simulation_classes=True,
        ports=frozenset({"lumped_sheet"}),
        junctions=frozenset({"inductor", "port", "open"}),
        boundaries=frozenset({"pec"}),
        outputs=frozenset(
            {
                "frequencies",
                "q",
                "junction_epr",
                "surface_epr",
                "network",
                "convergence_history",
                "fields",
            }
        ),
        geometry=frozenset({"ground_cutouts", "sheet_metal", "flip_chip"}),
        adaptive_refinement=True,
        parallel="threads",
        requires=_ANSYS_COM,
        notes="Materials come from AEDT's library by name; walls at AEDT defaults.",
    ),
    "q3d": Capabilities(
        label="Ansys Q3D (COM)",
        studies=frozenset({"electrostatic"}),
        simulation_classes=True,
        junctions=frozenset({"open"}),
        boundaries=frozenset({"pec", "open_electrostatic"}),
        outputs=frozenset({"capacitance", "convergence_history"}),
        geometry=frozenset({"ground_cutouts", "sheet_metal", "flip_chip"}),
        adaptive_refinement=True,
        parallel="threads",
        requires=_ANSYS_COM,
        notes="Materials come from AEDT's library by name.",
    ),
    "aedt_hfss": Capabilities(
        label="Ansys HFSS (pyaedt)",
        studies=frozenset({"eigenmode", "driven"}),
        direct_use=(
            "QHFSSEigenmodePyaedt / QHFSSDrivenmodalPyaedt; tutorials in "
            "docs/tut/4-Analysis/pyaedt-multiplanar"
        ),
        ports=frozenset({"lumped_sheet"}),
        junctions=frozenset({"inductor", "port", "open"}),
        boundaries=frozenset({"pec"}),
        outputs=frozenset({"frequencies", "q", "junction_epr", "network"}),
        geometry=frozenset({"ground_cutouts", "thick_metal", "multi_layer"}),
        materials=frozenset({"from_layer_stack"}),
        adaptive_refinement=True,
        parallel="threads",
        requires=_ANSYS_PYAEDT,
        notes="Ports in driven studies only.",
    ),
    "aedt_q3d": Capabilities(
        label="Ansys Q3D (pyaedt)",
        studies=frozenset({"electrostatic"}),
        direct_use=(
            "QQ3DPyaedt; tutorial docs/tut/4-Analysis/pyaedt-multiplanar/"
            "Q3D-pyaedt-multiplanar"
        ),
        junctions=frozenset({"open"}),
        boundaries=frozenset({"pec", "open_electrostatic"}),
        outputs=frozenset({"capacitance"}),
        geometry=frozenset({"ground_cutouts", "thick_metal", "multi_layer"}),
        materials=frozenset({"from_layer_stack"}),
        adaptive_refinement=True,
        parallel="threads",
        requires=_ANSYS_PYAEDT,
    ),
    "elmer": Capabilities(
        label="gmsh + ElmerFEM",
        studies=frozenset({"electrostatic"}),
        direct_use=(
            "render_design, add_solution_setup('capacitance'), run('capacitance'); "
            "tutorial 4.19"
        ),
        junctions=frozenset({"open"}),
        boundaries=frozenset({"pec", "open_electrostatic"}),
        outputs=frozenset({"capacitance", "fields"}),
        geometry=frozenset(
            {"ground_cutouts", "sheet_metal", "thick_metal", "multi_layer"}
        ),
        requires=(
            "ElmerGrid and ElmerSolver on PATH",
            "quantum-metal[mesh] (gmsh)",
        ),
    ),
    "gmsh": Capabilities(
        label="gmsh (mesher)",
        direct_use="render_design, export_mesh; tutorial 3.5",
        geometry=frozenset(
            {"ground_cutouts", "sheet_metal", "thick_metal", "multi_layer"}
        ),
        requires=("quantum-metal[mesh] (gmsh)",),
        notes="Builds and meshes the model; solves nothing.",
    ),
    "gds": Capabilities(
        label="GDS export",
        direct_use="export_to_gds; tutorial 3.2",
        notes="Writes the layout; solves nothing.",
    ),
}
"""Capabilities of the renderers registered in ``config.renderers_to_load``."""


def capabilities_for(renderer_name: str, renderer=None) -> Capabilities | None:
    """The capabilities a renderer declares.

    Args:
        renderer_name (str): its name, as in ``config.renderers_to_load``.
        renderer (optional): the renderer object or class; its
            ``capabilities`` attribute wins over :data:`BUILTIN`.

    Returns:
        Capabilities | None: None when nothing is declared.
    """
    declared = getattr(renderer, "capabilities", None)
    if isinstance(declared, Capabilities):
        return declared
    return BUILTIN.get(renderer_name)


def _alternatives(study: str, registered: Iterable[str]) -> str:
    registered = set(registered)
    names = [
        name
        for name, caps in BUILTIN.items()
        if caps.simulation_classes and study in caps.studies
    ]
    if not names:
        return "none of the renderers registered with Quantum Metal"
    parts = []
    for name in names:
        caps = BUILTIN[name]
        where = (
            "registered in this design"
            if name in registered
            else "needs " + ", ".join(caps.requires)
        )
        parts.append(f"'{name}' ({caps.label}; {where})")
    return "; ".join(parts)


def check_study(
    renderer_name: str,
    study: str,
    simulation: str,
    registered: Iterable[str] = (),
    renderer=None,
) -> None:
    """Check, before rendering, that a renderer can run a simulation class's
    study.

    Args:
        renderer_name (str): the renderer's name.
        study (str): ``"eigenmode"``, ``"electrostatic"`` or ``"driven"``.
        simulation (str): the simulation class's name, for the message.
        registered (iterable): renderer names registered in the design.
        renderer (optional): the renderer object, for declared capabilities.

    Raises:
        BackendCapabilityError: when the renderer cannot run the study
            through the simulation classes. Renderers that declare nothing
            are not checked.
    """
    caps = capabilities_for(renderer_name, renderer)
    if caps is None:
        return
    if caps.simulation_classes and study in caps.studies:
        return
    if not caps.studies:
        why = f"'{renderer_name}' ({caps.label}) runs no simulations."
    elif study not in caps.studies:
        why = (
            f"'{renderer_name}' ({caps.label}) cannot run {study} studies; "
            f"it runs {', '.join(sorted(caps.studies))}."
        )
    else:
        why = (
            f"'{renderer_name}' ({caps.label}) runs {study} studies through its "
            f"own API, not through {simulation}"
            + (f": {caps.direct_use}." if caps.direct_use else ".")
        )
    raise BackendCapabilityError(
        f"{simulation}(renderer_name='{renderer_name}'): {why} "
        f"Renderers that run {study} studies through {simulation}: "
        f"{_alternatives(study, registered)}."
    )


# ---------------------------------------------------------------------------
# From a problem to its requirements


_PORT_KIND = {"sheet": "lumped_sheet", "line": "lumped_line", "cpw": "lumped_cpw"}


def _metal_kind(bc) -> str:
    from qiskit_metal.analyses.simulation.problem import (
        Conductivity,
        SurfaceImpedance,
    )

    if isinstance(bc, SurfaceImpedance):
        return "surface_impedance"
    if isinstance(bc, Conductivity):
        return "conductivity"
    return "pec"


def _has_unlisted_junction(problem: "SimulationProblem") -> bool:
    """Does the design hold a junction, among the rendered components, that
    the problem leaves at the default (an inductor)?"""
    from qiskit_metal.analyses.simulation.problem import JunctionRef

    design = problem.design
    if design is None:
        return False
    table = design.qgeometry.tables.get("junction")
    if table is None or table.empty:
        return False
    names = {comp.id: name for name, comp in design.components.items()}
    selected = set(problem.components) if problem.components is not None else None
    for comp_id, jj_name in zip(table["component"], table["name"]):
        comp = names.get(comp_id)
        if selected is not None and comp not in selected:
            continue
        if JunctionRef(comp, jj_name) not in problem.junctions:
            return True
    return False


def requirements_from_problem(
    problem: "SimulationProblem", study, outputs: Iterable[str] = ()
) -> Requirements:
    """What a problem and study need from a backend.

    Args:
        problem (SimulationProblem): the problem.
        study: an :class:`~qiskit_metal.analyses.simulation.problem.EigenmodeStudy`,
            ``ElectrostaticStudy`` or ``DrivenStudy``.
        outputs (iterable): the outputs the caller needs, e.g.
            ``{"frequencies", "junction_epr"}``.

    Returns:
        Requirements: the study, port kinds, junction models, boundary
        conditions and outputs used.
    """
    from qiskit_metal.analyses.simulation.problem import LumpedPort, WavePort

    ports = set()
    for port in problem.ports:
        if isinstance(port, WavePort):
            ports.add("wave")
        elif isinstance(port, LumpedPort):
            ports.add(_PORT_KIND[port.shape])

    junctions = {jj.mode for jj in problem.junctions.values()}
    if _has_unlisted_junction(problem):
        junctions.add("inductor")
    if study.kind == "electrostatic":
        # A capacitance solve leaves every junction open.
        junctions = {"open"} if junctions else set()

    b = problem.boundaries
    boundaries = {_metal_kind(b.metal)} | {_metal_kind(v) for v in b.per_net.values()}
    for wall in b.outer_for(study.kind).values():
        boundaries.add(
            {"pec": "pec", "pmc": "pmc_wall", "absorbing": "absorbing"}.get(
                wall, "open_electrostatic"
            )
        )
    for plane in b.symmetry:
        boundaries.add(f"{plane.kind}_symmetry")

    outputs = set(outputs)
    if b.interfaces:
        outputs.add("surface_epr")
    return Requirements(
        study=study.kind,
        ports=frozenset(ports),
        junctions=frozenset(junctions),
        boundaries=frozenset(boundaries),
        outputs=frozenset(outputs),
    )


# ---------------------------------------------------------------------------
# The comparison table


def _cell(values) -> str:
    return ", ".join(sorted(values)) if values else "—"


def capability_table(fmt: Literal["markdown", "rst"] = "markdown") -> str:
    """The built-in capabilities as a table, one row per backend.

    Args:
        fmt (str): ``"markdown"`` or ``"rst"`` (a list-table).

    Returns:
        str: the table.
    """
    header = [
        "Renderer",
        "Backend",
        "Studies",
        "Through the simulation classes",
        "Ports",
        "Junctions",
        "Boundary conditions",
        "Outputs",
        "Needs",
    ]
    rows = []
    for name in sorted(BUILTIN):
        c = BUILTIN[name]
        rows.append(
            [
                f"``{name}``" if fmt == "rst" else f"`{name}`",
                c.label,
                _cell(c.studies),
                "yes" if c.simulation_classes else ("no" if c.studies else "—"),
                _cell(c.ports),
                _cell(c.junctions),
                _cell(c.boundaries),
                _cell(c.outputs),
                "; ".join(c.requires) or "—",
            ]
        )
    if fmt == "markdown":
        lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
        lines += ["| " + " | ".join(row) + " |" for row in rows]
        return "\n".join(lines)
    if fmt == "rst":
        lines = [".. list-table::", "   :header-rows: 1", ""]
        for row in [header] + rows:
            lines.append("   * - " + row[0])
            lines += [f"     - {cell}" for cell in row[1:]]
        return "\n".join(lines)
    raise ValueError(f"fmt must be 'markdown' or 'rst', got {fmt!r}.")
