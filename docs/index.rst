##############################################################
Quantum Metal (formerly Qiskit Metal)
##############################################################

.. container:: qm-hero

   .. image:: images/logo1.png
      :alt: Quantum Metal logo
      :class: qm-hero-logo

   **Design superconducting quantum chips in Python, then simulate them.**

   Open source and community-maintained. One Python API, with an optional desktop GUI,
   takes a chip from layout to Hamiltonian. No Qt required: it runs in a notebook
   or a plain script.

.. container:: qm-section

   .. rubric:: What is Quantum Metal?
      :class: qm-h2

   Designing quantum devices is a multi-step process that connects traditionally
   disparate worlds. Quantum Metal automates it, from layout to Hamiltonian, in
   a simple, open, community-driven framework.

   .. grid:: 1 2 2 4
      :gutter: 3

      .. grid-item-card:: Design
         :link: qdesign
         :link-type: ref

         Chips as Python objects: parametric layout, pins, routing, design rules.

      .. grid-item-card:: Components
         :link: qcomponents-gallery
         :link-type: doc

         Every transmon, coupler, route, resonator, termination and lumped
         element shipped with Quantum Metal.

      .. grid-item-card:: Render
         :link: qrenderer
         :link-type: ref

         Export to GDS, gmsh meshes, Ansys and ElmerFEM.

      .. grid-item-card:: Analyze
         :link: qanalysis
         :link-type: ref

         Capacitance, eigenmodes, energy participation, Hamiltonians.

.. container:: qm-section

   .. rubric:: Built on Quantum Metal
      :class: qm-h2

   Tools from the community that use it as their design layer:
   :doc:`SQuADDS, SQDMetal, QDesignOptimizer and more <ecosystem>`.

.. container:: qm-section

   .. rubric:: Community
      :class: qm-h2

   .. grid:: 1 2 2 4
      :gutter: 3

      .. grid-item-card:: Community Discord

         Fastest way to reach maintainers and the broader community.

         .. button-link:: https://discord.gg/FPNybyfpxd
            :color: primary
            :outline:
            :expand:

            Join Discord

      .. grid-item-card:: Qiskit Slack #metal

         Former main community workspace, being replaced by Discord.

         .. button-link:: https://qiskit.slack.com/archives/C01R8KP5WP7
            :color: primary
            :outline:
            :expand:

            Join #metal on Slack

      .. grid-item-card:: Quantum Device Workshop (QDW)

         Annual workshop hosted at UCLA/USC.

         .. button-link:: https://qdc-qcsa.org/qdw/2026/info
            :color: primary
            :outline:
            :expand:

            QDW 2026 information

      .. grid-item-card:: Quantum Device Consortium (QDC)

         Community organization stewarding Quantum Metal.

         .. button-link:: https://qdc-qcsa.vercel.app
            :color: primary
            :outline:
            :expand:

            QDC website

         .. button-link:: https://discord.gg/FPNybyfpxd
            :color: secondary
            :outline:
            :expand:

            QDC Discord

.. container:: qm-section

   .. rubric:: Devices designed with Quantum Metal
      :class: qm-h2

   Chips designed or rebuilt with Quantum Metal, from community fabrication to
   published processors. More device images, papers and theses are on
   :doc:`built-with-metal`.

{{ QM_FABRICATED:4 }}

   .. nblinkgallery::

       circuit-examples/F.Small-quantum-chips/53-Wallraff_17Qubit_SurfaceCode
       circuit-examples/F.Small-quantum-chips/52-Barends_5Qubit_Xmon_Processor
       circuit-examples/F.Small-quantum-chips/Full-Physical-Design-of-iSWAP-Gates
       tut/2-From-components-to-chip/2.21-Design-a-4-qubit-full-chip

   .. grid:: 1 2 3 3
      :gutter: 3
      :class-container: qm-hero-buttons

      .. grid-item::

         .. button-ref:: quickstart
            :ref-type: doc
            :color: primary
            :shadow:
            :expand:

            Quick start

      .. grid-item::

         .. button-ref:: built-with-metal
            :ref-type: doc
            :color: primary
            :outline:
            :expand:

            Devices and papers

      .. grid-item::

         .. button-ref:: tut/index
            :ref-type: doc
            :color: primary
            :outline:
            :expand:

            Learn: the tutorial course

.. note::
    **Rebrand in progress: Qiskit Metal → Quantum Metal.**
    The PyPI package is ``quantum-metal`` (v0.5+).
    A future release will rename the import path from ``qiskit_metal``
    to ``quantum_metal``; no version has been set for that yet.
    See :doc:`installation`.

.. toctree::
    :maxdepth: 2
    :caption: Get Started
    :hidden:

    Quick Start<quickstart>
    Installing Quantum Metal<installation>
    Choose Your Path<choose-your-path>
    Running Without the Desktop GUI<headless-usage>
    Built on Quantum Metal<ecosystem>

.. toctree::
    :maxdepth: 2
    :caption: Showcase & Learn
    :hidden:

    Device Images and Papers<built-with-metal>
    Reproduced Devices (Notebooks)<research>
    Learn<tut/index>
    Examples<circuit-examples/index>

.. toctree::
    :maxdepth: 1
    :caption: How It Works
    :hidden:

    Quantum Metal Workflow<workflow>
    Quantization Methods<quantization>
    Simulation Pathways<simulation-pathways>
    GDS in KLayout<klayout>
    GUI Navigation & Shortcuts<gui-shortcuts>

.. toctree::
    :maxdepth: 2
    :caption: API Reference
    :hidden:

    Overview<overview>
    QDesigns<apidocs/designs>
    QComponents<apidocs/qlibrary>
    Analyses<apidocs/analyses>
    QRenderers<apidocs/renderers>
    Toolbox<apidocs/toolbox_metal>
    QGeometry<apidocs/qgeometries>
    GUI<apidocs/gui>

.. toctree::
    :maxdepth: 1
    :caption: Project
    :hidden:

    Roadmap<roadmap>
    Frequently Asked Questions<faq>

.. toctree::
    :maxdepth: 2
    :caption: Community & Contributing
    :hidden:

    Contributor Guide<contributor-guide>
    Architecture<architecture>
    Code of Conduct<https://github.com/Qiskit/qiskit/blob/master/CODE_OF_CONDUCT.md>

.. Per-class autodoc stubs in ``apidocs/`` are reached via the
   autosummary ``:toctree: .`` directives in each module's
   ``__init__.py`` (e.g. ``qiskit_metal._gui/__init__.py`` lists
   ``MetalGUI`` under autosummary, which registers
   ``apidocs/qiskit_metal._gui.MetalGUI`` in a toctree). No hidden
   glob is needed.
