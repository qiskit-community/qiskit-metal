# `package_modes` — solver for tutorials 4.41–4.45

Shared code for the five notebooks in `docs/tut/4-Analysis/4.4*` that reproduce
R. Molavi *et al.*, *Extracting electromagnetic bare mode couplings in large
superconducting quantum processors*, [arXiv:2609.22442](https://arxiv.org/abs/2609.22442) (2026):
the couplings of a 10 × 10 transmon array to the modes of its metal package,
computed four ways.

The paper runs Ansys HFSS. Here the device is a Quantum Metal design, gmsh
meshes it, and a finite-element Maxwell solver assembled with
[scikit-fem](https://github.com/kinnala/scikit-fem) and solved with SciPy
does the rest:

```bash
pip install "quantum-metal[mesh]" scikit-fem pymetis   # pymetis is optional
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
