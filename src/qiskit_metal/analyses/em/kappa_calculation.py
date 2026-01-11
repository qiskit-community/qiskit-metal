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
"""

import numpy as np
from math import *
from scipy.special import ellipk

__all__ = ['kappa_in']


def kappa_in(*argv):
    """A simple calculator for the kappa value of a readout resonator.

    Args:
        freq (float): The frequency of interest, in Hz
        C_in (float): Effective capacitance between CPW and environment (from Q3D), in Farads
        freq_res (float): Lowest resonant frequency of a CPW (from HFSS), in Hz
        length (float): Length of the CPW readout resonator, in meters
        res_width (float): Width of the resonator trace (center) line, in meters
        res_gap (float): Width of resonator gap (dielectric space), in meters
        eta (float): 2.0 for half-wavelength resonator; 4.0 for quarter-wavelength resonator

    Returns:
        float: Kappa value
    """

    # Effective impedance of the CPW transmission line, in Ohms
    Z_tran = 50.0

    # Effective impedance of the readout resonator, in Ohms
    Z_res = 50.0

    # If three arguments are passed to kappa_in, then the lowest resonator frequency is assumed to be an input
    if len(argv) == 3:
        for i in argv:
            freq = argv[0]
            C_in = argv[1]
            freq_res = argv[2]

        # Calculation of kappa
        kappa = (2 / pi) * (freq**2.0) * (C_in**2.0) * (Z_tran**
                                                        2.0) * (freq_res)

        return kappa

    # If six arguments are passed to kappa_in, the lowest resonator frequency of the resonator is calculated in the ideal case
    elif len(argv) == 6:
        for i in argv:
            freq = argv[0]
            C_in = argv[1]
            length = argv[2]
            res_width = argv[3]
            res_gap = argv[4]
            eta = argv[5]

        # Arguments for elliptic integrals
        k0 = (res_width) / (res_width + 2.0 * res_gap)
        k01 = (1.0 - k0**2.0)**(0.5)

        # Calculation of the first resonant frequency of an ideal resonator
        freq_res = (Z_res) * (ellipk(
            k0**2.0)) / (15.0 * eta * length * ellipk(k01**2.0))

        # Calculation of kappa
        kappa = (2 / pi) * (freq**2.0) * (C_in**2.0) * (Z_tran**
                                                        2.0) * (freq_res)
        return kappa

    # Only three or six arguments accepted by kappa_in, otherwise the calculation in invalid.
    else:
        kappa = "Invalid number of arguments passed for kappa_in"
