.. _tutorials-overview:

=====
Learn
=====

The tutorial course, in four parts. Each part lists its notebooks in the
order to read them. New here? Start with the :doc:`../quickstart` page, then
Part 1.

Featured: package modes and qubit couplings
===========================================

Six notebooks follow R. Molavi *et al.*, `arXiv:2609.22442
<https://arxiv.org/abs/2609.22442>`_: the couplings of a 10 × 10 transmon array
to the modes of its metal package. They go from an analytic estimate (4.41) to
a full-wave model of the whole package (4.45); 4.46 then looks inside that
model term by term. They use gmsh and a scikit-fem Maxwell solver in place of HFSS (``pip install "quantum-metal[skfem]"``).
The notebooks are listed on the :doc:`../research` page.

.. nblinkgallery::

    4-Analysis/4.41-The-package-mode-on-paper
    4-Analysis/4.42-Four-ways-to-measure-a-coupling
    4-Analysis/4.43-Mesh-and-solve-the-10x10-processor
    4-Analysis/4.44-Every-coupling-from-one-eigenmode
    4-Analysis/4.45-Four-methods-one-full-wave-model
    4-Analysis/4.46-Beyond-the-dipole-multipoles-and-magnetic-coupling


The four parts
==============

.. grid:: 1 2 2 4
    :gutter: 2

    .. grid-item-card:: Part 1: First steps
        :link: first-steps
        :link-type: doc

        Place a component, build a four-qubit chip, save it, iterate on it.
        (5 notebooks)

    .. grid-item-card:: Part 2: From components to chip
        :link: components-to-chip
        :link-type: doc

        QComponents, routing, a full chip, and your own QComponent.
        (16 notebooks)

    .. grid-item-card:: Part 3: Render and export
        :link: render-and-export
        :link-type: doc

        Export to GDS, mesh with gmsh, render to Ansys, write a renderer.
        (5 notebooks)

    .. grid-item-card:: Part 4: Simulate and analyze
        :link: simulate-and-analyze
        :link-type: doc

        Open-source and Ansys simulation, then circuits to Hamiltonians.
        (26 notebooks)

Also: :doc:`../circuit-examples/index` (components and reference designs to
copy) and :doc:`../research` (published devices and results).

.. toctree::
    :maxdepth: 1
    :hidden:

    first-steps
    components-to-chip
    render-and-export
    simulate-and-analyze


.. raw:: html

    <a href="https://www.youtube.com/playlist?list=PLOFEBzvs-VvqHl5ZqVmhB_FcSqmLufsjb">
    Click for Video Tutorials</a><br><br>
    <table>
        <tr><td width="22%">
        <a href="https://www.youtube.com/playlist?list=PLOFEBzvs-VvqHl5ZqVmhB_FcSqmLufsjb">
	        <img src="https://www.gstatic.com/youtube/img/branding/youtubelogo/svg/youtubelogo.svg" width="100">
        </a>
        </td><td width="78%"></td></tr>
    </table>


External Workshops
==================

Independently-maintained workshop materials that exercise Quantum Metal
end-to-end (layout → simulation → analysis) using open-source EM solvers
via `SQDMetal <https://github.com/sqdlab/SQDMetal>`_.

- `QDW 2025 — tutorials_quantum_device_design
  <https://github.com/zlatko-minev/tutorials_quantum_device_design>`_
  *(historical, Metal pre-v0.5)* — 4 notebooks covering layout,
  transmon+resonator, qubit-qubit coupling, and an end-to-end project,
  simulated with **Palace** via SQDMetal.

- `QDW 2026 — qdw26-workshop-materials
  <https://github.com/quantum-device-consortium/qdw26-workshop-materials>`_
  *(active, near-mainline Metal)* — Dockerized re-tooling of the same
  4-notebook progression. Shared ``uv`` environment, JupyterLab + VS Code
  attach paths, Brev / cloud-instance support.


.. Hiding - Indices and tables
   :ref:`genindex`
   :ref:`modindex`
   :ref:`search`
