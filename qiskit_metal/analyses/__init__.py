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
=================================================
Analyses (:mod:`qiskit_metal.analyses`)
=================================================

.. currentmodule:: qiskit_metal.analyses

Module containing all Qiskit Metal analyses.

.. _qanalysis:


Analysis Core
-------------

.. autosummary::
    :toctree:

    QAnalysis
    QSimulation

Hamiltonian
-----------

.. autosummary::
    :toctree:

    Hcpb
    Hcpb_analytic
    HO_wavefunctions
    transmon_analytics

Electromagnetic & quantization / parameter extraction
-----------------------------------------------------

.. autosummary::
    :toctree:

    cpw_calculations
    kappa_calculation

Sweeping Options
----------------

.. autosummary::
    :toctree:

    Sweeper

Quantization
------------

.. autosummary::
    :toctree:

    LOManalysis
    EPRanalysis
    lumped_capacitive

Simulation
------------

.. autosummary::
    :toctree:

    LumpedElementsSim
    EigenmodeSim
    ScatteringImpedanceSim

"""

from .. import config

from .core import QAnalysis
from .core import QSimulation
from .em import cpw_calculations
from .em import kappa_calculation
from .quantization import lumped_capacitive
from .quantization import EPRanalysis
from .quantization import LOManalysis
from .simulation import LumpedElementsSim
from .simulation import EigenmodeSim
from .simulation import ScatteringImpedanceSim
from .hamiltonian.transmon_charge_basis import Hcpb
from .hamiltonian import HO_wavefunctions
from .hamiltonian import transmon_analytics
from .hamiltonian.transmon_CPB_analytic import Hcpb_analytic
from .sweep_and_optimize.sweeper import Sweeper
