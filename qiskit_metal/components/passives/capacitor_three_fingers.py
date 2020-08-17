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
@author: John Blair, Marco Facchini
'''
#  This a 3 finger planar metal capacitor design used on the chip Hummingbird V2
#  There is no CPW tee attached to this p# TODO create image of structure


# Imports required for drawing

import numpy as np
from qiskit_metal import draw
from qiskit_metal.toolbox_python.attr_dict import Dict
from qiskit_metal.components.base.base import QComponent

# Define class and options for the capacitor geometry


class Capacitor3Fingers(QComponent):
    """    Inherits QComponent class

    Description:
    ----------------------------------------------------------------------------
    Create a three finger planar capacitor with a ground pocket cuttout.  The width of
    the fingers is determined by the CPW width.

    Connectors can be added using the `options_connectors`
    dictionary. Each connectors has a name and a list of default
    properties.

    Options:
    ----------------------------------------------------------------------------
    Convention: Values (unless noted) are strings with units included,
                (e.g., '30um')

    Capacitor Metal Geometry and Ground Cuttout Pocket:
    ----------------------------------------------------------------------------
    cpw_width      - center trace width of the CPW lead line and cap fingers
    finger length  - length of each finger
    pocket_buffer_width_x - sets size of pocket in +-x direction, added to cap size
    pocket_buffer_width_y - sets size of pocket in +-y direction, added to cap size
                            this also determines the lead in line lengths   
                            pocket is a negative shape that is cut out of the ground plane
    pos_x / pos_y   - where the center of the pocket should be located on chip
    orientation     - degree of qubit rotation

    Connectors:
    ----------------------------------------------------------------------------
    There are two connectors on the capacitor at either end
    The connector attaches directly to the built in lead length and only needs a width defined
    cpw_width      - center trace width of the CPW line where the connector is placed
    
    

    Sketch:  TODO
    ----------------------------------------------------------------------------

    """

   #  TODO _img = 'CapThreeFinger.png'



   #Define structure functions

    default_options = Dict(
        layer='1',
        trace_width='10um',
        trace_gap='6um',
        finger_length='65um',
        pocket_buffer_width_x='10um',
        pocket_buffer_width_y='30um',
        position_x='100um',
        position_y='100um',
        orientation='90', #90 for 90 degree turn
    )

    def make(self):
        """ This is executed by the user to generate the qgeometry for the component.
        """
        p = self.p

        # Shapely polygons for the main cap structure
        pad     = draw.rectangle(p.trace_width * 5, p.trace_width)
        pad_top = draw.translate(pad, 0, +(p.trace_width * 2 + p.finger_length) / 2)
        pad_bot = draw.translate(pad, 0, -(p.trace_width * 2 + p.finger_length) / 2)
        finger  = draw.rectangle(p.trace_width, p.finger_length)
        cent_finger = draw.translate(finger, 0, +p.trace_width / 2)
        left_finger = draw.translate(finger, -p.trace_width * 2, -p.trace_width / 2)
        right_finger = draw.translate(finger, +p.trace_width * 2, -p.trace_width / 2)

        # Shapely polygons for the built in leads in the pocket (length=pocket_buffer_width_y)
        cpw_temp_1 = draw.rectangle(p.trace_width, p.pocket_buffer_width_y)
        cpw_top = draw.translate(cpw_temp_1, 0, +(p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2) / 2 - p.pocket_buffer_width_y / 2)
        cpw_bot = draw.translate(cpw_temp_1, 0, -(p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2) / 2 + p.pocket_buffer_width_y / 2)

        # These variables are used to graphically locate the pin locations
        top_pin_line = draw.LineString([(+p.trace_width / 2, (p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2) / 2),
                                        (-p.trace_width / 2, (p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2) / 2)])
        bot_pin_line = draw.LineString([(-p.trace_width / 2, -(p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2) / 2),
                                        (+p.trace_width / 2, -(p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2) / 2)])

        # make the shapely polygons for pocket ground plane cuttout
        pocket = draw.rectangle(p.trace_width * 5 + p.pocket_buffer_width_x * 2, p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2)

        # create polygon object list 
        polys1 = [top_pin_line, bot_pin_line, pad_top, pad_bot, cent_finger, left_finger, right_finger, pocket, cpw_top, cpw_bot]

        #rotates and translates all the objects as requested. Uses package functions in 'draw_utility' for easy
        # rotation/translation
        polys1 = draw.rotate(polys1, p.orientation, origin=(0, 0))
        polys1 = draw.translate(polys1, xoff=p.position_x, yoff=p.position_y)
        [top_pin_line, bot_pin_line, pad_top, pad_bot, cent_finger, left_finger, right_finger, pocket, cpw_top, cpw_bot] = polys1  #why backwards?

        # Adds the object to the qgeometry table (need help with this section this is an old format)
        self.add_qgeometry('poly', dict(pad_top=pad_top, pad_bot=pad_bot, cent_finger=cent_finger,
            left_finger=left_finger, right_finger=right_finger, cpw_top=cpw_top, cpw_bot=cpw_bot), layer=p.layer)
        # subtracts out ground plane on the layer its on
        self.add_qgeometry('poly', dict(pocket=pocket), subtract=True, layer=p.layer)
        # add pin extensions
        self.add_qgeometry('path', {'plus': top_pin_line, 'minus': bot_pin_line}, width=p.trace_width, layer=p.layer)

        # Generates its own pins . Not sure normal vector is correct.
        pts_top_pin = np.array(top_pin_line.coords)
        pts_bot_pin = np.array(bot_pin_line.coords)
        self.add_pin('plus', pts_top_pin[::-1], p.trace_width)
        self.add_pin('minus', pts_bot_pin[::-1], p.trace_width)
