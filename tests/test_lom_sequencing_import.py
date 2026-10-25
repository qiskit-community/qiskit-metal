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
"""The LOM-to-Sequencing modules explain how to get ``sequencing``, and
``sequencing`` 1.2.0 is adapted to qutip 5 (#1231)."""

import importlib
import importlib.util
import sys
import unittest

import qutip

from qiskit_metal.analyses.quantization import _sequencing_compat as compat

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


class TestSequencingCompat(unittest.TestCase):
    def test_needs_patch_only_for_qutip5_and_sequencing_up_to_1_2(self):
        self.assertTrue(compat.needs_patch("5.2.2", "1.2.0"))
        self.assertTrue(compat.needs_patch("5.0.0", "1.1.4"))
        self.assertFalse(compat.needs_patch("4.7.6", "1.2.0"))
        self.assertFalse(compat.needs_patch("5.2.2", "1.3.0"))

    def test_solver_options_keep_sequencing_defaults(self):
        self.assertEqual(
            compat._solver_options(None, 0.5, True),
            {"max_step": 0.5, "store_states": True},
        )
        opts = compat._solver_options({"atol": 1e-10, "max_step": 2}, 1, False)
        self.assertEqual(opts, {"max_step": 2, "store_states": False, "atol": 1e-10})

    def test_drop_zero_operators_without_data_nnz(self):
        """The wrapped method filters zero operators itself and still honours
        ``clean=False``."""
        calls = []

        class FakeSystem:
            def H0(self, modes=None, clean=True):
                calls.append(clean)
                return [qutip.num(3), 0 * qutip.num(3), qutip.destroy(3)]

        FakeSystem.H0 = compat._drop_zero_operators(FakeSystem.H0)
        system = FakeSystem()
        self.assertEqual(len(system.H0()), 2)
        self.assertEqual(len(system.H0(clean=False)), 3)
        self.assertEqual(calls, [False, False])

    @unittest.skipUnless(
        importlib.util.find_spec("sequencing"), "sequencing is not installed"
    )
    def test_a_pi_pulse_runs_and_inverts_the_qubit(self):
        lom_extensions = importlib.import_module(
            "qiskit_metal.analyses.quantization.lom_extensions"
        )
        seq = lom_extensions.seq
        import numpy as np

        qubit = seq.Transmon("q", levels=3, kerr=-0.2)
        cavity = seq.Cavity("c", levels=4, kerr=-1e-5)
        system = seq.System("s", modes=[qubit, cavity])
        system.set_cross_kerr(qubit, cavity, chi=-2e-3)
        sequence = seq.get_sequence(system)
        qubit.rotate_x(np.pi)
        result = sequence.run(system.ground_state())
        p_e = qutip.expect(qubit.fock_dm(1), result.states[-1])
        self.assertGreater(p_e, 0.99)


if __name__ == "__main__":
    unittest.main()
