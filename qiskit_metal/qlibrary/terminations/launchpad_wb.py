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


class LaunchpadWirebond(QComponent):
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
        * trace_width: 'cpw_width' -- Center trace width of the terminating transmission line
        * trace_gap: 'cpw_gap' -- Gap of the transmission line
        * lead_length: '25um' -- Length of the cpw line attached to the end of the launch pad
        * pos_x: '0um' -- Where the center of the pocket should be located on chip
        * pos_y: '0um' -- Where the center of the pocket should be located on chip
        * orientation: '0' -- 90 for 90 degree turn
    """

    default_options = Dict(
        layer='1',
        trace_width='cpw_width',
        trace_gap='cpw_gap',
        lead_length='25um',
        pos_x='0um',
        pos_y='0um',
        orientation='0'  #90 for 90 degree turn
    )
    """Default options"""

    def make(self):
        """This is executed by the user to generate the qgeometry for the
        component."""

        p = self.p
        trace_width = p.trace_width
        trace_width_half = trace_width / 2
        lead_length = p.lead_length
        trace_gap = p.trace_gap
        #########################################################

        # Geometry of main launch structure
        launch_pad = draw.Polygon([(0, trace_width_half),
                                   (-.122, trace_width_half + .035),
                                   (-.202, trace_width_half + .035),
                                   (-.202, -trace_width_half - .035),
                                   (-.122, -trace_width_half - .035),
                                   (0, -trace_width_half),
                                   (lead_length, -trace_width_half),
                                   (lead_length, +trace_width_half),
                                   (0, trace_width_half)])

        # Geometry pocket (gap)
        pocket = draw.Polygon([(0, trace_width_half + trace_gap),
                               (-.122, trace_width_half + trace_gap + .087),
                               (-.25, trace_width_half + trace_gap + .087),
                               (-.25, -trace_width_half - trace_gap - .087),
                               (-.122, -trace_width_half - trace_gap - .087),
                               (0, -trace_width_half - trace_gap),
                               (lead_length, -trace_width_half - trace_gap),
                               (lead_length, +trace_width_half + trace_gap),
                               (0, trace_width_half + trace_gap)])

        # These variables are used to graphically locate the pin locations
        main_pin_line = draw.LineString([(lead_length, trace_width_half),
                                         (lead_length, -trace_width_half)])

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
