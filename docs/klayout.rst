.. _gds-klayout:

===================================
Viewing and checking GDS in KLayout
===================================

`KLayout <https://www.klayout.de>`_ is the free, open-source layout viewer most
groups use to inspect a mask before sending it out. Two small files help it
read a GDS exported by Quantum Metal:

* :download:`quantum-metal.lyp <_static/klayout/quantum-metal.lyp>`, a layer-properties
  file that names and colors each layer and datatype.
* :download:`quantum-metal-basic.drc <_static/klayout/quantum-metal-basic.drc>`, a starter
  design-rule deck that flags thin features, narrow gaps and tiny islands.

Both were tried on a chip exported by ``QGDSRenderer``; see the notes at the end for
what they do not cover.

Export the chip
===============

Export a design with ``design.renderers.gds.export_to_gds("my_chip.gds")``. The
tutorials :doc:`1.4 Saving your chip design <tut/1-Overview/1.4-Saving-Your-Chip-Design>`
and :doc:`3.2 Export your design to GDS <tut/3-Renderers/3.2-Export-your-design-to-GDS>`
walk through the options, including cheesing and the fabrication export.

Color the layers
================

Open the GDS in KLayout (``klayout my_chip.gds``), then choose
*File* → *Load Layer Properties* and select ``quantum-metal.lyp``. The file lists
design layers 1 to 4. For a design with more layers, copy one block in the file
and change its layer number.

Quantum Metal writes each design layer as a GDS layer, and uses the datatype to say
what a shape is:

.. list-table::
    :header-rows: 1
    :widths: 12 88

    * - Datatype
      - Contents
    * - 10
      - Polygons: qubit pads, launchpads, and the ground-plane outline.
    * - 11
      - Paths: CPW traces.
    * - 0
      - The ground plane with its cut-outs, in the negative-mask export.
    * - 100
      - Cheese holes (``options.cheese.datatype``).
    * - 99
      - The no-cheese keep-out region, for viewing only
        (``options.no_cheese.datatype``). It is absent from a fabrication export.
    * - 101, 102
      - Working geometry for the cheese step. The layer file hides them.

The cheese and no-cheese datatypes are options, so if you changed them, change the
numbers in the layer file to match.

Run the design-rule deck
========================

From the command line:

.. code-block:: bash

    klayout -b -r quantum-metal-basic.drc -rd input=my_chip.gds -rd report=drc_report.lyrdb

Then open the GDS in KLayout and load the report with *Tools* → *Marker Browser*.
The deck reads the metal on one design layer (polygons and paths, minus the cheese
holes) and reports:

* ``min_width``: metal narrower than the minimum width;
* ``min_space``: a gap between metal shapes narrower than the minimum spacing;
* ``min_area``: a metal island smaller than the minimum area.

Set the thresholds on the command line, for example
``-rd min_width=2 -rd min_space=3 -rd min_area=10`` (micrometers and square
micrometers), and the design layer with ``-rd layer=2``. **The defaults are
placeholders.** Take the numbers from your fab's design rules before relying on the
result.

Notes
=====

* The deck is a starting point. It does not know about your process: no layer
  stack, no junction rules, no antenna or airbridge rules.
* Quantum Metal has its own checks that run before export:
  ``from qiskit_metal.validation import validate; print(validate(design).report())``
  catches problems such as unterminated CPW ends and starved fillets at the design
  stage. GDS-level checks are the job of KLayout and your fab's rule deck.
* Junctions appear in the GDS only if you set ``path_filename`` to a GDS file that
  holds the junction cells (see tutorial 1.4).
