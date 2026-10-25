.. _tut-simulate-and-analyze:

============================
Part 4: Simulate and analyze
============================

Extract capacitances, mode frequencies and couplings from a design with an EM solver, then build circuit models from them.
See :doc:`../simulation-pathways` for what each solver computes and how to install it.

Open-source solver first
------------------------

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

More
----

.. grid:: 1 2 2 2
    :gutter: 2

    .. grid-item-card:: Simulate with Ansys
        :link: simulate-ansys
        :link-type: doc

        Analysis classes, tuning a device, resonator S21, sweeps, and the
        pyaedt renderer. (16 notebooks)

    .. grid-item-card:: From circuits to Hamiltonians
        :link: circuits-to-hamiltonians
        :link-type: doc

        Lumped-oscillator models, analytic transmon models, circuit QED and
        gates. (9 notebooks)

.. toctree::
    :maxdepth: 1
    :hidden:

    simulate-ansys
    circuits-to-hamiltonians
