.. _how-do-i:

============
How do I...?
============

Short answers, organized by task. Each card names the call or page that does
it and links to where it is explained.

.. grid:: 1 2 4 4
    :gutter: 2

    .. grid-item::

        .. button-ref:: hdi-design
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Design

    .. grid-item::

        .. button-ref:: hdi-export
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Export and view

    .. grid-item::

        .. button-ref:: hdi-simulate
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Simulate

    .. grid-item::

        .. button-ref:: hdi-run
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Run and automate

.. _hdi-design:

Design
======

.. grid:: 1 2 3 3
    :gutter: 3
    :class-container: qm-cards-img

    .. grid-item-card:: Find a component
        :img-top: images/qlibrary/TransmonCross.png
        :class-card: sd-shadow-sm

        Browse the catalog: one entry per component with its default options
        and pins. The desktop GUI Library pane lists the same components.

        +++
        :doc:`Component catalog <qcomponents-gallery>` ·
        :doc:`API <apidocs/qlibrary>`

    .. grid-item-card:: Place a qubit
        :img-top: images/qlibrary/TransmonPocket.png
        :class-card: sd-shadow-sm

        Create it on a design:
        ``TransmonPocket(design, "Q1", options=dict(pos_x="1mm"))``.

        +++
        :doc:`2.01 Using a QComponent <tut/2-From-components-to-chip/2.01-How-to-use-a-QComponent>` ·
        :doc:`1.3 Four-qubit chip <tut/1-Overview/1.3-Build-a-4-qubit-chip>`

    .. grid-item-card:: Route a CPW
        :img-top: images/qlibrary/RouteMeander.png
        :class-card: sd-shadow-sm

        Use a route such as ``RouteMeander`` or ``RoutePathfinder`` between two
        pins: ``pin_inputs=dict(start_pin=..., end_pin=...)``.

        +++
        :doc:`2.11 Routing 101 <tut/2-From-components-to-chip/2.11-Routing-101>` ·
        :doc:`2.12 Meander <tut/2-From-components-to-chip/2.12-Simple-Meander>`

    .. grid-item-card:: Connect to a pin
        :img-top: images/qlibrary/LaunchpadWirebond.png
        :class-card: sd-shadow-sm

        Every catalog entry lists its pins. Pins carry position, direction and
        width, and routes attach to them.

        +++
        :doc:`Managing pins <tut/quick-topics/Managing-pins>`

    .. grid-item-card:: Sweep or repeat
        :img-top: images/qlibrary/Cap3Interdigital.png
        :class-card: sd-shadow-sm

        Change options in a loop to compare variants, or build many qubits from
        code.

        +++
        :doc:`1.5 Parametric design <tut/1-Overview/1.5-Parametric-design---iterate-and-compare>` ·
        :doc:`2.22 100 qubits <tut/2-From-components-to-chip/2.22-Design-100-qubits-programmatically>`

    .. grid-item-card:: Check the design rules
        :img-top: images/qlibrary/RouteStraight.png
        :class-card: sd-shadow-sm

        ``from qiskit_metal.validation import validate; validate(design)`` reports
        spacing, overlap and connection errors.

        +++
        :doc:`2.24 Design-rule checking <tut/2-From-components-to-chip/2.24-Design-rule-checking>`

    .. grid-item-card:: Write my own component
        :img-top: images/qlibrary/NGon.png
        :class-card: sd-shadow-sm

        Subclass ``QComponent``, give it default options and a ``make()``.

        +++
        :doc:`2.31 Basic <tut/2-From-components-to-chip/2.31-Create-a-QComponent-Basic>` ·
        :doc:`2.33 Reusable file <tut/2-From-components-to-chip/2.33-Add-my-QComponent-to-a-reusable-python-file>`

.. _hdi-export:

Export and view
===============

.. grid:: 1 2 3 3
    :gutter: 3
    :class-container: qm-cards-img

    .. grid-item-card:: Export GDS
        :img-top: _static/workflow/gds-layers.png
        :class-card: sd-shadow-sm

        ``design.renderers.gds.export_to_gds("chip.gds")``. Cheesing and the
        fabrication export are in the tutorial.

        +++
        :doc:`3.2 Export to GDS <tut/3-Renderers/3.2-Export-your-design-to-GDS>`

    .. grid-item-card:: Open the GDS in KLayout
        :img-top: _static/workflow/gds-layers.png
        :class-card: sd-shadow-sm

        Load the layer-properties file and the starter rule deck that ship with
        the docs.

        +++
        :doc:`GDS in KLayout <klayout>`

    .. grid-item-card:: Save and reload a design
        :img-top: _static/workflow/design-gui.png
        :class-card: sd-shadow-sm

        Keep a design as a file and load it back in another session.

        +++
        :doc:`1.4 Saving your design <tut/1-Overview/1.4-Saving-Your-Chip-Design>`

.. _hdi-simulate:

Simulate
========

.. grid:: 1 2 3 3
    :gutter: 3
    :class-container: qm-cards-img

    .. grid-item-card:: Choose a solver
        :img-top: _static/home/methods.webp
        :class-card: sd-shadow-sm

        Ansys, gmsh + ElmerFEM, gmsh + scikit-fem and Palace compared by what
        each computes and what it needs installed.

        +++
        :doc:`Simulation pathways <simulation-pathways>`

    .. grid-item-card:: Capacitance matrix
        :img-top: _static/diagrams/lumped-circuit.svg
        :class-card: sd-shadow-sm

        Open source with gmsh + ElmerFEM, or Ansys Q3D with the lumped
        oscillator model.

        +++
        :doc:`4.19 ElmerFEM <tut/4-Analysis/4.19-Analyze-a-transmon-using-ElmerFEM>` ·
        :doc:`4.01 Ansys <tut/4-Analysis/4.01-Capacitance-and-LOM>`

    .. grid-item-card:: Eigenmodes and participation
        :img-top: _static/workflow/eigenmode-field.png
        :class-card: sd-shadow-sm

        Open source with lumped junctions, or Ansys HFSS with
        energy-participation analysis.

        +++
        :doc:`4.43 scikit-fem <tut/4-Analysis/4.43-Mesh-and-solve-the-10x10-processor>` ·
        :doc:`4.02 Ansys <tut/4-Analysis/4.02-Eigenmode-and-EPR>`

    .. grid-item-card:: Get a Hamiltonian
        :img-top: _static/diagrams/epr-participation.svg
        :class-card: sd-shadow-sm

        Go from a capacitance matrix or mode participations to qubit
        parameters.

        +++
        :doc:`4.01 LOM <tut/4-Analysis/4.01-Capacitance-and-LOM>` ·
        :doc:`Quantization methods <quantization>`

    .. grid-item-card:: Use Ansys
        :img-top: _static/workflow/design-gui.png
        :class-card: sd-shadow-sm

        Render the design to HFSS or Q3D, then analyze.

        +++
        :doc:`3.3 Render to Ansys <tut/3-Renderers/3.3-Render-your-design-to-Ansys>` ·
        :doc:`Part 4 with Ansys <tut/simulate-ansys>`

    .. grid-item-card:: Reproduce a published chip
        :img-top: _static/home/gui-chip.webp
        :class-card: sd-shadow-sm

        Reproduced devices and results, and layouts of small processors.

        +++
        :doc:`Reproduced devices <research>` ·
        :doc:`Circuit examples <circuit-examples/index>`

.. _hdi-run:

Run and automate
================

.. grid:: 1 2 3 3
    :gutter: 3
    :class-container: qm-cards-img

    .. grid-item-card:: Run without the GUI
        :img-top: images/headless-view.png
        :class-card: sd-shadow-sm

        ``import qiskit_metal as qm; qm.view(design)`` draws the chip headlessly.

        +++
        :doc:`Desktop GUI or headless <headless-usage>`

    .. grid-item-card:: Script it or drive it from an assistant
        :img-top: _static/diagrams/workflow-loop.svg
        :class-card: sd-shadow-sm

        The build, check, export loop; a live preview with
        ``python -m qiskit_metal.watch``; reproducible GDS; using a coding
        assistant.

        +++
        :doc:`Scripting and agent use <orchestration>`

    .. grid-item-card:: Install it
        :img-top: images/logo.png
        :class-card: sd-shadow-sm

        ``pip install quantum-metal``, with extras for the GUI and solvers.

        +++
        :doc:`Installation <installation>` ·
        :doc:`Quick start <quickstart>` ·
        :doc:`Choose your path <choose-your-path>`
