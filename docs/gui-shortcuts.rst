.. _gui-shortcuts:

*******************************
GUI Navigation & Shortcuts
*******************************

The desktop GUI (``MetalGUI``) can be driven entirely with the mouse, but
the keyboard shortcuts below are faster once a design has more than a
couple of components. They're also available in-app: press **?** or use
the Help button on the plot toolbar for the same reference without
leaving the GUI.

Mouse
=====

.. list-table::
   :widths: 20 80
   :header-rows: 0

   * - **Pan**
     - Drag with the left mouse button.
   * - **Zoom**
     - Scroll the mouse wheel. Zoom centers on the pointer.
   * - **Zoom to region**
     - Drag with the right mouse button to rubber-band a rectangle.
   * - **Select a component**
     - Click it.
   * - **Edit a component**
     - Double-click it, or click a component that's already selected.

Move the selected component
============================

Click a component to select it, then use the arrow keys.

.. image:: images/gui-shortcuts/move.svg
   :alt: Arrow keys move the selected component up, down, left, and right.
   :width: 340

.. image:: images/gui-shortcuts/move.gif
   :alt: Animation of a transmon qubit being selected and moved with the arrow keys, then a zoomed-in view of the finer Alt step.
   :width: 300

Hold **Shift** while nudging for a coarser step, or **Alt** for a finer
one — the same modifier convention most drawing tools use.

Rotate the selected component
===============================

.. image:: images/gui-shortcuts/rotate.svg
   :alt: Q and the left bracket key rotate counter-clockwise; E and the right bracket key rotate clockwise.
   :width: 380

.. image:: images/gui-shortcuts/rotate.gif
   :alt: Animation of a transmon qubit rotating a full 90-degree-step circle, then a 15-degree fine wiggle.
   :width: 300

**Q** / **E** rotate counter-clockwise / clockwise in 90° steps — the
same convention used for rotation in many games and creative tools.
**[** / **]** do the same thing, for anyone who prefers the bracket
keys. Hold **Shift** for a finer 15° step instead of 90°.

Rebuild keeps your selection
==============================

Moving, rotating, and rebuilding (**R**) can be chained without ever
re-clicking the component — rebuilding re-routes any connected CPWs to
follow it, and the selection survives the rebuild so the next arrow key
keeps moving the same component:

.. image:: images/gui-shortcuts/rebuild.gif
   :alt: Animation of a transmon qubit connected to another by a CPW, moved, rebuilt (the CPW re-routes), and moved again without re-selecting it.
   :width: 340

Other shortcuts
================

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - **A**
     - Fit the view to the design (components only).
   * - **Shift+A**
     - Fit the view to the whole chip, including the die outline.
   * - **R** (also **Ctrl+D**)
     - Rebuild the design.
   * - **?**
     - Open this reference in-app.

Editing a component's options replots without moving the camera, so your
current zoom and pan are preserved.
