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

"""Regression tests for ``LOManalysis.run_lom()`` (issue #1125).

``run_lom()`` post-processes the per-pass Hamiltonian dicts into a DataFrame
and reads the first (readout) element of the ``chi_in_MHz`` / ``gbus``
sequences. Their concrete type shifted from a pandas ``Series`` to a
``numpy.ndarray`` with newer numpy/pandas, so the old ``.iloc[0]`` accessor
raised ``AttributeError: 'numpy.ndarray' object has no attribute 'iloc'``.

These tests drive the full ``run_lom()`` path from the checked-in sample
capacitance matrix — no Q3D/HFSS simulator required — and would fail on the
pre-fix code. ``LOManalysis(design)`` with ``renderer_name=None`` leaves
``sim`` as a plain ``Dict``, so the capacitance matrix can be injected directly
and the whole flow runs on a lite (pyaedt-free) install.
"""

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from qiskit_metal import designs, Dict
from qiskit_metal.analyses.quantization import LOManalysis
from qiskit_metal.analyses.quantization import lumped_capacitive as lc

TEST_DATA = Path(__file__).parent / "test_data"


def _sample_matrix() -> pd.DataFrame:
    """The checked-in single-transmon Q3D capacitance matrix as a DataFrame."""
    df, _units, _, _ = lc.load_q3d_capacitance_matrix(
        str(TEST_DATA / "q3d_example.txt"), _disp=False
    )
    return df


def _make_lom(all_passes: dict) -> LOManalysis:
    """LOManalysis with the sample matrix injected (no renderer / simulator)."""
    design = designs.DesignPlanar()
    lom = LOManalysis(design)  # renderer_name=None -> sim is a plain Dict
    df = _sample_matrix()
    lom.sim.capacitance_matrix = df
    lom.sim.capacitance_all_passes = all_passes
    lom.setup.junctions = Dict(Lj=12.31, Cj=2)
    lom.setup.freq_readout = 7.0
    lom.setup.freq_bus = [6.0, 6.2]
    return lom


class TestRunLom(unittest.TestCase):
    """End-to-end ``LOManalysis.run_lom()`` over the sample capacitance matrix."""

    def test_run_lom_multi_pass(self):
        """Two passes -> a DataFrame with finite readout chi/g columns."""
        df = _sample_matrix()
        out = _make_lom({1: df.values, 2: df.values}).run_lom()

        self.assertIsInstance(out, pd.DataFrame)
        self.assertEqual(len(out), 2)
        for col in ("χr MHz", "gr MHz", "EC", "EJ"):
            self.assertIn(col, out.columns)
        self.assertTrue(np.isfinite(out["χr MHz"].astype(float)).all())
        self.assertTrue(np.isfinite(out["gr MHz"].astype(float)).all())
        # Stable properties of this specific matrix (generous tolerances):
        self.assertAlmostEqual(float(out["gr MHz"].iloc[0]), 108.6, delta=1.0)
        self.assertGreater(float(out["χr MHz"].iloc[0]), 0.0)

    def test_run_lom_single_pass(self):
        """A single explicit pass returns one row with the readout columns."""
        df = _sample_matrix()
        out = _make_lom({1: df.values}).run_lom()
        self.assertEqual(len(out), 1)
        self.assertIn("χr MHz", out.columns)
        self.assertIn("gr MHz", out.columns)

    def test_run_lom_handles_ndarray_chi_gbus(self):
        """The exact #1125 failure mode: ndarray chi/gbus must not raise."""
        df = _sample_matrix()
        lom = _make_lom({1: df.values})
        try:
            lom.run_lom()
        except AttributeError as err:  # pragma: no cover - explicit regression guard
            self.fail(f"run_lom() raised AttributeError on ndarray chi/gbus: {err}")


if __name__ == "__main__":
    unittest.main()
