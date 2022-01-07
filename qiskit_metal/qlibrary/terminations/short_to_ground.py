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

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent
import numpy as np


class ShortToGround(QComponent):
    """A sample_shapes short to ground termination. Functions as a pin for auto CPW
    drawing.

    Inherits `QComponent` class.

    .. meta::
        Short to Ground

    Default Options:
        * width: '10um' -- The width of the 'cpw' terminating to ground (this is merely for the purpose of
          generating a value to pass to the pin)

    Values (unless noted) are strings with units included, (e.g., '30um')
    """
    component_metadata = Dict(short_name='term')
    """Component metadata"""

    default_options = Dict(width='10um')
    """Default connector options"""

    TOOLTIP = """A basic short to ground termination"""

    def make(self):
        """Build the component."""
        p = self.p  # p for parsed parameters. Access to the parsed options.

        port_line = draw.LineString([(0, -p.width / 2), (0, p.width / 2)])

        # Rotates and translates the connector polygons (and temporary port_line)
        port_line = draw.rotate(port_line, p.orientation, origin=(0, 0))
        port_line = draw.translate(port_line, p.pos_x, p.pos_y)

        port_points = list(draw.shapely.geometry.shape(port_line).coords)

        #Generates the pin
        self.add_pin('short', port_points, p.width)
