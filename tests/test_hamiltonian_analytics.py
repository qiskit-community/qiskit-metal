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

import numpy as np
from scipy.integrate import trapezoid

from qiskit_metal.analyses.hamiltonian.HO_wavefunctions import wavefunction


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


if __name__ == "__main__":
    unittest.main()
