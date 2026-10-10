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
"""Regression tests for LOM / EPR analysis fixes that need no simulator."""

import os
import sys
import tempfile
import unittest
import unittest.mock

import numpy as np
import pandas as pd

from qiskit_metal import designs
from qiskit_metal.analyses.quantization import EPRanalysis, LOManalysis
from qiskit_metal.analyses.quantization.lumped_capacitive import (
    df_cmat_style_print,
    extract_transmon_coupled_Noscillator,
)
from qiskit_metal.analyses.simulation import EigenmodeSim, LumpedElementsSim
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket

# ground, pad1, pad2, readout (fF) -- a floating two-pad transmon.
_NAMES = ["ground_main_plane", "pad_top_Q1", "pad_bot_Q1", "readout_Q1"]
_CMAT_FF = np.array(
    [
        [300.0, -30.0, -40.0, -5.0],
        [-30.0, 110.0, -60.0, -20.0],
        [-40.0, -60.0, 120.0, -10.0],
        [-5.0, -20.0, -10.0, 60.0],
    ]
)


def _cmat_df():
    return pd.DataFrame(_CMAT_FF.copy(), index=_NAMES, columns=_NAMES)


class TestRunLomUserMatrix(unittest.TestCase):
    """run_lom() with a capacitance matrix set directly by the user."""

    def test_dataframe_only_runs(self):
        # Setting only capacitance_matrix -- what the warning tells users to
        # do -- used to raise KeyError: 0.
        a = LOManalysis()
        a.setup.freq_bus = []
        a.sim.capacitance_matrix = _cmat_df()
        result = a.run_lom()
        self.assertIsNotNone(result)
        self.assertEqual(list(a.sim.capacitance_all_passes), [1])

    def test_dataframe_only_matches_explicit_passes_in_farads(self):
        a = LOManalysis()
        a.setup.freq_bus = []
        a.sim.capacitance_matrix = _cmat_df()
        implicit = a.run_lom()

        b = LOManalysis()
        b.setup.freq_bus = []
        b.sim.capacitance_matrix = _cmat_df()
        b.sim.capacitance_all_passes = {1: _CMAT_FF * 1e-15}
        explicit = b.run_lom()

        pd.testing.assert_frame_equal(implicit, explicit)

    def test_units_attribute_is_respected(self):
        a = LOManalysis()
        a.setup.freq_bus = []
        a.sim.capacitance_matrix = _cmat_df() * 1e-3
        a.sim.units = "pF"
        a.run_lom()
        np.testing.assert_allclose(a.sim.capacitance_all_passes[1], _CMAT_FF * 1e-15)

    def test_no_matrix_warns_and_returns_none(self):
        a = LOManalysis()
        with self.assertLogs(a.logger, level="WARNING"):
            self.assertIsNone(a.run_lom())


class TestLomSizeError(unittest.TestCase):
    def test_message_states_expected_size_and_order(self):
        with self.assertRaises(ValueError) as ctx:
            extract_transmon_coupled_Noscillator(
                _CMAT_FF[:3, :3] * 1e-15, 1e-8, 2e-15, 1, [], 7.0
            )
        msg = str(ctx.exception)
        self.assertIn("got 3x3", msg)
        self.assertIn("expected 4x4", msg)
        self.assertIn("ground, pad1, pad2, readout", msg)
        self.assertIn("two-pad", msg)


class TestCmatPrintWithoutIPython(unittest.TestCase):
    def test_falls_back_to_plain_print(self):
        with unittest.mock.patch.dict(sys.modules, {"IPython.display": None}):
            with unittest.mock.patch("builtins.print") as fake_print:
                df_cmat_style_print(_cmat_df())
        fake_print.assert_called_once()
        self.assertIn("pad_top_Q1", fake_print.call_args[0][0])


class TestSaveCapacitanceMatrix(unittest.TestCase):
    def test_round_trip_with_units_header(self):
        sim = LumpedElementsSim(designs.DesignPlanar())
        sim.capacitance_matrix = _cmat_df()
        sim.units = "fF"
        with tempfile.TemporaryDirectory() as tmp:
            path = sim.save_capacitance_matrix(os.path.join(tmp, "sub", "cmat.csv"))
            self.assertTrue(path.exists())
            loaded = pd.read_csv(path, index_col=0)
        self.assertEqual(loaded.index.name, "C [fF]")
        np.testing.assert_allclose(loaded.values, _CMAT_FF)
        self.assertEqual(list(loaded.columns), _NAMES)

    def test_raises_without_matrix(self):
        with self.assertRaises(ValueError):
            LumpedElementsSim(designs.DesignPlanar()).save_capacitance_matrix(
                "unused.csv"
            )


class TestSimWithoutDesign(unittest.TestCase):
    """A simulation built without a design must not connect to a simulator."""

    def test_construction_does_not_start_the_renderer(self):
        from qiskit_metal.renderers.renderer_base.renderer_base import QRenderer

        with unittest.mock.patch.object(
            QRenderer, "start", side_effect=AssertionError("start() called")
        ):
            for cls in (LumpedElementsSim, EigenmodeSim):
                try:
                    sim = cls()
                except ImportError as exc:  # lite install: no pyEPR
                    self.skipTest(str(exc))
                self.assertIsNotNone(sim.renderer)
                self.assertFalse(sim.renderer_initialized)

    def test_unknown_renderer_returns_none(self):
        sim = LumpedElementsSim(renderer_name="no_such_renderer")
        self.assertIsNone(sim.renderer)


class TestUnlinkedJunctionWarning(unittest.TestCase):
    """EigenmodeSim warns when setup.vars.Lj cannot reach the junction."""

    def setUp(self):
        self.design = designs.DesignPlanar()
        self.q1 = TransmonPocket(self.design, "Q1")  # hfss_inductance='10nH'
        self.sim = EigenmodeSim(self.design, "hfss")
        if "hfss_inductance" not in self.design.qgeometry.tables["junction"]:
            self.skipTest("HFSS renderer not installed (lite install)")

    def test_warns_when_lj_differs_from_literal(self):
        self.sim.setup.vars.Lj = "11 nH"
        with self.assertLogs(self.sim.logger, level="WARNING") as logs:
            self.sim._warn_unlinked_junction_inductance(["Q1"])
        text = "\n".join(logs.output)
        self.assertIn("Q1.rect_jj", text)
        self.assertIn("hfss_inductance", text)

    def _assert_silent(self):
        with unittest.mock.patch.object(self.sim.logger, "warning") as warn:
            self.sim._warn_unlinked_junction_inductance(["Q1"])
        warn.assert_not_called()

    def test_silent_with_defaults(self):
        # Default vars.Lj = "10 nH" equals the default "10nH" literal.
        self._assert_silent()

    def test_silent_when_linked_to_variable(self):
        self.sim.setup.vars.Lj = "11 nH"
        self.q1.options.hfss_inductance = "Lj"
        self.q1.rebuild()
        self._assert_silent()

    def test_only_rendered_components_are_checked(self):
        self.sim.setup.vars.Lj = "11 nH"
        TransmonPocket(self.design, "Q2", options=dict(pos_x="2mm"))
        self.q1.options.hfss_inductance = "Lj"
        self.q1.rebuild()
        with unittest.mock.patch.object(self.sim.logger, "warning") as warn:
            self.sim._warn_unlinked_junction_inductance(["Q1"])
        warn.assert_not_called()


class TestLargeHilbertSpaceWarning(unittest.TestCase):
    def setUp(self):
        self.epr = EPRanalysis(designs.DesignPlanar(), "hfss")

    def test_warns_for_six_modes_at_default_truncation(self):
        self.epr.sim.setup.n_modes = 6
        with self.assertLogs(self.epr.logger, level="WARNING") as logs:
            self.epr._warn_large_hilbert_space(7)
        self.assertIn("117649 states", "\n".join(logs.output))

    def test_silent_for_small_spaces(self):
        self.epr.sim.setup.n_modes = 4
        with unittest.mock.patch.object(self.epr.logger, "warning") as warn:
            self.epr._warn_large_hilbert_space(7)
        warn.assert_not_called()


class TestRunLomQuarterWaveCorrection(unittest.TestCase):
    """setup.res_L4_corr reaches the extractor (#1210)."""

    def _run(self, corr):
        a = LOManalysis()
        a.setup.freq_bus = []
        a.setup.res_L4_corr = corr
        a.sim.capacitance_matrix = _cmat_df()
        return a.run_lom()

    def test_default_is_half_wave(self):
        self.assertIsNone(LOManalysis.default_setup.res_L4_corr)
        pd.testing.assert_frame_equal(self._run(None), self._run([0]))

    def test_quarter_wave_matches_direct_call(self):
        res = self._run([1])
        from qiskit_metal.analyses.quantization.constants import Ic_from_Lj

        direct = extract_transmon_coupled_Noscillator(
            _CMAT_FF * 1e-15,
            Ic_from_Lj(12, "nH", "A"),
            2e-15,
            1,
            [],
            7.0,
            res_L4_corr=[1],
        )
        self.assertAlmostEqual(res["gr MHz"].iloc[-1], abs(direct["gbus"][0]), places=9)
        self.assertNotAlmostEqual(
            res["gr MHz"].iloc[-1], self._run(None)["gr MHz"].iloc[-1], places=3
        )


# bus1, ground, pad1, pad2, readout (fF): one readout and one bus (#1222)
_CMAT5_FF = np.array(
    [
        [60.0, -40.0, -8.0, -1.0, -0.5],
        [-40.0, 300.0, -30.0, -40.0, -5.0],
        [-8.0, -30.0, 110.0, -60.0, -20.0],
        [-1.0, -40.0, -60.0, 120.0, -10.0],
        [-0.5, -5.0, -20.0, -10.0, 60.0],
    ]
)
_IC = 2.067833848e-15 / (2 * np.pi * 12e-9)


class TestNoscillatorBusBusAndPurcell(unittest.TestCase):
    """Bus-bus coupling formula and Purcell T1 inputs (#1222)."""

    def _extract(self, **kw):
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            hd = extract_transmon_coupled_Noscillator(
                _CMAT5_FF * 1e-15, _IC, 2e-15, 2, [6.0], 7.0, print_info=True, **kw
            )
        return hd, buf.getvalue()

    def test_bus_bus_coupling_is_lc_resonator_value(self):
        import re

        _, out = self._extract()
        printed = float(re.search(r"gbus1_2 (\S+) \[MHz\]", out).group(1))
        # Effective capacitances, formed as in the extractor: buses at
        # [readout, bus1] = matrix indices [4, 0], pads [2, 3], ground 1.
        C = _CMAT5_FF * 1e-15
        wr = 2 * np.pi * np.array([7.0, 6.0]) * 1e9
        Cr = 0.5 * np.pi / (wr * 50)
        b, q = [4, 0], [2, 3]
        Cbus = np.array([[-C[i, j] for j in b] for i in q])
        C1S = -C[2, 1] + Cbus[0].sum()
        C2S = -C[3, 1] + Cbus[1].sum()
        c12 = -C[4, 0]
        tCS = [
            Cr[i] - Cbus[:, i].sum() ** 2 / (C1S + C2S) + Cbus[:, i].sum() + c12
            for i in range(2)
        ]
        tC12 = c12 + Cbus[:, 0].sum() * Cbus[:, 1].sum() / (C1S + C2S)
        # two capacitively coupled LC resonators
        g = 0.5 * tC12 / np.sqrt(tCS[0] * tCS[1]) * np.sqrt(wr[0] * wr[1])
        self.assertAlmostEqual(printed, g / (2 * np.pi * 1e6), places=5)

    def test_purcell_returned_only_with_q_res(self):
        hd, out = self._extract()
        self.assertNotIn("T1", hd)
        self.assertIn("placeholder Q", out)

        q_res = [2e4, 3e5]
        hd, _ = self._extract(Q_res=q_res)
        wq = 2 * np.pi * hd["fQ"] * 1e9
        wr = 2 * np.pi * np.array([7.0, 6.0]) * 1e9
        g = 2 * np.pi * np.asarray(hd["gbus"]) * 1e6
        kappa = wr / np.array(q_res)
        koch = (wq - wr) ** 2 / (kappa * g**2)  # Koch et al. Eq. 4.7
        expected = koch * ((wq + wr) / (2 * wq)) ** 2
        np.testing.assert_allclose(hd["T1bus"], expected, rtol=1e-10)
        self.assertAlmostEqual(hd["T1"], 1 / np.sum(1 / expected), places=12)

    def test_q_res_length_checked(self):
        with self.assertRaises(ValueError):
            self._extract(Q_res=[1e4])

    def test_z0_default_unchanged(self):
        a, _ = self._extract()
        b, _ = self._extract(Z0=50.0)
        c, _ = self._extract(Z0=25.0)
        np.testing.assert_array_equal(a["gbus"], b["gbus"])
        self.assertFalse(np.allclose(a["gbus"], c["gbus"]))

    def test_chargeline_t1_z0(self):
        from qiskit_metal.analyses.quantization.lumped_capacitive import (
            chargeline_T1,
        )

        t50 = chargeline_T1(0.1e-15, 80e-15, 5e9)
        self.assertEqual(t50, chargeline_T1(0.1e-15, 80e-15, 5e9, Z0=50.0))
        self.assertAlmostEqual(chargeline_T1(0.1e-15, 80e-15, 5e9, Z0=25.0) / t50, 2.0)


class TestLevelsVsNgHermitianSolver(unittest.TestCase):
    """levels_vs_ng_real_units uses a Hermitian eigensolver (#1210)."""

    def test_real_results_no_complex_warning(self):
        import warnings

        from qiskit_metal.analyses.quantization.lumped_capacitive import (
            levels_vs_ng_real_units,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            fq, alpha, disp, tphi = levels_vs_ng_real_units(65.0, 27.4, N=11)
        for v in (fq, alpha, disp, tphi):
            self.assertFalse(np.iscomplexobj(v))
        # Koch et al. (2007): f01 ~ sqrt(8 EJ EC) - EC, alpha ~ -EC
        self.assertGreater(fq, 4.0)
        self.assertLess(alpha, 0.0)


class TestHamiltonianResultsAnnotation(unittest.TestCase):
    def test_return_annotation_is_dict(self):
        import inspect

        from qiskit_metal.analyses.quantization.lom_core_analysis import (
            CompositeSystem,
        )

        sig = inspect.signature(CompositeSystem.hamiltonian_results)
        self.assertIs(sig.return_annotation, dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)
