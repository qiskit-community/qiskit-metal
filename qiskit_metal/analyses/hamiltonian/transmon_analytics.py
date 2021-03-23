import numpy as np
from math import *
from scipy.special import mathieu_a, mathieu_cem
import matplotlib.pyplot as plt
from sympy import mathieuc, mathieus

# this function calculates the index passed to the Mathieu characteristic function
# in the calculation of the eigenvalues for a given offset charge (ng) and energy level (m) 
def kidxRAW(m, ng):
    if ng==0:
        return m + 1.0 - ((m+1.0)%2.0) 
    else:
        return m + 1.0 - ((m+1.0)%2.0) + 2.0*ng*((-1.0)**(m - 0.5*(np.sign(ng)-1.0)))

def kidx(m, ng):
    return kidxRAW(m, ng) 

# define the Josephson to charging energy ratio E_J / E_C
ratio = 1.0

# define the charing energy 
E_C = 1.0

# this function calculates the eigenvalue (energy) for a given offset charge (ng)
# and energy level (m). Note that the scipy implementation of Mathieu characteristic
# values can only accept integer values of index. 
def transmon_eigenvalue(m,ng): 
    index = kidx(m,ng)
    return (E_C)*mathieu_a(index, -0.5*ratio)

# extremely coarse grid: only three points from -0.5 to 0.5. This so that only integer values
# of the index are used in the calculation of the Mathieu characteristic value. 
ng = np.linspace(-0.5,0.5,3)

# ng is periodic extending from -2 to 2: 
ng_periodic = np.linspace(-2.0, 2.0,9)

# define energies between (-0.5, 0.5) as empty lists. 
E0 = []
E1 = []
E2 = [] 
E3 = []

# define periodic energies between (-2.0, 2.0) 
E0_periodic = [None]*9
E1_periodic = [None]*9
E2_periodic = [None]*9
E3_periodic = [None]*9

# calculate the energies for m=0,1,2
for i in ng:
    E0.append(transmon_eigenvalue(0,i))
    E1.append(transmon_eigenvalue(1,i))
    E2.append(transmon_eigenvalue(2,i))
    E3.append(transmon_eigenvalue(3,i)) 
 
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
        E0_periodic[i] = E0_periodic[i-2]
        E1_periodic[i] = E1_periodic[i-2]
        E2_periodic[i] = E2_periodic[i-2] 
        E3_periodic[i] = E3_periodic[i-2] 

# plot the PERIODIC eigen energies between (-2.0, 2.0) 
plt.plot(ng_periodic, E0_periodic, 'k') # m=0 
plt.plot(ng_periodic, E1_periodic, 'r') # m=1
plt.plot(ng_periodic, E2_periodic, 'b') # m=2 
plt.plot(ng_periodic, E3_periodic, 'm') # m=3
plt.xlabel("Offset Charge [ng]")
plt.ylabel("Energy E_m[ng]") 