# `package_modes` — solver for tutorials 4.41–4.46

Shared code for the notebooks in `docs/tut/4-Analysis/4.4*`. Five of them follow
R. Molavi *et al.*, *Extracting electromagnetic bare mode couplings in large
superconducting quantum processors*, [arXiv:2609.22442](https://arxiv.org/abs/2609.22442) (2026):
the couplings of a 10 × 10 transmon array to the modes of its metal package,
computed four ways; the sixth, 4.46, goes beyond the dipole picture they use (see `multipoles.py` below).

The paper runs Ansys HFSS. Here the device is a Quantum Metal design, gmsh
meshes it, and a finite-element Maxwell solver assembled with
[scikit-fem](https://github.com/kinnala/scikit-fem) and solved with SciPy
does the rest:

```bash
pip install "quantum-metal[skfem]" pymetis   # [skfem] = gmsh + scikit-fem; pymetis is optional
```

The solver lives in Quantum Metal; the notebooks reach it through
`package_modes.py`, which re-exports it as `pm.<name>`.

`package_modes.py` itself holds what is specific to the paper:

1. the device and the numbers the paper reports (`DEVICE`, `PAPER`);
2. the design in Quantum Metal (`build_design`, `TwoPadTransmon`);
3. the paper's device as the default arguments of the analytic functions
   (`lsm_mode`, `fit_amplitude`, `package_from_design`, …).

`qiskit_metal.analyses.em.package_modes` holds the analytic models:

- analytic LSM modes of the dielectric-loaded box and the dipole estimate
  (`lsm_mode`, `dipole_coupling`);
- the two-mode circuit and the Appendix D impedance fit
  (`circuit_couplings`, `fit_impedance`).

`qiskit_metal.analyses.fem` holds the finite-element solver:

- the geometry a mesher needs (`package_from_design`) and meshing with gmsh
  (`mesh_package`), with optional extra seeding around the junctions;
- the curl-curl eigenproblem on lowest-order Nédélec edge elements
  (`MaxwellFEM`): metal and symmetry planes as boundary conditions, a lumped
  junction as a rank-one term;
- a port reduced-order model (`PortROM`): junction inductors and impedance
  matrices without new factorizations;
- electrostatics (`Electrostatics`): the capacitance across each junction and
  the qubit's dipole moment.

`multipoles.py` is the helper module of tutorial 4.46, *Beyond the dipole*. It is
independent of `package_modes.py` (it needs only the solver in
`qiskit_metal.analyses.fem`) and holds:

- the moments of a qubit's charge and of its charge-displacement current
  (`pad_p1_charges`, `moments`, `sheet_current`, `SheetCurrent`, `dipole_center`);
- the analytic LSM field and its potential at any point, with its derivatives
  (`lsm_fields`, `lsm_potential`, `phi_derivs`, `lse_frequencies`);
- the finite-element side: the package mode without the paddles (`bare_mode`),
  its curl (`curl_E`) and polynomial fits over a disc (`disc_fit`);
- the coupling: the exact ray integral and the multipole terms (`ray_coupling`,
  `multipole_terms`, `series_terms`), the whole-array analysis of the tutorial
  (`qubit_sources`, `bare_data`, `dressed_data`, `terms_per_qubit`) and the error budget
  that gives each small term a measured floor (`fit_variants`, `error_budget`);
- `selftest()`: checks of the moments, the ray integral and the current model on
  synthetic data, no mesh needed.
