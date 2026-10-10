# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Tests for ``analyze_loaded_tl`` (LOM 2.0 transmission-line resonator)
against closed-form transmission-line results."""

import unittest

import numpy as np

from qiskit_metal.analyses.quantization.lom_core_analysis import analyze_loaded_tl

_VP = 299792458.0 / np.sqrt(6.065)


class TestLoadedTLModeLength(unittest.TestCase):
    """The returned length is that of the fundamental mode."""

    def test_open_end_is_loaded_half_wave(self):
        # Open far end, capacitor C at z = 0: Y_stub + jwC = 0 with
        # Y_stub = j tan(kL) / Z0  ->  kL = pi - arctan(w Z0 C).
        fr, Z0, C = 7000.0, 51.6, 54.9
        *_, L = analyze_loaded_tl(fr, _VP, Z0, {"Q": C}, shorted=False)
        w = 2 * np.pi * fr * 1e6
        k = w / _VP
        expected = (np.pi - np.arctan(w * Z0 * C * 1e-15)) / k
        self.assertAlmostEqual(L / expected, 1.0, places=9)

    def test_shorted_end_is_loaded_quarter_wave(self):
        # Shorted far end: Y_stub = 1 / (j Z0 tan(kL))  ->  tan(kL) = 1/(w Z0 C).
        # Used to return the 3*lambda/4 mode (#1206).
        fr, Z0, C = 7000.0, 51.6, 54.9
        *_, L = analyze_loaded_tl(fr, _VP, Z0, {"Q": C}, shorted=True)
        w = 2 * np.pi * fr * 1e6
        k = w / _VP
        expected = np.arctan(1 / (w * Z0 * C * 1e-15)) / k
        self.assertAlmostEqual(L / expected, 1.0, places=9)
        self.assertLess(L, _VP / (fr * 1e6) / 4)

    def test_shorted_unloaded_limit_is_quarter_wave(self):
        fr = 7000.0
        *_, L = analyze_loaded_tl(fr, _VP, 50.0, {"Q": 1e-9}, shorted=True)
        self.assertAlmostEqual(L / (_VP / (fr * 1e6) / 4), 1.0, places=6)


class TestLoadedTLInputUnchanged(unittest.TestCase):
    """The caller's ``cap_loading`` dict is left alone (#1232)."""

    def _check(self, loading, shorted):
        original = dict(loading)
        first = analyze_loaded_tl(6000.0, _VP, 50.0, loading, shorted=shorted)
        self.assertEqual(loading, original)
        second = analyze_loaded_tl(6000.0, _VP, 50.0, loading, shorted=shorted)
        self.assertEqual(first[0], second[0])
        self.assertEqual(first[3], second[3])

    def test_single_open(self):
        self._check({"Q": 50.0}, shorted=False)

    def test_single_shorted(self):
        self._check({"Q": 50.0}, shorted=True)

    def test_two_nodes(self):
        self._check({"a": 20.0, "b": 30.0}, shorted=False)


if __name__ == "__main__":
    unittest.main()
