# Solver backends: shared abstractions (stage 1 design)

Status: design, with decisions D1 and D3–D6 taken and D2 (Palace packaging)
open (section 8). Steps 1.0 and 1.1 are done; the later steps are not
implemented yet. This note covers
stage 1 of `ROADMAP.md`, "Solver backends: shared abstractions, then
scikit-fem, ElmerFEM, Palace and Ansys". It has four parts: a gap analysis
(section 2), the proposed abstractions (section 3), how each backend would
read them (section 4), and Palace packaging, the implementation sequence and
the open decisions (sections 5–8). Related notes:
`docs/architecture/renderer_protocol.md`,
`docs/architecture/open_fem_scikit_fem.md` and `docs/simulation-pathways.rst`.
The Palace RFC is
[sqdlab/SQDMetal#67](https://github.com/sqdlab/SQDMetal/issues/67).

## 1. The problem

The analysis tutorials call three simulation classes: `EigenmodeSim`,
`LumpedElementsSim` and `ScatteringImpedanceSim`. `LOManalysis` and
`EPRanalysis` read their results. The simulation classes reach a solver by
renderer name. Before any solver runs, it has to be told these facts about
the device:

- where current enters or leaves: ports, and junctions modeled as lumped
  elements;
- which metal surfaces form one conductor;
- what the outer walls of the model are;
- what fills each volume;
- where the mesh must be fine.

Today each backend gets these facts differently:

- **Ansys renderers:** the facts are encoded in the call arguments, for
  example `port_list=[("Q1", "a", 50)]` and `open_terminations`.
- **Gmsh + ElmerFEM:** the renderer infers them from name suffixes and
  hard-codes a material list.
- **scikit-fem:** the tutorial module (tutorials 4.41–4.45) builds its own
  mesh and passes junctions as edge chains.
- **Palace:** Metal has no path. SQDMetal and pyPalace take a Metal design
  and derive the facts themselves, each from its own reading of the qgeometry
  tables.

Stage 1 moves these facts into one solver-neutral description in Metal core.
Each backend then declares which parts of that description it can honor.

Sources read for this note:

| Source | Version | Short name used below |
|---|---|---|
| Quantum Metal | `c181d449a` | paths from the repo root |
| SQDMetal | `7ea4d003` (2026-08-27) | `SQD/`, i.e. the repo's `SQDMetal/` package directory |
| pyPalace (pypalace 0.1.3) | `0859ed7a` (2026-08-25) | `pyP/`, i.e. `pypalace/` |
| Palace docs and config schema | `ce564d3` (2026-09-25) | `Palace:` |

## 2. Gap analysis

### 2.1 How each system reaches a solver today

- **Ansys, COM track** (`renderer_ansys/`, renderer names `hfss` and `q3d`).
  - This is the only track that satisfies the informal contract the
    simulation classes call. The contract is listed in section 2.10.
  - Metal is drawn as zero-thickness sheets with perfect-E (HFSS) or
    thin-conductor (Q3D) boundaries.
  - It reads `design.chips[...]`, not the layer stack.
- **Ansys, pyaedt track** (`renderer_ansys_pyaedt/`, `aedt_hfss`, `aedt_q3d`).
  - It uses a different API from the COM track. Missing methods include
    `execute_design`, `initialize_*`, `get_convergences`, `set_mode` and the
    `epr_*` methods, so the simulation classes cannot drive it.
  - It reads the `MultiPlanar` layer stack and draws metal as 3D `pec`
    solids.
  - Users call it directly, as in `docs/tut/4-Analysis/pyaedt-multiplanar/`.
- **Gmsh** (`QGmshRenderer`, an export-only `QRenderer`).
  - It builds an OpenCASCADE model from the qgeometry tables and the
    `MultiPlanar` layer stack:
    - extruded metal, ground planes with cutouts, the dielectric, a vacuum
      box, and junctions as rectangles;
    - fragmented at shared interfaces;
    - named physical groups.
  - It then meshes the model with distance-based size fields.
- **ElmerFEM** (`QElmerRenderer`, a `QRendererAnalysis`).
  - It composes `QGmshRenderer` and assigns galvanic nets from shapely
    geometry and pin connectivity.
  - It writes an Elmer input file and returns a Maxwell capacitance matrix.
  - It is used directly (tutorial 4.19), not through `LumpedElementsSim`.
- **scikit-fem** (`docs/tut/resources/package_modes/package_modes.py`).
  - It is a resource module with its own mesher: zero-thickness metal
    sheets, and junctions as embedded lines.
  - Its solvers are Nédélec eigenmodes, a port reduced-order model and P1/P2
    electrostatics.
  - It has no renderer and no ground-plane cutouts.
- **SQDMetal** (`SQD/PALACE/`).
  - It takes a `QDesign` through `metal_design=` (`SQD/PALACE/Model.py:176-180`).
  - It renders qgeometry to shapely through a `QMplRenderer` subclass
    (`SQD/Utilities/QiskitShapelyRenderer.py:13-39`), so path fillets and
    buffering come from Metal.
  - Its own gmsh builder then produces the model
    (`SQD/PALACE/Utilities/GMSH_Geometry_Builder.py:31-383`).
  - It writes Palace JSON and runs Palace locally, under WSL or in an
    Apptainer container.
- **pyPalace** (`pyP/`).
  - `mesh_Quantum_Metal_design(design, output_mesh, Attributes=...)`
    (`pyP/meshing.py:1544-2162`) reads the `poly` and `path` tables and places
    all metal at z = 0.
  - The user maps qgeometry rows to integer tags. There is no connectivity
    analysis.
  - A config builder mirrors Palace's JSON one-to-one (`pyP/config.py`,
    `pyP/builder.py`).
  - Result readers and small EPR and LOM helpers are in `pyP/simulation.py`
    and `pyP/analysis.py`.

### 2.2 Ports and junctions

| System | What it has | Where |
|---|---|---|
| Metal core | Pins carry `middle`, `normal`, `tangent`, `width`, `gap`; `design.net_info` records pin connections. The `junction` table stores a two-point LineString plus `width`, which gives both a sheet (rectangle) and an integration line. Renderers can add per-junction columns (`<renderer>_inductance`, `_capacitance`, `_resistance`, `_mesh_kw_jj`) through `element_table_data`. There is no port object. | `renderers/renderer_base/renderer_base.py:67-136`, `designs/design_base.py:292` |
| Simulation classes | Tuple arguments: `open_terminations=[(comp, pin)]`, `port_list=[(comp, pin, Z0)]`, `jj_to_port=[(comp, jj, Z0, draw_ind)]`, `ignored_jjs=[(comp, jj)]` | `analyses/simulation/eigenmode.py:82-143`, `scattering_impedance.py` `run_sim` |
| Gmsh | Open pins become endcap cutouts (axis-aligned pins only, `gmsh_renderer.py:678-693`). Junctions become 2D rectangles at mid-thickness of the metal layer, named `{comp}_{jj}` (`:466-512`). No ports. | `renderer_gmsh/gmsh_renderer.py` |
| Ansys COM | `port_list` gives a sheet from pin `middle` to `middle + gap·normal`: a lumped port (driven) or a resistive RLC boundary (eigenmode). Pins must be axis-aligned and z is hard-coded to 0. A junction becomes an RLC boundary (L, C, R from `hfss_*` columns) plus an integration line. `jj_to_port` with `draw_ind` splits the rectangle into a port half and an inductor half. No wave ports. | `renderer_ansys/hfss_renderer.py:90-448` |
| Ansys pyaedt | Ports in driven modal only; the eigenmode renderer rejects `port_list` and `jj_to_port` (`hfss_renderer_eigenmode_aedt.py:251-256`). `jj_to_port` is a 3-tuple. The integration line follows the pin normal (COM uses the rectangle axis). | `renderer_ansys_pyaedt/` |
| scikit-fem | A port is an embedded line, stored as the signed edge chain of a junction or probe. A lumped inductor is a rank-one term on that chain. | `package_modes.py:1089-1260`, `:1332-1448` |
| SQDMetal | Two-pin rectangle; junction port (R, L, C; L from E_J); two-element CPW port (±Direction) on a launcher, a route pin or an edge point; wave port on an airbox face; U-clip feed; surface-current source. Emitted as `LumpedPort` / `WavePort` with arbitrary `Direction` vectors. An axis-alignment check exists but is not called (`GMSH_Geometry_Builder.py:702-717`). | `SQD/PALACE/Model.py:1199-1716` |
| pyPalace | No port builder. The user adds port rectangles as extra Metal polys and gives `Direction` in the config. | `pyP/meshing.py`, `pyP/builder.py:129-340` |

**Gap.**

- Metal has the geometry every port needs (pin frames, junction lines and
  widths) but no port object.
- Each backend re-derives ports from tuples or from its own geometry.
- Three different port shapes are in use:
  - a sheet (Ansys, Palace);
  - a line, i.e. an edge chain (scikit-fem);
  - two sheets across a CPW's gaps (SQDMetal).
- Two different integration-line conventions are in use (COM versus pyaedt).
- Every Metal-side port and endcap path assumes pins lie along x or y.

### 2.3 Mesh-size control

| System | What it has | Where |
|---|---|---|
| Gmsh | Global `min_size`/`max_size`. One Distance field on all metal curves feeds a graded stack of Threshold fields. There is a `max_size_jj` option and a `custom_mesh_fn` escape hatch. **Until step 1.0 the junction field was built empty.** It collected curves from every metal surface and wrote them to the metal-edge field, so `max_size_jj` had no effect. Building a `TransmonPocket` model and listing the fields showed a junction Distance field with 0 curves. | `gmsh_renderer.py:1095-1193` |
| Ansys COM | Length-based mesh operations on junction rectangles (`max_mesh_length_jj`, default 7 µm) and on eigenmode port sheets (`max_mesh_length_port`). The `<renderer>_mesh_kw_jj` column is written but never read. Adaptive passes are controlled by the setup. | `renderer_ansys/ansys_renderer.py:153-154, 1660-1679` |
| Ansys pyaedt | `add_mesh` is empty. | `hfss_renderer_eigenmode_aedt.py:281`, `hfss_renderer_drivenmodal_aedt.py:682` |
| scikit-fem | `h_metal` along metal edges, `h_max` in the bulk, `grow` distance, and an optional `h_junction` ball of radius `r_junction` around each junction. | `package_modes.py:705-760` |
| SQDMetal | Region specs `{box, path, component outline, sliver features} × {min, max, dist_min, dist_max}` compiled to Distance+Threshold+Min. Palace adaptive refinement (`Model.Refinement`: `Tol`, `MaxIts`, `MaxSize`, `UpdateFraction`, `Nonconformal`) is available. | `SQD/PALACE/Model.py:657-848, 1035-1080`, `SQD/PALACE/Utilities/GMSH_Mesh_Builder.py:14-66` |
| pyPalace | One Distance→Threshold pair per distinct surface size, plus per-surface overrides. It exposes Palace's `Model.Refinement` (boxes, spheres). | `pyP/meshing.py:2062-2117`, `pyP/builder.py:26-48` |

**Gap.**

- All four mesh builders use the same recipe: a distance to a set of
  entities, a size threshold, and a minimum over fields.
- None of them lets the caller name the target by physical role ("junction
  gaps", "port sheets", "conductor Q1 edges").
- Metal's one junction-specific control was broken (now fixed; step 1.0).
- Adaptive refinement exists in two backends (HFSS passes, Palace
  error-indicator refinement), and the two use different stopping criteria.

### 2.4 Named physical groups

What `QGmshRenderer` produces today, for a `TransmonPocket` connected by a
CPW route to an `OpenToGround`, under the default layer stack:

```
layer 1:  Q1_pad_top, Q1_pad_top_sfs, Q1_pad_bot, ..., Q1_a_wire, cpw_trace,
          Q1_rect_jj (2D), ground_plane_(layer 1), ground_plane_(layer 1)_sfs
layer 3:  dielectric_(layer 3), dielectric_(layer 3)_sfs
global:   vacuum_box, vacuum_box_sfs
```

| System | What it has | Where |
|---|---|---|
| Gmsh | `physical_groups[layer][name] -> tag`. Names are `{comp}_{geom}` for volumes, `_sfs` for their surfaces, and `ground_plane_(layer N)` / `dielectric_(layer N)` for layers. The vacuum box is one volume and one group for all six faces. Nothing is tagged as a port, an outer face per side, a net or a symmetry face. | `gmsh_renderer.py:963-1084` |
| ElmerFEM | Consumers match substrings (`"dielectric" in k`, `"_sfs" in name`, `"ground_plane" in name`) and rebuild `{comp}_{geom}_sfs` keys from its own net lists. | `renderer_elmer/elmer_renderer.py:585-679` |
| SQDMetal | Integer tags returned in a structured dict (`metals`, `contiguous_metal_mapping`, `far_field{x_neg..z_pos}`, `ports`, `dielectric`, `dielectric_gaps`). Group names are `metal_{m}`, `gap_{m}`, `rf_port_N[a/b]`, `rf_wport_N`, `x_neg…z_pos`, `air_box`, `dielectric_substrate`. | `GMSH_Geometry_Builder.py:319-383` |
| pyPalace | Reserved names `substrate`, `air`, `ground_plane`, `far_field`, plus user rows by name or `(component, name)`. Palace itself uses integer attributes only. The name parser drops names containing spaces. | `pyP/meshing.py:1762-1770, 2021-2058`, `:120-131` |
| Palace | Domains and boundaries are selected by integer attribute. Names are not used. | Palace: `docs/src/guide/model.md` |

**Gap.**

- Metal has names but no roles.
- A consumer cannot ask for "the surfaces of net 3", "the port sheets", "the
  `x+` wall" or "the dielectric volumes and their materials" without parsing
  strings.
- Metal's layer group names contain spaces and parentheses, which some
  external readers drop.

### 2.5 Nets, capacitance naming and sign convention

| System | Conductor identity and naming | Matrix convention | Where |
|---|---|---|---|
| Q3D (COM) | `AutoIdentifyNets` in AEDT. Objects are named `{geom}_{component}` and the ground is `ground_{chip}_plane`. In the stored output of tutorial 4.01, each net carries a member object's name (`pad_top_Q1`, `ground_main_plane`). | Maxwell, fF, positive diagonal, negative off-diagonal; the ground is a solved row. Per-pass matrices are converted to farads and lose their labels; the units string still says "fF". | `renderer_ansys/q3d_renderer.py:185-187, 412-465`, `ansys_renderer.py:1242, 1621` |
| Q3D (pyaedt) | `auto_identify_nets()` | Per-pass values are magnitudes, so the off-diagonal sign is lost; `get_capacitance_matrix` is a stub. | `q3d_renderer_aedt.py:393-453` |
| ElmerFEM | `assign_nets`: shapely contact (distance 0, same chip, touching layers) plus pin-based grounding. A pin that is not open and not connected to another pin shorts its geometry to ground. A net is labeled by its last member, `{comp}_{geom}`; the ground is `ground_plane`. | Maxwell, fF. The ground row and column are synthesized from row sums and the ground self-capacitance is a placeholder `300`. | `elmer_renderer.py:277-421, 483-521` |
| scikit-fem | One unknown per conductor (Schur complement onto conductor unknowns); names come from `Package.metals` (`{comp}.{geom}`) | Maxwell; the ground is Dirichlet 0 and has no row | `package_modes.py:1448-1560` |
| SQDMetal | Contiguous fused polygons, one per conductor, in `unary_union` order (geometric). Named `Cond{i}` for display. The ground plane is one `Terminal`; the far-field faces are `Ground`. | `terminal-C.csv` read unchanged (F); the ground is a terminal row. Hard-coded 3–6-conductor transmon formulas. | `SQD/PALACE/Capacitance_Simulation.py:104-220, 313-692` |
| pyPalace | Nets exist only where the user maps several rows to one tag. | Maxwell (F). The ground row is appended as `C_ig = −Σ_j C_ij`. | `pyP/simulation.py:164-216` |

How the matrix is consumed in Metal:

- **`LOManalysis.run_lom`** calls `extract_transmon_coupled_Noscillator`.
  - The matrix is read **by position**, in the order
    `bus1 … busN-1, ground, pad1, pad2, readout`
    (`analyses/quantization/lumped_capacitive.py:193-199`).
  - Q3D's alphabetical `{geom}_{component}` names produce this order for
    `TransmonPocket` (tutorial 4.01).
  - Per-pass matrices arrive as unlabeled arrays in farads
    (`lumped_oscillator_model.py:153-194`).
- **LOM 2.0 (`Cell`, `Subsystem`)** reads the matrix **by name**.
  - It needs a `grd_node`: `ground_main_plane` for Q3D matrices (4.04, 4.05).
  - Tutorial 4.19 maps Elmer's names by hand with `node_rename`.

**Gap.**

- Galvanic nets exist in Metal only inside `QElmerRenderer`.
- The two in-tree capacitance producers disagree on:
  - net labels (`pad_top_Q1` against `Q1_pad_top`);
  - the ground label (`ground_main_plane` against `ground_plane`);
  - row order;
  - whether the ground self-capacitance is meaningful.
- The per-pass matrices carry no labels at all.
- The sign convention agrees: every producer is Maxwell.
- Two things differ in how the ground row is made:
  - Q3D and SQDMetal solve the ground row.
  - Elmer, pyPalace and scikit-fem either synthesize it or omit it.

### 2.6 Boundary conditions

| System | Metal surfaces | Outer walls | Other | Where |
|---|---|---|---|---|
| HFSS (COM) | Perfect-E sheets. The ground is included only if its chip has subtract geometry. | Not set, so Ansys defaults apply | Wirebonds as PEC solids | `hfss_renderer.py:450-452`, `ansys_renderer.py:1633-1636, 1682-1736` |
| Q3D (COM) | Thin conductor, "pec", 200 nm | No vacuum box | — | `q3d_renderer.py:161-183` |
| ElmerFEM | Capacitance bodies per net; the ground is body 0 | `Electric Infinity BC` on the whole vacuum box | — | `elmer_renderer.py:629-679` |
| scikit-fem | PEC (edges removed) | PEC walls | PMC or PEC symmetry cuts (half, quarter) | `package_modes.py:1089-1170` |
| SQDMetal | PEC; or surface impedance `Ls` (H/sq) on all metals (`add_kinetic_inductance`) | Per face `pec` / `absorbing` (order 1) / `conductor` | Dielectric interface layers (SA/MS/MA) for EPR; no symmetry | `SQD/PALACE/Model.py:1786-1875` |
| Palace | `PEC`, `Impedance(Rs, Ls, Cs)`, `Conductivity` | `PEC`, `PMC`, `Absorbing(Order)`, `Ground`, `ZeroCharge` | `Periodic`, `FloquetPort`, interface `Dielectric` postprocessing | `pyP/builder.py:129-407` (mirrors the Palace schema) |

**Gap.**

- Metal has no boundary-condition vocabulary. The following are all implicit
  in each renderer:
  - the metal treatment;
  - the outer-wall treatment (not set in HFSS, an "infinity" condition in
    Elmer, PEC in scikit-fem);
  - symmetry, which only scikit-fem has.
- There is no per-face group to attach a wall condition to.

### 2.7 Materials

| System | What it has | Where |
|---|---|---|
| Layer stack | A `material` column per `(chip, layer, datatype)` with `pec` / `silicon` by default. No property values. | `toolbox_metal/layer_stack_handler.py:20-66` |
| `DesignPlanar` chips | `material="silicon"`, `size_z` | `designs/design_planar.py:94-108` |
| Gmsh | Ignores `material`; a layer counts as metal or dielectric through `layer_types` | `gmsh_renderer.py:116-117` |
| ElmerFEM | Hard-coded `materials=["vacuum", "silicon"]`, silicon εr = 11.45; every dielectric layer is treated as silicon | `elmer_renderer.py:108`, `elmer_configs.py:7-15` |
| Ansys COM | The chip `material` name is looked up in the AEDT library, so the values come from AEDT | `ansys_renderer.py:1613, 1628` |
| scikit-fem tutorials | εr = 11.9, the value used in the reproduced paper | `package_modes.py:58` |
| Analytic CPW formulas | εr = 11.45 default | `analyses/em/cpw_calculations.py:50` |
| SQDMetal | Scalar library: silicon 11.45 with tan δ 2.7e-6, sapphire 9.4 / 11.35, interfaces. The driven solve sets substrate tan δ = 1.2e-5 regardless of material (`Frequency_Driven_Simulation.py:168`). | `SQD/Utilities/Materials.py` |
| Palace | Scalar or anisotropic (3-vector plus `MaterialAxes`) permittivity, loss tangent, conductivity, London depth | Palace schema |

**Gap.**

- "silicon" means εr = 11.45 in Elmer and SQDMetal, 11.9 in the scikit-fem
  tutorials, and whatever AEDT's library says in HFSS.
- The layer stack names materials, but no Metal code reads the name.
- There is no place for a loss tangent, anisotropy, or a thin interface
  layer.

### 2.8 Solve setups

- **Metal.** The simulation classes' `default_setup` dicts are HFSS- and
  Q3D-shaped (adaptive passes, `max_delta_f`, `percent_error`,
  `basis_order`).
  - They are forwarded wholesale: `initialize_eigenmode(**self.setup)`
    (`eigenmode.py:77`) and `initialize_cap_extract(**self.setup)`
    (`lumped_elements.py:83`). The Ansys renderers accept `**kwargs` there
    (`ansys_renderer.py:978-1002`).
  - Their defaults use `if not x:`, so `0` and `False` cannot be passed.
  - `EigenmodeSim` defaults `basis_order=1`, while the HFSS renderer's
    default is `-1`.
- **SQDMetal and pyPalace** use Palace's own vocabulary:
  - `Eigenmode{N, Target, Tol}`;
  - `Solver.Order`;
  - `Driven{MinFreq, MaxFreq, FreqStep}`;
  - `Electrostatic{Save}`;
  - `Model.Refinement`.
- **scikit-fem** takes `eigenmodes(f_target, n, inductors)` directly and has
  no passes.

**Gap.**

- There is no neutral description of a study.
- Settings that only mean something for an adaptive solver (passes, deltas)
  have no defined meaning for a single-pass solver.
- New neutral options cannot be added to `setup`, because the Ansys renderers
  would receive them as keyword arguments.

### 2.9 Outputs

| Output | Ansys COM | ElmerFEM | scikit-fem | SQDMetal / pyPalace |
|---|---|---|---|---|
| Frequencies, Q | From pyEPR (`epr_get_frequencies`) or the last row of `convergence_f` | — | `Mode` objects | `eig.csv` |
| Junction EPR | pyEPR `DistributedAnalysis` on the Ansys model (`epr_*`, `ansys_renderer.py:1776-1887`) | — | Junction voltages from the solution (EPR low by `sqrt(L_J/(L_J+dL))` when only the junction is counted) | `port-EPR.csv`, signed p_mj (Palace: `docs/src/reference.md`, "Energy-participation ratios") |
| Surface or bulk loss participation | pyEPR `dissipatives` | — | — | Palace `Dielectric` postprocessing, `surface-Q.csv` (SQDMetal) |
| Capacitance | see 2.5 | see 2.5 | P1/P2 | `terminal-C.csv` |
| Convergence | Per-pass tables (`get_convergences`, `hfss_renderer.py:1052`) plus a GUI-text parse | — | none (single solve) | Palace AMR iterations; not parsed by SQDMetal |
| Network (S/Y/Z) | `get_params`, `get_all_Pparms_matrices` | — | `PortROM.impedance` | `port-S.csv` |
| Fields | In AEDT (`set_mode`, `plot_fields`) | Gmsh post-processing file | Point evaluation (`Mode.field`) | ParaView `.pvd` |

**Gap.**

- `EPRanalysis` delegates every step to Ansys-specific renderer methods
  (`energy_participation_ratio.py:185-268`); its own TODO at lines 185–187
  records this.
- Yet the numerical core it needs is solver-neutral:
  - pyEPR's `CalcsBasic.epr_to_zpf(Pmj, SJ, Ω, EJ)` and
    `epr_numerical_diagonalization(freqs, Ljs, ϕzpf, ...)` are pure
    functions;
  - `import pyEPR` needs neither COM nor pyaedt, and its dependencies are
    pure Python (pyEPR 1.0.1, `29d4513`).
- The full analysis and its reports come from `QuantumAnalysis`.
  - It loads a pickle file with a fixed per-variation schema:
    `freqs_hfss_GHz`, `Qs`, `Ljs`, `Cjs`, `Pm`, `Sm`, `I_peak`, `V_peak`,
    `mesh`, `convergence`, and more (`core_quantum_analysis.py:276-305`).
  - Only the Ansys analyses write that file: `DistributedAnalysis` and
    `PyaedtDistributedAnalysis`.
  - Its junction participation is the junction's inductive energy divided by
    the mode's electric energy (`core_distributed_analysis.py:1121`). That is
    the normalization Palace uses for `port-EPR.csv`.
- Palace (`port-EPR.csv`) and scikit-fem (junction voltages) can each supply
  their inputs: p_mj with sign, f_m and L_j.
- There is no result type that records how a number was produced, e.g. which
  element order, which mesh, and whether it converged.

### 2.10 The informal renderer contract

These are the calls the simulation and analysis classes make, with their
return shapes. The COM track implements all of them. The pyaedt track and
`QElmerRenderer` implement almost none.

| Call | Caller | Return |
|---|---|---|
| `execute_design(name, solution_type, vars_to_initialize, force_redraw, **{selection, open_pins, port_list, jj_to_port, ignored_jjs, box_plus_buffer})` | `core/simulation.py:173` | final design name |
| `initialize_eigenmode(vars, **setup)` / `initialize_cap_extract(**setup)` / `initialize_drivenmodal(sweep_setup, vars, **setup)` | `eigenmode.py:77`, `lumped_elements.py:83`, `scattering_impedance.py:94` | setup name; `(setup, sweep)` for driven |
| `analyze_setup(name)`, `analyze_sweep(sweep, setup)` | same files | — |
| `get_convergences(variation)` | `eigenmode.py:262` | `(convergence_t, convergence_f, text)` |
| `get_capacitance_matrix()`, `get_capacitance_all_passes()`, `get_convergence()` | `lumped_elements.py:91-95` | `(DataFrame, "fF")`, `(dict, units)`, `bool \| None` |
| `set_mode`, `plot_fields`, `clear_fields`, `plot_params` | `eigenmode.py:337-347`, `scattering_impedance.py:109-129` | — |
| `epr_start`, `epr_get_stored_energy`, `epr_run_analysis`, `epr_spectrum_analysis`, `epr_report_hamiltonian`, `epr_get_frequencies` | `energy_participation_ratio.py:200-268` | pyEPR objects and values |
| `plot_convergence_main`, `plot_convergence_chi` | `lumped_oscillator_model.py:219, 230` | — |

### 2.11 What Metal already has that the RFC and SQDMetal do not use

1. **`QGmshRenderer` itself.** It handles:
   - ground planes with cutouts;
   - finite-thickness or sheet metal (`ignore_metal_volume`);
   - multi-layer and multi-chip stacks from `design.ls`;
   - component selection with bounding-box buffers;
   - open-pin endcaps;
   - junction rectangles.

   Both SQDMetal and pyPalace rebuild these.
2. **Galvanic nets from pin connectivity.** `QElmerRenderer.assign_nets` and
   `get_gnd_qgeoms` use `design.net_info` and pin positions to decide which
   geometries are one conductor and which are grounded. SQDMetal's
   conductors are anonymous fused polygons, and pyPalace leaves nets to the
   user.
3. **The junction table as a port source.** Each row's LineString and
   `width` give the sheet, the direction and the line. Ansys already uses
   them. SQDMetal uses only the LineString and width. pyPalace ignores the
   table.
4. **Per-renderer junction values.** The `element_table_data` mechanism
   creates `<renderer>_inductance`-style columns that components carry as
   options. A Palace or scikit-fem renderer gets per-junction L, C and R
   with no new core code. `EigenmodeSim` already warns when these disagree
   with `setup.vars.Lj` (`eigenmode.py:145-204`).
5. **Renderer registration without an entry-point mechanism.**
   - `config.renderers_to_load` is a plain `Dict` read when each design is
     created (`config.py:24-53`, `design_base.py:978-1060`).
   - A package that adds an entry before the design is created is
     registered by name.
   - Missing optional dependencies are already caught, and the renderer is
     skipped.
6. **Layer stack and chip data** (thickness, z, material names, sample-holder
   heights), which SQDMetal takes from `chips['main'].size_z` and user calls.

### 2.12 What Metal lacks that made native use hard

1. No port object and no port geometry in the gmsh model (2.2).
2. No roles on physical groups, and no per-face outer-boundary groups (2.4).
3. No boundary-condition or material vocabulary. The only material data is
   Elmer's hard-coded list (2.6, 2.7).
4. No role-addressed mesh refinement; the junction field was broken until step 1.0 (2.3).
5. Nets and their labels are private to `QElmerRenderer`. There is no
   canonical label or order, and per-pass matrices are unlabeled (2.5).
6. A renderer contract shaped by Ansys: setup names, passes, variation
   strings, and `epr_*` methods wrapping pyEPR's Ansys `ProjectInfo` (2.8–2.10).
7. No declaration of what a backend can do. Asking `EigenmodeSim` for
   `"elmer"` fails with `AttributeError: 'QElmerRenderer' object has no
   attribute 'execute_design'`, not with a
   message.
8. No explicit length-unit contract with the mesh:
   - `export_mesh` scales mm to m by default (`gmsh_renderer.py:1320-1344`);
   - Palace's `L0` defaults to 1e-6;
   - SQDMetal writes mm with `L0 = 1e-3`;
   - pyPalace writes µm with `L0 = 1e-6`.

### 2.13 RFC statements that differ from the current tree

These are recorded so the design below starts from the code as it is.

- The RFC says `LOManalysis.run_lom` consumes the matrix by net name. The
  function it calls reads it by position (2.5). LOM 2.0 reads by name.
- The RFC says SQDMetal restricts lumped ports to ±x/±y. The check it cites
  is not called, and ports are emitted with arbitrary `Direction` vectors
  (2.2). The axis-alignment restriction that does exist today is Metal's
  own: gmsh endcaps and Ansys port sheets.
- The RFC's packaging section assumes `numpy<2` across the environment and a
  two-folder notebook sync. Metal 0.9.0 supports numpy 2, and notebooks now
  live only under `docs/`.
- The RFC proposes an entry-point group `qiskit_metal.renderers`. None exists
  today; see item 5 in 2.11 for the mechanism that does.

## 3. Design

### 3.1 Principles

- **Differences are declared, not hidden.** A backend that cannot do
  something says so before any geometry is built, and the error names the
  backends that can.
- **Additive.** No change to public signatures of `QComponent`, `QDesign`,
  `QRenderer`, the simulation classes' `run_sim`, or their `setup` keys.
  Nothing in `renderer_ansys*` or the pyEPR bridge changes.
- **One description, many readers.** The simulation classes build one
  `SimulationProblem` from their arguments. Every non-Ansys backend reads
  that description. The Ansys path keeps receiving today's tuple arguments.
- **No physical value is a constant in backend code.** All of these are
  options:
  - permittivities, loss tangents and conductivities;
  - interface layers;
  - surface impedances;
  - junction values;
  - port impedances.

  Each option is either unset or has a documented default in one place. A
  loss tangent that is not set means lossless, and every result records the
  values it used.
- **Physical quantities in SI at the interfaces.** Users write Metal strings
  (`"2um"`, `"10nH"`), parsed with design variables. The neutral objects
  hold SI floats. Every mesh export states its length unit.
- **Pure Python in core.** The new modules import nothing heavier than
  shapely and pandas, so they load on the lite install and are tested on
  every PR.

### 3.2 Module map

| Module | Contents |
|---|---|
| `analyses/simulation/problem.py` | `SimulationProblem`, ports and junctions, boundary conditions, `MeshSpec`, studies; converters to and from the tuple arguments |
| `analyses/simulation/materials.py` | Material records and a small library; resolution from the layer stack and chip data |
| `analyses/simulation/results.py` | Result types and provenance |
| `analyses/simulation/capabilities.py` | `Capabilities`, the registry, the pre-run check, the capability table |
| `toolbox_metal/nets.py` | Galvanic nets and labels, lifted from `QElmerRenderer` |
| `renderers/renderer_gmsh/groups.py` | `PhysicalGroup`, `Role`, `PhysicalGroupMap` (plain data; filled by `QGmshRenderer`) |

### 3.3 The problem description

The simulation classes assemble a `SimulationProblem` from `run_sim`
arguments, `setup` and a new `sim.model` attribute. `sim.model` holds
everything that has no tuple-argument form: boundary conditions, materials,
mesh, and explicit ports. It is separate from `setup` because `setup` is
forwarded to the Ansys renderers as keyword arguments (2.8).

```python
@dataclass
class SimulationProblem:
    design: QDesign
    components: list[str] | None         # None = all
    box: Box                             # box_plus_buffer
    pins: dict[PinRef, PinEnd]           # OPEN (endcap cut); others SHORT
    junctions: dict[JunctionRef, Junction]  # others: the default inductor
    ports: list[LumpedPort | WavePort]
    boundaries: Boundaries
    materials: dict                      # material options (3.7)
    mesh: MeshSpec
```

- **`from_run_args(design, components, open_terminations, port_list,
  jj_to_port, ignored_jjs, box_plus_buffer)`** covers every tuple pattern
  the tutorials use, including the pyaedt renderers' three-element
  `jj_to_port`. It only converts; `validate()` checks the names against the
  design and reports every problem at once.
- **`to_run_args(jj_to_port_arity=4)`** goes the other way, for the Ansys
  path. It raises `NotExpressibleError`, listing every offending part, when
  the problem holds something the tuples cannot express: a wave port, a port
  that is not on a pin, a junction with its own L, C or R, or non-default
  boundary conditions. Mesh refinement and material options have no tuple
  form either, but they are settings, reported as ignored by the capability
  check (3.11).
- **Values follow Metal's conventions.** Lengths are strings with units,
  design variables, or numbers in design units. R, L and C are strings with
  units, variables, or SI numbers. `length_m()` and `circuit_value()` return
  SI floats.

### 3.4 Ports and junctions

A port is where a lumped circuit element or a transmission line meets the
field. It has three things:

- a place: a pin, or explicit geometry;
- a shape: a sheet, a line, or two sheets across a CPW's gaps;
- a circuit: R, L and C in parallel.

A junction is described by `Junction`, never by a port. Its mode says whether
it is an inductor, a port, or left open, so there is one way to say each
thing. Which ports are driven belongs to the driven study (3.9).

```python
@dataclass(frozen=True)
class PinRef:       component: str; pin: str
@dataclass(frozen=True)
class JunctionRef:  component: str; name: str          # row in the junction table
@dataclass(frozen=True)
class Segment:      p0: tuple; p1: tuple; width: float; layer: int

@dataclass(frozen=True)
class LumpedPort:
    at: PinRef | Segment
    R: Value | None = 50.0                             # ohm; L in H, C in F
    L: Value | None = None
    C: Value | None = None
    shape: Literal["sheet", "line", "cpw"] = "sheet"   # cpw: two sheets across the gaps
    name: str | None = None                            # default Port_<component>_<pin>

@dataclass(frozen=True)
class Junction:
    mode: Literal["inductor", "port", "open"] = "inductor"
    L: Value | None = None      # None: <renderer>_inductance column (may name a setup.vars entry)
    C: Value | None = None
    R: Value | None = None      # port impedance ("port"; default 50 ohm) or parallel R
    shunt_inductor: bool = False  # "port": keep the inductor beside it (draw_ind)

@dataclass(frozen=True)
class WavePort:
    face: Literal["x-", "x+", "y-", "y+", "z-", "z+"]
    center: tuple; size: tuple
    n_modes: int = 1
    name: str | None = None                            # default WavePort_<face>
```

Geometry is computed once, in core, with shapely.

- **Pin port.** The sheet runs from `middle` to `middle + gap·normal`, with
  the pin's `width`. This is the Ansys convention.
- **Pin port, `cpw` shape.** Two sheets fill the side gaps, with ±direction.
  This is the SQDMetal convention.
- **Junction port.** The sheet is the junction's rectangle, the line is its
  LineString, and the direction is the LineString's direction.

Each port carries its direction vector. Pins at any angle are handled. The
existing axis-aligned code paths (gmsh endcaps, Ansys sheets) are recorded as
capability limits, not copied.

The tuple arguments map one to one:

| Tuple argument | Neutral form |
|---|---|
| `open_terminations=[(c, p)]` | `pins[PinRef(c, p)] = OPEN` |
| `port_list=[(c, p, Z)]` | `LumpedPort(at=PinRef(c, p), R=Z)` |
| `jj_to_port=[(c, j, Z, draw_ind)]` | `junctions[JunctionRef(c, j)] = Junction("port", R=Z, shunt_inductor=draw_ind)` |
| `ignored_jjs=[(c, j)]` | `Junction("open")` |
| any other junction | `Junction("inductor")`, with values from `<renderer>_inductance` / `_capacitance` or `setup.vars` |

### 3.5 Nets and physical groups

**Nets.** `galvanic_nets(design, selection, open_pins, metal_layers)` returns
a `NetMap`:

```python
@dataclass(frozen=True)
class Net:
    id: int
    members: tuple[GeomRef, ...]   # (component, qgeometry name, table)
    is_ground: bool
    chip: str
```

It is `QElmerRenderer.assign_nets` and `get_gnd_qgeoms` moved into
`toolbox_metal/nets.py`: shapely contact plus pin-based grounding. It needs
no gmsh, so the gmsh renderer, ElmerFEM, scikit-fem and Palace all read the
same nets. `QElmerRenderer` calls it and keeps its current output.

**Labels.** `NetMap.label(net, style)` gives one deterministic label per
style.

- The `q3d` style is `{geom}_{component}` of the net's first member in sort
  order, with the ground labeled `ground_{chip}_plane`.
- The `elmer` style reproduces today's Elmer labels.
- Capacitance results are ordered alphabetically by label. With the `q3d`
  style this gives the positional order `extract_transmon_coupled_Noscillator`
  expects, and the names LOM 2.0 cells already use (`grd_node=
  "ground_main_plane"`).
- Which style is canonical is decision D3.

**Physical groups.** `QGmshRenderer.group_map` is a `PhysicalGroupMap` built
from the same tags as `physical_groups`. The existing dict and its names do
not change.

```python
class Role(Enum):
    CONDUCTOR = ...     # metal surfaces (dim 2) or volumes (dim 3), with .net
    GROUND = ...
    DIELECTRIC = ...    # volumes, with .material
    VACUUM = ...
    JUNCTION = ...      # sheet (dim 2) or line (dim 1)
    PORT = ...          # sheets, with .port and .direction
    OUTER_FACE = ...    # with .side in {x-, x+, y-, y+, z-, z+}
    SYMMETRY_FACE = ...
    INTERFACE = ...     # MA / SA / MS layers for surface participation

@dataclass(frozen=True)
class PhysicalGroup:
    name: str; dim: int; tag: int; role: Role
    net: str | None = None; layer: int | None = None; material: str | None = None
    component: str | None = None; qgeometry: str | None = None
    port: str | None = None; side: str | None = None; direction: tuple | None = None
```

Consumers query by role and attribute (`group_map.tags(role=Role.CONDUCTOR,
net="pad_top_Q1")`), never by substring.

Extra groups are opt-in, requested by the backend. These are the port
sheets, per-side outer faces, junction lines and interface layers. The
default model stays what ElmerFEM reads today. An entity in two physical
groups changes what the exported mesh contains, so each opt-in group is
checked against the ElmerFEM regression in section 7.

### 3.6 Boundary conditions

```python
@dataclass
class Boundaries:
    metal: PEC | SurfaceImpedance | Conductivity = PEC()
    per_net: dict[str, PEC | SurfaceImpedance | Conductivity] = field(default_factory=dict)
    outer: dict[Side, Literal["pec", "pmc", "absorbing", "open"]] | None = None  # None: study default
    symmetry: list[SymmetryPlane] = field(default_factory=list)   # axis, position, "pmc" | "pec"
    interfaces: LossInterfaces | None = None   # from sim.model.interfaces; no defaults

@dataclass(frozen=True)
class SurfaceImpedance:
    Ls: float = 0.0   # H per square: kinetic inductance
    Rs: float = 0.0   # ohm per square
```

- Kinetic inductance is a property of a metal surface, not a port. It
  replaces PEC on the nets it names.
- The outer-wall default depends on the study: `pec` for eigenmode and
  driven, `open` for electrostatics.
- "Open" is not one condition. It is Elmer's `Electric Infinity BC`, Palace's
  `ZeroCharge` or `Ground`, or whatever Q3D does, and each gives slightly
  different results for a finite box. Each backend's capability entry states
  which one it uses.
- A symmetry plane is a geometry cut plus a condition. The PMC or PEC choice
  selects the mode family (`.claude/skills/chip-simulation/SKILL.md`,
  section 4).

### 3.7 Materials

Material properties are options, like a component's `default_options`. They
are not constants in any backend.

```python
sim.model.materials = Dict(
    vacuum=Dict(eps_r=1.0),
    silicon=Dict(eps_r=11.45),                        # a default option value (D4)
    sapphire=Dict(eps_r=(9.3, 9.3, 11.5), axes=...),  # anisotropic: diagonal plus axes
)
sim.model.materials.silicon.tan_delta = 2.7e-6        # lossy only when set
sim.model.interfaces = Dict(                           # no defaults: set to use
    MA=Dict(thickness="2nm", eps_r=10, tan_delta=5e-4),
)
```

**Where the values come from.**

- The option defaults are one documented `default_materials` Dict in
  `analyses/simulation/materials.py`. It holds permittivities only; no loss
  tangent, conductivity or interface layer has a default.
- A material name comes from the layer stack's `material` column, or from
  `design.chips[...].material` for `DesignPlanar`.
- The value for that name is taken from the first of these that sets it:
  1. `sim.model.materials`;
  2. an optional `eps_r` / `tan_delta` column on that layer-stack row;
  3. `default_materials`.
- A name that none of these resolves is an error that names the missing
  material. It never falls back silently.

**How each backend uses it.**

- ElmerFEM's hard-coded `["vacuum", "silicon"]` list and `11.45` become the
  default option values, so ElmerFEM results do not change unless the user
  sets something.
- Palace receives exactly the resolved values; a loss tangent appears in its
  config only when the user set one.
- HFSS keeps AEDT's library by name, and its capability entry says that
  Metal's material options do not reach it.
- Every result's provenance lists the εr and tan δ used, with "not set" for
  unset loss.

### 3.8 Mesh-size control

```python
@dataclass(frozen=True)
class Refine:
    select: Select                 # role / net / component / port / junction / box
    size: Value                    # element size on the target
    grow: Value                    # distance over which size grows to max_size
    shape: Literal["distance", "ball"] = "distance"

@dataclass
class MeshSpec:
    max_size: Value | None = None  # None: the renderer's own option
    min_size: Value | None = None
    refine: list[Refine] = field(default_factory=list)
```

The mesh spec says only where elements must be small. Element order and
adaptive refinement belong to the study (3.9), which is where both HFSS and
Palace keep them.

- `QGmshRenderer` compiles a `MeshSpec` to Distance+Threshold(+Ball)+Min
  fields, resolved through the group map.
- The spec equivalent to today's `options.mesh` is the default, and it must
  reproduce today's fields exactly.
- The junction field works since step 1.0 (section 6).
- Ansys maps only what its options express: `max_mesh_length_jj` and
  `max_mesh_length_port`, plus the adaptive settings in `setup`. Anything
  else is reported as ignored.
- Palace can add error-indicator refinement (`Model.Refinement`) on top of
  the gmsh mesh.

### 3.9 Studies

```python
@dataclass
class EigenmodeStudy:     n_modes: int; min_freq_ghz: float; order; adaptive; backend_settings; set_keys
@dataclass
class ElectrostaticStudy: order; adaptive; backend_settings; set_keys
@dataclass
class DrivenStudy:        sweep: Sweep; adapt_freq_ghz; excite: list[str]; order; adaptive; backend_settings; set_keys

@dataclass(frozen=True)
class Adaptive:  max_passes; min_passes; min_converged; tolerance; criterion; refine_pct
```

`study_from_setup(solution_type, setup, defaults)` builds a study from the
existing `setup` dict and the class's `default_setup`.

- **Neutral meaning.** Only keys with one are mapped: `n_modes`,
  `min_freq_ghz`, the sweep, and the adaptive-pass keys. The adaptive
  criterion is `delta_f_pct` (HFSS eigenmode), `delta_c_pct` (Q3D) or
  `delta_s` (driven).
- **Everything else** goes to `backend_settings` for the backend that knows
  it: `basis_order`, `solution_order`, Q3D's `freq_ghz`, `vars`, and so on.
  `basis_order` is not translated to an element order, because its numbering
  is AEDT's own.
- **Changed keys.** `set_keys` lists the keys that differ from the class
  defaults. The capability check warns about an ignored setting only when
  the user changed it, so a single-pass backend does not warn about the
  default `max_passes=10` on every run.
- **Excitation.** `DrivenStudy.excite` names the driven ports; empty means
  every port.
- Metal's bookkeeping keys (`name`, `reuse_selected_design`, `reuse_setup`)
  are not part of a study.

### 3.10 Results and provenance

```python
@dataclass
class Provenance:
    backend: str; backend_version: str | None
    element_order: int | None
    mesh: MeshStats | None          # elements, unknowns, h_min, h_max, mesh id
    converged: bool | None          # None: not assessed (single solve)
    ignored_settings: dict
    materials: dict                 # name -> (eps_r, tan_delta) used

@dataclass
class Modes:           freq_ghz: np.ndarray; q: np.ndarray | None; fields: FieldHandle | None; provenance: Provenance
@dataclass
class JunctionEPR:     p: np.ndarray; junctions: list[str]; L: np.ndarray   # p: modes x junctions, signed
@dataclass
class Capacitance:     matrix: pd.DataFrame; units: str; per_pass: list[pd.DataFrame] | None
                       ground_row: Literal["solved", "synthesized"]; method: str; provenance: Provenance
@dataclass
class Network:         freq_ghz: np.ndarray; Z: np.ndarray | None; Y: ...; S: ...; ports: list[str]; z0: np.ndarray
@dataclass
class Convergence:     table: pd.DataFrame   # one row per pass or per mesh: size, monitored values, delta
```

- **Existing data labels.** The simulation classes copy results into their
  current data labels (`capacitance_matrix`, `units`, `cap_all_passes`,
  `is_converged`, `convergence_t`, `convergence_f`). `LOManalysis` and the
  plots therefore work unchanged. Per-pass matrices keep their labels.
- **Single-pass backends.** These report one convergence row and
  `converged=None`. Convergence is shown by re-solving on a list of
  `MeshSpec`s, which fills the same table one row per mesh. This is the
  proposed answer to the RFC's question on "passes" for single-pass solvers,
  and it goes into the stage-3 contract.
- **EPR.** The numerics stay in pyEPR (D6). `EPRanalysis` gains a path for
  any backend that returns `JunctionEPR` (f_m, Q_m, L_j, C_j, and p_mj with
  sign).
  - That path hands the arrays to a new public entry in pyEPR, for example
    `QuantumAnalysis.from_arrays(...)`. The entry builds the same
    per-variation data the Ansys analyses write, with `Pm = |p|` and
    `Sm = sign(p)`.
  - HFSS, Palace and scikit-fem results then share one `QuantumAnalysis`:
    the same χ, anharmonicities and reports.
  - The Ansys path is untouched.
- **The P1 trap.** In a lowest-order edge-element model, the static part of
  every mode is first-order (P1) electrostatics on the same mesh. The qubit
  capacitance inside an N0 eigenmode is therefore the P1 capacitance, not
  the converged one (about 230 fF against a converged 174 fF on a 0.1 mm
  mesh; `open_fem_scikit_fem.md`). For this
  reason:
  - `Capacitance.method` states the element order and `Provenance.mesh`
    identifies the mesh.
  - Helpers that combine a capacitance with a mode (induced-EMF couplings,
    LOM against eigenmode) check that both come from the same mesh and the
    same order, and refuse to mix them otherwise.
  - Cross-backend tests compare converged quantities or the same
    discretization, never raw numbers from different element orders.

### 3.11 Capabilities and the pre-run check

```python
@dataclass(frozen=True)
class Capabilities:
    studies: frozenset[str]        # eigenmode, electrostatic, driven, magnetostatic
    ports: frozenset[str]          # lumped_sheet, lumped_line, lumped_cpw, wave
    junctions: frozenset[str]      # inductor, port, open
    boundaries: frozenset[str]     # pec, surface_impedance, conductivity, absorbing,
                                   # open_electrostatic, pmc_symmetry, pec_symmetry
    outputs: frozenset[str]        # frequencies, q, junction_epr, surface_epr,
                                   # capacitance, network, convergence_history, fields
    geometry: frozenset[str]       # ground_cutouts, sheet_metal, thick_metal,
                                   # multi_layer, flip_chip, any_pin_angle
    materials: frozenset[str]      # from_layer_stack, loss_tangent, anisotropic
    element_orders: tuple[int, ...]
    adaptive_refinement: bool
    parallel: Literal["none", "threads", "mpi"]
    requires: tuple[str, ...]      # e.g. "Ansys AEDT license", "ElmerSolver on PATH"
```

**Registration.**

- A new renderer carries `capabilities` as a class attribute.
- The Ansys and existing ElmerFEM entries live in the registry module
  (`capabilities.py`), keyed by renderer name. They describe what the code
  does today, so `renderer_ansys*` is not touched.
- Some Ansys entries are narrower than AEDT itself. HFSS can model a
  surface impedance, for example, but Metal's HFSS renderer does not expose
  one, so the entry says `surface_impedance` is unsupported.

**The check.** It runs at the start of `run_sim`, before rendering:

```
BackendCapabilityError: renderer 'elmer' cannot run: study 'eigenmode', output 'junction_epr'.
Backends that can: hfss (registered; needs Ansys AEDT license), skfem (not installed: pip install ...).
```

- A missing study, port kind, boundary condition or output is an error.
- A setting the backend ignores, such as `max_passes` on a single-pass
  solver, is recorded in provenance. It is also a warning when the user
  changed it from the class default (`set_keys`, 3.9). Strictness is
  decision D5.
- On the legacy Ansys path only the study type is checked, so nothing that
  runs today starts failing.

**The docs table.** `capability_table()` renders the registry as the
comparison table in `docs/simulation-pathways.rst`, so the table and the
code cannot drift.

### 3.12 How the simulation classes reach a backend

Two shapes are possible. This is decision D1.

**N (recommended): a small neutral protocol next to the legacy path.**

```python
@runtime_checkable
class SolverBackend(Protocol):
    capabilities: Capabilities
    def prepare(self, problem: SimulationProblem) -> None: ...   # geometry, groups, mesh
    def solve(self, study) -> Modes | Capacitance | Network: ... # plus JunctionEPR, Convergence
```

- A backend is still a `QRendererAnalysis`, registered by name, so
  `renderer_name="skfem"` and `design.renderers.skfem` keep working as the
  front door (decision log, 2026-09-27).
- In `run_sim`:
  - if the renderer satisfies `SolverBackend`, the class checks
    capabilities, builds the problem, calls `prepare` and `solve`, and stores
    the results;
  - otherwise it runs today's `_render` / `_analyze` code, unchanged.
- The neutral path can be tested in CI with a fake backend that returns an
  analytic LC circuit.

**A: new backends imitate the Ansys contract** (RFC section 4a).

- Each new backend implements `execute_design`, `initialize_*`,
  `analyze_setup`, `get_convergences`, `get_capacitance_*`, `set_mode`,
  `plot_fields`, `clear_fields` and the `epr_*` family.
- The simulation classes stay as they are.
- The cost:
  - every backend invents setup names, passes and variation strings;
  - every backend re-parses the tuple arguments;
  - boundary conditions, materials and mesh specs have no way through;
  - `EPRanalysis` stays tied to pyEPR's Ansys `ProjectInfo`.

A backend may implement both shapes. Shape N does not rule out an
`execute_design` shim for code that calls renderers directly.

### 3.13 Units

- Metal parses lengths to design units (mm).
- `QGmshRenderer` builds in mm and `export_mesh` writes meters by default
  (`scaling_factor=1e-3`).
- The neutral objects hold SI.
- Mesh export returns `(path, unit_in_m)`.
  - The ElmerFEM reader assumes meters, as it does today.
  - The Palace config takes `L0` from the returned unit. Palace's default
    `L0` is 1e-6 (Palace: `scripts/schema/config-schema.json`), so writing it
    explicitly is required.
  - A round-trip test builds a known capacitor and checks that its
    capacitance does not depend on the export unit.
- Frequencies stay in GHz and capacitances in fF with a units string, as the
  simulation classes return them today.

## 4. How each backend reads the abstractions

| Abstraction | Ansys (COM; pyaedt as noted) | ElmerFEM | scikit-fem | Palace |
|---|---|---|---|---|
| Entry | Legacy path: `to_run_args()`, renderer unchanged | `SolverBackend` (after migration; direct API kept) | `SolverBackend` | `SolverBackend` |
| Geometry | Ansys renderer draws it | `QGmshRenderer` | `QGmshRenderer` with sheet metal (`ignore_metal_volume` or a zero-thickness layer), junction lines | `QGmshRenderer` (sheet or thick metal) |
| Ports | `port_list` sheets; no wave ports; axis-aligned pins | Not used (electrostatics: junctions open) | `lumped_line` on junction lines and probes | `LumpedPort` from sheets (single or ± elements), `WavePort` from outer faces |
| Junctions | RLC boundary from `hfss_*` columns | Open | Rank-one inductor on the edge chain | `LumpedPort` with L (and C); EPR from `port-EPR.csv` |
| Groups | Ansys object names | `group_map`: conductors by net, ground, dielectric, vacuum | `group_map`: conductor sheets, junction lines, symmetry faces | `group_map` to integer attributes for Domains and Boundaries |
| Boundary conditions | PEC sheets; walls at Ansys defaults | Ground body, infinity BC on the box | PEC walls, PMC/PEC symmetry | `PEC`, `Impedance`, `Absorbing`, `Ground` / `ZeroCharge`, `Dielectric` postprocessing |
| Materials | AEDT library by name (Metal's material options do not reach it) | Material options (εr) | Material options (εr); lossless | Material options, including tan δ and anisotropy when set |
| Mesh | `max_mesh_length_jj/port` plus adaptive passes | `MeshSpec` through gmsh | `MeshSpec` through gmsh | `MeshSpec` through gmsh, optional `Model.Refinement` |
| Studies | eigenmode, capacitance, driven | electrostatic (eigenmode: stage 2) | eigenmode, electrostatic, driven via port ROM | eigenmode, electrostatic, driven, magnetostatic |
| Outputs | pyEPR tables, Q3D matrices, S/Y/Z | Capacitance (ground synthesized) | Modes, junction voltages, capacitance (P1/P2), Z | `eig.csv`, `port-EPR.csv`, `terminal-C.csv`, `port-S.csv`, `.pvd` |
| Convergence | Adaptive passes | One solve | One solve per `MeshSpec` | AMR iterations or one solve per `MeshSpec` |

Notes:

- **Ansys.** It stays fully supported, and stage 1 adds nothing to
  `renderer_ansys*`.
  - The pyaedt track cannot be driven by the simulation classes today, so its
    registry entry says so.
  - Moving from the Windows-only COM renderers to current pyaedt is the
    separate Ansys track (ROADMAP), gated on AEDT testing.
  - A pyaedt-based renderer can implement the neutral protocol (3.12)
    directly, reading ports, junctions and studies from `SimulationProblem`.
    EPR then goes through pyEPR's pyaedt analysis (`PyaedtDistributedAnalysis`,
    `pyEPR/ansys_pyaedt.py`). Neither needs the COM track's informal
    contract.
- **ElmerFEM.** It migrates in steps (section 6):
  - nets from `toolbox_metal/nets.py`;
  - bodies and boundaries from `group_map`;
  - materials from the material options.

  Each step is checked against a byte-identical `.sif` and the same net
  dictionary on the tutorial 4.19 design. The direct
  `render_design` / `add_solution_setup` / `run` API stays.
- **scikit-fem.** Stage 2 moves `MaxwellFEM`, `PortROM` and `Electrostatics`
  into `src/` behind an optional extra. It reads geometry from `group_map`
  instead of `mesh_package`, which brings ground planes with cutouts and
  CPWs. `package_modes.py` stays as a thin wrapper, so tutorials 4.41–4.45
  run unchanged. Junction lines need gmsh to embed 1D entities, which the
  port step (1.6) provides.
- **Palace.**
  - The config is plain JSON, validated against the schema Palace ships
    (`scripts/schema/config-schema.json`). pyPalace's `Config.load_config`
    can read it.
  - The result readers:
    - strip Palace's padded CSV headers;
    - keep the EPR sign;
    - select ports by `Index`, not by column position.
  - The runner:
    - finds the binary on `PATH` or through an option;
    - checks for an MPI launcher when more than one process is requested;
    - sets the working directory;
    - checks the return code;
    - writes outside `docs/`.
  - Which pieces come from SQDMetal (Apache-2.0) or pyPalace (MIT), with
    attribution, is decided in stage 2.

## 5. Palace packaging: native renderer or downstream plugin

This is the maintainer's decision. Both options need the stage-1
abstractions, the same runtime (gmsh through `[mesh]`, plus the Palace binary
and MPI installed outside pip), and the same tests. They differ in where the
Palace-specific code lives and who versions it.

| | Native renderer in core | Downstream plugin (e.g. `quantum-metal-palace`) |
|---|---|---|
| Code | `renderers/renderer_palace/`: config builder, runner, readers | A separate repository and package |
| Python dependencies | None beyond `[mesh]`; an optional `[palace]` extra only if a helper needs one | Depends on `quantum-metal>=<release with the stage-1 modules>` |
| Registration | An entry in `config.renderers_to_load`, like `elmer` | Either (i) the plugin adds itself to `config.renderers_to_load` on import, which works today but must happen before the design is created; or (ii) core adds entry-point discovery, a new public contract (group name, metadata-only scan, a failing plugin skipped with a log line) |
| Capabilities | In the core registry and the docs table | Declared on the plugin's renderer class; the docs table lists it when installed |
| API stability | Stage-1 modules can change together with the Palace code | Stage-1 modules become a public API for another package, needing a deprecation policy |
| Palace config schema changes | Tracked in Metal releases | Tracked in plugin releases |
| Tests | Tier 0 in Metal CI (config from a tagged fixture, readers on checked-in CSVs); tier 2 locally | The same tests in the plugin's CI; Metal's cross-backend tests need the plugin installed |
| Tutorials | In `docs/tut/`; stored outputs from local runs | In `docs/tut/` with an install note, or in the plugin's docs; the docs build does not execute notebooks either way |
| Code derived from SQDMetal / pyPalace | Carried in Metal with license headers and attribution | Carried in the plugin |

## 6. Implementation sequence

Stage 1 consists of small, separately reviewable changes. Each is tier 0: it
runs in seconds, needs no solver binary, and writes nothing under `docs/`.
None changes a stored notebook output.

| Step | Change | Evidence it is right |
|---|---|---|
| 1.0 (done) | Fix the junction size field in `QGmshRenderer.define_mesh_size_fields`. | `tests/test_gmsh_mesh_size_fields.py`: the junction field lists the junction curves and uses `max_size_jj`. With `skip_junctions=True` (tutorial 4.19's Elmer path) the mesh is node-for-node the same as before. |
| 1.1 (done) | `problem.py`: ports, junctions, pins, boxes, boundaries, `MeshSpec`, studies; `from_run_args` / `to_run_args`; `validate()`; SI values. No caller yet. | `tests/test_simulation_problem.py`: round trips of the argument lists of the analysis tutorials (4.02, 4.03, 4.14, 4.16–4.18, 4.22, 4.23, A.4, A.7, pyaedt multiplanar); every error reported by `validate()`; studies from the three default setups. |
| 1.2 | `capabilities.py` with entries for `hfss`, `q3d`, `aedt_hfss`, `aedt_q3d`, `elmer`, `gmsh`; the study-type check in the three simulation classes; `capability_table()`. | `EigenmodeSim(design, "elmer")` gives the new message; every existing Ansys call path is unchanged (tests with a stub renderer). |
| 1.3 | `toolbox_metal/nets.py` (moved from `QElmerRenderer`); `QElmerRenderer` calls it; label styles. | The same `nets` dictionary as today on the 4.19 design and the two-qubit cell. |
| 1.4 | `renderer_gmsh/groups.py` and `QGmshRenderer.group_map`; opt-in per-side outer faces. | Every tag in `physical_groups` appears once in the map; the Elmer `.sif` and `.msh` are unchanged with defaults. |
| 1.5 | `MeshSpec` compiled by `QGmshRenderer`; today's options become the default spec. | Identical field list and parameters for the default spec; role-selected refinements tested on the fixture. |
| 1.6 | Port and junction geometry (sheet, line, CPW pair, wave-port face) in `QGmshRenderer`, registered as `PORT` / `JUNCTION` groups; endcaps at any pin angle. | Sheet geometry against pin `middle`/`normal`/`width`/`gap` at 0°, 90° and 45°. |
| 1.7 | `materials.py`: material options and their resolution; `QElmerRenderer` reads the options instead of its hard-coded list. | The Elmer `.sif` is unchanged for default options; setting `sim.model.materials.silicon.eps_r` or a sapphire layer changes εr; an unresolved material name raises. |
| 1.8a | In pyEPR: a public array entry to `QuantumAnalysis` (frequencies, Q, L_j, C_j, signed p_mj), with its own tests there. | pyEPR's tests: an analytic single-junction case gives the known anharmonicity; an existing HFSS data file reproduces the same results through the new entry. |
| 1.8 | `results.py`, the `SolverBackend` protocol, the neutral path in the simulation classes and `EPRanalysis` (through 1.8a). | A fake backend returning an analytic LC circuit gives the known frequency, capacitance matrix and χ through the public classes. |
| 1.9 | Stage 3: the written contract (a section of `renderer_protocol.md`) and the generated capability table in `docs/simulation-pathways.rst`. | The docs build renders the table from the registry. |

Stage 2, on these abstractions:

1. **scikit-fem** (`renderer_name="skfem"`, pip-only, runs in CI). Move the
   solvers into `src/` behind an extra and read `group_map`.
   - Tier 0: the empty box on a coarse mesh against TM110.
   - Tier 1: small-mesh 4.4x problems against reference values extracted
     from the stored outputs (`tests/solver_references/`).
2. **ElmerFEM eigenmodes.** Use Elmer's edge-element solver in eigen mode,
   with junctions as lumped elements; the mechanism in Elmer is to be
   confirmed. Cross-check against scikit-fem on the 4.19 cell and the 4.43
   package.
3. **Palace**, packaged as decided under D2. The first slice is eigenmode
   with one lumped port on a transmon, a launch pad and a CPW, compared with
   stored HFSS output. Tier 2, local only.
4. **Ansys.** Only its registry entry changes. Code changes stay on the
   Ansys track.

## 7. Testing

The tiers are those in `ROADMAP.md`, "Testing solvers without losing the
stored answers". Stage 1 adds only tier-0 tests. The regression anchors are:

- the ElmerFEM `.sif`, the `.msh` physical groups and the `nets` dictionary
  for the tutorial 4.19 design, rendered with default options and compared
  with today's output;
- the `QGmshRenderer` field list for default options;
- round trips of every tutorial's `run_sim` arguments;
- a fake backend for the neutral path.

Stored notebook outputs remain the reference answers. No test executes or
rewrites a notebook in place.

## 8. Decisions

Taken (September 2026):

- **D1. How simulation classes reach a new backend:** the neutral protocol N,
  next to the untouched legacy path (3.12).
- **D3. Net labels for capacitance results:** the `q3d` style
  (`{geom}_{component}`, `ground_{chip}_plane`, alphabetical order). Elmer's
  labels stay available as a style.
- **D4. Materials:** every material property is an option (3.7). Silicon's
  default εr is 11.45. Loss tangents, conductivities and interface layers
  have no defaults.
- **D5. The pre-run check:**
  - an error for a missing study, port, boundary condition or output;
  - a warning, recorded in provenance, for an ignored setting;
  - the study type only, on the legacy Ansys path.
- **D6. EPR numerics:** they stay in pyEPR.
  - pyEPR gains an array-based entry to `QuantumAnalysis` (step 1.8a), and
    pyEPR is updated as needed for it.
  - pyEPR imports without Ansys. It becomes a dependency of the open
    backends' extras, or of a small `[epr]` extra.

Open:

- **D2. Palace packaging:** native renderer or downstream plugin (section 5).
