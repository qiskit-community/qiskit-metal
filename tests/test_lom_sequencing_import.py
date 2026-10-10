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
"""The LOM-to-Sequencing modules explain how to get ``sequencing`` (#1231)."""

import importlib
import sys
import unittest

_MISSING = object()
_MODULES = (
    "qiskit_metal.analyses.quantization.lom_extensions",
    "qiskit_metal.analyses.quantization.lom_time_evolution_sim",
)


class TestSequencingMissing(unittest.TestCase):
    def test_import_without_sequencing_names_the_package(self):
        """Without ``sequencing`` both modules raise an ImportError that says
        what to install, not a bare ModuleNotFoundError."""
        # Import the dependencies first: only the two modules under test may
        # be (re)imported while ``sequencing`` is hidden.
        importlib.import_module("qiskit_metal.analyses.quantization.lom_core_analysis")
        for name in _MODULES:
            with self.subTest(module=name):
                saved = {m: sys.modules.pop(m) for m in _MODULES if m in sys.modules}
                saved_seq = sys.modules.get("sequencing", _MISSING)
                # ``None`` in sys.modules makes ``import sequencing`` raise
                # ImportError whether or not it is installed.
                sys.modules["sequencing"] = None
                try:
                    with self.assertRaises(ImportError) as ctx:
                        importlib.import_module(name)
                finally:
                    for m in _MODULES:
                        sys.modules.pop(m, None)
                    sys.modules.update(saved)
                    if saved_seq is _MISSING:
                        sys.modules.pop("sequencing", None)
                    else:
                        sys.modules["sequencing"] = saved_seq
                message = str(ctx.exception)
                self.assertIn("pip install sequencing", message)
                self.assertIn("qutip", message)


if __name__ == "__main__":
    unittest.main()
