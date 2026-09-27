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


if __name__ == "__main__":
    unittest.main(verbosity=2)
