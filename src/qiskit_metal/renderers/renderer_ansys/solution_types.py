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
"""HFSS / Q3D solution-type name handling.

HFSS 2024.1 introduced new solution-type identifiers alongside the
legacy ones (``HFSS Modal Network`` / ``HFSS Hybrid Modal Network``
replace ``DrivenModal``; same shape for ``DrivenTerminal``). The
identifiers are reported verbatim by the underlying COM
``GetSolutionType()``.

These alias sets mirror ``pyEPR.solution_types`` (pyEPR PR #176).
**pyEPR normalises ``design.solution_type`` at read time**, so any code
in metal that reads ``pinfo.design.solution_type`` already receives the
canonical pre-AEDT-2021.2 string (``DrivenModal``, ``DrivenTerminal``,
``Eigenmode``, ``Q3D``) regardless of which HFSS version is running. The
predicates here are still correct as defence-in-depth and are
**essential** for the one call site (``hfss_renderer.py``'s
``set_mode``) that reaches past pyEPR and calls
``o_design.GetSolutionType()`` directly — that path sees the raw HFSS
string and would silently mismatch on HFSS 2024.1+ without these
predicates.

If HFSS introduces a new alias in a future release, update both this
file *and* pyEPR's ``solution_types.py``; the test suites in both repos
will fail until the new alias is added, which is the intended early
warning.

This module is pure Python: no Ansys, no Windows, no pyEPR. It's safe
to import on any platform.
"""

from typing import Optional

#: HFSS Eigenmode solver. The legacy name is unchanged in HFSS 2024.1+.
EIGENMODE_NAMES = frozenset({
    'Eigenmode',
})

#: HFSS Driven Modal solver. HFSS 2024.1+ exposes the same solver under
#: two additional identifiers depending on whether the design is
#: "Hybrid". Naming matches ``pyEPR.solution_types.DRIVEN_MODAL_NAMES``.
DRIVEN_MODAL_NAMES = frozenset({
    'DrivenModal',  # HFSS <= 2023
    'HFSS Modal Network',  # HFSS 2024.1+
    'HFSS Hybrid Modal Network',  # HFSS 2024.1+
})

#: HFSS Driven Terminal solver. Renamed in HFSS 2024.1+ alongside Driven
#: Modal. qiskit-metal does not currently ship a renderer for this
#: solver, but the helper is provided so future renderer code can use
#: the same pattern. Naming matches
#: ``pyEPR.solution_types.DRIVEN_TERMINAL_NAMES``.
DRIVEN_TERMINAL_NAMES = frozenset({
    'DrivenTerminal',  # HFSS <= 2023
    'HFSS Terminal Network',  # HFSS 2024.1+
    'HFSS Hybrid Terminal Network',  # HFSS 2024.1+
})

#: Q3D Extractor capacitive/inductive solver. Unaffected by the HFSS
#: 2024.1 rename, but tracked here for symmetry.
Q3D_NAMES = frozenset({
    'Q3D',
})


def is_eigenmode(solution_type: Optional[str]) -> bool:
    """True if ``solution_type`` names the HFSS Eigenmode solver."""
    return solution_type in EIGENMODE_NAMES


def is_drivenmodal(solution_type: Optional[str]) -> bool:
    """True if ``solution_type`` names any alias of the HFSS Driven
    Modal solver, including the post-2024.1 ``HFSS Modal Network`` and
    ``HFSS Hybrid Modal Network`` identifiers."""
    return solution_type in DRIVEN_MODAL_NAMES


def is_driventerminal(solution_type: Optional[str]) -> bool:
    """True if ``solution_type`` names any alias of the HFSS Driven
    Terminal solver."""
    return solution_type in DRIVEN_TERMINAL_NAMES


def is_q3d(solution_type: Optional[str]) -> bool:
    """True if ``solution_type`` names the Q3D Extractor solver."""
    return solution_type in Q3D_NAMES


def canonical_kind(solution_type: Optional[str]) -> Optional[str]:
    """Map a raw HFSS / Q3D ``solution_type`` string to its canonical
    metal-internal kind.

    Returns one of ``'eigenmode'``, ``'drivenmodal'``,
    ``'driventerminal'``, ``'q3d'``, or ``None`` if the string is not a
    recognised solver identifier.

    The metal-internal kinds are stable across HFSS versions; downstream
    metal code (renderer dispatch, design-creation guards) should
    compare against these rather than the raw HFSS strings.
    """
    if is_eigenmode(solution_type):
        return 'eigenmode'
    if is_drivenmodal(solution_type):
        return 'drivenmodal'
    if is_driventerminal(solution_type):
        return 'driventerminal'
    if is_q3d(solution_type):
        return 'q3d'
    return None
