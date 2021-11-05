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


class CapNInterdigital(QComponent):
    """Generates a two pin (+) structure comprised of a north CPW transmission
    line, and a south transmission line, coupled together via a finger
    capacitor. Such a structure can be used, as an example, for generating CPW
    resonators. (0,0) represents the center position of the component. Setting
    finger length to 0 gives a simple gap capacitor. The width of the gap
    capacitor is found via.

    (cap_width * finger_count +  * cap_gap * (finger_count-1)).

    Inherits QComponent class.

    ::

                  (0,0)     N
                    +       ^
                    |       |
                    |
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
        CapNInterdigital.png
    
    .. meta::
        Cap N Interdigital
    
    Options:
        * north_width: '10um' -- The width of the 'north' portion of the CPW transmission line
        * north_gap: '6um' -- The dielectric gap of the 'north' portion of the CPW transmission line
        * south_width: '10um' -- The width of the 'south' portion of the CPW transmission line
        * south_gap: '6um' -- The dielectric gap of the 'south' portion of the CPW transmission line
            (also for the capacitor gap to ground)
        * cap_width: '10um' -- The width of the finger capacitor metal (and islands)
        * cap_gap: '6um' -- The width of dielectric for the capacitive coupling/fingers
        * cap_gap_ground: '6um' -- Width of the dielectric between the capacitor and ground
        * finger_length: '20um' -- The depth of the finger islands of the capacitor
        * finger_count: '5' -- Number of fingers in the capacitor
        * cap_distance: '50um' -- Distance of the north point of the capacitor from the north pin
    """
    component_metadata = Dict(short_name='cpw',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_path='True')
    """Component metadata"""

    #Currently setting the primary CPW length based on the coupling_length
    #May want it to be it's own value that the user can control?
    default_options = Dict(north_width='10um',
                           north_gap='6um',
                           south_width='10um',
                           south_gap='6um',
                           cap_width='10um',
                           cap_gap='6um',
                           cap_gap_ground='6um',
                           finger_length='20um',
                           finger_count='5',
                           cap_distance='50um')
    """Default connector options"""

    TOOLTIP = """Generates a two pin (+) structure
     comprised of a north CPW transmission line, 
     and a south transmission line, coupled 
     together via a finger capacitor."""

    def make(self):
        """Build the component."""
        p = self.p
        N = int(p.finger_count)

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
            N * p.cap_width + (N - 1) * p.cap_gap + 2 * p.cap_gap_ground,
            p.cap_gap + 2 * p.cap_width + p.finger_length +
            2 * p.cap_gap_ground, 0, -p.cap_distance -
            (p.cap_gap + 2 * p.cap_width + p.finger_length) / 2)

        #CPW
        north_cpw = draw.LineString([[0, 0], [0, -p.cap_distance]])

        south_cpw = draw.LineString(
            [[
                0, -p.cap_distance -
                (p.cap_gap + 2 * p.cap_width + p.finger_length)
            ],
             [
                 0, -2 * p.cap_distance -
                 (p.cap_gap + 2 * p.cap_width + p.finger_length)
             ]])

        #Rotate and Translate
        c_items = [north_cpw, south_cpw, cap_body, cap_etch]
        c_items = draw.rotate(c_items, p.orientation, origin=(0, 0))
        c_items = draw.translate(c_items, p.pos_x, p.pos_y)
        [north_cpw, south_cpw, cap_body, cap_etch] = c_items

        #Add to qgeometry tables
        self.add_qgeometry('path', {'north_cpw': north_cpw},
                           width=p.north_width,
                           layer=p.layer)
        self.add_qgeometry('path', {'north_cpw_sub': north_cpw},
                           width=p.north_width + 2 * p.north_gap,
                           layer=p.layer,
                           subtract=True)

        self.add_qgeometry('path', {'south_cpw': south_cpw},
                           width=p.south_width,
                           layer=p.layer)
        self.add_qgeometry('path', {'south_cpw_sub': south_cpw},
                           width=p.south_width + 2 * p.south_gap,
                           layer=p.layer,
                           subtract=True)

        self.add_qgeometry('poly', {'cap_body': cap_body}, layer=p.layer)
        self.add_qgeometry('poly', {'cap_etch': cap_etch},
                           layer=p.layer,
                           subtract=True)

        #Add pins
        north_pin_list = north_cpw.coords
        south_pin_list = south_cpw.coords

        self.add_pin('north_end',
                     points=np.array(north_pin_list[::-1]),
                     width=p.north_width,
                     input_as_norm=True)
        self.add_pin('south_end',
                     points=np.array(south_pin_list),
                     width=p.south_width,
                     input_as_norm=True)
