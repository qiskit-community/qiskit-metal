.. _research:

============================================================
Research showcase: published devices and results, reproduced
============================================================

Notebooks that reproduce a published device or result. Each is listed once
here; the table at the end gives the source, what is reproduced, and what it
needs.

Featured: package modes and qubit couplings
-------------------------------------------

Six notebooks follow R. Molavi *et al.*, `arXiv:2609.22442
<https://arxiv.org/abs/2609.22442>`_: the couplings of a 10 × 10 transmon array
to the modes of its metal package. They go from an analytic estimate (4.41) to
a full-wave model of the whole package (4.45); 4.46 then looks inside that
model term by term. They use gmsh and a scikit-fem Maxwell solver in place of HFSS (``pip install "quantum-metal[skfem]"``).

.. nbgallery::

    tut/4-Analysis/4.41-The-package-mode-on-paper
    tut/4-Analysis/4.42-Four-ways-to-measure-a-coupling
    tut/4-Analysis/4.43-Mesh-and-solve-the-10x10-processor
    tut/4-Analysis/4.44-Every-coupling-from-one-eigenmode
    tut/4-Analysis/4.45-Four-methods-one-full-wave-model
    tut/4-Analysis/4.46-Beyond-the-dipole-multipoles-and-magnetic-coupling

Published devices
-----------------

.. nbgallery::

    circuit-examples/F.Small-quantum-chips/52-Barends_5Qubit_Xmon_Processor
    circuit-examples/F.Small-quantum-chips/Full-Physical-Design-of-iSWAP-Gates
    circuit-examples/F.Small-quantum-chips/53-Wallraff_17Qubit_SurfaceCode
    circuit-examples/F.Small-quantum-chips/54-Wallraff_TwoQubit_Cell_Mesh

Summary
-------

.. list-table::
    :header-rows: 1

    * - Notebook
      - Reproduces
      - Level
      - Needs
    * - 4.41 to 4.46
      - R. Molavi *et al.*, `arXiv:2609.22442 <https://arxiv.org/abs/2609.22442>`_
      - analytic estimate to full-wave model
      - lite (4.41, 4.42); ``[skfem]`` and gmsh (4.43 to 4.46; 4.46 also ``pymetis``)
    * - 52 Barends
      - Barends *et al.*, `Nature 508, 500 (2014) <https://doi.org/10.1038/nature13171>`_: 5-qubit Xmon processor
      - layout
      - lite
    * - iSWAP
      - three published iSWAP devices
      - layout
      - see the notebook
    * - 53 Wallraff
      - Krinner *et al.*, `Nature 2022 <https://doi.org/10.1038/s41586-022-04566-8>`_: 17-qubit surface-code chip (Wallraff group)
      - layout, design-rule checks, GDS export
      - lite
    * - 54 Wallraff cell
      - two-qubit cell of the 53 chip
      - gmsh mesh and ElmerFEM capacitance
      - ``[mesh]`` and ElmerFEM
