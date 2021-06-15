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
Models the transmon qubit in the cooper-pair charge basis
and calculate the exact (analytic) solutions

@author: Nick Lanzillo (IBM)
"""
# pylint: disable=invalid-name

import numpy as np
from scipy.special import mathieu_a


class Hcpb_analytic:
    """
    Analytic version of Hamiltonian-model Cooper pair box (Hcpb) class.

    Used calculate the exact eigenvalues for arbitrary Ej, Ec, ng values.
    """

    def __init__(self, Ej: float = None, Ec: float = None, ng: float = 0.5):
        """
        Generate a Cooper-pair box (CPB) model.

        Arguments:
            Ej (float): Josephson energy of the JJ
            Ec (float): Charging energy of the CPB
            ng (float): Offset charge of the CPB (ng=0.5 is the sweet spot).
                        `ng` only needs to run betweren -0.5 and 0.5.
                        `ng` is defined in units of cooper pairs (2e)
        """

        self._Ej = Ej
        self._Ec = Ec
        self._ng = ng
        self.evals = None
        self.evecs = None
        # Generate the diagonal and offdiagonal components of the Hamiltonian
        #self._gen_operators()
        # compute the eigenvectors and eigenvalues of the CPB
        # all properties can be derived from these
        #self._calc_H()

    def evalue_k(self, k: int):
        """
        Return the eigenvalue of the Hamiltonian for level k.

        Arguments:
            k (int): Index of the eigenvalue

        Returns:
            float: eigenvalue of the Hamiltonian
        """
        if self._ng == 0:
            index = k + 1.0 - ((k + 1.0) % 2.0)
        else:
            index = k + 1.0 - ((k + 1.0) % 2.0) + 2.0 * self._ng * (
                (-1.0)**(k - 0.5 * (np.sign(self._ng) - 1.0)))

        self.evals = self._Ec * mathieu_a(index, -0.5 * self._Ej / self._Ec)
        #return self.evals[k]
        return self.evals
