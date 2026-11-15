.. _tut-simulate-and-analyze:

============================
Part 4: Simulate and analyze
============================

Extract capacitances, mode frequencies and couplings from a design with an EM solver, then build circuit models from them.
See :doc:`../simulation-pathways` for what each solver computes and how to install it.

.. grid:: 1 1 3 3
    :gutter: 2

    .. grid-item::

        .. button-ref:: p4-open-source
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Open-source solver first

    .. grid-item::

        .. button-ref:: p4-ansys
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Simulate with Ansys

    .. grid-item::

        .. button-ref:: p4-hamiltonians
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            From circuits to Hamiltonians

.. _p4-open-source:

Open-source solver first
------------------------

gmsh, ElmerFEM and scikit-fem; no Ansys license needed.

.. nbgallery::

    4-Analysis/4.19-Analyze-a-transmon-using-ElmerFEM

Related notebooks listed elsewhere:

.. nblinkgallery::

    3-Renderers/3.5-Render-your-design-to-Gmsh
    4-Analysis/4.43-Mesh-and-solve-the-10x10-processor
    4-Analysis/4.44-Every-coupling-from-one-eigenmode
    4-Analysis/4.45-Four-methods-one-full-wave-model
    4-Analysis/4.46-Beyond-the-dipole-multipoles-and-magnetic-coupling
    ../circuit-examples/F.Small-quantum-chips/54-Wallraff_TwoQubit_Cell_Mesh
    ../circuit-examples/full-design-flow-examples/A.4-Full-chip-design

.. _p4-ansys:

Simulate with Ansys
-------------------

These notebooks need Ansys Electronics Desktop.

Two renderers drive Ansys: the legacy COM renderer and the pyaedt renderer.
The notebooks below cover the same three tasks on each.

.. list-table::
    :header-rows: 1

    * - Task
      - Legacy renderer
      - pyaedt renderer
    * - Q3D capacitance
      - 4.21
      - Q3D (MultiPlanar)
    * - Eigenmode and EPR
      - 4.22
      - Eigenmode (MultiPlanar)
    * - Driven S, Z, Y
      - 4.23
      - DrivenModal (MultiPlanar)

For impedance, 4.03 shows the recommended flow (analysis classes). 4.14 shows
the advanced flow, which drives the simulator through the renderer commands.

.. rubric:: Analysis classes

.. nbgallery::

    4-Analysis/4.01-Capacitance-and-LOM
    4-Analysis/4.02-Eigenmode-and-EPR
    4-Analysis/4.03-Impedance

.. rubric:: Tune a device directly

.. nbgallery::

    4-Analysis/4.11-Analyze-and-tune-a-transmon
    4-Analysis/4.12-Analyze-a-resonator
    4-Analysis/4.13-Analyze-transmon-and-resonator
    4-Analysis/4.14-Analyze-a-double-hanger-resonator

.. rubric:: Resonator S21

.. nbgallery::

    4-Analysis/4.16-Analyze-S21-of-Hange-Geometry-with-WirebondLunchpadDriven
    4-Analysis/4.17-Fit-S21-of-Hanger-Resonator-Geometry
    4-Analysis/4.18-Analyse-a-Resonator-with-Ports

.. rubric:: Sweeps (legacy renderer)

.. nbgallery::

    4-Analysis/4.21-Capacitance-matrix
    4-Analysis/4.22-Eigenmode-matrix
    4-Analysis/4.23-Impedance-and-scattering-Z-S-Y-matrices

.. rubric:: pyaedt renderer

.. nbgallery::

    4-Analysis/pyaedt-multiplanar/Q3D-pyaedt-multiplanar
    4-Analysis/pyaedt-multiplanar/Eigenmode-pyaedt-multiplanar
    4-Analysis/pyaedt-multiplanar/DrivenModal-pyaedt-multiplanar

.. _p4-hamiltonians:

From circuits to Hamiltonians
-----------------------------

Lumped-oscillator models of a design, analytic transmon models, and circuit QED.

.. rubric:: LOM 2.0

.. nbgallery::

    4-Analysis/4.04-New-LOM-and-Fluxonium-Example
    4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example
    4-Analysis/4.05-New-LOM-and-Two-Coupled-Transmon-Example-with-sequence

.. rubric:: Analytic models

.. nbgallery::

    4-Analysis/4.15-CPW-kappa-calculation
    4-Analysis/4.31-Plot-quantum-oscillator-wavefunction
    4-Analysis/4.32-Transmon-analytics-HCPB
    4-Analysis/4.34-Transmon-qubit-CPB-hamiltonian-charge-basis

.. rubric:: Circuit QED and gates

.. nbgallery::

    4-Analysis/cQED-with-the-Jaynes-Cummings-Interaction-Model
    4-Analysis/Design-and-Simulation-of-a-Cross-Resonance-Gate
