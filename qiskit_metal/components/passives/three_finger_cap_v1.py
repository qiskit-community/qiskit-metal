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
@date: 2020/07/25
@author: John Blair
'''
#  This a 3 finger planar metal capacitor design used on the chip Hummingbird V2
#  There is no CPW tee attached to this p# TODO create image of structure


# Imports required for drawing

# import numpy as np # (currently not used, may be needed later for component customization)
from qiskit_metal import draw
from qiskit_metal.toolbox_python.attr_dict import Dict
from qiskit_metal.components.base.base import QComponent

# Define class and options for the capacitor geometry

class ThreeFingerCapV1(QComponent):

    """

    Inherits QComponent class

    Description:
        Create a three finger planar capacitor with a ground pocket cuttout.  The width of
        the fingers is determined by the CPW width.

    Options:
        Convention: Values (unless noted) are strings with units included,
        (e.g., '30um')

    Capacitor Metal Geometry and Ground Cuttout Pocket:
        *finger length  - length of each finger
        *pocket_buffer_width_x - sets size of pocket in +-x direction, added to cap size
        *pocket_buffer_width_y - sets size of pocket in +-y direction, added to cap size
                                 this also determines the lead in line lengths
                                 pocket is a negative shape that is cut out of the ground plane
        *pos_x / pos_y   - where the center of the pocket should be located on chip
        *orientation     - degree of qubit rotation

    Pins:
        There are two pins on the capacitor at either end
        The pins attach directly to the built in lead length and only needs a width defined
        *cpw_width - center trace width of the CPW lead line and cap fingers
        *cpw_gap        - gap of the cpw line

    Sketch:
        Below is a sketch of the capacitor
        ::
            TODO

            y
            ^
            |
            |------> x

    .. image::
        ThreeFingerCap_V1.png

    """

   #  Define structure functions

    default_options = Dict(
        layer='1',
        cpw_width='10um',
        cpw_gap='6um',
        finger_length='65um',
        pocket_buffer_width_x='10um',
        pocket_buffer_width_y='30um',
        pos_x='100um',
        pos_y='100um',
        orientation='0')

    """Default drawing options"""

    def make(self):
        """ This is executed by the user to generate the qgeometry for the component.
        """
        p = self.p
        #########################################################

        # Make the shapely polygons for the main cap structure
        pad = draw.rectangle(p.cpw_width*5, p.cpw_width)
        pad_top = draw.translate(pad, 0, +(p.cpw_width*2+p.finger_length)/2)
        pad_bot = draw.translate(pad, 0, -(p.cpw_width*2+p.finger_length)/2)
        finger = draw.rectangle(p.cpw_width, p.finger_length)
        cent_finger = draw.translate(finger, 0, +(p.cpw_width)/2)
        left_finger = draw.translate(finger, -(p.cpw_width*2), -(p.cpw_width)/2)
        right_finger = draw.translate(finger, +(p.cpw_width*2), -(p.cpw_width)/2)

        # Make the shapely polygons for the leads in the pocket (length=pocket_buffer_width_y)
        cpw_temp_1 = draw.rectangle(p.cpw_width, p.pocket_buffer_width_y)
        cpw_top = draw.translate(cpw_temp_1, 0,
                                 +(p.finger_length+p.cpw_width*3+p.pocket_buffer_width_y*2)
                                 /2-p.pocket_buffer_width_y/2)
        cpw_bot = draw.translate(cpw_temp_1, 0,
                                 -(p.finger_length+p.cpw_width*3+p.pocket_buffer_width_y*2)
                                 /2+p.pocket_buffer_width_y/2)

        # Make the shapely polygons for pocket ground plane cuttout
        pocket = draw.rectangle(p.cpw_width*5+p.pocket_buffer_width_x*2,
                                p.finger_length+p.cpw_width*3+p.pocket_buffer_width_y*2)

        # These variables are used to graphically locate the pin locations
        top_pin_line = draw.LineString([(-p.cpw_width/2, (p.finger_length+p.cpw_width*3
                                                          +p.pocket_buffer_width_y*2)/2),
                                        (+p.cpw_width/2, (p.finger_length+p.cpw_width*3
                                                          +p.pocket_buffer_width_y*2)/2)])
        bot_pin_line = draw.LineString([(-p.cpw_width/2, -(p.finger_length+p.cpw_width*3
                                                           +p.pocket_buffer_width_y*2)/2),
                                        (+p.cpw_width/2, -(p.finger_length+p.cpw_width*3
                                                           +p.pocket_buffer_width_y*2)/2)])

        # Create polygon object list
        polys1 = [top_pin_line, bot_pin_line, pad_top, pad_bot, cent_finger, left_finger,
                  right_finger, pocket, cpw_top, cpw_bot]

        # Rotates and translates all the objects as requested. Uses package functions
        # in 'draw_utility' for easyrotation/translation
        polys1 = draw.rotate(polys1, p.orientation, origin=(0, 0))
        polys1 = draw.translate(polys1, xoff=p.pos_x, yoff=p.pos_y)
        [top_pin_line, bot_pin_line, pad_top, pad_bot, cent_finger, left_finger,
         right_finger, pocket, cpw_top, cpw_bot] = polys1

        # Adds the object to the qgeometry table
        self.add_qgeometry('poly', dict(pad_top=pad_top, pad_bot=pad_bot, cent_finger=cent_finger,
                                        left_finger=left_finger, right_finger=right_finger,
                                        cpw_top=cpw_top, cpw_bot=cpw_bot), layer=p.layer)

        #subtracts out ground plane on the layer its on
        self.add_qgeometry('poly', dict(pocket=pocket), subtract=True, layer=p.layer)

        # Generates its own pins
        self.add_pin('a', top_pin_line.coords, p.cpw_width)
        self.add_pin('b', bot_pin_line.coords[::-1], p.cpw_width)
        