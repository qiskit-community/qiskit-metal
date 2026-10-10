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
"""Regression tests for the analytic transmon / oscillator helpers in
``qiskit_metal.analyses.hamiltonian``, each checked against an independent
numerical reference rather than against pinned outputs."""

import unittest
import warnings

import numpy as np
from scipy.integrate import trapezoid
from scipy.optimize import brentq

from qiskit_metal.analyses.hamiltonian import transmon_analytics
from qiskit_metal.analyses.hamiltonian.HO_wavefunctions import wavefunction
from qiskit_metal.analyses.hamiltonian.transmon_CPB_analytic import Hcpb_analytic
from qiskit_metal.analyses.hamiltonian.transmon_charge_basis import Hcpb

NCUT = 30


def ref_levels(Ej, Ec, ng, nlev=6):
    """Reference transmon levels: dense diagonalization of
    4 Ec (n - ng)^2 - (Ej/2)(|n><n+1| + h.c.) for |n| <= 30."""
    n = np.arange(-NCUT, NCUT + 1)
    H = np.diag(4 * Ec * (n - ng) ** 2) - 0.5 * Ej * (
        np.eye(len(n), k=1) + np.eye(len(n), k=-1)
    )
    return np.linalg.eigvalsh(H)[:nlev]


def ref_f01(Ej, Ec, ng):
    E = ref_levels(Ej, Ec, ng, 2)
    return E[1] - E[0]


class TestHOWavefunction(unittest.TestCase):
    """#1202: LC-oscillator eigenfunctions, coordinate = charge Q."""

    def test_orthonormal_for_many_levels(self):
        """Orthonormal for n = 0..9 (n >= 5 used to raise UnboundLocalError)."""
        for L, C in [(1.0, 1.0), (4.0, 1.0), (0.5, 3.0)]:
            x = np.linspace(-25, 25, 40001)
            psi = np.array([wavefunction(L, C, n, x) for n in range(10)])
            gram = trapezoid(psi[:, None, :] * psi[None, :, :], x, axis=-1)
            np.testing.assert_allclose(gram, np.eye(10), atol=1e-9)

    def test_charge_fluctuation_uses_omega_one_over_sqrt_LC(self):
        """<Q^2> in level n is (n + 1/2) hbar / (L omega), omega = 1/sqrt(LC),
        i.e. (n + 1/2) hbar sqrt(C/L)."""
        L, C = 4.0, 0.25
        x = np.linspace(-30, 30, 60001)
        for n in range(4):
            psi = wavefunction(L, C, n, x)
            q2 = trapezoid(psi**2 * x**2, x)
            self.assertAlmostEqual(q2, (n + 0.5) * np.sqrt(C / L), places=9)

    def test_energy_matches_hbar_omega(self):
        """<H> = (n + 1/2) hbar omega with H = -hbar^2/2L d^2/dQ^2 + Q^2/2C,
        evaluated by finite differences on the returned wavefunction."""
        L, C = 2.0, 0.5
        omega = 1 / np.sqrt(L * C)
        x = np.linspace(-20, 20, 40001)
        dx = x[1] - x[0]
        for n in range(5):
            psi = wavefunction(L, C, n, x)
            d2 = np.gradient(np.gradient(psi, dx), dx)
            energy = trapezoid(psi * (-0.5 / L * d2 + 0.5 * x**2 / C * psi), x)
            self.assertAlmostEqual(energy, (n + 0.5) * omega, places=4)

    def test_si_units_with_hbar(self):
        """SI inputs are normalized when hbar is passed in SI."""
        from scipy.constants import hbar

        L, C = 12e-9, 65e-15
        q_zpf = np.sqrt(hbar / (2 * np.sqrt(L / C)))
        x = np.linspace(-12 * q_zpf, 12 * q_zpf, 20001)
        psi = wavefunction(L, C, 0, x, hbar=hbar)
        self.assertAlmostEqual(trapezoid(psi**2, x), 1.0, places=9)

    def test_negative_level_raises(self):
        with self.assertRaises(ValueError):
            wavefunction(1.0, 1.0, -1, 0.0)


class TestParamsFromFreqFixEC(unittest.TestCase):
    """#1203: Ej at fixed Ec must reproduce f01."""

    def test_reproduces_f01_against_reference(self):
        Ec = 295.2
        for ratio in (20.0, 47.33, 70.0, 100.0):
            for ng in (0.5, 0.0):
                f01 = ref_f01(ratio * Ec, Ec, ng)
                # Independent inverse: root find on the dense reference.
                Ej_ref = brentq(lambda e: ref_f01(e, Ec, ng) - f01, 1.0, 1e6)
                h = Hcpb(nlevels=15, Ej=1.0, Ec=Ec, ng=ng)
                with warnings.catch_warnings():
                    warnings.simplefilter("error")
                    Ej = h.params_from_freq_fixEC(f01, Ec)
                self.assertAlmostEqual(Ej / Ej_ref, 1.0, places=7)
                self.assertAlmostEqual(h.Ej, Ej)
                self.assertLess(abs(ref_f01(Ej, Ec, ng) - f01), 1e-3)

    def test_tutorial_4_34_numbers(self):
        """Tutorial 4.34: Ej = 13971.3, Ec = 295.2 (used to return 14424)."""
        Ec = 295.2
        f01 = Hcpb(nlevels=15, Ej=13971.3, Ec=Ec, ng=0.5).fij(0, 1)
        Ej = Hcpb(nlevels=15, Ej=1, Ec=Ec, ng=0.5).params_from_freq_fixEC(f01, Ec)
        self.assertAlmostEqual(Ej, 13971.3, delta=1e-3)

    def test_unreachable_target_warns(self):
        # At ng = 0, f01 >= ~4 Ec for every Ej >= 0, so 100 is unreachable.
        self.assertGreater(min(ref_f01(e, 300.0, 0.0) for e in (0, 300, 1e3, 1e4)), 100)
        h = Hcpb(nlevels=15, Ej=1.0, Ec=300.0, ng=0.0)
        with self.assertWarns(UserWarning):
            h.params_from_freq_fixEC(100.0, 300.0)


class TestParamsFromSpectrum(unittest.TestCase):
    """#1221: (Ej, Ec) must reproduce (f01, anharm) or warn."""

    def test_grid_reproduces_targets(self):
        Ec = 250.0
        for ratio in (20.0, 46.0, 100.0, 200.0, 300.0):
            E = ref_levels(ratio * Ec, Ec, 0.5, 3)
            f01, alpha = E[1] - E[0], (E[2] - E[1]) - (E[1] - E[0])
            h = Hcpb(nlevels=15, Ej=1.0, Ec=1.0)  # default ng = 0.5
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                Ej, Ec_fit = h.params_from_spectrum(f01, alpha)
            E2 = ref_levels(Ej, Ec_fit, 0.5, 3)
            self.assertLess(abs((E2[1] - E2[0]) - f01), 1e-3, msg=ratio)
            self.assertLess(
                abs((E2[2] - E2[1]) - (E2[1] - E2[0]) - alpha), 1e-3, msg=ratio
            )
            # At ng = 1/2, alpha/Ec is not monotonic in Ej/Ec below ~30, so
            # (f01, alpha) -> (Ej, Ec) is not unique there (Ej/Ec = 20 has a
            # second solution near 15.6); only check uniqueness above that.
            if ratio >= 30:
                self.assertAlmostEqual(Ej / (ratio * Ec), 1.0, places=6)
                self.assertAlmostEqual(Ec_fit / Ec, 1.0, places=6)

    def test_unreachable_target_warns(self):
        h = Hcpb(nlevels=15, Ej=1.0, Ec=1.0)
        with self.assertWarns(UserWarning):
            h.params_from_spectrum(3000.0, -800.0)


class TestMathieuLevels(unittest.TestCase):
    """#1220: Hcpb_analytic / transmon_eigenvalue vs the dense reference."""

    NG = (0.0, 0.5, -0.5, 0.25, -0.3, 0.1, 0.9, 1.0)

    def test_hcpb_analytic_matches_reference(self):
        Ec = 298.0
        for ratio in (1.0, 5.0, 20.0, 45.7, 100.0):
            for ng in self.NG:
                ref = ref_levels(ratio * Ec, Ec, ng)
                h = Hcpb_analytic(Ej=ratio * Ec, Ec=Ec, ng=ng)
                got = np.array([h.evalue_k(m) for m in range(6)])
                np.testing.assert_allclose(
                    got, ref, rtol=0, atol=1e-6 * Ec, err_msg=f"Ej/Ec={ratio}, ng={ng}"
                )

    def test_transmon_eigenvalue_explicit_and_module_defaults(self):
        Ej, Ec = 13622.0, 298.0
        for ng in (0.0, 0.25, 0.5):
            ref = ref_levels(Ej, Ec, ng)
            got = [
                transmon_analytics.transmon_eigenvalue(m, ng, Ej=Ej, Ec=Ec)
                for m in range(6)
            ]
            np.testing.assert_allclose(got, ref, rtol=0, atol=1e-6 * Ec)
        # Without Ej/Ec, the module constants RATIO and E_C are used.
        ref = ref_levels(
            transmon_analytics.RATIO * transmon_analytics.E_C,
            transmon_analytics.E_C,
            0.0,
        )
        got = [transmon_analytics.transmon_eigenvalue(m, 0.0) for m in range(4)]
        np.testing.assert_allclose(got, ref[:4], rtol=0, atol=1e-9)


if __name__ == "__main__":
    unittest.main()
