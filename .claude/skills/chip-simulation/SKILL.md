---
name: chip-simulation
description: Simulate a Quantum Metal design (a cell, an array, a package) and extract Hamiltonian parameters -- mode frequencies, capacitances, qubit-qubit and qubit-mode couplings -- with Ansys, ElmerFEM or the open-source gmsh + scikit-fem solver. Choosing the solver and the extraction method, validating against analytic cases, mesh seeding and convergence, symmetry reduction, junctions as lumped elements, comparing methods fairly, and reproducing a published analysis. Use when asked to simulate, analyze, extract g / chi / EPR / capacitance, check a design against targets, or reproduce a paper's numbers.
---

# Simulating a design and extracting its parameters

The loop: **validate the solver on a case with a known answer, mesh where
the physics is, converge the quantity you report, cross-check with a second
method.** A frequency that agrees with the paper says little about a
coupling computed on the same mesh. Every rule below is here because the
opposite went wrong (tutorials 4.41–4.45, `docs/tut/4-Analysis/4.4*`).

## 1. Pick the solver for the question

| Question | Tool |
|---|---|
| capacitance matrix, LOM | Ansys Q3D; ElmerFEM (`renderer_elmer`, tutorials 4.19, A.4); P1/P2 electrostatics (`qiskit_metal.analyses.fem.Electrostatics`) |
| eigenmodes, EPR, junction-mode couplings | Ansys HFSS (`renderer_ansys*`); gmsh + scikit-fem (`qiskit_metal.analyses.fem.MaxwellFEM`, lowest-order edge elements, junction = lumped inductor) |
| impedance / S-parameters at ports | HFSS driven; `qiskit_metal.analyses.fem.PortROM.impedance` (lumped line ports) |
| first estimates | analytic: `analyses.hamiltonian.transmon_analytics`, `analyses.em.cpw_calculations`; closed-form cavity modes |

The scikit-fem path runs anywhere `pip` does, in minutes for ~10^5–10^6
unknowns, and every matrix is in your hands (rank-one junctions, reduced
models, custom ports). Its limits: lowest-order elements, zero-thickness
metal, no ground-plane cutouts or CPWs in the mesher yet, single process.
Details: `docs/architecture/open_fem_scikit_fem.md`. The user-facing
summary of all paths (what each computes, how to install it, which
tutorials use it) is `docs/simulation-pathways.rst`. AWS Palace is reachable
through SQDMetal today; a native `renderer_name="palace"` path is being
designed (RFC: sqdlab/SQDMetal#67). Backends differ in what they support:
check a backend's capabilities before assuming a solve type, port or
boundary condition carries over (ROADMAP "Solver backends", stage 1).

## 2. Validate the solver before the device

Build up the model and check each step against something known:

1. **Empty geometry vs closed form** (a rectangular box: TM110 at
   `c/2 sqrt(1/Lx^2 + 1/Ly^2)`).
2. **Add one ingredient** (a dielectric slab: the LSM transcendental
   equation) — agreement to ~0.1% says units, materials and boundary
   conditions are right.
3. **Circuit limit**: the extraction formulas on a lumped circuit whose
   answer is exact (tutorial 4.42) before they meet a mesh.
4. **Reduced models vs direct solves**: a Krylov/port reduced model must
   reproduce a direct eigen solve (frequency and port voltages) before you
   trust sweeps done on it.

## 3. Mesh where the physics is, and converge what you report

- Seed finely at metal edges and junction gaps (charge crowds on edges;
  couplings are read in the gap); leave the bulk coarse (a package mode
  varies over centimeters). A sphere of fine seeding around each junction
  moves a junction voltage as much as refining every metal edge, with far
  fewer unknowns.
- **Frequencies converge long before couplings.** The package frequency
  was right to 0.1% on a mesh whose couplings were still 4% low. Run a
  convergence table (3–4 meshes) of the reported quantity itself.
- **Sheet-metal edges converge slowly** with lowest-order elements
  (capacitance 230 fF at 0.1 mm vs 174 fF converged). Use second-order
  electrostatics for capacitances.
- Know the cost before launching: record unknowns, time and peak memory
  per mesh; a full 30 mm package with 100 qubits at 0.1 mm edges was ~450k
  unknowns, ~40 s, ~8 GB.

## 4. Use symmetry, and know when you cannot

- A geometry symmetric under a mirror has modes that are even or odd under
  it. Model a half or a quarter with a **PMC** cut (field tangential to the
  plane; in the edge-element formulation, leave the face alone) or a **PEC**
  cut (field normal; remove its edges). Choosing the cut conditions selects
  the mode family — it also separates degenerate modes (LSM210 vs LSM120 in
  a square box) without distorting the geometry.
- Report energies for the whole package (`n_sym` × the region), and unfold
  results with the right parity: across a PMC plane tangential **E** is even
  and normal **E** odd; across PEC the reverse.
- **A junction inductor on one qubit breaks the symmetry.** In a reduced
  model it acts on every mirror image at once: N images form one bright
  qubit with coupling `sqrt(N) g`. Mesh the full structure for single-qubit
  perturbations (avoided crossing, EPR, impedance per qubit).

## 5. Junctions and ports

- Replace the junction by what the method needs: open (induced EMF),
  lumped inductor (EPR, avoided crossing), lumped port (impedance).
- In an edge-element model a lumped element across a junction is a
  rank-one term on the edges of the junction line: sweeping its inductance
  needs no new factorization. Build a reduced model at the ports once
  (block Krylov, moment matching) and answer every termination from it.
- **A shunted probe port is metal.** A probe shorted to ground by a small
  inductance is a post; keep it away from the qubits you compare (a post
  1.8 mm from a weakly coupled qubit changed its coupling by 100%).

## 6. Coupling extraction: what each method gives

| Method | Needs | Gives |
|---|---|---|
| avoided crossing | a sweep of the junction inductance per qubit | `|g|` only |
| energy participation | one eigen solve per qubit, detuned | `g` with sign; low by `sqrt(L_J / (L_J + L_geometric))` if only the junction's energy is counted |
| induced EMF | **one** eigen solve with all junctions open + each qubit's capacitance | `g` with sign, all qubits at once — cheapest for arrays |
| impedance fit | a driven sweep per qubit and a pole–residue fit | `g`; the split into `g_C` and `g_L` is port-dependent, not physical |

- **Compare methods on one discrete model.** An edge-element model's static
  fields are first-order electrostatics on the same mesh, so its qubits
  carry the P1 capacitance. The induced-EMF formula must then use
  `Electrostatics(mesh, order=1)` to agree with the other three; use P2 for
  absolute values. **Agreement between methods is not convergence.**
- **Impedance fits:** a weakly coupled pole sits within a kHz of a zero;
  a uniform 0.1 MHz grid misses it. Sample adaptively around the poles
  (a reduced model gives them), never exactly on one.
- Fix sign conventions explicitly (eigenvector sign, voltage direction
  along the junction) — relative signs between qubits are physical, the
  overall sign is not.
- Normalize consistently: peak amplitudes, `E_m = (1/2) int eps |E|^2`
  as the total mode energy, 1 J by convention.

## 7. Reproducing a published analysis

- Read the whole paper first; put every geometric parameter and every
  reported number into a data structure (`DEVICE`, `PAPER`) and print
  "ours vs paper" next to each result.
- Reproduce figure by figure, cheapest first: analytic results, then the
  circuit model, then full-wave.
- Transcribe equations with their signs and conventions; check each
  against a limit. (Eq. E9 of the reproduced paper carries a minus sign
  that the quoted value drops.)
- When a number disagrees and refinement does not move it, report it with
  both values and what you checked — do not tune toward the paper, and do
  not "fix" the paper. Tell the authors, if they are in the loop.
- Credit the paper in every notebook and in the data module.

## 8. Testing solvers

- **The stored outputs of solver notebooks are reference answers** — often
  the only record of an Ansys, ElmerFEM or long run. Never re-execute them in
  place to "refresh"; run into a scratch copy and compare. Extract the key
  numbers into reference files with a tolerance and their provenance.
- **Tier the tests by cost**: seconds and no external binaries on every CI
  run (analytic cases, a tiny mesh); minutes behind an opt-in marker;
  external binaries, MPI, licenses and large meshes local only. Give every
  solver test a time and memory budget and a skip when the solver is absent.
  Policy: `ROADMAP.md`, "Solver backends", "Testing solvers".

## 9. Report

Say for each number which mesh, which method and which capacitance it came
from, and whether it is converged or a consistency check. Keep the
convergence table in the deliverable.

## Where the rest lives

- `docs/tut/4-Analysis/4.41`–`4.45` — worked example: package modes of a
  10 × 10 transmon array, four extraction methods, Figs. 5–9 of
  arXiv:2609.22442.
- `docs/architecture/open_fem_scikit_fem.md` — the scikit-fem solver:
  conventions, validation record, limitations, extension path.
- `.claude/context/lessons-learned.md`, "Open FEM: gmsh + scikit-fem" —
  gmsh speed, point location, ARPACK, orderings, fit sampling.
- `.claude/skills/chip-design/SKILL.md` — design and build rules; section 7
  hands off to this skill.
- `.claude/skills/tutorial-notebook/SKILL.md` — turning an analysis into a
  tutorial.
