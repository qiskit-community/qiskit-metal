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

from qiskit_metal import draw
from qiskit_metal.toolbox_python.attr_dict import Dict
from qiskit_metal.qlibrary.core import QComponent


class Cap3Interdigital(QComponent):
    """Create a three finger planar capacitor with a ground pocket cuttout.
    The width of the fingers is determined by the trace width.

    Inherits QComponent class.

    Capacitor Metal Geometry and Ground Cutout Pocket:
        * finger length  - length of each finger
        * pocket_buffer_width_x - sets size of pocket in +-x direction, added to cap size
        * pocket_buffer_width_y - sets size of pocket in +-y direction, added to cap size
          this also determines the lead in line lengths
          pocket is a negative shape that is cut out of the ground plane

    Pins:
        There are two pins on the capacitor at either end
        The pins attach directly to the built in lead length and only needs a width defined
        * trace_width - center trace width of the trace lead line and cap fingers

    Sketch:
        Below is a sketch of the capacitor
        ::

                 |
            -----------
                 |
            |    |    |
            |    |    |
            |    |    |
            |    |    |
            |         |
            -----------
                 |

    .. image::
        Cap3Interdigital.png

    .. meta::
        Cap 3 Interdigital

    Default Options:
        * trace_width: '10um'
        * finger_length: '65um'
        * pocket_buffer_width_x: '10um'
        * pocket_buffer_width_y: '30um'
    """

    #  Define structure functions

    default_options = Dict(trace_width='10um',
                           finger_length='65um',
                           pocket_buffer_width_x='10um',
                           pocket_buffer_width_y='30um')
    """Default drawing options"""

    TOOLTIP = """Create a three finger planar capacitor with a ground pocket cuttout."""

    def make(self):
        """This is executed by the user to generate the qgeometry for the
        component."""
        p = self.p
        #########################################################

        # Make the shapely polygons for the main cap structure
        pad = draw.rectangle(p.trace_width * 5, p.trace_width)
        pad_top = draw.translate(pad, 0,
                                 +(p.trace_width * 2 + p.finger_length) / 2)
        pad_bot = draw.translate(pad, 0,
                                 -(p.trace_width * 2 + p.finger_length) / 2)
        finger = draw.rectangle(p.trace_width, p.finger_length)
        cent_finger = draw.translate(finger, 0, +(p.trace_width) / 2)
        left_finger = draw.translate(finger, -(p.trace_width * 2),
                                     -(p.trace_width) / 2)
        right_finger = draw.translate(finger, +(p.trace_width * 2),
                                      -(p.trace_width) / 2)

        # Make the shapely polygons for the leads in the pocket (length=pocket_buffer_width_y)
        trace_temp_1 = draw.rectangle(p.trace_width, p.pocket_buffer_width_y)
        trace_top = draw.translate(
            trace_temp_1, 0,
            +(p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2)
            / 2 - p.pocket_buffer_width_y / 2)
        trace_bot = draw.translate(
            trace_temp_1, 0,
            -(p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2)
            / 2 + p.pocket_buffer_width_y / 2)

        # Make the shapely polygons for pocket ground plane cuttout
        pocket = draw.rectangle(
            p.trace_width * 5 + p.pocket_buffer_width_x * 2,
            p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2)

        # These variables are used to graphically locate the pin locations
        top_pin_line = draw.LineString([
            (-p.trace_width / 2,
             (p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2)
             / 2),
            (+p.trace_width / 2,
             (p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2)
             / 2)
        ])
        bot_pin_line = draw.LineString([(
            -p.trace_width / 2,
            -(p.finger_length + p.trace_width * 3 + p.pocket_buffer_width_y * 2)
            / 2),
                                        (+p.trace_width / 2,
                                         -(p.finger_length + p.trace_width * 3 +
                                           p.pocket_buffer_width_y * 2) / 2)])

        # Create polygon object list
        polys1 = [
            top_pin_line, bot_pin_line, pad_top, pad_bot, cent_finger,
            left_finger, right_finger, pocket, trace_top, trace_bot
        ]

        # Rotates and translates all the objects as requested. Uses package functions
        # in 'draw_utility' for easy rotation/translation
        polys1 = draw.rotate(polys1, p.orientation, origin=(0, 0))
        polys1 = draw.translate(polys1, xoff=p.pos_x, yoff=p.pos_y)
        [
            top_pin_line, bot_pin_line, pad_top, pad_bot, cent_finger,
            left_finger, right_finger, pocket, trace_top, trace_bot
        ] = polys1

        # Adds the object to the qgeometry table
        self.add_qgeometry('poly',
                           dict(pad_top=pad_top,
                                pad_bot=pad_bot,
                                cent_finger=cent_finger,
                                left_finger=left_finger,
                                right_finger=right_finger,
                                trace_top=trace_top,
                                trace_bot=trace_bot),
                           layer=p.layer)

        #subtracts out ground plane on the layer its on
        self.add_qgeometry('poly',
                           dict(pocket=pocket),
                           subtract=True,
                           layer=p.layer)

        # Generates its own pins
        self.add_pin('a', top_pin_line.coords, p.trace_width)
        self.add_pin('b', bot_pin_line.coords[::-1], p.trace_width)
