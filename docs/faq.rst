.. _faq:

***************************
Frequently asked questions
***************************

Short answers, with a link to the page that explains each. For task-oriented
answers see :doc:`how-do-i`.

.. _faq_setup:

-------
Install
-------

**Which Python versions are supported?**
Python 3.11 through 3.14. Install with ``pip install quantum-metal``; the
import name is still ``qiskit_metal``. See :doc:`installation`.

**Why do I get an error about PySide6, pyEPR or gmsh?**
The default install is lite and leaves those out. Add the extra you need:
``"quantum-metal[gui]"`` for the desktop GUI, ``[ansys]`` for Ansys and pyEPR,
``[mesh]`` for gmsh and Elmer, ``[skfem]`` for the scikit-fem solver, or
``[full]`` for the GUI, Ansys and gmsh together. :doc:`installation` lists
every extra.

**Jupyter says** ``No module named 'qiskit_metal'`` **. What is wrong?**
The notebook is running a kernel from a different environment. Register the
kernel from inside the environment where you installed the package, with
``python -m ipykernel install --user --name <name>``, then pick it under
*Kernel* > *Change Kernel*. See the Jupyter Lab section of :doc:`installation`.

------------------
GUI and headless
------------------

**Do I need the desktop GUI?**
No. ``qm.view(design)`` draws a design with matplotlib, and ``qm.gui(design)``
returns the desktop window when PySide6 and a display are available and an
inline viewer otherwise. See :doc:`headless-usage`.

**My script opens the GUI and exits at once, but the same code works in
Jupyter. Why?**
Nothing runs the Qt event loop. End the script with
``if __name__ == "__main__" and gui.qApp is not None: gui.qApp.exec()``.
Scripts from ``design.to_python_script()`` already include this guard.

**The GUI crashed my kernel, or I see "Could not load the Qt platform
plugin". What now?**
Launch it again: ``MetalGUI`` keeps a startup journal and, after a failed
launch, discards saved window state and starts with the default layout. To
trace startup, set ``QISKIT_METAL_DEBUG_INIT=1``; to clear saved state, set
``QISKIT_METAL_RESET_UI_SETTINGS=1``. If the GUI stays unusable, use
``qm.view(design)`` or set ``QISKIT_METAL_HEADLESS=1``. Background: issue
`#1048 <https://github.com/qiskit-community/qiskit-metal/issues/1048>`_ and
:doc:`headless-usage`.

**Is the window layout restored on startup?**
Not by default. Set ``QISKIT_METAL_RESTORE_LAYOUT=1`` to opt in. On Windows
the GUI uses software OpenGL unless ``QISKIT_METAL_QT_HARDWARE_GL=1`` is set.

------
Design
------

**Where do I find a component and its options and pins?**
In the :doc:`component catalog <qcomponents-gallery>`, one entry per
component, or in the GUI Library pane. See :doc:`how-do-i`.

**How do I check a design before export?**
``from qiskit_metal.validation import validate; validate(design)`` runs the
design rules and returns the findings. See
:doc:`2.24 Design-rule checking <tut/2-From-components-to-chip/2.24-Design-rule-checking>`
and :doc:`orchestration`.

**How do I save a design and load it later?**
See :doc:`1.4 Saving your chip design <tut/1-Overview/1.4-Saving-Your-Chip-Design>`.

---------------------
GDS and fabrication
---------------------

**How do I export GDS?**
``design.renderers.gds.export_to_gds("chip.gds")``. Cheesing and the
fabrication export are in
:doc:`3.2 Export your design to GDS <tut/3-Renderers/3.2-Export-your-design-to-GDS>`.

**Why are junctions missing from my GDS?**
They appear only if ``path_filename`` points to a GDS file that holds the
junction cells. See :doc:`klayout` and tutorial 1.4.

**How do I view the GDS and check basic rules?**
Open it in KLayout with the layer-properties file and the starter rule deck;
the deck's default thresholds are placeholders, so use your fab's numbers.
See :doc:`klayout`.

----------
Simulation
----------

**Which solver should I use?**
It depends on what you compute and what you can install. See
:doc:`simulation-pathways`.

**Do I need Ansys?**
No for capacitance matrices (gmsh + ElmerFEM) or for eigenmodes and couplings
of small cells (gmsh + scikit-fem, ``pip`` only). The HFSS and Q3D paths need
Ansys Electronics Desktop and ``"quantum-metal[ansys]"``. See
:doc:`simulation-pathways`.

---------------
Troubleshooting
---------------

**Where is the documentation, and can I build it locally?**
It is at https://qiskit-community.github.io/qiskit-metal/. ``qm.open_docs()``
opens it in a browser (in a headless or CI session it prints the link
instead). To build it, run ``tox -e docs``; the HTML goes to
``docs/_build/html``, and notebooks are not executed unless
``QISKIT_DOCS_BUILD_TUTORIALS`` is set. See :doc:`contributor-guide`.

**How do I download a tutorial?**
The notebooks are in ``docs/tut/`` and ``docs/circuit-examples/`` on GitHub;
clone the repository to get them all. You can also run the Quick start in
Colab or Binder from :doc:`quickstart`.

---------
Community
---------

**Where do I ask a question or report a bug?**
Open a `GitHub issue <https://github.com/qiskit-community/qiskit-metal/issues>`_,
or use the Discord link on the :doc:`home page <index>`. To contribute, see
:doc:`contributor-guide`.

.. TODO-verify: Discord invite (https://discord.gg/FPNybyfpxd) is copied from
   docs/index.rst; not checked live.
