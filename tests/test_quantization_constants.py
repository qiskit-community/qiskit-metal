"""Physics-meaning validation for ``analyses/quantization/constants.py``.

These tests would have caught the near-disaster from the lite-flip PR
where ``phi0``'s meaning almost got swapped from the **reduced**
flux quantum (ℏ/2e) to the **full** flux quantum (h/2e) — a factor-
of-2π difference that would have silently broken every junction
calculation downstream.

The point of this file isn't to test that ``transmon_props`` or
``LOManalysis.run_lom`` produce specific numbers (those tests exist
elsewhere with hardcoded expected values). It's to assert that each
named constant **means what its name says**, and that the vendored
``Ic_from_Lj`` / ``Ej_from_Lj`` / ``Ec_from_Cs`` helpers compute the
textbook quantities they claim to.

Cross-checks are run at a relative tolerance large enough to absorb
the gap between metal's CODATA-2014-rounded constants and SI 2019
exact values (~10⁻⁴), while still being orders of magnitude tighter
than any units-swap or factor-of-2π mistake would survive.
"""

from __future__ import annotations

import math
import unittest

from qiskit_metal.analyses.quantization import constants as C


# SI 2019 exact reference values (these are the defining constants, no
# uncertainty). Tests below assert ``constants.py`` matches to ~1e-4
# — well below any units-swap or off-by-2π mistake.
_E_REF = 1.602176634e-19  # elementary charge, C
_H_REF = 6.62607015e-34  # Planck, J·s
_HBAR_REF = _H_REF / (2 * math.pi)  # reduced Planck
_PHI_FULL_REF = _H_REF / (2 * _E_REF)  # full flux quantum, h/(2e), Wb
_PHI_REDUCED_REF = _HBAR_REF / (2 * _E_REF)  # reduced flux quantum, ℏ/(2e), Wb


class TestPhysicalConstantsMeaning(unittest.TestCase):
    """Each named constant points at the right physical quantity."""

    REL_TOL = 1e-3  # 0.1%: tight enough to catch factor-of-2π mistakes,
    # loose enough to absorb CODATA-2014 vs SI-2019 rounding.

    def assertCloseRel(self, actual, expected, rel_tol=None, msg=""):
        rel_tol = rel_tol if rel_tol is not None else self.REL_TOL
        rel_err = abs(actual - expected) / abs(expected)
        self.assertLess(
            rel_err,
            rel_tol,
            msg=f"{msg}: |{actual} - {expected}| / |{expected}| = {rel_err:.2e}, "
            f"exceeds rel_tol {rel_tol:.2e}",
        )

    def test_e_is_elementary_charge(self):
        """``e`` should be the elementary charge (~1.6e-19 C), not
        Euler's number (~2.72) or anything else."""
        self.assertCloseRel(C.e, _E_REF, msg="C.e")
        # And not Euler's number — a coarse sanity check.
        self.assertNotAlmostEqual(C.e, math.e, places=10)

    def test_h_is_planck(self):
        self.assertCloseRel(C.h, _H_REF, msg="C.h")

    def test_hbar_is_h_over_2pi(self):
        """``hbar`` must equal ``h / (2π)`` to within the precision
        of ``h`` itself."""
        self.assertCloseRel(C.hbar, _HBAR_REF, msg="C.hbar (vs ref ℏ)")
        self.assertCloseRel(
            C.hbar, C.h / (2 * math.pi), rel_tol=1e-6, msg="C.hbar (vs C.h/(2π))"
        )

    def test_phinot_is_full_flux_quantum(self):
        """``phinot`` (full flux quantum) must be h/(2e), about
        2.07e-15 Wb. Not the reduced form."""
        self.assertCloseRel(C.phinot, _PHI_FULL_REF, msg="C.phinot")
        # And definitely not 2π times smaller (which would be the
        # reduced flux quantum):
        self.assertGreater(C.phinot, 1e-15)
        self.assertLess(C.phinot, 1e-14)

    def test_phi0_is_reduced_flux_quantum(self):
        """``phi0`` must be the **reduced** flux quantum ℏ/(2e),
        about 3.29e-16 Wb. The downstream physics in
        ``lumped_capacitive.transmon_props`` and the vendored
        ``Ic_from_Lj`` rely on this meaning — swapping it for the
        full flux quantum would silently break every junction
        calculation by a factor of 2π."""
        self.assertCloseRel(C.phi0, _PHI_REDUCED_REF, msg="C.phi0")
        # Sanity bounds — reduced flux quantum is ~3e-16 Wb.
        self.assertGreater(C.phi0, 1e-16)
        self.assertLess(C.phi0, 1e-15)
        # And it must be smaller than phinot by a factor of ~2π,
        # not the same, not larger:
        ratio = C.phinot / C.phi0
        self.assertCloseRel(ratio, 2 * math.pi, rel_tol=1e-6, msg="phinot / phi0")


class TestVendoredJosephsonHelpers(unittest.TestCase):
    """The ``Ic_from_Lj`` / ``Ej_from_Lj`` / ``Ec_from_Cs`` helpers
    compute the textbook Josephson quantities and respect units.

    These mirror ``pyEPR.calcs.convert.Convert``. Vendored here so the
    analyses path doesn't carry a runtime pyEPR dependency.
    """

    REL_TOL = 1e-3

    def assertCloseRel(self, actual, expected, msg=""):
        rel_err = abs(actual - expected) / abs(expected)
        self.assertLess(
            rel_err,
            self.REL_TOL,
            msg=f"{msg}: rel_err {rel_err:.2e} > {self.REL_TOL}",
        )

    def test_Ic_from_Lj_textbook(self):
        """Ic = Φ₀_R / Lj. For Lj = 10 nH this is ~3.29e-8 A."""
        # Default units: nH → A.
        ic = C.Ic_from_Lj(10.0)
        expected = C.phi0 / 10e-9  # nH → H
        self.assertCloseRel(ic, expected, msg="Ic_from_Lj(10 nH)")

    def test_Ic_from_Lj_unit_conversion(self):
        """Passing Lj in nH should produce numerically the same
        result as passing in H (after the units flag handles the
        conversion)."""
        ic_nH = C.Ic_from_Lj(10.0, "nH", "A")
        ic_H = C.Ic_from_Lj(10e-9, "H", "A")
        self.assertCloseRel(ic_H, ic_nH, msg="Ic_from_Lj nH vs H input")
        # And output in nA should be 1e9 × output in A:
        ic_nA = C.Ic_from_Lj(10.0, "nH", "nA")
        self.assertCloseRel(ic_nA, ic_nH * 1e9, msg="Ic_from_Lj A vs nA output")

    def test_Ej_from_Lj_textbook(self):
        """Ej = Φ₀_R² / Lj (Joules); Ej_Hz = Ej / h. For Lj = 12 nH
        this is ~13.6 GHz."""
        ej_mhz = C.Ej_from_Lj(12.0)  # default nH → MHz
        expected_J = C.phi0**2 / 12e-9
        expected_mhz = expected_J / C.h / 1e6
        self.assertCloseRel(ej_mhz, expected_mhz, msg="Ej_from_Lj(12 nH)")
        # And in physically sane range — should be ~10 GHz scale:
        self.assertGreater(ej_mhz, 1e3)  # > 1 GHz
        self.assertLess(ej_mhz, 1e5)  # < 100 GHz

    def test_Ec_from_Cs_textbook(self):
        """Ec = e²/(2 Cs) (Joules); Ec_Hz = Ec / h. For Cs = 80 fF
        this is ~240 MHz."""
        ec_mhz = C.Ec_from_Cs(80.0)  # default fF → MHz
        expected_J = C.e**2 / (2 * 80e-15)
        expected_mhz = expected_J / C.h / 1e6
        self.assertCloseRel(ec_mhz, expected_mhz, msg="Ec_from_Cs(80 fF)")
        # Typical transmon Ec is ~100-300 MHz — sanity bounds:
        self.assertGreater(ec_mhz, 10)
        self.assertLess(ec_mhz, 10_000)

    def test_unknown_unit_raises(self):
        """Bad units should raise ValueError, not silently produce
        garbage numbers."""
        with self.assertRaises(ValueError):
            C.Ic_from_Lj(10.0, "Henrys", "A")  # typo
        with self.assertRaises(ValueError):
            C.Ec_from_Cs(80.0, "fF", "Joules")  # not a frequency

    def test_no_pyEPR_required(self):
        """The vendored helpers must work in an environment where
        pyEPR is not importable. This is the whole point of the
        vendor — the analyses path is now independent of pyEPR."""
        import sys

        # Snapshot any existing pyEPR import so we don't leak across tests.
        saved = {k: v for k, v in sys.modules.items() if k.startswith("pyEPR")}
        try:
            for k in list(sys.modules):
                if k.startswith("pyEPR"):
                    del sys.modules[k]

            class _BlockpyEPR:
                def find_spec(self, name, path, target=None):
                    if name == "pyEPR" or name.startswith("pyEPR."):
                        raise ImportError(f"BLOCKED: {name}")
                    return None

            blocker = _BlockpyEPR()
            sys.meta_path.insert(0, blocker)
            try:
                # If anything in constants.py touched pyEPR transitively,
                # this would raise. It should not.
                result = C.Ic_from_Lj(10.0)
                self.assertGreater(result, 0)
            finally:
                sys.meta_path.remove(blocker)
        finally:
            sys.modules.update(saved)


if __name__ == "__main__":
    unittest.main()
