# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

'''
@date: 2019
@author: Qiskit Team
'''

from qiskit_metal import draw, Dict
from qiskit_metal.components.base import QComponent
import numpy as np

class ShortToGround(QComponent):
    """A basic short to ground termination. Functions as a pin for auto CPW drawing.

    Inherits `QComponent` class


    Options:
        * width: the width of the 'cpw' terminating to ground (this is merely for the purpose of
          generating a value to pass to the pin)
        * pos_x/_y: the x/y position of the ground termination.
        * rotation: the direction of the termination. 0 degrees is +x, following a
          counter-clockwise rotation (eg. 90 is +y)
        * chip: the chip the pin should be on.
        * layer: layer the pin is on. Does not have any practical impact to the short.

    Values (unless noted) are strings with units included, (e.g., '30um')
    """
    component_metadata = Dict(
        short_name='term'
        )
    """Component metadata"""

    default_options = Dict(
        width='10um',
        pos_x='0um',
        pos_y='0um',
        rotation='0',
        chip='main',
        layer='1'
    )
    """Default connector options"""

    def make(self):
        """Build the component"""
        p = self.p  # p for parsed parameters. Access to the parsed options.

        port_line = draw.LineString([(0, -p.width/2), (0, p.width/2)])

        # Rotates and translates the connector polygons (and temporary port_line)
        port_line = draw.rotate(port_line, p.rotation, origin=(0, 0))
        port_line = draw.translate(port_line, p.pos_x, p.pos_y)

        port_points = list(draw.shapely.geometry.shape(port_line).coords)
        self.add_pin('short', port_points, p.width)
        #HOW TO ADD A 0 volume element to a table for the GUI? Or not even needed?
