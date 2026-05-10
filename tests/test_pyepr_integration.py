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
"""Tests pinning the pyEPR API surface that qiskit-metal depends on.

These tests do not require Ansys. They exercise the pyEPR symbols that
metal's analyses and renderers import at the module level — the
`Convert` math helpers, physical constants, the Pint ``ureg``, and the
``parse_units`` / ``unparse_units`` utilities. If a future pyEPR release
renames or relocates any of these, this file fails loudly and points
the integrator at the exact import to update on the metal side.
"""

import unittest

from .assertions import AssertionsMixin


class TestPyEPRConvertIntegration(unittest.TestCase, AssertionsMixin):
    """`pyEPR.calcs.convert.Convert` is used by lumped_capacitive,
    lumped_oscillator_model, and lom_core_analysis."""

    def test_convert_symbols_importable(self):
        """The three Convert methods metal calls must remain on the class."""
        from pyEPR.calcs.convert import Convert
        self.assertTrue(callable(Convert.Ic_from_Lj))
        self.assertTrue(callable(Convert.Ej_from_Lj))
        self.assertTrue(callable(Convert.Ec_from_Cs))

    def test_convert_ic_from_lj_matches_metal_call_site(self):
        """Reproduce the call shape used in lumped_capacitive.py:801 and
        lumped_oscillator_model.py:157 and assert physical correctness.

        Ic = Phi_0 / (2*pi*Lj). For Lj = 10 nH this is hbar/(2e*Lj) =
        3.291e-16 Wb / 10e-9 H = 3.291e-8 A.
        """
        from pyEPR.calcs.convert import Convert
        ic_amps = Convert.Ic_from_Lj(10.0, 'nH', 'A')
        self.assertAlmostEqualRel(ic_amps, 3.291059784754533e-08, rel_tol=1e-9)

    def test_convert_ic_from_lj_default_units(self):
        """Default units must be (nH -> nA)."""
        from pyEPR.calcs.convert import Convert
        # 10 nH -> ~32.91 nA
        ic_default = Convert.Ic_from_Lj(10.0)
        ic_explicit = Convert.Ic_from_Lj(10.0, 'nH', 'nA')
        self.assertAlmostEqualRel(ic_default, ic_explicit, rel_tol=1e-12)
        self.assertAlmostEqualRel(ic_default, 32.91059784754533, rel_tol=1e-9)

    def test_convert_ej_from_lj_matches_metal_call_site(self):
        """Reproduce lom_core_analysis.py:960 ``Convert.Ej_from_Lj(1/L)``.

        Default units (nH -> MHz). Ej/h = Phi_0^2 / (4*pi^2 * Lj * h).
        For Lj = 10 nH the textbook value is ~16346 MHz.
        """
        from pyEPR.calcs.convert import Convert
        ej_mhz = Convert.Ej_from_Lj(10.0)
        self.assertAlmostEqualRel(ej_mhz, 16346.15128067812, rel_tol=1e-9)

    def test_convert_ec_from_cs_matches_metal_call_site(self):
        """Reproduce lom_core_analysis.py:961, :1015 ``Convert.Ec_from_Cs(1/C)``.

        Default units (fF -> MHz). Ec/h = e^2 / (2*Cs*h).
        For Cs = 100 fF the textbook value is ~193.7 MHz.
        """
        from pyEPR.calcs.convert import Convert
        ec_mhz = Convert.Ec_from_Cs(100.0)
        self.assertAlmostEqualRel(ec_mhz, 193.7022932465912, rel_tol=1e-9)


class TestPyEPRConstantsIntegration(unittest.TestCase, AssertionsMixin):
    """`pyEPR.calcs.constants` is used by lom_core_analysis."""

    def test_constants_importable(self):
        """The two constants metal imports must be present."""
        from pyEPR.calcs.constants import e_el, hbar
        self.assertIsNotNone(e_el)
        self.assertIsNotNone(hbar)

    def test_constants_match_codata(self):
        """`e_el` and `hbar` should track CODATA values; metal does
        unit-conversion arithmetic with them."""
        from pyEPR.calcs.constants import e_el, hbar
        # 2019-redefined exact value of the elementary charge.
        self.assertAlmostEqualRel(e_el, 1.602176634e-19, rel_tol=1e-9)
        # CODATA 2018 reduced Planck constant.
        self.assertAlmostEqualRel(hbar, 1.054571817e-34, rel_tol=1e-7)


class TestPyEPRAnsysIntegration(unittest.TestCase, AssertionsMixin):
    """`pyEPR.ansys` exposes parse_units, unparse_units, ureg, set_property,
    HfssApp, release. Metal's renderer modules import every one of these at
    module load. If any disappears, the renderers can no longer be imported."""

    def test_top_level_symbols_importable(self):
        """The full set of `pyEPR.ansys` symbols metal imports."""
        from pyEPR.ansys import (parse_units, unparse_units, ureg,
                                 set_property, HfssApp, release)
        self.assertTrue(callable(parse_units))
        self.assertTrue(callable(unparse_units))
        self.assertTrue(callable(set_property))
        self.assertTrue(callable(HfssApp))
        self.assertTrue(callable(release))
        # ureg must be a Pint UnitRegistry instance.
        import pint
        self.assertIsInstance(ureg, pint.UnitRegistry)

    def test_parse_units_length_to_meters(self):
        """`parse_units` converts length strings to the HFSS internal unit
        (meters). Metal's `to_ansys_units` and `parse_value_hfss` rely on this."""
        from pyEPR.ansys import parse_units
        self.assertAlmostEqualRel(parse_units('1mm'), 1e-3, rel_tol=1e-12)
        self.assertAlmostEqualRel(parse_units('1um'), 1e-6, rel_tol=1e-12)
        self.assertAlmostEqualRel(parse_units('2.5 mm'), 2.5e-3, rel_tol=1e-12)

    def test_unparse_units_meters_to_mm(self):
        """`unparse_units` is the inverse: meters -> mm."""
        from pyEPR.ansys import unparse_units
        self.assertAlmostEqualRel(unparse_units(1e-3), 1.0, rel_tol=1e-12)
        self.assertAlmostEqualRel(unparse_units(2.5e-3), 2.5, rel_tol=1e-12)

    def test_ureg_can_quantify_metal_units(self):
        """Metal uses `ureg` to construct Pint quantities. Confirm the unit
        registry recognises the units metal actually uses."""
        from pyEPR.ansys import ureg
        # nH appears in lumped_elements.py and Q3D conversions
        self.assertEqual(str(ureg.Quantity(1.0, 'nH').units), 'nanohenry')
        # fF appears in capacitance handling
        self.assertEqual(str(ureg.Quantity(1.0, 'fF').units), 'femtofarad')
        # GHz appears in eigenmode setup configuration
        self.assertEqual(str(ureg.Quantity(1.0, 'GHz').units), 'gigahertz')


class TestPyEPRReportsIntegration(unittest.TestCase, AssertionsMixin):
    """`pyEPR.reports` exposes the convergence plotters used by
    analyses/simulation/eigenmode.py and renderers/renderer_ansys/q3d_renderer.py.

    The Q3D plotters are imported via private (underscore-prefixed) names:
    these are the most fragile pyEPR symbols metal depends on. If a future
    pyEPR makes them public (drops the underscore) or removes them, this
    test will fail and the metal import will need to follow."""

    def test_public_eigenmode_convergence_plotters_importable(self):
        from pyEPR.reports import (plot_convergence_f_vspass,
                                   plot_convergence_max_df,
                                   plot_convergence_maxdf_vs_sol,
                                   plot_convergence_solved_elem)
        for fn in (plot_convergence_f_vspass, plot_convergence_max_df,
                   plot_convergence_maxdf_vs_sol,
                   plot_convergence_solved_elem):
            self.assertTrue(callable(fn))

    def test_private_q3d_plotters_importable(self):
        """`q3d_renderer.py:22` reaches into pyEPR's private namespace."""
        from pyEPR.reports import (_plot_q3d_convergence_main,
                                   _plot_q3d_convergence_chi_f)
        self.assertTrue(callable(_plot_q3d_convergence_main))
        self.assertTrue(callable(_plot_q3d_convergence_chi_f))


class TestPyEPRTopLevelIntegration(unittest.TestCase, AssertionsMixin):
    """`import pyEPR as epr` is followed by `epr.ProjectInfo`,
    `epr.DistributedAnalysis`, `epr.QuantumAnalysis` in the renderers and
    analyses. Without Ansys we cannot instantiate them, but we can confirm
    the names resolve on the package."""

    def test_top_level_names_resolve(self):
        import pyEPR as epr
        for name in ('ProjectInfo', 'DistributedAnalysis', 'QuantumAnalysis'):
            self.assertTrue(hasattr(epr, name),
                            f'pyEPR no longer exposes {name} at top level')


class TestMetalParseWrapper(unittest.TestCase, AssertionsMixin):
    """`renderers/renderer_ansys/parse.py` re-exports parse/unparse helpers.

    Until this branch the file was dead-importing `pyEPR.hfss` (removed in
    pyEPR 0.9). These tests pin the module so the regression cannot recur."""

    def test_parse_module_imports(self):
        from qiskit_metal.renderers.renderer_ansys import parse  # noqa: F401

    def test_parse_value_hfss_round_trip(self):
        from qiskit_metal.renderers.renderer_ansys.parse import (
            parse_value_hfss, unparse_units)
        # 1 mm -> 1e-3 m (HFSS internal) -> 1.0 mm
        meters = parse_value_hfss('1mm')
        self.assertAlmostEqualRel(meters, 1e-3, rel_tol=1e-12)
        self.assertAlmostEqualRel(unparse_units(meters), 1.0, rel_tol=1e-12)


if __name__ == '__main__':
    unittest.main(verbosity=2)
