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
"""Checks of the closed-form kappa and chi helpers against independent
numerical models (a distributed transmission line for kappa, exact
diagonalization of a transmon coupled to an oscillator for chi)."""

import unittest
import warnings

import numpy as np
from scipy import linalg
from scipy.optimize import fsolve
from scipy.special import ellipk

from qiskit_metal.analyses.em.kappa_calculation import kappa_in
from qiskit_metal.analyses.quantization.lumped_capacitive import chi

Z0 = 50.0


def transmon_ladder(Ej, Ec, ng=0.0, nt=8, ncut=30):
    """Transmon levels (relative to E0) and the signed charge operator in the
    energy basis, from 4 Ec (n - ng)^2 - Ej cos(phi), |n| <= ncut."""
    n = np.arange(-ncut, ncut + 1)
    ev, vec = linalg.eigh_tridiagonal(
        4 * Ec * (n - ng) ** 2, -Ej / 2 * np.ones(2 * ncut)
    )
    vec = vec[:, :nt]
    return ev[:nt] - ev[0], vec.T @ np.diag(n) @ vec


def chi_exact(ev, nop, g, wr, n_res=12):
    """chi = [(E11 - E10) - (E01 - E00)] / 2 from exact diagonalization of
    H_t + wr a^dag a + beta n (a + a^dag) (no RWA), beta = g / |n01|."""
    nt = len(ev)
    a = np.diag(np.sqrt(np.arange(1, n_res)), 1)
    beta = g / abs(nop[0, 1])
    H = (
        np.kron(np.diag(ev), np.eye(n_res))
        + wr * np.kron(np.eye(nt), a.T @ a)
        + beta * np.kron(nop, a + a.T)
    )
    E, V = np.linalg.eigh(H)

    def dressed(i, k):
        return E[np.argmax(np.abs(V[i * n_res + k, :]))]

    return ((dressed(1, 1) - dressed(1, 0)) - (dressed(0, 1) - dressed(0, 0))) / 2


def line_complex_mode(f_bare, Ck, eta):
    """Complex natural frequency of an ideal TL resonator (open far end for
    eta = 2, shorted for eta = 4) coupled at its open end through Ck to a
    matched Z0 load: Y_line(w) + 1/(Z0 + 1/(j w Ck)) = 0, exp(j w t)."""
    wr = 2 * np.pi * f_bare
    bl_per_w = np.pi / wr if eta == 2 else np.pi / (2 * wr)

    def F(v):
        w = v[0] + 1j * v[1]
        bl = w * bl_per_w
        y_line = 1j / Z0 * np.tan(bl) if eta == 2 else -1j / Z0 / np.tan(bl)
        y_ext = 1.0 / (Z0 + 1.0 / (1j * w * Ck))
        r = (y_line + y_ext) * Z0
        return [r.real, r.imag]

    v = fsolve(F, [wr * 0.999, wr * 1e-5], xtol=1e-12)
    return v[0] + 1j * v[1]


class TestKappaIn(unittest.TestCase):
    """#1204: kappa_in returns kappa/2pi in Hz."""

    def test_three_args_matches_distributed_line(self):
        """Half-wave resonator: kappa/2pi from the complex root of the line
        model, within 0.1 % for weak coupling."""
        for f_bare, Ck in [(7e9, 6.81e-15), (7e9, 2e-15), (5e9, 5e-15)]:
            w = line_complex_mode(f_bare, Ck, eta=2)
            f_loaded = w.real / (2 * np.pi)
            kappa_2pi = 2 * abs(w.imag) / (2 * np.pi)
            got = kappa_in(f_loaded, Ck, f_loaded)
            self.assertAlmostEqual(got / kappa_2pi, 1.0, delta=1e-3)

    def test_six_args_quarter_wave_matches_distributed_line(self):
        """Six-argument form: f_res = c / (eta l sqrt(eps_eff)) and the
        quarter-wave prefactor 4/pi, checked against the line model."""
        width, gap, length, Ck = 10e-6, 6e-6, 4.3e-3, 3e-15
        k0 = width / (width + 2 * gap)
        sqrt_eps = 30 * np.pi * ellipk(1 - k0**2) / (Z0 * ellipk(k0**2))
        f_res = 299792458.0 / (4 * length * sqrt_eps)
        self.assertAlmostEqual(f_res / 6.86e9, 1.0, delta=0.01)  # ~ 6.9 GHz
        w = line_complex_mode(f_res, Ck, eta=4)
        kappa_2pi = 2 * abs(w.imag) / (2 * np.pi)
        # Evaluated at the bare resonance (as the six-argument form does) the
        # formula is ~1 % high: kappa ~ w^3 and loading pulls w down ~0.4 %.
        got = kappa_in(f_res, Ck, length, width, gap, 4.0)
        self.assertAlmostEqual(got / kappa_2pi, 1.0, delta=0.02)
        w_l = w.real
        at_loaded = (4 / np.pi) * w_l**3 * Ck**2 * Z0**2 / (2 * np.pi)
        self.assertAlmostEqual(at_loaded / kappa_2pi, 1.0, delta=1e-3)
        # Half-wave of the same length: twice the frequency, (2/pi) prefactor,
        # identical to the three-argument form.
        got2 = kappa_in(2 * f_res, Ck, length, width, gap, 2.0)
        self.assertAlmostEqual(
            got2 / kappa_in(2 * f_res, Ck, 2 * f_res), 1.0, places=12
        )

    def test_tutorial_4_15_value(self):
        """5 GHz, 30 fF, 4.5 GHz: (2/pi) w^2 C^2 Z0^2 w_r / 2pi = 6.36 MHz."""
        w, wr = 2 * np.pi * 5e9, 2 * np.pi * 4.5e9
        expected = (2 / np.pi) * w**2 * (30e-15) ** 2 * Z0**2 * wr / (2 * np.pi)
        self.assertAlmostEqual(kappa_in(5e9, 30e-15, 4.5e9) / expected, 1.0, places=12)
        self.assertAlmostEqual(expected / 1e6, 6.3617, places=3)

    def test_wrong_argument_count_warns(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.assertIsNone(kappa_in(1.0, 1.0))
        self.assertTrue(any("3" in str(c.message) for c in caught))


class TestChi(unittest.TestCase):
    """#1208: lumped_capacitive.chi vs exact transmon-oscillator spectra."""

    Ec = 0.30  # GHz
    g = 0.05  # GHz

    def test_default_is_unchanged_harmonic_g12(self):
        g, wr, w01, w12 = 0.07, 7.0, 5.3824, 5.3824 - 0.3455
        old = (
            g**2 * (1 / (w01 - wr) - 2 / (w12 - wr) + 1 / (w01 + wr) - 2 / (w12 + wr))
            + 2 * g**2 * w01 / (w01**2 - wr**2)
        ) / 2
        self.assertAlmostEqual(chi(g, wr, w01, w12), old, places=15)
        self.assertEqual(chi(g, wr, w01, w12, g12=np.sqrt(2) * g), chi(g, wr, w01, w12))

    def test_exact_g12_matches_diagonalization(self):
        """With g12 = g n12/n01 the result is within 2.5 % of exact
        diagonalization for Ej/Ec = 30-100 and detunings -2..+1 GHz."""
        for ratio in (30, 46, 70, 100):
            ev, nop = transmon_ladder(ratio * self.Ec, self.Ec)
            f01, f12 = ev[1], ev[2] - ev[1]
            r = abs(nop[1, 2]) / abs(nop[0, 1])
            for delta in (-2.0, -1.0, -0.7, 1.0):
                wr = f01 - delta
                ref = chi_exact(ev, nop, self.g, wr)
                got = chi(self.g, wr, f01, f12, g12=r * self.g)
                self.assertAlmostEqual(got / ref, 1.0, delta=0.025, msg=(ratio, delta))

    def test_harmonic_default_is_biased(self):
        """Documents the bias of the default g12 = sqrt(2) g (see docstring)."""
        ev, nop = transmon_ladder(46 * self.Ec, self.Ec)
        f01, f12 = ev[1], ev[2] - ev[1]
        wr = f01 + 1.0
        ref = chi_exact(ev, nop, self.g, wr)
        self.assertLess(chi(self.g, wr, f01, f12) / ref, 0.9)


if __name__ == "__main__":
    unittest.main()
