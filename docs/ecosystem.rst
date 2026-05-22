.. _ecosystem:

The Quantum Metal Ecosystem
###########################

Quantum Metal is one tool in a growing open-source community for
superconducting quantum device design. It sits at the **chip-design**
layer; other community projects plug in at the layers above
(design-discovery / databases) and below (simulation backends, mesh
generation, post-processing).

This page maps the ecosystem so you can find the right tool for your
need — and so we can avoid accidentally reinventing what an active
neighbour already maintains.

If you maintain a project we should list here, please
`open an issue <https://github.com/qiskit-community/qiskit-metal/issues/new/choose>`_
or ping us on `Discord <https://discord.gg/kaZ3UFuq>`_.


At a glance
===========

.. list-table::
   :header-rows: 1
   :widths: 24 50 14 12

   * - Layer
     - Tool
     - License
     - Status
   * - Design discovery
     - `SQuADDS <https://github.com/LFL-Lab/SQuADDS>`_ — validated qubit-design database + parameter interpolation
     - MIT
     - Uses Quantum Metal ✅
   * - **Chip design**
     - **Quantum Metal** (this project) — ``QComponent``-based design and analysis
     - Apache 2.0
     - —
   * - Chip design (alt)
     - `KQCircuits <https://github.com/iqm-finland/KQCircuits>`_ (IQM) — GDS-centric design framework
     - GPL-3.0
     - Separate community
   * - Chip design (alt)
     - `gdsfactory <https://github.com/gdsfactory/gdsfactory>`_ — broader photonic / circuit design
     - MIT
     - Separate community
   * - Simulation wrapper
     - `SQDMetal <https://github.com/sqdlab/SQDMetal>`_ (SQDLab @ UQ) — wraps Palace + COMSOL workflows; accepts ``QDesign`` directly
     - Apache 2.0
     - Coordinating 🟡
   * - Simulation wrapper
     - `pypalace <https://pypalace.readthedocs.io/>`_ (Northwestern) — Python toolkit for AWS Palace with Quantum Metal gmsh export
     - n/a
     - Coordinating 🟡
   * - Mesher utility
     - `meshwell <https://github.com/simbilod/meshwell>`_ — 2.5D meshing helper on top of gmsh + OCC
     - GPL-3.0
     - Aware, not integrated
   * - Solver
     - `AWS Palace <https://github.com/awslabs/palace>`_ — open-source Maxwell solver (eigenmode + driven + electrostatic + AMR)
     - Apache 2.0
     - Roadmap 🟡 (see :doc:`ROADMAP <https://github.com/qiskit-community/qiskit-metal/blob/main/ROADMAP.md>`)
   * - Solver
     - `Elmer FEM <https://www.elmerfem.org/>`_ — open FEM solver (capacitance / LOM)
     - LGPL
     - Integrated in ``[mesh]`` extra
   * - Solver (commercial)
     - Ansys HFSS / Q3D via `pyaedt <https://github.com/ansys/pyaedt>`_
     - MIT (pyaedt)
     - Integrated in ``[ansys]`` extra
   * - Mesher
     - `gmsh <https://gmsh.info/>`_ — workhorse mesh generator
     - GPL-2.0
     - Integrated in ``[mesh]`` extra
   * - Quantization
     - `pyEPR-quantum <https://github.com/zlatko-minev/pyEPR>`_ — energy-participation-ratio analysis on HFSS fields
     - BSD-3
     - Integrated in ``[ansys]`` extra
   * - Quantization
     - `scqubits <https://github.com/scqubits/scqubits>`_ — closed-form qubit spectra
     - BSD-3
     - In base deps
   * - Quantization
     - `CircuitQ <https://github.com/PhilippAumann/CircuitQ>`_ — arbitrary-circuit quantization
     - MIT
     - Aware, not integrated
   * - Quantum dynamics
     - `QuTiP <https://github.com/qutip/qutip>`_ — quantum-systems simulation
     - BSD-3
     - In base deps
   * - Visualization
     - `PyVista <https://github.com/pyvista/pyvista>`_ — Python ParaView wrapper for field data
     - MIT
     - Used downstream of FEM solvers


How the layers fit together
===========================

A typical workflow:

1. **Discover** a candidate design with SQuADDS (search the database,
   interpolate to your target parameters).
2. **Build** the QDesign in Quantum Metal — instantiate ``QComponents``,
   place + route, set options.
3. **Simulate** via the renderer of your choice:

   * Ansys HFSS / Q3D via the ``[ansys]`` extra,
   * Open-source FEM via ``[mesh]`` + Elmer (LOM today),
   * Palace via SQDMetal or pypalace (coordination underway — see the
     `ROADMAP <https://github.com/qiskit-community/qiskit-metal/blob/main/ROADMAP.md>`_).
4. **Analyse** the results:

   * EPR (``pyEPR`` on HFSS fields),
   * LOM (``LOManalysis`` on capacitance matrices),
   * Spectra (``scqubits``),
   * Dynamics (``QuTiP``).
5. **Export** to GDS via the built-in ``QGDSRenderer``; view in KLayout
   or hand off to fab.


Why we ecosystem-map instead of building everything ourselves
==============================================================

Quantum Metal's job is to be the best **chip-design layer** it can be —
``QComponent`` library, renderer protocol, headless ``qm.view()``, GDS
export, the lite-by-default install. We're not the best place to
reimplement a Maxwell solver, a qubit-design database, or a 2.5D meshing
helper. Other projects exist that do those well.

The community win is when these projects coordinate at the edges —
shared file formats, compatible ``QDesign`` consumption, mutual links in
docs — rather than competing for the same maintainer hours.

If you want to help shape that coordination, see the
`Adoption / DevRel section in ROADMAP.md <https://github.com/qiskit-community/qiskit-metal/blob/main/ROADMAP.md>`_
or reach out on Discord.
