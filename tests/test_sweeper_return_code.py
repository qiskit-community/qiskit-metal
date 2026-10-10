# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""QAnalysis.run_sweep reports a failed run() instead of return code 0 (#1230)."""

import unittest

from qiskit_metal import Dict, designs
from qiskit_metal.analyses.core import QAnalysis
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket


class _Analysis(QAnalysis):
    """Minimal analysis whose run() fails for chosen option values."""

    default_setup = Dict(run=Dict())

    def __init__(self, design, fail_for=()):
        self.design = design
        self.fail_for = set(fail_for)
        super().__init__()

    def run(self, **kwargs):
        value = self.design.components["Q1"].options.pad_gap
        if value in self.fail_for:
            raise RuntimeError(f"no simulator for {value}")
        self._variables["ran_with"] = value


class TestRunSweepReturnCode(unittest.TestCase):
    def setUp(self):
        self.design = designs.DesignPlanar()
        TransmonPocket(self.design, "Q1")

    def _sweep(self, fail_for):
        a = _Analysis(self.design, fail_for)
        return a.run_sweep("Q1", "pad_gap", ["20um", "30um"], ["Q1"], [])

    def test_all_succeed_returns_0(self):
        sweeps, code = self._sweep(())
        self.assertEqual(code, 0)
        self.assertNotIn("error", sweeps["20um"])

    def test_all_fail_returns_7_with_errors(self):
        sweeps, code = self._sweep({"20um", "30um"})
        self.assertEqual(code, 7)
        for key in ("20um", "30um"):
            self.assertIn("no simulator", sweeps[key]["error"])

    def test_partial_failure_returns_7(self):
        sweeps, code = self._sweep({"30um"})
        self.assertEqual(code, 7)
        self.assertNotIn("error", sweeps["20um"])
        self.assertIn("error", sweeps["30um"])


if __name__ == "__main__":
    unittest.main()
