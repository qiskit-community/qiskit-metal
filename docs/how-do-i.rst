.. _how-do-i:

============
How do I...?
============

Short answers, organized by task. Each entry names the call or page that does
it and links to where it is explained.

Design
======

**...find a component?**
   Browse the :doc:`component catalog <qcomponents-gallery>`: one entry per
   component with its default options and pins. In the desktop GUI, the Library
   pane lists the same components. Programmatic list:
   :doc:`QComponents API <apidocs/qlibrary>`.

**...place a qubit?**
   Create it on a design, ``TransmonPocket(design, "Q1", options=dict(pos_x="1mm"))``.
   See :doc:`tut/2-From-components-to-chip/2.01-How-to-use-a-QComponent`, and the
   qubit entries in the :doc:`catalog <qcomponents-gallery>`.

**...route a CPW?**
   Use a route component such as ``RouteMeander`` or ``RoutePathfinder`` between two
   pins, ``pin_inputs=dict(start_pin=..., end_pin=...)``. Start with
   :doc:`tut/2-From-components-to-chip/2.11-Routing-101`; for a resonator of a
   given length, :doc:`tut/2-From-components-to-chip/2.12-Simple-Meander`.

**...connect to a pin or see what pins a component has?**
   Every catalog entry lists its pins; see :doc:`tut/quick-topics/Managing-pins`.

**...sweep a parameter or build many qubits?**
   :doc:`tut/1-Overview/1.5-Parametric-design---iterate-and-compare` and
   :doc:`tut/2-From-components-to-chip/2.22-Design-100-qubits-programmatically`.

**...write my own component?**
   :doc:`tut/2-From-components-to-chip/2.31-Create-a-QComponent-Basic`.

**...check the design rules?**
   ``from qiskit_metal.validation import validate; validate(design)``. See
   :doc:`tut/2-From-components-to-chip/2.24-Design-rule-checking`.

Export and view
===============

**...export GDS?**
   ``design.renderers.gds.export_to_gds("chip.gds")``. Options, including cheesing
   and the fabrication export, are in
   :doc:`tut/3-Renderers/3.2-Export-your-design-to-GDS`.

**...open the GDS in KLayout?**
   Load the layer-properties file and the starter rule deck shipped with the docs:
   :doc:`klayout`.

**...save and reload a design?**
   :doc:`tut/1-Overview/1.4-Saving-Your-Chip-Design`.

Simulate and analyze
====================

**...choose a solver?**
   :doc:`simulation-pathways` compares Ansys, gmsh + ElmerFEM, gmsh + scikit-fem
   and Palace by what each computes and what it needs installed.

**...compute a capacitance matrix?**
   Open source: :doc:`tut/4-Analysis/4.19-Analyze-a-transmon-using-ElmerFEM`
   (gmsh + ElmerFEM). Ansys: :doc:`tut/4-Analysis/4.01-Capacitance-and-LOM`.

**...compute eigenmodes and participation?**
   Open source, with lumped junctions:
   :doc:`tut/4-Analysis/4.43-Mesh-and-solve-the-10x10-processor`. Ansys:
   :doc:`tut/4-Analysis/4.02-Eigenmode-and-EPR`.

**...get a qubit Hamiltonian from a layout?**
   Capacitance matrix to Hamiltonian: :doc:`tut/4-Analysis/4.01-Capacitance-and-LOM`;
   the quantization methods are described in :doc:`quantization`.

**...use Ansys?**
   :doc:`tut/3-Renderers/3.3-Render-your-design-to-Ansys`, then
   :doc:`tut/simulate-ansys`.

Reproduce and learn
===================

**...reproduce a published chip?**
   :doc:`research` lists reproduced devices and results; the layouts of
   several small processors are in :doc:`circuit-examples/index`.

**...find a worked example of a component?**
   Cards in the :doc:`catalog <qcomponents-gallery>` link to a notebook where one
   exists; all component notebooks are on
   :doc:`circuit-examples/component-examples`.

**...pick a learning path?**
   :doc:`choose-your-path`.

Run and automate
================

**...run without the GUI?**
   ``import qiskit_metal as qm; qm.view(design)`` draws the chip headlessly.
   See :doc:`headless-usage`.

**...script it or drive it from an assistant?**
   :doc:`orchestration` covers the build, check, export loop, a live preview
   (``python -m qiskit_metal.watch``), reproducible GDS, and using a coding assistant.

**...install it?**
   :doc:`installation`, or :doc:`quickstart` for the shortest path.
