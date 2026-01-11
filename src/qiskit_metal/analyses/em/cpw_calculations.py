# -*- coding: utf-8 -*-

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
"""For calculations of CPW parameters. Referenced primarily as a tool for some
components.

@author: Thomas McConkey, as part of https://uwspace.uwaterloo.ca/handle/10012/13464

Key References:

D. Schuster, Ph.D. Thesis, Yale University (2007)
https://rsl.yale.edu/sites/default/files/files/RSL_Theses/SchusterThesis.pdf

Goppl et al., Journal of Applied Physics 104, 1139044 (2008)
https://aip.scitation.org/doi/abs/10.1063/1.3010859?journalCode=jap

Mohebbi and Majedi, Superconducting Science and Technology 22, 125028 (2009)
https://iopscience.iop.org/article/10.1088/0953-2048/22/12/125028/meta
"""

import numpy as np
from scipy.special import ellipk

c0 = 2.9979 * 10**8
e0 = 8.85419 * 10**-12
u0 = 4 * np.pi * 10**-7

__all__ = [
    'guided_wavelength', 'lumped_cpw', 'effective_dielectric_constant',
    'elliptic_int_constants'
]


def guided_wavelength(freq,
                      line_width,
                      line_gap,
                      substrate_thickness,
                      film_thickness,
                      dielectric_constant=11.45):
    """A simple calculator to determine the guided wavelength of a planar CPW
    transmission line. Assumes the substrate has relative permeability of 1.
    Assumes package grounds are far away.

    Args:
        freq (float): The frequency of interest, in Hz (eg. 5*10**9).
        line_width (float): The width of the CPW trace (center) line, in meters (eg. 10*10**-6).
        line_gap (float): The width of the CPW gap (dielectric space), in meters (eg. 6*10**-6).
        substrate_thickness (float): Thickness of the dielectric substrate, in meters (eg. 760*10**-6).
        film_thickness (float): Thickness of the thin film, in meters (eg. 200*10**-9).
        dielectric_constant (float): The relative permittivity of the substrate.
            Defaults to 11.45, the value for Silicon at cryogenic temperatures.

    Returns:
        tuple: Contents outlined below

    Tuple contents:
        * lambdaG: The guided wavelength of the CPW based on the input parameters, in meters.
          This value is for a full wavelength. Divide by 2 for a lambda/2 resonator, 4 for a lambda/4.
        * etfSqrt: Effective dielectric constant (accounting for film thickness)
        * q: Filling factor
    """

    s = line_width
    w = line_gap
    h = substrate_thickness
    t = film_thickness
    eRD = dielectric_constant

    #elliptic integrals
    Kk0, Kk01, Kk1, Kk11 = elliptic_int_constants(s, w, h)

    #filling factor
    q = 0.5 * (Kk1 * Kk01) / (Kk11 * Kk0)

    #effective dielectric constant (accounting for film thickness)
    etfSqrt = effective_dielectric_constant(freq, s, w, h, t, q, Kk0, Kk01, eRD)

    lambdaG = (c0 / freq) / etfSqrt

    return lambdaG, etfSqrt, q


def lumped_cpw(freq,
               line_width,
               line_gap,
               substrate_thickness,
               film_thickness,
               dielectric_constant=11.45,
               loss_tangent=10**-5,
               london_penetration_depth=30 * 10**-9):
    """A simple calculator to determine the lumped element equivalent of a CPW
    transmission line. Assumes a lossless superconductor. The internal
    geometric series inductance is ignored.

    Args:
        freq (float): The frequency of interest, in Hz (eg. 5*10**9).
        line_width (float): The width of the CPW trace (center) line, in meters (eg. 10*10**-6).
        line_gap (float): The width of the CPW gap (dielectric space), in meters (eg. 6*10**-6).
        substrate_thickness (float): Thickness of the dielectric substrate, in meters (eg. 760*10**-6).
        film_thickness (float): Thickness of the thin film, in meters (eg. 200*10**-9).
        dielectric_constant (float, optional): The relative permittivity of the substrate.
            Defaults to 11.45, the value for silicon at cryogenic temperatures.
        loss_tangent (float, optional): The loss tangent of the dielectric.
            Defaults to 10**-6, reasonable quality silicon.
        london_penetration_depth (float, optional): The superconducting london penetration depth, in meters.
            It is advised to use the temperature and film thickness dependent value. If circuit
            geometries are on the scale of the Pearl Length, the kinetic inductance formulas
            breakdown.
            Defaults to 30*10**-9, for Niobium.

    Returns:
        tuple: Contents outlined below

    Tuple contents:
        * Lk (float): The series kinetic inductance, in Henries.
        * Lext (float): The series geometric external inductance, in Henries.
        * C (float): The shunt capacitance, in Farads.
        * G (float): The shunt admittance, in Siemens. #NOTE:double check if right units
        * Z0 (float): sqrt(L / C)
        * etfSqrt**2: Effective Dielectric Constant
        * Cstar: External Inductance

    ::

        -----Lext + Lk--+---+---
                        |   |
                        C   G
                        |   |
        ----------------+---+---
    """
    s = line_width
    w = line_gap
    h = substrate_thickness
    t = film_thickness
    eRD = dielectric_constant
    tanD = loss_tangent
    lambdaLT = london_penetration_depth
    wfreq = freq * 2 * np.pi

    Kk0, Kk01, Kk1, Kk11 = elliptic_int_constants(s, w, h)

    C = 2 * e0 * (eRD - 1) * (Kk1 / Kk11) + 4 * e0 * (Kk0 / Kk01)

    #filling factor
    q = 0.5 * (Kk1 * Kk01) / (Kk11 * Kk0)

    #Admittance
    G = wfreq * C * q * tanD

    #Effective Dielectric Constant
    etfSqrt = effective_dielectric_constant(freq, s, w, h, t, q, Kk0, Kk01, eRD)

    #External Inducatance
    Z0 = (30 * np.pi / etfSqrt) * Kk01 / Kk0
    Lext = Z0**2 * C
    Cstar = 2 * e0 * (etfSqrt**2 - 1) * (Kk1 / Kk11) + 4 * e0 * (Kk0 / Kk01)

    #Kinetic Inductance
    A1 = (-t / np.pi) + (1 / 2) * np.sqrt((2 * t / np.pi)**2 + s**2)
    B1 = s**2 / (4 * A1)
    C1 = B1 - (t / np.pi) + np.sqrt((t / np.pi)**2 + w**2)
    D1 = 2 * t / np.pi + C1

    LkinStep = (u0 * lambdaLT * C1 / (4 * A1 * D1 * Kk0))

    Lkin1 = LkinStep * 1.7 / (np.sinh(t / (2 * lambdaLT)))
    Lkin2 = LkinStep * 0.4 / (np.sqrt(
        (((B1 / A1)**2) - 1) * (1 - (B1 / D1)**2)))

    Lk = Lkin1 + Lkin2

    return Lk, Lext, C, G, Z0, etfSqrt**2, Cstar


def effective_dielectric_constant(freq, s, w, h, t, q, Kk0, Kk01, eRD=11.45):
    """Returns the film and substrate thickness dependent effective dielectric
    constant for a planar CPW transmission line. Assumes package ground can be
    ignored.

    Args:
        freq (float): The frequency of interest (eg. 5*10**9)
        s (float): The width of the CPW trace (center) line, in meters (eg. 10*10**-6).
        w (float): The width of the CPW gap (dielectric space), in meters (eg. 6*10**-6).
        h (float): Thickness of the dielectric substrate, in meters (eg. 760*10**-6).
        t (float): Thickness of the thin film, in meters (eg. 200*10**-9).
        q (float): Filling factor of the CPW in question
        Kk0 (float): The complete elliptic integral for k0
        Kk01 (float): The complete elliptic integral for k01
        eRD (float, optional): The relative permittivity of the substrate. Defaults to 11.45.

    Returns:
        float: etfSqrt is the effective permittivity for a CPW transmission line, considering
        film and substrate thickness.
    """

    #Effective Dielectric Constant
    e00 = 1 + q * (eRD - 1)
    et0 = e00 - (0.7 * (e00 - 1) * t / w) / ((Kk0 / Kk01) + 0.7 * t / w)

    p = np.log(s / h)
    v = 0.43 - 0.86 * p + 0.54 * p**2
    u = 0.54 - 0.64 * p + 0.015 * p**2
    fTE = c0 / (4 * h * np.sqrt(eRD - 1))
    g = np.exp(u * np.log(s / w) + v)

    etfSqrt = np.sqrt(et0) + (np.sqrt(eRD) -
                              np.sqrt(et0)) / (1 + g * (freq / fTE)**-1.8)

    return etfSqrt


def elliptic_int_constants(s, w, h):
    """Calculates the complete elliptic integral of the first kind for CPW
    lumped element equivalent circuit calculations.

    Args:
        s (float): The width of the CPW trace (center) line, in meters (eg. 10*10**-6).
        w (float): The width of the CPW gap (dielectric space), in meters (eg. 6*10**-6).
        h (float): Thickness of the dielectric substrate, in meters (eg. 760*10**-6).

    Returns:
        tuple: Contents outlined below

    Tuple contents:
        * ellipk(k0) (float): The complete elliptic integral for k0
        * ellipk(k01) (float): The complete elliptic integral for k01
        * ellipk(k1) (float): The complete elliptic integral for k1
        * ellipk(k11) (float): The complete elliptic integral for k11
    """
    #elliptical integral constants
    k0 = s / (s + 2 * w)
    k01 = np.sqrt(1 - k0**2)
    k1 = np.sinh((np.pi * s) / (4 * h)) / (np.sinh(
        (np.pi * (s + 2 * w)) / (4 * h)))
    k11 = np.sqrt(1 - k1**2)

    return ellipk(k0**2.0), ellipk(k01**2.0), ellipk(k1**2.0), ellipk(k11**2.0)
