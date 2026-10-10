"""This code calculates the photon loss (kappa) due to the capacitive coupling
between CPWs and input/output transmission lines in a quantum circuit.

Two cases are treated: In the first case, three arguments are passed to the function kappa_in
and the resonant frequency of the CPW is input as a float. In the second case, six arguments
are passed to kappa_in and the frequency of the CPW is calculated assuming an ideal CPW.

Key References:

D. Schuster, Ph.D. Thesis, Yale University (2007)
https://rsl.yale.edu/sites/default/files/files/RSL_Theses/SchusterThesis.pdf

T. McConkey, Ph.D. Thesis, University of Waterloo (2018)
https://uwspace.uwaterloo.ca/bitstream/handle/10012/13464/McConkey_Thomas.pdf?sequence=3&isAllowed=y

Mohebbi and Majedi, Superconducting Science and Technology 22, 125028 (2009)
https://iopscience.iop.org/article/10.1088/0953-2048/22/12/125028/meta

P. Krantz, et al. Physical Review Applied 6, 021318 (2019)
https://aip.scitation.org/doi/10.1063/1.5089550

M. Goppl, et al. Journal of Applied Physics 104, 113904 (2008)
https://doi.org/10.1063/1.3010859
"""

import warnings
from math import pi

from scipy.constants import c as SPEED_OF_LIGHT
from scipy.special import ellipk

__all__ = ["kappa_in"]


def kappa_in(*argv):
    r"""Linewidth of a CPW resonator capacitively coupled to a matched line.

    Two call forms::

        kappa_in(freq, C_in, freq_res)
        kappa_in(freq, C_in, length, res_width, res_gap, eta)

    Uses the weak-coupling result (e.g. Goppl et al. 2008) for a resonator
    coupled at one end through :math:`C_\mathrm{in}` to a line of impedance
    :math:`Z_0 = 50\,\Omega`:

    .. math::

        \kappa = \frac{\eta}{\pi}\,\omega^2 C_\mathrm{in}^2 Z_0^2\,\omega_r,
        \qquad \omega = 2\pi f,\ \omega_r = 2\pi f_r,

    with :math:`\eta = 2` for a half-wave and :math:`\eta = 4` for a
    quarter-wave resonator (whose equivalent capacitance is half that of a
    half-wave line). The three-argument form assumes a half-wave resonator.

    **Units.** The return value is :math:`\kappa/2\pi` in Hz (the full width
    at half maximum of the resonance); multiply by :math:`2\pi` for the
    energy decay rate in 1/s. Before #1204 the formula was evaluated with
    :math:`f` in place of :math:`\omega`, which returned a value
    :math:`(2\pi)^2` smaller than :math:`\kappa/2\pi`.

    In the six-argument form the resonance frequency is that of an ideal
    (conformal-mapping) CPW whose effective permittivity makes its impedance
    50 Ohm for the given width and gap:
    :math:`f_r = c / (\eta\,\ell\sqrt{\epsilon_\mathrm{eff}})` with
    :math:`\sqrt{\epsilon_\mathrm{eff}} = 30\pi K(k_0')/(Z_r K(k_0))`.

    Args:
        freq (float): The frequency at which kappa is evaluated, in Hz
            (normally the resonance frequency).
        C_in (float): Coupling capacitance between the CPW and the feed line
            (from Q3D), in Farads.
        freq_res (float): Resonant frequency of the CPW (from HFSS), in Hz.
            Three-argument form only.
        length (float): Length of the CPW resonator, in meters.
        res_width (float): Width of the resonator center trace, in meters.
        res_gap (float): Width of the resonator gap, in meters.
        eta (float): 2.0 for a half-wavelength resonator; 4.0 for a
            quarter-wavelength resonator.

    Returns:
        float: :math:`\kappa/2\pi` in Hz, or ``None`` (with a warning) if the
        number of arguments is neither 3 nor 6.
    """

    # Effective impedance of the CPW transmission line, in Ohms
    Z_tran = 50.0

    # Effective impedance of the readout resonator, in Ohms
    Z_res = 50.0

    if len(argv) == 3:
        freq, C_in, freq_res = argv
        eta = 2.0
    elif len(argv) == 6:
        freq, C_in, length, res_width, res_gap, eta = argv

        # Moduli for the complete elliptic integrals (scipy's ellipk takes the
        # parameter m = k**2).
        k0 = (res_width) / (res_width + 2.0 * res_gap)
        k01 = (1.0 - k0**2.0) ** (0.5)

        # Fundamental resonance of the ideal resonator, c / (eta l sqrt(eps_eff)),
        # with sqrt(eps_eff) = 30 pi K(k0') / (Z_res K(k0)).
        freq_res = (
            SPEED_OF_LIGHT
            * Z_res
            * ellipk(k0**2.0)
            / (30.0 * pi * eta * length * ellipk(k01**2.0))
        )
    else:
        warnings.warn(
            "kappa_in takes 3 (freq, C_in, freq_res) or 6 (freq, C_in, length, "
            f"res_width, res_gap, eta) arguments, got {len(argv)}; returning None.",
            stacklevel=2,
        )
        return None

    omega = 2.0 * pi * freq
    omega_res = 2.0 * pi * freq_res
    kappa = (eta / pi) * omega**2.0 * C_in**2.0 * Z_tran**2.0 * omega_res  # 1/s
    return kappa / (2.0 * pi)  # kappa / 2 pi, in Hz
