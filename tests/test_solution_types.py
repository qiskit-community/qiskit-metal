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
"""Tests for HFSS solution-type alias handling.

HFSS 2024.1 introduced new solution-type identifiers (``HFSS Modal
Network``, ``HFSS Hybrid Modal Network``, ``HFSS Terminal Network``,
``HFSS Hybrid Terminal Network``) alongside the legacy ``DrivenModal`` /
``DrivenTerminal`` names. The helpers in
:mod:`qiskit_metal.renderers.renderer_ansys.solution_types` must accept
both eras and reject anything else. These tests pin every alias the
metal renderers depend on so an HFSS or pyEPR rename surfaces in CI
rather than silently in user simulations.

The tests are pure-string and cross-platform; no Ansys, no Windows.
"""

import unittest

from qiskit_metal.renderers.renderer_ansys.solution_types import (
    DRIVEN_MODAL_NAMES, DRIVEN_TERMINAL_NAMES, EIGENMODE_NAMES, Q3D_NAMES,
    canonical_kind, is_drivenmodal, is_driventerminal, is_eigenmode, is_q3d)


class TestSolutionTypeAliases(unittest.TestCase):
    """The frozen sets must contain every alias the renderers branch on."""

    def test_eigenmode_legacy_name_present(self):
        self.assertIn('Eigenmode', EIGENMODE_NAMES)

    def test_drivenmodal_legacy_name_present(self):
        """``DrivenModal`` is what HFSS <= 2023 returns. Must remain
        accepted to keep older installations working."""
        self.assertIn('DrivenModal', DRIVEN_MODAL_NAMES)

    def test_drivenmodal_hfss_2024_aliases_present(self):
        """HFSS 2024.1+ reports DrivenModal under two new identifiers
        (Hybrid vs non-Hybrid). Both must map to the drivenmodal kind."""
        self.assertIn('HFSS Modal Network', DRIVEN_MODAL_NAMES)
        self.assertIn('HFSS Hybrid Modal Network', DRIVEN_MODAL_NAMES)

    def test_driventerminal_legacy_name_present(self):
        self.assertIn('DrivenTerminal', DRIVEN_TERMINAL_NAMES)

    def test_driventerminal_hfss_2024_aliases_present(self):
        self.assertIn('HFSS Terminal Network', DRIVEN_TERMINAL_NAMES)
        self.assertIn('HFSS Hybrid Terminal Network',
                      DRIVEN_TERMINAL_NAMES)

    def test_q3d_name_present(self):
        self.assertIn('Q3D', Q3D_NAMES)

    def test_alias_sets_are_disjoint(self):
        """The four kinds must not share any alias; a single
        ``solution_type`` can never legitimately be two kinds at once."""
        all_sets = (EIGENMODE_NAMES, DRIVEN_MODAL_NAMES,
                    DRIVEN_TERMINAL_NAMES, Q3D_NAMES)
        for i, a in enumerate(all_sets):
            for j, b in enumerate(all_sets):
                if i < j:
                    self.assertEqual(a & b, frozenset(),
                                     f'overlap between {a} and {b}')


class TestSolutionTypePredicates(unittest.TestCase):
    """``is_*`` predicates must match every alias and reject unknowns."""

    def test_is_eigenmode_accepts_all_aliases(self):
        for name in EIGENMODE_NAMES:
            self.assertTrue(is_eigenmode(name), name)

    def test_is_drivenmodal_accepts_all_aliases(self):
        for name in DRIVEN_MODAL_NAMES:
            self.assertTrue(is_drivenmodal(name), name)

    def test_is_driventerminal_accepts_all_aliases(self):
        for name in DRIVEN_TERMINAL_NAMES:
            self.assertTrue(is_driventerminal(name), name)

    def test_is_q3d_accepts_all_aliases(self):
        for name in Q3D_NAMES:
            self.assertTrue(is_q3d(name), name)

    def test_predicates_reject_unknown_strings(self):
        for unknown in ('', 'eigenmode', 'drivenmodal',
                        'HFSSEigenmode', 'modal', None):
            self.assertFalse(is_eigenmode(unknown), repr(unknown))
            self.assertFalse(is_drivenmodal(unknown), repr(unknown))
            self.assertFalse(is_driventerminal(unknown), repr(unknown))
            self.assertFalse(is_q3d(unknown), repr(unknown))

    def test_predicates_are_case_sensitive(self):
        """HFSS reports CamelCase; tolerating other casings would mask
        bugs. Confirm we don't silently accept lowercase variants."""
        self.assertFalse(is_eigenmode('eigenmode'))
        self.assertFalse(is_drivenmodal('drivenmodal'))
        self.assertFalse(is_drivenmodal('hfss modal network'))
        self.assertFalse(is_q3d('q3d'))


class TestCanonicalKind(unittest.TestCase):
    """``canonical_kind`` is what call sites use to dispatch."""

    def test_eigenmode_maps(self):
        self.assertEqual(canonical_kind('Eigenmode'), 'eigenmode')

    def test_drivenmodal_legacy_maps(self):
        self.assertEqual(canonical_kind('DrivenModal'), 'drivenmodal')

    def test_drivenmodal_hfss_2024_aliases_map(self):
        self.assertEqual(canonical_kind('HFSS Modal Network'),
                         'drivenmodal')
        self.assertEqual(canonical_kind('HFSS Hybrid Modal Network'),
                         'drivenmodal')

    def test_driventerminal_legacy_maps(self):
        self.assertEqual(canonical_kind('DrivenTerminal'),
                         'driventerminal')

    def test_driventerminal_hfss_2024_aliases_map(self):
        self.assertEqual(canonical_kind('HFSS Terminal Network'),
                         'driventerminal')
        self.assertEqual(canonical_kind('HFSS Hybrid Terminal Network'),
                         'driventerminal')

    def test_q3d_maps(self):
        self.assertEqual(canonical_kind('Q3D'), 'q3d')

    def test_unknown_returns_none(self):
        self.assertIsNone(canonical_kind(''))
        self.assertIsNone(canonical_kind(None))
        self.assertIsNone(canonical_kind('NotASolverType'))
        self.assertIsNone(canonical_kind('eigenmode'))  # wrong case


if __name__ == '__main__':
    unittest.main(verbosity=2)
