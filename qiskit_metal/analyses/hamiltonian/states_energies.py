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
"""
This file contains functions related to extracting and manipulating Hamiltonians
and their energy levels.
"""
from typing import Dict as Dict_
from typing import List

import numpy as np
import qutip
from qutip import Qobj


def basis_state_on(mode_size: List[int], excitations: Dict_[int, int]):
    ''' Construct a qutip Qobj. Taken from pyEPR
    https://github.com/zlatko-minev/pyEPR/blob/master/pyEPR/calcs/back_box_numeric.py

    Args:
        mode_size (list): list of integers specifying number of fock states
                           for each mode, respectively
        excitations (dict): {mode index: # of photons}
            give the value excitations[i] or 0 if index i not in excitations;
            i.e., by default ground state.

    Returns:
        qutip Qobj: qutip tensor product representing the state
    '''
    return qutip.tensor(*[
        qutip.basis(mode_size[i], excitations.get(i, 0))
        for i in range(len(mode_size))
    ])


def extract_energies(esys_array: np.ndarray,
                     mode_size: List[int],
                     zero_evals: bool = True,
                     chi_prime: bool = False):
    """
    Returns the frequencies, anharmonicities, and dispersive shifts of the modes.

    Args:
        esys_array (np.ndarray): numpy array of shape (2, ). It's an array of objects.
            The first element of the array is an array of eigenvalues of the diagonalized
            hamiltonian. The second element of the array is an QutipEigenStates object,
            which is a list of the corresponding eigenstates of the diagonalized hamiltonian
        mode_size (List[int]): list of integers specifying number of fock states
            for each mode, respectively
        zero_evals (bool, optional): If true, the "ground state" eigenvalue is substracted
            all eigenvalues. Defaults to True.
        chi_prime (bool, optional): Defaults to False.

    Returns:
        np.ndarray, np.ndarray: a tuple of arrays. The first array is the frequencies of
            the modes. The second array is a matrix where the diagonal entries are the
            anharmonicities of the modes and the off-diagonal entries are the dispersive
            shifts, i.e., the chi's between the modes
    """

    print("Processing eigensystem...", end='')
    evals, evecs = esys_array
    print("\rFinished eigensystem.     ")

    if zero_evals:
        evals -= evals[0]  # zero out

    # if use_1st_order:
    def closest_state_to(s: Qobj):
        # find the eigenvector among evecs that is closest
        # to s (largest inner product)

        def distance(s2: Qobj):
            return (s.dag() * s2[1]).norm()

        return max(zip(evals, evecs), key=distance)

    N = len(mode_size)

    def state_on(excitations):
        return basis_state_on(mode_size, excitations)  # eigenstate on

    f1s = [closest_state_to(state_on({i: 1}))[0] for i in range(N)]
    chis = [[0] * N for _ in range(N)]
    chips = [[0] * N for _ in range(N)]
    for i in range(N):
        for j in range(i, N):
            d = {k: 0 for k in range(N)}  # put 0 photons in each mode (k)
            d[i] += 1
            d[j] += 1
            # load ith mode and jth mode with 1 photon
            fs = state_on(d)
            ev, _evec = closest_state_to(fs)
            chi = (ev - (f1s[i] + f1s[j]))
            chis[i][j] = chi
            chis[j][i] = chi

            if chi_prime:
                d[j] += 1
                fs = state_on(d)
                ev, _evec = closest_state_to(fs)
                chip = (ev - (f1s[i] + 2 * f1s[j]) - 2 * chis[i][j])
                chips[i][j] = chip
                chips[j][i] = chip

    return np.array(f1s), np.array(chis)
