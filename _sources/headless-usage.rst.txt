.. _headless-usage:

==========================================
Using Quantum Metal without the Qt GUI
==========================================

You do not need the desktop Qt GUI (``MetalGUI``) to use Quantum
Metal. The full API — designs, components, renderers, analyses — works
headlessly in a plain Python interpreter, a Jupyter notebook, or a
cloud notebook environment (Colab, Binder, JupyterLab on a shared
server). The Qt GUI is one *interface* to the API, not a requirement.

.. rubric:: Run the tutorials in your browser

.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/qiskit-community/qiskit-metal/blob/main/tutorials/1%20Overview/1.1%20Quick%20start.ipynb
   :alt: Open Quick Start in Colab

.. image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/qiskit-community/qiskit-metal/main?labpath=tutorials%2F1%20Overview%2F1.1%20Quick%20start.ipynb
   :alt: Open Quick Start in Binder

In Colab / Binder the first cell installs the lite wheel
(``pip install -q quantum-metal``). The tutorial then calls
``gui = qm.gui(design)`` — a factory that returns the desktop
``MetalGUI`` when a display is available and a Qt-free
``MetalGUIHeadless`` (inline matplotlib renderer with the same
``gui.rebuild()`` / ``gui.screenshot()`` / ``gui.edit_component(...)``
surface) when it isn't. The same notebook runs in both environments
unchanged.

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

Installing without Qt
=====================

As of **v0.7.0**, ``pip install quantum-metal`` no longer pulls in
PySide6 or the Qt stack. The base install is headless by default —
no GUI, no Qt surprises.

If you have the ``[gui]`` extra installed and want to suppress Qt
initialisation at runtime (e.g. in a script that runs headlessly),
set the ``QISKIT_METAL_HEADLESS`` environment variable:

.. code-block:: bash

    export QISKIT_METAL_HEADLESS=1
    python my_script.py

This prevents matplotlib from switching to the ``QtAgg`` backend
during import. The Qt packages stay installed but are never touched.

Install extras
==============

* ``pip install quantum-metal`` — lite default: no Qt, no Ansys, no gmsh
* ``pip install "quantum-metal[gui]"`` — + PySide6 + qdarkstyle
* ``pip install "quantum-metal[ansys]"`` — + pyaedt + pyEPR-quantum
* ``pip install "quantum-metal[mesh]"`` — + gmsh (foundation for Elmer / Palace).
  ``[fem]`` is a backward-compatible alias.
* ``pip install "quantum-metal[full]"`` — all extras (v0.6.x behavior)

See :doc:`installation` for the full feature matrix and
:doc:`migration-to-v0.7.0` for per-persona migration recipes.

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
