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
'''
@date: 2019
@author: Qiskit Team
'''

from qiskit_metal import draw, Dict
from qiskit_metal.components.base import QComponent
import numpy as np

class CPWHangerT(QComponent):
    """Generates a three pin (+) structure comprised of a primary two pin CPW transmission line,
    and a secondary one pin neigbouring CPW transmission line that is capacitively/inductively
    coupled to the primary. Such a structure can be used, as an example, for generating
    CPW resonator hangars off of a transmission line.

    Inherits QComponent class.

    ::

        +----------------------------+
        ------------------------------
        |
        |
        |
        |
        +

    Options:
        * prime_width: the width of the trace of the two pin CPW transmission line
        * prime_gap: the dielectric gap of the two pin CPW transmission line
        * second_width: the width of the trace of the one pin CPW transmission line
        * second_gap: the dielectric gap of the one pin CPW transmission line
        * coupling_space: the amound of ground plane between the two transmission lines
        * coupling_length: the length of parallel between the two transmission lines
          note: this includes the distance of the curved second of the second line
        * pos_x/_y: the x/y position of the ground termination.
        * rotation: the direction of the termination. 0 degrees is +x, following a
          counter-clockwise rotation (eg. 90 is +y)
        * mirror: flips the hanger around the y-axis
        * open_termination: sets if the termination of the second line at the coupling side
          is an open to ground or short to ground
        * chip: the chip the pin should be on.
        * layer: layer the pin is on. Does not have any practical impact to the short.
    """
    component_metadata = Dict(
        short_name='cpw'
        )
    """Component metadata"""

    #Currently setting the primary CPW length based on the coupling_length
    #May want it to be it's own value that the user can control?
    default_options = Dict(
        prime_width='10um',
        prime_gap='6um',
        second_width='10um',
        second_gap='6um',
        coupling_space='3um',
        coupling_length='100um',
        fillet='25um',
        pos_x='0um',
        pos_y='0um',
        rotation='0',
        mirror=False,
        open_termination=True, #Better way to decide this?
        chip='main',
        layer='1'
    )
    """Default connector options"""

    def make(self):
        """Build the component"""
        p=self.p

        prime_cpw_length = p.coupling_length*2
        second_flip = 1
        if p.mirror: second_flip = -1

        #Primary CPW
        prime_cpw = draw.LineString([[-prime_cpw_length/2, 0], [prime_cpw_length/2, 0]])

        #Secondary CPW
        second_down_length = p.coupling_length*2
        second_y = -p.prime_width/2 - p.prime_gap - p.coupling_space - p.second_gap - p.second_width/2
        second_cpw = draw.LineString([[second_flip*(-p.coupling_length/2), second_y],
                                        [second_flip*(p.coupling_length/2), second_y],
                                        [second_flip*(p.coupling_length/2), second_y-second_down_length]])

        second_termination = 0
        if p.open_termination: second_termination = p.second_gap

        second_cpw_etch = draw.LineString([[second_flip*(-p.coupling_length/2 - second_termination), second_y],
                                        [second_flip*(p.coupling_length/2), second_y],
                                        [second_flip*(p.coupling_length/2), second_y-second_down_length]])

        #Rotate and Translate
        c_items = [prime_cpw, second_cpw, second_cpw_etch]
        c_items = draw.rotate(c_items, p.rotation, origin=(0, 0))
        c_items = draw.translate(c_items, p.pos_x, p.pos_y)
        [prime_cpw, second_cpw, second_cpw_etch] = c_items

        #Add to qgeometry tables
        self.add_qgeometry('path', {'prime_cpw': prime_cpw}, width=p.prime_width)
        self.add_qgeometry('path', {'prime_cpw_sub': prime_cpw},
            width=p.prime_width+2*p.prime_gap,subtract=True)
        self.add_qgeometry('path', {'second_cpw': second_cpw}, width=p.second_width,fillet=p.fillet)
        self.add_qgeometry('path', {'second_cpw_sub': second_cpw_etch},
            width=p.second_width+2*p.second_gap,subtract=True, fillet=p.fillet)

        #Add pins
        prime_pin_list = prime_cpw.coords
        second_pin_list = second_cpw.coords

        self.add_pin('prime_start',
                     points=np.array(prime_pin_list[::-1]),
                     width=p.prime_width, input_as_norm=True)
        self.add_pin('prime_end',
                     points=np.array(prime_pin_list),
                     width=p.prime_width, input_as_norm=True)
        self.add_pin('second_end',
                     points=np.array(second_pin_list[1:]),
                     width=p.second_width, input_as_norm=True)
