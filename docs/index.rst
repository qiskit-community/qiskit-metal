##############################################################
Quantum Metal (formerly Qiskit Metal)
##############################################################


Quantum Device Design & Analysis (Q-EDA)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. attention::

    **v0.5 transition in progress.** Qiskit Metal is officially becoming **Quantum Metal**.
    The Python import path remains ``qiskit_metal`` for now; a follow-up release will update it.
    The PyPI package ``qiskit-metal`` stays archived at the pre-0.5 state—install v0.5 **from source**
    via the :doc:`installation </installation>` guide. For details on the transition and the roadmap, see the :doc:`Roadmap </workflow>`. 
    
    **Breaking changes should be expected at least until v0.6.** Thereafter, patch version updates (v0.6.x) will maintain compatibility with the previous version. Minor version updates (v0.x.y) will add new features with potential breaking changes. We will switch to `SemVer <https://semver.org>`_ or `EffVer <https://jacobtomlinson.dev/effver/>`_ for versioning after v1.0 (release date TBD).

.. hint::
    **Community support?**
    Join the Quantum Device Community (QDC) Discord and Quantum Metal channel:
    `discord.gg/kaZ3UFuq <https://discord.gg/kaZ3UFuq>`_.
    You can also join the the Slack channel `#metal <https://qiskit.slack.com/archives/C01R8KP5WP7>`_
    in the `Qiskit workspace <https://qisk.it/join-slack>`_, which we will slowly phase out.

    You can open this documentation using

    .. code-block:: python

        import qiskit_metal
        qiskit_metal.open_docs()

.. image:: images/logo1.png
   :alt: Missing Logo Diagram

**Quantum Metal | Open source • Community maintained & driven quantum EDA • API**

Design and analyze superconducting quantum chips with a Python API + GUI that plugs into your favorite tools.
Leverages existing EDA stacks, automates tedious workflows, and keeps best practices baked in.

.. grid:: 1 2 2 2
   :gutter: 1

   .. grid-item-card:: Get Started
      :class-header: sd-bg-primary sd-text-light


      .. button-ref:: installation
         :ref-type: doc
         :color: primary
         :outline:
         :expand:

         Install

      .. button-ref:: videoseducation
         :ref-type: doc
         :color: primary
         :outline:
         :expand:

         Tutorials (videos)

      .. button-ref:: tut/index
         :ref-type: doc
         :color: primary
         :outline:
         :expand:

         Tutorials index

      .. button-ref:: videoseducation
         :ref-type: doc
         :color: primary
         :outline:
         :expand:

         Videos & Education

   .. grid-item-card:: Quick links
      :class-header: sd-bg-secondary sd-text-light

      .. grid:: 1 1 1 1
         :gutter: 1

         .. grid-item::
            :child-align: start

            .. button-ref:: overview
               :ref-type: doc
               :color: primary
               :outline:
               :expand:

               API Overview

         .. grid-item::
            :child-align: start

            .. button-ref:: apidocs/qlibrary
               :ref-type: doc
               :color: primary
               :outline:
               :expand:

               API Reference


         .. grid-item::
            :child-align: start

            .. button-ref:: contributor-guide
               :ref-type: doc
               :color: primary
               :outline:
               :expand:

               Contribute

.. dropdown:: Live tutorials and Q&A
   :icon: calendar
   :open:

   We host live tutorials and Q&A sessions. Announcements for future tutorials are posted in the #metal channel.

.. grid:: 1 2 2 4
   :gutter: 1

   .. grid-item-card:: Community Discord
      :class-header: sd-bg-secondary sd-text-light

      Fastest way to reach maintainers and the broader community.
      Open community server for Quantum Metal users and collaborators.

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

   .. grid-item-card:: Quantum Device Workshop (QDW) Annual Conference
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

      Community organization stewarding Quantum Metal and companion tools.

      .. button-link:: https://qdc-qcsa.vercel.app
         :color: primary
         :outline:
         :expand:

         QDC website & governance

      .. button-link:: https://discord.gg/kaZ3UFuq
         :color: secondary
         :outline:
         :expand:

         QDC Discord


.. rubric:: **Qiskit Metal Vision**:

Designing quantum devices is the bedrock of the quantum ecosystem,
but it is a difficult, multi-step process that connects traditionally disparate worlds.
Metal is automating and streamlining this process.
Our vision is to develop a community-driven universal platform capable
of orchestrating quantum chip development from concept to fabrication in
a simple and open framework.

We want to accelerate, and to lower the barrier to, innovation of  quantum devices.
Today at the IEEE Quantum Week Conference, the team discussed their vision for this first-of-its-kind project. Led by quantum physicist Zlatko Minev and
developed with other IBM Quantum team members, this project is meant for those interested in quantum hardware design: a suite of design automation
tools that can be used to devise and analyze superconducting devices, with a focus on being able to integrate the best tools into a quantum hardware
designer’s workflow. We’ve code-named the project Qiskit Metal.

We hope that as a community, we might make the process of quantization — bridging the gap between pieces of a superconducting metal on a quantum chip
with the computational mathematics of Hamiltonians and Hilbert spaces — available to anyone with a curious mind and a laptop. We want to make quantum
device design a streamlined process that automates the laborious tasks as it does with conventional electronic device design. We are writing software
with built-in best practices and cutting-edge quantum analysis techniques, all this while seamlessly leveraging the power of conventional EDA tools.
The goal of Qiskit Metal is to allow for easy quantum hardware modeling with reduction of design-related errors plus increased speed.

(read the full `Medium blog <https://medium.com/qiskit/what-if-we-had-a-computer-aided-design-program-for-quantum-computers-4cb88bd1ddea>`_)

**Quantum Metal consists of four foundational elements:**

.. grid:: 2 2 2 4
   :gutter: 1

   .. grid-item-card:: Quantum Device Design
      :class-header: sd-bg-primary sd-text-light
      :link: qdesign
      :link-type: ref

      :ref:`qdesign`

   .. grid-item-card:: Quantum Device Components
      :class-header: sd-bg-secondary sd-text-light
      :link: qlibrary
      :link-type: ref

      :ref:`qlibrary`

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

.. toctree::
    :maxdepth: 2
    :hidden:

    About<self>
    Installing Qiskit Metal<installation>

.. toctree::
    :maxdepth: 2
    :caption: Overview
    :hidden:

    Metal Workflow<workflow>
    Contributor Guide<contributor-guide>
    Frequently Asked Questions<faq>


.. toctree::
    :maxdepth: 1
    :caption: Tutorials
    :hidden:

    Videos & Education<videoseducation>
    Tutorials<tut/index>
    Example Designs<circuit-examples/index>

.. toctree::
    :maxdepth: 1
    :caption: Libraries
    :hidden:

    All Quantum Devices<apidocs/qlibrary>

.. toctree::
    :maxdepth: 2
    :caption: API References
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
    :titlesonly:
    :hidden:

    Code of Conduct<https://github.com/Qiskit/qiskit/blob/master/CODE_OF_CONDUCT.md>

.. Hiding - Indices and tables
   :ref:`genindex`
   :ref:`modindex`
   :ref:`search`
