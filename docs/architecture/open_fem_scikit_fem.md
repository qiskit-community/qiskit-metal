# Open-source Maxwell solver: gmsh + scikit-fem

Design notes, validation record and extension path for the finite-element
solver in `docs/tut/resources/package_modes/package_modes.py`, written for
tutorials 4.41–4.45 (a reproduction of R. Molavi *et al.*,
arXiv:2609.22442). Read this before reusing the solver elsewhere or turning
it into a backend (see `ROADMAP.md`, "Solver backends").

## What it does

| Capability | Entry point | Method |
|---|---|---|
| Geometry from a Metal design | `package_from_design(design)` | chip outline → box; layer stack → substrate thickness; `sample_holder_*` variables → lid height; non-subtracted polys → metal sheets; `junction` table → port lines |
| Mesh | `mesh_package(package, region, h_metal, h_max, h_junction=None, probe=None)` | gmsh OCC: two boxes (substrate, vacuum), metal as zero-thickness surfaces, junctions and an optional vertical probe as embedded lines, all `fragment`ed; size field by distance from metal edges (and optionally a finer sphere around each junction) |
| Eigenmodes | `MaxwellFEM(mesh, cuts).eigenmodes(f, n, inductors)` | curl-curl on lowest-order Nédélec tetrahedra; shift-invert ARPACK on one sparse LU |
| Lumped junctions / ports | `inductors={name: L}` | rank-one term `(mu0 1e-3 / L) c c^T`, `c` = signed edge chain of the port line |
| Many junction terminations, impedance matrices | `PortROM(fem, ports, f_center, n_moments)` | block Krylov space from the port vectors, Galerkin projection; eigenmodes with any inductors and `Z(f)` on any grid from small dense matrices |
| Capacitance matrix, charges, dipole | `Electrostatics(mesh, order=1|2)` | Lagrange P1/P2; each conductor collapsed to one unknown; capacitance = Schur complement onto conductor unknowns (one LU) |
| Fields anywhere | `Mode.field(points)`, `Electrostatics.potential(...)` | KD-tree over element centroids + barycentric coordinates; Whitney (N0) or P2 shape functions evaluated directly |
| Analytic references | `lsm_mode`, `circuit_couplings`, `circuit_impedance`, `fit_impedance` | Appendix E LSM modes; two-mode circuit; Appendix D pole–residue fit |

Dependencies: `gmsh`, `scikit-fem`, SciPy; `pymetis` optional (nested
dissection ordering; without it SuperLU uses `MMD_AT_PLUS_A`, several times
more fill). No MPI, no external binaries.

## Conventions

- Lengths in mm inside mesh and solver; SI elsewhere.
- A Nédélec degree of freedom is the line integral of **E** along a mesh edge,
  from its lower-numbered to its higher-numbered node, in volts. A port
  voltage is `c . u`; **E** in V/m is `1e3` times the interpolated field.
- Weak form (mm units): `int curl E . curl F + sum_p (mu0 1e-3 / L_p) V_p(E) V_p(F) = k0^2 int eps_r E . F`.
- Mode energy (J) = `n_sym * 0.5 * eps0 * 1e-3 * u^T M u` (peak amplitude, so
  this is the total energy); `n_sym` = 1, 2, 4 for full, half, quarter.
- Impedance: `Z = j w mu0 1e-3 c_q^T (A - k0^2 M)^-1 c_p` (engineering `j`).
- Eigenvector sign: `MaxwellFEM` makes `E_z > 0` near the region's inner
  corner; `PortROM.eigenmodes` makes each mode's largest port voltage
  positive.
- Metal and walls: tangential **E** = 0, so their edges are removed. A cut
  face of a symmetry-reduced mesh is PMC (natural condition, nothing to do) or
  PEC (edges removed). Unfolding junction voltages across a cut:
  `pm.mirror_signs(cuts)`.

## Validation record (tutorial runs, September 2026)

| Quantity | Solver | Reference |
|---|---|---|
| empty 30×30×3 mm box, TM110 | 7.065 GHz | 7.066 GHz analytic |
| with 0.5 mm Si, LSM110 | 6.487 GHz (h_max 0.8 mm) | 6.493 GHz analytic, 6.49 GHz paper |
| qubit capacitance (P2) | 173.4–174.3 fF | 173.8 fF (paper fit) |
| EMF coupling amplitude A/2π | 15.63 MHz (quarter, h_metal 0.05 mm) | 15.6 MHz (paper) |
| LSM210 amplitude | 51.6 MHz | 49.8 MHz (paper) |
| four methods, 25 qubits, one mesh | max spread 4.1 %, mean 3.8 % | 4.8 %, 2.9 % (paper) |
| two-mode circuit, Appendix D fit | exact (rms 1e-13) | paper values of qubit (0,0) |
| PortROM vs direct solves | frequencies to 1e-6 GHz, Z to 5 digits | — |
| field evaluator vs `skfem` interpolator | 1e-16 relative | — |

Costs, measured on a laptop: quarter box, 0.1 mm paddle edges: ~110k
unknowns, ~7 s; full 10×10 box, 0.1 mm: ~450k unknowns, ~40 s, ~8 GB peak;
full box port ROM, 26 ports × 4 moments: ~35–70 s.

## Physics and numerics to know before reusing it

- **The Maxwell model's qubit capacitance is first-order electrostatics on
  the same mesh.** N0 edge elements contain the gradients of P1 nodal
  functions exactly, so the static (charge) part of any mode is P1
  electrostatics. On a 0.1 mm mesh with zero-thickness paddles that is
  ~230 fF against a converged 174 fF (sheet-edge singularities converge
  slowly). Consequences: (a) a qubit with junction inductance `L` sits lower
  than `1/sqrt(L C_P2)`; (b) when comparing methods on one mesh, use
  `Electrostatics(mesh, order=1)` for the induced-EMF capacitance;
  (c) for absolute couplings, P2 capacitance with the N0 junction voltage
  converges faster than either alone (4.44).
- **Energy participation runs low by `sqrt(L_J / (L_J + dL))`** when only the
  junction's energy is counted (Eq. 8 assumes no geometric inductance).
  Measured 3.7 %, predicted 3.6 % from the fitted `dL`. Exact on the circuit
  when the whole branch is counted (4.42).
- **Zero-frequency null space.** With junctions open, each floating paddle
  pair contributes static modes at `k0 = 0`. Ask ARPACK for few eigenvalues
  near the shift; requesting more than exist near it makes it chase the
  degenerate cluster (100× slower).
- **Impedance fit sampling.** A port shunted by a small inductance barely
  sees a mode: its pole and the adjacent zero can fall inside one 0.1 MHz
  step. Sample adaptively around the poles (the ROM gives them) and never
  exactly on one. A local probe shunted to ground is a post: keep it away
  from the qubits being compared.
- **Eq. (E9) of the paper carries a minus sign**; the paper quotes `|E0,x|`.
  `LSMMode.E0x` is the magnitude, `Ex_surface` applies the sign.
- **Dipole moment.** Electrostatic `p_x` gives a dipole length of 0.64 mm
  (stable under refinement) against 0.58 mm quoted from an HFSS
  surface-current integral; the dipole estimate with 0.64 mm gives
  A ≈ 15.7 MHz.

Tooling pitfalls (gmsh size-field speed, point location, mesh slices,
empty fragment maps) are in `.claude/context/lessons-learned.md`, section
"Open FEM: gmsh + scikit-fem".

## Limitations

- Lowest-order elements only (scikit-fem ships `ElementTetN0`); no curved or
  second-order Nédélec elements.
- Metal is zero-thickness; the mesher reads non-subtracted polygons and
  junction lines. No ground plane with cutouts, no CPW gaps, no wirebonds,
  no finite-thickness metal.
- Lossless: no dielectric loss, radiation boundaries or wave ports; ports are
  lumped lines.
- Single-process sparse direct solves; memory grows quickly beyond ~1M
  unknowns.

## Extension path (reusable backend)

The staged plan and the testing policy are in `ROADMAP.md`, "Solver
backends: shared abstractions, then scikit-fem, ElmerFEM, Palace and Ansys".
Stage 1 there (ports, mesh-size control, named physical groups, boundary
conditions, net naming, capability declarations in core) lands before this
solver moves. The Palace RFC in
[sqdlab/SQDMetal#67](https://github.com/sqdlab/SQDMetal/issues/67) proposes
the same kind of seams. For this solver:

1. **Geometry through the core abstractions**: take the tagged mesh from
   `QGmshRenderer` once it returns a structured physical-group map, ports,
   per-region mesh fields and symmetry faces (stage 1), instead of the
   tutorial's own mesher; this also brings ground planes with
   cutouts and CPW paths. `mesh_package` shows what the tags must carry:
   metal surfaces, junction lines as edge chains, probe lines, cut faces.
2. **Solver code**: move `MaxwellFEM`, `PortROM`, `Electrostatics` and
   `_Locator` into `src/qiskit_metal/analyses/` behind an optional extra
   (`scikit-fem`, optional `pymetis`). Keep `package_modes.py` as a thin
   wrapper so the tutorials keep running unchanged.
3. **Renderer front door**: a `renderer_name="skfem"` renderer on the same
   seam as Elmer and Palace, implementing the eigenmode and capacitance
   flows of the simulation classes; the port reduced-order model and the
   four coupling methods stay available as direct calls.
4. **Tests**, tiered as in the ROADMAP: tier 0 (CI) — analytic box and LSM
   modes, the two-mode circuit and Appendix D fit, an empty box on a coarse
   mesh; tier 1 (opt-in) — small-mesh versions of the 4.4x problems against
   reference values extracted from the stored notebook outputs
   (`tests/solver_references/`); tier 2 (local only) — full-size runs.
   Never regenerate the stored notebook outputs from a test.
5. **Cross-checks**: capacitance against the ElmerFEM notebooks (4.19, A.4)
   and the stored Q3D outputs; eigenmodes against stored HFSS outputs and,
   once available, Elmer and Palace on the same tagged problem.
6. **Integration**: let `EigenmodeSim` / `LumpedElementsSim` accept the
   backend next to `renderer_name`.
7. **Accuracy**: second-order edge elements (a custom element in scikit-fem
   or another assembler) would remove most of the paddle-edge capacitance
   error.
