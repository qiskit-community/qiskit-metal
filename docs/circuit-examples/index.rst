.. _circuit-examples:

========
Examples
========

Designs to copy. Notebooks that teach a feature are under :doc:`../tut/index`.
Every component class has a thumbnail in the :doc:`component gallery <../qcomponents-gallery>`.

.. grid:: 1 1 3 3
    :gutter: 2

    .. grid-item::

        .. button-ref:: ex-reference-designs
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Reference designs

    .. grid-item::

        .. button-ref:: ex-component-examples
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Component examples

    .. grid-item::

        .. button-ref:: ex-design-flow
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Full design-flow examples

.. _ex-reference-designs:

Reference designs
=================

Complete designs to copy and adapt, from a single unit cell to a four-qubit chip. The 100-qubit mockup is tutorial :doc:`2.22 <../tut/2-From-components-to-chip/2.22-Design-100-qubits-programmatically>`.

.. rubric:: Unit cells

Reference layouts from stock Quantum Metal components. A.1-A.3 are adapted with attribution from the open-source `SQDMetal <https://github.com/sqdlab/SQDMetal>`_ benchmark devices (`arXiv:2511.01220 <https://arxiv.org/abs/2511.01220>`_).

.. nbgallery::

    ../tut/full-design-examples/A.1-Transmon-with-readout-resonator
    C.Composite-bi-partite/21-OneTransmonsWithMeanderAndOTG
    E.Input-output-coupling/42-ResonatorAndLaunchPad

.. rubric:: Two qubits

.. nbgallery::

    D.Qubit-couplers/32-TwoTransmonsDirectCoupling
    D.Qubit-couplers/33-TwoTransmonsWithMeander
    D.Qubit-couplers/31-TwoCrossmonsTunableCoupler
    ../tut/full-design-examples/A.2-Two-coupled-transmons

.. rubric:: Four qubits

.. nbgallery::

    ../tut/full-design-examples/A.3-Four-qubit-multiplexed-readout

.. _ex-published-devices:

Published devices
=================

Reproductions of published chips are on the :doc:`Reproduced devices <../research>` page, with sources and requirements. Fabricated devices, papers and projects are on :doc:`Devices and papers <../built-with-metal>`.

.. nblinkgallery::

    F.Small-quantum-chips/52-Barends_5Qubit_Xmon_Processor
    F.Small-quantum-chips/Full-Physical-Design-of-iSWAP-Gates
    F.Small-quantum-chips/53-Wallraff_17Qubit_SurfaceCode
    F.Small-quantum-chips/54-Wallraff_TwoQubit_Cell_Mesh

.. _ex-component-examples:

Component examples
==================

One notebook per component: build it, change its options, view it. The :doc:`component gallery <../qcomponents-gallery>` lists every component class.

.. rubric:: Transmon qubits

.. nbgallery::

    A.Qubits/01-Transmon_cross
    A.Qubits/05-Transmon_cross_fl
    A.Qubits/02-Transmon_floating
    A.Qubits/06-Transmon_floating_6
    A.Qubits/10-Transmon_floating_teeth
    A.Qubits/03-concentric_transmon
    A.Qubits/04-Interdigitated_Transmon
    ../tut/quick-topics/QComponent-Interdigitated-transmon
    A.Qubits/11-Star_shaped_qubit
    E.Input-output-coupling/43-TransmonPocketCL

.. rubric:: Josephson junctions

.. nbgallery::

    A.Qubits/08-JJ-Dolan
    A.Qubits/09-JJ-Manhattan
    ../tut/quick-topics/JJ-Demo-Notebook

.. rubric:: Resonators and input/output coupling

.. nbgallery::

    B.Resonators/11-Resonator_Meander
    E.Input-output-coupling/41-LaunchPad
    ../tut/quick-topics/QComponent-3-fingers-capacitor

.. _ex-design-flow:

Full design-flow examples
=========================

Complete designs taken through simulation and analysis.

.. nbgallery::

    full-design-flow-examples/A.4-Full-chip-design
    full-design-flow-examples/A.7-IMS-2022-workshop

.. toctree::
    :maxdepth: 1
    :hidden:

    Component Gallery<../qcomponents-gallery>
