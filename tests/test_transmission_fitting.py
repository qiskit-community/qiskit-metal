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
"""fit_transmission on noise-free synthetic notch data (#1209)."""

import unittest
import warnings

import numpy as np

from qiskit_metal.analyses.em.transmission_fitting import fit_transmission

FR = 7.0e9
QC = 7000.0
QL = 1 / (1 / QC + 1 / 2e5)


def notch(f, a, alpha, tau, Ql, Qc, fr, phi):
    """The model of the fit_transmission docstring, absolute frequency."""
    return (
        a
        * np.exp(1j * alpha)
        * np.exp(-2j * np.pi * f * tau)
        * (1 - (Ql / Qc) * np.exp(1j * phi) / (1 + 2j * Ql * (f / fr - 1)))
    )


def _fit(f, s, **kw):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return fit_transmission(f, s, plot=False, **kw)


class TestFitTransmission(unittest.TestCase):
    def check(self, half_span_linewidths, tau, detrend=True):
        half = half_span_linewidths * FR / QL
        f = np.linspace(FR - half, FR + half, 801)
        s = notch(f, 0.8, 0.4, tau, QL, QC, FR, 0.3)
        p, plots = _fit(f, s, detrend=detrend)
        self.assertEqual(plots, [])
        self.assertLess(abs(p["Qr"] / QL - 1), 1e-4)
        self.assertLess(abs(p["Qc"] / QC - 1), 1e-4)
        self.assertLess(abs(p["fr"] / FR - 1), 1e-8)
        self.assertAlmostEqual(abs(p["amplitude_complex"]), 0.8, places=5)
        self.assertAlmostEqual(p["delay"] * 1e9, tau * 1e9, places=4)
        A = p["amplitude_complex"]
        model = notch(
            f, abs(A), np.angle(A), p["delay"], p["Qr"], p["Qc"], p["fr"], p["phi0"]
        )
        self.assertLess(np.max(np.abs(s - model)), 1e-6)

    def test_narrow_and_wide_spans(self):
        for n in (2, 6, 50):
            with self.subTest(linewidths=n):
                self.check(n, 0.0)

    def test_cable_delay(self):
        for n in (6, 50):
            with self.subTest(linewidths=n):
                self.check(n, 40e-9)

    def test_detrend_false(self):
        self.check(6, 0.0, detrend=False)

    def test_full_output_parameters_match_the_model(self):
        f = np.linspace(FR - 50 * FR / QL, FR + 50 * FR / QL, 801)
        s = notch(f, 0.8, 0.4, 30e-9, QL, QC, FR, 0.3)
        values, _, raw, cov = _fit(f, s, full_output=True)
        self.assertEqual(raw.shape, (7,))
        self.assertEqual(cov.shape, (7, 7))
        mag, arg, Qr, Qc, fr, phi0, delay = raw
        np.testing.assert_allclose(values[0], mag * np.exp(1j * arg))
        model = notch(f, mag, arg, delay, Qr, Qc, fr, phi0)
        self.assertLess(np.max(np.abs(s - model)), 1e-6)


if __name__ == "__main__":
    unittest.main()
