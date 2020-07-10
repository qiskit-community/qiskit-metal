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
Parsed dynamic attributes.

@author: Zlatko Minev
@date: 2020
"""

from qiskit_metal import Dict
from qiskit_metal import draw
from .base import QComponent
#from qiskit_metal.toolbox_metal.parsing import is_true


class MyQComponent(QComponent):
    """
    `MyQComponent` base class.

    Inherits components.QComponent class

    Use this class as a template for your components - have fun
    """

    # EDIT HERE
    # Define the default tempate options
    default_options = Dict(
        width='500um',
        height='300um',
        pos_x='0um',
        pos_y='0um',
        rotation='0',
        layer='1'
    )
    """Default drawing options"""

   # pylint: disable=invalid-name
    def make(self):
        """Draw the component"""

        p = self.parse_options()  # Parse the string options into numbers

        # EDIT HERE - Replace the following with your code

        # Create some raw geometry -- See autocompletion for the `draw` module
        rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        rect = draw.rotate(rect, p.rotation)
        # Create QGeometry from a polygon
        geom = {'my_polygon': rect}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)
