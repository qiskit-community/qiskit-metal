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

"""File contains dictionary for NSquareSpiral and the make()."""

from qiskit_metal import draw, Dict
from qiskit_metal.components.base import QComponent
import numpy as np


class ResonatorRectangleSpiral(QComponent):
    """A rectnagle spiral resonator based on length input. The X dimension is modified
    by the code based on the total length inputed.

    Inherits `QComponent` class

    Description:
        A rectangular spiral resonator. The width of the spiral is modified based on inputted values
        and given total length of the spiral.
        ::

            <--------X-------->
            __________________
            |   ___________   |
            |  |           |  |
            |  |           |  |
            |  |______________|
            |

    Options:
        Convention: Values (unless noted) are strings with units included,
        (e.g., '30um')

        * n: number of turns of the spiral
        * length: total length of the spiral
        * line_width: the width of the line of the spiral
        * height: the height of the inner portion of the spiral
        * gap: the distance between each layer of the spiral
        * coupler_distance: the pin position from the grounded termination of the spiral
        * pos_x/_y: the x/y position of the ground termination.
        * rotation: the direction of the termination. 0 degrees is +x, following a
          counter-clockwise rotation (eg. 90 is +y)
        * chip: the chip the pin should be on.
        * layer: layer the pin is on. Does not have any practical impact to the short.
    """
    component_metadata = Dict(
        short_name='res'
        )
    """Component metadata"""

    default_options = Dict(
        n='3',
        length='2000um',
        line_width='1um',
        height='40um',
        gap='4um',
        coupler_distance='10um',
        pos_x='0um',
        pos_y='0um',
        rotation='0',
        chip='main',
        layer='1'
    )
    """Default drawing options"""

    def make(self):
        """
        The make function implements the logic that creates the geoemtry
        (poly, path, etc.) from the qcomponent.options dictionary of parameters,
        and the adds them to the design, using qcomponent.add_qgeometry(...),
        adding in extra needed information, such as layer, subtract, etc.
        """
        p = self.p  # p for parsed parameters. Access to the parsed options.
        n = int(p.n)
        # Create the geometry

        spiral_list = []

        #Formulat to determine the size of the spiral based on inputed length.
        x_n = (p.length/(2*n)) - (p.height + 2*(p.gap + p.line_width) * (2*n - 1))

        if x_n <= p.gap+p.line_width:
            self._error_message = f'Inputted values results in the width of the spiral being too small.'
            self.logger.warning(self._error_message)
            return
 

        for step in range(n):
            x_point = x_n/2 + step*(p.line_width+p.gap)
            y_point = p.height/2 + step*(p.line_width+p.gap)

            spiral_list.append((-x_point, -y_point))
            spiral_list.append((x_point, -y_point))
            spiral_list.append((x_point, y_point))
            spiral_list.append((-x_point-(p.line_width+p.gap), y_point))

        x_point = (x_n/2 + (step+1)*(p.line_width+p.gap))
        y_point = (p.height/2 + (step+1)*(p.line_width+p.gap)-p.line_width/2)
        spiral_list.append((-x_point, -y_point))
        spiral_list = draw.LineString(spiral_list)

        spiral_etch = draw.shapely.geometry.box(-(x_point+p.line_width/2+p.gap),-y_point, 
            x_point-p.line_width/2, y_point)
        #Generates a linestring to track port location
        points = draw.LineString([(-x_point+p.line_width/2, -y_point+p.coupler_distance), 
            (-x_point-p.line_width/2, -y_point+p.coupler_distance)])

        c_items = [spiral_list, spiral_etch,points]
        c_items = draw.rotate(c_items, p.rotation, origin=(0, 0))
        c_items = draw.translate(c_items, p.pos_x, p.pos_y)
        [spiral_list, spiral_etch, points] = c_items
        ##############################################
        # add elements
        self.add_qgeometry('path', {'n_spiral': spiral_list}, width=p.line_width)
        self.add_qgeometry('poly', {'n_spira_etch':spiral_etch}, subtract=True)

        
        # NEW PIN SPOT
        self.add_pin('spiralPin',
                     points=np.array(points.coords),
                     width=p.line_width, input_as_norm=True)
