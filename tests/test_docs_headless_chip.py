# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""The scripting guide's example (docs/examples/headless_chip.py) keeps working."""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from qiskit_metal.validation import DesignRuleViolation, validate

SCRIPT = Path(__file__).resolve().parents[1] / "docs" / "examples" / "headless_chip.py"


def _load():
    spec = importlib.util.spec_from_file_location("headless_chip", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(SCRIPT.exists(), "docs/examples is not in this checkout")
class TestHeadlessChipExample(unittest.TestCase):
    def test_design_passes_the_rules_and_exports(self):
        example = _load()
        with tempfile.TemporaryDirectory() as tmp:
            out = example.main(tmp)
            self.assertTrue((Path(out) / "chip.gds").stat().st_size > 0)
            self.assertTrue((Path(out) / "chip.png").stat().st_size > 0)

    def test_geometry_and_gds_are_repeatable(self):
        example = _load()
        self.assertEqual(
            example.fingerprint(example.build()), example.fingerprint(example.build())
        )
        with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
            with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
                gds_a = example.main(a) / "chip.gds"
                gds_b = example.main(b) / "chip.gds"
                self.assertEqual(gds_a.read_bytes(), gds_b.read_bytes())

    def test_a_launchpad_off_the_chip_fails_the_check(self):
        example = _load()
        design = example.build()
        design.components["LP1"].options.pos_x = "3.5mm"
        design.rebuild()
        result = validate(design)
        self.assertFalse(result.ok)
        self.assertIn("chip-bounds", {f.rule for f in result.errors})
        with self.assertRaises(DesignRuleViolation):
            validate(design, strict=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
