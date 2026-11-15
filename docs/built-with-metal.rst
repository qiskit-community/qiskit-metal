.. _built-with-metal:

==========================
Devices and papers
==========================

Images of devices designed with Quantum Metal, and the papers, theses and software that
used it. Notebooks that reproduce published devices are on a separate page:
:doc:`research`.

.. grid:: 1 2 4 4
    :gutter: 2

    .. grid-item::

        .. button-ref:: devices-fabricated
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Device images

    .. grid-item::

        .. button-ref:: devices-chips
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Chips and designs

    .. grid-item::

        .. button-ref:: devices-papers
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Papers and theses

    .. grid-item::

        .. button-ref:: devices-software
            :ref-type: ref
            :color: primary
            :shadow:
            :expand:

            Software

Entries come from published sources that name Quantum Metal (or Qiskit Metal).
A paper is listed under "Papers and theses" only if it used the software for a
design or an analysis; papers that cite or review it are at the end.
To add or correct an entry, open an issue or a pull request that edits
``docs/_data/papers.json``.

.. _devices-fabricated:

Device images
=============

{{ QM_FABRICATED }}

.. _devices-chips:

Chips and designs
=================

{{ QM_PAPERS:chips }}

.. _devices-papers:

Papers and theses that used Quantum Metal
=========================================

{{ QM_PAPERS:papers }}

.. _devices-software:

Software built on or for Quantum Metal
======================================

Further tools are described on :doc:`ecosystem`.

{{ QM_PAPERS:software }}

.. _devices-mentions:

Papers that cite or discuss Quantum Metal
=========================================

Reviews, comparisons and papers that name the software without using it for a
design in the work.

{{ QM_PAPERS:mentions }}

Next
====

To rebuild one of these devices, see :doc:`research`. To start a design of your own, see :doc:`quickstart`.
