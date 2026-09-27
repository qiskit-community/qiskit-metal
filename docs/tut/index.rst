.. _tutorials-overview:

=========
Tutorials
=========

Overview
========


.. nbgallery::
    :glob:

    1-Overview/*


Components
==========

-----------------
Using QComponents
-----------------

.. nbgallery::
    :glob:

    2-From-components-to-chip/2.0*


---------------------------
Routing between QComponents
---------------------------

.. nbgallery::
    :glob:

    2-From-components-to-chip/2.1*


---------------------------------
My first full quantum chip design
---------------------------------

.. nbgallery::
    :glob:

    2-From-components-to-chip/2.2*


----------------------------------
How do I make my custom QComponent
----------------------------------

.. nbgallery::
    :glob:

    2-From-components-to-chip/2.3*


Renderers
=========


.. nbgallery::
    :glob:

    3-Renderers/*


Analysis
========

--------------------------
Core - EM and quantization
--------------------------

.. nbgallery::
    :glob:

    4-Analysis/4.0*


-----------------
Analysis examples
-----------------

.. nbgallery::
    :glob:

    4-Analysis/4.1*


-----------------
Parametric sweeps
-----------------

.. nbgallery::
    :glob:

    4-Analysis/4.2*


------------------
Hamiltonian models
------------------

.. nbgallery::
    :glob:

    4-Analysis/4.3*
    4-Analysis/Design-and-Simulation-of-a-Cross-Resonance-Gate
    4-Analysis/cQED-with-the-Jaynes-Cummings-Interaction-Model


---------------------------------
Package modes and qubit couplings
---------------------------------

Reproduces R. Molavi *et al.*, `arXiv:2609.22442
<https://arxiv.org/abs/2609.22442>`_: the couplings of a 10 × 10 transmon array
to the modes of its metal package, with gmsh and a scikit-fem Maxwell solver in
place of HFSS.

.. nbgallery::
    :glob:

    4-Analysis/4.4*


Full-Chip Design Examples
=========================

End-to-end reference layouts built from stock Quantum Metal components,
adapted with attribution from the open-source `SQDMetal
<https://github.com/sqdlab/SQDMetal>`_ benchmark devices
(`arXiv:2511.01220 <https://arxiv.org/abs/2511.01220>`_).

.. nbgallery::
    :glob:

    full-design-examples/*


Quick Topics
============

.. nbgallery::
    :glob:

    quick-topics/*


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
