.. _tut-simulate-ansys:

===================
Simulate with Ansys
===================

These notebooks need Ansys Electronics Desktop.

Two renderers drive Ansys: the legacy COM renderer and the pyaedt renderer.
The notebooks below cover the same three tasks on each.

.. list-table::
    :header-rows: 1

    * - Task
      - Legacy renderer
      - pyaedt renderer
    * - Q3D capacitance
      - 4.21
      - Q3D (MultiPlanar)
    * - Eigenmode and EPR
      - 4.22
      - Eigenmode (MultiPlanar)
    * - Driven S, Z, Y
      - 4.23
      - DrivenModal (MultiPlanar)

For impedance, 4.03 shows the recommended flow (analysis classes). 4.14 shows
the advanced flow, which drives the simulator through the renderer commands.

Analysis classes
----------------

.. nbgallery::

    4-Analysis/4.01-Capacitance-and-LOM
    4-Analysis/4.02-Eigenmode-and-EPR
    4-Analysis/4.03-Impedance

Tune a device directly
----------------------

.. nbgallery::

    4-Analysis/4.11-Analyze-and-tune-a-transmon
    4-Analysis/4.12-Analyze-a-resonator
    4-Analysis/4.13-Analyze-transmon-and-resonator
    4-Analysis/4.14-Analyze-a-double-hanger-resonator

Resonator S21
-------------

.. nbgallery::

    4-Analysis/4.16-Analyze-S21-of-Hange-Geometry-with-WirebondLunchpadDriven
    4-Analysis/4.17-Fit-S21-of-Hanger-Resonator-Geometry
    4-Analysis/4.18-Analyse-a-Resonator-with-Ports

Sweeps (legacy renderer)
------------------------

.. nbgallery::

    4-Analysis/4.21-Capacitance-matrix
    4-Analysis/4.22-Eigenmode-matrix
    4-Analysis/4.23-Impedance-and-scattering-Z-S-Y-matrices

pyaedt renderer
---------------

.. nbgallery::

    4-Analysis/pyaedt-multiplanar/Q3D-pyaedt-multiplanar
    4-Analysis/pyaedt-multiplanar/Eigenmode-pyaedt-multiplanar
    4-Analysis/pyaedt-multiplanar/DrivenModal-pyaedt-multiplanar
