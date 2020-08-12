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
Module containing Basic Qiskit Metal Planar (2D) design for CPW type geometry.

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

    # TODO How to get the values into self.chip.
    # For now, just hard code in something.
    def __init__(self):
        super(DesignPlanar, self).__init__()
        self._chips['minx'] = '0'
        self._chips['miny'] = '0'
        self._chips['maxx'] = '1234'  # ?????? and which units
        self._chips['maxy'] = '4567'  # ?????? and which units

        # or something like below.
        size_tuple = (0, 0, 1234, 4567)    # tuple=(minx, miny, maxx, maxy)
        self._chips['main'] = size_tuple

        # I think this is short and sweet, there is only one chip based on doc-string above.
        self._chips['size'] = size_tuple
