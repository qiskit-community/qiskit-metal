from typing import Dict as Dict_
from typing import List

import numpy as np
import qutip
from qutip import Qobj


def basis_state_on(mode_size: List[int], excitations: Dict_[int, int]):
    ''' excitations = {mode number: # of photons}
        give me the value excitations[i] or 0 if index i not in excitations;
        i.e., by default ground state.
    '''
    return qutip.tensor(*[
        qutip.basis(mode_size[i], excitations.get(i, 0))
        for i in range(len(mode_size))
    ])


def extract_energies(H: Qobj, zero_evals=True, chi_prime=False):

    mode_size = H.dims[0]  # how many levels for each mode like [20, 12]

    print("Processing eigensystem...", end='')
    evals, evecs = H.eigenstates()
    print("\rFinished eigensystem.     ")

    if zero_evals:
        evals -= evals[0]  # zero out

    # if use_1st_order:
    # TOOD: Copy from pyEPR
    def closest_state_to(s: Qobj):

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
