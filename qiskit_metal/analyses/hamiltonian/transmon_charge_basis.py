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
"""Models the transmon qubit in the cooper-pair charge basis, assuming wrapped
junction phase variable. This model is closer to the analytic solution than the
Duffing oscillator model. Can work backwards from target qubit parameters to
get the Ej, Ec or use input Ej, Ec to find the spectrum of the Cooper Pair Box.

@author: Christopher Warren (Chalmers University of Technology), updated by Zlatko K. Minev (IBM Quantum)
"""
# pylint: disable=invalid-name

import numpy as np
import qutip as qt
import scipy.linalg as linalg
import scipy.optimize as opt


class Hcpb:
    """Hamiltonian-model Cooper pair box (Hcpb) class.

    Used to model analytically the CPB Hamiltonian quickly
    and efficiently. Solves in charge basis tridiagonal eigenvalue
    problem for arbitrary Ej, Ec, ng values.

    As long as nlevels remains fixed the number of charge states
    considered does not change and it does not recreate the arrays,
    just recomputes the properties

    Returns all properties of interest for the CPB.
    """

    def __init__(self,
                 nlevels: int = 15,
                 Ej: float = None,
                 Ec: float = None,
                 ng: float = 0.5):
        """Generate a Cooper-pair box (CPB) model.

        Args:
            nlevels (int): Number of charge states of the CPB [-nlevels, nlevels+1]
            Ej (float): Josephson energy of the JJ
            Ec (float): Charging energy of the CPB
            ng (float): Offset charge of the CPB (ng=0.5 is the sweet spot).
                        `ng` only needs to run between -0.5 and 0.5.
                        `ng` is defined in units of cooper pairs (2e)

        Example use:

            .. code-block::

                H = Hcpb(nlevels=15, Ej=13971.3, Ec=295.2, ng=0.001)

                print(f'''
                Transmon frequencies
                ω01/2π = {H.fij(0,1): 6.0f} MHz
                  α/2π = {H.anharm(): 6.0f} MHz
                ''')

            .. code-block::

                import matplotlib.pyplot as plt
                for k in range (3):
                    ψ, θ = H.psi_k(k)
                    plt.plot(θ, ψ.real+ψ.imag, label=f"|{k}>") # it's in either quadrature, but not both
                plt.xlabel("Junction phase θ (wrapped in the interval [-π, π])")
                plt.ylabel("Re(ψ(θ))")
                plt.legend(title="Level")
        """

        self._nlevels = nlevels
        self._Ej = Ej
        self._Ec = Ec
        self._ng = ng
        self.evals = None
        self.evecs = None
        # Generate the diagonal and offdiagonal components of the Hamiltonian
        self._gen_operators()
        # compute the eigenvectors and eigenvalues of the CPB
        # all properties can be derived from these
        self._calc_H()

    def _gen_operators(self):
        """Generate at initialization the number of levels and only recompute
        the size of the problem if nlevels changes."""

        self._diag = np.arange(-self._nlevels, self._nlevels + 1)
        self._off = np.ones(len(self._diag) - 1)

    def _calc_H(self):
        """Only diagonalize the Hamiltonian if the CPB is supplied with the
        three mandatory parameters Ej, Ec, ng, but allow for them to not be set
        at initialization."""
        if (self._Ej is None) or (self._Ec is None) or (self._ng is None):
            self.evals = None
            self.evecs = None
        else:
            self._diagonalize_H()

    def _diagonalize_H(self):
        """Diagonalize the CPB Hamiltonian using symmetric tridiagonal
        eigensolver for efficient calculation of properties."""
        ham_diag = 4 * self._Ec * (self._diag - self._ng)**2
        ham_off = -(self._Ej / 2.0) * self._off
        evals, evecs = linalg.eigh_tridiagonal(ham_diag, ham_off)
        self.evals = np.real(np.array(evals))
        self.evecs = np.array(evecs)

    def evalue_k(self, k: int):
        """Return the eigenvalue of the Hamiltonian for level k.

        Args:
            k (int): Index of the eigenvalue

        Returns:
            float: eigenvalue of the Hamiltonian
        """
        return self.evals[k]

    def evec_k(self, k: int):
        """Return the eigenvector of the CPB Hamiltonian for level k.

        Args:
            k (int): Index of eigenvector

        Returns:
            array: Eigenvector of the \|k> level of the CPB Hamiltonian
        """
        return self.evecs[:, k]

    def psi_k(self, k: int, pts: int = 1001):
        """Return the wavevector of the CPB Hamiltonian in the flux basis. Made
        compact over the interval of [-pi, pi].

        Args:
            k (int): index of wavevector corresponding to the
                     \|k> eigenstate
            pts (int): Number of points to approximate the wavevector
                       in the interval [-pi, pi]. Defaults to 1001.

        Returns:
            array: Wavevector corresponding the \|k> eigenstate
        """
        phi = np.linspace(-np.pi, np.pi, pts)
        evec = self.evecs[:, k]
        n = np.arange(-self._nlevels, self._nlevels + 1)
        psi = []
        for i, val in enumerate(n):
            # Get Fourier component of each charge basis state
            psi.append(evec[i] * np.exp(1j * val * phi))
        psi = np.array(psi)
        # Sum over Fourier components to get eigenwave
        psi = np.sum(psi, axis=0) / np.sqrt(2 * np.pi)
        # Normalize Psi
        norm = np.sqrt(np.dot(psi, psi.conj()))
        psi = psi / norm
        return psi, phi

    def fij(self, i: int, j: int):
        """Compute the transition energy (or frequency) between states.

        \|i> and \|j>.

        Args:
            i (int): Index of state \|i>
            j (int): Index of state \|j>

        Returns:
            float: Eij, the transition energy
        """
        return np.abs(self.evalue_k(i) - self.evalue_k(j))

    def anharm(self):
        """Compute the anharmonicity of the CPB.

        Returns:
            float: Anharmonicty defined as E12-E01
        """
        return self.fij(1, 2) - self.fij(0, 1)

    def n_ij(self, i: int, j: int):
        """Compute the value of the number operator for coupling elements
        together in the energy eigen-basis.

        Args:
            i (int): \|i> Index of the transmon
            j (int): \|j> Index of the transmon

        Returns:
            float: Matrix element corresponding to the
            number operator in the transmon basis
            `n_ij = |<i|n|j>|`
        """
        n_op = np.arange(-self._nlevels, self._nlevels + 1)
        n_ij = np.conj(self.evec_k(i)) * n_op * self.evec_k(j)
        n_ij = np.abs(np.sum(n_ij))
        return n_ij

    def h0_to_qutip(self, n_transmon: int):
        """Wrapper around Qutip to output the diagonalized Hamiltonian
        truncated up to n levels of the transmon for modeling.

        Args:
            n_transmon (int): Truncate up to n levels of the
                              Transmon Hamiltonian

        Returns:
            Qobj: Returns a Qutip Qobj for the diagonalized
            transmon
        """
        ham = np.diag(self.evals[:n_transmon] - self.evals[0])
        return qt.Qobj(ham)

    def n_to_qutip(self, n_transmon: int, thresh=None):
        """Wrapper around Qutip to output the number operator (charge) for the
        Transmon Hamiltonian in the energy eigen-basis. Used for computing the
        coupling between other elements in the system.

        Args:
            n_transmon (int): Number of energy levels to consider
            thresh (float): Threshold for keeping small values
                            in the number operator i.e `n_{i,i+2}`
                            terms drop off exponentially. If None
                            retain all terms. Defaults to None

        Returns:
            Qobj: Returns a Qutip Qobj corresponding to the
            number operator for defining couplings in the
            energy eigen-basis.
        """
        n_op = np.zeros((n_transmon, n_transmon))
        for i in range(n_transmon):
            for j in range(n_transmon):
                if i == j:
                    n_op[i, j] = 0
                else:
                    val = self.n_ij(i, j)
                    if thresh is not None:
                        if val < thresh:
                            val = 0
                    n_op[i, j] = val
        return qt.Qobj(n_op)

    def params_from_spectrum(self, f01: float, anharm: float, **kwargs):
        """Method to work backwards from a desired transmon frequency and
        anharmonicty to extract the target Ej and Ec for design and
        fabrication. Updates the class to include these Ej and Ec as the new
        values for extracting properties.

        Args:
            f01 (float): Desired qubit frequency
            anharm (float): Desired qubit anharmonicity (should be negative)

        Keyword Args:
            Passed to least_squares

        Returns:
            (float, float): Ej and Ec of the transmon Hamiltonian
            corresponding to the f01 and anharmonicty
            of the device
        """
        # Anharmonicty should be negative for the Transmon
        if anharm > 0:
            anharm = -anharm

        def fun(x):
            self.Ej = x[0]
            self.Ec = x[1]
            # the 10 on the anharmonicity allows faster convergnce, see Minev
            return (self.fij(0, 1) - f01)**2 + 10 * (self.anharm() - anharm)**2

        # Initial guesses from
        # f01 ~ sqrt(8*Ej*Ec) - Ec
        #  eta ~ -Ec
        x0 = [(f01 - anharm)**2 / (8 * (-anharm)), -anharm]
        # can converge slowly if cost function not set up well, or alpha<<freq
        ops = dict(bounds=[(0, 0), (x0[0] * 3, x0[1] * 3)],
                   f_scale=1 / x0[0],
                   max_nfev=2000)
        res = opt.least_squares(fun, x0, **{**ops, **kwargs})
        self.Ej, self.Ec = res.x
        return res.x

    def params_from_freq_fixEC(self, f01: float, Ec: float, **kwargs):
        """Find transmon Ej given a fixed EC and frequency.

        Args:
            f01 (float): Desired qubit frequency
            Ec (float): Qubit EC (4ECn^2) in same units as f01

        Returns:
            float: Ej in same units
        """

        def fun(x):
            self.Ej = x[0]
            self.Ec = Ec
            # the 15 on the anharmonicity allows faster convergnce, see Minev
            return (self.fij(0, 1) - f01)**2 + 15 * (self.anharm() - Ec)**2

        x0 = [(f01 - Ec)**2 / (8 * (Ec))]
        # can converge slowly if cost function not set up well, or alpha<<freq
        ops = dict(bounds=[(0,), (x0[0] * 3,)],
                   f_scale=1 / x0[0],
                   max_nfev=2000)
        res = opt.least_squares(fun, x0, **{**ops, **kwargs})
        self.Ej = res.x[0]
        self.Ec = Ec
        return res.x[0]

    @property
    def nlevels(self):
        """Return the number of levels."""
        return self._nlevels

    @nlevels.setter
    def nlevels(self, value: int):
        """Set the number of levels and recompute the Hamiltonian with the new
        size."""
        self._nlevels = value
        self.__init__(value)

    @property
    def Ej(self):
        """Returns Ej."""
        return self._Ej

    @Ej.setter
    def Ej(self, value: float):
        """Set Ej and recompute properties."""
        self._Ej = value
        self._calc_H()

    @property
    def Ec(self):
        """Return Ec."""
        return self._Ec

    @Ec.setter
    def Ec(self, value: float):
        """Set Ec and recompute properties."""
        self._Ec = value
        self._calc_H()

    @property
    def ng(self):
        """Return ng."""
        return self._ng

    @ng.setter
    def ng(self, value: float):
        """Set ng and recompute properties."""
        self._ng = value
        self._calc_H()
