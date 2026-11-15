.. _tut-render-and-export:

=========================
Part 3: Render and export
=========================

A renderer turns a design into another representation: a GDS file for the foundry, a mesh for a field
solver, or an Ansys project. Parts 3 and 4 go together. Here you learn what each renderer produces and how
to drive it. In :doc:`Part 4 <simulate-and-analyze>` the same renderers feed the solvers, and that is
where most of the analysis tutorials are.

.. grid:: 1 1 3 3
    :gutter: 2

    .. grid-item::

        .. button-ref:: p3-gds
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            GDS and the basics

    .. grid-item::

        .. button-ref:: p3-open
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Meshing (open source)

    .. grid-item::

        .. button-ref:: p3-ansys
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Ansys and your own renderer

Which renderer for what
=======================

.. list-table::
    :header-rows: 1
    :widths: 20 30 25 25

    * - Goal
      - Renderer
      - Tutorial here
      - Then, in Part 4
    * - Draw, check and export a layout
      - ``QGDSRenderer`` (GDS); ``QMplRenderer`` (matplotlib, headless)
      - 3.1, 3.2
      - none needed
    * - Capacitance and modes without an Ansys license
      - ``QGmshRenderer`` (mesh), then ElmerFEM or the scikit-fem solver
      - 3.5
      - 4.19; 4.43 to 4.46 (:doc:`open-source path <simulate-and-analyze>`)
    * - Eigenmodes, EPR, S-parameters in Ansys
      - legacy COM renderer (``hfss``, ``q3d``) or pyaedt renderer (``aedt_hfss``, ``aedt_q3d``)
      - 3.3
      - 4.01 to 4.03, 4.11 to 4.18, 4.21 to 4.23
    * - Something else (your solver, your file format)
      - subclass ``QRenderer``
      - 3.4
      - none needed

The solver paths are compared on :doc:`../simulation-pathways`.

.. _p3-gds:

GDS and the basics
------------------

Start with 3.1, then export to GDS. Design-rule checks are covered in 2.24, before export.

.. nbgallery::

    3-Renderers/3.1-Introduction-to-QRenderers
    3-Renderers/3.2-Export-your-design-to-GDS

.. _p3-open:

Meshing (open source)
---------------------

Export the design to a gmsh mesh. The mesh goes to ElmerFEM or to the scikit-fem solver; no Ansys license is needed.

.. nbgallery::

    3-Renderers/3.5-Render-your-design-to-Gmsh

Continue with the solvers: :ref:`p4-open-source`.

.. _p3-ansys:

Ansys and your own renderer
---------------------------

3.3 sends a design to Ansys HFSS or Q3D (Ansys Electronics Desktop needed). 3.4 shows how to write a renderer for another tool.

.. nbgallery::

    3-Renderers/3.3-Render-your-design-to-Ansys
    3-Renderers/3.4-How-do-I-make-my-custom-QRenderer

Continue with the solvers: :ref:`p4-ansys`.
