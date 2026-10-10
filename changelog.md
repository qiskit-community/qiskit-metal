# Changelog Note Scratchpad for Developers

This log is used by developers to jot notes.

For the offical user-facing changelog for a particular release can be found in the correspondent Github release page. For example, you can find the changelog for the `0.0.4` release [here](https://github.com/Qiskit/qiskit-metal/releases/tag/0.0.4)

The changelog for all releases can be found in the release page: [![Releases](https://img.shields.io/github/release/Qiskit/qiskit-metal.svg?style=popout-square)](https://github.com/Qiskit/qiskit-metal/releases)

## Unreleased

Fixes for issues #1202–#1234: analytic formulas (transmon, LOM, kappa, chi,
package modes, resonator fitting), GDS export, design-rule checks, routing,
and tutorials. Several fixes change numbers or geometry; see *Behaviour
changes*.

### Behaviour changes

- **`RouteMeander` now reaches `total_length` when its leads are jogged or its fillet/spacing pair left it short** (#1225, #1234). `make()` refits the meander (up to 8 secant steps) when the first build misses by more than 1e-4 design units, and warns with both lengths when it still cannot. A `total_length` shorter than the shortest possible route draws that route and warns with its length, where it raised `IndexError` before. Routes that already reached `total_length` are unchanged bit for bit; routes that were short change shape on existing chips.
- **`ReadoutResFC` etches on its own layer** (#1224). `layer_subtract` now defaults to `""` (same as `layer`); it defaulted to `"2"`, so the GDS ground ended up on layer 2 while the trace was on layer 1. `layer_subtract="2"` gives the old output.
- **GDS cheesing drops holes that cross the no-cheese region** instead of trimming them into slivers narrower than the spacing rule (#1214). Fewer holes along the keep-out edge; holes that only touch it are kept.
- **Design-rule checks on `DesignFlipChip`** (#1212). Overlap and spacing rules group geometry by chip and layer; `ChipBoundsRule` and `GroundContinuityRule` default to `chip=None` (every chip in `design.chips`) instead of `"main"`. Planar results and messages are unchanged.
- **`QGDSRenderer` `path_filename` defaults to `None`** (#1223). The old default, `'../resources/Fake_Junctions.GDS'`, was relative to the working directory and the file is not in the package, so outside the tutorial folders the export already had no junction cells, with a warning per chip. Now an export with junctions and no `path_filename` logs one warning saying the junction geometry is left out and how to set a junction GDS file; a missing file is reported with its absolute path; `path_filename = None` no longer raises `TypeError`.
- **`constants.phinot` is h/2e to full precision** (#1207). It was 2.067e-15 (4e-4 low), which shifted `Ej_from_Lj` f01 by about −2.3 MHz for a 5.4 GHz transmon; LOM 1.0 mixed the two values. Stored outputs of tutorials 4.01, 4.11 and 4.21 move in the fourth digit.
- **LOM 2.0 two-node transmission-line resonators carry the sign of the mode at each end** (#1219). Bus-mediated and direct couplings now add with the correct relative sign, which changes J in designs with both paths. The term between the two ends of one line (`C⁻¹[b1, b2]`, non-zero when the ends are capacitively linked) is now added once; it was added twice. The `TL_RESONATOR` docstring states the single-mode limit: through a two-node bus the omitted higher modes reduce J (+15 % single-mode error in the #1219 circuit).
- **`kappa_in` returns κ/2π in Hz** (#1204). It used f where the formula needs ω, so values were off by (2π)²; the six-argument form now computes the resonance frequency correctly and uses the λ/4 prefactor.
- **`import qiskit_metal` no longer calls `logging.captureWarnings(True)`** (#1229). Python warnings from other libraries were routed to a logger with no handler and disappeared; they print again. **The `metal` logger defaults to INFO (was DEBUG), and a renderer skipped for a missing optional dependency is logged at DEBUG** (was INFO, one line per renderer for every new design). The reasons are in the new `design.skipped_renderers` dict and in the `ValueError` an analysis raises for that renderer; `qiskit_metal.logger.setLevel(logging.DEBUG)` shows the lines again. The GUI log shows INFO and above from `metal`, as the console does.
- **`Hcpb.n_ij` and `Hcpb.n_to_qutip` return the signed charge matrix elements** (#1221). They returned `|<i|n|j>|`, which at ng ≠ 0, ½ gives the wrong sign of gauge-invariant products such as n01·n12·n20 (−0.0354 at Ej/Ec = 5, ng = 0.25) and so a slightly wrong coupled spectrum. Eigenvector signs now follow a fixed convention (`<k|n|k+1> > 0`, ground state's largest charge component positive), which also fixes the signs of `evec_k` and `psi_k`. Magnitudes are unchanged; `n_to_qutip(thresh=...)` compares `|n_ij|`.
- **`QAnalysis.run_sweep` returns code 7 when any run fails** (#1230), with the error recorded under `'error'` for that value; it returned 0. **Simulations raise `ValueError` at construction when the renderer is unavailable** (unknown, misconfigured, or not started because its optional dependency is not installed), naming the available renderers; they returned `None` and failed later with `AttributeError`. `LOManalysis(design)` with no renderer is unchanged.
- **`fit_transmission`** fits the raw S21 with a free cable delay, after using the detrended data only for starting values (#1209). Q is unbiased for narrow spans and cable delays (it was +11 % at ±6 linewidths and failed at 40 ns). `amplitude_complex` and `delay` refer to the absolute-frequency model stated in the docstring. A tilted |S21| baseline is not in the default model and biases Qr and Qc (about +0.25 % for a 2 % tilt across the span, +0.55 % for 5 %). The new opt-in `baseline_slope=True` multiplies the model by a real linear baseline `(1 + k (f - fr))` and fits `k`; Q is then unbiased for 2 % and 5 % tilts, with and without cable delay. With the option on, `full_output` returns 8 parameters (`baseline_slope` last) and the dict gets a `baseline_slope` key; the default output is unchanged.
- **`design.to_python_script()`** opens the viewer with `qiskit_metal.gui(design)` (headless fallback on lite installs), keeps the design class, and restores chips and variables (#1205).

### Fixed

- **Transmon analytics:** `HO_wavefunctions.wavefunction` uses ω = 1/√(LC), is normalized and works for any n (#1202); `Hcpb.params_from_freq_fixEC` returns an Ej that reproduces f01 (#1203); `Hcpb.params_from_spectrum` fits a residual vector and warns when the target is unreachable (#1221); `Hcpb_analytic` and `transmon_analytics` use `mathieu_b` for odd levels and handle any ng (#1220).
- **`lumped_capacitive.chi`** documents its convention (Koch's χ) and approximations; a new optional `g12` uses the exact 1–2 matrix element, which brings χ within ~2 % of full diagonalization for Ej/Ec ≥ 30. The default (g12 = √2 g) is unchanged (#1208).
- **`analyze_loaded_tl`:** a shorted single-ended line is solved for its λ/4 mode, not 3λ/4 (#1206); the caller's `cap_loading` dict is no longer modified (#1232); the short is treated exactly instead of as a 1e30 fF capacitor, removing ~1e-4 noise in Q_zpf and a wrong-mode root for heavily loaded two-ended lines (#1233).
- **LOM:** `run_lom` passes `res_L4_corr` (#1210); bus–bus coupling uses C12·√(ω1ω2)/(2√(C1C2)); `extract_transmon_coupled_Noscillator` takes `Q_res` and `Z0` (also `LOManalysis.setup.Q_res` / `.Z0`) and always returns `T1`/`T1bus`, appended after the existing keys and columns; without `Q_res` they use the placeholder Qs (1e4 readout, 1e5 bus) and a warning says so (#1222). Bus–bus g values print about 1.6× the old value.
- **`package_modes.lsm_mode`** finds the lowest LSM root for small boxes (ValueError below ~4 mm, a higher mode at 2 mm); `lsm_mode_approx` warns outside its thin-slab validity (#1211). The paper device of tutorials 4.41–4.45 is unchanged.
- **GDS:** `fabricate=True` with cheesing no longer leaves dangling cell references (#1218).
- **Validation:** `ShortSegmentRule` has a float tolerance and reports each path once (#1213).
- **`draw.buffer`** passes `quad_segs` to shapely (no DeprecationWarning on shapely ≥ 2.1) (#1228).
- **No pandas `FutureWarning` ("DataFrame concatenation with empty or all-NA entries is deprecated") from building a design, GDS export, `metal_geometry_table`, the chip-bounds helper or `QDesignCheck`** (seen after #1229 stopped hiding warnings). The qgeometry tables are concatenated with a new `toolbox_python.utility_functions.concat_tables`, which gives the pandas 2 dtypes on pandas 2 and 3. Results are unchanged on pandas 2; on pandas 3 the `fillet` column of the `path` table and of the tables built from it is float64 again (it became object).
- **Connection pads added after construction** (`options.connection_pads.new = ...`) rebuild correctly (#1226); `to_python_script()` no longer writes a spurious `options_connection_pads` warning for every qubit (#1227).
- **`sequencing`** missing now raises an `ImportError` that says how to install it (#1231). `sequencing` 1.2.0 (2022, written for qutip 4) now runs on qutip 5: on import, `lom_extensions` replaces its two solver calls (`CompiledPulseSequence.run` and `.propagator`) with qutip 5 equivalents, and wraps three `System` methods that used `Qobj.data.nnz` (`_sequencing_compat`). Nothing is applied with qutip 4 or a newer `sequencing`. Tutorial 4.05-with-sequence runs end to end again; its stored outputs reflect the current LOM χ matrix.
- **Tutorials 4.04, 4.15 and 4.31–4.34 re-executed** with the fixed formulas (4.04: transmon EJ 13278.8 MHz, was 13268.1). 4.34 uses a converged charge cutoff for its transmon (`nlevels=15`; `nlevels=3` printed α/2π = +11 MHz), evaluates T2 = ħ/(Aπ|ε1|) as stated (the code was π² too long), and explains the `params_from_spectrum` result; 4.15 states that `kappa_in` returns κ/2π (6.4 MHz for its 30 fF example) and drops an unused `MetalGUI` import, so it now runs in the lite-install notebook job.
- **Tutorials:** example 52's readout resonators are quarter-wave (`open_termination=False`) (#1217); the CR-gate and Jaynes-Cummings tutorials pass `e_ops` by keyword for qutip 5.3 (#1216); tutorial 2.24 shows that an airbridge over an uncut crossing still reports, and how to cut and wire through it or waive it (#1215).
- **CR-gate tutorial** (#1216): the simulation now shows the conditional (ZX) dynamics. Two three-level transmons with a bus-mediated J; the control is driven at the dressed target frequency; the target's Bloch components are plotted for the control in |0⟩ and |1⟩; ZX, IX and ZI come from an exact block-diagonalisation and are compared with the leading-order formulas, with a check against an explicit bus. In the layout, the meander joins the `bus_01` pads (10.5 mm) instead of the `readout` pads.


## Quantum Metal v0.9.0 (open-source FEM solver, shape DRC, Python 3.13/3.14 and numpy 2)

Minor release: the gmsh + scikit-fem Maxwell solver and the package-mode
tutorials (4.41–4.45); shape rules in the design-rule check; new components
(`PolylineCPW`, `CapFingerInFrame`, `TransmonStar`) and two reference chips; the
first shared solver-backend abstractions (nets, physical groups, mesh
refinement, ports) for the gmsh renderer; every tutorial in one tree under
`docs/`; Python 3.13/3.14 and numpy 2; and analysis, renderer and tutorial
fixes. The dependency minimums move up (see *Upgrade notes*). No API removals.

### Added

- **Python 3.13 and 3.14 support.** `requires-python` is now `>=3.10,<3.15`. Until now every release since 0.5.2.post4 declared `<3.13`, so `pip install quantum-metal` on 3.13/3.14 silently resolved to 0.5.1. CI tests 3.10–3.14 on Linux and 3.10 + 3.14 on macOS/Windows. Based on #1182 by @PositroniumJS. (closes #1029)
- **`LumpedElementsSim.save_capacitance_matrix(path)`** saves the capacitance matrix to a CSV of your choice, with the units in the header cell. (#1017)
- **The scikit-fem Maxwell solver of tutorials 4.41–4.45 is part of Quantum Metal**: `qiskit_metal.analyses.fem` (package mesher, `MaxwellFEM` eigenmodes with lumped junctions, `PortROM` port reduced-order model, `Electrostatics`) and `qiskit_metal.analyses.em.package_modes` (analytic LSM package modes, dipole estimate, two-mode circuit, impedance-matrix fit). The tutorials' `package_modes.py` keeps the paper's device and design and re-exports the rest; their results are unchanged. Install with `pip install "quantum-metal[skfem]"`, which brings gmsh and scikit-fem; ElmerFEM and Palace need only `[mesh]` (`pymetis`, optional, speeds up the sparse factorizations).
- **Ports and junction lines in the gmsh model.** `QGmshRenderer.ports` takes lumped ports (on a pin: a sheet across the end gap, or two sheets across a CPW's side gaps, or a line; or on an explicit segment) and wave ports (a face on an outer wall), each with its own physical group that records its name and voltage direction (`group_map`); a lumped port's pin gets an endcap. `options.junction_lines` embeds each junction's line as a 1D entity for edge-element solvers. Open-pin endcaps now work at any pin angle (they assumed pins along x or y). Without ports the mesh is unchanged.
- **`QGmshRenderer.mesh_spec`**: refine the mesh by role, net, component, around a junction (a ball) or in a box, on top of the `mesh` options, with sizes in design units or strings with units (`analyses.simulation.problem.MeshSpec`, `Refine`, `Select`). Its `max_size` / `min_size` override the options. Without a spec the mesh is unchanged.
- **`QGmshRenderer.group_map`**: every physical group of the rendered model with what it is (conductor, ground, dielectric, vacuum, junction, outer wall), its component and shape, its net label and its layer's material, so solvers select groups by role instead of by name. `options.outer_face_groups=True` adds one group per outer wall. Default output is unchanged.
- **Simulation classes check the renderer before running.** `EigenmodeSim`, `LumpedElementsSim` and `ScatteringImpedanceSim` raise `BackendCapabilityError`, naming the renderers that can run the study, when the chosen renderer cannot (e.g. `EigenmodeSim(design, "q3d")`, `LumpedElementsSim(design, "elmer")`); these failed with an `AttributeError` inside the renderer before. What each renderer can do is declared in `analyses/simulation/capabilities.py` (`capability_table()` prints it).
- **`PolylineCPW`** (`qlibrary.tlines`): a CPW drawn along an explicit list of points, with no routing -- for paths you already have (traced, exported, octilinear). `taps={name: [x, y]}` adds pins partway along the line for branches, so a mid-line joint is a registered connection instead of a DRC waiver.
- **`CapFingerInFrame`** (`qlibrary.lumped`): a single-finger gap capacitor, a frame electrode around a finger, tuned per instance by its length.
- **`TransmonStar`** (`qlibrary.qubits`): `TransmonCross` generalized to `num_points` radial arms; arms without a connection pad stay bare stubs.
- **`Airbridge` pins `a`/`b`** for signal crossovers: cut the upper line and connect the cut ends to the bridge.
- **`StarQubit.rotation_jj`** places the junction independently of the couplers (same convention as the connector rotations). The default `'auto'` keeps the old placement.
- **Shape rules:** `SelfIntersectionRule`, `SharpTurnRule`, `FilletStarvationRule` and `PinAlignmentRule` (a line must leave the pin it connects to square-on) now run by default. `DanglingEndRule` (an unconnected CPW end fabricates as a short) is opt-in, because it also reports unused qubit pad stubs: `validate(design, rules=[*DEFAULT_RULES, *SHAPE_RULES])` runs all of them, each once.
- **`QComponent.to_html()` and a Jupyter HTML view.** A component shown in a notebook now renders as a table of its options -- nested groups indented, each option's description parsed from the `Default Options:` sections of the class docstrings, optionally the parsed values -- and a table of its pins with their position, direction, width and what each connects to. Options changed from the class defaults are highlighted (hover a name for its default), and a picture of the component is included, drawn off-screen so it is safe headless and next to the desktop GUI. Readable in light and dark themes. `to_html(docs=..., parsed=..., pins=..., image=...)` selects the sections; `to_html(display=True)` shows the card directly. Renderer options such as `hfss_inductance` are documented through a new `QRenderer.element_table_docs`.
- **HTML views for a design and its component list** (`design._repr_html_`, `design.components._repr_html_`), and `design["Q1"]` / `"Q1" in design` as shorthand for `design.components`.
- **Simulation pathways page** (`docs/simulation-pathways.rst`): what Ansys HFSS/Q3D, gmsh + ElmerFEM and the gmsh + scikit-fem solver each compute, how to install them and which tutorials use them; AWS Palace through SQDMetal, with the native integration tracked in sqdlab/SQDMetal#67. Every tutorial that runs a solver links to it from a short callout (markdown only; stored outputs unchanged).
- **Tutorials 4.41–4.45: package modes and qubit couplings.** Reproduces R. Molavi *et al.*, arXiv:2609.22442: a 10 × 10 transmon array in a metal package, its LSM package modes, and the qubit–mode couplings extracted four ways (avoided crossing, energy participation, induced EMF, impedance-matrix fit). The design is a `MultiPlanar` Quantum Metal design, meshed with gmsh; the eigenmode, driven and electrostatic solves use the scikit-fem finite-element solver in `qiskit_metal.analyses.fem` (lowest-order Nédélec elements, a port reduced-order model for junction sweeps and impedance matrices). 4.41 and 4.42 need only NumPy and SciPy; 4.43–4.45 need the `[skfem]` extra (and optionally `pymetis`). The series is featured after the Overview on the tutorials page.
- **Two-qubit cell notebook:** a cell of the 17-qubit chip (two qubits and their coupler) built as its own cropped design and meshed with gmsh; the ElmerFEM capacitance step runs where `ElmerSolver` is installed.
- **DRC waivers:** `validate(..., waivers=[Waiver(...)])` accepts named exceptions with a reason and an optional bound; waived findings are reported separately.
- **Example designs:** a 17-qubit distance-3 surface-code chip (Wallraff group, ETH Zurich; Krinner *et al.*, Nature 2022) built stage by stage with a design-rule check after each stage, GUI or headless; and a 5-qubit Xmon processor (Barends *et al.*, Nature 2014), adapted from a Quantum Device Workshop 2026 project by Murat Can Sarihan.
- **Docs:** keycap-badge GIFs on the GUI shortcuts page; QDesignOptimizer (202Q-lab, Chalmers) on the ecosystem and videos pages.
- **Six more notebooks on the docs site**, modernized and re-run: the three published iSWAP full chips, the flip-chip tutorial, the A.7 IMS 2022 workshop, and the three pyaedt `MultiPlanar` notebooks (driven modal, Q3D, eigenmode). Cells that need Ansys carry the `requires-ansys` tag and are shown without outputs; everything else has stored outputs.

### Fixed

- **`ResonatorLumped`: `n_turns` and `inner_space` now take effect, and the trace stays connected.** The meander was hard-coded to 14 U-turns, so both options were ignored. Its lines were offset by `res_width` while its bends used `perimeter_thickness`, and the last bend assumed `initial == turn_radius`, so changing any of those split the trace into up to 27 disconnected pieces. The meander is now built from `n_turns` (default now `14`), `turn_radius`, and `inner_space`, which is the edge-to-edge gap between lines (default now `0.19mm`). Default geometry is unchanged (within 1 nm). The component warns when the trace overlaps the perimeter, or when `final` ends inside the box.
- **`LumpedElementsSim()` / `EigenmodeSim()` without a design no longer connect to Ansys on construction.** The design-less path created the renderer with `initiate=True`, so building a simulation object just to load a saved matrix failed off Windows. It now matches the design path (`initiate=False`); `run_sim()` still starts the renderer. An unknown `renderer_name` without a design now logs an error instead of raising `AttributeError`.
- **Pin names documented.** Seventeen components (the three tees, both tunable couplers, `CapNInterdigital`, `Cap3Interdigital`, `ResonatorCoilRect`, `NSquareSpiral`, `TransmonInterdigitated`, `StarQubit`, both concentric transmons, `TransmonCrossFL`, `ResonatorLumped`, and the three launchpads) now list their pins in a `Pins:` section. A test checks that every pin created at default options is named in its class docstring.
- **Elmer capacitance matrix was wrong under pandas 3.** Two chained assignments in `QElmerRenderer._get_capacitance_matrix` are no-ops under Copy-on-Write (pandas 3's default, which pip installs on Python 3.11+), leaving the diagonal unconverted and the ground entry NaN with only a warning. Now `.iloc`/`.loc`.
- **`DesignPlanar()` crashed when gmsh was installed but could not load** (e.g. `libGLU.so.1` missing on headless Linux): the import guards only caught `ImportError`. The gmsh renderer is now skipped, and using it explains which system library failed to load.
- **Clear errors instead of cryptic ones:** `QElmerRenderer.add_solution_setup()`/`run()` without `render_design()` on the same renderer (was `AttributeError: nets`, #1008); ElmerSolver crashes (was a later missing-file error; now raises with the log tail, #1005); a layer/datatype missing from the layer stack (was `TypeError: Dict / int` in the pyaedt renderer, #992).
- **Non-string geometry names.** `add_qgeometry` coerces dictionary keys to `str`, so e.g. `{0: jj_line}` no longer breaks the HFSS renderer's name sanitiser or MultiPolygon splitting. (#995)
- **`LOManalysis.run_lom()` with a user-supplied matrix.** Setting only `sim.capacitance_matrix` (as the method's own warning suggests) raised `KeyError: 0`: an inverted type check never filled the per-pass data. It now uses the matrix as the single pass, converted from `sim.units` (default fF) to farads.
- **Lite installs: `load_q3d_capacitance_matrix()` no longer needs IPython/jinja2** to print the matrix; it falls back to plain text.
- **Docs:** `Subsystem` energies (`EJ`, `EL`, `EC`) are in MHz, not GHz (#920); `TransmonPocketCL` documents its `Charge_Line` pin (#989).
- **Tutorials that failed on a fresh kernel.** Fifteen notebooks (3.5, 4.02–4.05, 4.11–4.14, 4.19, two Hamiltonian-model notebooks, and two Appendix B topics) lost their import cells when `%autoreload` was stripped in 6512e0d, and raised `NameError` at the first cell that used `designs`, `MetalGUI`, etc. The import cells are restored; stored outputs are unchanged.
- **Tutorial 4.02: junction now follows `sim.setup.vars.Lj`.** Section I links the qubit's `hfss_inductance`/`hfss_capacitance` to the `Lj`/`Cj` design variables, so HFSS and the EPR step use the same junction inductance. (#1019)
- **scqubits < 4.2 failed under numpy 2 outside LOM 2.0**, e.g. `Transmon.wavefunction()` in tutorial 4.34 raised `AttributeError: np.complex_ was removed`. scqubits 4.1 builds arrays with `np.float_` / `np.complex_`, and it is what macOS resolves next to a current scipy (scqubits 4.2+ caps scipy at 1.13.1 there). Only the LOM 2.0 path restored the two aliases; `import qiskit_metal` now does, when the installed scqubits is older than 4.2. With scqubits 4.2+ nothing changes.
- **Tutorial 2.14's third route doubled back over itself**, as the new self-intersection rule found: from its anchor at y = -1.5 the pathfinder could only leave back along the route's own first leg. The anchor is now at y = -1.25. The chip is also 13 mm wide instead of 9 mm, so the two qubits at x = ±5 mm and the routes that wrap around them are inside it.
- **ElmerFEM mislabeled shapes after a component was deleted.** `QElmerRenderer` found a component's name from its id by position in `design.components`, so once a component had been deleted, shapes were named after the wrong component and `add_solution_setup` failed with a `KeyError`. Net assignment now lives in `toolbox_metal/nets.py` (shared by the solver backends), with the correct id-to-name map; results for designs without deletions are unchanged.
- **pyaedt HFSS renderers drew nothing unless `port_list` and `jj_to_port` were both given**, so `QHFSSEigenmodePyaedt`, which accepts neither, drew nothing at all. A lint cleanup (ruff E712) had turned the assignments `port_list_is_valid = True` / `jj_to_port_is_valid = True` in `QHFSSPyaedt.valid_input_arguments` into no-op expressions: an omitted list left its flag `None`, and `render_design()` stopped with "Check the arguments to render_design". The assignments are restored (checked by reading the code and by a test on a stub; not yet run in AEDT).
- **HFSS renderer: ports without `open_terminations` raised `TypeError`** (`None + list` when adding endcaps), e.g. `ScatteringImpedanceSim.run_sim(port_list=[...])`. The port pins now get endcaps on their own.
- **Ansys setups ignored an explicit `False` or `0`.** The COM and pyaedt setup functions (`add_q3d_setup`, `add_eigenmode_setup`, `add_drivenmodal_setup`, and the pyaedt `add_q3d_setup`, `add_hfss_em_setup`, `add_hfss_dm_setup`) filled defaults with `if not x`, so e.g. `LumpedElementsSim.setup.auto_increase_solution_order = False` or `enabled = False` was replaced by the default `True`, and `basis_order = 0` by the default order. Only `None` now means "use the default".
- **HFSS renderer drew port sheets at z = 0.** `create_ports` placed each port's sheet and voltage line at z = 0 whatever the chip's `center_z`, so on a raised chip (flip-chip) they missed the metal. They now sit at the chip's z, as the component's endcaps and junctions already did. Designs with `center_z = 0` are unchanged.
- **pyaedt renderers: the autosave options had no effect, and closing turned AEDT autosave on.** `_initiate_renderer` read a misspelled option (`begin_enable_autosave`), so autosave was never turned off, while `_close_renderer` enabled it unconditionally, including for users who keep it off; the setting is an AEDT user preference that persists after the session. The renderer now records the setting (`oDesktop.GetAutoSaveEnabled`), turns autosave off while it works, and on close turns it back on only if it was on, the pattern pyaedt uses around its own long operations. Checked against pyaedt 0.23.0 and 1.7.0 (the two locked versions); not yet run in AEDT.
- **pyaedt `QQ3DPyaedt.render_design()` without `open_pins` raised `TypeError`** while checking the pin names.
- **pyaedt `QHFSSEigenmodePyaedt.analyze_setup()` raised `AttributeError` for a setup that did not exist yet**: it called the driven-modal `add_hfss_dm_setup`. It now adds an eigenmode setup.
- **Q3D per-pass capacitance matrices were labeled `fF` but held farads** (`get_capacitance_all_passes`). The returned units are now `"farad"`. `LumpedElementsSim` and `LOManalysis` already treated the values as farads, so no result changes.
- **`QHFSSPyaedt.default_setup` was a one-element tuple** (a trailing comma); it is now the `Dict` it was meant to be. The subclasses define their own, so no run used it.
- **gmsh: `mesh.max_size_jj` had no effect.** `define_mesh_size_fields` built the junction distance field from every metal surface and wrote those curves to the metal-edge field, leaving the junction field empty. The junction field now measures distance to the junction edges. The metal-edge field is unchanged, so a design rendered with `skip_junctions=True` (the ElmerFEM capacitance path of tutorial 4.19) meshes exactly as before.
- **GDS export silently dropped cuts.** The ground plane was one chip-sized `gdstk` boolean; when gdstk could not link a hole it printed "Unable to link hole in boolean operation" and wrote that cut as solid ground (on a 17-qubit chip, three whole flux-line gaps). The ground and cheesing booleans now run in vertical strips, each checked against shapely and rebuilt when gdstk's result is wrong. Cheesing is also much faster.
- **Rebuilding a component dropped its connections.** `QComponent.rebuild()` (and `design.rebuild()`, and GUI edits) deleted the component's nets; only routes reconnected. Connections made with `design.connect_pins` are now restored, and a partner pin that cannot be reconnected is reset to net 0 instead of keeping a stale id.
- **Spikes along straight CPWs in the GUI and `qm.view`.** On a straight run the fillet's dot product could round past -1, `arccos` returned NaN, and the fillet was drawn as a sawtooth of spikes. The stored geometry was unaffected.
- **`StarQubit` left floating slivers of island metal** when two arms are close together (e.g. a readout arm 45 degrees from a coupler); only the island part at the center is kept.
- **Ground-continuity rule fooled by nanometer slivers.** Floating-point booleans leave ground strips a nanometer wide where two etched edges almost coincide, joining regions no metal joins. `GroundContinuityRule(min_link_width=1e-4)` ignores links narrower than 0.1 um (`0` restores the exact check).
- **GUI: the left dock could not be narrower than ~430 px on macOS**, because the native style disables tab-bar scroll arrows; they are now enabled.
- **gmsh renderer: "Could not create circle arc"** on paths through nearly straight corners (as resampled or traced lines have): the path angle came from an unclipped `arccos`, and a corner bent by ~1e-6 rad got a fillet arc shorter than the rounding of its control points. Such corners are now drawn straight.
- **`cpw-gap` rule flagged gaps equal to the minimum** (a 3 um gap computed as 2.9999999999999996 um); it now compares with a 1e-9 mm tolerance.
- **Elmer capacitance solve failed unless `simulation_dir` sat directly below the working directory.** `run_elmergrid()` handed ElmerGrid `../<mesh_file>` and found its output with `meshfile.split(".")`; with a temporary `simulation_dir` (as the airbridge Elmer test uses) the solve stopped with `FileNotFoundError: 'out'`. ElmerGrid now gets absolute paths, a relative `mesh_file` lives inside `simulation_dir` (nothing is written to the working directory), and `run()` exports the mesh if `export_mesh()` was not called.
- **LOM 2.0 Hamiltonian step (`CompositeSystem.hamiltonian_results`) crashed** with two scqubits releases: scqubits 4.1 (what macOS resolves with a current scipy, because scqubits 4.2+ caps scipy at 1.13.1 there) uses `np.float_`, removed in numpy 2; scqubits 4.3.1 rejects the scipy sparse arrays qutip 5.3 returns (`TypeError: Unsupported operator type: csc_array`). `analyses/quantization/_scqubits_compat.py` restores the numpy aliases and has scqubits convert qutip objects to sparse matrices, each only when needed. A new test runs the chain end to end and checks the qubit against a bare `scqubits.Transmon`.
- **LOM 2.0 reported a wrong resonator self-Kerr** (a resonator's diagonal entry in the chi matrix): with the default three levels the two-photon state is the top of the retained space, which gave e.g. +0.57 MHz where the converged value is -0.0003 MHz. Qubit frequencies, anharmonicities and qubit-resonator shifts were unaffected. Resonators without an explicit `truncated_dim` now keep 5 levels when the whole Hilbert space stays within `CompositeSystem.max_auto_dimension` (4000) states, and 3 otherwise with a warning that their self-Kerr is not converged.
- **Importing LOM analysis replaced `h5py`** for the whole process with a dummy class (a 2021 workaround for a conda conflict); scqubits already treats h5py as optional, so the replacement is gone.
- **Pre-commit hook** split staged paths containing spaces (e.g. `tutorials/Appendix C ...`) into nonexistent files.

### Changed

- **`pyEPR-quantum>=1.0.2`** in `[ansys]` and `[full]`. pyEPR 1.0.1 raised `AttributeError` under numpy 2 at the end of a default EPR analysis (`print_result=True`, which the pyaedt eigenmode renderer passes) and could not read Q3D matrix exports under pandas 3; 1.0.2 fixes both.
- **numpy 2 supported; `numpy<2` cap removed.** The cap dated from a `pandas==1.5.3` pin: wheels built against numpy 1.x fail to import under numpy 2. Floors now sit at the first numpy-2-compatible releases: pandas 2.2.2, scipy 1.13.0, matplotlib 3.8.4, shapely 2.0.4 and pint 0.24.4 (older pint calls `np.cumproduct`; 0.24.0–0.24.3 also break with flexparser 0.4). numpy 1.x remains supported. pyyaml floor 6.0.1 (first with Python 3.12 wheels). Verified by running the suite at the lowest allowed versions under both numpy 1.24.2 and 2.0.0.
- **pyaedt pin is Python-version dependent.** `>=0.21,<0.24` on Python < 3.14 (unchanged), `>=1.0.1` on 3.14 only, because pyaedt 0.2x requires `numpy<2.3`, which has no 3.14 wheels. The pyaedt renderer has not been validated against AEDT with pyaedt 1.x.
- `math_and_overrides.cross` computes the 2D z-component directly; `np.cross` on 2-element vectors is deprecated in numpy 2. (@PositroniumJS, #1182)
- **Clearer legacy-LOM size error.** `extract_transmon_coupled_Noscillator` now reports the actual and expected matrix size, the required net order, and that only floating two-pad transmons are supported, pointing grounded qubits to the Cell/Subsystem/CompositeSystem API. (#1015)
- **`EigenmodeSim` warns when `setup.vars.Lj` can't reach the junction:** a rendered junction whose `hfss_inductance` is a fixed value different from `Lj` is simulated at that value while the EPR step reads `Lj`. Silent with defaults and when the junction is linked to the variable. (#1019)
- **`EPRanalysis` warns before a very large spectrum diagonalisation** (`fock_trunc**n_modes` > 20,000 states) with the estimated memory. (#1018)
- **Locked dependencies with known advisories updated:** anyio 4.14.2, click 8.5.0, jupyter-server 2.21.1, mistune 3.3.4, soupsieve 2.10 (all dev/docs/transitive; no runtime floor changes).
- **CI: two dependency-bound jobs.** `tests-deps-pandas3` runs the suite with pandas 3 (Copy-on-Write default), and `tests-deps-lowest` with every direct dependency at its declared minimum. Both install outside `uv.lock`, as pip users do.
- **GUI subprocess tests report the crash stack.** On a native crash in the child, failures showed only the last 2,000 characters of stderr, which faulthandler fills with its extension-module list. `tests/_crash_output.py` drops that list and keeps the fatal error and thread stacks. (#1048)

### Upgrade notes

- **Minimum versions raised:** pandas 2.2.2, scipy 1.13.0, matplotlib 3.8.4, shapely 2.0.4, pint 0.24.4, pyyaml 6.0.1, and pyEPR-quantum 1.0.2 (`[ansys]`, `[full]`). An environment pinned below these will need to upgrade them.
- **`ResonatorLumped`:** default geometry is unchanged, but designs that set `n_turns` or `inner_space` explicitly now get that geometry instead of the fixed 14-turn meander.
- **Python 3.14 + `[ansys]`** installs pyaedt 1.x, which has not been validated against AEDT with the pyaedt renderer.
- **`validate()` runs four more rules by default** (the shape rules above), so its report says "11 rules ran" instead of 7, and designs with a self-crossing line, a hairpin, a starved fillet or a line leaving a pin askew get new findings.
- **Tutorial notebooks moved to `docs/`.** The copies in `tutorials/` (names with spaces) are gone; every notebook now lives once, under `docs/tut/` or `docs/circuit-examples/`, with the hyphenated names the docs site already used. `tutorials/README.md` maps each old path to its new one. Input files the notebooks load (e.g. `Fake_Junctions.GDS`) are in `docs/tut/resources/`; a local `renderers_to_load` entry for the skeleton renderer becomes `docs.tut.resources.skeleton_renderer`.

## Quantum Metal v0.8.1 (GUI stability + interactive editing; no breaking changes)

GUI stability fixes for issue #1048 and interactive canvas editing (select, move, rotate, rebuild from the keyboard). Full notes: https://github.com/qiskit-community/qiskit-metal/releases/tag/v0.8.1

### Fixed

- **`TransmonCross` `connector_location='270'`** placed the connector on the east arm instead of the south arm. The rotation chain had no branch above 225 degrees, so 270 matched the `> 135` test. (#1173, closes #1052)
- **`connector_location` now wraps mod 360.** The chain saturated at its top branch, so out-of-range angles landed arbitrarily — `'360'` resolved to south rather than west, `'-90'` to west rather than south. In-range angles, including the half-way values 45/135/225, keep their existing arm.

### Changed

- **`TransmonCrossFL` warns when a connection pad resolves to the south arm** while `make_fl` is True. That arm carries the flux line, and the claw polygon overlaps it. The south arm also carries the junction on the base `TransmonCross`; at default options the claw clears it by ~11um, with the etch region within ~5um. Both constraints are now documented on the class docstrings.

## Quantum Metal v0.8.0 (airbridges + design-rule checking; no breaking changes)

Minor release: two new feature areas, one deprecation, and one default-behaviour
change to the matplotlib viewer. No API breaks. See *Upgrade notes*.

> **Skipped version: there is no 0.7.7.** A `v0.7.7` tag and GitHub Release exist
> on `a7efeeb1`, but that commit's `pyproject.toml` still read `0.7.6`, so the
> publish workflow built a `0.7.6` wheel and PyPI rejected it as a duplicate.
> Nothing was ever published under 0.7.7 — PyPI went 0.7.6 → 0.8.0. The tag is
> left in place rather than rewritten. Tag *after* the version bump merges; this
> is the same ordering that broke v0.6.0 (`.claude/commands/release.md`).

### Added (v0.8.0-only)

- **`Airbridge` QComponent + `route_airbridges` auto-placement.** Bridges are placed on the filleted centreline, idempotently, with `bridge_at_corners` to control corner behaviour. Tutorial 2.15 covers the flow end to end, including GDS export with coloured layers. (#1138, #1142)
- **Experimental 3D airbridges** via layer-stack elevation, with support posts so the route and its bridges connect in a 3D mesh, plus a ready-to-run Elmer capacitance path. (#1144, #1150)
- **`qiskit_metal.validation` — design-rule checking.** `validate(design)` returns a `ValidationResult` of structured `Finding`s; `strict=True` raises `DesignRuleViolation` for build scripts and CI. Seven rules with configurable thresholds: `metal-overlap`, `metal-spacing`, `cpw-gap`, `chip-bounds`, `short-segment`, `qubit-clearance`, `ground-continuity`. Rules are layer-aware (an airbridge crossing a CPW is not a short) and net-aware (a route abutting its own pin is not a short). Defaults follow published superconducting-chip rule sets where one exists; the one project heuristic is labelled as such. Tutorial 2.24 walks a deliberately broken design through detection, fix, threshold tuning, and writing a custom rule. (#1168, #1169)
- **Die outline in the viewer.** `QMplRenderer` draws each chip's extent, so `qm.view` and the Qt `MetalGUI` both show where the chip ends. (#1168)

### Fixed (v0.8.0-only)

- **`RouteMeander` sharp kinks** when `meander_number` is too tight for the requested geometry. (#1167, closes #1086)
- **`RouteMeander` `IndexError`** when the start/end-direction parity adjustment takes `meander_number` from 1 to 0, skipping the zero-meander early return. (#1168)
- **GDS export of routes with short lead segments.** (#1141)
- **Gmsh 3D render of routes with sub-width lead segments.** (#1144)
- **`design.to_python_script()` output** now starts a Qt event loop correctly across install variants. (#1159 by @saschabuehrle, hardened in #1160)
- **Reference designs 2 and 3** placed launchpads 1.76 mm and 3.26 mm outside the default 9×6 mm die, so a corner of ground plane was clipped on every render. Both now set an explicit chip size, and `tests/test_reference_designs.py` gates all three against the design rules. (#1168)

### Deprecated (v0.8.0-only)

- **`QDesignCheck`** — construction emits a `DeprecationWarning`. It detects only crossing outlines, so it misses an overlap where one trace sits entirely inside another, and it is blind to layers and to pin connections. Use `qiskit_metal.validation.validate` instead. The class keeps working; no removal date set. (#1168)

### CI / infrastructure (v0.8.0-only)

- `uv.lock` ↔ `pyproject.toml` consistency guard. (#1137)
- Ruff rule set pinned so a ruff release cannot break CI; the safely-fixable subset of ruff 0.16's expanded defaults adopted, plus a second tier. (#1161, #1163, #1165)
- Decision log for non-obvious choices and deferrals. (#1162, #1164)
- Flaky gmsh meshing test isolated. (#1165)

### Upgrade notes

No API changes. One visible default change: the matplotlib viewer now draws the die outline, and because the outline participates in autoscaling, a design whose components sit well inside the die is framed to the whole die rather than to the components. Pass `qm.view(design, chip_outline=False)`, or set `renderer.options.chip_outline = False`, for the previous framing.

`QDesignCheck` users will see a `DeprecationWarning`; behaviour is unchanged.

## Quantum Metal v0.7.5 (Windows GUI crash fix + routing/qubit fixes; no breaking changes)

Patch release. Additive — no breaking changes.

### Fixed (v0.7.5-only)

- **`MetalGUI` no longer crashes at `show()` on Windows** (the on-screen crash, distinct from the exit-teardown segfault fixed in v0.7.4). Root cause was **persisted-state corruption**: Metal saves window geometry / dock layout to the registry (`HKCU\Software\QiskitMetal\MainWindow`) on close, and after a display-configuration change (tablet-mode toggle, undock, DPI change on 2-in-1 laptops with WDDM 3.2) Qt's `restoreState()` handed `show()` an inconsistent widget tree that fast-failed (`__fastfail(7)`) at first paint — the "works on the first run, crashes after" pattern several Windows 11 users reported. Fix: persisted UI state is invalidated when the saved Qt version differs from the running one, and is **cleared** (not just logged) if restoration raises, so one bad shutdown can't brick every future session. Reporter-validated (6/6 clean runs). One-shot escape hatch: `QISKIT_METAL_RESET_UI_SETTINGS=1`. (#1122, closes #1048; builds on #1104 / #1110)
- **Auto-routing no longer passes straight through a component.** `RouteAnchors.unobstructed()` returned `True` when both segment endpoints lay inside a component's bounding box even though the segment crossed the actual (non-rectangular) contour, so routed paths could penetrate e.g. a circular pad. The contour is now checked in that case too. (#1113, closes #1036; reimplements the community fix #1038 by @Jinyuan426, with a regression test)
- **`design.to_python_script()` output is runnable again.** Exported `.metal.py` scripts that use numpy arrays now include `from numpy import array` in the header. (#1043 by @saschabuehrle, closes #1042)

### Added (v0.7.5-only)

- **`TransmonCross` non-uniform claw options.** New per-connection-pad `claw_width_back` / `ground_spacing_back` let the back of a claw connector (facing the incoming CPW) use a different width / ground spacing than the sides — e.g. MIT-LL "candle" qubits. Both default to `None` (fall back to `claw_width` / `ground_spacing`), so existing designs render byte-for-byte identically. (#1115; reimplements #957 by @clarkmiyamoto)
- **Windows Qt software-OpenGL default.** On Windows, `import qiskit_metal` sets `QT_OPENGL=software` before PySide6 imports (opt out with `QISKIT_METAL_QT_HARDWARE_GL=1`) — harm-reduction for fragile integrated-GPU / WDDM 3.2 driver stacks. (#1122)
- **Reference full-chip design tutorials.** Three executed, headless-rendered end-to-end examples — single transmon + readout resonator, two coupled transmons, and 4-qubit multiplexed readout — under *Tutorials → Full-Chip Design Examples* on the docs site. (#1108)

### Docs (v0.7.5-only)

- Component-gallery cards now deep-link to each component's own API page with real descriptions (registry-aware, so new components self-link). (#1108)
- `ROADMAP.md` now renders inline on the docs site as a single source of truth; site TOC restructured for clarity. (#1118–#1121)

### Security / CI (v0.7.5-only)

- Cleared 10 Dependabot advisories in the dev/docs toolchain (`starlette`, `bleach`, `jupyter-server`, `jupyterlab`, `tornado`) — lockfile-only, no runtime impact for installed users. (#1111)
- Hardened the CI `apt` setup against flaky third-party runner sources (azure-cli / Microsoft repos) that were failing jobs before any test ran. (#1112)
- Windows on-screen GUI init hardening + `QISKIT_METAL_DEBUG_INIT` diagnostic + a `tests-gui-display-windows` CI job. (#1110)

### Upgrade notes

No API changes; drop-in upgrade from 0.7.4. Windows users hitting the GUI crash: just upgrade — the fix is automatic. If a machine is already in a poisoned state, `QISKIT_METAL_RESET_UI_SETTINGS=1` (or deleting `HKCU\Software\QiskitMetal\MainWindow`) clears it once.

## Quantum Metal v0.7.4 (new SNAIL component + crash fixes; no breaking changes)

Patch release. Additive — no breaking changes.

### Added (v0.7.4-only)

- **`SNAIL` QComponent** (`qiskit_metal.qlibrary.qubits.SNAIL`) — a Superconducting Nonlinear Asymmetric Inductive eLement: a loop with three large Josephson junctions on one arm and one smaller junction on the other. Emits the four junctions to the `junction` qgeometry table (three large at `Lj`, one small at `Lj_small`) so it renders as lumped Josephson inductances under HFSS-eigenmode / pyEPR, and exposes pins `a`/`b` for routing. Default junction inductances and the documented physics (`alpha`, Kerr-free flux, `alpha < 1/n` constraint) are grounded in Frattini et al. 2017/2018 and Sivak et al. 2019. (#1100, closes #1099)

### Fixed (v0.7.4-only)

- **`EigenmodeSim.plot_convergences()` raised `NameError: plot_convergence_f_vspass`.** A prior lazify-imports refactor removed the `from pyEPR.reports import (...)` line from `analyses/simulation/eigenmode.py` on the mistaken belief the four plot helpers were unused — they are called inside the method. Restored as a lazy use-site import (keeps the no-pyEPR import path clean). (#1102, closes #1101)
- **`analyses/sweep_and_optimize/sweeping.py` was entirely unimportable.** `Sweeping._extract_min_passes` used an unquoted `Union[None, float]` return annotation without importing `Union`, so `class Sweeping` raised `NameError` at definition time. It went unnoticed because nothing in the package or tests imported the module. Added the missing `Union` import. (#1102)
- **`MetalGUI` segfaulted at interpreter exit** (in a Jupyter kernel: "the kernel appears to have died"). At finalization PySide6 destroyed the `QApplication` while the window was still alive, dispatching an event through the main window's `QMenuBar` event filter whose target was half-deleted → SIGSEGV. Fixed with a one-shot `atexit` handler that deletes top-level Qt widgets while the interpreter / `QApplication` are still alive. (#1104, addresses #1048)

### CI (v0.7.4-only)

- **`tests-gui-display`** — first CI job to launch the real on-screen Qt `MetalGUI` (under Xvfb), so GUI-lifecycle crashes like #1048 can't regress unnoticed. Every other job runs headless. (#1104)

## Quantum Metal v0.7.3 (Qt-mode polish + `qm.show_inline`; no breaking changes)

Patch release rolling up the v0.7.2 line. v0.7.2 was never tagged to PyPI; everything below shipped together as **v0.7.3**.

### Added (v0.7.3-only)

- **`qm.show_inline(fig)`** — backend-agnostic figure display. When the active matplotlib backend is interactive (`Qt6Agg` while the desktop `MetalGUI` is open, or `TkAgg` on some local installs), `plt.show()` opens a separate OS window rather than rendering inline in Jupyter. `qm.show_inline(fig)` saves to a PNG buffer and displays via `IPython.display.Image` — identical cell output in Qt mode and headless (Agg / inline) mode. Falls back to `plt.show()` when IPython is unavailable. Lives at `src/qiskit_metal/viewer/show_inline.py`; exported at top level.
- **`PlotCanvas.zoom_on_components(component_names)`** — the Qt canvas now mirrors `MetalGUIHeadless.zoom_on_components`: computes the bounding box of the named components with 10 % padding, sets the axis limits, refreshes the canvas.

### Fixed (v0.7.3-only)

- **`gui.highlight_components(...)` silently inert in Qt mode** — the canvas method at `mpl_canvas.py:692` appended rectangles + text to the axes correctly, but the resulting redraw was missing some Qt event-loop flushes. The visual highlight only appeared after a second manual `gui.refresh_plot()`. Fix: `canvas.refresh()` now follows `self.draw()` with `self.draw_idle()`, scheduling a redraw on the next event-loop tick so the annotations actually render on the first call. (Headless `MetalGUIHeadless.highlight_components` was unaffected — it draws synchronously.)
- **Double-click on a QComponents-table row crashed with `AttributeError: 'PlotCanvas' object has no attribute 'zoom_on_components'`.** The desktop GUI calls `gui.canvas.zoom_on_components([name])` on double-click; that method existed on `MetalGUIHeadless` but not on the Qt canvas. Added — see above.

### Highlights (carried from v0.7.2)



**Follow-up to v0.7.1** centered on making "lite Colab/Binder users" and
"desktop GUI users" walk the same tutorial path. v0.7.0 + v0.7.1 split
the install into lite vs full extras; v0.7.2 makes that split invisible
to the user. No breaking changes.

### Highlights

- **New `qm.gui(design)` factory** auto-picks the desktop `MetalGUI`
  (Qt) when PySide6 + a display are available, and a new
  `MetalGUIHeadless` (inline matplotlib) otherwise. The
  `MetalGUIHeadless` class mirrors `MetalGUI`'s tutorial-facing surface
  (`gui.rebuild()`, `gui.screenshot()`, `gui.edit_component(...)`,
  `gui.highlight_components(...)`, `gui.zoom_on_components(...)`,
  `gui.main_window`), so tutorial code is identical on Colab, Binder,
  headless servers, and the desktop. Detection covers
  `QISKIT_METAL_HEADLESS=1`, Google Colab, Binder env vars, Linux
  without `DISPLAY`, and missing PySide6.
- **Colab + Binder badges on every numbered tutorial and circuit
  example** — 90+ notebooks across `tutorials/` and
  `docs/circuit-examples/`. One click in the docs site → a running
  notebook in the browser via the lite install.
- **Section 1 tutorials restructured for hands-on flow**:
  1.1 Quick start (was: Bird's eye view), 1.2 Bird's eye view (was: 1.1),
  1.3 Build a 4-qubit chip (new — promoted from end of old 1.1),
  1.4 Saving & exporting (was: 1.3), 1.5 Parametric (unchanged).
  Old 1.4 Headless + 1.6 Shape library dropped (subsumed by `qm.gui`
  + the new gallery).
- **QComponent Gallery** (`docs/qcomponents-gallery.rst`) — visual
  catalog of every component shipped, grouped by category, each card
  linking through to autodoc. Auto-generated at every docs build from
  a single source of truth in `src/qiskit_metal/_gui/_imgs/components/`.
- **Tutorial CI gate**: 22 lite-runnable notebooks now execute on
  every PR via `_dev/rerun_auto.py`. Split into auto-refresh (17
  matplotlib-only) and frozen-Qt (5 with hand-curated Qt screenshots
  — CI verifies pass/fail without clobbering committed outputs).

### Added

- `src/qiskit_metal/viewer/headless_gui.py` — `MetalGUIHeadless` class,
  `_is_headless_environment()` detector, and the `gui()` factory.
  Exposed at the top level as `qm.gui` and `qm.MetalGUIHeadless`.
- One-time onboarding banner in `MetalGUIHeadless` explaining the
  active mode and how to install desktop GUI extras. Suppress with
  `QISKIT_METAL_HEADLESS_QUIET=1`.
- `qm.MetalGUI` is now a lazy attribute via `__getattr__`. `import
  qiskit_metal` no longer pulls in PySide6; the import only fires when
  Qt is actually requested. Clean `ImportError` on lite installs
  pointing at `pip install 'quantum-metal[gui]'` + the factory.
- Bottom-right corner watermark on headless figures: faint logo +
  "Qiskit / Quantum Metal" text (same spec as the desktop `MetalGUI`
  canvas), painted via an inset axes so it never offsets the parent
  `dataLim`.
- `open_docs(force=False)` — suppresses the browser pop in headless /
  CI / Linux-without-DISPLAY contexts; displays the URL as a clickable
  HTML link instead.
- `docs/qcomponents-gallery.rst` + `_dev/generate_qcomponent_gallery.py`
  — auto-generated visual gallery with grid-card layout per category.
- `docs/architecture.rst` + mermaid architecture diagram (also
  rendered natively on GitHub from `.claude/context/architecture.md`).
- Sphinx `builder-inited` hook in `docs/conf.py` regenerates gallery
  RST + thumbnail PNGs at every docs build. Adds `sphinxcontrib-mermaid`
  to docs deps.
- 7 scaffold icons (`base_qcomponent.png`, `base_qubit.png`,
  `user_template.png`, ...) so the MetalGUI Library pane no longer
  shows the globe placeholder for `core/` and `user_components/`
  classes.
- 22 auto-generated QComponent thumbnails for `Route*`, `Tunable*`,
  `Resonator*`, `ShortToGround`, `OpenToGround`, `ReadoutResFC` etc.
  `_dev/generate_qlibrary_thumbnails.py` renders default instantiations;
  `SPECIAL_RECIPES` covers components needing pins or anchors.
- `scripts/check_qlibrary_images.py` — CI gate that fails on broken or
  one-line `.. image::` directives in any component class.
- `_dev/rerun_auto.py` + two whitelist files
  (`notebooks-auto-refresh.txt` / `notebooks-frozen-qt.txt`) drive
  the new tutorial-execute CI step.

### Fixed

- **Watermark autoscale bug** in `_axis_set_watermark_img` (shared by
  desktop `MetalGUI` + new headless renderer): the watermark image
  previously expanded the parent axes' `dataLim` on every redraw,
  pushing the chip off-center after `gui.autoscale()` or `gui.rebuild()`.
  Now rendered into an inset axes that doesn't contribute to the
  parent `dataLim`.
- **Wide-chip letterboxing** in headless renders: switched
  `ax.set_aspect("equal")` to `adjustable="datalim"` so a 6 mm × 2 mm
  layout no longer collapses into a thin band with whitespace.
- `edit_component` no longer noisy in headless mode — true no-op now;
  the docstring points users at `design.components['<name>'].options`.
- `screenshot(display=True)` no longer double-displays in Jupyter
  (returning the figure after `display(Image(...))` triggered the
  cell's auto-display of the last expression).
- `find_id` warning silenced — replaced `design.components.get(name)`
  with `name in design.components` checks (`Components` isn't a dict;
  `.get` was being interpreted as a component lookup).
- `WARNING [_maybe_warn_lite_flip]` from v0.7.0 removed at source +
  scrubbed from 9 notebooks where it had been cached in output cells.
- `RouteMeander` docstring inline literal across a line break rewritten
  to a valid double-backtick literal.
- `JJ_Dolan.png`, `JJ_Manhattan.png`, `squid_loop.png` —
  case-sensitive filename mismatches in the corresponding docstrings
  fixed. Invisible on macOS HFS+ but broke the Library pane on Linux.
- 11 one-line `.. image:: foo.png` directives split to the two-line
  form the MetalGUI scanner regex requires.
- Tutorial 1.2 cell that printed `<Figure size 2400x1000 with 2 Axes>`
  instead of rendering inline now displays a PNG buffer via
  `IPython.display.Image` — backend-agnostic.

### Changed

- MetalGUI Library pane defaults to the **Library** tab on launch
  instead of QComponents (the latter is empty before any components
  exist).
- `MetalGUI` Library pane filters the `qlibrary/` tree to `*.py` only.
- `Quantum Metal` → `Qiskit / Quantum Metal` in both viewers' title
  strip and corner watermark.
- README hero strip: 3 cards → 4. New "🧩 Component Gallery" card.
- Tutorial 1.1 ↔ 1.2 swap. 1.4 Headless + 1.6 Shape library dropped.
- 2.01 + 2.02 merged into a single "QComponent lifecycle" notebook.
- `docs/qcomponents-gallery.rst`, `docs/images/qlibrary/`, and
  `docs/apidocs/*.png` are now generated at every docs build via the
  `builder-inited` hook and **gitignored**. Was: 100+ duplicate PNG
  blobs committed across two directories.
- `Opening documentation` quick-topic notebook no longer calls
  `open_docs()` automatically — line is commented; user opts in.
- 75+ stale `:doc:` references to the dropped 1.4 Headless tutorial
  swept to point at 1.1 Quick start.
- 41 numbered tutorials had `%load_ext autoreload` / `%autoreload 2`
  stripped (104 cells total) — these break in Colab.

### Deprecated

- Nothing. `MetalGUI(design)` direct construction remains fully
  supported; `qm.gui(design)` is an additive convenience.

### Migration

See `docs/migration-to-v0.7.0.rst` for the v0.7.2 "prefer
`qm.gui(design)` over `MetalGUI(design)`" section.


## Quantum Metal v0.7.1 (UX + docs polish; no breaking changes)

**Follow-up to v0.7.0** focused on adoption / DevRel polish, build-time
quality, and a friendlier ElmerFEM error surface. No breaking changes —
v0.7.0 users can upgrade in place.

### Highlights

- **ElmerFEM UX**: missing-binary errors now print actionable install
  instructions (platform-specific) instead of a bare ``FileNotFoundError``
  from ``subprocess.run``. Windows install-path lookup unpinned from
  Elmer 9.0 (globs ``Elmer *-Release/bin/``, so Elmer 10.x ships
  cleanly with no code change). Also fixed a pre-existing bug where
  passing an explicit ``elmersolver=`` path silently skipped the
  subprocess call.
- **New ``[mesh]`` extra** for the gmsh dependency (canonical name for
  the universal mesher — used by Elmer today, will feed Palace and
  future open FEM backends). ``[fem]`` kept as a backward-compatible
  alias; both extras install gmsh.
- **Docs build: zero warnings.** Previously failed with ~50+ warnings
  + several errors (heading hierarchy, nbformat validation, duplicate
  substitutions, ambiguous cross-refs). All fixed at source.
- **README modernization**: 482 → 225 lines, headless-first Quick Start,
  Colab + Codespaces "try it now" buttons, hero animated GIF showing a
  4-qubit chip built in 5 frames.
- **``CITATION.cff``** added for GitHub's "Cite this repository" widget.

### Bug fixes

- ``elmer_runner._resolve_elmer_binary`` — friendly errors when ElmerFEM
  binaries are missing; auto-detects newer Windows release directories.
- ``elmer_runner.run_elmersolver`` — explicit-path code path no longer
  skipped due to indentation bug; ``encoding="utf=8"`` typo fixed.
- ``analyses/__init__.py`` — added missing autosummary blocks so the
  rendered Analyses overview page is actually useful.
- ``_gui/main_window*.py`` — RST docstring lint pass (bullet lists,
  paragraph spacing); PySide2 → PySide6 in docstrings (we've shipped
  PySide6 since v0.5).
- ``contributor-guide.rst`` — example directives no longer accidentally
  fire at build time and generate phantom RST files.

### Docs

- Sphinx ``conf.py``: added ``intersphinx`` for python/matplotlib/numpy/
  pandas, ``nitpick_ignore`` for ``logger``/``figure``,
  ``nbsphinx_codecell_lexer="python3"`` (silenced ~1500 warnings).
- Tutorial notebook normalisation (nbformat cell IDs across 108
  notebooks) + heading-hierarchy fixes across 1.1/1.2/4.05.
- New ``scripts/check_tutorials_sync.py`` CI gate ensures ``tutorials/``
  and ``docs/tut/`` cell content stays byte-identical.
- ``README_Gmsh_Elmer.md`` → ``README_Open_FEM_Stack.md`` (broader scope:
  gmsh + Elmer + future Palace).
- Stripped v0.5/v0.6 era qualifiers across installation, migration,
  headless-usage, workflow, contributor-guide, FAQ.
- Dead links fixed (gohlke wheels site retired in 2022); rebrand pass
  across all auxiliary READMEs.

### Hygiene

- ``[tool.ruff]`` — added ``extend-exclude`` for ``_dev/``, ``docs/_archive/``,
  ``docs/_build/`` (scratch / generated dirs).
- ``ipython>=8.0`` and ``ipywidgets>=8.1`` added to docs deps (silence
  nbsphinx lexer and ipywidgets-path warnings).
- ``ROADMAP.md`` — new "Adoption, DevRel, and onboarding" section
  capturing follow-up ideas (Colab embeds, JupyterLite, gallery page,
  SUPPORT.md / GOVERNANCE.md, devcontainer, recipes section, etc.).
- CI matrix: ``tests-extras`` now runs both ``mesh`` and ``fem`` (alias)
  paths so neither can regress silently.

### Compatibility matrix

| | v0.7.0 | **v0.7.1** |
|---|---|---|
| Python | 3.10 / 3.11 / 3.12 | 3.10 / 3.11 / 3.12 |
| Default install | lite (no Qt / Ansys / gmsh) | same |
| ``[gui]`` extra | PySide6, qdarkstyle | same |
| ``[ansys]`` extra | pyaedt, pyEPR-quantum | same |
| ``[fem]`` extra | gmsh | same (alias for new ``[mesh]``) |
| ``[mesh]`` extra | — | **new** (canonical name; gmsh) |
| ``[full]`` extra | all of above | same |

## Quantum Metal v0.6.2 (deprecation-notice release)

**Pre-flip release.** All v0.6.x install behaviour is unchanged
— but a `FutureWarning` now fires on `import qiskit_metal` letting
users know v0.7.0 will move the heavy dependencies (PySide6,
qdarkstyle, pyaedt, pyEPR-quantum, gmsh) out of base into opt-in
extras. To preserve current behaviour, install with
`pip install 'quantum-metal[full]'` before upgrading to v0.7.0.

This release also lazifies the last remaining eager heavy-dep
import — gmsh — so the `tests-lite` CI matrix can validate the
full v0.7.0 install behaviour ahead of the actual deps flip.

### What landed

- **gmsh lazification** in `renderer_gmsh/gmsh_utils.py` and
  `renderer_gmsh/gmsh_renderer.py`: same `try/except` +
  `_require_gmsh()` pattern as the pyEPR/pyaedt lazification in
  v0.6.x. `QGmshRenderer.__init__` raises a clear
  `ImportError: ... pip install 'quantum-metal[fem]'` when gmsh
  isn't available. The `_start_renderers` skip-and-log path
  catches it.
- **gmsh version pin tighten**: `gmsh>=4.11.1` → `gmsh>=4.15.0,<5`.
  The dev env already ships gmsh 4.15.0 (bumped in v0.5.3.post1
  but the floor wasn't updated). Upper bound caps before any
  future gmsh 5 lands.
- **`FutureWarning` on `import qiskit_metal`** advertising the
  v0.7.0 lite-flip. Fires once per process via Python's standard
  warning deduplication. Suppress with
  `QISKIT_METAL_SUPPRESS_LITE_FLIP_WARNING=1`.
- **Version bumped** to 0.6.2.

### Nothing else changed

- Public API: unchanged
- Test behaviour: unchanged (all 458 tests still pass)
- Install behaviour: unchanged (heavies still in base)
- Headless / lite paths: unchanged

The next release (v0.7.0) will flip `pyproject.toml`'s base
dependencies and the warning becomes truth.

## Quantum Metal v0.7.0 (lite-by-default release)

**Headline: lite-by-default install.** `pip install quantum-metal`
no longer pulls PySide6, qdarkstyle, pyaedt, pyEPR-quantum, or gmsh
— those move into opt-in extras (`[gui]` / `[ansys]` / `[fem]` /
`[full]`). The base install is now small, fast, and friendly to AI
orchestration, Colab / Binder, cloud Jupyter, headless CI, and any
non-interactive workflow.

See [`ROADMAP.md`](./ROADMAP.md) and
[`docs/migration-to-v0.7.0.rst`](./docs/migration-to-v0.7.0.rst) for
the full migration recipes.

### Breaking change — what to do

`pip install quantum-metal` no longer pulls the heavies. Pick the
install command that matches your workflow:

| Command | What you get |
|---|---|
| `pip install quantum-metal` | Lite: designs + `qm.view()` + GDS + pure-Python analyses |
| `pip install "quantum-metal[gui]"` | + `MetalGUI` desktop app (PySide6, qdarkstyle) |
| `pip install "quantum-metal[ansys]"` | + HFSS/Q3D renderers + EPR analyses (pyaedt, pyEPR) |
| `pip install "quantum-metal[fem]"` | + gmsh / Elmer mesher |
| `pip install "quantum-metal[full]"` | All of the above — v0.6.x compatibility set |

The full feature matrix is in `README.md` and `docs/installation.rst`.

### Why

- **AI orchestration loops**, cloud Jupyter, Colab / Binder, and
  headless CI no longer install or ignore hundreds of MB of Qt + AEDT
  they'll never use. Base install drops from ~1 GB to a few dozen MB.
- **Academic and educational users** without Ansys licenses can now
  install + use the full design/analysis path without artificially
  needing pyaedt.
- **Tutorial notebooks** that don't need Ansys / gmsh now run on lite.

### What didn't change

- `import qiskit_metal` (the import path stays for v0.7.x; see the
  upcoming import-rename heads-up below)
- Public API on `QDesign`, `QComponent`, `QRenderer`
- The Python API surface — every class, function, and method is
  unchanged

### Upcoming next: import path rename

A future major release will rename the Python import path from
`qiskit_metal` to `quantum_metal` to match the PyPI package name.
No version has been set for the cutover. A `FutureWarning` now fires on
`import qiskit_metal` advertising this. Plan to update your imports
ahead of that release; an alias/shim period will be considered
during the cutover. See the README rebrand notice for details.

Silence the warning with `QISKIT_METAL_SUPPRESS_RENAME_WARNING=1`.

### CI

- **`tests-extras` matrix added** — exercises `[gui]`, `[ansys]`,
  and `[fem]` install pathways individually so a regression on any
  one extra surfaces in CI (previously only the full + lite paths
  were tested).

### Docs

- **README** redesigned with a 5-card install-pathway grid + feature
  matrix.
- **`docs/installation.rst`** expanded with the same 5-card grid and
  a more thorough install-pathway breakdown.
- **`docs/index.rst`** updated to reflect the v0.5 → v0.7
  transition state and the upcoming import-rename heads-up.
- Various "Qiskit Metal" → "Quantum Metal" rebrand cleanups
  throughout README / docs / install pages.

## Quantum Metal v0.6.2 (deprecation-notice release)

**Pre-flip release.** All v0.6.x install behaviour was unchanged
— but a `FutureWarning` fired on `import qiskit_metal` advising
users of the upcoming v0.7.0 lite-flip. Also lazified the last
remaining eager heavy-dep import (gmsh) and tightened the gmsh pin
to `>=4.15.0,<5`.

### What landed

- **gmsh lazification** in `renderer_gmsh/gmsh_utils.py` and
  `renderer_gmsh/gmsh_renderer.py`: same `try/except` +
  `_require_gmsh()` pattern as the pyEPR/pyaedt lazification.
- **gmsh version pin tighten**: `gmsh>=4.11.1` → `gmsh>=4.15.0,<5`.
- **`FutureWarning` on `import qiskit_metal`** advertising the
  v0.7.0 lite-flip. Repurposed in v0.7.0 to advertise the upcoming
  import path rename.
- **Docs CI**: `docs.yml` now also runs on PRs (build-only; deploy
  only on push-to-main).
- **Version bumped** to 0.6.2.

## Quantum Metal v0.6.1 (May 2026)

Patch release after the v0.6.0 tag-only failure (PyPI publish step
failed during the v0.6.0 cut; `pip install quantum-metal==0.6.0`
404s. Don't tag-and-walk-away on releases — verify PyPI received
the wheel before announcing). See `.claude/commands/release.md`
post-mortem.

User-visible changes vs v0.6.0:

- Sphinx docs build warnings resolved
- Tutorial notebook heading-level hierarchy normalized (nbsphinx
  was choking on `# → ###` skips)
- qutip 5 + pyEPR 0.9.5+ version sync — fixes `np.array([Qobj])`
  stacking issue, `np.absolute(Qobj)` issue, and the HFSS 2024.1+
  solution-type rename
- Ruff auto-fixes + trailing-whitespace cleanup

## Quantum Metal v0.6.0 (May 2026)

**Major release.** Foundation for the lite-by-default flip in
v0.7.0. All changes here are additive — current users on v0.5.x
upgrade without code changes.

### Highlights

- **`qm.view(design)`** — standalone matplotlib viewer that works
  without PySide6 / Qt installed. Renders in a Jupyter notebook
  inline or to a file. The headless entry point for tutorials,
  CI, agent workflows, and any environment where you don't want
  to install a Qt binding. See `docs/headless-usage.rst`.
- **Lazy Qt initialization** — `import qiskit_metal` no longer
  requires PySide6 at module-load time. Set
  `QISKIT_METAL_HEADLESS=1` to skip the Qt-backend probe entirely;
  `MetalGUI` still works on full installs.
- **`[gui]` / `[ansys]` / `[fem]` / `[full]` optional-dependency
  extras** added to `pyproject.toml`. In v0.6.x they're
  informational (every extra's deps are also in base), but the
  `tests-lite` CI job exercises the lite-install path so it stays
  green for v0.7.0's flip.
- **`tests-lite` CI matrix entry** — runs the full test suite on
  a venv built without PySide6 / pyaedt / gmsh, catching any
  regression on the lite path.
- **`qutip 5` + `pyEPR 0.9.5+` compatibility** — fixes
  `np.array([Qobj])` no longer stacking, `np.absolute(Qobj)` no
  longer working directly, and the HFSS 2024.1+
  `solution_type` rename (`"DrivenModal"` →
  `"HFSS Modal Network"`).
- **Pandas 2.2 compatibility** — uses `.iloc[]` for positional
  indexing where 2.2 stopped doing the old positional-fallback.
- **Type annotations** on the core public API methods of
  `QComponent`, `QDesign`, and the renderer bases — unlocks
  downstream type-checking for orchestration tools.

### New tests

- `test_pin_normals_point_outward` — static sanity check that
  every component's pins point away from the component centroid.
  Catches HFSS port-flip bugs at component-author time, not at
  HFSS-eval time. One known failing case logged:
  `LaunchpadWirebondDriven.in` (see `KNOWN_INWARD_PINS`).
- Static AST audit that every `self.options.X` access has a
  matching key in `default_options`. Catches typos that would
  silently fall through.
- `test_view_hides_layers` — gates the new `qm.view(design)`
  `hidden_layers={...}` parameter.

### Tutorials

- Every tutorial notebook now has a "no Qt required" callout
  near the top, explaining when the tutorial does and doesn't
  need `MetalGUI`.
- New `1.4 Headless Quick View.ipynb` — short notebook showing
  the `qm.view(design)` path end-to-end with no Qt.
- The headless tutorial path is exercised in CI via
  `nbconvert --execute` on `1.4 Headless Quick View.ipynb`
  inside the `tests-lite` job.

### Infrastructure

- `CLAUDE.md` + `.claude/` directory: documents the repo's
  hard-touch zones, recurring tasks, and lessons-learned for
  future AI agents.
- `tests-lite` uses `.venv/bin/python` directly (not `uv run`)
  because `uv run` was re-syncing the venv and overwriting the
  custom lite-install state. See
  `.claude/context/lessons-learned.md`.

### Known issues

- `LaunchpadWirebondDriven.in` pin normal points inward (HFSS
  validation blocked the fix in v0.6.0; documented in
  `tests/test_qlibrary_pin_sanity.py::KNOWN_INWARD_PINS`).
- 13 ruff findings in HFSS / `_gui/` deferred to v0.6.1+ for
  validation environment. (**Resolved** in v0.6.1+ via the
  ruff-sweep PR #1070, with one caveat documented in
  `.claude/context/lessons-learned.md`.)
- v0.6.0 PyPI publish failed; install
  `quantum-metal>=0.6.1` instead. (**Fixed** in v0.6.1.)

## Quantum Metal v0.5.3.post1 (Jan 23, 2026)
- Pinned pyaedt to less than v0.24 due to bugs. 
- Updated gmsh dependency 4.11.1 → 4.15.0

## Quantum Metal v0.5.3 (Jan 17, 2026)

- Various dependency updates. 
- Removed descartes and cython dependencies (unused).
- pandas, geopandas, scqubits and qutip updates to latest major version. Should fix [#1027](Ihttps://github.com/qiskit-community/qiskit-metal/issues/1027).
- Updates to contributor guide to fix inconsistent headline levels. Also convert example images to rst source code blocks. 
- Update various parts in the docs to indicate near-term versioning updates. 
- Update uv version to 0.9.24 in CI. Remove step to upgrade runner packages in CI for workflows speedup. 
- Convert package from [flat layout to src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/#src-layout-vs-flat-layout). This is a forward looking change that will help decouple source code from docs and tests. In this configurations, the any package code must be imported using the package name, instead of relative imports as before. This also requires installing the package in the virtual environment (either as editable or via the wheel) to import it, which we already support in our uv-based workflows. 
- Fixed floating `QLabel` bug in `MetalGUI` [#1031](https://github.com/qiskit-community/qiskit-metal/issues/1031).
- New CI workflow to bump version using uv, commit and push a git tag and create a draft release. This also triggers the PyPI release. 
- Update CI workflows to use Python 3.12.


## Quantum Metal v0.5.2 (Dec 11, 2025)

- We have adopted uv as a project/dependency management tool. 
- Tasks are still run using tox, but with the tox-uv plugin. 
- We adopted ruff for linting and formatting. We have a good starting configuration for linting, but it needs some work before it could be considered stable. 
- The GitHub actions workflows have been updates with these changes. 
    - Python 3.12 is the slowest to build wheels in CI, partly because qutip and pandas take a very long time to build on this version. This needs to be investigated. 
- New developer onboarding instuctions added to `README_developers.md`. The old instructions in`README_developers.md` have been retained with a note for usage on older versions of `qiskit-metal`. 
- Development install instructions have been added to documentation in the "Contributor Guide". 
- Installation instructions have been updates. More updates to come. 
- Single source package version from `pyproject.toml`.
- Updated to contributor docs to add instructions on bumping package version using uv. 



## QISKIT METAL v0.5 (2025)

### Major Updates

This release addresses significant package changes and ports:

- **PyQt5 to PySide6**: A complete overhaul of the GUI.
- **GDSPY to GDSTK**: Replaced GDSPY with the more robust GDSTK library.
- **PYAEDT to Ansys (v1.0)**: Major update with a new syntax. Extensive testing required.
- **Installation Improvements**: Transitioned to `venv` for faster environment setup, moving away from `conda`. Also, most package versions have been floated and upgraded.
- **Docs**:
    - Migrate qiskit_sphinx_theme to the new theme
    - Add divs on the front page to tuts etc
    - Add user content and showcase page

---

### GUI Enhancements

1. **Traceback Reporting**: Added detailed traceback reporting in the logging system to aid debugging.
2. **Model Reset Issue**: Fixed the issue causing the warning: *"metal: WARNING: endResetModel called on LibraryFileProxyModel(0x17fda8200) without calling beginResetModel first (No context available from Qt)"*.
3. **MPL Renderer Issue**: Resolved the error: *"Ignoring fixed y limits to fulfill fixed data aspect with adjustable data limits. Ignoring fixed x limits to fulfill fixed data aspect with adjustable data limits."*.
4. **UI Button Update**: Added a red border style to the "Create Component" button in the UI for better visibility.

---

### PYAEDT Update

- **FutureWarning**: The `pyaedt` module has been restructured and is now an alias for the new package structure based on `ansys.aedt.core`. To avoid issues in future versions, please update your imports to use the new architecture. Additionally, several files have been renamed to follow the PEP 8 naming conventions. For more information, refer to the [Ansys AEDT documentation](https://aedt.docs.pyansys.com/version/stable/release_1_0.html).
