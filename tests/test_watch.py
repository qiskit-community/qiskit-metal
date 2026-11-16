# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""``python -m qiskit_metal.watch`` re-runs a design script and reports."""

import os
import tempfile
import time
import unittest
from pathlib import Path

from qiskit_metal.watch import run_once, watch

GOOD = """
from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
design = designs.DesignPlanar()
TransmonPocket(design, "Q1")
"""


class TestWatch(unittest.TestCase):
    def test_run_once_renders_checks_and_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "chip.py"
            script.write_text(GOOD)
            res = run_once(script, out_dir=Path(tmp) / "out", gds=True)
            self.assertTrue(res["ok"])
            self.assertIn("Design rules", res["report"])
            names = {p.name for p in res["files"]}
            self.assertEqual(names, {"design.png", "design.gds"})
            for p in res["files"]:
                self.assertGreater(p.stat().st_size, 0)

    def test_an_error_in_the_script_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "chip.py"
            script.write_text("raise ValueError('typo')\n")
            res = run_once(script, out_dir=Path(tmp) / "out")
            self.assertFalse(res["ok"])
            self.assertIn("typo", res["error"])

    def test_a_script_without_a_design_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "chip.py"
            script.write_text("x = 1\n")
            res = run_once(script, out_dir=Path(tmp) / "out")
            self.assertIn("did not leave a QDesign", res["error"])

    def test_watch_reruns_when_the_file_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "chip.py"
            script.write_text(GOOD)
            self.assertEqual(
                watch(script, interval=0.01, max_runs=1, out_dir=Path(tmp) / "out"), 1
            )
            first = (Path(tmp) / "out" / "design.png").stat().st_mtime_ns
            time.sleep(0.05)
            script.write_text(GOOD + "\n# edited\n")
            os.utime(script, (time.time() + 5, time.time() + 5))
            self.assertEqual(
                watch(script, interval=0.01, max_runs=1, out_dir=Path(tmp) / "out"), 1
            )
            self.assertGreaterEqual(
                (Path(tmp) / "out" / "design.png").stat().st_mtime_ns, first
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
