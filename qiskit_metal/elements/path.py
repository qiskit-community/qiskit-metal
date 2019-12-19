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
This is the main module that defines what a path element is in Qiskit Metal.

@author: Zlatko Minev, Thomas McConekey, ... (IBM)
@date: 2019
"""

from .base import BaseElement, BaseGeometry, BaseComponent


class PathElement(BaseElement):
    """
    Class to handle paths, such as CPWs, or other structures that can be defined
    by linestrings, rather than by polygons.
    Elements that can buffered, etc.
    """

    def __init__(self,
                 name: str,
                 geom: BaseGeometry,
                 parent: BaseComponent,
                 width: (str, float),
                 chip=None,
                 fillet=None,
                 subtract=False,
                 ):
        """

        Arguments:
            name {str} -- [description]
            geom {BaseGeometry} -- [description]
            parent {BaseComponent} -- [description]
            width {[type]} -- If width is zero, then draw as line.

        Keyword Arguments:
            chip {[type]} -- [description] (default: {None})
            fillet {[type]} -- [description] (default: {None})
            subtract {bool} -- [description] (default: {False})
        """
        super().__init__(name, geom, parent, chip=chip, fillet=fillet, subtract=subtract)
        self.width = width

    def get_length(self):
        """
        Returns the lenght of the path element.
        """
        raise NotImplementedError()
