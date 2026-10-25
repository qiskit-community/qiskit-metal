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
"""Package modes and qubit couplings, analytically.

A superconducting chip in a metal package sits in a box resonator loaded by
the silicon slab. The lowest box modes are LSM modes, whose electric field at
the slab surface drives every qubit on the chip at once, with a coupling that
follows the mode's standing-wave pattern across the array. This module holds
the closed-form side of that picture, to check a full-wave simulation
against:

- the LSM_ab0 modes of a rectangular box partly filled with a dielectric slab
  (``lsm_mode``, and the closed-form approximations ``lsm_mode_approx``), and
  the electric-dipole estimate of a qubit's coupling to one (``dipole_coupling``);
- the two-mode lumped circuit of a qubit and a package mode, its couplings,
  eigenfrequencies and impedance matrix (``circuit_couplings``,
  ``circuit_impedance``), and the fit of a simulated impedance matrix back to
  that circuit (``fit_impedance``);
- the amplitude of a coupling pattern over a uniform ``n x n`` array
  (``qubit_centers``, ``fit_amplitude``).

Equation numbers refer to R. Molavi *et al.*, "Extracting electromagnetic
bare mode couplings in large superconducting quantum processors,"
arXiv:2609.22442 (2026). Used by tutorials 4.41-4.45; the finite-element side
is :mod:`qiskit_metal.analyses.fem`.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import scipy.linalg as la
import scipy.optimize as opt

EPS0 = 8.8541878128e-12  # F/m
MU0 = 1.25663706212e-6  # H/m
C0 = 299792458.0  # m/s
C0_MM = C0 * 1e3  # mm/s


def qubit_centers(n, pitch):
    """{(i, j): (x, y)} qubit centers in mm, column i along x, row j along y."""
    return {
        (i, j): ((i + 0.5) * pitch, (j + 0.5) * pitch)
        for i in range(n)
        for j in range(n)
    }


# ---------------------------------------------------------------------------
# 2. Analytic package modes: LSM modes of a dielectric-loaded box (App. E)
# ---------------------------------------------------------------------------


@dataclass
class LSMMode:
    """One LSM_ab0 mode of a rectangular box partially filled with a slab.

    Lengths in metres. ``E0x`` is the amplitude of the in-plane field at the
    slab surface for 1 J of mode energy, Eq. (E14).
    """

    a: int
    b: int
    f: float
    kz_si: float
    kz_air: float
    gamma: float
    E0z: float
    E0x: float
    U_ratio: float
    Lx: float
    Ly: float
    Lz: float
    t: float
    eps_r: float

    def Ez(self, z):
        """Vertical field E_z(z) at the in-plane maximum, Eqs. (E1)-(E2)."""
        z = np.asarray(z, dtype=float)
        si = self.E0z * np.cos(self.kz_si * z)
        air = (
            self.eps_r
            * self.E0z
            * np.cos(self.kz_si * self.t)
            / np.cosh(self.kz_air * (self.Lz - self.t))
            * np.cosh(self.kz_air * (self.Lz - z))
        )
        return np.where(z <= self.t, si, air)

    def Ex_surface(self, x, y):
        """In-plane field E_x at the slab surface z = t, Eqs. (15), (E8)-(E9).

        ``E0x`` holds the magnitude the paper quotes. Eq. (E9) carries a minus
        sign, because E_z decreases with height in the silicon:
        E_x = -a |E0x| cos(a pi x/Lx) sin(b pi y/Ly) for E_z > 0.
        """
        return (
            -self.a
            * self.E0x
            * np.cos(self.a * np.pi * x / self.Lx)
            * np.sin(self.b * np.pi * y / self.Ly)
        )


def lsm_mode(a, b, Lx, Ly, Lz, t, eps_r, Em=1.0):
    """Solve the transcendental equation (E3) for the lowest LSM_ab0 mode.

    The lowest mode is the root with ``kz_si * t < pi/2``, below the first
    pole of ``ks tan(ks t)``.

    ``Lx``, ``Ly``, ``Lz`` (the box) and ``t`` (the slab) are in mm; the
    returned mode is in SI units, normalized to mode energy ``Em`` joules.
    """
    Lx, Ly, Lz, t = [1e-3 * v for v in (Lx, Ly, Lz, t)]
    gamma = np.hypot(a * np.pi / Lx, b * np.pi / Ly)

    def kz(w):
        k0 = w / C0
        return np.sqrt(eps_r * k0**2 - gamma**2), np.sqrt(gamma**2 - k0**2)

    def residual(w):
        ks, ka = kz(w)
        return ks * np.tan(ks * t) - eps_r * ka * np.tanh(ka * (Lz - t))

    # The lowest root has ks t < pi/2; ks tan(ks t) has a pole at ks t = pi/2,
    # which lies inside (c gamma / sqrt(eps_r), c gamma) for small boxes or
    # thick slabs. Stop the bracket just below it.
    lo = C0 * gamma / np.sqrt(eps_r) * (1 + 1e-12)
    w_pole = C0 * np.sqrt(gamma**2 + (np.pi / (2 * t)) ** 2) / np.sqrt(eps_r)
    hi = min(C0 * gamma * (1 - 1e-12), w_pole * (1 - 1e-9))
    w = opt.brentq(residual, lo, hi, xtol=1e-6)
    ks, ka = kz(w)

    # Mode energy, Eq. (E13), in units of U0 = eps0 E0z^2 V / 16
    r_si = (ks / gamma) ** 2
    r_air = (ka / gamma) ** 2
    U_ratio = eps_r * (
        (1 + r_si) * t / Lz + (1 - r_si) * np.sin(2 * ks * t) / (2 * ks * Lz)
    ) + (eps_r**2 * np.cos(ks * t) ** 2 / np.cosh(ka * (Lz - t)) ** 2) * (
        (1 - r_air) * (1 - t / Lz)
        + (1 + r_air) * np.sinh(2 * ka * (Lz - t)) / (2 * ka * Lz)
    )
    V = Lx * Ly * Lz
    E0z = np.sqrt(Em / (EPS0 * V / 16 * U_ratio))
    E0x = (np.pi / Lx) * ks * np.sin(ks * t) / gamma**2 * E0z  # Eq. (E14)
    return LSMMode(
        a, b, w / (2 * np.pi), ks, ka, gamma, E0z, E0x, U_ratio, Lx, Ly, Lz, t, eps_r
    )


def lsm_mode_approx(a, b, Lx, Ly, Lz, t, eps_r, Em=1.0):
    """The closed-form approximations at the end of Appendix E (SI units).

    They assume a thin slab, ``kz_si * t << 1``. A ``UserWarning`` is issued
    when the approximate ``kz_si * t`` exceeds 0.5, where the frequency is
    off by about 1 % or more (small boxes or thick slabs); use
    :func:`lsm_mode` there.
    """
    Lx, Ly, Lz, t = [1e-3 * v for v in (Lx, Ly, Lz, t)]
    gamma = np.hypot(a * np.pi / Lx, b * np.pi / Ly)
    eps_eff = 1 / (t / Lz / eps_r + (1 - t / Lz))
    V = Lx * Ly * Lz
    kz_si = gamma * np.sqrt((eps_r - 1) * (1 - t / Lz))
    if kz_si * t > 0.5:
        warnings.warn(
            f"lsm_mode_approx: kz_si * t = {kz_si * t:.2f} > 0.5, outside the "
            "thin-slab validity of the closed-form approximation (frequency "
            "error ~1 % or more); use lsm_mode.",
            stacklevel=2,
        )
    return dict(
        f=C0 * gamma / np.sqrt(eps_eff) / (2 * np.pi),
        kz_si=kz_si,
        kz_air=gamma * np.sqrt(1 - 1 / eps_eff),
        E0x=(eps_r - 1)
        * np.pi
        * t
        / Lx
        * (1 - t / Lz)
        * np.sqrt(8 * Em / (eps_r * EPS0 * V) * eps_eff / eps_r),
        eps_eff=eps_eff,
    )


def dipole_coupling(px, mode: LSMMode, Em=1.0, En=1.0):
    """Electric-dipole estimate of the on-resonance coupling amplitude.

    k_C = p_x a E0x / (2 sqrt(Em En)) (Eq. 16 at the field maximum), and
    g_C = k_C sqrt(w_m w_n) / 2 with w_n = w_m. Returns (k_C, A) with A in Hz.
    """
    kC = px * mode.a * mode.E0x / (2 * np.sqrt(Em * En))
    return kC, kC * mode.f / 2


# ---------------------------------------------------------------------------
# 3. The two-mode circuit (Fig. 3) and the impedance-matrix fit (App. D)
# ---------------------------------------------------------------------------


def circuit_couplings(C, L):
    """Bare frequencies and couplings of two coupled LC resonators, Eq. (A6)-(A11).

    ``C`` and ``L`` are the 2x2 capacitance and inductance matrices (SI).
    Returns a dict with bare angular frequencies ``w`` (2,), coupling
    efficiencies ``kC``, ``kL`` and couplings ``gC``, ``gL`` in rad/s.
    """
    Ci = la.inv(C)
    Li = la.inv(L)
    w = np.sqrt(np.diag(Li) * np.diag(Ci))
    kC = Ci[0, 1] / np.sqrt(Ci[0, 0] * Ci[1, 1])
    kL = -Li[0, 1] / np.sqrt(Li[0, 0] * Li[1, 1])
    s = np.sqrt(w[0] * w[1])
    return dict(w=w, kC=kC, kL=kL, gC=kC * s / 2, gL=kL * s / 2)


def g_on_resonance(gC, gL, wm, wn):
    """Eq. (10): convert (g_C, g_L) at a detuned qubit to the resonant g."""
    return (gC - gL * wm / wn) * np.sqrt(wm / wn)


def circuit_eigenfrequencies(C, L):
    """Exact normal-mode angular frequencies: eigenvalues of C^-1/2 L^-1 C^-1/2."""
    Cih = la.inv(la.sqrtm(C)).real
    return np.sqrt(np.sort(la.eigvalsh(Cih @ la.inv(L) @ Cih)))


def circuit_impedance(w, Lp, C, dL):
    """Impedance matrix of the lumped model, Eq. (12). ``w`` in rad/s.

    ``Lp`` holds the port shunts (diagonal), ``C`` the capacitance matrix and
    ``dL`` the geometric inductances. Returns complex Z of shape (len(w), 2, 2)
    with the engineering convention Z = jX.
    """
    w = np.atleast_1d(w)
    Z = np.empty((len(w), 2, 2), dtype=complex)
    for k, wk in enumerate(w):
        inner = la.inv(la.inv(1j * wk * C) + 1j * wk * dL)
        Z[k] = la.inv(la.inv(1j * wk * Lp) + inner)
    return Z


@dataclass
class ImpedanceFit:
    """Result of the Appendix-D fit (SI units, index 0 = package, 1 = qubit)."""

    poles: np.ndarray  # angular frequencies of the two poles
    residues: np.ndarray  # (2, 2, 2) residue matrices R_mu
    C: np.ndarray
    Lp: np.ndarray
    dL: np.ndarray
    rms_error: float

    @property
    def L(self):
        return self.Lp + self.dL

    def couplings(self):
        """(g_C, g_L, g) in Hz: g_C, g_L at the fitted detuning, g via Eq. (10)."""
        c = circuit_couplings(self.C, self.L)
        g = g_on_resonance(c["gC"], c["gL"], c["w"][0], c["w"][1])
        return c["gC"] / (2 * np.pi), c["gL"] / (2 * np.pi), g / (2 * np.pi)


def fit_impedance(w, Z, n_poles=2):
    """Fit a simulated 2x2 impedance matrix to Eq. (12), following Appendix D.

    1. Fit Z = sum_mu 2 j w w_mu R_mu / (w_mu^2 - w^2) + j w dL~ (Eq. D1, D4):
       the pole frequencies by least squares, the residues and dL~ linearly.
    2. Factor each residue as R_mu = sigma_mu sigma_mu^T (D5), stack Sigma.
    3. L~^-1 = 1/2 Sigma^-T Omega Sigma^-1, C~ = 1/2 Sigma^-T Omega^-1 Sigma^-1 (D7).
    4. Undo the tail correction with alpha = I + L~^-1 dL~ (D3).

    ``w`` in rad/s, ``Z`` complex (nw, 2, 2) in ohms.
    """
    w = np.asarray(w, dtype=float)
    X = np.asarray(Z).imag.reshape(len(w), -1)
    finite = np.all(np.isfinite(X), axis=1)  # a sample exactly on a pole is infinite
    w, X = w[finite], X[finite]
    # relative weights, softened so zero crossings of X do not dominate
    weight = 1 / (np.abs(X) + np.median(np.abs(X), axis=0))

    def rows(poles):
        """Drop samples that sit on top of a pole."""
        return np.all(
            np.abs(w[:, None] - poles[None, :]) > 1e-9 * poles[None, :], axis=1
        )

    def design(poles, keep):
        cols = [2 * w[keep] * p / (p**2 - w[keep] ** 2) for p in poles] + [w[keep]]
        return np.stack(cols, axis=1)  # (nw, n_poles + 1)

    def solve_linear(poles):
        keep = rows(poles)
        A = design(poles, keep)
        s = np.abs(A).max(axis=0)  # column scaling for conditioning
        coef = np.empty((A.shape[1], X.shape[1]))
        for k in range(
            X.shape[1]
        ):  # weighted least squares, one matrix element at a time
            wk = weight[keep, k][:, None]
            coef[:, k] = la.lstsq(wk * A / s, weight[keep, k] * X[keep, k])[0] / s
        return coef, A, keep

    def resid(poles):
        coef, A, keep = solve_linear(poles)
        r = np.zeros_like(
            X
        )  # fixed length: samples on top of a trial pole count as zero misfit
        r[keep] = (A @ coef - X[keep]) * weight[keep]
        return r.ravel()

    # Poles: det X jumps through infinity at a pole (and passes through zero
    # at a zero of Z). Take the sign changes with the largest |det X| and
    # refine each as the root of 1/det X, which is smooth across the pole.
    det = X[:, 0] * X[:, 3] - X[:, 1] * X[:, 2]
    flips = np.nonzero(np.sign(det[:-1]) != np.sign(det[1:]))[0]
    size = np.sqrt(np.abs(det[flips] * det[flips + 1]))
    flips = np.sort(flips[np.argsort(-size)[:n_poles]])
    if len(flips) < n_poles:
        raise ValueError(
            f"found {len(flips)} of {n_poles} poles: refine the frequency grid so that "
            "each pole and the zero next to it fall in different intervals"
        )
    guess, lower, upper = [], [], []
    for k in flips:
        lo, hi = max(k - 1, 0), min(k + 3, len(w))
        dw = w[k + 1] - w[k]
        coeffs = np.polyfit((w[lo:hi] - w[k]) / dw, 1 / det[lo:hi], min(hi - lo - 1, 3))
        roots = (
            np.roots(coeffs).real * dw + w[k]
            if np.all(np.isfinite(coeffs))
            else np.array([])
        )
        roots = roots[(roots >= w[k]) & (roots <= w[k + 1])]
        guess.append(roots[0] if len(roots) else 0.5 * (w[k] + w[k + 1]))
        lower.append(w[k])  # the pole lies between the two samples where det X flips
        upper.append(w[k + 1])
    guess, lower, upper = np.array(guess), np.array(lower), np.array(upper)
    sol = opt.least_squares(
        resid,
        guess,
        x_scale=(upper - lower) / 10,
        bounds=(lower, upper),
        xtol=1e-15,
        ftol=1e-15,
        gtol=1e-15,
    )
    poles = np.sort(sol.x)
    coef, A, keep = solve_linear(poles)
    residues = coef[:n_poles].reshape(n_poles, 2, 2)
    dLt = coef[n_poles].reshape(2, 2)
    dLt = (dLt + dLt.T) / 2

    sig = []
    for R in residues:
        R = (R + R.T) / 2
        ev, vec = la.eigh(R)
        k = np.argmax(np.abs(ev))
        sig.append(vec[:, k] * np.sqrt(abs(ev[k])))
    Sig = np.stack(sig, axis=1)
    Om = np.diag(poles)
    SiT = la.inv(Sig).T
    Lt_inv = 0.5 * SiT @ Om @ la.inv(Sig)
    Ct = 0.5 * SiT @ la.inv(Om) @ la.inv(Sig)
    alpha = np.eye(2) + Lt_inv @ dLt
    ai = la.inv(alpha)
    C = ai @ Ct @ ai.T
    Lp_inv = ai @ Lt_inv
    dL = alpha.T @ dLt
    Lp = la.inv((Lp_inv + Lp_inv.T) / 2)
    rms = np.sqrt(np.mean(resid(poles) ** 2))
    return ImpedanceFit(poles, residues, (C + C.T) / 2, Lp, (dL + dL.T) / 2, rms)


def fit_amplitude(g, a, b, Lx, Ly):
    """Least-squares A in g = A cos(a pi x/Lx) sin(b pi y/Ly) (Eqs. 14, 17).

    ``g`` is an (n, n) array [j, i] over a uniform grid of qubits on a
    ``Lx x Ly`` (mm) chip. Returns (A, largest residual / |A|).
    """
    n = g.shape[0]
    c = qubit_centers(n, Lx / n)
    shape = np.zeros_like(g)
    for (i, j), (x, y) in c.items():
        shape[j, i] = np.cos(a * np.pi * x / Lx) * np.sin(b * np.pi * y / Ly)
    ok = np.isfinite(g)
    A = np.sum(g[ok] * shape[ok]) / np.sum(shape[ok] ** 2)
    return A, np.max(np.abs(g[ok] - A * shape[ok])) / abs(A)
