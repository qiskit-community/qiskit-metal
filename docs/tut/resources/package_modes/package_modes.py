"""Package modes and qubit couplings: the paper's device, for tutorials 4.41-4.45.

Tutorials 4.41-4.45 reproduce

    R. Molavi, E. Forati, Y. Zhang, A. R. Klots, J. Atalaya, B. W. Langley,
    D. A. Timucin, M. Nazari, G. Khan, Z. K. Minev, A. N. Korotkov and
    M. H. Devoret, "Extracting electromagnetic bare mode couplings in large
    superconducting quantum processors," arXiv:2609.22442 (2026).

The paper runs Ansys HFSS. Here the same calculations run on an open stack:
Quantum Metal holds the design, gmsh meshes it, scikit-fem assembles the
finite-element matrices and SciPy solves them. The solver lives in Quantum
Metal (:mod:`qiskit_metal.analyses.fem`, and the analytic models in
:mod:`qiskit_metal.analyses.em.package_modes`). This module adds what is
specific to the paper: its device and reported numbers (``DEVICE``,
``PAPER``), the 10 x 10 processor as a Quantum Metal design
(``build_design``), and the paper's device as the default for the analytic
functions. It re-exports the solver, so the tutorials call everything as
``pm.<name>``.

Units: lengths in millimetres inside the mesh and the solver, SI everywhere
else.
"""

from __future__ import annotations

from qiskit_metal.analyses.em import package_modes as _analytic
from qiskit_metal.analyses.em.package_modes import (  # noqa: F401
    C0,
    C0_MM,
    EPS0,
    MU0,
    ImpedanceFit,
    LSMMode,
    circuit_couplings,
    circuit_eigenfrequencies,
    circuit_impedance,
    dipole_coupling,
    fit_impedance,
    g_on_resonance,
)
from qiskit_metal.analyses.fem import solver as _fem
from qiskit_metal.analyses.fem.solver import (  # noqa: F401
    Electrostatics,
    MaxwellFEM,
    Mode,
    Package,
    PackageMesh,
    PortROM,
    emf_coupling,
    mesh_package,
    mirror_signs,
    plot_package_3d,
)

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
    return _analytic.qubit_centers(n, pitch)


def _device(**given):
    """The given lengths and permittivity, the paper's device where None."""
    return {k: DEVICE[k] if v is None else v for k, v in given.items()}


def lsm_mode(a=1, b=1, Lx=None, Ly=None, Lz=None, t=None, eps_r=None, Em=1.0):
    """The lowest LSM_ab0 mode (lengths in mm; defaults: the paper's device).
    See :func:`qiskit_metal.analyses.em.package_modes.lsm_mode`."""
    return _analytic.lsm_mode(
        a, b, **_device(Lx=Lx, Ly=Ly, Lz=Lz, t=t, eps_r=eps_r), Em=Em
    )


def lsm_mode_approx(a=1, b=1, Lx=None, Ly=None, Lz=None, t=None, eps_r=None, Em=1.0):
    """The closed-form approximations of Appendix E (defaults: the paper's device)."""
    return _analytic.lsm_mode_approx(
        a, b, **_device(Lx=Lx, Ly=Ly, Lz=Lz, t=t, eps_r=eps_r), Em=Em
    )


def fit_amplitude(g, a=1, b=1, Lx=None, Ly=None):
    """Least-squares amplitude of g = A cos(a pi x/Lx) sin(b pi y/Ly) over the
    array (defaults: the paper's device). Returns (A, largest residual / |A|)."""
    return _analytic.fit_amplitude(g, a, b, **_device(Lx=Lx, Ly=Ly))


def unfold_quarter(values, cuts=("pmc", "pmc"), n=DEVICE["n"]):
    """{(i, j): v} on the quarter i, j < n/2 -> an (n, n) array [j, i] on the whole array."""
    return _fem.unfold_quarter(values, cuts, n)


def package_from_design(design, eps_r=None):
    """Box, substrate, paddles and junction lines of a Metal design (mm); the
    slab's permittivity defaults to the paper's silicon."""
    return _fem.package_from_design(design, DEVICE["eps_r"] if eps_r is None else eps_r)


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
