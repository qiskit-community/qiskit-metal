.. _headless-usage:

==========================================
Using Quantum Metal without the Qt GUI
==========================================

You do not need the desktop Qt GUI (``MetalGUI``) to use Quantum
Metal. The full API — designs, components, renderers, analyses — works
headlessly in a plain Python interpreter, a Jupyter notebook, or a
cloud notebook environment (Colab, Binder, JupyterLab on a shared
server). The Qt GUI is one *interface* to the API, not a requirement.

Quick start
===========

The shortest path to rendering a design without Qt:

.. code-block:: python

    import qiskit_metal as qm
    from qiskit_metal.designs import DesignPlanar
    from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket

    design = DesignPlanar()
    TransmonPocket(design, "Q1",
                   options={"connection_pads": {"a": {}}})

    fig = qm.view(design)
    fig.savefig("q1.png")          # save to file
    # or, in a Jupyter notebook, just `fig` displays inline.

``qm.view`` accepts options for customising the output:

.. code-block:: python

    # Render into an existing axes for a multi-panel figure
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    qm.view(design_a, ax=axes[0], title="Design A")
    qm.view(design_b, ax=axes[1], title="Design B")

    # Render only specific components
    qm.view(design, components=["Q1", "Q2"])

    # Hide specific layers
    qm.view(design, hidden_layers={2})

    # Custom figure size
    qm.view(design, figsize=(10, 8))

The returned :class:`matplotlib.figure.Figure` can be saved
(``fig.savefig``), embedded in a larger figure, or further customised
with the standard matplotlib API.

What works headlessly
=====================

Everything except the desktop interactive editor:

* All component classes in :mod:`qiskit_metal.qlibrary`
* Designs (:class:`~qiskit_metal.designs.DesignPlanar`,
  :class:`~qiskit_metal.designs.DesignFlipChip`, ...)
* Geometry rendering via :func:`qm.view <qiskit_metal.viewer.view>`
* GDS export via :class:`~qiskit_metal.renderers.renderer_gds.gds_renderer.QGDSRenderer`
* Q3D / HFSS rendering (when run on a machine with Ansys AEDT
  available — the *renderer* doesn't require Qt, but Ansys does)
* All :mod:`qiskit_metal.analyses` modules

What requires the Qt GUI
========================

Only the interactive desktop editor itself:

* :class:`~qiskit_metal.MetalGUI` — the dockable PySide6 window
* The pan/zoom toolbar from
  :func:`~qiskit_metal.renderers.renderer_mpl.mpl_interaction.figure_pz`
  (use :func:`qm.view` instead in notebooks for static images, or
  ``%matplotlib widget`` + ``ipympl`` for interactive pan/zoom in
  Jupyter)

Installing without Qt (v0.6.x)
==============================

Today the base ``pip install quantum-metal`` install pulls in PySide6
and the rest of the Qt stack so the desktop GUI works out of the box.
You can still skip Qt initialisation at runtime by setting
the ``QISKIT_METAL_HEADLESS`` environment variable:

.. code-block:: bash

    export QISKIT_METAL_HEADLESS=1
    python my_script.py

This prevents matplotlib from switching to the ``QtAgg`` backend
during import. The Qt packages stay installed but are never touched.

Migrating to a lite install (v0.7.0)
====================================

A future v0.7.0 release will flip the default install:

* ``pip install quantum-metal`` -> no Qt, no Ansys, no gmsh
* ``pip install quantum-metal[gui]`` -> + PySide6 + qdarkstyle
* ``pip install quantum-metal[ansys]`` -> + pyaedt + pyEPR
* ``pip install quantum-metal[fem]`` -> + gmsh
* ``pip install quantum-metal[full]`` -> all extras (current behavior)

These extras already exist in ``pyproject.toml`` from v0.6.x onwards;
they're additive today, becoming the canonical opt-in pathway when
v0.7.0 ships.

Roadmap: a richer in-notebook viewer
====================================

``qm.view`` covers the **viewing** workflow: render a design to an
inline image. A richer interactive viewer — pan, zoom, click-to-select
components, edit option values inline — is planned as a future
project. The likely direction is Jupyter widgets + Plotly or
``ipympl``, both of which give us a no-Qt interactive surface that
works in Colab, Binder, and JupyterLab without setup gymnastics.

This will be tracked as its own initiative once the basic headless
rendering path (this page) is stable. In the meantime, ``qm.view`` is
the supported way to display designs in notebooks.

See also
========

* :func:`qiskit_metal.view` — the headless viewer entry point
* :class:`qiskit_metal.MetalGUI` — the desktop Qt GUI (when you want
  it)
