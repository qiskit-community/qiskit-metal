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


class OpenToGround(QComponent):
    """A sample_shapes open to ground termination. Functions as a pin for auto drawing.

    Inherits `QComponent` class.

    Default Options:
        * width: '10um' -- The width of the 'cpw' terminating to ground (this is merely
          for the purpose of generating a value to pass to the pin)
        * gap: '6um' -- The gap of the 'cpw'
        * termination_gap: '6um' -- The length of dielectric from the end of the cpw center trace to the ground.
        * pos_x: '0um' -- The x position of the ground termination.
        * pos_y: '0um' -- The y position of the ground termination.
        * rotation: '0' -- The direction of the termination. 0 degrees is +x, following a
          counter-clockwise rotation (eg. 90 is +y)
        * chip: 'main' -- The chip the pin should be on.
        * layer: '1' -- Layer the pin is on. Does not have any practical impact to the short.

    Values (unless noted) are strings with units included, (e.g., '30um')
    """
    component_metadata = Dict(short_name='term', _qgeometry_table_poly='True')
    """Component metadata"""

    default_options = Dict(width='10um',
                           gap='6um',
                           termination_gap='6um',
                           pos_x='0um',
                           pos_y='0um',
                           orientation='0',
                           chip='main',
                           layer='1')
    """Default connector options"""

    TOOLTIP = """A basic open to ground termination. """

    def make(self):
        """Build the component."""
        p = self.p  # p for parsed parameters. Access to the parsed options.

        port_line = draw.LineString([(0, -p.width / 2), (0, p.width / 2)])
        open_termination = draw.box(0, -(p.width / 2 + p.gap),
                                    p.termination_gap, (p.width / 2 + p.gap))
        # Rotates and translates the connector polygons (and temporary port_line)
        polys = [open_termination, port_line]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [open_termination, port_line] = polys

        # Subtracts out ground plane on the layer its on
        self.add_qgeometry('poly', {'open_to_ground': open_termination},
                           subtract=True,
                           layer=p.layer)

        # Generates the pins
        self.add_pin('open', port_line.coords, p.width)
