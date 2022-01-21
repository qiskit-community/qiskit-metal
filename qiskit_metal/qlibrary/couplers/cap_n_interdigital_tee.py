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


class CapNInterdigitalTee(QComponent):
    """Generates a three pin (+) structure comprised of a primary two pin CPW
    transmission line, and a secondary one pin neighboring CPW transmission
    line that is capacitively coupled to the primary. Such a structure can be
    used, as an example, for generating CPW resonator hangars off of a
    transmission line. (0,0) represents the center position of the component.
    Setting finger length to 0 gives a simple gap capacitor.

    Inherits QComponent class.

    ::

                  (0,0)
        +--------------------------+
                    |
               --|-----|--
              |  |  |  |  |
              |-----|-----|
                    |
                    |
                    |
                    |
                    +

    .. image::
        CapNInterdigitalTee.png

    .. meta::
        Cap N Interdigital Tee

    Options:
        * prime_width: '10um' -- The width of the trace of the two pin CPW transmission line
        * prime_gap: '6um' -- The dielectric gap of the two pin CPW transmission line
        * second_width: '10um' -- The width of the trace of the one pin CPW transmission line
        * second_gap: '6um' -- The dielectric gap of the one pin CPW transmission line (also for the capacitor)
        * cap_gap: '6um' -- The width of dielectric for the capacitive coupling (default same as second_gap)
        * cap_width: '10um' -- The width of the finger capacitor (default same as second)
        * finger_length: '20um' -- The depth of the charge islands of the capacitor
        * finger_count: '5' -- Number of fingers in the capacitor
        * cap_distance: '50um' -- Distance of capacitor from center transmission line
    """
    component_metadata = Dict(short_name='cpw',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_path='True')
    """Component metadata"""

    #Currently setting the primary CPW length based on the coupling_length
    #May want it to be it's own value that the user can control?
    default_options = Dict(prime_width='10um',
                           prime_gap='6um',
                           second_width='10um',
                           second_gap='6um',
                           cap_gap='6um',
                           cap_width='10um',
                           finger_length='20um',
                           finger_count='5',
                           cap_distance='50um')
    """Default connector options"""

    TOOLTIP = """Generates a three pin (+) structure comprised of a primary two pin CPW
    transmission line, and a secondary one pin neighboring CPW transmission
    line that is capacitively coupled to the primary."""

    def make(self):
        """Build the component."""
        p = self.p
        N = int(p.finger_count)
        prime_cpw_length = p.cap_width * 2 * N

        #Primary CPW
        prime_cpw = draw.LineString([[-prime_cpw_length / 2, 0],
                                     [prime_cpw_length / 2, 0]])

        #Finger Capacitor
        cap_box = draw.rectangle(N * p.cap_width + (N - 1) * p.cap_gap,
                                 p.cap_gap + 2 * p.cap_width + p.finger_length,
                                 0, 0)
        make_cut_list = []
        make_cut_list.append([0, (p.finger_length) / 2])
        make_cut_list.append([(p.cap_width) + (p.cap_gap / 2),
                              (p.finger_length) / 2])
        flip = -1

        for i in range(1, N):
            make_cut_list.append([
                i * (p.cap_width) + (2 * i - 1) * (p.cap_gap / 2),
                flip * (p.finger_length) / 2
            ])
            make_cut_list.append([
                (i + 1) * (p.cap_width) + (2 * i + 1) * (p.cap_gap / 2),
                flip * (p.finger_length) / 2
            ])
            flip = flip * -1

        cap_cut = draw.LineString(make_cut_list).buffer(p.cap_gap / 2,
                                                        cap_style=2,
                                                        join_style=2)
        cap_cut = draw.translate(cap_cut,
                                 -(N * p.cap_width + (N - 1) * p.cap_gap) / 2,
                                 0)

        cap_body = draw.subtract(cap_box, cap_cut)
        cap_body = draw.translate(
            cap_body, 0, -p.cap_distance -
            (p.cap_gap + 2 * p.cap_width + p.finger_length) / 2)

        cap_etch = draw.rectangle(
            N * p.cap_width + (N - 1) * p.cap_gap + 2 * p.second_gap,
            p.cap_gap + 2 * p.cap_width + p.finger_length + 2 * p.second_gap, 0,
            -p.cap_distance -
            (p.cap_gap + 2 * p.cap_width + p.finger_length) / 2)

        #Secondary CPW
        second_cpw_top = draw.LineString([[0, -p.prime_width / 2],
                                          [0, -p.cap_distance]])

        second_cpw_bottom = draw.LineString(
            [[
                0, -p.cap_distance -
                (p.cap_gap + 2 * p.cap_width + p.finger_length)
            ],
             [
                 0, -2 * p.cap_distance -
                 (p.cap_gap + 2 * p.cap_width + p.finger_length)
             ]])

        #Rotate and Translate
        c_items = [
            prime_cpw, second_cpw_top, second_cpw_bottom, cap_body, cap_etch
        ]
        c_items = draw.rotate(c_items, p.orientation, origin=(0, 0))
        c_items = draw.translate(c_items, p.pos_x, p.pos_y)
        [prime_cpw, second_cpw_top, second_cpw_bottom, cap_body,
         cap_etch] = c_items

        #Add to qgeometry tables
        self.add_qgeometry('path', {'prime_cpw': prime_cpw},
                           width=p.prime_width,
                           layer=p.layer)
        self.add_qgeometry('path', {'prime_cpw_sub': prime_cpw},
                           width=p.prime_width + 2 * p.prime_gap,
                           subtract=True,
                           layer=p.layer)
        self.add_qgeometry('path', {
            'second_cpw_top': second_cpw_top,
            'second_cpw_bottom': second_cpw_bottom
        },
                           width=p.second_width,
                           layer=p.layer)
        self.add_qgeometry('path', {
            'second_cpw_top_sub': second_cpw_top,
            'second_cpw_bottom_sub': second_cpw_bottom
        },
                           width=p.second_width + 2 * p.second_gap,
                           subtract=True,
                           layer=p.layer)

        self.add_qgeometry('poly', {'cap_body': cap_body}, layer=p.layer)
        self.add_qgeometry('poly', {'cap_etch': cap_etch},
                           layer=p.layer,
                           subtract=True)

        #Add pins
        prime_pin_list = prime_cpw.coords
        second_pin_list = second_cpw_bottom.coords

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
