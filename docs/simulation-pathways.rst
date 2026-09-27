.. _simulation-pathways:

===================
Simulation pathways
===================

A Quantum Metal design reaches an electromagnetic solver along one of several
paths. Which one to take depends on what you need to compute and what you can
install. The tutorials use all of them, often on the same kind of device, so a
result from one path can be checked against another.

.. list-table::
   :header-rows: 1
   :widths: 16 26 20 20 18

   * - Pathway
     - Computes
     - Install
     - Where in Metal
     - Tutorials
   * - **Ansys HFSS / Q3D** (commercial)
     - eigenmodes and energy participation (EPR); driven S/Z/Y parameters;
       capacitance matrices for the lumped-oscillator model (LOM)
     - Ansys Electronics Desktop with a license; ``pip install
       "quantum-metal[ansys]"``
     - renderers ``hfss``, ``q3d``, ``aedt_hfss``, ``aedt_q3d``;
       ``analyses.simulation`` (``EigenmodeSim``, ``LumpedElementsSim``,
       ``ScatteringImpedanceSim``); ``LOManalysis``
     - 3.3; 4.01–4.05; 4.11–4.18; 4.21–4.23; pyaedt multiplanar; A.4–A.7
   * - **gmsh + ElmerFEM** (open source)
     - capacitance matrices (electrostatics) for LOM
     - ``pip install "quantum-metal[mesh]"`` plus the ElmerFEM binaries
       (``ElmerGrid``, ``ElmerSolver`` on ``PATH``; see
       ``README_Open_FEM_Stack.md``)
     - ``QGmshRenderer``, ``QElmerRenderer``
     - 3.5; 4.19; A.4; the two-qubit cell of the 17-qubit chip
   * - **gmsh + scikit-fem** (open source, pure Python)
     - eigenmodes with lumped junction inductors; EPR, avoided-crossing,
       induced-EMF and impedance-matrix couplings; port impedance matrices;
       capacitance matrices
     - ``pip install "quantum-metal[mesh]" scikit-fem pymetis``
       (``pymetis`` optional)
     - a tutorial resource module, ``docs/tut/resources/package_modes``
       (not yet a renderer)
     - 4.41–4.45
   * - **AWS Palace** (open source, planned)
     - eigenmodes, driven and electrostatic solves, EPR, on MPI clusters
     - builds from source (CMake, MPI)
     - planned; see the roadmap
     - —

Choosing a path
===============

- **Eigenmodes, EPR, S-parameters, and an Ansys license**: HFSS, the most
  complete path in Quantum Metal today.
- **Capacitance and LOM without a license**: ElmerFEM for larger models (it
  runs in parallel and supports higher-order elements); the scikit-fem solver
  for small ones or where installing binaries is not possible.
- **Eigenmodes and couplings without a license**: the scikit-fem solver, for
  cells and arrays of simple qubits. Tutorials 4.43–4.45 reproduce a published
  HFSS study of a 10 × 10 transmon array to within a few percent.
- **Teaching, Colab, continuous integration**: the scikit-fem solver needs
  only ``pip``.

What the open-source paths do not do yet
========================================

- ElmerFEM is connected for electrostatics only; its electromagnetic-wave
  solvers are not wired into Quantum Metal.
- The scikit-fem solver uses lowest-order elements and zero-thickness metal,
  handles metal islands and junction lines but not ground planes with
  cutouts or CPWs, and runs in one process (up to about a million unknowns).
- Neither has wave ports or losses.

Plans
=====

The roadmap sections "Open FEM stack" and "Solver backends" describe how these
paths are meant to converge on one interface — scikit-fem and ElmerFEM
first, then Palace — and how solver results are tested. Design notes for the
scikit-fem solver: ``docs/architecture/open_fem_scikit_fem.md`` in the
repository.
