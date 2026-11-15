# Quantum Metal — Roadmap

Where Quantum Metal is heading, as of November 2026. Linked issues and pull
requests are the source of truth for whether an item is done; release notes
are in [`changelog.md`](https://github.com/qiskit-community/qiskit-metal/blob/main/changelog.md) and on the
[releases page](https://github.com/qiskit-community/qiskit-metal/releases).
If an item matters to your work, say so on its issue or open a new one: the
order below shifts with user demand and contributor time.

| Status | Meaning |
|---|---|
| `[shipped]` | Released. |
| `[in-progress]` | Active development; a pull request is open or imminent. |
| `[planned]` | Scoped and queued. |
| `[research]` | Direction set, design open. Help wanted. |
| `[needs re-verification]` | Status unclear against the current release. |

---

## Vision

Quantum Metal is an open-source chip-design layer for superconducting quantum
hardware: you build a chip from `QComponent`s, check it, analyze it, and hand
it to the solver, fab flow or orchestrator of your choice. The core stays
**lite by default**: `pip install quantum-metal` imports quickly and assumes
no Qt, Ansys, gmsh or Palace; heavy backends are opt-in extras. The API
should be **scriptable and orchestration-friendly**, so that a script, an
optimizer or an AI agent can generate a design, run design-rule checks,
dispatch it to one or more solvers and iterate, with no GUI prompts and no
hidden state. Analysis should not require a commercial license: open solvers
sit beside Ansys behind one interface. Related open-source projects are
listed in the [ecosystem page](https://github.com/qiskit-community/qiskit-metal/blob/main/docs/ecosystem.rst).

---

## Recently shipped `[shipped]`

**v0.8.0: airbridges and design-rule checking**
- `qiskit_metal.validation.validate(design)` with seven configurable,
  layer- and net-aware rules and `strict=True` as a build gate (#1169);
  tutorial 2.24. `QDesignCheck` is deprecated.
- `Airbridge` component and `route_airbridges` auto-placement (#1138, #1142);
  experimental 3D airbridges with an Elmer capacitance path (#1144, #1150).
- The viewer draws the die outline (#1168).

**v0.8.1: GUI stability**
- Fixes for the GUI crash family (#1048) and interactive canvas editing.
- `TransmonCross` `connector_location='270'` fix; angles wrap mod 360
  (#1173, closes #1052).

**v0.9.0 (September 2026): open-source FEM solver**
- The gmsh + scikit-fem Maxwell solver (`qiskit_metal.analyses.fem`, extra
  `[skfem]`) and tutorials 4.41–4.45, reproducing a published HFSS
  package-mode study.
- First shared solver-backend abstractions in `QGmshRenderer`: ports,
  `group_map`, `mesh_spec`; simulation classes check renderer capabilities.
- Shape rules in the design-rule check (self-intersection, sharp turn,
  fillet starvation, pin alignment; dangling ends opt-in) and waivers.
- Python 3.13 and 3.14; numpy 2; raised dependency minimums.
- New components (`PolylineCPW`, `CapFingerInFrame`, `TransmonStar`), a
  17-qubit surface-code example chip, and every notebook in one tree under
  `docs/`.

**v0.10.0 (November 2026): fixes and docs**
- Python 3.11 is the minimum.
- Fixes for #1202–#1234 and #1242–#1253: transmon, LOM, kappa, chi,
  package-mode and resonator-fit formulas; GDS export; design-rule checks;
  routing; components. Several change numbers or geometry (see the
  changelog).
- New documentation home page and navigation (#1255); tutorial 4.46 on
  multipole qubit–mode coupling.
- `import qiskit_metal` no longer imports `gdstk` or `qutip`.
- The legacy HFSS renderer places junction boundaries along off-axis
  junction lines (#1242), checked in AEDT 2023 R1.1 by the reporter.

---

## Now and next

**Desktop GUI**
- `[in-progress]` macOS teardown crash family (#1048). Three GUI test modules
  are opt-in with `--run-crashy-gui`. A second `MetalGUI` built in one process
  after an application stylesheet is set still segfaults at exit (failure
  mode 1 in `docs/architecture/gui_crash_defenses.md`).
- `[planned]` Lift the `pyside6!=6.12.0` exclusion once a PySide6 release
  fixes the `none_dealloc` abort on Python < 3.12.
- `[planned]` GUI plug-in discovery: the Library pane lists only built-in components (#1178).

**Ansys renderers**
- `[planned]` Validate in AEDT the renderer fixes made in v0.9.0 and v0.10.0
  that are tested only with mocks or stubs (#1242 has been checked in AEDT). Needs a contributor with an
  AEDT license.

**API**
- `[planned]` #1166: give `Vec3D.two_points_described` the same one-argument
  call form as `Vector.two_points_described` by making `user_plane` optional;
  existing calls keep working.
- `[research]` Rename the import path `qiskit_metal` → `quantum_metal` to
  match the PyPI name. No release has been set.

**Tutorials**
- `[planned]` Follow-up notebook 55, which needs the scikit-fem backend to
  read the `QGmshRenderer.group_map` scope.
- `[planned]` Refresh stored outputs that need Qt or Ansys: the flip-chip
  tutorial, the iSWAP full chips, A.4–A.7, 2.21, the LOM 1.0 notebooks after
  #1207 and #1222, and the CR-gate notebook's `MetalGUI` cells.
- `[planned]` An execution harness: run every runnable notebook in a scratch
  copy, grouped by the extras it needs, with a time budget and a report of
  errors and missing outputs. Stored outputs stay the reference answers and
  are refreshed only in separate, reviewed changes.

---

## Research and help wanted

**Solver backends** `[research]`. Goal: an analysis tutorial runs on Ansys,
ElmerFEM, scikit-fem or AWS Palace by changing the renderer name, and each
solver is checked against the others. The design and gap analysis are in
`docs/architecture/solver_backends.md`; the user-facing summary is
`docs/simulation-pathways.rst`.

1. **Shared abstractions in core** `[in-progress]`: ports, mesh-size
   control, named physical groups, boundary conditions, materials from the
   layer stack, net naming and sign convention for capacitance matrices,
   backend-neutral solve setups, and declared capabilities. Ports,
   `group_map`, `mesh_spec` and capability checks shipped in v0.9.0.
2. **scikit-fem and ElmerFEM** on those abstractions: scikit-fem reads its
   geometry from `group_map` and `mesh_spec` and becomes a
   `renderer_name="skfem"` backend for eigenmode and capacitance; ElmerFEM
   gains eigenmodes with lumped junctions, cross-checked against
   scikit-fem. ElmerFEM still hard-codes materials and labels nets
   differently from Q3D.
3. **AWS Palace** as a downstream `quantum-metal-palace` plugin, following
   the RFC in [sqdlab/SQDMetal#67](https://github.com/sqdlab/SQDMetal/issues/67).
   First slice: transmon + launchpad + CPW → gmsh → Palace eigenmode with one
   lumped port, checked against an HFSS reference. Tested locally (MPI).
4. **Ansys HFSS / Q3D**, a separate track gated on AEDT validation: make the
   pyaedt renderers drivable by the simulation classes, fill the Q3D
   capacitance stub and keep mutual-capacitance signs, reconcile the COM and
   pyaedt conventions (voltage-line direction, sample-holder options), and
   move the EPR step to pyEPR's gRPC path (`PyaedtDistributedAnalysis`)
   after checking it covers surface and dielectric loss.
5. **The renderer contract written down**: which calls each solve type
   needs and how capabilities are reported, for every backend.
6. **Testing without losing the stored answers**: reference numbers
   extracted from stored notebook outputs into version-controlled files;
   analytic and tiny scikit-fem checks in CI, larger runs opt-in, ElmerFEM,
   Palace and Ansys local only.

**Open FEM, further out** `[research]`. A gmsh API audit ahead of gmsh 5;
openEMS as a lighter open-FEM option once Palace lands.

**Design-rule checking** `[research]`. More rules (airbridge spacing on long
CPW runs, minimum feature width); per-PDK rule sets loaded from a file;
cross-layer `ground-continuity` that treats an airbridge as connecting two
ground regions. GDS-level DRC stays with KLayout.

**KLayout handoff** `[planned]`. Ship a `.lyp` layer-property file for
exported GDS, a Metal → KLayout how-to, and a starter KLayout DRC deck for
superconducting basics that PDK authors can extend.

**Scriptable and agent-driven use** `[research]`. An orchestration guide (a
design built, checked, exported and analyzed in a short headless script); a
documented stable public API for `QDesign`, `QComponent` and the renderer
bases; deterministic geometry construction so two runs give the same
artifact; vendor-neutral task definitions that let a coding assistant drive
Metal, with DRC as the success signal.

**Architecture** `[research]`. PEP 561 type hints across the core classes;
entry-point discovery for third-party renderers and component libraries
(and a reference PDK package that uses it); a functional component API
beside the class hierarchy; JAX-differentiable parametric components,
starting with `TransmonPocket`.

**In the browser** `[research]`. Bundle the notebooks that need no external
solver into the JupyterLite site (`jupyterlite_contents` in `docs/conf.py`
still points at a missing `tutorials/` folder); a read-only web design
viewer.

### Needs re-verification

Recorded earlier and not checked against v0.10.0:

- Ansys 2025R1 reports #1046 and the AEDT spot-check request #1079.
- Airbridge follow-ups: overlap and off-chip warnings, adjacent-CPW handling.
- LOM 2.0 `TL_RESONATOR` keeps one mode (#1219 docstring); the LOM paper's
  Eq. 13a factor of 2; `Hcpb.nlevels` resetting `Ej`/`Ec`;
  `hamiltonian_results` printing `np.float64(...)` under numpy 2;
  `fit_transmission(detrend=False)` starting from zero cable delay.
- pyEPR packaging: `pywin32` declared only in its `[pyaedt]` extra (a fix in
  pyEPR, not here).

---

## How to help

- **Use it and file issues**, especially for anything that broke off the
  happy path.
- **Bring a solver.** The renderer protocol is in
  [`docs/architecture/renderer_protocol.md`](https://github.com/qiskit-community/qiskit-metal/blob/main/docs/architecture/renderer_protocol.md);
  the backend plan is in
  [`docs/architecture/solver_backends.md`](https://github.com/qiskit-community/qiskit-metal/blob/main/docs/architecture/solver_backends.md).
- **Run Ansys.** With an AEDT license you can validate the renderer fixes
  and the open Ansys issues above.
- **Join the conversation** on [Discord](https://discord.gg/FPNybyfpxd).
