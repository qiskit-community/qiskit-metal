# This code is part of Quantum Metal.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""LOM 2.0 end to end: capacitance matrix -> Cell -> CompositeSystem -> H.

Nothing covered hamiltonian_results(), so two scqubits incompatibilities went
unnoticed: scqubits 4.1 (what macOS resolves) uses ``np.float_``, gone in
numpy 2, and scqubits 4.3.1 rejects the sparse arrays qutip 5.3 returns. See
``_scqubits_compat``. Tutorial 4.19 runs the same steps.
"""

import sys
import unittest

import numpy as np
import pandas as pd
import scqubits as scq
from scipy.constants import speed_of_light

from qiskit_metal.analyses.quantization.lom_core_analysis import (
    Cell,
    CompositeSystem,
    Subsystem,
)

# Maxwell capacitance matrix in fF: a floating two-pad transmon and one
# readout pad; the last row is ground.
_NAMES = ["pad_top", "pad_bot", "readout_pad", "ground_plane"]
_CMAT_FF = np.array(
    [
        [100.0, -30.0, -1.0, -69.0],
        [-30.0, 100.0, -8.0, -62.0],
        [-1.0, -8.0, 50.0, -41.0],
        [-69.0, -62.0, -41.0, 300.0],
    ]
)
_LJ_NH = 12.0


def _system(readout_opts=None):
    cell = Cell(
        dict(
            node_rename={"readout_pad": "readout"},
            cap_mat=pd.DataFrame(_CMAT_FF, index=_NAMES, columns=_NAMES),
            ind_dict={("pad_top", "pad_bot"): _LJ_NH},
            jj_dict={("pad_top", "pad_bot"): "j1"},
            cj_dict={("pad_top", "pad_bot"): 2},
        )
    )
    qubit = Subsystem(name="qubit", sys_type="TRANSMON", nodes=["j1"])
    readout = Subsystem(
        name="readout",
        sys_type="TL_RESONATOR",
        nodes=["readout"],
        q_opts=dict(
            f_res=7.0, Z0=50, vp=0.404314 * speed_of_light, **(readout_opts or {})
        ),
    )
    system = CompositeSystem(
        subsystems=[qubit, readout],
        cells=[cell],
        grd_node="ground_plane",
        nodes_force_keep=["readout"],
    )
    return system, qubit


class TestHamiltonianResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.system, cls.qubit = _system()
        space = cls.system.add_interaction()
        cls.results = cls.system.hamiltonian_results(space, print_info=False)

    def test_qubit_matches_the_bare_transmon(self):
        """The readout only dresses the qubit: a few MHz at g/2pi ~ 45 MHz."""
        params = self.qubit.h_params["j1"]  # EJ, EC in MHz
        bare = scq.Transmon(EJ=params["EJ"], EC=params["EC"], ng=0, ncut=30)
        e0, e1, e2 = bare.eigenvals(evals_count=3)
        f_q = self.results["fQ_in_Ghz"]["qubit"] * 1e3
        alpha = self.results["chi_in_MHz"].to_dataframe().loc["qubit", "qubit"]
        self.assertAlmostEqual(f_q, e1 - e0, delta=5)
        self.assertAlmostEqual(alpha, e2 - 2 * e1 + e0, delta=5)

    def test_readout_stays_near_its_bare_frequency(self):
        self.assertAlmostEqual(self.results["fQ_in_Ghz"]["readout"], 7.0, delta=0.1)

    def test_coupling_is_symmetric_and_nonzero(self):
        g = self.system.compute_gs().to_dataframe()
        self.assertAlmostEqual(g.loc["j1", "readout"], g.loc["readout", "j1"])
        self.assertGreater(abs(g.loc["j1", "readout"]), 1.0)  # MHz


class TestResonatorLevels(unittest.TestCase):
    """A resonator's self-Kerr needs more than three levels to converge."""

    def _self_kerr(self, readout_opts=None):
        system, _ = _system(readout_opts)
        space = system.add_interaction()
        results = system.hamiltonian_results(space, print_info=False)
        dims = [s.truncated_dim for s in system.quantum_subsystems]
        return results["chi_in_MHz"].to_dataframe().loc["readout", "readout"], dims

    def test_small_system_gets_five_levels_and_a_converged_self_kerr(self):
        kerr, dims = self._self_kerr()
        self.assertEqual(dims[1], 5)
        # K ~ alpha (g/Delta)^4 ~ 1e-4 MHz here; three levels gave +0.57 MHz.
        self.assertLess(abs(kerr), 0.01)

    def test_explicit_truncated_dim_is_kept(self):
        _, dims = self._self_kerr(dict(truncated_dim=3))
        self.assertEqual(dims[1], 3)

    def test_large_system_keeps_three_levels_and_warns(self):
        names = ["pad_top", "pad_bot"] + [f"r{k}" for k in range(6)] + ["ground_plane"]
        n = len(names)
        cmat = np.zeros((n, n))
        for k in range(2, n - 1):
            cmat[k, k], cmat[k, 1], cmat[1, k], cmat[k, -1] = 50.0, -5.0, -5.0, -45.0
        cmat[0, 0], cmat[1, 1], cmat[0, 1], cmat[1, 0] = 100.0, 130.0, -30.0, -30.0
        cmat[0, -1] = cmat[-1, 0] = -70.0
        cmat[1, -1] = cmat[-1, 1] = -70.0
        cmat[-1, -1] = 300.0
        cell = Cell(
            dict(
                node_rename={},
                cap_mat=pd.DataFrame(cmat, index=names, columns=names),
                ind_dict={("pad_top", "pad_bot"): _LJ_NH},
                jj_dict={("pad_top", "pad_bot"): "j1"},
                cj_dict={("pad_top", "pad_bot"): 2},
            )
        )
        lines = [
            Subsystem(
                name=f"r{k}",
                sys_type="TL_RESONATOR",
                nodes=[f"r{k}"],
                q_opts=dict(f_res=6.0 + 0.1 * k, Z0=50, vp=0.404314 * speed_of_light),
            )
            for k in range(6)
        ]
        qubit = Subsystem(name="qubit", sys_type="TRANSMON", nodes=["j1"])
        system = CompositeSystem(
            subsystems=[qubit, *lines],
            cells=[cell],
            grd_node="ground_plane",
            nodes_force_keep=[f"r{k}" for k in range(6)],
        )
        with self.assertLogs("metal", level="WARNING") as logs:
            system.create_hilbertspace()
        self.assertEqual(
            [s.truncated_dim for s in system.quantum_subsystems][1:], [3] * 6
        )
        self.assertIn("not converged", "\n".join(logs.output))


class TestScqubitsCompat(unittest.TestCase):
    def test_converter_returns_a_matrix(self):
        """What scqubits' type check needs, whichever qutip is installed."""
        import qutip
        import scipy.sparse as sp
        from scqubits.utils import misc, spectrum_utils

        for module in (misc, spectrum_utils):
            converted = module.Qobj_to_scipy_csc_matrix(qutip.num(3))
            self.assertTrue(sp.isspmatrix_csc(converted), type(converted))

    def test_bare_hilbert_space(self):
        """The failing scqubits call itself, without any Metal objects."""
        transmon = scq.Transmon(EJ=10.0, EC=0.3, ng=0.0, ncut=10, truncated_dim=3)
        oscillator = scq.Oscillator(E_osc=5.0, truncated_dim=3)
        space = scq.HilbertSpace([transmon, oscillator])
        self.assertEqual(space.hamiltonian().shape, (9, 9))


class TestImportSideEffects(unittest.TestCase):
    def test_h5py_is_not_replaced(self):
        """Importing LOM must not swap a dummy into sys.modules['h5py']."""
        module = sys.modules.get("h5py")
        if module is not None:
            self.assertTrue(hasattr(module, "File"), module)


if __name__ == "__main__":
    unittest.main()
