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

#  This a launch structure used on BlueJayV2, used for wire bonding
#  There is no CPW tee attached to this p#

# Imports required for drawing

# import numpy as np # (currently not used, may be needed later for component customization)
from qiskit_metal import draw
from qiskit_metal.toolbox_python.attr_dict import Dict
from qiskit_metal.qlibrary.core import QComponent

# Define class and options for the launch geometry


class LaunchpadWirebondFreeShape(QComponent):
    """Launch pad to feed/read signals to/from the chip.

    Inherits 'QComponent' class.

    Creates a 50 ohm launch pad with a ground pocket cutout.
    Limited but expandable parameters to control the launchpad polygons.
    The (0,0) point is the center of the necking of the launch tip.
    The pin attaches directly to the built in lead length at its midpoint

    Pocket and pad:
        Pocket and launch pad geometries are currently fixed.
        (0,0) point is the midpoint of the necking of the launch tip.
        Pocket is a negative shape that is cut out of the ground plane

    Values (unless noted) are strings with units included, (e.g., '30um')

    Sketch:
        Below is a sketch of the launch
        ::

            -----------
            |          \
            |      ---------\\
            |      |    0    |    (0,0) pin at midpoint of necking, before the lead
            |      ---------//
            |          /
            -----------

            y
            ^
            |
            |------> x

    .. image::
        LaunchpadWirebond.png

    Default Options:
        * layer: '1'
        * trace_width: Width of the trace of the launch pad
        * trace_height: Height of the trace of the launch pad
        * trace_gap: Gap of the launch pad (the gray area)
        * lead_length: -- 'cpw_width' -- Length of the cpw line attached to the end of the launch pad, should be same as cpw_width
        * neck_height: Height of the necking part
        * cpw_gap: -- 'cpw_gap' -- gap of the transmission line
        * pos_x: '0um' -- Where the center of the pocket should be located on chip
        * pos_y: '0um' -- Where the center of the pocket should be located on chip
        * orientation: '0' -- 90 for 90 degree turn
    """

    default_options = Dict(
        layer='1',
        trace_width ='300um',
        trace_height='300um',
        trace_gap   ='300um',
        lead_length ='cpw_width',
        neck_height ='200um',
        cpw_gap     ='cpw_gap',
        pos_x='0um',
        pos_y='0um',
        orientation='0'  #90 for 90 degree turn
    )
    """Default options"""

    TOOLTIP = """Launch pad to feed/read signals to/from the chip."""

    def make(self):
        """This is executed by the user to generate the qgeometry for the
        component."""

        p = self.p

        trace_width  = p.trace_width
        trace_height = p.trace_height
        trace_gap    = p.trace_gap
        lead_length  = p.lead_length
        neck_height  = p.neck_height 
        cpw_gap = p.cpw_gap
        
        trace_gap = p.trace_gap
                #########################################################

        # Geometry of main launch structure
        # The shape is a polygon and we prepare this point as orientation is 0 degree
        launch_pad = draw.Polygon([(0, lead_length/2.),
                                   (-neck_height, trace_width/2.),
                                   (-(trace_height+neck_height), trace_width/2.),
                                   (-(trace_height+neck_height), -trace_width/2.),
                                   (-neck_height, -trace_width/2.),
                                   (0, -lead_length/2.)
                                   ]
                                   )

        # Geometry pocket (gap)
        # Same way applied for pocket
        pocket = draw.Polygon([(0, lead_length/2.+cpw_gap),
                               (-neck_height, (trace_width+trace_gap)/2.),
                               (-(trace_height+neck_height+trace_gap/2), (trace_width+trace_gap)/2.),
                               (-(trace_height+neck_height+trace_gap/2), -(trace_width+trace_gap)/2.),
                               (-neck_height, -(trace_width+trace_gap)/2.),
                               (0, -(lead_length/2.+cpw_gap))
                              ]
                            )

        # These variables are used to graphically locate the pin locations
        # Since there is no coupled pad or anything else pin should be on the launch pad. Because transmission line will start ecxatly from the beginnig point of pin
        main_pin_line = draw.LineString([(0, lead_length/2.),
                                         (0, -lead_length/2.)])

        # Create polygon object list
        polys1 = [main_pin_line, launch_pad, pocket]

        # Rotates and translates all the objects as requested. Uses package functions in
        # 'draw_utility' for easy rotation/translation
        polys1 = draw.rotate(polys1, p.orientation, origin=(0, 0))
        polys1 = draw.translate(polys1, xoff=p.pos_x, yoff=p.pos_y)
        [main_pin_line, launch_pad, pocket] = polys1

        # Adds the object to the qgeometry table
        self.add_qgeometry('poly', dict(launch_pad=launch_pad), layer=p.layer)

        # Subtracts out ground plane on the layer its on
        self.add_qgeometry('poly',
                           dict(pocket=pocket),
                           subtract=True,
                           layer=p.layer)

        # Generates the pins
        self.add_pin('tie', main_pin_line.coords, trace_width)
