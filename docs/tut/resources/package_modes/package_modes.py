"""Package modes and qubit couplings with an open-source Maxwell solver.

Shared code for tutorials 4.41-4.45, which reproduce

    R. Molavi, E. Forati, Y. Zhang, A. R. Klots, J. Atalaya, B. W. Langley,
    D. A. Timucin, M. Nazari, G. Khan, Z. K. Minev, A. N. Korotkov and
    M. H. Devoret, "Extracting electromagnetic bare mode couplings in large
    superconducting quantum processors," arXiv:2609.22442 (2026).

The paper runs Ansys HFSS. Here the same calculations run on an open stack:
Quantum Metal holds the design, gmsh meshes it, scikit-fem assembles the
finite-element matrices (lowest-order Nedelec edge elements for the
electromagnetic field, Lagrange elements for electrostatics), and SciPy
solves them.

Units: lengths in millimetres inside the mesh and the solver, SI everywhere
else. A field vector ``u`` from the solver holds edge line integrals of E in
volts, so a junction voltage is a signed sum of edge values, and E in V/m is
``1e3`` times the interpolated ``u``.

Sections
    1. The paper's device and its reported numbers
    2. Analytic package modes (LSM modes of a dielectric-loaded box)
    3. The two-mode circuit and the impedance-matrix fit (Appendix D)
    4. The design in Quantum Metal
    5. Meshing with gmsh
    6. The Maxwell eigenproblem (scikit-fem + SciPy)
    7. Port reduced-order model: junction inductors and impedance matrices
    8. Electrostatics: capacitance matrix and dipole moment
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import scipy.linalg as la
import scipy.optimize as opt
import scipy.sparse as sp
import scipy.sparse.linalg as sla

EPS0 = 8.8541878128e-12  # F/m
MU0 = 1.25663706212e-6  # H/m
C0 = 299792458.0  # m/s
C0_MM = C0 * 1e3  # mm/s

# ---------------------------------------------------------------------------
# 1. The paper's device and its reported numbers
# ---------------------------------------------------------------------------

#: Geometry of the validation device (Fig. 4 of the paper), millimetres.
DEVICE = dict(
    Lx=30.0,  # package length along x
    Ly=30.0,  # package length along y
    Lz=3.0,  # package height
    t=0.5,  # silicon thickness
    eps_r=11.9,  # silicon relative permittivity
    n=10,  # qubits per row and per column
    pitch=3.0,  # qubit period in x and y
    pad_w=0.5,  # paddle size along x (the junction direction)
    pad_h=1.0,  # paddle size along y
    gap=0.2,  # paddle-to-paddle gap along x
)

#: Numbers quoted in the paper, for side-by-side comparison.
PAPER = dict(
    f_empty=7.07e9,  # fundamental mode, empty box
    f_si=6.49e9,  # with the silicon slab
    f_pads=6.48e9,  # with the qubit paddles, junctions open
    f_lsm210=10.23e9,  # LSM210 without paddles
    kz_si=445.4,  # 1/m, LSM110
    kz_air=58.4,  # 1/m, LSM110
    E0x_110=25.56e6,  # V/m for 1 J, LSM110
    E0x_210=26.25e6,  # V/m for 1 J, LSM210
    px=3.41e-10,  # C m, qubit dipole moment for 1 J
    dipole_length=0.58e-3,  # m
    C_qubit=170e-15,  # F (approximate, Sec. IV)
    A_110=15.6e6,  # Hz, fitted amplitude of g/2pi (Fig. 8)
    A_110_dipole=14.2e6,  # Hz, electric-dipole estimate
    A_210=49.8e6,  # Hz, fitted amplitude, LSM210 (Fig. 9)
    A_210_dipole=45.7e6,  # Hz, electric-dipole estimate
    two_g_q11=12.6e6,  # Hz, avoided crossing of qubit (1,1) (Fig. 5)
    # Impedance-matrix fit for qubit (0,0), Sec. III D:
    zfit_q00=dict(
        Lp_n=3.63e-9,
        Lp_m=1e-12,
        C_n=173.8e-15,
        dL_n=0.32e-9,
        C_m=132.0e-15,
        C_c=100e-18,
        dL_m=4.57e-9,
        M=-0.34e-12,
        gC=2.07e6,
        gL=-0.25e6,
        g=2.42e6,
    ),
    L_qubit_zfit=3.6e-9,  # shunt used in the impedance-matrix method
    max_rel_diff=0.048,  # largest spread between the four methods (Fig. 7)
)


def qubit_centers(n=DEVICE["n"], pitch=DEVICE["pitch"]):
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


def lsm_mode(a=1, b=1, Lx=None, Ly=None, Lz=None, t=None, eps_r=None, Em=1.0):
    """Solve the transcendental equation (E3) for the lowest LSM_ab0 mode.

    Arguments are in mm (defaults: the paper's device); the returned mode is
    in SI units, normalized to mode energy ``Em`` joules.
    """
    d = DEVICE
    Lx, Ly, Lz, t = [
        1e-3 * (v if v is not None else d[k])
        for v, k in ((Lx, "Lx"), (Ly, "Ly"), (Lz, "Lz"), (t, "t"))
    ]
    eps_r = d["eps_r"] if eps_r is None else eps_r
    gamma = np.hypot(a * np.pi / Lx, b * np.pi / Ly)

    def kz(w):
        k0 = w / C0
        return np.sqrt(eps_r * k0**2 - gamma**2), np.sqrt(gamma**2 - k0**2)

    def residual(w):
        ks, ka = kz(w)
        return ks * np.tan(ks * t) - eps_r * ka * np.tanh(ka * (Lz - t))

    lo = C0 * gamma / np.sqrt(eps_r) * (1 + 1e-12)
    hi = C0 * gamma * (1 - 1e-12)
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


def lsm_mode_approx(a=1, b=1, Lx=None, Ly=None, Lz=None, t=None, eps_r=None, Em=1.0):
    """The closed-form approximations at the end of Appendix E (SI units)."""
    d = DEVICE
    Lx, Ly, Lz, t = [
        1e-3 * (v if v is not None else d[k])
        for v, k in ((Lx, "Lx"), (Ly, "Ly"), (Lz, "Lz"), (t, "t"))
    ]
    eps_r = d["eps_r"] if eps_r is None else eps_r
    gamma = np.hypot(a * np.pi / Lx, b * np.pi / Ly)
    eps_eff = 1 / (t / Lz / eps_r + (1 - t / Lz))
    V = Lx * Ly * Lz
    return dict(
        f=C0 * gamma / np.sqrt(eps_eff) / (2 * np.pi),
        kz_si=gamma * np.sqrt((eps_r - 1) * (1 - t / Lz)),
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


# ---------------------------------------------------------------------------
# 4. The design in Quantum Metal
# ---------------------------------------------------------------------------


def _two_pad_transmon_class():
    """Build the TwoPadTransmon QComponent lazily (keeps Metal import optional)."""
    from qiskit_metal import Dict, draw
    from qiskit_metal.qlibrary.core import BaseQubit

    class TwoPadTransmon(BaseQubit):
        """Two rectangular paddles and a junction across the gap -- no ground pocket.

        The bare transmon of the paper's validation device: the paddles are
        separated along x (before rotation), the junction is a line across
        the gap.

        Default Options:
            * pad_width: '0.5mm' -- paddle size along the junction direction
            * pad_height: '1mm' -- paddle size across the junction direction
            * pad_gap: '0.2mm' -- gap between the paddles (the junction length)
            * jj_width: '20um' -- drawn width of the junction line
        """

        default_options = Dict(
            pad_width="0.5mm", pad_height="1mm", pad_gap="0.2mm", jj_width="20um"
        )
        component_metadata = Dict(
            short_name="Q",
            _qgeometry_table_poly="True",
            _qgeometry_table_junction="True",
        )

        def make(self):
            p = self.p
            pad = draw.rectangle(p.pad_width, p.pad_height)
            shift = (p.pad_gap + p.pad_width) / 2
            pad_left = draw.translate(pad, -shift, 0)
            pad_right = draw.translate(pad, +shift, 0)
            jj = draw.LineString([(-p.pad_gap / 2, 0), (p.pad_gap / 2, 0)])
            geoms = draw.rotate([pad_left, pad_right, jj], p.orientation, origin=(0, 0))
            pad_left, pad_right, jj = draw.translate(geoms, p.pos_x, p.pos_y)
            self.add_qgeometry(
                "poly", dict(pad_left=pad_left, pad_right=pad_right), chip=p.chip
            )
            self.add_qgeometry("junction", dict(jj=jj), width=p.jj_width, chip=p.chip)

    return TwoPadTransmon


def build_design(
    n=None,
    pitch=None,
    Lx=None,
    Ly=None,
    Lz=None,
    t=None,
    pad_w=None,
    pad_h=None,
    gap=None,
    orientation=0,
):
    """The validation processor as a Quantum Metal design (defaults: the paper).

    An ``n x n`` array of TwoPadTransmon qubits named ``Q_i_j`` (column i
    along x, row j along y) on a ``Lx x Ly`` chip. The chip spans
    0 < x < Lx, 0 < y < Ly so coordinates match the paper. The layer stack
    holds zero-thickness metal on a ``t`` mm silicon substrate, and the
    sample-holder variables put the package lid ``Lz`` above the floor.
    There is no ground plane on this chip. ``orientation`` (degrees) rotates
    every qubit; at 0 the paddles sit side by side along x, as in the paper.
    """
    from qiskit_metal import designs

    d = dict(DEVICE)
    for k, v in dict(
        n=n, pitch=pitch, Lx=Lx, Ly=Ly, Lz=Lz, t=t, pad_w=pad_w, pad_h=pad_h, gap=gap
    ).items():
        if v is not None:
            d[k] = v
    import qiskit_metal

    TwoPadTransmon = _two_pad_transmon_class()
    # Creating a design lists every renderer it cannot load (Ansys ones, when the
    # [ansys] extra is absent) at INFO level; none of them is used here.
    level = qiskit_metal.logger.level
    qiskit_metal.logger.setLevel("WARNING")
    try:
        design = designs.MultiPlanar({}, overwrite_enabled=True)
    finally:
        qiskit_metal.logger.setLevel(level)
    size = design.chips.main.size
    size.center_x, size.center_y = f"{d['Lx'] / 2}mm", f"{d['Ly'] / 2}mm"
    size.size_x, size.size_y = f"{d['Lx']}mm", f"{d['Ly']}mm"
    ls = design.ls.ls_df
    ls.loc[ls.layer == 1, "thickness"] = "0um"
    ls.loc[ls.layer == 3, "thickness"] = f"-{d['t']}mm"
    design.variables["sample_holder_top"] = f"{d['Lz'] - d['t']}mm"
    design.variables["sample_holder_bottom"] = f"{d['t']}mm"
    for i in range(d["n"]):
        for j in range(d["n"]):
            TwoPadTransmon(
                design,
                f"Q_{i}_{j}",
                options=dict(
                    pos_x=f"{(i + 0.5) * d['pitch']}mm",
                    pos_y=f"{(j + 0.5) * d['pitch']}mm",
                    pad_width=f"{d['pad_w']}mm",
                    pad_height=f"{d['pad_h']}mm",
                    pad_gap=f"{d['gap']}mm",
                    orientation=str(orientation),
                ),
            )
    return design


@dataclass
class Package:
    """What the mesher needs: the box, the slab, the metal and the junctions (mm)."""

    Lx: float
    Ly: float
    Lz: float
    t: float
    eps_r: float
    metals: dict  # name -> (k, 2) polygon exterior, box coordinates
    junctions: dict  # qubit name -> ((x0, y0), (x1, y1))

    @staticmethod
    def qubit_index(name):
        """'Q_3_7' -> (3, 7)."""
        _, i, j = name.split("_")
        return int(i), int(j)


def package_from_design(design, eps_r=None):
    """Read box, substrate, paddles and junction lines from a Metal design.

    The chip outline sets the package walls; the silicon thickness comes from
    the layer stack and the lid height from the sample-holder variables.
    Subtracted shapes (ground-plane cuts) are ignored: this chip has no
    ground plane.
    """

    def mm(v):
        return float(design.parse_value(v))

    size = design.chips.main.size
    Lx, Ly = mm(size.size_x), mm(size.size_y)
    x0, y0 = mm(size.center_x) - Lx / 2, mm(size.center_y) - Ly / 2
    ls = design.ls.ls_df
    t = abs(mm(ls.loc[ls.layer == 3, "thickness"].iloc[0]))
    Lz = mm(design.variables["sample_holder_top"]) + mm(
        design.variables["sample_holder_bottom"]
    )
    comps = {c.id: name for name, c in design.components.items()}
    metals, junctions = {}, {}
    polys = design.qgeometry.tables["poly"]
    for _, row in polys[~polys["subtract"].astype(bool)].iterrows():
        xy = np.asarray(row.geometry.exterior.coords)[:-1] - (x0, y0)
        metals[f"{comps[row.component]}.{row['name']}"] = xy
    for _, row in design.qgeometry.tables["junction"].iterrows():
        a, b = np.asarray(row.geometry.coords)[[0, -1]] - (x0, y0)
        junctions[comps[row.component]] = (a, b)
    return Package(
        Lx, Ly, Lz, t, DEVICE["eps_r"] if eps_r is None else eps_r, metals, junctions
    )


def plot_package_3d(ax, package, colors=None, z_scale=3.0):
    """Draw the box, the slab and the paddles on a matplotlib 3D axis.

    ``colors`` gives one color per paddle (in the order of
    ``package.metals``); z is stretched by ``z_scale`` so the thin package
    stays readable.
    """
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    Lx, Ly, Lz, t = package.Lx, package.Ly, package.Lz * z_scale, package.t * z_scale
    for x0, y0 in ((0, 0), (Lx, 0), (Lx, Ly), (0, Ly)):
        ax.plot([x0, x0], [y0, y0], [0, Lz], color="0.4", lw=0.8)
    for z0 in (0, Lz):
        ax.plot([0, Lx, Lx, 0, 0], [0, 0, Ly, Ly, 0], [z0] * 5, color="0.4", lw=0.8)
    slab = [
        [(0, 0, t), (Lx, 0, t), (Lx, Ly, t), (0, Ly, t)],
        [(0, 0, 0), (Lx, 0, 0), (Lx, 0, t), (0, 0, t)],
        [(Lx, 0, 0), (Lx, Ly, 0), (Lx, Ly, t), (Lx, 0, t)],
    ]
    ax.add_collection3d(
        Poly3DCollection(slab, facecolor="0.75", edgecolor="none", alpha=0.35)
    )
    pads = [[(x, y, t + 1e-3) for x, y in poly] for poly in package.metals.values()]
    ax.add_collection3d(
        Poly3DCollection(
            pads, facecolor="tab:orange" if colors is None else colors, edgecolor="none"
        )
    )
    ax.set(xlim=(0, Lx), ylim=(0, Ly), zlim=(0, Lz), xlabel="x (mm)", ylabel="y (mm)")
    ax.set_zticks([0, t, Lz], ["0", f"{package.t:g}", f"{package.Lz:g}"])
    ax.set_box_aspect((Lx, Ly, Lz))
    ax.view_init(elev=28, azim=-60)
    return ax


# ---------------------------------------------------------------------------
# 5. Meshing with gmsh
# ---------------------------------------------------------------------------


@dataclass
class PackageMesh:
    """A tetrahedral mesh of (part of) the package, with the entities we need."""

    p: np.ndarray  # (3, N) node coordinates, mm
    t: np.ndarray  # (4, T) tetrahedra
    material: np.ndarray  # (T,) 1 = silicon, 0 = vacuum
    metal_tris: dict  # metal name -> (k, 3) triangles on that paddle
    junction_segs: dict  # qubit name -> (k, 2) segments ordered from p0 to p1
    probe_segs: np.ndarray | None  # (k, 2) bottom to top, or None
    probe_xy: tuple | None
    bounds: tuple  # (x0, x1, y0, y1) of the meshed region
    region: str  # 'full', 'half' or 'quarter'
    package: Package
    mesh_time: float = 0.0

    @property
    def n_sym(self):
        """How many copies of this region make up the whole package."""
        return {"full": 1, "half": 2, "quarter": 4}[self.region]

    def triangles_in_plane(self, z, axis=2, tol=1e-6):
        """Mesh triangles lying in the plane coordinate[axis] = z, shape (k, 3)."""
        from skfem import MeshTet

        f = MeshTet(self.p, self.t).facets
        on = np.all(np.abs(self.p[axis, f] - z) < tol, axis=0)
        return f[:, on].T

    def slice(self, axis, value):
        """Cut the tetrahedra with the plane coordinate[axis] = value.

        Returns (polygons, material): a list of (k, 2) arrays in the two
        remaining coordinates (triangles or quadrilaterals), and the
        material of the tetrahedron each came from. Plot them with a
        matplotlib PolyCollection to see the mesh through the package.
        """
        other = [a for a in range(3) if a != axis]
        c = self.p[axis, self.t]  # (4, T)
        hit = np.nonzero((c.min(axis=0) < value) & (c.max(axis=0) > value))[0]
        pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        polys, mats = [], []
        for e in hit:
            nodes = self.t[:, e]
            pts = []
            for a, b in pairs:
                ca, cb = self.p[axis, nodes[a]], self.p[axis, nodes[b]]
                if (ca - value) * (cb - value) < 0:
                    s_ = (value - ca) / (cb - ca)
                    pts.append(
                        self.p[other, nodes[a]] * (1 - s_)
                        + self.p[other, nodes[b]] * s_
                    )
            pts = np.array(pts)
            ctr = pts.mean(axis=0)
            order = np.argsort(np.arctan2(pts[:, 1] - ctr[1], pts[:, 0] - ctr[0]))
            polys.append(pts[order])
            mats.append(self.material[e])
        return polys, np.array(mats)

    def summary(self):
        return (
            f"{self.region} package: {self.t.shape[1]:,} tetrahedra, {self.p.shape[1]:,} nodes, "
            f"{len(self.metal_tris)} paddles, {len(self.junction_segs)} junctions"
            + (", 1 probe" if self.probe_segs is not None else "")
            + f" (meshed in {self.mesh_time:.1f} s)"
        )


def mesh_package(
    package: Package,
    region="full",
    h_metal=0.1,
    h_max=0.8,
    grow=3.0,
    h_junction=None,
    r_junction=0.2,
    probe=None,
    pads=True,
    substrate=True,
    verbose=False,
):
    """Mesh the package with gmsh.

    Args:
        package: the geometry, e.g. from :func:`package_from_design`.
        region: ``'full'``, ``'half'`` (y < Ly/2) or ``'quarter'``
            (x < Lx/2, y < Ly/2). The cut faces become symmetry planes in
            the solver.
        h_metal: element size along the paddle edges (mm).
        h_max: largest element size (mm), in the bulk of the package.
        grow: distance (mm) over which the size grows from h_metal to h_max.
        h_junction: optional finer element size around each junction (mm).
            By default the junctions get h_metal like the paddle edges. The
            field is strongest in the junction gap, so seeding it finely is
            the most economical way to converge the junction voltages.
        r_junction: radius (mm) of the refined region around each junction.
        probe: optional (x, y) of a vertical wire port from floor to lid.
        pads: set False to leave the paddles (and junctions) out.
        substrate: set False to leave the silicon out (empty box).
    """
    import gmsh

    x1 = (
        package.Lx
        if region == "full"
        else package.Lx / 2
        if region == "quarter"
        else package.Lx
    )
    y1 = package.Ly if region == "full" else package.Ly / 2
    Lz, t = package.Lz, package.t
    tol = 1e-9

    def inside(xy):
        c = np.mean(xy, axis=0)
        return c[0] < x1 - tol and c[1] < y1 - tol

    initialized_here = not gmsh.isInitialized()
    if initialized_here:
        gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
    gmsh.model.add("package")
    occ = gmsh.model.occ
    if substrate:
        vols = [
            (occ.addBox(0, 0, 0, x1, y1, t), 1),
            (occ.addBox(0, 0, t, x1, y1, Lz - t), 0),
        ]
    else:
        vols = [(occ.addBox(0, 0, 0, x1, y1, Lz), 0)]
    tools, tool_kind = [], []
    if pads:
        for name, xy in package.metals.items():
            if not inside(xy):
                continue
            pts = [occ.addPoint(x, y, t) for x, y in xy]
            lines = [
                occ.addLine(pts[k], pts[(k + 1) % len(pts)]) for k in range(len(pts))
            ]
            surf = occ.addPlaneSurface([occ.addCurveLoop(lines)])
            tools.append((2, surf))
            tool_kind.append(("metal", name))
        for name, (a, b) in package.junctions.items():
            if not inside(np.array([a, b])):
                continue
            line = occ.addLine(occ.addPoint(a[0], a[1], t), occ.addPoint(b[0], b[1], t))
            tools.append((1, line))
            tool_kind.append(("junction", name))
    if probe is not None:
        line = occ.addLine(
            occ.addPoint(probe[0], probe[1], 0), occ.addPoint(probe[0], probe[1], Lz)
        )
        tools.append((1, line))
        tool_kind.append(("probe", "probe"))
    _, out_map = occ.fragment([(3, v) for v, _ in vols], tools)
    occ.synchronize()

    # silicon below z = t, vacuum above (by bounding box: robust to renumbering)
    vol_material = {}
    for _, tag in gmsh.model.getEntities(3):
        zmax = gmsh.model.getBoundingBox(3, tag)[5]
        vol_material[tag] = 1 if (substrate and zmax < t + 1e-6) else 0
    metal_surfs, junction_curves, probe_curves = {}, {}, []
    for (kind, name), children in zip(tool_kind, out_map[len(vols) :]):
        tags = [tag for _, tag in children]
        if kind == "metal":
            metal_surfs[name] = tags
        elif kind == "junction":
            junction_curves[name] = tags
        else:
            probe_curves = tags

    # Mesh size: fine along the paddle edges and junctions, coarse in the bulk
    # where the package mode varies over centimeters. An optional third level,
    # h_junction, seeds a small sphere around each junction more finely.
    edge_curves = []
    for tags in metal_surfs.values():
        for tag in tags:
            edge_curves += [
                c for _, c in gmsh.model.getBoundary([(2, tag)], oriented=False)
            ]
    edge_curves += probe_curves
    jj_curves = [c for tags in junction_curves.values() for c in tags]
    fld = gmsh.model.mesh.field
    sizes = []

    def seed(curves, h, dist_min, dist_max):
        dist = fld.add("Distance")
        fld.setNumbers(dist, "CurvesList", sorted(set(curves)))
        fld.setNumber(dist, "Sampling", 60)
        thr = fld.add("Threshold")
        fld.setNumber(thr, "InField", dist)
        fld.setNumber(thr, "SizeMin", h)
        fld.setNumber(thr, "SizeMax", h_max)
        fld.setNumber(thr, "DistMin", dist_min)
        fld.setNumber(thr, "DistMax", dist_max)
        sizes.append(thr)

    if h_junction is None or h_junction >= h_metal:
        edge_curves, jj_curves = edge_curves + jj_curves, []
    if edge_curves:
        seed(edge_curves, h_metal, 0.0, grow)
    if jj_curves:
        seed(jj_curves, h_junction, r_junction, r_junction + grow)
    if sizes:
        fmin = fld.add("Min")
        fld.setNumbers(fmin, "FieldsList", sizes)
        fld.setAsBackgroundMesh(fmin)
    gmsh.option.setNumber("Mesh.MeshSizeMax", h_max)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber(
        "Mesh.LcIntegrationPrecision", 1e-3
    )  # the default 1e-9 makes 1D meshing crawl
    gmsh.option.setNumber("Mesh.Algorithm3D", 10)  # HXT: fast, parallel
    gmsh.option.setNumber("General.NumThreads", 0)
    start = time.time()
    gmsh.model.mesh.generate(3)
    mesh_time = time.time() - start

    node_tags, coords, _ = gmsh.model.mesh.getNodes()
    xyz = coords.reshape(-1, 3)
    index = np.zeros(int(node_tags.max()) + 1, dtype=np.int64)
    index[node_tags.astype(np.int64)] = np.arange(len(node_tags))

    tets, material = [], []
    for tag, mat in vol_material.items():
        _, _, enodes = gmsh.model.mesh.getElements(3, tag)
        tt = index[enodes[0].astype(np.int64)].reshape(-1, 4)
        tets.append(tt)
        material.append(np.full(len(tt), mat, dtype=np.int8))

    metal_tris = {}
    for name, tags in metal_surfs.items():
        tris = []
        for tag in tags:
            _, _, enodes = gmsh.model.mesh.getElements(2, tag)
            tris.append(index[enodes[0].astype(np.int64)].reshape(-1, 3))
        metal_tris[name] = np.vstack(tris)

    def ordered_segments(tags, start, direction):
        segs = []
        for tag in tags:
            _, _, enodes = gmsh.model.mesh.getElements(1, tag)
            segs.append(index[enodes[0].astype(np.int64)].reshape(-1, 2))
        segs = np.vstack(segs)
        s0 = (xyz[segs[:, 0]] - start) @ direction
        s1 = (xyz[segs[:, 1]] - start) @ direction
        segs = np.where((s1 < s0)[:, None], segs[:, ::-1], segs)
        return segs[np.argsort(np.minimum(s0, s1))]

    junction_segs = {}
    for name, tags in junction_curves.items():
        a, b = package.junctions[name]
        start = np.array([a[0], a[1], t])
        direction = np.array([b[0] - a[0], b[1] - a[1], 0.0])
        junction_segs[name] = ordered_segments(tags, start, direction)
    probe_segs = None
    if probe_curves:
        probe_segs = ordered_segments(
            probe_curves, np.array([probe[0], probe[1], 0.0]), np.array([0, 0, 1.0])
        )

    gmsh.model.remove()
    if initialized_here:
        gmsh.finalize()
    return PackageMesh(
        p=xyz.T.copy(),
        t=np.vstack(tets).T.copy(),
        material=np.concatenate(material),
        metal_tris=metal_tris,
        junction_segs=junction_segs,
        probe_segs=probe_segs,
        probe_xy=None if probe is None else tuple(probe),
        bounds=(0.0, x1, 0.0, y1),
        region=region,
        package=package,
        mesh_time=mesh_time,
    )


class _Locator:
    """Find the tetrahedron and barycentric coordinates of arbitrary points.

    A KD-tree over the element centroids proposes candidates; the barycentric
    coordinates decide. Vectorized, so tens of thousands of points take
    seconds on a mesh of a million elements.
    """

    def __init__(self, p, t, n_candidates=16):
        from scipy.spatial import cKDTree

        self.p, self.t, self.k = p, t, n_candidates
        v0 = p[:, t[0]].T
        J = np.stack(
            [p[:, t[1]].T - v0, p[:, t[2]].T - v0, p[:, t[3]].T - v0], axis=2
        )  # (T, 3, 3), columns
        self.Jinv = np.linalg.inv(J)  # rows are the gradients of lambda_1..3
        self.v0 = v0
        self.tree = cKDTree(p[:, t].mean(axis=1).T)

    def locate(self, pts):
        """(element index (n,), barycentric coordinates (4, n)) for points (3, n) in mm."""
        x = np.asarray(pts, dtype=float).T
        _, cand = self.tree.query(x, k=self.k)
        best = np.full(len(x), -1)
        best_score = np.full(len(x), -np.inf)
        lam_best = np.zeros((4, len(x)))
        for c in cand.T:
            l123 = np.einsum("nij,nj->ni", self.Jinv[c], x - self.v0[c])
            lam = np.vstack([1 - l123.sum(axis=1), l123.T])
            score = lam.min(axis=0)
            better = score > best_score
            best[better], best_score[better], lam_best[:, better] = (
                c[better],
                score[better],
                lam[:, better],
            )
        return best, lam_best

    def gradients(self, elems):
        """Gradients of the four barycentric coordinates, shape (n, 4, 3), in 1/mm."""
        g123 = self.Jinv[elems]
        return np.concatenate([-g123.sum(axis=1, keepdims=True), g123], axis=1)


_LOCAL_EDGES = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]


def _element_edges(mesh, t):
    """Global edge index of each of the six local edges of every tetrahedron, (T, 6)."""
    N = mesh.p.shape[1]
    ek = mesh.edges[0].astype(np.int64) * N + mesh.edges[1]
    order = np.argsort(ek)
    out = np.empty((t.shape[1], 6), dtype=np.int64)
    for k, (a, b) in enumerate(_LOCAL_EDGES):
        lo, hi = np.minimum(t[a], t[b]), np.maximum(t[a], t[b])
        out[:, k] = order[
            np.searchsorted(ek, lo.astype(np.int64) * N + hi, sorter=order)
        ]
    return out


# ---------------------------------------------------------------------------
# 6. The Maxwell eigenproblem
# ---------------------------------------------------------------------------


class _Factor:
    """Sparse LU of a symmetric matrix, with a fill-reducing ordering.

    Uses METIS nested dissection when pymetis is installed (much less fill
    on 3D meshes), else SuperLU's minimum degree on A + A^T.
    """

    def __init__(self, A):
        A = A.tocsr()
        self.n = A.shape[0]
        self.perm = None
        try:
            import pymetis

            G = A.copy()
            G.setdiag(0)
            G.eliminate_zeros()
            adj = (
                pymetis.CSRAdjacency(G.indptr, G.indices)
                if hasattr(pymetis, "CSRAdjacency")
                else None
            )
            if adj is not None:
                perm, _ = pymetis.nested_dissection(adj)
            else:
                perm, _ = pymetis.nested_dissection(xadj=G.indptr, adjncy=G.indices)
            self.perm = np.asarray(perm)
            Ap = A[self.perm][:, self.perm].tocsc()
            self.lu = sla.splu(
                Ap,
                permc_spec="NATURAL",
                diag_pivot_thresh=0.0,
                options=dict(SymmetricMode=True),
            )
        except ImportError:
            self.lu = sla.splu(
                A.tocsc(),
                permc_spec="MMD_AT_PLUS_A",
                diag_pivot_thresh=0.0,
                options=dict(SymmetricMode=True),
            )
        self.nnz = self.lu.L.nnz + self.lu.U.nnz

    def solve(self, b):
        if self.perm is None:
            return self.lu.solve(b)
        x = np.empty_like(b)
        x[self.perm] = self.lu.solve(np.ascontiguousarray(b[self.perm]))
        return x


def _facet_index(mesh, tris):
    """Indices of the skfem facets with the given node triples."""
    N = mesh.p.shape[1]

    def key(tri):
        s = np.sort(np.asarray(tri), axis=-1).astype(np.int64)
        return (s[..., 0] * N + s[..., 1]) * N + s[..., 2]

    allk = key(mesh.facets.T)
    order = np.argsort(allk)
    k = key(tris)
    pos = order[np.searchsorted(allk, k, sorter=order)]
    if not np.all(allk[pos] == k):
        raise ValueError("triangle not found among the mesh facets")
    return pos


def _edge_chain(mesh, segs):
    """(edge indices, signs) of a chain of oriented segments.

    Nedelec degrees of freedom are line integrals of E along each mesh edge,
    from its lower to its higher node number; the sign flips an edge that
    points against the chain.
    """
    N = mesh.p.shape[1]
    ek = mesh.edges[0].astype(np.int64) * N + mesh.edges[1]
    order = np.argsort(ek)
    lo, hi = np.minimum(segs[:, 0], segs[:, 1]), np.maximum(segs[:, 0], segs[:, 1])
    k = lo.astype(np.int64) * N + hi
    pos = order[np.searchsorted(ek, k, sorter=order)]
    if not np.all(ek[pos] == k):
        raise ValueError("segment not found among the mesh edges")
    return pos, np.where(segs[:, 0] < segs[:, 1], 1.0, -1.0)


@dataclass
class Mode:
    """An eigenmode, normalized to 1 J of energy in the whole package."""

    f: float  # Hz
    u: np.ndarray  # edge line integrals of E (V) on all edges of the region
    fem: "MaxwellFEM" = field(repr=False)

    def voltage(self, port):
        """Voltage across a port (junction name or 'probe'), in volts."""
        return self.fem.voltage(self.u, port)

    def field(self, points):
        """E at points (3, n) in mm, returned in V/m, shape (3, n)."""
        return self.fem.field(self.u, points)


class MaxwellFEM:
    """Curl-curl eigenproblem for the package, on lowest-order Nedelec elements.

    Weak form (lengths in mm, E in V/mm):

        int curl E . curl F dV + sum_ports (mu0 1e-3 / L_p) V_p(E) V_p(F)
            = k0^2 int eps_r E . F dV,

    where V_p(E) is the line integral of E across port p. Perfect-conductor
    walls and paddles pin the tangential E to zero (their edges are removed);
    a symmetry plane is either a perfect electric conductor ('pec', edges
    removed) or a perfect magnetic conductor ('pmc', nothing to do: the
    natural boundary condition).

    Args:
        pmesh: the mesh from :func:`mesh_package`.
        cuts: boundary condition on the x = Lx/2 and y = Ly/2 cut faces
            of a quarter (or half) mesh, e.g. ('pmc', 'pmc') for LSM110.
    """

    def __init__(self, pmesh: PackageMesh, cuts=("pmc", "pmc")):
        from skfem import Basis, BilinearForm, ElementTetN0, MeshTet, asm
        from skfem.helpers import curl, dot

        start = time.time()
        self.pmesh = pmesh
        self.cuts = cuts
        mesh = MeshTet(pmesh.p, pmesh.t)
        self.mesh = mesh
        element = ElementTetN0()
        self.basis = Basis(mesh, element)

        @BilinearForm
        def curlcurl(u, v, w):
            return dot(curl(u), curl(v))

        @BilinearForm
        def mass(u, v, w):
            return dot(u, v)

        self.K = asm(curlcurl, self.basis).tocsr()
        M = asm(mass, Basis(mesh, element, elements=np.nonzero(pmesh.material == 0)[0]))
        si = np.nonzero(pmesh.material == 1)[0]
        if len(si):
            M = M + pmesh.package.eps_r * asm(mass, Basis(mesh, element, elements=si))
        self.M = M.tocsr()

        # perfect-conductor edges: package walls, pec cut faces, paddles
        x0, x1, y0, y1 = pmesh.bounds
        pkg = pmesh.package
        bf = mesh.boundary_facets()
        fc = mesh.p[:, mesh.facets[:, bf]].mean(axis=1)
        keep_open = np.zeros(len(bf), bool)  # pmc cut faces
        if x1 < pkg.Lx - 1e-9 and cuts[0] == "pmc":
            keep_open |= np.isclose(fc[0], x1)
        if y1 < pkg.Ly - 1e-9 and cuts[1] == "pmc":
            keep_open |= np.isclose(fc[1], y1)
        pec_facets = [bf[~keep_open]]
        for tris in pmesh.metal_tris.values():
            pec_facets.append(_facet_index(mesh, tris))
        pec_edges = np.unique(mesh.f2e[:, np.concatenate(pec_facets)])
        self.free = np.setdiff1d(np.arange(self.basis.N), pec_edges)
        self._to_free = -np.ones(self.basis.N, dtype=np.int64)
        self._to_free[self.free] = np.arange(len(self.free))
        self.Kf = self.K[self.free][:, self.free].tocsc()
        self.Mf = self.M[self.free][:, self.free].tocsc()

        # port vectors: V_p = c_p . u
        self.ports = {}
        for name, segs in pmesh.junction_segs.items():
            self.ports[name] = _edge_chain(mesh, segs)
        if pmesh.probe_segs is not None:
            self.ports["probe"] = _edge_chain(mesh, pmesh.probe_segs)
        self._factors = {}
        self.assembly_time = time.time() - start

    # -- helpers -----------------------------------------------------------
    @property
    def n_dofs(self):
        return len(self.free)

    def port_vector(self, name, free=True):
        """Dense c_p with V_p = c_p . u (on free dofs by default)."""
        edges, signs = self.ports[name]
        if free:
            idx = self._to_free[edges]
            if np.any(idx < 0):
                raise ValueError(f"port {name} touches a perfect conductor")
            c = np.zeros(self.n_dofs)
            np.add.at(c, idx, signs)
        else:
            c = np.zeros(self.basis.N)
            np.add.at(c, edges, signs)
        return c

    @staticmethod
    def alpha(L):
        """Stiffness weight of a lumped inductor L (henry), in 1/mm."""
        return MU0 * 1e-3 / L

    def factor(self, sigma, inductors=None):
        """Cached LU of K + inductors - sigma M on the free dofs."""
        key = (round(sigma, 14), tuple(sorted((inductors or {}).items())))
        if key not in self._factors:
            A = self.Kf - sigma * self.Mf
            for name, L in (inductors or {}).items():
                c = sp.csc_matrix(self.port_vector(name)).T
                A = A + self.alpha(L) * (c @ c.T)
            self._factors = {key: _Factor(A)}  # keep one factorization in memory
        return self._factors[key]

    def energy(self, u):
        """Energy (J) in the whole package of a field u defined on this region.

        u is a peak amplitude, so 1/2 int eps |E|^2 is the total mode energy.
        """
        return self.pmesh.n_sym * 0.5 * EPS0 * 1e-3 * (u @ (self.M @ u))

    def voltage(self, u, port):
        edges, signs = self.ports[port]
        return float(signs @ u[edges])

    def field(self, u, points):
        """E (V/m) at points (3, n) given in mm.

        E = sum over the element's edges of u_e w_e, with the Whitney function
        w_ab = lambda_a grad lambda_b - lambda_b grad lambda_a for the edge
        from its lower-numbered node a to its higher-numbered node b.
        """
        if not hasattr(self, "_locator"):
            self._locator = _Locator(self.pmesh.p, self.pmesh.t)
            self._t2e = _element_edges(self.mesh, self.pmesh.t)
        elems, lam = self._locator.locate(points)
        grad = self._locator.gradients(elems)  # (n, 4, 3)
        t = self.pmesh.t[:, elems]
        E = np.zeros((len(elems), 3))
        for k, (a, b) in enumerate(_LOCAL_EDGES):
            s = np.where(t[a] < t[b], 1.0, -1.0)[:, None]
            w = lam[a][:, None] * grad[:, b] - lam[b][:, None] * grad[:, a]
            E += (s * w) * u[self._t2e[elems, k]][:, None]
        return 1e3 * E.T

    def _full(self, x):
        u = np.zeros(self.basis.N)
        u[self.free] = x
        return u

    def eigenmodes(self, f_target, n=1, inductors=None):
        """The n modes closest to f_target (Hz), each normalized to 1 J.

        ``inductors`` maps a port name to an inductance in henry: a lumped
        element across that junction (or probe). Ports not listed are open.
        """
        k0 = 2 * np.pi * f_target / C0_MM
        sigma = k0**2
        lu = self.factor(sigma, inductors)
        A = self.Kf
        for name, L in (inductors or {}).items():
            c = sp.csc_matrix(self.port_vector(name)).T
            A = A + self.alpha(L) * (c @ c.T)
        OPinv = sla.LinearOperator(A.shape, matvec=lu.solve, dtype=float)
        vals, vecs = sla.eigsh(A, k=n, M=self.Mf, sigma=sigma, which="LM", OPinv=OPinv)
        order = np.argsort(vals)
        modes = []
        for k in order:
            u = self._full(vecs[:, k])
            u /= np.sqrt(self.energy(u))
            u *= self._sign(u)
            modes.append(Mode(np.sqrt(vals[k]) * C0_MM / (2 * np.pi), u, self))
        return modes

    def _sign(self, u):
        """Fix the arbitrary eigenvector sign: E_z > 0 near the region's inner corner."""
        x0, x1, y0, y1 = self.pmesh.bounds
        pkg = self.pmesh.package
        pt = np.array(
            [
                [min(x1, pkg.Lx / 2) * 0.5],
                [min(y1, pkg.Ly / 2) * 0.5],
                [(pkg.t + pkg.Lz) / 2],
            ]
        )
        ez = self.field(u, pt)[2, 0]
        return 1.0 if ez >= 0 else -1.0


def emf_coupling(f, V, C, Em=1.0):
    """Induced-EMF coupling, Eq. (11): g/2pi in Hz.

    ``f`` is the package-mode frequency (Hz), ``V`` the voltage it induces
    across the open junction (V) at mode energy ``Em`` (J), and ``C`` the
    capacitance seen across the junction (F).
    """
    w = 2 * np.pi * f
    return w * V / 2 * np.sqrt(C / (2 * Em)) / (2 * np.pi)


def mirror_signs(cuts):
    """Sign of g under the x- and y-mirrors, for the given cut conditions.

    The junction voltage is a line integral of E_x. Across a 'pmc' plane the
    tangential field is even, across a 'pec' plane it is odd; the x-cut is
    normal to E_x and the y-cut is parallel to it.
    """
    sx = -1 if cuts[0] == "pmc" else +1
    sy = +1 if cuts[1] == "pmc" else -1
    return sx, sy


def unfold_quarter(values, cuts=("pmc", "pmc"), n=DEVICE["n"]):
    """{(i, j): v} on the quarter i, j < n/2 -> an (n, n) array [j, i] on the whole array."""
    sx, sy = mirror_signs(cuts)
    out = np.full((n, n), np.nan)
    for (i, j), v in values.items():
        out[j, i] = v
        out[j, n - 1 - i] = sx * v
        out[n - 1 - j, i] = sy * v
        out[n - 1 - j, n - 1 - i] = sx * sy * v
    return out


def fit_amplitude(g, a=1, b=1, Lx=None, Ly=None):
    """Least-squares A in g = A cos(a pi x/Lx) sin(b pi y/Ly) (Eqs. 14, 17).

    ``g`` is an (n, n) array [j, i]. Returns (A, largest residual / |A|).
    """
    n = g.shape[0]
    Lx = DEVICE["Lx"] if Lx is None else Lx
    Ly = DEVICE["Ly"] if Ly is None else Ly
    c = qubit_centers(n, Lx / n)
    shape = np.zeros_like(g)
    for (i, j), (x, y) in c.items():
        shape[j, i] = np.cos(a * np.pi * x / Lx) * np.sin(b * np.pi * y / Ly)
    ok = np.isfinite(g)
    A = np.sum(g[ok] * shape[ok]) / np.sum(shape[ok] ** 2)
    return A, np.max(np.abs(g[ok] - A * shape[ok])) / abs(A)


# ---------------------------------------------------------------------------
# 7. Port reduced-order model
# ---------------------------------------------------------------------------


class PortROM:
    """A reduced model of the package seen from its ports, built once.

    Every junction or probe enters the finite-element problem only through a
    rank-one term (mu0 1e-3 / L) c c^T. So all four extraction methods need
    only the response of the open structure at its ports, near the band of
    interest. This class captures that response with a block Krylov space

        span{ R, (A - sigma M)^-1 M R, ... },  R = (A - sigma M)^-1 [c_1 ... c_p],

    one sparse LU and ``n_moments`` block solves, then answers every question
    on small dense matrices: eigenmodes with any junction inductors, and the
    impedance matrix over any frequency grid. It is the same idea as the fast
    frequency sweep in commercial solvers (moment matching / Pade).
    """

    def __init__(
        self, fem: MaxwellFEM, ports, f_center, n_moments=6, extra=None, verbose=True
    ):
        start = time.time()
        self.fem = fem
        self.ports = list(ports)
        k0 = 2 * np.pi * f_center / C0_MM
        self.sigma = k0**2
        lu = fem.factor(self.sigma)
        C = np.stack([fem.port_vector(p) for p in self.ports], axis=1)
        blocks = (
            []
            if extra is None
            else [np.asarray(extra, dtype=float).reshape(fem.n_dofs, -1)]
        )
        Q = np.zeros((fem.n_dofs, 0))
        R = lu.solve(C)
        for _ in range(n_moments):
            if Q.shape[1]:
                R = R - Q @ (Q.T @ R)
                R = R - Q @ (Q.T @ R)
            Qn, s, _ = la.svd(R, full_matrices=False)
            keep = s > 1e-10 * (s[0] if len(s) else 1.0)
            Qn = Qn[:, keep]
            Q = np.hstack([Q, Qn])
            R = lu.solve(fem.Mf @ Qn)
        for E in blocks:
            E = E - Q @ (Q.T @ E)
            E = E - Q @ (Q.T @ E)
            Qn, s, _ = la.svd(E, full_matrices=False)
            Q = np.hstack([Q, Qn[:, s > 1e-10 * s[0]]])
        self.Q = Q
        self.K = Q.T @ (fem.Kf @ Q)
        self.M = Q.T @ (fem.Mf @ Q)
        self.C = Q.T @ C
        self.build_time = time.time() - start
        if verbose:
            print(
                f"port ROM: {len(self.ports)} ports, {Q.shape[1]} basis vectors, built in {self.build_time:.0f} s"
            )

    def _index(self, name):
        return self.ports.index(name)

    def _stiffness(self, inductors):
        A = self.K.copy()
        for name, L in (inductors or {}).items():
            c = self.C[:, self._index(name)]
            A += MaxwellFEM.alpha(L) * np.outer(c, c)
        return A

    def eigenmodes(self, inductors=None, fmin=0.0, fmax=np.inf):
        """(frequencies in Hz, port voltages (n_modes, n_ports) for 1 J)."""
        A = self._stiffness(inductors)
        vals, Y = la.eigh(A, self.M)
        f = np.sqrt(np.clip(vals, 0, None)) * C0_MM / (2 * np.pi)
        sel = (f > fmin) & (f < fmax)
        Y = Y[:, sel]  # M-orthonormal: y^T M y = 1
        # scale to 1 J in the whole package: energy = n_sym 0.5 eps0 1e-3 y^T M y
        scale = 1 / np.sqrt(self.fem.pmesh.n_sym * 0.5 * EPS0 * 1e-3)
        V = (self.C.T @ Y).T * scale
        # fix each eigenvector's arbitrary sign: its largest port voltage is positive
        V *= np.sign(V[np.arange(len(V)), np.argmax(np.abs(V), axis=1)])[:, None]
        return f[sel], V

    def modes(self, inductors=None, fmin=0.0, fmax=np.inf):
        """Full-field :class:`Mode` objects (1 J each) for the reduced eigenmodes in [fmin, fmax]."""
        A = self._stiffness(inductors)
        vals, Y = la.eigh(A, self.M)
        f = np.sqrt(np.clip(vals, 0, None)) * C0_MM / (2 * np.pi)
        out = []
        for k in np.nonzero((f > fmin) & (f < fmax))[0]:
            u = self.fem._full(self.Q @ Y[:, k])
            u /= np.sqrt(self.fem.energy(u))
            u *= self.fem._sign(u)
            out.append(Mode(f[k], u, self.fem))
        return out

    def impedance(self, freqs, inductors=None, ports=None):
        """Impedance matrix Z(f) = j w mu0 1e-3 c^T (A - k0^2 M)^-1 c (ohms).

        ``inductors`` shunt the listed ports; ``ports`` picks the rows and
        columns to return (default: all ports of the model).
        """
        A = self._stiffness(inductors)
        idx = [self._index(p) for p in (ports or self.ports)]
        # Diagonalize once: (A - k^2 M)^-1 = sum_k y_k y_k^T / (lambda_k - k^2)
        lam, Y = la.eigh(A, self.M)
        B = Y.T @ self.C[:, idx]  # (r, p) port projections of every reduced mode
        f = np.atleast_1d(np.asarray(freqs, dtype=float))
        k2 = (2 * np.pi * f / C0_MM) ** 2
        H = np.einsum("kp,fk,kq->fpq", B, 1.0 / (lam[None, :] - k2[:, None]), B)
        return 1j * (2 * np.pi * f * MU0 * 1e-3)[:, None, None] * H


# ---------------------------------------------------------------------------
# 8. Electrostatics: capacitance matrix and dipole moment
# ---------------------------------------------------------------------------


class Electrostatics:
    """Maxwell capacitance matrix of all paddles, with one LU.

    Each paddle is a perfect conductor, so its nodes share one potential:
    they collapse to a single unknown. Package walls are grounded; cut faces
    of a symmetry-reduced mesh are left free (images at equal potential,
    irrelevant for the local capacitance of a qubit). With K the stiffness
    matrix of div(eps grad phi) = 0, the capacitance matrix is the Schur
    complement of K onto the paddle unknowns.
    """

    def __init__(self, pmesh: PackageMesh, order=2):
        from skfem import Basis, BilinearForm, ElementTetP1, ElementTetP2, MeshTet, asm
        from skfem.helpers import dot, grad

        start = time.time()
        mesh = MeshTet(pmesh.p, pmesh.t)
        element = ElementTetP2() if order == 2 else ElementTetP1()
        basis = Basis(mesh, element)

        @BilinearForm
        def laplace(u, v, w):
            return dot(grad(u), grad(v))

        K = asm(
            laplace, Basis(mesh, element, elements=np.nonzero(pmesh.material == 0)[0])
        )
        si = np.nonzero(pmesh.material == 1)[0]
        if len(si):
            K = K + pmesh.package.eps_r * asm(
                laplace, Basis(mesh, element, elements=si)
            )
        K = (EPS0 * 1e-3 * K).tocsr()  # farads

        x0, x1, y0, y1 = pmesh.bounds
        pkg = pmesh.package
        bf = mesh.boundary_facets()
        fc = mesh.p[:, mesh.facets[:, bf]].mean(axis=1)
        cut = np.zeros(len(bf), bool)
        if x1 < pkg.Lx - 1e-9:
            cut |= np.isclose(fc[0], x1)
        if y1 < pkg.Ly - 1e-9:
            cut |= np.isclose(fc[1], y1)
        ground = basis.get_dofs(facets=bf[~cut]).flatten()
        self.names = list(pmesh.metal_tris)
        owner = -np.ones(basis.N, dtype=np.int64)
        for k, name in enumerate(self.names):
            owner[
                basis.get_dofs(
                    facets=_facet_index(mesh, pmesh.metal_tris[name])
                ).flatten()
            ] = k
        owner[ground] = -2
        interior = np.nonzero(owner == -1)[0]
        nm = len(self.names)
        P = sp.csr_matrix(
            (
                np.ones(np.sum(owner >= 0)),
                (np.nonzero(owner >= 0)[0], owner[owner >= 0]),
            ),
            shape=(basis.N, nm),
        )
        Kii = K[interior][:, interior]
        Kim = (K[interior] @ P).toarray()
        Kmm = (P.T @ K @ P).toarray()
        lu = _Factor(Kii)
        X = lu.solve(Kim)  # interior response to 1 V on each paddle
        self.C = Kmm - Kim.T @ X
        self.C = (self.C + self.C.T) / 2
        self._K, self._P, self._X, self._interior, self._owner = (
            K,
            P,
            X,
            interior,
            owner,
        )
        self.doflocs = basis.doflocs
        self._basis, self._mesh, self._p, self._t, self._order = (
            basis,
            mesh,
            pmesh.p,
            pmesh.t,
            order,
        )
        self.time = time.time() - start

    def index(self, name):
        return self.names.index(name)

    def port_capacitance(self, a, b):
        """Capacitance across the port between paddles a and b, with every
        other paddle floating (zero net charge): 1 / (e_ab^T C^-1 e_ab)."""
        e = np.zeros(len(self.names))
        e[self.index(a)], e[self.index(b)] = 1.0, -1.0
        return 1.0 / (e @ la.solve(self.C, e))

    def charges(self, a, b, energy=1.0):
        """Nodal charges (C) on all paddles for the qubit mode of port (a, b).

        Returns (locations (3, k) in mm, charges (k,)). Charges +q on a and -q
        on b with (1/2) C V^2 = ``energy``; every other paddle floats.
        """
        Cp = self.port_capacitance(a, b)
        q = Cp * np.sqrt(2 * energy / Cp)
        Q = np.zeros(len(self.names))
        Q[self.index(a)], Q[self.index(b)] = q, -q
        Vm = la.solve(self.C, Q)
        phi = self._P @ Vm
        phi[self._interior] = -self._X @ Vm
        r = self._K @ phi
        on_metal = self._owner >= 0
        return self.doflocs[:, on_metal], r[on_metal]

    def potential(self, a, b, points, energy=1.0):
        """Electrostatic potential (V) at points (3, n) in mm, for the qubit mode
        of port (a, b) with the given energy (charges +q, -q; others floating)."""
        Cp = self.port_capacitance(a, b)
        q = Cp * np.sqrt(2 * energy / Cp)
        Q = np.zeros(len(self.names))
        Q[self.index(a)], Q[self.index(b)] = q, -q
        Vm = la.solve(self.C, Q)
        phi = self._P @ Vm
        phi[self._interior] = -self._X @ Vm
        if not hasattr(self, "_locator"):
            self._locator = _Locator(self._p, self._t)
            self._t2e = _element_edges(self._mesh, self._t)
        elems, lam = self._locator.locate(points)
        t = self._t[:, elems]
        nodal = self._basis.nodal_dofs[0]
        out = np.zeros(len(elems))
        for i in range(4):
            out += phi[nodal[t[i]]] * lam[i] * (2 * lam[i] - 1)
        if self._order == 2:
            edge = self._basis.edge_dofs[0]
            for k, (a, b) in enumerate(_LOCAL_EDGES):
                out += phi[edge[self._t2e[elems, k]]] * 4 * lam[a] * lam[b]
        else:
            out = sum(phi[nodal[t[i]]] * lam[i] for i in range(4))
        return out

    def dipole(self, a, b, energy=1.0):
        """Dipole moment p (C m, 3-vector) of the qubit mode with the given energy.

        Charges +q on a and -q on b, all other paddles floating; the nodal
        charges are the reactions K phi on the paddle nodes.
        """
        loc, q = self.charges(a, b, energy)
        return (loc * 1e-3) @ q
