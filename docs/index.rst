##############################################################
Quantum Metal (formerly Qiskit Metal)
##############################################################

Quantum Device Design & Analysis (Q-EDA)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: images/logo1.png
   :alt: Quantum Metal logo

**Quantum Metal | Open source · Community-maintained quantum EDA**

Design and analyze superconducting quantum chips with a Python API + optional GUI
that plugs into your favourite EDA tools.
No Qt required — works headlessly in any Jupyter notebook or plain Python script.

.. grid:: 1 2 2 4
   :gutter: 2

   .. grid-item-card:: 🚀 Install
      :class-header: sd-bg-primary sd-text-light

      .. button-ref:: installation
         :ref-type: doc
         :color: primary
         :outline:
         :expand:

         Get started in 60 seconds

   .. grid-item-card:: 📚 Tutorials
      :class-header: sd-bg-secondary sd-text-light

      .. button-ref:: tut/index
         :ref-type: doc
         :color: secondary
         :outline:
         :expand:

         Hands-on notebooks

   .. grid-item-card:: 🧩 Component Gallery
      :class-header: sd-bg-primary sd-text-light

      .. button-ref:: qcomponents-gallery
         :ref-type: doc
         :color: primary
         :outline:
         :expand:

         Browse every QComponent visually

   .. grid-item-card:: 💬 Community
      :class-header: sd-bg-secondary sd-text-light

      .. button-link:: https://discord.gg/kaZ3UFuq
         :color: secondary
         :outline:
         :expand:

         Join the Discord

.. rubric:: What is Quantum Metal?

Designing quantum devices is the bedrock of the quantum ecosystem, but it is a
difficult, multi-step process that connects traditionally disparate worlds.
Quantum Metal automates and streamlines this process — from layout to Hamiltonian —
in a simple, open, community-driven framework.

.. grid:: 2 2 2 4
   :gutter: 1

   .. grid-item-card:: Quantum Device Design
      :class-header: sd-bg-primary sd-text-light
      :link: qdesign
      :link-type: ref

      :ref:`qdesign`

   .. grid-item-card:: Quantum Device Components
      :class-header: sd-bg-secondary sd-text-light
      :link: qcomponents-gallery
      :link-type: doc

      Visual catalog: every transmon, coupler, route, resonator,
      termination, and lumped element shipped with Quantum Metal.

   .. grid-item-card:: Quantum Renderer
      :class-header: sd-bg-primary sd-text-light
      :link: qrenderer
      :link-type: ref

      :ref:`qrenderer`

   .. grid-item-card:: Quantum Analysis
      :class-header: sd-bg-secondary sd-text-light
      :link: qanalysis
      :link-type: ref

      :ref:`qanalysis`

.. rubric:: Community

.. grid:: 1 2 2 4
   :gutter: 1

   .. grid-item-card:: Community Discord
      :class-header: sd-bg-secondary sd-text-light

      Fastest way to reach maintainers and the broader community.

      .. button-link:: https://discord.gg/kaZ3UFuq
         :color: primary
         :outline:
         :expand:

         Join Discord

   .. grid-item-card:: Qiskit Slack #metal
      :class-header: sd-bg-primary sd-text-light

      Former main community workspace, being replaced by Discord.

      .. button-link:: https://qiskit.slack.com/archives/C01R8KP5WP7
         :color: primary
         :outline:
         :expand:

         Join #metal on Slack

   .. grid-item-card:: Quantum Device Workshop (QDW)
      :class-header: sd-bg-secondary sd-text-light

      Annual workshop hosted at UCLA/USC.

      .. button-link:: https://qdw-ucla.squarespace.com/
         :color: primary
         :outline:
         :expand:

         QDW site

      .. button-link:: https://qdw-ucla.squarespace.com/qdw2026
         :color: secondary
         :outline:
         :expand:

         Sign for 2026

   .. grid-item-card:: Quantum Device Consortium (QDC)
      :class-header: sd-bg-primary sd-text-light

      Community organization stewarding Quantum Metal.

      .. button-link:: https://qdc-qcsa.vercel.app
         :color: primary
         :outline:
         :expand:

         QDC website

      .. button-link:: https://discord.gg/kaZ3UFuq
         :color: secondary
         :outline:
         :expand:

         QDC Discord

.. note::
    **Rebrand in progress: Qiskit Metal → Quantum Metal.**
    The PyPI package is ``quantum-metal`` (v0.5+; current: v0.7.0).
    A future release (target v0.8–v1.0) will rename the import path from
    ``qiskit_metal`` to ``quantum_metal``.
    See :doc:`installation` and :doc:`migration-to-v0.7.0`.

.. toctree::
    :maxdepth: 2
    :caption: Get Started
    :hidden:

    Installing Quantum Metal<installation>
    Quick Start<tut/1-Overview/1.1-Quick-start>

.. toctree::
    :maxdepth: 1
    :caption: Tutorials
    :hidden:

    Tutorials<tut/index>
    QComponent Gallery<qcomponents-gallery>
    Example Designs<circuit-examples/index>
    Videos & Education<videoseducation>

.. toctree::
    :maxdepth: 1
    :caption: Ecosystem
    :hidden:

    Built on / with Quantum Metal<ecosystem>

.. toctree::
    :maxdepth: 2
    :caption: Concepts
    :hidden:

    Quantum Metal Workflow<workflow>
    Frequently Asked Questions<faq>

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
    :maxdepth: 2
    :caption: Community & Contributing
    :hidden:

    Contributor Guide<contributor-guide>
    Architecture<architecture>
    Using Quantum Metal without Qt<headless-usage>
    Migrating to v0.7.0<migration-to-v0.7.0>
    Code of Conduct<https://github.com/Qiskit/qiskit/blob/master/CODE_OF_CONDUCT.md>

.. Per-class autodoc stubs in ``apidocs/`` are reached via the
   autosummary ``:toctree: .`` directives in each module's
   ``__init__.py`` (e.g. ``qiskit_metal._gui/__init__.py`` lists
   ``MetalGUI`` under autosummary, which registers
   ``apidocs/qiskit_metal._gui.MetalGUI`` in a toctree). No hidden
   glob is needed.
