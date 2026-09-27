---
name: chip-design
description: Design a new superconducting quantum chip in Quantum Metal from a specification -- requirements and frequency plan, floorplan, component choice, staged build with a design-rule check after every stage, simulation of a unit cell, iteration, GDS. Also the build and verification rules that keep a CPW layout from failing silently. Use when asked to design, lay out, or iterate on a chip or a variant of one, or to turn target parameters into geometry.
---

# Designing a chip in Quantum Metal

The loop: **specify, plan, lay out in stages, check every stage, simulate a
cell, adjust, repeat.** Geometry comes last and follows from the numbers.
The build and verification rules below come from full-chip builds; each is
here because the opposite went wrong.

## 1. Start from a specification, not a drawing

Write the spec down (a data file the builder reads) before placing
anything, and get the author to confirm it:

- **Function**: qubit count, connectivity graph, which qubits are read out
  and driven, what the chip is for (a code, a gate, a characterization).
- **Targets per element**: qubit frequency and anharmonicity; readout
  frequency, linewidth and dispersive shift; coupling strengths; Purcell
  filtering if any. Leave a number open rather than inventing it -- ask.
- **Constraints**: die size, launchpad count and pitch, fab stack
  (substrate, film, minimum feature and gap, airbridges available or not),
  what the package and fridge wiring allow.

## 2. Plan before geometry

- **Frequency plan first.** Assign qubit and readout frequencies, check for
  collisions (neighbors, readout groups sharing a feedline, harmonics).
  First-pass estimates:
  `qiskit_metal.analyses.hamiltonian.transmon_analytics` (E_J/E_C to
  frequency and anharmonicity), `analyses.em.cpw_calculations`
  (`guided_wavelength` -> resonator length), `analyses.em.kappa_calculation`.
- **Floorplan as boxes.** Place qubits on the connectivity graph, give every
  line a launchpad on a named edge, group readout resonators per feedline,
  and count crossings. Fewer crossings means fewer airbridges; decide here,
  not while routing.
- **Name everything by role** from the start (`LP_flux_Q3`, `RO_Q3`,
  `CPL_Q1_Q2`): the design, the DRC report and the GDS stay readable.

## 3. Choose components

- **Reuse the library first** (`qiskit_metal.qlibrary`); read the class
  docstring and look at the built pins before trusting option names.
  `StarQubit.rotation_*` sits 90 deg ahead of the pin it produces.
- **Routes**: when the length is the design variable (resonators), use a
  router with a length target (`RouteMeander`); when the path is fixed by
  the floorplan, `PolylineCPW` draws the given points. `connect_simple()`
  only makes Manhattan shapes.
- **New component** only when nothing fits; then look at its generated
  thumbnail and docstring, and add it to
  `tests/test_qlibrary_pin_sanity.py`'s explicit list.

## 4. Lay out in stages

One function per stage, driven by the spec file, nothing hard-coded:
die and launchpads, qubits, couplers, control lines, readout, filters,
feedlines, lumped couplers. After **every** stage:

```python
from qiskit_metal.validation import DEFAULT_RULES, SHAPE_RULES, validate
print(validate(design, rules=[*DEFAULT_RULES, *SHAPE_RULES]).report())
```

and render it. Batching stages hides which one broke the design. For a
non-trivial stage, ask a fresh-context subagent to look for defects, not to
confirm.

## 5. Build rules (each one failed silently once)

- **Terminate every line end explicitly.** Path metal and its ground cut
  end flush, so a bare CPW end butts the ground plane and fabricates as a
  short. Capacitive (drive) ends: `OpenToGround`; inductive (flux) ends:
  `ShortToGround`. Convention: `orientation` = the line's outgoing direction
  at that end. Get the physics of each end from the paper or the scheme
  before drawing it.
- **Register every intended joint** with `design.connect_pins`. A branch off
  the middle of a line: give the line a **tap**
  (`PolylineCPW(..., taps={name: [x, y]})`) and connect to it -- not a waiver.
- **Crossings**: interrupt the upper line, span the gap with an `Airbridge`
  (own layer), and connect the cut ends to its pins `a`/`b`. An unwired
  bridge is a broken line with two shorted stumps. Name bridges after the
  line, so a line drawn in two calls does not overwrite its own bridges.
- **Fillets**: the path fillet is clamped to half the shortest segment, so
  one short segment starves every corner. Keep `min_segment` above the
  shortest chord and `fillet` <= half of it.
- **Dimensions below what you can justify**: use the standard (e.g. 50 ohm
  on the substrate) and say so in the code.
- **Waivers** only for genuine exceptions: exact component pair,
  `max_value`, and the reason.

## 6. Verify the built geometry, not your intent

- Assert on drawn qgeometry (`design.qgeometry.tables['path']`) and on built
  pin positions and normals, not on `options`.
- `SHAPE_RULES` includes `pin-alignment`: every line must leave the pin it
  connects to square-on. Start lines with a short straight lead along the pin
  (40 um worked) rather than aiming straight at the next waypoint.
- Write each check as the property you need. "Open end touches the feedline"
  passed *because* every end had run onto the feedline -- the defect it was
  meant to catch. The property was "open end is >= 15 um away".
- `design.rebuild()` must leave DRC unchanged. If it does not, look at
  `design.net_info` first.
- Prove a diagnosis (compare old vs new geometry) before writing it down.
- A check that stops firing after a change that should not have fixed it
  is suspect: nanometer boolean slivers once joined ground islands and hid
  a real warning.
- Verify the GDS itself after export (every line's gap is cut, no dropped
  holes), not only the design.

## 7. Simulate a cell, then iterate

- Cut out a representative cell (a qubit with its readout, or two coupled
  qubits) rather than meshing the chip.
- **Capacitance / LOM**: Ansys Q3D, or the open-source ElmerFEM path
  (`renderer_elmer`, tutorial `docs/tut/4-Analysis/4.19-Analyze-a-transmon-using-ElmerFEM.ipynb`);
  LOM analysis turns the matrix into frequencies and couplings
  (`docs/tut/4-Analysis/4.0*`). **Eigenmode / EPR / couplings**: Ansys HFSS,
  or the open-source gmsh + scikit-fem solver of tutorials 4.43–4.45
  (`docs/tut/resources/package_modes/`).
- Validation, mesh convergence, symmetry, junctions as lumped elements and
  the choice of coupling-extraction method: `.claude/skills/chip-simulation/SKILL.md`.
- Sweep the few dimensions that set each target
  (`analyses.sweep_and_optimize`), update the spec, rebuild, re-check.
- Say which numbers were simulated and which are analytic estimates.

## 8. Deliver

GDS export (`design.renderers.gds.export_to_gds`), a DRC report with any
waivers and their reasons, and the spec file that produced it.

## Where the rest lives

- `.claude/skills/chip-layout-from-images/SKILL.md` -- reproducing a
  published device from images (measurement, conformance to the source).
- Worked full-chip build with a stage-by-stage DRC:
  `docs/circuit-examples/F.Small-quantum-chips/53-Wallraff_17Qubit_SurfaceCode.ipynb`
  (builder and data in `resources/wallraff_17q/`).
- New-design examples: `docs/tut/1-Overview/1.3-Build-a-4-qubit-chip.ipynb`,
  `docs/tut/full-design-examples/`, `docs/circuit-examples/full-design-flow-examples/`.
- `qiskit_metal.validation` -- `validate`, `Waiver`, `SHAPE_RULES`.
- `.claude/skills/chip-simulation/SKILL.md` -- simulating a cell or array and extracting parameters.
- `.claude/context/lessons-learned.md` -- component-authoring traps.
