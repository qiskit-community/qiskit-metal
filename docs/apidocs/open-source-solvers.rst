.. _api-open-source-solvers:

====================
Open-source solvers
====================

The solvers that run without a commercial license. See :doc:`../simulation-pathways`
for what each computes and how to choose.

gmsh + scikit-fem
=================

.. automodule:: qiskit_metal.analyses.fem
   :members:
   :imported-members:

Analytic package-mode models
============================

.. automodule:: qiskit_metal.analyses.em.package_modes
   :no-members:

gmsh and ElmerFEM
=================

Meshing is :doc:`QGmshRenderer <qiskit_metal.renderers.QGmshRenderer>`.

.. autoclass:: qiskit_metal.renderers.renderer_elmer.elmer_renderer.QElmerRenderer
   :members:
