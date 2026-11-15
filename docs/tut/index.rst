.. _tutorials-overview:

=====
Learn
=====

The tutorial course, in four parts. Each part lists its notebooks in the
order to read them. New here? Start with the :doc:`../quickstart` page, then
Part 1, or pick a goal on :doc:`../choose-your-path`.

Want a result fast?
===================

.. grid:: 1 2 2 2
    :gutter: 2

    .. grid-item-card:: 1.3 Build a 4-qubit chip
        :class-header: sd-bg-primary sd-text-light
        :link: 1-Overview/1.3-Build-a-4-qubit-chip
        :link-type: doc

        Four transmons joined by meander CPWs. Runs in Colab.

    .. grid-item-card:: 2.21 Design a 4 qubit full chip
        :class-header: sd-bg-secondary sd-text-light
        :link: 2-From-components-to-chip/2.21-Design-a-4-qubit-full-chip
        :link-type: doc

        A complete chip, exported to GDS.


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
        (30 notebooks)

Also: :doc:`../circuit-examples/index` (components and reference designs to
copy) and :doc:`../research` (published devices and results).

.. toctree::
    :maxdepth: 1
    :hidden:

    first-steps
    components-to-chip
    render-and-export
    simulate-and-analyze


.. _videos_education:

Videos and education
====================

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

Qiskit Metal (now Quantum Metal) has a rich set of talks and tutorials across YouTube and community channels. Below are curated links to get you started, plus a call to add your own videos.

.. note::
   The legacy Qiskit Metal YouTube playlist targets an older version of the project, but much of the material is still useful for fundamentals. If you have updated walkthroughs, please add them here!

Contribute a video
------------------
- Have you recorded a tutorial, talk, or walkthrough using Metal? Open a PR and add your link to this page.

Overviews by Dr. Zlatko Minev
-----------------------------
All slides can be found on a `GitHub repo <https://github.com/zlatko-minev/zlatko-minev-quantum-repository>`_.

- `QDW Beginner Track (Day 1, Sessions 2–3): Superconducting qubits 101 — making your first qubit <https://www.youtube.com/watch?v=rUjePWndpiY>`_
- More Qiskit Metal/Quantum Device Workshop (QDW) videos: https://www.youtube.com/@uclaqcsa
- `Quantum Hardware Design: Energy, Circuits, and Metal (Qiskit Seminar Series) <https://www.youtube.com/watch?v=jjdYHZ0qxcY>`_
- `Superconducting Qubits: design, analysis, energy & Qiskit Metal (Berkeley) <https://www.youtube.com/watch?v=ggfQa6jBV3Y>`_
- `Qiskit Global Summer School (quantization lecture + full playlist) <https://www.youtube.com/playlist?list=PLOFEBzvs-VvqJwybFxkTiDzhf5E11p8BI>`_
  - Direct link to quantization lecture: https://www.youtube.com/watch?v=SDiiFOham6Y
- More lecture series by Minev: https://www.zlatko-minev.com/education

Community-driven tutorials
--------------------------
- `Qiskit Metal Introduction (video) <https://www.youtube.com/watch?v=tT96I2lgQx4>`_
- `Legacy Qiskit Metal playlist (older version) <https://www.youtube.com/playlist?list=PLOFEBzvs-VvqHl5ZqVmhB_FcSqmLufsjb>`_
- `Quantum Chip Design using HFSS (detailed series) <https://www.youtube.com/playlist?list=PLnK6MrIqGXsIS_97Nt-8R6uNrJXxMiOro>`_
- `Quantum Computer Hardware Chip Design - Qiskit Metal <https://www.youtube.com/watch?v=PU7Cz9BVhwA>`_
- `Qiskit Metal + KLayout + Blender: Rendering Tutorial <https://www.youtube.com/watch?v=NxArWX8WhPc>`_
- `Lab 9: Finding the cross-Kerr of a Transmon in a 3D Cavity using pyEPR in Qiskit Metal <https://www.youtube.com/watch?v=vCCVgfFAFwo>`_
- `CPW resonator design using Qiskit Metal (video 10) <https://www.youtube.com/watch?v=9INNvUQs3GM>`_
- `How to use Qiskit Metal (community tutorial) <https://www.youtube.com/watch?v=x4RXYUvQg24>`_
- `pyEPR original video tutorials <https://www.youtube.com/watch?v=fSRYvD-ITnQ>`_
- `Automatic multi-parameter design optimization for superconducting quantum devices (Lukas Splitthoff, QDesignOptimizer) <https://www.youtube.com/watch?v=M940wW7Taos>`_

Further reading & references
----------------------------
- `A Review of Design Concerns in Superconducting Quantum Circuits (Levenson-Falk, Shanto, 2024) <https://arxiv.org/html/2411.16967v2>`_
- Eriksson et al., *QDesignOptimizer based on ANMod: an automated, physics-guided, multi-parameter design optimizer for superconducting quantum devices*, `Quantum Sci. Technol. 11, 035024 (2026) <https://iopscience.iop.org/article/10.1088/2058-9565/ae7ab6>`_
- Minev et al., Energy-participation (EPR) quantization (see `arXiv:2010.00620 <https://arxiv.org/abs/2010.00620>`_, and pyEPR docs)
- Minev et al., Lumped Oscillator Model (LOM) quantization (see docs and Qiskit Metal papers)
- Kjaergaard et al., *Superconducting Qubits: Current State of Play*, Annu. Rev. Cond. Matt. Phys. 11, 369 (2020).
- Clarke and Wilhelm, *Superconducting quantum bits*, Nature 453, 1031 (2008).
- Devoret and Schoelkopf, *Superconducting Circuits for Quantum Information: An Outlook*, Science 339, 1169 (2013).
- Wendin, *Quantum information processing with superconducting circuits: A review*, Rep. Prog. Phys. 80, 106001 (2017).
- Krantz et al., *A quantum engineer’s guide to superconducting qubits*, Appl. Phys. Rev. 6, 021318 (2019).
- Kwon et al., *Gate-based superconducting quantum computing*, J. Appl. Phys. 129, 041102 (2021).
- Blais et al., *Circuit quantum electrodynamics*, Rev. Mod. Phys. 93, 025005 (2021).
- Gao et al., *Practical Guide for Building Superconducting Quantum Devices*, PRX Quantum 2, 040202 (2021).

.. dropdown:: Historical office-hours & tutorial recording log (2021–2023)

    Dated recordings from the original Qiskit Metal team's live tutorial and
    Q&A series. Superseded as a going concern (the series is not ongoing), but
    many of the individual recordings are still useful references.

    .. list-table::
       :header-rows: 1

       * - Date
         - Type
         - Topic
       * - April 1
         - Tutorial
         - `Introduction to Qiskit Metal <https://youtu.be/NCNv3YPvveM>`_
       * - April 8
         - Tutorial
         - Overview: Qubit chip design-flow, `Part 1 <https://youtu.be/bsrsKZLTkTo>`_
       * - April 15
         - Tutorial
         - Overview: Qubit chip design-flow, `Part 2 <https://youtu.be/fj1hpAqZfmg>`_
       * - April 22
         - Forum
         - First impressions — Qiskit Metal team answers questions and invites feedback.
       * - April 29
         - Tutorial
         - `QComponents <https://youtu.be/ljzWF3dNHEU>`_: how to use, modify, and extend the Qiskit Metal library.
       * - May 6
         - Forum
         - Q&A — customizing Qiskit Metal designs.
       * - May 6
         - Offline recordings
         - Analysis methods: `Capacitance and frequency control <https://youtu.be/rY7Os7B9sg0>`_,
           `Eigenmode & Energy Participation Ratio <https://youtu.be/mvT9Fb7UGH4>`_,
           `Energy Participation Ratio Theory <https://youtu.be/ITCkKfjxcbc>`_,
           `EPR Quantization with Code Example <https://youtu.be/FXmPyYEyL9U>`_,
           `Finish Eigenmode + Impedance Analysis <https://youtu.be/4jBVdHzmJdw>`_,
           `Impedance Analysis Example <https://youtu.be/Bi8ZVAq-0tw>`_
       * - May 13
         - Tutorial
         - `Quantum Analysis 101 <https://youtu.be/QIr2Rlj1cpI>`_
       * - May 20
         - Tutorial
         - `Introduction to the Transmon Qubit <https://youtu.be/6KgOaU1BAxg>`_
       * - May 27
         - Tutorial
         - `Physics of the Cooper Pair Box Transmon <https://youtu.be/Ql8AS4Iay-Q>`_
       * - June 3
         - Tutorial
         - `Parametric Sweeps <https://youtu.be/ZRsk5dvH1K0>`_, `Github Contribution How-to <https://youtu.be/rJWo1Pt19vI>`_
       * - July 15
         - Tutorial
         - `Energy Participation Ratio in Qiskit Metal <https://youtu.be/HJNKG5z6Jys>`_,
           `New Feature: LOM Analysis for Composite Systems <https://youtu.be/XpnTJSBjb8E>`_,
           `New Feature: Export Design to Script <https://youtu.be/JpoD3SjObHc>`_
       * - Sept 23
         - Tutorial
         - `Making a QComponent from Scratch <https://youtu.be/5iEOJDMWXDE>`_
       * - Oct 7
         - Tutorial
         - `New LOM Analysis Methodology — Part 1 <https://youtu.be/S8Wx2Lo2CxQ>`_
       * - Oct 21
         - Tutorial
         - `New LOM Analysis Methodology — Part 2 <https://youtu.be/b2azGJ-RCjk>`_
       * - Nov 4
         - Tutorial
         - `New LOM Analysis Methodology — Part 3 <https://youtu.be/kWFYYUa0V3k>`_
       * - Nov 18
         - Forum
         - Q&A — ask anything to the Qiskit Metal team.
       * - Jan 13, 2022
         - Forum
         - Q&A — open discussion with the Qiskit Metal team.
       * - Jan 27, 2022
         - Forum
         - Helping users generate a custom component.
       * - Feb 10, 2022
         - Tutorial
         - `GUI Icons <https://youtu.be/aE2Dsc67S8w>`_, `Jaynes-Cummings Model <https://youtu.be/dtwL_K-TJtY>`_,
           `Template Options, Default Options <https://youtu.be/qKLyEyW7cbQ>`_
       * - Feb 24, 2022
         - Tutorial
         - `Flip Chip, by guest speaker Sandoko Kosen <https://youtu.be/BUojR6Uti5Q>`_
       * - Mar 10, 2022
         - Forum
         - Metal community feedback session.
       * - Mar 24, 2022
         - Tutorial
         - `Time Evolution for the CR Gate <https://www.youtube.com/watch?v=icDryjZrUQ4>`_
       * - Aug 4, 2022
         - Tutorial
         - `Open-Source Rendering and Simulation Solution for Qiskit Metal <https://youtu.be/sA0uXtCAhWw>`_
       * - Aug 11, 2022
         - Tutorial
         - `Qiskit Metal E21: Quantum Spice Web App — Sneak Peak <https://youtu.be/3UE57DaG-HI>`_
       * - Feb 2, 2023
         - Tutorial
         - `Qiskit Metal E22: Open-Source Simulation Renderers — Gmsh & ElmerFEM <https://youtu.be/84j3l_9fHko>`_

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
