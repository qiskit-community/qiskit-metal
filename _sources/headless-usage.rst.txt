.. _headless-usage:

==========================================
Desktop GUI or headless
==========================================

Quantum Metal has two ways to look at a design. Both use the same Python
API (designs, components, renderers, analyses); they differ only in where
the picture appears.

* **The desktop GUI** (``MetalGUI``) is a Qt window with a component
  library, an options editor, a log and a live plot. Pick this when you
  work at a laptop or workstation and want to click on, edit and rebuild
  components interactively. It needs the optional ``[gui]`` install (PySide6).
* **Headless** means no Qt window. ``qm.view(design)`` returns a matplotlib
  figure, and ``qm.gui(design)`` returns an inline viewer with the same
  ``rebuild()``, ``screenshot()`` and ``edit_component(...)`` methods. It
  runs in a plain script, a Jupyter notebook, a CI job, Colab or Binder,
  and it is what ``pip install quantum-metal`` gives you by default.

.. grid:: 1 1 2 2
   :gutter: 3
   :class-container: qm-pair

   .. grid-item::

      .. figure:: _static/workflow/design-gui.png
         :alt: The Quantum Metal desktop GUI: component library and options editor on the left, a plot of one transmon qubit in the center, a log at the bottom.
         :width: 100%

         Desktop GUI: ``gui = qm.gui(design)`` opens this window.

   .. grid-item::

      .. figure:: images/headless-view.png
         :alt: A matplotlib plot of the same transmon qubit, two blue pads inside a gray pocket, with plain axes and no toolbar or panels.
         :width: 100%

         Headless: ``qm.view(design)`` draws the same layout inline.

What you give up without the GUI is the point-and-click editing: the
dockable panels and the interactive pan/zoom toolbar. Everything else is
identical. Designs, GDS export, renderers and analyses do not depend on Qt.

How ``qm.gui(design)`` chooses
==============================

``qm.gui(design)`` returns the desktop ``MetalGUI`` when Qt and a display
are available, and the inline ``MetalGUIHeadless`` otherwise: no PySide6
installed, a Linux session without ``DISPLAY``, Colab, Binder, or
``QISKIT_METAL_HEADLESS=1``. ``qm.gui(design, force_headless=True)`` forces
the inline viewer for one call. A tutorial written with ``qm.gui(design)``
therefore runs unchanged on a laptop and in the cloud.

.. rubric:: Run the tutorials in your browser

.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :target: https://colab.research.google.com/github/qiskit-community/qiskit-metal/blob/main/docs/tut/1-Overview/1.1-Quick-start.ipynb
   :alt: Open Quick Start in Colab

.. image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/qiskit-community/qiskit-metal/main?labpath=docs%2Ftut%2F1-Overview%2F1.1-Quick-start.ipynb
   :alt: Open Quick Start in Binder

In Colab and Binder the first cell installs the lite wheel
(``pip install -q quantum-metal``), and the tutorial's ``qm.gui(design)``
call picks the inline viewer.

Render without Qt
=================

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

``qm.view`` accepts options for customizing the output:

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
(``fig.savefig``), embedded in a larger figure, or further customized
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
initialization at runtime (e.g. in a script that runs headlessly),
set the ``QISKIT_METAL_HEADLESS`` environment variable:

.. code-block:: bash

    export QISKIT_METAL_HEADLESS=1
    python my_script.py

This prevents matplotlib from switching to the ``QtAgg`` backend
during import. The Qt packages stay installed but are never touched.
``qm.gui(design)`` then returns the inline viewer; ``qm.gui(design,
force_headless=True)`` does the same for one call, and
``QISKIT_METAL_HEADLESS_QUIET=1`` hides the one-time notice it prints.

Install extras
==============

* ``pip install quantum-metal`` — lite default: no Qt, no Ansys, no gmsh
* ``pip install "quantum-metal[gui]"`` — + PySide6 + qdarkstyle
* ``pip install "quantum-metal[ansys]"`` — + pyaedt + pyEPR-quantum
* ``pip install "quantum-metal[mesh]"`` — + gmsh (foundation for Elmer / Palace).
* ``pip install "quantum-metal[skfem]"`` — ``[mesh]`` + the scikit-fem eigenmode solver (tutorials 4.41–4.46).
  ``[fem]`` is a backward-compatible alias.
* ``pip install "quantum-metal[full]"`` — all extras

See :doc:`installation` for the full feature matrix.

See also
========

* :func:`qiskit_metal.view` — the headless viewer entry point
* :class:`qiskit_metal.MetalGUI` — the desktop Qt GUI (when you want
  it)
