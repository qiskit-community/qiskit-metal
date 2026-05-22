.. _migration-to-v0.7.0:

Migrating to v0.7.0 (lite-by-default install)
==============================================

.. attention::

    **v0.7.0 is not yet released.** This document describes the
    migration path so you can prepare. Until v0.7.0 lands,
    ``pip install quantum-metal`` keeps the v0.6.x behaviour of
    pulling every dependency. See the changelog and
    `ROADMAP <https://github.com/qiskit-community/qiskit-metal/blob/main/ROADMAP.md>`_
    for status.

.. contents::
   :local:
   :depth: 2

TL;DR
-----

In v0.7.0, ``pip install quantum-metal`` no longer pulls
PySide6, qdarkstyle, pyaedt, pyEPR-quantum, or gmsh. Those
move into opt-in extras.

The fastest migration is one of:

.. code-block:: bash

    # Want everything? Restore the v0.6.x experience:
    pip install "quantum-metal[full]"

    # Just MetalGUI?
    pip install "quantum-metal[gui]"

    # Just HFSS / Q3D / EPR (no GUI)?
    pip install "quantum-metal[ansys]"

    # Just gmsh meshing?
    pip install "quantum-metal[fem]"

    # Headless designs, GDS export, qm.view, no heavy deps?
    pip install quantum-metal      # base install — much smaller


Who is affected
---------------

You **need to do something** if any of these describe your
v0.6.x install:

- You run ``MetalGUI`` (the desktop Qt GUI)
- You import or use the HFSS / Q3D renderers
  (``QAnsysRenderer``, ``QHFSSPyaedt``, ``QQ3DPyaedt``,
  ``QHFSSDrivenmodalPyaedt``, ``QHFSSEigenmodePyaedt``)
- You import or use the EPR analyses
  (``LOManalysis``, ``LumpedElementsSim``,
  ``EigenmodeSim``, ``extract_transmon_coupled_Noscillator``)
- You import or use the gmsh / Elmer renderers
  (``QGmshRenderer``, ``Vec3DArray``, the
  ``renderer_elmer`` module)

You **probably don't need to do anything** if your workflow is:

- Build a design (``DesignPlanar``, ``DesignFlipChip``, ...)
- Add components from ``qiskit_metal.qlibrary``
- View it inline with ``qm.view(design)``
- Export to GDS via ``QGDSRenderer``
- Run pure-Python analyses that don't touch
  ``quantization/`` or ``simulation/`` modules

The lite install covers the second list out of the box.


What changed
------------

Base ``dependencies`` (the v0.7.0 ``pip install quantum-metal``
slim install):

- All current base deps **except** PySide6, qdarkstyle, pyaedt,
  pyEPR-quantum, and gmsh.

New ``optional-dependencies`` (extras you opt in to):

================  ================================================
Extra             Pulls
================  ================================================
``[gui]``         ``pyside6``, ``qdarkstyle``
``[ansys]``       ``pyaedt``, ``pyEPR-quantum``
``[fem]``         ``gmsh``
``[full]``        all of the above — v0.6.x compatibility set
================  ================================================

The Python API surface itself is **unchanged**. ``MetalGUI``,
``QHFSSPyaedt``, ``QGmshRenderer``, ``LOManalysis`` still exist
in the same import paths. They just raise a clear
``ModuleNotFoundError`` at *use* time if you didn't install the
extra they need.


Migration recipes
-----------------

I am a desktop GUI user
~~~~~~~~~~~~~~~~~~~~~~~

If your workflow opens ``MetalGUI`` and edits designs visually:

.. code-block:: bash

    pip install "quantum-metal[gui]"

You're done. Nothing else changes.


I run HFSS / Q3D analyses
~~~~~~~~~~~~~~~~~~~~~~~~~

Your workflow uses ``QHFSSPyaedt`` or any of the AEDT-based
renderers, or the EPR analyses
(``LOManalysis``, ``EigenmodeSim``, ``LumpedElementsSim``):

.. code-block:: bash

    pip install "quantum-metal[ansys]"

If you also use ``MetalGUI``, install both:

.. code-block:: bash

    pip install "quantum-metal[gui,ansys]"


I use the gmsh / Elmer FEM path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install "quantum-metal[fem]"

Note that gmsh on Apple Silicon Macs still needs the brew
``gmsh`` package — see ``README_Gmsh_Elmer.md``.


I want the v0.6.x all-batteries-included install
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install "quantum-metal[full]"

This is the no-think migration — the install is bit-for-bit
the same dep set you had on v0.6.x.


I am driving Quantum Metal from an AI agent / orchestrator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the workflow v0.7.0 was designed for. The base install
is now what you want:

.. code-block:: bash

    pip install quantum-metal

You get the design builders, all of ``qlibrary``, all
pure-Python analyses, GDS export, and the headless
``qm.view(design)`` viewer in a few dozen MB instead of ~1 GB.

If your orchestrator dispatches to a specific backend, install
only that extra at the dispatch layer:

.. code-block:: bash

    # Worker pod handling HFSS jobs
    pip install "quantum-metal[ansys]"

    # Worker pod handling gmsh-based meshing
    pip install "quantum-metal[fem]"


Common errors and fixes
-----------------------

``ModuleNotFoundError: No module named 'PySide6'``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You instantiated ``MetalGUI`` on a lite install. Fix:

.. code-block:: bash

    pip install "quantum-metal[gui]"


``ModuleNotFoundError: No module named 'pyEPR'``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You called an EPR-using analysis (``LOManalysis.run_lom``,
``extract_transmon_coupled_Noscillator``, or any of the
HFSS/Q3D renderers' simulation methods) on a lite install.
Fix:

.. code-block:: bash

    pip install "quantum-metal[ansys]"


``ModuleNotFoundError: No module named 'gmsh'``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You instantiated ``QGmshRenderer`` or the Elmer renderer on
a lite install. Fix:

.. code-block:: bash

    pip install "quantum-metal[fem]"


``Could not load the Qt platform plugin 'xcb'`` (and similar
``QPA``-style errors)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These come from PySide6 starting up. On a lite install they
shouldn't fire at all. If they do, you're either running
``MetalGUI`` directly or you have a stray
``import PySide6`` in your own code. See :doc:`headless-usage`
for the Qt-free workflow.


Why this change
---------------

Three forces drove it:

- **AI orchestration**. Increasingly, Quantum Metal is used
  inside LLM-driven design loops and multi-backend solver
  pipelines. None of those need a desktop Qt GUI; they want
  a fast, predictable, scriptable Python library.
- **Cloud / Colab / Binder**. Hundreds of MB of Qt + AEDT in
  the base install is friction every notebook environment
  has to work around. Many just give up and pin an older
  version.
- **Academic and educational use**. Users without an Ansys
  license shouldn't be forced to install pyaedt + pyEPR
  to import ``qiskit_metal``.

The Qt-free path was added in v0.6.0 (``qm.view(design)``,
lazy Qt initialization). The v0.7.0 flip completes the
story by making the lite install the **default**, with
extras for the heavy backends.

See :doc:`headless-usage` for what the lite install gives
you today, and `ROADMAP.md
<https://github.com/qiskit-community/qiskit-metal/blob/main/ROADMAP.md>`_
for what's coming next.


Reporting issues
----------------

If the migration recipe for your scenario isn't covered
above, please open an issue at
https://github.com/qiskit-community/qiskit-metal/issues with
the label ``v0.7.0-migration``. Include:

- Your previous install command (``pip install ...``)
- Which Python entry points / classes you use
- The error message you hit

We'll add your case to this doc so the next person hits a
search result instead of a wall.
