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
"""This code calculations the wavefunction(s) of the simple harmonic oscillator
corresponding to an LC circuit.

Key References:
    - *R. Shankar*, "Principles of Quantum Mechanics", Second Edition, Springer (1994)
    - or any other undergraduate quantum mechanics textbook)
"""

import matplotlib.pyplot as plt
import numpy as np
from math import *

__all__ = ['wavefunction']


def wavefunction(L, C, n, x):
    """This function calculates the nth wavefunction of the harmonic oscillator
    for a given value of inductance (L) and capacitance (C) at a charge x.

    Args:
        L (float): The inductance of the inductor in an LC circuit.
        C (float): The capacitance of the capacitor in an LC circuit.
        n (int): The energy state of the harmonic oscillator.
        x (float): The value of charge (independent variable) for which the wavefunction is calculated.

    Returns:
        float: Calculated wavefunction
    """
    # This is the fundamental frequency of the LC circuit
    omega = (L * C)**(0.5)

    # For simplicity, let's work in units where hbar=1
    hbar = 1.0

    # these are two terms in the expression for wavefunction which do not depend on charge (x)
    prefactor = np.sqrt(1.0 / ((2.0**n) * (np.math.factorial(n))))
    qubic_root = ((L * omega) / (np.pi * hbar))**(0.25)

    # these are the terms in the expression for the wavefunction which depend on charge (x) and energy state (n)
    if n == 0:
        Hermitian_term = prefactor * qubic_root * (2.71828**(
            (-L * omega * x**2.0) / (2.0 * hbar))) * 1.0
    if n == 1:
        Hermitian_term = prefactor * qubic_root * (2.71828**(
            (-L * omega * x**2.0) / (2.0 * hbar))) * (2.0 * x)
    if n == 2:
        Hermitian_term = prefactor * qubic_root * (2.71828**(
            (-L * omega * x**2.0) / (2.0 * hbar))) * (4.0 * x**2.0 - 2.0)
    if n == 3:
        Hermitian_term = prefactor * qubic_root * (2.71828**(
            (-L * omega * x**2.0) / (2.0 * hbar))) * (8.0 * x**3.0 - 12.0 * x)
    if n == 4:
        Hermitian_term = prefactor * qubic_root * (2.71828**(
            (-L * omega * x**2.0) /
            (2.0 * hbar))) * (16.0 * x**4.0 - 48.0 * x**2.0 + 12.0)

    # the final wavefunction is the product of these terms
    return (prefactor) * (qubic_root) * (Hermitian_term)
