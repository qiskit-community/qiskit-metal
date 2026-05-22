.. _ecosystem:

The Quantum Metal Ecosystem
###########################

Quantum Metal is the **open-source chip-design layer** for superconducting
quantum hardware. A growing community of tools builds on top of it,
extends it with new simulation backends, and plugs into it for
quantization, visualization, and parameter discovery.

This page maps that ecosystem so you can find the right tool for what
you're trying to do — and so we can highlight the projects that already
choose Quantum Metal as their substrate.

If you maintain a project we should list here, please
`open an issue <https://github.com/qiskit-community/qiskit-metal/issues/new/choose>`_
or ping us on `Discord <https://discord.gg/kaZ3UFuq>`_.


Built on Quantum Metal
======================

These projects use Quantum Metal directly — they consume ``QDesign``
objects, extend the ``QComponent`` library, or treat Metal as their
foundation:

.. list-table::
   :header-rows: 1
   :widths: 26 56 18

   * - Project
     - What it does
     - License
   * - `SQuADDS <https://github.com/LFL-Lab/SQuADDS>`_
       (LFL-Lab @ USC)
     - Validated qubit-design database + physics-based parameter interpolation. Search the DB, interpolate to your target Hamiltonian, generate the design in Quantum Metal. Published in *Quantum* journal (Sept 2024). Includes an MCP server for AI agents.
     - MIT
   * - `SQDMetal <https://github.com/sqdlab/SQDMetal>`_
       (SQDLab @ UQ)
     - Simulation wrapper for ``QDesign`` → AWS Palace / COMSOL workflows. Covers eigenmode, capacitance, driven, inductance simulations end-to-end. Accepts Quantum Metal ``QDesign`` objects directly.
     - Apache 2.0
   * - `ML_qubit_design <https://github.com/CosmiQuantum/ML_qubit_design>`_
       (Fermilab + Northwestern)
     - ML-based inverse design — predicts Quantum Metal design parameters from target qubit, resonator, coupler, and Hamiltonian properties using multi-layer perceptrons. Notebook-driven research project.
     - see repo
   * - `pypalace <https://pypalace.readthedocs.io/>`_
       (Northwestern)
     - Python toolkit for AWS Palace with Quantum Metal gmsh export, JSON config builders, LOM analysis utilities.
     - see repo

**This list grows with the community.** If you're building on Quantum
Metal in a research project, an internal tool, or a startup, we'd
genuinely love to know — open an issue and we'll add you.


Solvers Quantum Metal integrates with
=====================================

These are the simulation backends Quantum Metal drives via its renderer
protocol. Each is its own project; we wrap, we don't fork.

.. list-table::
   :header-rows: 1
   :widths: 26 56 18

   * - Solver
     - Role
     - Integrated via
   * - `AWS Palace <https://github.com/awslabs/palace>`_
       (AWS Center for Quantum Computing)
     - Maxwell solver — eigenmode + driven + electrostatic + magnetostatic + AMR. Apache 2.0.
     - Roadmap (see `ROADMAP.md <https://github.com/qiskit-community/qiskit-metal/blob/main/ROADMAP.md>`_)
   * - `Ansys HFSS / Q3D <https://www.ansys.com/products/electronics/ansys-hfss>`_
     - Industrial-grade EM solvers. Closed-source, requires AEDT license.
     - ``[ansys]`` extra → `pyaedt <https://github.com/ansys/pyaedt>`_
   * - `Elmer FEM <https://www.elmerfem.org/>`_
     - Open-source FEM solver. Today: capacitance for LOM analysis.
     - ``[mesh]`` extra (gmsh + Elmer external binary)
   * - `gmsh <https://gmsh.info/>`_
     - Workhorse mesh generator (used by Elmer today, Palace tomorrow).
     - ``[mesh]`` extra


Quantization & analysis libraries
=================================

After simulation produces fields / S-parameters / capacitance, these
libraries turn the results into qubit physics:

.. list-table::
   :header-rows: 1
   :widths: 26 56 18

   * - Library
     - Role
     - Integration
   * - `pyEPR-quantum <https://github.com/zlatko-minev/pyEPR>`_
     - Energy-Participation-Ratio quantization from HFSS field data. The math we use to turn eigenmodes into Hamiltonians.
     - ``[ansys]`` extra
   * - `scqubits <https://github.com/scqubits/scqubits>`_
     - Closed-form qubit-spectra and circuit-Hamiltonian library.
     - Base deps
   * - `QuTiP <https://github.com/qutip/qutip>`_
     - Quantum dynamics — time evolution, master equations, etc.
     - Base deps
   * - `CircuitQ <https://github.com/PhilippAumann/CircuitQ>`_
     - Quantization of arbitrary superconducting circuits.
     - Aware, not yet integrated


Visualization
=============

For viewing simulation outputs (Palace / Elmer field data, mesh files):

- `PyVista <https://github.com/pyvista/pyvista>`_ — Python ParaView wrapper, MIT.
- `ParaView <https://www.paraview.org/>`_ — the underlying renderer, BSD.

The ``[mesh]`` extra and Palace renderers emit ``.vtu`` / ``.pvtu``
files these tools open natively.


Other design tools (different scope)
====================================

A few other Python design tools exist in adjacent or overlapping scopes.
Worth knowing about for completeness:

- `KQCircuits <https://github.com/iqm-finland/KQCircuits>`_ (IQM Finland) —
  GDS-centric superconducting-circuit design framework. Different
  philosophy than Quantum Metal's ``QComponent``-first approach. GPL-3.0.
- `gdsfactory <https://github.com/gdsfactory/gdsfactory>`_ — primarily
  photonics-focused, with growing superconducting use. MIT.
- `femwell <https://github.com/HelgeGehring/femwell>`_ — photonics FEM
  library (eigenmode + thermal + RF CPW), gdsfactory-adjacent. GPL-3.0.


How the layers fit together
===========================

A typical workflow walks through several of these projects:

1. **Discover** a candidate design via SQuADDS (search the DB,
   interpolate to your target parameters) — or hand-design from scratch
   using Quantum Metal's ``QComponent`` library.
2. **Build** the ``QDesign`` in Quantum Metal — instantiate
   ``QComponents``, place + route, set options.
3. **Simulate** via the renderer of your choice — Ansys via ``[ansys]``,
   open-FEM via ``[mesh]`` + Elmer, or AWS Palace via SQDMetal /
   pypalace (coordination underway — see `ROADMAP.md
   <https://github.com/qiskit-community/qiskit-metal/blob/main/ROADMAP.md>`_).
4. **Analyse** — EPR (``pyEPR``), LOM (``LOManalysis``), spectra
   (``scqubits``), dynamics (``QuTiP``).
5. **Export** to GDS via the built-in ``QGDSRenderer``; view in KLayout
   or hand off to fab.

Some users also close the loop with **ML inverse design** —
``ML_qubit_design`` trains on Quantum Metal simulation data to predict
``QDesign`` parameters from target qubit properties, enabling fast
parameter exploration without running full EM simulations.


Why we ecosystem-map instead of building it all
================================================

Quantum Metal's job is to be the best chip-design layer it can be —
``QComponent`` library, renderer protocol, headless ``qm.view()``, GDS
export, the lite-by-default install. We're explicitly **not** the right
place to reimplement a Maxwell solver, a qubit-design database, an ML
inverse-design framework, or a photonic-FEM library. Other projects do
those well.

The community wins when these projects coordinate at the edges — shared
``QDesign`` formats, compatible meshing conventions, mutual docs links —
rather than competing for the same maintainer-hours.

If you want to help shape that coordination, see the
**Adoption / DevRel section** in `ROADMAP.md
<https://github.com/qiskit-community/qiskit-metal/blob/main/ROADMAP.md>`_
or reach out on `Discord <https://discord.gg/kaZ3UFuq>`_.
