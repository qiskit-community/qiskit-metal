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

    def test_heavily_loaded_two_ends_is_fundamental(self):
        # With phi_0 + phi_L > pi/2 the old arctan form jumped to the next
        # mode. Check the ABCD resonance condition Y_in(0) + jwC0 = 0 with
        # 0 < kL < pi.
        fr, Z0 = 6000.0, 50.0
        for c0, cl in ((20.0, 60.0), (400.0, 400.0), (600.0, 600.0), (900.0, 100.0)):
            with self.subTest(c0=c0, cl=cl):
                *_, L = analyze_loaded_tl(fr, _VP, Z0, {"a": c0, "b": cl})
                w = 2 * np.pi * fr * 1e6
                kL = w / _VP * L
                self.assertGreater(kL, 0)
                self.assertLess(kL, np.pi)
                y0, yl = 1 / Z0, 1j * w * cl * 1e-15
                t = np.tan(kL)
                y_in = y0 * (yl + 1j * y0 * t) / (y0 + 1j * yl * t)
                self.assertLess(abs(y_in + 1j * w * c0 * 1e-15) / y0, 1e-9)


def _q_zpf_shorted_stub(fr, vp, Z0, C):
    """Independent Q_zpf for a capacitor C [F] loading a shorted stub:
    u(z) = sin(k (L - z)), tan(kL) = 1 / (w Z0 C), Eq. 19-20 of
    arXiv:2103.10344 with the line integral done numerically."""
    from scipy.integrate import quad

    # same hbar as the code under test, so only the physics is compared
    from qiskit_metal.analyses.quantization.constants import hbar

    w = 2 * np.pi * fr * 1e6
    k = w / vp
    L = np.arctan(1 / (w * Z0 * C)) / k
    c = 1 / (Z0 * vp)
    u0 = np.sin(k * L)
    line = quad(lambda z: np.sin(k * (L - z)) ** 2, 0, L, epsabs=0, epsrel=1e-13)[0]
    p = C * u0**2 / (C * u0**2 + c * line)
    return np.sqrt(hbar * w / 2 * C * p)


class TestLoadedTLShortedEnd(unittest.TestCase):
    """A shorted end is treated exactly (#1233)."""

    def test_q_zpf_matches_closed_form(self):
        for C in (20.0, 54.9, 300.0):
            with self.subTest(C=C):
                q, *_ = analyze_loaded_tl(7000.0, _VP, 51.6, {"Q": C}, shorted=True)
                ref = _q_zpf_shorted_stub(7000.0, _VP, 51.6, C * 1e-15)
                self.assertAlmostEqual(q["Q"] / ref, 1.0, places=11)

    def test_shorted_end_has_no_charge_fluctuation(self):
        q, phi, *_ = analyze_loaded_tl(6000.0, _VP, 50.0, {"Q": 50.0}, shorted=True)
        self.assertEqual(q["_cl"], 0.0)
        self.assertEqual(phi["_cl"], np.inf)

    def test_q_zpf_is_smooth_in_frequency(self):
        fs = np.linspace(6000.0, 6000.001, 41)  # MHz, 1 kHz span
        q = np.array(
            [
                analyze_loaded_tl(f, _VP, 50.0, {"Q": 50.0}, shorted=True)[0]["Q"]
                for f in fs
            ]
        )
        x = fs - fs[0]
        resid = q - np.polyval(np.polyfit(x, q, 2), x)
        self.assertLess(np.max(np.abs(resid)) / q[0], 1e-10)


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
