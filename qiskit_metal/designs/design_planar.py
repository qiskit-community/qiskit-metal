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
Basic Qiskit Metal Planar (2D) design for CPW type geometry.


@date: 2019
@author: Zlatko Minev, Thomas McConeky, ... (IBM)
"""

from .design_base import QDesign

__all__ = ['DesignPlanar']

class DesignPlanar(QDesign):
    """Metal class for a planar (2D) design, consisting of a single plane chip.
    Typically assumed to have some CPW geometires.

    Inherits QDesign class.
    """
    pass