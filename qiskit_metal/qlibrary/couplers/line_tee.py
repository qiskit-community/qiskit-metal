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
""""""

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent
import numpy as np


class LineTee(QComponent):
    """Generates a three pin (+) structure comprised of a primary two pin CPW
    transmission line, and a secondary one pin neighboring CPW transmission
    line that is capacitively coupled to the primary. Such a structure can be
    used, as an example, for generating CPW resonator hangars off of a
    transmission line. (0,0) represents the center position of the component.

    Inherits QComponent class.

    ::

                  (0,0)
        +--------------------------+
                    |
                    |
                    |
                    |
                    |
                    +

    .. image::
        LineTee.png

    .. meta::
        Line Tee

    Options:
        * prime_width: '10um' -- The width of the trace of the two pin CPW transmission line
        * prime_gap: '6um' -- The dielectric gap of the two pin CPW transmission line
        * second_width: '10um' -- The width of the trace of the one pin CPW transmission line
        * second_gap: '6um' -- The dielectric gap of the one pin CPW transmission line (also for the capacitor)
        * t_length: '50um' -- The length for the t branches
    """
    component_metadata = Dict(short_name='cpw', _qgeometry_table_path='True')
    """Component metadata"""

    #Currently setting the primary CPW length based on the coupling_length
    #May want it to be it's own value that the user can control?
    default_options = Dict(prime_width='10um',
                           prime_gap='6um',
                           second_width='10um',
                           second_gap='6um',
                           t_length='50um')
    """Default connector options"""

    TOOLTIP = """Generates a three pin (+) structure comprised of a primary two pin CPW
    transmission line, and a secondary one pin neighboring CPW transmission
    line that is capacitively coupled to the primary."""

    def make(self):
        """Build the component."""
        p = self.p
        prime_cpw_length = p.t_length * 2

        #Primary CPW
        prime_cpw = draw.LineString([[-prime_cpw_length / 2, 0],
                                     [prime_cpw_length / 2, 0]])

        #Secondary CPW
        second_cpw = draw.LineString([[0, -p.prime_width / 2], [0,
                                                                -p.t_length]])

        #Rotate and Translate
        c_items = [prime_cpw, second_cpw]
        c_items = draw.rotate(c_items, p.orientation, origin=(0, 0))
        c_items = draw.translate(c_items, p.pos_x, p.pos_y)
        [prime_cpw, second_cpw] = c_items

        #Add to qgeometry tables
        self.add_qgeometry('path', {'prime_cpw': prime_cpw},
                           width=p.prime_width,
                           layer=p.layer)
        self.add_qgeometry('path', {'prime_cpw_sub': prime_cpw},
                           width=p.prime_width + 2 * p.prime_gap,
                           subtract=True,
                           layer=p.layer)
        self.add_qgeometry('path', {'second_cpw': second_cpw},
                           width=p.second_width,
                           layer=p.layer)
        self.add_qgeometry('path', {'second_cpw_sub': second_cpw},
                           width=p.second_width + 2 * p.second_gap,
                           subtract=True,
                           layer=p.layer)

        #Add pins
        prime_pin_list = prime_cpw.coords
        second_pin_list = second_cpw.coords

        self.add_pin('prime_start',
                     points=np.array(prime_pin_list[::-1]),
                     width=p.prime_width,
                     input_as_norm=True)
        self.add_pin('prime_end',
                     points=np.array(prime_pin_list),
                     width=p.prime_width,
                     input_as_norm=True)
        self.add_pin('second_end',
                     points=np.array(second_pin_list),
                     width=p.second_width,
                     input_as_norm=True)
