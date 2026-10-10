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
"""Tests for ``analyze_loaded_tl`` (LOM 2.0 transmission-line resonator)
against closed-form transmission-line results."""

import unittest

import numpy as np

from qiskit_metal.analyses.quantization.lom_core_analysis import analyze_loaded_tl

_VP = 299792458.0 / np.sqrt(6.065)


class TestLoadedTLModeLength(unittest.TestCase):
    """The returned length is that of the fundamental mode."""

    def test_open_end_is_loaded_half_wave(self):
        # Open far end, capacitor C at z = 0: Y_stub + jwC = 0 with
        # Y_stub = j tan(kL) / Z0  ->  kL = pi - arctan(w Z0 C).
        fr, Z0, C = 7000.0, 51.6, 54.9
        *_, L = analyze_loaded_tl(fr, _VP, Z0, {"Q": C}, shorted=False)
        w = 2 * np.pi * fr * 1e6
        k = w / _VP
        expected = (np.pi - np.arctan(w * Z0 * C * 1e-15)) / k
        self.assertAlmostEqual(L / expected, 1.0, places=9)

    def test_shorted_end_is_loaded_quarter_wave(self):
        # Shorted far end: Y_stub = 1 / (j Z0 tan(kL))  ->  tan(kL) = 1/(w Z0 C).
        # Used to return the 3*lambda/4 mode (#1206).
        fr, Z0, C = 7000.0, 51.6, 54.9
        *_, L = analyze_loaded_tl(fr, _VP, Z0, {"Q": C}, shorted=True)
        w = 2 * np.pi * fr * 1e6
        k = w / _VP
        expected = np.arctan(1 / (w * Z0 * C * 1e-15)) / k
        self.assertAlmostEqual(L / expected, 1.0, places=9)
        self.assertLess(L, _VP / (fr * 1e6) / 4)

    def test_shorted_unloaded_limit_is_quarter_wave(self):
        fr = 7000.0
        *_, L = analyze_loaded_tl(fr, _VP, 50.0, {"Q": 1e-9}, shorted=True)
        self.assertAlmostEqual(L / (_VP / (fr * 1e6) / 4), 1.0, places=6)

    def test_heavily_loaded_two_ends_is_fundamental(self):
        # With phi_0 + phi_L > pi/2 the old arctan form jumped to the next
        # mode. Check the ABCD resonance condition Y_in(0) + jwC0 = 0 with
        # 0 < kL < pi.
        fr, Z0 = 6000.0, 50.0
        for c0, cl in ((20.0, 60.0), (400.0, 400.0), (600.0, 600.0), (900.0, 100.0)):
            with self.subTest(c0=c0, cl=cl):
                *_, L = analyze_loaded_tl(fr, _VP, Z0, {"a": c0, "b": cl})
                w = 2 * np.pi * fr * 1e6
                kL = w / _VP * L
                self.assertGreater(kL, 0)
                self.assertLess(kL, np.pi)
                y0, yl = 1 / Z0, 1j * w * cl * 1e-15
                t = np.tan(kL)
                y_in = y0 * (yl + 1j * y0 * t) / (y0 + 1j * yl * t)
                self.assertLess(abs(y_in + 1j * w * c0 * 1e-15) / y0, 1e-9)


def _q_zpf_shorted_stub(fr, vp, Z0, C):
    """Independent Q_zpf for a capacitor C [F] loading a shorted stub:
    u(z) = sin(k (L - z)), tan(kL) = 1 / (w Z0 C), Eq. 19-20 of
    arXiv:2103.10344 with the line integral done numerically."""
    from scipy.integrate import quad

    # same hbar as the code under test, so only the physics is compared
    from qiskit_metal.analyses.quantization.constants import hbar

    w = 2 * np.pi * fr * 1e6
    k = w / vp
    L = np.arctan(1 / (w * Z0 * C)) / k
    c = 1 / (Z0 * vp)
    u0 = np.sin(k * L)
    line = quad(lambda z: np.sin(k * (L - z)) ** 2, 0, L, epsabs=0, epsrel=1e-13)[0]
    p = C * u0**2 / (C * u0**2 + c * line)
    return np.sqrt(hbar * w / 2 * C * p)


class TestLoadedTLShortedEnd(unittest.TestCase):
    """A shorted end is treated exactly (#1233)."""

    def test_q_zpf_matches_closed_form(self):
        for C in (20.0, 54.9, 300.0):
            with self.subTest(C=C):
                q, *_ = analyze_loaded_tl(7000.0, _VP, 51.6, {"Q": C}, shorted=True)
                ref = _q_zpf_shorted_stub(7000.0, _VP, 51.6, C * 1e-15)
                self.assertAlmostEqual(q["Q"] / ref, 1.0, places=11)

    def test_shorted_end_has_no_charge_fluctuation(self):
        q, phi, *_ = analyze_loaded_tl(6000.0, _VP, 50.0, {"Q": 50.0}, shorted=True)
        self.assertEqual(q["_cl"], 0.0)
        self.assertEqual(phi["_cl"], np.inf)

    def test_q_zpf_is_smooth_in_frequency(self):
        fs = np.linspace(6000.0, 6000.001, 41)  # MHz, 1 kHz span
        q = np.array(
            [
                analyze_loaded_tl(f, _VP, 50.0, {"Q": 50.0}, shorted=True)[0]["Q"]
                for f in fs
            ]
        )
        x = fs - fs[0]
        resid = q - np.polyval(np.polyfit(x, q, 2), x)
        self.assertLess(np.max(np.abs(resid)) / q[0], 1e-10)


def _ladder_end_charges(L, vp, Z0, C0, CL, N=4000):
    """Signed charge ZPF on the two end capacitors [F] of an N-section LC
    ladder of length L, fundamental mode, normalised so that the z = 0 end
    is positive. Independent of analyze_loaded_tl."""
    from scipy.linalg import eigh_tridiagonal

    from qiskit_metal.analyses.quantization.constants import hbar

    c, lpu, dz = 1 / (Z0 * vp), Z0 / vp, L / N
    cap = np.full(N + 1, c * dz)
    cap[0] += C0 - c * dz / 2
    cap[-1] += CL - c * dz / 2
    y = 1 / (lpu * dz)
    diag = np.full(N + 1, 2 * y)
    diag[0] = diag[-1] = y
    s = 1 / np.sqrt(cap)
    w2, vec = eigh_tridiagonal(
        diag * s * s, -y * s[:-1] * s[1:], select="i", select_range=(0, 2)
    )
    i = int(np.argmax(w2 > 1e16))  # skip the d.c. mode
    w = np.sqrt(w2[i])
    v = vec[:, i] * s
    v = v * np.sign(v[0]) * np.sqrt(hbar / (2 * w * (v @ (cap * v))))
    return w / (2 * np.pi), C0 * w * v[0], CL * w * v[-1]


class TestLoadedTLTwoEndSigns(unittest.TestCase):
    """Q_zpf at the two ends of a line loaded at both ends carries the sign
    of the mode function there (#1219)."""

    def test_against_lc_ladder(self):
        vp, fr, Z0 = 0.4 * 299792458.0, 6000.0, 50.0
        for c0, cl in ((20.0, 20.0), (20.0, 60.0), (600.0, 600.0)):
            with self.subTest(c0=c0, cl=cl):
                q, phi_zpf, _, L = analyze_loaded_tl(fr, vp, Z0, {"a": c0, "b": cl})
                f, q0, ql = _ladder_end_charges(L, vp, Z0, c0 * 1e-15, cl * 1e-15)
                self.assertAlmostEqual(f / (fr * 1e6), 1.0, places=5)
                self.assertGreater(q["a"], 0)
                self.assertLess(q["b"], 0)
                self.assertAlmostEqual(q["a"] / q0, 1.0, places=5)
                self.assertAlmostEqual(q["b"] / ql, 1.0, places=5)
                self.assertLess(phi_zpf["b"], 0)

    def test_bus_and_direct_coupling_interfere_constructively(self):
        """Two transmons below a lambda/2 bus, coupled to opposite ends, plus a
        small direct capacitance. The bus-mediated exchange g1 g2 / Delta and
        the direct g12 add (an independent LC-ladder model of this circuit
        gives J = 3.64 MHz vs 2.94 MHz direct-only), so with Delta < 0
        sign(g1b * g2b) must be opposite to sign(g12)."""
        import pandas as pd

        from qiskit_metal.analyses.quantization.lom_core_analysis import (
            Cell,
            CompositeSystem,
            Subsystem,
        )

        nodes = ["g", "q1a", "q1b", "q2a", "q2b", "b1", "b2"]
        branch = {
            ("q1a", "q1b"): 45, ("q2a", "q2b"): 45, ("q1a", "g"): 40,
            ("q1b", "g"): 40, ("q2a", "g"): 40, ("q2b", "g"): 40,
            ("q1a", "b1"): 4, ("q2a", "b2"): 4, ("b1", "g"): 20,
            ("b2", "g"): 20, ("q1a", "q2a"): 0.3,
        }  # fmt: skip
        cmat = pd.DataFrame(0.0, index=nodes, columns=nodes)
        for (a, b), c in branch.items():
            cmat.loc[a, a] += c
            cmat.loc[b, b] += c
            cmat.loc[a, b] -= c
            cmat.loc[b, a] -= c
        cell = Cell(
            dict(
                node_rename={},
                cap_mat=cmat,
                jj_dict={("q1a", "q1b"): "j1", ("q2a", "q2b"): "j2"},
                ind_dict={("q1a", "q1b"): 12.0, ("q2a", "q2b"): 12.0},
                cj_dict={("q1a", "q1b"): 2.0, ("q2a", "q2b"): 2.0},
            )
        )
        f_bus = 6.15
        subs = [
            Subsystem(name="Q1", sys_type="TRANSMON", nodes=["j1"]),
            Subsystem(name="Q2", sys_type="TRANSMON", nodes=["j2"]),
            Subsystem(
                name="bus",
                sys_type="TL_RESONATOR",
                nodes=["b1", "b2"],
                q_opts=dict(f_res=f_bus, Z0=50.0, vp=0.4 * 299792458.0),
            ),
        ]
        system = CompositeSystem(
            subsystems=subs, cells=[cell], grd_node="g", nodes_force_keep=["b1", "b2"]
        )
        system.create_hilbertspace()
        for sub, node in ((subs[0], "j1"), (subs[1], "j2")):
            p = sub.h_params[node]  # MHz
            self.assertLess(np.sqrt(8 * p["EJ"] * p["EC"]) - p["EC"], f_bus * 1e3)
        g = system.compute_gs()
        idx = {n: system.node_index(n) for n in ("j1", "j2", "b1", "b2")}
        g12 = g[idx["j1"], idx["j2"]]
        g1b = g[idx["j1"], idx["b1"]]
        g2b = g[idx["j2"], idx["b2"]]
        self.assertNotEqual(g12, 0)
        self.assertEqual(np.sign(g1b * g2b), -np.sign(g12))


# The #1219 circuit: two floating transmons, each coupled with 4 fF to one end
# of a two-node TL_RESONATOR bus; c_dir between the transmon pads and c12
# between the two bus ends. Capacitances in fF, inductances in nH.
_BUS_VP, _BUS_Z0, _BUS_F, _LJ, _CJ = 0.4 * 299792458.0, 50.0, 6.15, 12.0, 2.0


def _bus_system(c_dir=0.0, c12=0.0):
    """CompositeSystem of the #1219 circuit with the transmons linearized
    (``LUMPED_RESONATOR`` on the junction, L_J and C), so that an exact
    linear circuit is the reference."""
    import pandas as pd

    from qiskit_metal.analyses.quantization.lom_core_analysis import (
        Cell,
        CompositeSystem,
        Subsystem,
    )

    names = ["g", "q1a", "q1b", "q2a", "q2b", "b1", "b2"]
    branch = {
        ("q1a", "q1b"): 45, ("q2a", "q2b"): 45, ("q1a", "g"): 40,
        ("q1b", "g"): 40, ("q2a", "g"): 40, ("q2b", "g"): 40,
        ("q1a", "b1"): 4, ("q2a", "b2"): 4, ("b1", "g"): 20,
        ("b2", "g"): 20, ("q1a", "q2a"): c_dir, ("b1", "b2"): c12,
    }  # fmt: skip
    cmat = pd.DataFrame(0.0, index=names, columns=names)
    for (a, b), c in branch.items():
        cmat.loc[a, a] += c
        cmat.loc[b, b] += c
        cmat.loc[a, b] -= c
        cmat.loc[b, a] -= c
    junctions = (("q1a", "q1b"), ("q2a", "q2b"))
    cell = Cell(
        dict(
            node_rename={},
            cap_mat=cmat,
            jj_dict=dict(zip(junctions, ("j1", "j2"))),
            ind_dict={j: _LJ for j in junctions},
            cj_dict={j: _CJ for j in junctions},
        )
    )
    bus_opts = dict(f_res=_BUS_F, Z0=_BUS_Z0, vp=_BUS_VP, truncated_dim=4)
    subs = [
        Subsystem(name=f"Q{i}", sys_type="LUMPED_RESONATOR", nodes=[f"j{i}"])
        for i in (1, 2)
    ]
    subs.append(
        Subsystem(
            name="bus", sys_type="TL_RESONATOR", nodes=["b1", "b2"], q_opts=bus_opts
        )
    )
    system = CompositeSystem(
        subsystems=subs, cells=[cell], grd_node="g", nodes_force_keep=["b1", "b2"]
    )
    return system, cmat


def _ladder_frequencies(system, cmat, sections=200):
    """Normal-mode frequencies [GHz] of the same circuit with the qubits
    linear (L_J, C_J) and the bus an LC ladder of the length the LOM assigns
    to it. Independent of the LOM Hamiltonian assembly."""
    from scipy.linalg import eigh

    c_inv = np.asarray(system.circuitGraph().C_inv_k)
    port = {b: system.node_index(b) for b in ("b1", "b2")}
    loads = {b: 1 / c_inv[i, i] for b, i in port.items()}
    *_, length = analyze_loaded_tl(_BUS_F * 1e3, _BUS_VP, _BUS_Z0, loads)
    nodes = ["q1a", "q1b", "q2a", "q2b", "b1", "b2"]
    idx = {n: i for i, n in enumerate(nodes)}
    n0, dim = len(nodes), len(nodes) + sections - 1
    cap = np.zeros((dim, dim))
    cap[:n0, :n0] = cmat.loc[nodes, nodes].to_numpy() * 1e-15
    k_inv = np.zeros((dim, dim))

    def branch(mat, a, b, y):
        mat[a, a] += y
        mat[b, b] += y
        mat[a, b] -= y
        mat[b, a] -= y

    for a, b in (("q1a", "q1b"), ("q2a", "q2b")):
        branch(cap, idx[a], idx[b], _CJ * 1e-15)
        branch(k_inv, idx[a], idx[b], 1 / (_LJ * 1e-9))
    dz = length / sections
    chain = [idx["b1"], *range(n0, dim), idx["b2"]]
    for m, node in enumerate(chain):
        cap[node, node] += dz / (_BUS_Z0 * _BUS_VP) * (0.5 if m in (0, sections) else 1)
    for a, b in zip(chain[:-1], chain[1:]):
        branch(k_inv, a, b, _BUS_VP / (_BUS_Z0 * dz))
    w2 = eigh(k_inv, cap, eigvals_only=True)
    f = np.sqrt(w2[w2 > (2 * np.pi * 1e9) ** 2]) / (2 * np.pi * 1e9)
    return np.sort(f)


class TestTwoNodeTLCoupling(unittest.TestCase):
    """Couplings through a two-node TL_RESONATOR against an exact linear
    circuit (#1219 follow-up)."""

    def test_end_to_end_term_counted_once(self):
        """C^-1_k[b1, b2] Q_b1 Q_b2 appears once in 1/2 Q^T C_k^-1 Q. 1 fF
        between the bus ends moves the ladder bus 7.8 MHz down. The LOM bus,
        counting the term once, is 0.24 MHz above the ladder (the rest is
        second order in c12, through the omitted bus modes); counted twice,
        as before, it was 7.3 MHz below."""
        bus = []
        for c12 in (0.0, 1.0):
            system, cmat = _bus_system(c12=c12)
            evals = system.add_interaction().eigenvals(evals_count=4)
            f_lom = (evals[3] - evals[0]) / 1e3  # GHz; levels 1, 2 are the qubits
            bus.append((f_lom, _ladder_frequencies(system, cmat)[2]))
        (_, f_ladder_0), (f_lom, f_ladder) = bus
        self.assertGreater(f_ladder_0 - f_ladder, 7e-3)
        self.assertLess(abs(f_lom - f_ladder), 1e-3)


class TestLoadedTLInputUnchanged(unittest.TestCase):
    """The caller's ``cap_loading`` dict is left alone (#1232)."""

    def _check(self, loading, shorted):
        original = dict(loading)
        first = analyze_loaded_tl(6000.0, _VP, 50.0, loading, shorted=shorted)
        self.assertEqual(loading, original)
        second = analyze_loaded_tl(6000.0, _VP, 50.0, loading, shorted=shorted)
        self.assertEqual(first[0], second[0])
        self.assertEqual(first[3], second[3])

    def test_single_open(self):
        self._check({"Q": 50.0}, shorted=False)

    def test_single_shorted(self):
        self._check({"Q": 50.0}, shorted=True)

    def test_two_nodes(self):
        self._check({"a": 20.0, "b": 30.0}, shorted=False)


if __name__ == "__main__":
    unittest.main()
