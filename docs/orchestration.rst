.. _orchestration:

=======================================
Scripting Quantum Metal and agent use
=======================================

Quantum Metal builds a chip from Python objects, and everything between the
first line and the GDS file runs without a window: no Qt, no prompts and no
state outside the design object. That makes it a good fit for scripts, test
suites, optimizers and coding assistants that generate a design, check it and
iterate. This page shows the loop, how to make the design-rule check the pass
or fail signal, and what to rely on from run to run.

It needs only the lite install, ``pip install quantum-metal`` (see
:doc:`headless-usage`).

The loop: build, check, export, analyze
=======================================

The script below builds a transmon with a meandered readout resonator and a
launchpad, checks the design, exports a picture and a GDS file, and estimates the
transmon levels. It is tested with the rest of the suite, so it runs as shown.
Download it as :download:`headless_chip.py <examples/headless_chip.py>`.

.. literalinclude:: examples/headless_chip.py
    :language: python
    :linenos:

Run it with ``python headless_chip.py chip_out``. It prints

.. code-block:: text

    Design rules passed (11 rules ran, no findings).
    f01 = 5.267 GHz, anharmonicity = -350 MHz
    geometry fingerprint: 8463ea8fe7b47922

and writes ``chip.png`` and ``chip.gds``.

The analysis step here is an estimate from :math:`E_J` and :math:`E_C`. For
capacitances, eigenmodes and couplings from a field solver, see
:doc:`simulation-pathways`; the same script can hand the design to a solver
renderer in place of that last step.

The design-rule check as the success signal
===========================================

``validate(design)`` runs the design rules and returns a result. A script or an
agent needs three things from it:

* ``result.ok`` is ``True`` when nothing of ERROR severity was found. ERROR
  means the geometry is wrong whatever the intent: a shape off the chip, a short
  between nets, a route too close to a qubit. A WARNING is legal geometry that is
  probably unintended, such as a straight segment too short for its fillet.
* ``result.errors`` and ``result.warnings`` are lists of findings. Each has a
  ``severity``, the ``rule`` that raised it, the ``components`` involved and a
  ``message`` that says what to change.
* ``validate(design, strict=True)`` raises ``DesignRuleViolation`` on any ERROR,
  and ``result.raise_if_errors()`` does the same later. Use either as a gate in a
  build script or in CI.

For example, move the launchpad off the chip:

.. code-block:: python

    design = build()
    design.components["LP1"].options.pos_x = "3.5mm"
    design.rebuild()

    result = validate(design)
    for finding in result.errors:
        print(finding.rule, finding.components, finding.message)

.. code-block:: text

    chip-bounds ('LP1',) LP1 extends 1760.0 um beyond the 'main' chip outline
    chip-bounds ('readout',) readout extends 1475.0 um beyond the 'main' chip outline

An optimizer can read these findings, change an option and rebuild until the
result is clean. Findings you accept on purpose are recorded with
``validate(design, waivers=[...])``, which keeps the reason in the report instead
of hiding it. The rules and their thresholds are described in
:mod:`qiskit_metal.validation`; a different process design kit is a constructor
argument, not a fork.

Watch a script and see the chip update
======================================

While you edit a design script, ``python -m qiskit_metal.watch my_design.py``
re-runs it each time you save, writes ``watch_out/design.png``, and prints the
design-rule report. Add ``--gds`` to also write ``watch_out/design.gds``, which
KLayout can reload. The script only has to leave a ``QDesign`` in a variable named
``design`` (``--var`` changes the name). An error in the script is printed and the
watch keeps running. Nothing here needs Qt.

Getting the same answer twice
=============================

* **Geometry.** Building the same options gives the same geometry. The script's
  ``fingerprint`` function hashes every polygon and path in a fixed order, so two
  runs print the same value. Compare it in a test to catch a change that moves
  the layout.
* **The GDS file.** A GDS file stores the time it was written, so two exports of
  one design differ by a few bytes. Set the standard ``SOURCE_DATE_EPOCH``
  environment variable (seconds since 1970) and the export is identical byte for
  byte:

  .. code-block:: bash

      SOURCE_DATE_EPOCH=1700000000 python headless_chip.py chip_out

* **The design as a script.** ``design.to_python_script()`` returns the Python
  that rebuilds the design, which is a readable artifact to store next to the GDS.

What to rely on
===============

Quantum Metal is a 0.x library, so a minor release can change behavior. Two
habits keep a script safe:

* Rely on the surface the :doc:`API reference <overview>` documents:
  ``QDesign`` and its subclasses, ``QComponent`` options, ``qm.view`` and
  ``qm.gui``, ``validate``, the renderers' export methods and the analyses.
  Public method signatures do not change without a deprecation path.
* Read the *Behavior changes* part of the `changelog
  <https://github.com/qiskit-community/qiskit-metal/blob/main/changelog.md>`_ when
  you upgrade. Every change that moves numbers or geometry is listed there, and
  the fingerprint above shows whether your design moved.

Pin the version in your environment (for example ``quantum-metal==0.10.0``) so a
run you want to repeat uses the same code.

Using a coding assistant
========================

An assistant can drive the script above directly: ask it to change options, run
``validate``, and keep going until ``result.ok`` is true, then export. Give it the
``validate`` output as feedback, since the finding messages say what is wrong.

The repository also carries task notes written for assistants, as plain Markdown
files that any tool can read, under ``.claude/skills/``:

* ``chip-design``: from a specification to a staged build with a check after
  every stage;
* ``chip-layout-from-images``: reproducing a published device from its figures;
* ``chip-simulation``: choosing a solver and extracting capacitances, frequencies
  and couplings;
* ``tutorial-notebook``: writing and re-running tutorial notebooks.

Point an assistant at the one that matches the task. The design-rule check is the
success signal in all of them.

Where a script cannot go
========================

Interactive editing needs the desktop GUI (:doc:`gui-shortcuts`). Ansys solves
need an Ansys license, and the Ansys renderers run on a machine where Ansys is
installed. Everything else on this page runs anywhere Python does, including
Colab and a CI runner.
