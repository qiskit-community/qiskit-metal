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
=================================================
Designs (:mod:`qiskit_metal.designs`)
=================================================

.. currentmodule:: qiskit_metal.designs

Module containing all Qiskit Metal designs.

@date: 2019

@author: Zlatko Minev (IBM)

UNDER CONSTRUCTION


QDesign
---------------

.. autosummary::
    :toctree: ../stubs/

    QDesign


DesignPlanar
---------------

.. autosummary::
    :toctree: ../stubs/

    DesignPlanar


QNet
---------------

.. autosummary::
    :toctree: ../stubs/

    QNet

"""

from .. import Dict
from .. import is_design
from .design_base import QDesign
from .design_planar import DesignPlanar
from .net_info import QNet
#from .interface_components import Components
