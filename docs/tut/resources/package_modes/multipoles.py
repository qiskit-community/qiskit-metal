"""Multipole moments of a qubit and the fields it couples to: helpers for tutorial 4.46.

A transmon couples to a package mode through its charge and its current. Seen
from far away, both are a short list of moments:

    charge     p_i = sum q r_i      S_ij = sum q r_i r_j      O_ijk = sum q r_i r_j r_k
    current    mtilde = (1/2) int r x Ktilde dA      Mtilde_ij = int r_i (r x Ktilde)_j dA

(``q`` are the charges on the paddles and ``Ktilde`` is the charge-displacement
sheet current, ``div Ktilde = -sigma``, ``int Ktilde dA = p``). In the
multipolar (Power-Zienau-Woolley) form the coupling energy of the qubit with
the package field is an expansion in the field and its derivatives at the
qubit,

    U = p.E + (1/2) S_ij d_i E_j + (1/6) O_ijk d_i d_j E_k + ...        (electric)
      + mtilde.(curl E) + (1/3) Mtilde_ij d_i (curl E)_j + ...           (magnetic)

with both modes normalized to 1 J, so that g/2pi = f U / 4 on resonance. For a
planar source only the in-plane E and the normal component of ``curl E`` (= omega B_z)
enter. This module computes the moments, the fields at the qubit and the terms
of the series.

Sections, in the order tutorial 4.46 uses them:

1. the source: lumping the electrostatic charges, moments (``pad_p1_charges``,
   ``own_charges``, ``moments``), the sheet current (``SheetCurrent``);
2. the field, analytically: LSM modes at any point (``lsm_fields``), the potential of
   the in-plane field and its derivatives (``lsm_potential``, ``phi_derivs``);
3. the field, in the finite-element solution: the mode without the paddles
   (``bare_mode``), its curl (``curl_E``), polynomial fits (``disc_fit``);
4. the coupling: the exact ray integral and the series (``ray_coupling``,
   ``multipole_terms``, ``loop_circulation``).

Units: positions of points in millimetres (the mesh), moments, fields and
energies in SI.  Run ``selftest()`` for the checks that need no mesh.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass

import numpy as np

from qiskit_metal.analyses.em.package_modes import EPS0, MU0
from qiskit_metal.analyses.fem import solver as _fem

_GL_X, _GL_W = np.polynomial.legendre.leggauss(12)
_LAM, _WLAM = (_GL_X + 1) / 2, _GL_W / 2  # Gauss-Legendre on [0, 1]


# ---------------------------------------------------------------------------
# 1. The source: charges, moments, current
# ---------------------------------------------------------------------------


def pad_p1_charges(loc, q, pmesh, name, order=2):
    """Lump second-order nodal charges onto the first-order triangles of one paddle.

    ``Electrostatics(order=2).charges`` returns the charge each second-order node
    carries, vertices and edge midpoints. A first-order hat function is the vertex
    function plus half of each of its edge-midpoint functions, so the charge a
    vertex carries on the paddle's triangles is its own plus half of every
    neighboring midpoint's. The total charge and the dipole moment are unchanged.
    With ``order=1`` the charges are already on the vertices.

    Returns ``(xy, r, tri)``: vertex positions (2, n) in mm, charges (n,) in C and
    the triangles (k, 3) as indices into the vertices.
    """
    from scipy.spatial import cKDTree

    tris = pmesh.metal_tris[name]
    nodes, inv = np.unique(tris, return_inverse=True)
    tri = inv.reshape(-1, 3)
    xyz = pmesh.p[:, nodes]
    tree = cKDTree(loc.T)
    d, idx = tree.query(xyz.T)
    assert d.max() < 1e-7, "paddle vertex without a second-order node"
    r = np.array(q[idx], dtype=float)
    edges = np.unique(
        np.sort(np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [0, 2]]]), axis=1),
        axis=0,
    )
    if order == 2:
        mid = 0.5 * (xyz[:, edges[:, 0]] + xyz[:, edges[:, 1]])
        d, idx = tree.query(mid.T)
        assert d.max() < 1e-7, "paddle edge without a midpoint node"
        np.add.at(r, edges[:, 0], 0.5 * q[idx])
        np.add.at(r, edges[:, 1], 0.5 * q[idx])
    return xyz[:2], r, tri


def lumped_density(xy, r, tri):
    """Surface charge density (C/m^2) at the vertices of a paddle's triangles: each
    vertex's charge over a third of the area of the triangles around it. ``xy`` in m."""
    area = np.zeros(xy.shape[1])
    d1, d2 = xy[:, tri[:, 1]] - xy[:, tri[:, 0]], xy[:, tri[:, 2]] - xy[:, tri[:, 0]]
    a = 0.5 * np.abs(d1[0] * d2[1] - d1[1] * d2[0])
    for k in range(3):
        np.add.at(area, tri[:, k], a / 3)
    return r / area


def own_charges(loc, q, center, half=(0.65, 0.55)):
    """The charges of one qubit's own paddles: nodes inside a box around its center.

    ``center`` and ``half`` in mm. Returns positions relative to the center
    (2, k) in metres and the charges (k,) in C.
    """
    c = np.asarray(center, dtype=float)
    rel = loc[:2] - c[:, None]
    own = (np.abs(rel[0]) < half[0]) & (np.abs(rel[1]) < half[1])
    return rel[:, own] * 1e-3, np.asarray(q)[own]


def moments(r, q):
    """Charge multipole moments about the origin, SI.

    ``r`` (2, k) in m, ``q`` (k,) in C. Returns a dict: net charge ``Q``, dipole
    ``p`` (2,), Cartesian quadrupole ``S`` (2, 2) and octupole ``O`` (2, 2, 2) of
    ``sum q r..r``, and the traceless quadrupole ``Qj`` = 3 S - delta tr S of
    Jackson's convention (in-plane block).
    """
    r = np.asarray(r, dtype=float)
    q = np.asarray(q, dtype=float)
    S = np.einsum("ik,jk,k->ij", r, r, q)
    return dict(
        Q=q.sum(),
        p=r @ q,
        S=S,
        O=np.einsum("ik,jk,lk,k->ijl", r, r, r, q),
        Qj=3 * S - np.eye(2) * np.trace(S),
    )


def shift_origin(mom, d):
    """Moments about a new origin ``d`` (m): for a neutral source S -> S - d p - p d."""
    d = np.asarray(d, dtype=float)
    p, S = mom["p"], mom["S"]
    return dict(p=p, S=S - np.outer(d, p) - np.outer(p, d))


def dipole_center(mom):
    """Shift d (m) of the origin that removes S_xx and S_xy of a source whose dipole points along x.

    Under r -> r - d a neutral source has S -> S - d p - p d (:func:`shift_origin`), so with
    p = (p_x, 0): S_xx -> S_xx - 2 d_x p_x and S_xy -> S_xy - d_y p_x. What cannot be shifted
    away is S_yy: the quadrupole of the source about its own dipole center.
    """
    p, S = mom["p"], mom["S"]
    return np.array([S[0, 0] / (2 * p[0]), S[0, 1] / p[0]])


@dataclass
class SheetCurrent:
    """The charge-displacement current of a qubit: sheets on its paddles and a junction line.

    ``div K = -sigma`` on the paddles, ``K`` flows from the junction terminal of
    the negative paddle to that of the positive one through a line element, and
    ``int K dA = p``. Built by :func:`sheet_current`.

    X, K, w: quadrature points (2, n) in m, K (2, n) in C/m and weights (n,) in
    m^2 on the paddles; ``lines``: junction line elements (r_from, r_to, Q) with
    positions (2,) in m and the charge Q (C) that crosses them.
    """

    X: np.ndarray
    K: np.ndarray
    w: np.ndarray
    lines: list

    def shifted(self, d):
        """The same current with positions measured from a new origin at ``d`` (m, relative to the old one)."""
        d = np.asarray(d, dtype=float)
        return SheetCurrent(
            self.X - d[:, None],
            self.K,
            self.w,
            [(a - d, b - d, Q) for a, b, Q in self.lines],
        )

    def dipole(self):
        """int K dA, including the junction line: equals p."""
        out = (self.K * self.w).sum(axis=1)
        for a, b, Q in self.lines:
            out = out + Q * (b - a)
        return out

    def m(self):
        """mtilde_z = (1/2) int (x K_y - y K_x) dA, C m^2."""
        out = 0.5 * np.sum((self.X[0] * self.K[1] - self.X[1] * self.K[0]) * self.w)
        for a, b, Q in self.lines:
            out += 0.5 * Q * (a[0] * (b - a)[1] - a[1] * (b - a)[0])
        return out

    def M(self):
        """Mtilde_iz = int r_i (x K_y - y K_x) dA for i = x, y, in C m^3."""
        circ = self.X[0] * self.K[1] - self.X[1] * self.K[0]
        out = np.array([np.sum(self.X[i] * circ * self.w) for i in (0, 1)])
        for a, b, Q in self.lines:
            cross = a[0] * (b - a)[1] - a[1] * (b - a)[0]
            out += Q * cross * (a + (b - a) / 2)
        return out

    def overlap(self, E_fn, c=(0.0, 0.0)):
        """Velocity-gauge coupling int K.E dA for the in-plane field E_fn(x_mm, y_mm)."""
        c = np.asarray(c, dtype=float)
        Ex, Ey = E_fn(c[0] + 1e3 * self.X[0], c[1] + 1e3 * self.X[1])
        out = np.sum((self.K[0] * Ex + self.K[1] * Ey) * self.w)
        for a, b, Q in self.lines:
            pts = a[:, None] + _LAM[None, :] * (b - a)[:, None]
            ex, ey = E_fn(c[0] + 1e3 * pts[0], c[1] + 1e3 * pts[1])
            out += Q * np.sum(_WLAM * (ex * (b - a)[0] + ey * (b - a)[1]))
        return out

    def bz(self, pts, z, omega, images=()):
        """Normal magnetic field (T, amplitude) of the model current at height ``z``.

        Biot-Savart for the current omega * K (the quasi-static limit: the qubit is
        1 mm across, the wavelength tens of mm). ``pts`` (2, m) in m relative to the
        qubit center, ``z`` (m) above the sheet. ``images`` lists (height, sign) of
        mirror sheets, e.g. a perfect-conductor floor at depth d below the sheet
        is ``(-2 d, -1)``. The junction line is a source too.
        """
        pts = np.asarray(pts, dtype=float)

        def sheet(zz, sign):
            Rx = pts[0][:, None] - self.X[0][None, :]
            Ry = pts[1][:, None] - self.X[1][None, :]
            R3 = (Rx**2 + Ry**2 + zz**2) ** 1.5
            val = ((self.K[0] * Ry - self.K[1] * Rx) * self.w[None, :] / R3).sum(axis=1)
            for a, b, Q in self.lines:
                s = _LAM[None, :]
                x = a[0] + s * (b - a)[0]
                y = a[1] + s * (b - a)[1]
                Rx = pts[0][:, None] - x
                Ry = pts[1][:, None] - y
                R3 = (Rx**2 + Ry**2 + zz**2) ** 1.5
                val += Q * (
                    ((b - a)[0] * Ry - (b - a)[1] * Rx) / R3 * _WLAM[None, :]
                ).sum(axis=1)
            return sign * val

        out = sheet(z, 1.0) + sum(sheet(z - zi, s) for zi, s in images)
        return MU0 * omega / (4 * np.pi) * out


def sheet_current(pads, junction):
    """The charge-displacement current of a two-paddle qubit.

    On each paddle ``K = -grad psi`` with ``-laplace psi = div K = -sigma``: a
    two-dimensional Poisson problem on the paddle's first-order triangles,
    insulating edges and a point sink at the junction terminal, where the whole
    charge of the paddle leaves (the resistive-sheet limit: the current takes the
    path of least dissipation). It is one model among several -- a superconducting
    sheet would add a divergence-free screening current -- but it respects charge
    conservation and the symmetry of the layout.

    Args:
        pads: two tuples ``(xy, r, tri)`` as from :func:`pad_p1_charges`, the first
            paddle the positive one; ``xy`` in metres relative to the qubit center.
        junction: (point_on_pad0, point_on_pad1), each (2,) in m: where the
            junction line touches each paddle.
    """
    from skfem import Basis, BilinearForm, ElementTriP1, MeshTri, asm
    from skfem.helpers import dot, grad
    import scipy.sparse.linalg as sla

    X, K, W, ends, Qs = [], [], [], [], []
    for (xy, r, tri), jpt in zip(pads, junction):
        mesh = MeshTri(
            np.ascontiguousarray(xy), np.ascontiguousarray(np.asarray(tri).T)
        )
        basis = Basis(mesh, ElementTriP1())
        stiff = asm(BilinearForm(lambda u, v, w: dot(grad(u), grad(v))), basis).tocsr()
        term = int(np.argmin(np.hypot(xy[0] - jpt[0], xy[1] - jpt[1])))
        Qpad = r.sum()
        # weak form: int grad psi.grad v = -int sigma v + (outflow at the terminal) v(term),
        # and the whole charge of the paddle flows into it
        rhs = -np.array(r, dtype=float)
        rhs[term] += Qpad
        A = stiff.tolil()
        A[0, :] = 0
        A[0, 0] = 1  # psi is defined up to a constant
        rhs[0] = 0
        psi = sla.spsolve(A.tocsr(), rhs)
        gr = basis.interpolate(psi).grad  # (2, nel, nqp)
        X.append(basis.global_coordinates().value.reshape(2, -1))
        K.append((-gr).reshape(2, -1))
        W.append(basis.dx.reshape(-1))
        ends.append(np.array([xy[0][term], xy[1][term]]))
        Qs.append(Qpad)
    # the junction carries the positive paddle's charge from the negative paddle's terminal
    line = (ends[1], ends[0], Qs[0])
    return SheetCurrent(np.hstack(X), np.hstack(K), np.concatenate(W), [line])


# ---------------------------------------------------------------------------
# 2. The field, analytically
# ---------------------------------------------------------------------------


def lsm_eps(mode, z):
    """Permittivity (F/m) at height z (mm): silicon below the slab surface, vacuum above."""
    return EPS0 * np.where(np.asarray(z, dtype=float) * 1e-3 <= mode.t, mode.eps_r, 1.0)


def lsm_fields(mode, x, y, z):
    """E (V/m) and B (T, amplitude) of an analytic LSM_ab0 mode at points (mm).

    The mode is TM in z: E_z = E_z(z) sin(kx x) sin(ky y), the in-plane field
    follows from E_t = grad_t(d_z E_z)/gamma^2, and B = (curl E)/omega is purely
    in-plane, B_t = -mu0 omega eps(z) (zhat x grad_t E_z)/gamma^2; B_z = 0. B is
    in quadrature with E; its sign is a phase convention. Normalized to 1 J.
    Returns arrays of shape (3,) + broadcast shape.
    """
    x, y, z = np.broadcast_arrays(*(np.asarray(v, dtype=float) for v in (x, y, z)))
    kx, ky = mode.a * np.pi / mode.Lx, mode.b * np.pi / mode.Ly
    zz = z * 1e-3
    xx, yy = x * 1e-3, y * 1e-3
    si = zz <= mode.t
    Ez = mode.Ez(zz)
    dz_si = -mode.E0z * mode.kz_si * np.sin(mode.kz_si * zz)
    dz_air = (
        -mode.eps_r
        * mode.E0z
        * np.cos(mode.kz_si * mode.t)
        / np.cosh(mode.kz_air * (mode.Lz - mode.t))
        * mode.kz_air
        * np.sinh(mode.kz_air * (mode.Lz - zz))
    )
    dEz = np.where(si, dz_si, dz_air)
    s_x, c_x = np.sin(kx * xx), np.cos(kx * xx)
    s_y, c_y = np.sin(ky * yy), np.cos(ky * yy)
    g2 = mode.gamma**2
    E = np.stack([dEz / g2 * kx * c_x * s_y, dEz / g2 * ky * s_x * c_y, Ez * s_x * s_y])
    w = 2 * np.pi * mode.f
    eps = EPS0 * np.where(si, mode.eps_r, 1.0)
    B = np.stack(
        [
            MU0 * w * eps / g2 * Ez * ky * s_x * c_y,
            -MU0 * w * eps / g2 * Ez * kx * c_x * s_y,
            np.zeros_like(Ez),
        ]
    )
    return E, B


def lsm_inplane(mode):
    """E_fn(x_mm, y_mm) -> (E_x, E_y) in V/m at the slab surface, the planar source's field."""

    def E_fn(x, y):
        E, _ = lsm_fields(mode, x, y, mode.t * 1e3)
        return E[0], E[1]

    return E_fn


def lsm_potential(mode, x, y):
    """Potential (V) of the in-plane field at the slab surface, E_t = -grad_t Phi.

    Phi = (E0x Lx / pi) sin(kx x) sin(ky y): the in-plane field is curl-free
    because B_z = 0. Positions in mm.
    """
    kx, ky = mode.a * np.pi / mode.Lx, mode.b * np.pi / mode.Ly
    phi0 = mode.E0x * mode.Lx / np.pi
    return phi0 * np.sin(kx * 1e-3 * np.asarray(x)) * np.sin(ky * 1e-3 * np.asarray(y))


def phi_derivs(mode, x, y, n):
    """The n-th derivative tensor of Phi (V/m^n), shape (2,)*n, at (x, y) mm.

    sin(u) sin(v) = [cos(u - v) - cos(u + v)]/2, and each derivative of a cosine
    of a linear phase multiplies by its wavevector component and shifts the phase
    by pi/2.
    """
    kx, ky = mode.a * np.pi / mode.Lx, mode.b * np.pi / mode.Ly
    phi0 = mode.E0x * mode.Lx / np.pi
    X, Y = 1e-3 * np.asarray(x), 1e-3 * np.asarray(y)
    out = np.zeros((2,) * n)
    for kv, sign in (((kx, -ky), +0.5), ((kx, ky), -0.5)):
        u = kv[0] * X + kv[1] * Y
        amp = phi0 * sign * math.cos(u + n * math.pi / 2)
        t = np.array(1.0)
        for _ in range(n):
            t = np.multiply.outer(t, np.array(kv))
        out = out + amp * t
    return out


# ---------------------------------------------------------------------------
# 3. The field, in the finite-element solution
# ---------------------------------------------------------------------------


def bare_mode(pmesh, cuts, f_guess):
    """The package mode on a mesh refined around the paddles, with the paddles removed.

    Takes the mesh of ``pm.mesh_package`` (fine along the paddle edges), drops the
    metal and the junctions from it and solves ``MaxwellFEM``: the mode of the
    empty package, sampled finely at every qubit. Returns ``(fem, mode)``.
    """
    bare = dataclasses.replace(pmesh, metal_tris={}, junction_segs={})
    fem = _fem.MaxwellFEM(bare, cuts=cuts)
    (mode,) = fem.eigenmodes(f_guess)
    return fem, mode


def curl_E(fem, u, pts):
    """(curl E) at points (3, n) in mm, V/m^2, from the edge coefficients ``u``.

    Inside one tetrahedron the Whitney function of the edge (a, b) has curl
    2 grad(lambda_a) x grad(lambda_b), constant per element; B = (curl E)/omega.
    """
    if not hasattr(fem, "_locator"):
        fem._locator = _fem._Locator(fem.pmesh.p, fem.pmesh.t)
        fem._t2e = _fem._element_edges(fem.mesh, fem.pmesh.t)
    el, _ = fem._locator.locate(pts)
    g = fem._locator.gradients(el)
    t = fem.pmesh.t[:, el]
    C = np.zeros((len(el), 3))
    for k, (a, b) in enumerate(_fem._LOCAL_EDGES):
        s = np.where(t[a] < t[b], 1.0, -1.0)[:, None]
        C += s * 2 * np.cross(g[:, a], g[:, b]) * u[fem._t2e[el, k]][:, None]
    return 1e6 * C.T


def plane_field(mode, z):
    """E_fn(x_mm, y_mm) -> (E_x, E_y) from a finite-element mode at height z (mm)."""

    def E_fn(x, y):
        x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
        pts = np.vstack([x.ravel(), y.ravel(), np.full(x.size, float(z))])
        E = mode.field(pts)
        return E[0].reshape(x.shape), E[1].reshape(x.shape)

    return E_fn


@dataclass
class DiscFit:
    """A quadratic fit of k fields over a disc: value (k,), grad (k, 2), hess (k, 2, 2).

    Derivatives per metre (positions were in mm).
    """

    value: np.ndarray
    grad: np.ndarray
    hess: np.ndarray
    scatter: np.ndarray  # rms of the residual, per field


def disc_fit(F, c, R=0.8, N=2000, rmin=0.0, deg=2, offset=(0.0, 0.0)):
    """Least-squares polynomial of F(pts) over a disc of radius R (mm), expanded about c.

    ``F(pts)`` takes points (3, N) in mm and returns (k, N). A finite-element field
    scatters by a percent or so from one element to the next, so the value at the
    center point is not the value of the underlying field; a fit over a disc of
    several hundred elements is. With ``rmin > 0`` the fit uses the annulus
    rmin < r < R (to leave a metal paddle out of it). ``deg`` is 2 (the default) or 3;
    ``offset`` (mm) moves the sampled disc away from c while the polynomial is still
    expanded about c, which tests how much the answer depends on where the fit looked.
    Returns a :class:`DiscFit` (value, gradient and Hessian at c).
    """
    k_ = np.arange(N) + 0.5
    rad = np.sqrt(rmin**2 + (R**2 - rmin**2) * k_ / N)
    ang = k_ * np.pi * (3 - np.sqrt(5))  # a Fibonacci spiral: even coverage, no seed
    dx, dy = rad * np.cos(ang) + offset[0], rad * np.sin(ang) + offset[1]
    pts = np.vstack([c[0] + dx, c[1] + dy, np.full(N, c[2])])
    Fv = np.atleast_2d(F(pts))
    cols = [np.ones(N), dx, dy, dx**2, dx * dy, dy**2]
    if deg == 3:
        cols += [dx**3, dx**2 * dy, dx * dy**2, dy**3]
    basis = np.vstack(cols).T
    coef = np.linalg.lstsq(basis, Fv.T, rcond=None)[0]  # (n_terms, k)
    resid = Fv.T - basis @ coef
    grad = 1e3 * coef[1:3].T
    hess = np.empty((Fv.shape[0], 2, 2))
    hess[:, 0, 0] = 2e6 * coef[3]
    hess[:, 1, 1] = 2e6 * coef[5]
    hess[:, 0, 1] = hess[:, 1, 0] = 1e6 * coef[4]
    return DiscFit(coef[0], grad, hess, resid.std(axis=0))


# ---------------------------------------------------------------------------
# 4. The coupling
# ---------------------------------------------------------------------------


def ray_coupling(E_fn, c, r, q):
    """Exact multipolar coupling energy U = sum_k q_k int_0^1 r_k.E(c + lambda r_k) dlambda (J).

    Each charge couples along the straight ray from the origin ``c`` (mm) to its
    position; summed over a neutral source this is the dipole term and every
    higher electric multipole, to all orders. ``E_fn(x_mm, y_mm)`` -> (E_x, E_y).
    """
    r = np.asarray(r, dtype=float)
    X = c[0] + 1e3 * np.outer(_LAM, r[0])
    Y = c[1] + 1e3 * np.outer(_LAM, r[1])
    Ex, Ey = E_fn(X, Y)
    return float(np.sum(q * (_WLAM @ (Ex * r[0][None] + Ey * r[1][None]))))


def multipole_terms(mom, mode, c, nmax=3):
    """The electric series U_n, n = 1..nmax, of the analytic in-plane field (J).

    U_n = -(1/n!) M^(n)_{i1..in} d_{i1..in} Phi, with the charge moments M^(1) = p,
    M^(2) = S, M^(3) = O. The sum over all n is the exact coupling.
    """
    Ms = [mom["p"], mom["S"], mom["O"]]
    out = []
    for n in range(1, nmax + 1):
        d = phi_derivs(mode, c[0], c[1], n)
        out.append(-np.sum(Ms[n - 1] * d) / math.factorial(n))
    return np.array(out)


def series_terms(mode, c, r, q, nmax=6):
    """The electric terms U_1 .. U_nmax (J) of the exact coupling in the analytic in-plane field.

    U_n = -(1/n!) sum_k q_k (r_k . grad)^n Phi(c): the n-th order of the Taylor series
    of the potential along each charge's ray, summed over the charges, so U_1 is the
    dipole term, U_2 the quadrupole, U_3 the octupole. For n <= 3 it equals
    :func:`multipole_terms` (the contraction with the moment tensors). The sum over
    all n is :func:`exact_analytic`. Positions ``c`` in mm, ``r`` (2, k) in m.
    """
    kx, ky = mode.a * np.pi / mode.Lx, mode.b * np.pi / mode.Ly
    phi0 = mode.E0x * mode.Lx / np.pi
    X, Y = 1e-3 * c[0], 1e-3 * c[1]
    out = np.zeros(nmax)
    for (k1, k2), sign in (((kx, -ky), +0.5), ((kx, ky), -0.5)):
        u = k1 * X + k2 * Y
        kr = k1 * r[0] + k2 * r[1]
        for n in range(1, nmax + 1):
            out[n - 1] += (
                -sign
                * phi0
                * np.sum(q * kr**n * np.cos(u + n * np.pi / 2))
                / math.factorial(n)
            )
    return out


def g_MHz(f, U):
    """g/2pi (MHz) of a coupling energy U (J) between two modes at 1 J, on resonance at f."""
    return f * np.asarray(U) / 4 / 1e6


def loop_circulation(E_fn, rect, n=24):
    """Counter-clockwise line integral of E_t around a rectangle (x0, x1, y0, y1) in mm, volts.

    By Faraday's law it is omega times the magnetic flux through the loop, so it
    tests ``B_z = 0`` without taking a derivative of a finite-element field.
    """
    x0, x1, y0, y1 = rect
    gx, gw = np.polynomial.legendre.leggauss(n)
    s = (gx + 1) / 2
    w = gw / 2
    out = 0.0
    for (ax, ay), (bx, by) in (
        ((x0, y0), (x1, y0)),
        ((x1, y0), (x1, y1)),
        ((x1, y1), (x0, y1)),
        ((x0, y1), (x0, y0)),
    ):
        X, Y = ax + s * (bx - ax), ay + s * (by - ay)
        Ex, Ey = E_fn(X, Y)
        out += 1e-3 * np.sum(w * (Ex * (bx - ax) + Ey * (by - ay)))
    return float(out)


# ---------------------------------------------------------------------------
# 5. A whole quarter-array, and the numbers that summarize it
# ---------------------------------------------------------------------------


def qubit_center(package, name):
    """Midpoint of a qubit's junction line (mm): the origin of its moments."""
    a, b = package.junctions[name]
    return 0.5 * (np.asarray(a, float) + np.asarray(b, float))


def qubit_sources(es, pmesh, package, qubits, order=2):
    """Moments and sheet current of the qubits ``[(i, j), ...]`` of a package.

    Charges from ``es`` (an :class:`Electrostatics` of ``pmesh``) for the qubit
    mode with +q on the right paddle, kept on the qubit's own paddles. Returns
    ``{(i, j): dict(c, r, q, mom, cur, C)}``: center (mm), charges, moments,
    :class:`SheetCurrent` and the capacitance across the junction.
    """
    out = {}
    for ij in qubits:
        name = "Q_%d_%d" % ij
        right, left = f"{name}.pad_right", f"{name}.pad_left"
        c = qubit_center(package, name)
        loc, q = es.charges(right, left)
        polys = np.vstack([package.metals[right], package.metals[left]])
        half = 0.5 * (polys.max(axis=0) - polys.min(axis=0)) + 0.05
        mid = 0.5 * (polys.max(axis=0) + polys.min(axis=0))
        r, qq = own_charges(loc, q, mid, half)
        r = r - ((c - mid) * 1e-3)[:, None]  # relative to the junction midpoint
        pads, jpts = [], []
        for nm in (right, left):
            xy, rr, tri = pad_p1_charges(loc, q, pmesh, nm, order)
            pads.append(((xy - c[:, None]) * 1e-3, rr, tri))
            ends = [np.asarray(e, float) for e in package.junctions[name]]
            cen = package.metals[nm].mean(axis=0)
            e = min(ends, key=lambda v: np.hypot(*(v - cen)))
            jpts.append((e - c) * 1e-3)
        out[ij] = dict(
            c=c,
            r=r,
            q=qq,
            pads=pads,
            mom=moments(r, qq),
            cur=sheet_current(pads, jpts),
            C=es.port_capacitance(left, right),
        )
    return out


def _fit_set(
    mode, fem, c, z, N, rmin=0.0, R=0.8, with_E=True, deg=2, offset=(0.0, 0.0)
):
    """Disc fit of (E_x, E_y, (curl E)_z) at the plane z around c (mm)."""

    def F(pts):
        rows = []
        if with_E:
            rows.append(mode.field(pts)[:2])
        rows.append(curl_E(fem, mode.u, pts)[2:3])
        return np.vstack(rows)

    return disc_fit(F, (c[0], c[1], z), R=R, N=N, rmin=rmin, deg=deg, offset=offset)


def field_maps(mode, fem, z, n=59, extent=(0.25, 14.75)):
    """E (V/m) and curl E (V/m^2) on an n x n grid of the quarter at height z (mm)."""
    g = np.linspace(extent[0], extent[1], n)
    X, Y = np.meshgrid(g, g)
    pts = np.vstack([X.ravel(), Y.ravel(), np.full(X.size, float(z))])
    return dict(
        x=g,
        E=mode.field(pts).reshape(3, n, n),
        curl=curl_E(fem, mode.u, pts).reshape(3, n, n),
    )


def bare_data(pmesh, cuts, f_guess, an, sources, z, N=2000, maps=False, keep=False):
    """The bare package mode on a mesh: its fits at every qubit, optionally maps.

    ``an`` is the analytic mode (for the comparison), ``sources`` from
    :func:`qubit_sources`. Returns a dict with the frequency ``f``, the
    fits per qubit (E_0, dE[i, j] = d_i E_j, (curl E)_z and its gradient) and, if
    ``keep``, the mode and the solver.
    """
    fem, mode = bare_mode(pmesh, cuts, f_guess)
    fits = {}
    for ij, s in sources.items():
        ft = _fit_set(mode, fem, s["c"], z, N)
        fits[ij] = dict(
            E0=ft.value[:2],
            dE=ft.grad[:2].T,  # dE[i, j] = d_i E_j
            hE=ft.hess[:2],  # hE[k, i, j] = d_i d_j E_k
            cz=ft.value[2],
            gcz=ft.grad[2],
            scatter=ft.scatter,
        )
    E_fn = plane_field(mode, z)
    U_ray = {
        ij: ray_coupling(E_fn, s["c"], s["r"], s["q"]) for ij, s in sources.items()
    }
    out = dict(f=mode.f, n_dofs=fem.n_dofs, fits=fits, an=an, U_ray=U_ray, z=z)
    if maps:
        out["maps"] = field_maps(mode, fem, z)
    if keep:
        out["mode"], out["fem"] = mode, fem
    return out


def dressed_data(pmesh, cuts, f_guess, an, sources, z, N=2000, maps=False, keep=False):
    """The mode with every paddle present and every junction open (the model of 4.44).

    Returns the frequency, the induced-EMF coupling g/2pi (MHz) of every qubit
    (Eq. 11 of the paper: exact to all orders in the multipole expansion, and
    including the loading of the mode by the paddles) and the fit of (curl E)_z over
    the annulus 0.85-1.7 mm around each qubit, outside its own paddles.
    """
    fem = _fem.MaxwellFEM(pmesh, cuts=cuts)
    (mode,) = fem.eigenmodes(f_guess)
    g_emf, fits = {}, {}
    for ij, s in sources.items():
        name = "Q_%d_%d" % ij
        g_emf[ij] = _fem.emf_coupling(mode.f, mode.voltage(name), s["C"]) / 1e6
        ft = _fit_set(mode, fem, s["c"], z, N, rmin=0.85, R=1.7, with_E=False)
        fits[ij] = dict(cz=ft.value[0], gcz=ft.grad[0])
    out = dict(f=mode.f, n_dofs=fem.n_dofs, g_emf=g_emf, fits=fits, z=z)
    if maps:
        out["maps"] = field_maps(mode, fem, z)
    if keep:
        out["mode"], out["fem"] = mode, fem
    return out


def magnetic_terms(cur, cz, gcz):
    """(M1, M2) in J: mtilde (curl E)_z and (1/3) Mtilde_iz d_i (curl E)_z.

    ``cz`` in V/m^2 and ``gcz`` (2,) in V/m^3 at the qubit.
    """
    return cur.m() * cz, np.sum(cur.M() * np.asarray(gcz)) / 3


def exact_analytic(mode, c, r, q):
    """Exact coupling energy (J) of the charges in the analytic in-plane field:
    -sum q [Phi(c + r) - Phi(c)]. Equals the all-orders ray integral."""
    return -np.sum(
        q
        * (
            lsm_potential(mode, c[0] + 1e3 * r[0], c[1] + 1e3 * r[1])
            - lsm_potential(mode, c[0], c[1])
        )
    )


def terms_per_qubit(src, bare, dressed=None):
    """All coupling terms of every qubit for one mode, as arrays [j, i] of g/2pi in MHz.

    Keys: ``E1`` (dipole, finite-element field), ``E1a`` (dipole, analytic field), ``E2``
    (quadrupole, FE field), ``E3`` (octupole, analytic), ``E3fe`` (octupole from the second
    derivatives of the FE field: noisy), ``exact_a`` (all electric
    orders, analytic), ``exact_fe`` (ray integral in the FE field), ``M1``, ``M2`` (bare
    FE field), ``M1d``, ``M2d`` (with the paddles present), ``emf`` (induced EMF).
    """
    an, f = bare["an"], bare["f"]
    names = (
        "E1",
        "E1a",
        "E2",
        "E3",
        "E3fe",
        "exact_a",
        "exact_fe",
        "M1",
        "M2",
        "M1d",
        "M2d",
        "emf",
    )
    n = 1 + max(max(ij) for ij in src)
    out = {k: np.full((n, n), np.nan) for k in names}
    if "U_ray" not in bare:  # the mode is still at hand
        E_fe = plane_field(bare["mode"], bare["z"])
        bare["U_ray"] = {
            ij: ray_coupling(E_fe, s["c"], s["r"], s["q"]) for ij, s in src.items()
        }
    for (i, j), s in src.items():
        ft = bare["fits"][(i, j)]
        m, c = s["mom"], s["c"]
        out["E1"][j, i] = g_MHz(f, m["p"] @ ft["E0"])
        out["E2"][j, i] = g_MHz(f, 0.5 * np.sum(m["S"] * ft["dE"]))
        out["E3fe"][j, i] = g_MHz(f, np.einsum("ijk,kij->", m["O"], ft["hE"]) / 6)
        t = multipole_terms(m, an, c, 3)
        out["E1a"][j, i], out["E3"][j, i] = g_MHz(f, t[0]), g_MHz(f, t[2])
        out["exact_a"][j, i] = g_MHz(f, exact_analytic(an, c, s["r"], s["q"]))
        out["exact_fe"][j, i] = g_MHz(f, bare["U_ray"][(i, j)])
        M1, M2 = magnetic_terms(s["cur"], ft["cz"], ft["gcz"])
        out["M1"][j, i], out["M2"][j, i] = g_MHz(f, M1), g_MHz(f, M2)
        if dressed is not None:
            fd = dressed["fits"][(i, j)]
            M1, M2 = magnetic_terms(s["cur"], fd["cz"], fd["gcz"])
            out["M1d"][j, i], out["M2d"][j, i] = g_MHz(f, M1), g_MHz(f, M2)
            out["emf"][j, i] = dressed["g_emf"][(i, j)]
    return out


#: estimator variants used to measure how much a number depends on the choices of the polynomial fit
BARE_VARIANTS = (
    dict(R=0.8, N=2000, deg=2, offset=(0.0, 0.0)),  # the default
    dict(R=0.5, N=2000, deg=2, offset=(0.0, 0.0)),
    dict(R=1.1, N=2000, deg=2, offset=(0.0, 0.0)),
    dict(R=0.8, N=1000, deg=2, offset=(0.0, 0.0)),
    dict(R=0.8, N=4000, deg=2, offset=(0.0, 0.0)),
    dict(R=1.1, N=3000, deg=3, offset=(0.0, 0.0)),
    dict(R=0.8, N=2000, deg=2, offset=(0.15, 0.0)),
    dict(R=0.8, N=2000, deg=2, offset=(-0.15, 0.0)),
    dict(R=0.8, N=2000, deg=2, offset=(0.0, 0.15)),
    dict(R=0.8, N=2000, deg=2, offset=(0.0, -0.15)),
)
DRESSED_VARIANTS = (
    dict(rmin=0.85, R=1.7, N=2000),
    dict(rmin=0.7, R=1.5, N=2000),
    dict(rmin=1.0, R=2.0, N=2000),
    dict(rmin=0.85, R=1.4, N=2000),
    dict(rmin=0.85, R=1.7, N=1000),
)


def fit_variants(bare, dressed, src, z):
    """Terms of every qubit recomputed with different polynomial fits (radius, number of
    points, degree, offset of the disc): the scatter measures the noise of the *estimator*.

    ``bare`` and ``dressed`` are :func:`bare_data` / :func:`dressed_data` results computed
    with ``keep=True``. Returns {term: array (n_variants, n, n)} of g/2pi in MHz for
    ``E1``, ``E2``, ``E3fe``, ``M`` (= M1 + M2, bare) and ``Md`` (dressed).
    """
    n = 1 + max(max(ij) for ij in src)
    f = bare["f"]
    out = {k: [] for k in ("E1", "E2", "E3fe", "M")}
    for cfg in BARE_VARIANTS:
        arr = {k: np.full((n, n), np.nan) for k in out}
        for (i, j), s in src.items():
            ft = _fit_set(
                bare["mode"],
                bare["fem"],
                s["c"],
                bare["z"],
                cfg["N"],
                R=cfg["R"],
                deg=cfg["deg"],
                offset=cfg["offset"],
            )
            m = s["mom"]
            arr["E1"][j, i] = g_MHz(f, m["p"] @ ft.value[:2])
            arr["E2"][j, i] = g_MHz(f, 0.5 * np.sum(m["S"] * ft.grad[:2].T))
            arr["E3fe"][j, i] = g_MHz(
                f, np.einsum("ijk,kij->", m["O"], ft.hess[:2]) / 6
            )
            M1, M2 = magnetic_terms(s["cur"], ft.value[2], ft.grad[2])
            arr["M"][j, i] = g_MHz(f, M1 + M2)
        for k in out:
            out[k].append(arr[k])
    md = []
    for cfg in DRESSED_VARIANTS:
        arr = np.full((n, n), np.nan)
        for (i, j), s in src.items():
            ft = _fit_set(
                dressed["mode"],
                dressed["fem"],
                s["c"],
                dressed["z"],
                cfg["N"],
                rmin=cfg["rmin"],
                R=cfg["R"],
                with_E=False,
            )
            M1, M2 = magnetic_terms(s["cur"], ft.value[0], ft.grad[0])
            arr[j, i] = g_MHz(dressed["f"], M1 + M2)
        md.append(arr)
    res = {k: np.array(v) for k, v in out.items()}
    res["Md"] = np.array(md)
    return res


def term_arrays(T, tag):
    """The terms of :func:`terms_per_qubit` that the error budget reports, as {name: (kind, array in MHz)}.

    kind: 'nonzero' (a term that exists), 'null' (zero by symmetry: its value is a measurement
    of the noise of the estimator) or 'bound' (an upper bound on what is neglected).
    """
    out = {
        "E1 dipole": ("nonzero", T["E1"]),
        "all electric orders": ("nonzero", T["exact_fe"]),
        "E3 octupole (analytic field)": ("nonzero", T["E3"]),
        "E3 octupole (FE field)": ("nonzero", T["E3fe"]),
        "E2 quadrupole": ("null", T["E2"]),
        "M1 + M2, bare mode": ("null", T["M1"] + T["M2"]),
        "M1 + M2, dressed mode": ("nonzero?", T["M1d"] + T["M2d"]),
        "g_EMF - all electric orders": ("bound", T["emf"] - T["exact_fe"]),
    }
    if tag == "210":
        out["dark column i = 2"] = ("null", T["exact_fe"][:, 2:3])
    return out


def _peak(a):
    return float(np.nanmax(np.abs(a)))


def error_budget(tag, T_main, T_prev, ens, var, O_null_rel, dark_rel, levels=None):
    """Noise floor, significance and relevance of every coupling term of one mode.

    Floors (peak over the qubits of the quarter, kHz), each measured:

    - ``mesh``: the largest qubit-wise change between the two finest mesh levels
      (``T_main``, ``T_prev`` are :func:`terms_per_qubit` of those levels);
    - ``ensemble``: the scatter between independent meshes of nearly the same size
      (``ens``: list of :func:`terms_per_qubit`), the nondeterminism of the mesher;
    - ``fit``: the scatter between estimator variants (``var`` from :func:`fit_variants`);
    - ``null``: for a term that is zero by symmetry, its own value (a measurement of the
      noise of its estimator); for the others, the relative noise that the symmetry
      nulls of the same calculation measure (``dark_rel`` for the couplings, ``O_null_rel``
      for the octupole moments).

    The floors add in quadrature (``total``). A term is *resolved* if its peak exceeds 3 x
    total and it changes by less than its own size between the two finest levels; with
    ``T_prev=None`` that stability cannot be tested and the term is at best "unverified".
    A term that is zero by symmetry is flagged if it is *reproducible* over the mesh ensemble
    (same sign, mean above 4 standard errors at some qubit) and does not shrink with refinement
    (``levels``: [(h, terms), ...] from coarse to fine; the peak must fall as h^s with s > 0.15),
    which would be a real finding; reproducible but shrinking is a systematic bias of the
    discretization.
    Returns a list of dicts, one per term, in kHz.
    """
    rows = []
    var_key = {
        "E1 dipole": "E1",
        "E2 quadrupole": "E2",
        "E3 octupole (FE field)": "E3fe",
        "M1 + M2, bare mode": "M",
        "M1 + M2, dressed mode": "Md",
    }
    A = term_arrays(T_main, tag)
    Ap = (
        term_arrays(T_prev, tag) if T_prev is not None else A
    )  # no second mesh level: the mesh floor is not measured
    Ae = [term_arrays(e, tag) for e in ens]
    e1_peak = _peak(T_main["E1"]) * 1e3
    for name, (kind, arr) in A.items():
        V = _peak(arr) * 1e3
        f_mesh = _peak(arr - Ap[name][1]) * 1e3
        f_ens = (
            _peak(np.nanstd(np.array([a[name][1] for a in Ae]), axis=0, ddof=1)) * 1e3
            if len(Ae) > 1
            else 0.0
        )
        f_fit = 0.0
        if name in var_key:
            f_fit = _peak(np.nanstd(var[var_key[name]], axis=0, ddof=1)) * 1e3
        f_null = 0.0
        if kind == "null":
            f_null = V
        elif name == "E3 octupole (analytic field)":
            f_null = V * O_null_rel
        elif name in ("E1 dipole", "all electric orders"):
            f_null = V * dark_rel
        parts = dict(mesh=f_mesh, ensemble=f_ens, fit=f_fit, null=f_null)
        total = float(np.sqrt(sum(v**2 for v in parts.values())))
        biggest = max(parts, key=parts.get)
        mesh_tested = T_prev is not None
        stable = mesh_tested and f_mesh < V
        above = V > 3 * total
        status = (
            "resolved"
            if (above and stable)
            else ("unverified" if (above and not mesh_tested) else "upper limit")
        )
        # a term that is zero by symmetry is a real finding only if it is reproducible: the same sign on independent
        # meshes, with a mean that stands out of the scatter (4 standard errors) at some qubit
        flag, systematic = False, False
        if kind == "null" and len(Ae) > 2:
            stack = np.array([a[name][1] for a in Ae])  # (n_ens, ...)
            mean = np.nanmean(stack, axis=0)
            se = np.nanstd(stack, axis=0, ddof=1) / np.sqrt(len(Ae))
            reproducible = bool(
                np.any((np.abs(mean) > 4 * se) & (np.sign(mean) == np.sign(arr)))
            )
            # shrinking with refinement: a bias of the discretization that goes away
            if levels is not None and len(levels) >= 3:
                hh = np.log([h for h, _ in levels])
                vv = np.log(
                    [max(_peak(term_arrays(T, tag)[name][1]), 1e-30) for _, T in levels]
                )
                falling = bool(np.polyfit(hh, vv, 1)[0] > 0.15)
            else:
                falling = mesh_tested and V < _peak(Ap[name][1]) * 1e3
            flag = reproducible and not falling
            systematic = reproducible and falling
        rows.append(
            dict(
                term=name,
                kind=kind,
                value=V,
                rel_E1=V / e1_peak,
                floor=total,
                parts=parts,
                biggest=biggest,
                stable=stable,
                mesh_tested=mesh_tested,
                status=status,
                resolved=status == "resolved",
                flag_real_null=flag,
                systematic_null=systematic,
                above_1kHz=V > 1.0,
                above_paper=V / e1_peak > 0.048,
                model_band=(0.5 * V, 2 * V) if "M1" in name else None,
            )
        )
    return rows


def pattern_amplitude(g, an, package_L=30.0, pitch=3.0):
    """Least-squares A in g = A cos(a pi x/L) sin(b pi y/L) over the quarter [j, i] array."""
    n = g.shape[0]
    X = (np.arange(n) + 0.5) * pitch
    shape = np.cos(an.a * np.pi * X[None, :] / package_L) * np.sin(
        an.b * np.pi * X[:, None] / package_L
    )
    ok = np.isfinite(g)
    return np.sum(g[ok] * shape[ok]) / np.sum(shape[ok] ** 2)


def summarize_level(src, bares, dresseds=None):
    """Convergence numbers of one mesh level: every quantity the tutorial plots against refinement.

    ``bares`` and ``dresseds`` map a mode tag ('110', '210') to :func:`bare_data` and
    :func:`dressed_data`. Genuine nonzero terms (p_x, A, E3/E1) should converge to a
    finite value; terms that vanish by symmetry should fall toward zero or sit at a floor.
    """
    px = np.array([abs(s["mom"]["p"][0]) for s in src.values()])
    py = np.array([abs(s["mom"]["p"][1]) for s in src.values()])
    S = np.array([np.abs(s["mom"]["S"]).max() for s in src.values()])
    mz = np.array([abs(s["cur"].m()) for s in src.values()])
    Mxz = np.array([abs(s["cur"].M()[0]) for s in src.values()])
    Myz = np.array([s["cur"].M()[1] for s in src.values()])
    mm = 1e-3
    out = dict(
        px=px.mean(),
        py_over_px=(py / px).max(),
        S_over_pmm=(S / (px * mm)).max(),
        mz_over_pmm=(mz / (px * mm)).max(),
        Myz=Myz.mean(),
        Mxz_over_Myz=(Mxz / np.abs(Myz)).max(),
    )
    for tag, bare in bares.items():
        T = terms_per_qubit(src, bare, (dresseds or {}).get(tag))
        an = bare["an"]
        ok = np.abs(T["E1a"]) > 0.05 * np.nanmax(np.abs(T["E1a"]))
        out[f"A_{tag}"] = pattern_amplitude(T["E1"], an)
        out[f"A_exact_{tag}"] = pattern_amplitude(T["exact_fe"], an)
        out[f"E3_over_E1_{tag}"] = np.median((T["E3"] / T["E1a"])[ok])
        out[f"E2_floor_kHz_{tag}"] = 1e3 * np.nanmax(np.abs(T["E2"]))
        out[f"M_floor_kHz_{tag}"] = 1e3 * np.nanmax(np.abs(T["M1"]) + np.abs(T["M2"]))
        gmax = np.nanmax(np.abs(T["exact_a"]))
        dark = np.zeros_like(ok)  # qubits on a node of E_x: g = 0 to all orders
        for i, j in src:
            xq = src[(i, j)]["c"][0]
            dark[j, i] = abs(np.cos(an.a * np.pi * xq / (an.Lx * 1e3))) < 1e-9
        out[f"dark_{tag}"] = (
            np.nanmax(np.abs(T["exact_fe"])[dark]) / gmax if dark.any() else np.nan
        )
        if tag in bares and "maps" in bare:
            G, w = bare["maps"], 2 * np.pi * bare["f"]
            Bt = np.hypot(G["curl"][0], G["curl"][1]) / w
            out[f"Bz_rms_{tag}"] = np.sqrt(np.mean((G["curl"][2] / w) ** 2)) / Bt.max()
        if dresseds and tag in dresseds:
            d = dresseds[tag]
            res = T["emf"] - T["exact_fe"]
            out[f"emf_resid_max_{tag}"] = np.nanmax(np.abs(res)) / gmax
            out[f"emf_resid_mean_{tag}"] = (
                np.nanmean(res / T["exact_fe"])
                if False
                else np.nanmean(res[ok] / T["exact_fe"][ok])
            )
            out[f"Md_over_E1_{tag}"] = np.nanmax(np.abs(T["M1d"] + T["M2d"])) / gmax
            if "maps" in d:
                G, w = d["maps"], 2 * np.pi * d["f"]
                Bt = np.hypot(G["curl"][0], G["curl"][1]) / w
                out[f"Bz_dressed_rms_{tag}"] = (
                    np.sqrt(np.mean((G["curl"][2] / w) ** 2)) / Bt.max()
                )
        out[f"n_dofs_{tag}"] = bare["n_dofs"]
    return out


def lse_frequencies(a, b, Lx, Ly, Lz, t, eps_r, n=3):
    """The lowest ``n`` LSE (TE_z) frequencies (Hz) of the slab-loaded box with in-plane indices (a, b).

    TE_z modes have H_z = h(z) cos(a pi x/Lx) cos(b pi y/Ly), with h = sin(kz_si z) in the silicon
    and h = C sin(kz_air (Lz - z)) above it; E_t is proportional to h and H_t to h', so h and h'
    are continuous at the surface:

        kz_si cos(kz_si t) sin(kz_air (Lz - t)) + kz_air sin(kz_si t) cos(kz_air (Lz - t)) = 0.

    Lengths in mm. These are the modes with B_z != 0: they start about 40 GHz here.
    """
    import scipy.optimize as opt

    from qiskit_metal.analyses.em.package_modes import C0

    Lx, Ly, Lz, t = (1e-3 * v for v in (Lx, Ly, Lz, t))
    g = np.hypot(a * np.pi / Lx, b * np.pi / Ly)

    def F(w):
        k0 = w / C0
        ks = np.sqrt(eps_r * k0**2 - g**2 + 0j)
        ka = np.sqrt(k0**2 - g**2 + 0j)
        return (
            ks * np.cos(ks * t) * np.sin(ka * (Lz - t))
            + ka * np.sin(ks * t) * np.cos(ka * (Lz - t))
        ).real

    ws = np.linspace(C0 * g * (1 + 1e-4), C0 * g * np.sqrt(eps_r) * 6, 40000)
    vals = F(ws)
    roots = []
    for i in np.nonzero(vals[:-1] * vals[1:] < 0)[0]:
        roots.append(opt.brentq(F, ws[i], ws[i + 1]) / (2 * np.pi))
        if len(roots) == n:
            break
    return roots


# ---------------------------------------------------------------------------
# Checks that need no mesh
# ---------------------------------------------------------------------------


def selftest(verbose=True):
    """Checks of the moments, the ray integral and the current model on synthetic data.

    Returns a dict of the measured numbers; raises AssertionError on failure.
    """
    from skfem import MeshTri

    from qiskit_metal.analyses.em.package_modes import lsm_mode

    res = {}
    # 1. two charges: p = q d, S = 0, O_xxx = q d^3 / 4; origin shift of S
    q0, d0 = 2.5e-7, 1.2e-3
    r = np.array([[d0 / 2, -d0 / 2], [0.0, 0.0]])
    q = np.array([q0, -q0])
    mom = moments(r, q)
    sh = np.array([0.3e-3, -0.2e-3])
    mom_sh = moments(r - sh[:, None], q)
    res["T1 p"] = mom["p"][0] / (q0 * d0) - 1
    res["T1 S"] = np.abs(mom["S"]).max() / (q0 * d0 * d0)
    res["T1 O"] = mom["O"][0, 0, 0] / (q0 * d0**3 / 4) - 1
    res["T1 shift"] = np.abs(mom_sh["S"] - shift_origin(mom, sh)["S"]).max() / (
        q0 * d0 * d0
    )
    # 2. the ray integral against the potential difference, for the analytic mode
    mode = lsm_mode(1, 1, 30.0, 30.0, 3.0, 0.5, 11.9)
    rng = np.random.default_rng(3)
    rr = rng.uniform(-0.6e-3, 0.6e-3, (2, 9))
    qq = rng.normal(size=9)
    qq -= qq.mean()
    c = (4.5, 10.5)
    U_ray = ray_coupling(lsm_inplane(mode), c, rr, qq)
    U_phi = -np.sum(
        qq
        * (
            lsm_potential(mode, c[0] + 1e3 * rr[0], c[1] + 1e3 * rr[1])
            - lsm_potential(mode, *c)
        )
    )
    res["T2 ray"] = abs(U_ray / U_phi - 1)
    series = multipole_terms(moments(rr, qq), mode, c, nmax=3).sum()
    res["T2 series3"] = abs(series / U_phi - 1)

    # 3. the sheet current on two rectangles: int K = p, and the test fields
    def pad(x0, x1, sgn):
        m = MeshTri.init_tensor(
            np.linspace(x0, x1, 11), np.linspace(-0.5e-3, 0.5e-3, 21)
        )
        xy = m.p
        # a smooth charge density, positive or negative, consistent nodal charges
        sig = (
            sgn
            * (1 + 4 * (xy[1] / 0.5e-3) ** 2)
            * (1 + 3 * np.abs(xy[0] - (x0 + x1) / 2) / 0.25e-3)
        )
        from skfem import Basis, BilinearForm, ElementTriP1, asm
        from skfem.helpers import dot

        b = Basis(m, ElementTriP1())
        Mmat = asm(BilinearForm(lambda u, v, w: u * v), b)
        rload = Mmat @ (sig * 1e-3)
        return xy, rload, m.t.T

    pL, pR = pad(-0.6e-3, -0.1e-3, -1.0), pad(0.1e-3, 0.6e-3, +1.0)
    scale = abs(pL[1].sum())
    for P_ in (pL, pR):
        P_[1][:] *= abs(1e-7 / scale)
    cur = sheet_current(
        [pR, pL], [(0.1e-3, 0.2e-3), (-0.1e-3, 0.2e-3)]
    )  # junction off axis: mtilde_z != 0
    pdip = sum((P_[0] @ P_[1]) for P_ in (pL, pR))
    res["T3 int K = p"] = np.abs(cur.dipole() - pdip).max() / np.abs(pdip).max()
    # E = (-y, x): int K.E = 2 mtilde_z, with a zero pure-charge ray integral
    Ecurl = lambda x, y: (-y * 1e-3, x * 1e-3)  # noqa: E731  (x, y in mm -> V/m at 1 V/m^2)
    res["T3 curl"] = abs(cur.overlap(Ecurl) / (2 * cur.m()) - 1)
    # E = (-y^2, 0): velocity overlap = ray integral + (2/3) Mtilde_yz
    Equad = lambda x, y: (-((y * 1e-3) ** 2), 0 * y)  # noqa: E731
    allr = np.hstack([pL[0], pR[0]]) * 1.0
    allq = np.concatenate([pL[1], pR[1]])
    U_vel = cur.overlap(Equad)
    U_rep = ray_coupling(Equad, (0.0, 0.0), allr, allq) + 2 / 3 * cur.M()[1]
    res["T3 quad"] = abs(U_vel / U_rep - 1)
    limits = {
        "T1 p": 1e-12,
        "T1 S": 1e-12,
        "T1 O": 1e-12,
        "T1 shift": 1e-12,
        "T2 ray": 1e-10,
        "T2 series3": 5e-3,
        "T3 int K = p": 1e-10,
        "T3 curl": 1e-9,
        "T3 quad": 2e-2,
    }
    for k, lim in limits.items():
        ok = res[k] < lim
        if verbose:
            print(f"{k:>14}: {res[k]:.2e} (limit {lim:.0e})  {'ok' if ok else 'FAIL'}")
        assert ok, (k, res[k])
    return res
