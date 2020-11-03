# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""

Google doc format - follow docathon guidelines

* Created 2019-03-09 - Thomas McConkey

Listing of each variable with reference to paper: 10.1109/TMTT.2019.2893639

**Qubit**
w_i : qubit mode i's frequency
w_Ji : bare qubit mode i's frequency
C_i : total shunt capacitance of qubit i
L_Ji : bare junction inductance of qubit i
E_Ci : charging energy of qubit i
d_i : anharmonicity of qubit i

**Resonator**


**Coupling**
J_ij : exchange coupling rate between qubit modes i and j (see coupling_rate_J_ij)
chi_ik : disperisve energy shift between qubit mode i and resonator mode k (see dispersive_chi_ik)
e_id : coupling of qubit mode i to voltage source d

"""

import numpy as np

# define constants
h = 6.62606957e-34
hbar = 1.0545718E-34
phinot = 2.067*1E-15
e = 1.60217657e-19


E_Ci = e^2 / (2*C_i)
d_i = -E_Ci * (w_Ji / w_i)^2
w_Ji = 1/(np.sqrt(L_Ji * C_i))
w_i = w_Ji - (E_Ci / hbar - E_Ci/(hbar*w_Ji))



def import_impedance_matrix(): #or might import S-matrix and change into impedance matrix?
    pass

def import_capacitance_matrix(): #same as for Jay's code
    pass

def coupling_rate_J_matrix():
    
    
    return


def coupling_rate_J_ij(w_i,w_j,L_i,L_j,Z_ij_w_i,Z_ij_w_j):
    return (-1/4) * np.sqrt(w_i*w_j/(L_i*L_j))*np.imag((Z_ij_w_i/w_i) + (Z_ij_w_j/w_j))



def dispersive_chi_ik():
    return 8*d_i
