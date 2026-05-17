# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Headless matplotlib viewer for Quantum Metal designs.

Exposes :func:`view`, a one-line entry point that returns a matplotlib
:class:`~matplotlib.figure.Figure` populated with every component's
geometry. No Qt, no :class:`~qiskit_metal._gui.main_window.MetalGUI`;
works in plain Python, Jupyter notebooks, headless CI, Binder, Colab.

The viewer reuses :class:`~qiskit_metal.renderers.renderer_mpl.mpl_renderer.QMplRenderer`
internally — same rendering logic the Qt GUI uses — but in standalone
mode (no Qt canvas).

Example
-------

>>> import qiskit_metal as qm
>>> from qiskit_metal.designs import DesignPlanar
>>> from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
>>> design = DesignPlanar()
>>> TransmonPocket(design, 'Q1', options={'connection_pads': {'a': {}}})
>>> fig = qm.view(design)
>>> fig.savefig('q1.png')
"""

from __future__ import annotations

from typing import Iterable, Optional, Tuple

from .view import view

__all__ = ["view"]
