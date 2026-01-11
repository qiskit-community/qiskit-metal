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

#pylint: disable-msg=import-error
#pylint: disable-msg=consider-using-enumerate
"""
This code calculates the energy eigenvalues of the transmon qubit cooper pair box
as a function of the offset charge and plots the corresponding results.

Key References:
    - J. Koch et al. "Charge-insensitive qubit design derived from the Cooper pair box"
      Phys. Rev. A. 76, 042319 (2007).

"""

from scipy.special import mathieu_a
import numpy as np
import matplotlib.pyplot as plt

__all__ = ['kidx_raw', 'kidx', 'transmon_eigenvalue', 'plot_eigenvalues']


def kidx_raw(m, my_ng):
    """
    This function calculates the integers which correct sort the eigenstates and eigenenergies
    of the solution to Mathieu's equation.

        Args:
            m (int): The energy level of the qubit (m=0,1,2,3,etc.)
            my_ng (float): the offset charge of the Josephjunction island (in units of 2e)

        Returns:
            float: the calculated index
    """
    if my_ng == 0:
        return m + 1.0 - ((m + 1.0) % 2.0)

    return m + 1.0 - ((m + 1.0) % 2.0) + 2.0 * my_ng * (
        (-1.0)**(m - 0.5 * (np.sign(my_ng) - 1.0)))


def kidx(m, my_ng):
    """
    This function is a placeholder which performs an additional modulo operation
    with an offset of ng=0.5, but is not necessary when only integer values of
    kidxRAW(m, my_ng) are used. If non-integer values of kidxRAW are used, then
    the modulo operation below needs to be updated to include the offset.

        Args:
            m (int): The energy level of the qubit (m=0,1,2,3,etc.)
            ng (float): the offset charge of the Josephjunction island (in units of 2e)

        Returns:
            float: the calculated energy eigenvalue, after an ng=0.5 offset.
    """
    return kidx_raw(m, my_ng)


# define the Josephson to charging energy ratio E_J / E_C
RATIO = 1.0

# define the charing energy
E_C = 1.0


def transmon_eigenvalue(m, my_ng):
    """
    This function calculate the energy eigenvalue of the transmon qubit for a given
    energy level (m) and offset charge (my_ng). The input values are first used to
    calculate the index using the function defined above, and then the calculated
    index is used to calculate the energy eigenvalue using Mathieu's characteristic values.

        Args:
            m (int): The energy level of the qubit (m=0,1,2,3,etc.)
            ng (float): the offset charge of the Josephjunction island (in units of 2e)

        Returns:
            float: the calculated energy eigenvalue.
    """
    index = kidx(m, my_ng)
    return (E_C) * mathieu_a(index, -0.5 * RATIO)


# extremely coarse grid: only three points from -0.5 to 0.5. This so that only integer values
# of the index are used in the calculation of the Mathieu characteristic value.
ng = np.linspace(-0.5, 0.5, 3)

# ng is periodic extending from -2 to 2:
ng_periodic = np.linspace(-2.0, 2.0, 9)

# define energies between (-0.5, 0.5) as empty lists.
E0 = []
E1 = []
E2 = []
E3 = []

# define periodic energies between (-2.0, 2.0)
E0_periodic = [None] * 9
E1_periodic = [None] * 9
E2_periodic = [None] * 9
E3_periodic = [None] * 9

# calculate the energies for m=0,1,2 at each value of offset charge
for i in ng:
    E0.append(transmon_eigenvalue(0, i))
    E1.append(transmon_eigenvalue(1, i))
    E2.append(transmon_eigenvalue(2, i))
    E3.append(transmon_eigenvalue(3, i))

# define the periodic eigen energies based on the values between (-0.5,0.5)
for i in range(len(E0_periodic)):
    E0_periodic[0] = E0[1]
    E0_periodic[1] = E0[0]
    E1_periodic[0] = E1[1]
    E1_periodic[1] = E1[0]
    E2_periodic[0] = E2[1]
    E2_periodic[1] = E2[0]
    E3_periodic[0] = E3[1]
    E3_periodic[1] = E3[0]

    if i > 1:
        E0_periodic[i] = E0_periodic[i - 2]
        E1_periodic[i] = E1_periodic[i - 2]
        E2_periodic[i] = E2_periodic[i - 2]
        E3_periodic[i] = E3_periodic[i - 2]


def plot_eigenvalues():
    """
    This function actually creates the plot(s) of eigenvalues as a function of
    offset charge. No arguments need to be passed.

    Returns:
        A plot of the eigenvalues as a function of offset charge.
    """
    # plot the PERIODIC eigen energies between (-2.0, 2.0)
    plt.plot(ng_periodic, E0_periodic, 'k')  # m=0
    plt.plot(ng_periodic, E1_periodic, 'r')  # m=1
    plt.plot(ng_periodic, E2_periodic, 'b')  # m=2
    plt.plot(ng_periodic, E3_periodic, 'm')  # m=3
    plt.xlabel("Offset Charge [ng]")
    plt.ylabel("Energy E_m[ng]")
