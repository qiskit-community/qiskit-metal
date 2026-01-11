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
                     zero_evals: bool = True):
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

    Returns:
        np.ndarray, np.ndarray: a tuple of arrays. The first array is the frequencies of
            the modes. The second array is a matrix where the diagonal entries are the
            anharmonicities of the modes and the off-diagonal entries are the dispersive
            shifts, i.e., the chi's between the modes
    """

    evals, evecs = esys_array

    if zero_evals:
        evals -= evals[0]  # zero out

    N = len(mode_size)

    def state_on(excitations):
        return basis_state_on(mode_size, excitations)  # eigenstate on

    chis = np.empty((N, N))

    # Reformat the set of eigenvectors as a matrix where each row of the matrix
    # is the hermitian conjugate of the original eigenvector
    evecs_dag_mat = np.squeeze(
        np.array([evecs[ii].dag() for ii in range(evecs.size)]))

    single_excitation_states = [state_on({i: 1}) for i in range(N)]

    # Prepare states with 2-photon excitations, either in two separate modes or
    # the same mode
    double_excitation_states = []
    mode_idx_to_state = {}
    for i in range(N):
        for j in range(i, N):
            d = {k: 0 for k in range(N)}  # put 0 photons in each mode (k)
            # load ith mode and jth mode with 1 photon
            d[i] += 1
            d[j] += 1
            # mode_idx_to_state keeps track of mode excitation index for each state
            mode_idx_to_state[(i, j)] = len(double_excitation_states)
            double_excitation_states.append(state_on(d))

    # Format the target states as a matrix where each column of the matrix
    # is one of the target states

    single_excitation_states_mat = np.squeeze(
        np.array([
            single_excitation_states[ii]
            for ii in range(len(single_excitation_states))
        ])).T

    double_excitation_states_mat = np.squeeze(
        np.array([
            double_excitation_states[ii]
            for ii in range(len(double_excitation_states))
        ])).T

    # Find the inner product of each of the target state with each of the
    # eigenvector; hence overlap has dimension of number of eigenvectors x number of target states
    overlap_single = np.absolute(
        np.array((Qobj(evecs_dag_mat) * Qobj(single_excitation_states_mat))))
    overlap_double = np.absolute(
        np.array((Qobj(evecs_dag_mat) * Qobj(double_excitation_states_mat))))

    # find the index of the eigenvector that is closest to each target state
    # hence evec_idx has shape of (number of target states, )
    evec_idx_single = np.argsort(overlap_single, axis=0)[::-1, :][0]
    evec_idx_double = np.argsort(overlap_double, axis=0)[::-1, :][0]

    for i in range(N):
        for j in range(i, N):
            ev = evals[evec_idx_double[mode_idx_to_state[(i, j)]]]
            chi = (ev - (evals[evec_idx_single[i]] + evals[evec_idx_single[j]]))
            chis[i, j] = chi
            chis[j, i] = chi

    return evals[evec_idx_single], chis
