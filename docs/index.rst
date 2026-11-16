##############################################################
Qiskit Metal is now Quantum Metal
##############################################################

.. container:: qm-hero

   .. raw:: html

      <div class="qm-hero-art" aria-hidden="true">
      <svg viewBox="0 0 1200 380" preserveAspectRatio="xMidYMid slice" focusable="false">
        <g>
          <path class="pad" d="M140 140h20v-20h20v20h20v20h-20v20h-20v-20h-20z"/>
          <path class="tr" pathLength="1" style="--i:0" d="M140 140h20v-20h20v20h20v20h-20v20h-20v-20h-20z"/>
          <path class="tr" pathLength="1" style="--i:1" d="M170 180v90h140"/>
          <path class="tr" pathLength="1" style="--i:2" d="M-20 300h330h30v-90h40v90h40v-90h40v90h40v-90h40v90h30h140"/>
          <path class="tr" pathLength="1" style="--i:3" d="M60 60h60v40M60 60v-40"/>
          <path class="pad" d="M40 4h40v32h-40z"/>
          <path class="tr" pathLength="1" style="--i:4" d="M700 330h520"/>
          <path class="tr" pathLength="1" style="--i:5" d="M780 330v-70h40v70m40 0v-70h40v70m40 0v-70h40v70"/>
          <path class="tr" pathLength="1" style="--i:6" d="M1100 250h20v-20h20v20h20v20h-20v20h-20v-20h-20z"/>
          <path class="pad" d="M1100 250h20v-20h20v20h20v20h-20v20h-20v-20h-20z"/>
        </g>
        <g>
          <circle class="sph" cx="1000" cy="120" r="64"/>
          <ellipse class="sph sph-dash" cx="1000" cy="120" rx="64" ry="20"/>
          <ellipse class="sph sph-dash" cx="1000" cy="120" rx="20" ry="64"/>
          <path class="vec" d="M1000 120v-64"/>
          <circle class="tip" r="4.5" cx="0" cy="0"/>
        </g>
      </svg>
      </div>

   **Design superconducting quantum chips in Python, then simulate them.**

   Open source and community-maintained. One Python API, with an optional desktop GUI,
   takes a chip from layout to Hamiltonian.

   .. grid:: 1 2 2 2
      :gutter: 2
      :class-container: qm-hero-buttons

      .. grid-item::

         .. button-ref:: quickstart
            :ref-type: doc
            :color: primary
            :shadow:
            :expand:

            Quick start

      .. grid-item::

         .. button-ref:: tut/index
            :ref-type: doc
            :color: primary
            :outline:
            :expand:

            Learn: the tutorial course

   .. raw:: html

      <div class="qm-stage">
        <div class="qm-scene">
          <figure class="qm-card qm-gui">
            <img src="_static/home/gui-chip.webp" width="1400" height="1232" alt="The Quantum Metal desktop GUI showing a four-qubit chip layout with its component list and options.">
          </figure>
          <figure class="qm-card qm-methods">
            <img src="_static/home/methods.webp" width="1162" height="704" alt="Four analysis methods side by side: capacitance extraction, eigenmode and field, impedance and scattering parameters, and the transmon Hamiltonian with its Bloch sphere." loading="lazy">
          </figure>
        </div>
      </div>
      <p class="qm-credit">Images: Z. Minev</p>

.. container:: qm-section

   .. rubric:: What is Quantum Metal?
      :class: qm-h2

   Designing quantum devices is a multi-step process that connects traditionally
   disparate worlds. Quantum Metal automates it, from layout to Hamiltonian, in
   a simple, open, community-driven framework.

   .. grid:: 1 2 2 4
      :gutter: 3
      :class-container: qm-steps4

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

   Looking for one specific task, such as routing a CPW or exporting GDS? See
   :doc:`how-do-i`.

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

   .. container:: qm-cta

      .. button-ref:: built-with-metal
         :ref-type: doc
         :color: primary
         :outline:

         Devices and papers

.. container:: qm-section

   .. rubric:: Built on Quantum Metal
      :class: qm-h2

   Tools from the community that use it as their design layer:
   :doc:`SQuADDS, SQDMetal, QDesignOptimizer and more <ecosystem>`.

.. container:: qm-section

   .. rubric:: Community
      :class: qm-h2

   Questions, ideas and bug reports are welcome.

   .. container:: qm-chips

      * `Discord <https://discord.gg/FPNybyfpxd>`__
      * `GitHub issues <https://github.com/qiskit-community/qiskit-metal/issues>`__
      * `Quantum Device Workshop <https://qdc-qcsa.org/qdw/2026/info>`__
      * `Quantum Device Consortium <https://qdc-qcsa.vercel.app>`__


.. toctree::
    :maxdepth: 2
    :caption: Get Started
    :hidden:

    Quick Start<quickstart>
    Installing Quantum Metal<installation>
    Choose Your Path<choose-your-path>

.. toctree::
    :maxdepth: 2
    :caption: Showcase & Learn
    :hidden:

    Device Images and Papers<built-with-metal>
    Built on Quantum Metal<ecosystem>
    Reproduced Devices (Notebooks)<research>
    Learn<tut/index>
    Examples<circuit-examples/index>
    How Do I...?<how-do-i>

.. toctree::
    :maxdepth: 1
    :caption: How It Works
    :hidden:

    Quantum Metal Workflow<workflow>
    Quantization Methods<quantization>
    Simulation Pathways<simulation-pathways>
    GDS in KLayout<klayout>
    Desktop GUI or Headless<headless-usage>
    Scripting and Agent Use<orchestration>
    GUI Navigation & Shortcuts<gui-shortcuts>

.. toctree::
    :maxdepth: 2
    :caption: API Reference
    :hidden:

    Overview<overview>
    QDesigns<apidocs/designs>
    QComponents<apidocs/qlibrary>
    Component Catalog<qcomponents-gallery>
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
