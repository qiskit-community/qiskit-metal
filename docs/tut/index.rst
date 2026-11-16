.. _tutorials-overview:

=====
Learn
=====

The tutorial course, in four parts. Each part lists its notebooks in the
order to read them. New here? Start with the :doc:`../quickstart` page, then
Part 1, or pick a goal on :doc:`../choose-your-path`. Looking for one task?
See :doc:`../how-do-i`.

.. grid:: 1 2 4 4
    :gutter: 2

    .. grid-item::

        .. button-ref:: learn-part1
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            1 First steps

    .. grid-item::

        .. button-ref:: learn-part2
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            2 Components to chip

    .. grid-item::

        .. button-ref:: learn-part3
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            3 Render and export

    .. grid-item::

        .. button-ref:: learn-part4
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            4 Simulate and analyze

Want a result fast?
===================

.. nblinkgallery::

    1-Overview/1.1-Quick-start
    1-Overview/1.3-Build-a-4-qubit-chip
    2-From-components-to-chip/2.21-Design-a-4-qubit-full-chip

.. _learn-part1:

Part 1: First steps
===================

Place a component, build a four-qubit chip, save it, iterate on it.
:doc:`All 5 notebooks <first-steps>`.

.. nblinkgallery::

    1-Overview/1.2-Bird's-eye-view-of-Quantum-Metal
    1-Overview/1.4-Saving-Your-Chip-Design
    1-Overview/1.5-Parametric-design---iterate-and-compare

.. _learn-part2:

Part 2: From components to chip
===============================

QComponents, routing, a full chip, design rules, and your own QComponent.
:doc:`All 16 notebooks <components-to-chip>`.

.. nblinkgallery::

    2-From-components-to-chip/2.01-How-to-use-a-QComponent
    2-From-components-to-chip/2.11-Routing-101
    2-From-components-to-chip/2.12-Simple-Meander
    2-From-components-to-chip/2.24-Design-rule-checking
    2-From-components-to-chip/2.31-Create-a-QComponent-Basic

.. _learn-part3:

Part 3: Render and export
=========================

Export to GDS, mesh with gmsh, render to Ansys, write a renderer.
:doc:`All 5 notebooks <render-and-export>`.

.. nblinkgallery::

    3-Renderers/3.1-Introduction-to-QRenderers
    3-Renderers/3.2-Export-your-design-to-GDS
    3-Renderers/3.3-Render-your-design-to-Ansys
    3-Renderers/3.5-Render-your-design-to-Gmsh

.. _learn-part4:

Part 4: Simulate and analyze
============================

Open-source and Ansys simulation, then circuits to Hamiltonians. See
:doc:`../simulation-pathways` for what each solver computes.
:doc:`All 30 notebooks <simulate-and-analyze>`.

.. nblinkgallery::

    4-Analysis/4.19-Analyze-a-transmon-using-ElmerFEM
    4-Analysis/4.01-Capacitance-and-LOM
    4-Analysis/4.02-Eigenmode-and-EPR
    4-Analysis/4.33-Transmon-analytics

Featured: package modes and qubit couplings
===========================================

Six notebooks follow R. Molavi *et al.*, `arXiv:2609.22442
<https://arxiv.org/abs/2609.22442>`_: the couplings of a 10 × 10 transmon array
to the modes of its metal package. They go from an analytic estimate (4.41) to
a full-wave model of the whole package (4.45); 4.46 then looks inside that
model term by term. They use gmsh and a scikit-fem Maxwell solver in place of
HFSS (``pip install "quantum-metal[skfem]"``). Also on the :doc:`../research`
page.

.. nblinkgallery::

    4-Analysis/4.41-The-package-mode-on-paper
    4-Analysis/4.42-Four-ways-to-measure-a-coupling
    4-Analysis/4.43-Mesh-and-solve-the-10x10-processor
    4-Analysis/4.44-Every-coupling-from-one-eigenmode
    4-Analysis/4.45-Four-methods-one-full-wave-model
    4-Analysis/4.46-Beyond-the-dipole-multipoles-and-magnetic-coupling

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

Talks, lectures and community walkthroughs. The legacy Qiskit Metal playlist
targets an older version, but much of it still teaches the fundamentals.

.. button-link:: https://www.youtube.com/playlist?list=PLOFEBzvs-VvqHl5ZqVmhB_FcSqmLufsjb
    :color: primary
    :outline:

    Legacy video playlist (YouTube)

.. grid:: 1 1 3 3
    :gutter: 3

    .. grid-item-card:: Start here
        :class-card: sd-shadow-sm

        * `QDW Beginner Track: superconducting qubits 101, making your first qubit <https://www.youtube.com/watch?v=rUjePWndpiY>`_
        * `Qiskit Metal introduction <https://www.youtube.com/watch?v=tT96I2lgQx4>`_
        * `How to use Qiskit Metal (community tutorial) <https://www.youtube.com/watch?v=x4RXYUvQg24>`_
        * `Quantum computer hardware chip design <https://www.youtube.com/watch?v=PU7Cz9BVhwA>`_

    .. grid-item-card:: Lectures by Z. Minev
        :class-card: sd-shadow-sm

        Slides are on a `GitHub repo <https://github.com/zlatko-minev/zlatko-minev-quantum-repository>`_.

        * `Quantum hardware design: energy, circuits, and Metal (Qiskit Seminar Series) <https://www.youtube.com/watch?v=jjdYHZ0qxcY>`_
        * `Superconducting qubits: design, analysis, energy (Berkeley) <https://www.youtube.com/watch?v=ggfQa6jBV3Y>`_
        * `Qiskit Global Summer School playlist <https://www.youtube.com/playlist?list=PLOFEBzvs-VvqJwybFxkTiDzhf5E11p8BI>`_, with the `quantization lecture <https://www.youtube.com/watch?v=SDiiFOham6Y>`_
        * `More QDW videos <https://www.youtube.com/@uclaqcsa>`_ and `more lecture series <https://www.zlatko-minev.com/education>`_

    .. grid-item-card:: Community tutorials
        :class-card: sd-shadow-sm

        * `Chip design using HFSS (series) <https://www.youtube.com/playlist?list=PLnK6MrIqGXsIS_97Nt-8R6uNrJXxMiOro>`_
        * `Metal + KLayout + Blender rendering <https://www.youtube.com/watch?v=NxArWX8WhPc>`_
        * `CPW resonator design (video 10) <https://www.youtube.com/watch?v=9INNvUQs3GM>`_
        * `Cross-Kerr of a transmon in a 3D cavity with pyEPR (Lab 9) <https://www.youtube.com/watch?v=vCCVgfFAFwo>`_
        * `pyEPR video tutorials <https://www.youtube.com/watch?v=fSRYvD-ITnQ>`_
        * `Multi-parameter design optimization, QDesignOptimizer (L. Splitthoff) <https://www.youtube.com/watch?v=M940wW7Taos>`_

Recorded a walkthrough with Metal? Open a PR and add your link to this page.

.. dropdown:: Further reading and references

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
