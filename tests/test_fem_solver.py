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
"""The package-mode solver: analytic models (analyses/em/package_modes.py)
and the scikit-fem Maxwell solver (analyses/fem). Tier 0: the finite-element
check is an empty box on a coarse mesh; it is skipped without gmsh and
scikit-fem."""

import subprocess
import sys
import unittest

import numpy as np

from qiskit_metal.analyses.em import package_modes as pm

C0 = 299792458.0


def _fem_available():
    try:
        import gmsh  # noqa: F401
        import skfem  # noqa: F401

        return True
    except Exception:
        return False


class TestAnalyticPackageModes(unittest.TestCase):
    def test_lsm_mode_of_the_paper_device(self):
        """30 x 30 x 3 mm box with 0.5 mm of silicon: 6.493 GHz (validation
        record in docs/architecture/open_fem_scikit_fem.md)."""
        mode = pm.lsm_mode(1, 1, Lx=30, Ly=30, Lz=3, t=0.5, eps_r=11.9)
        self.assertAlmostEqual(mode.f / 1e9, 6.493, places=2)
        approx = pm.lsm_mode_approx(1, 1, Lx=30, Ly=30, Lz=3, t=0.5, eps_r=11.9)
        self.assertLess(abs(approx["f"] / mode.f - 1), 0.02)

    def test_without_the_slab_it_is_the_box_mode(self):
        mode = pm.lsm_mode(1, 1, Lx=30, Ly=30, Lz=3, t=1e-6, eps_r=11.9)
        tm110 = C0 / 2 * np.hypot(1 / 30e-3, 1 / 30e-3)
        self.assertLess(abs(mode.f / tm110 - 1), 1e-4)

    def test_lsm_mode_small_box_finds_the_lowest_root(self):
        """#1211: for small boxes the pole of ks tan(ks t) lies inside the
        old bracket (ValueError at 4 mm, a higher root at 2 mm)."""
        t, eps_r = 0.5, 11.45
        for L, f_ghz in ((12, 16.072), (4, 39.093), (2, 51.329)):
            mode = pm.lsm_mode(1, 1, L, L, 3.0, t, eps_r)
            self.assertAlmostEqual(mode.f / 1e9, f_ghz, places=2)
            self.assertLess(mode.kz_si * t * 1e-3, np.pi / 2)
            ks, ka = mode.kz_si, mode.kz_air
            lhs = ks * np.tan(ks * t * 1e-3)
            rhs = eps_r * ka * np.tanh(ka * (3.0 - t) * 1e-3)
            self.assertLess(abs(lhs - rhs) / abs(rhs), 1e-8)

    def test_lsm_mode_approx_warns_outside_its_validity(self):
        """#1211 follow-up: warn when kz_si * t > 0.5 (thin-slab limit)."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            pm.lsm_mode_approx(1, 1, 30, 30, 3.0, 0.5, 11.45)
        with self.assertWarns(UserWarning):
            pm.lsm_mode_approx(1, 1, 5, 5, 3.0, 0.5, 11.45)

    def test_uncoupled_circuit_frequencies(self):
        C = np.diag([100e-15, 200e-15])
        L = np.diag([10e-9, 5e-9])
        expected = sorted(1 / np.sqrt(np.diag(L) * np.diag(C)))  # rad/s
        f = sorted(np.ravel(pm.circuit_eigenfrequencies(C, L)))
        np.testing.assert_allclose(f, expected, rtol=1e-12)

    def test_grid_and_amplitude_fit(self):
        centers = pm.qubit_centers(2, 3.0)
        self.assertEqual(centers[(1, 0)], (4.5, 1.5))
        n, Lx = 4, 12.0
        g = np.zeros((n, n))
        for (i, j), (x, y) in pm.qubit_centers(n, Lx / n).items():
            g[j, i] = 2.5 * np.cos(np.pi * x / Lx) * np.sin(np.pi * y / Lx)
        A, residual = pm.fit_amplitude(g, 1, 1, Lx, Lx)
        self.assertAlmostEqual(A, 2.5)
        self.assertLess(residual, 1e-12)

    def test_importing_the_solver_needs_no_scikit_fem(self):
        code = (
            "import sys; import qiskit_metal.analyses.fem as f; "
            "print('skfem' in sys.modules, 'gmsh' in sys.modules)"
        )
        out = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, check=True
        )
        self.assertEqual(out.stdout.split()[-2:], ["False", "False"])


@unittest.skipUnless(_fem_available(), "gmsh and scikit-fem not installed")
class TestMaxwellFEM(unittest.TestCase):
    def test_empty_box_mode(self):
        """TM110 of an empty 6 x 6 x 3 mm box on a coarse mesh, within 3 %."""
        from qiskit_metal.analyses.fem import MaxwellFEM, Package, mesh_package

        box = Package(Lx=6.0, Ly=6.0, Lz=3.0, t=0.5, eps_r=1.0, metals={}, junctions={})
        mesh = mesh_package(box, h_max=0.6, pads=False, substrate=False)
        f = MaxwellFEM(mesh).eigenmodes(35e9, n=1)[0].f
        tm110 = C0 / 2 * np.hypot(1 / 6e-3, 1 / 6e-3)
        self.assertLess(
            abs(f / tm110 - 1), 0.03, f"{f / 1e9:.3f} GHz vs {tm110 / 1e9:.3f}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
