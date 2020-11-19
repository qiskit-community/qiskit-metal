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
'''
@date: 2020/08/12
@author: John Blair
'''
#  This a launch structure used on BlueJayV2, used for wire bonding
#  There is no CPW tee attached to this p# TODO create image of structure

# Imports required for drawing

# import numpy as np # (currently not used, may be needed later for component customization)
from qiskit_metal import draw
from qiskit_metal.toolbox_python.attr_dict import Dict
from qiskit_metal.components.base.base import QComponent

# Define class and options for the launch geometry


class LaunchpadWirebondCoupled(QComponent):
    """
    Create a 50 ohm launch with a ground pocket cuttout.  Geometry is hardcoded set of
    polygon points for now. The (0,0) point is the center of the end of the launch.  This
    launch has an inductive coupler section that is currently fixed (can be changed later).

    Inherits 'QComponent' class

    Options:
        Convention: Values (unless noted) are strings with units included,
        (e.g., '30um')

    Pocket and pad:
        Pocket and lauch pad geometry are currently fixed.
        (0,0) point is the midpoint of the end of the pad.
        Pocket is a negative shape that is cut out of the ground plane

        * pos_x / pos_y   - where the center of the pocket should be located on chip
        * orientation     - degree of qubit rotation

    Pins:
        The pin attaches directly to the built in lead length at its midpoint

        * cpw_width      - center trace width of the CPW line where the connector is placed
        * cpw_gap        - gap of the cpw line
        * leadin_length  - length of the cpw line attached to the end of the launch

    Sketch:
        Below is a sketch of the launch
        ::

            ----------------
            |               \
            |      ---------\\
            |      |  --------|    (0,0) pin at midpoint, leadin starts there
            |      ---------//
            |               /
            ----------------

            y
            ^
            |
            |------> x

    .. image::
        LaunchpadWirebondCoupled.png

    """

    #Define structure functions

    default_options = Dict(
        layer='1',
        cpw_width='10um',
        cpw_gap='6um',
        leadin_length='65um',
        pos_x='100um',
        pos_y='100um',
        orientation='0'  #90 for 90 degree turn
    )
    """Default drawing options"""

    def make(self):
        """ This is executed by the user to generate the qgeometry for the component.
        """

        # TODO: rotation tip up and tip down cause the "pin" to be 0.140 off in the x direction.
        #  correct behavior: rotation should keep the pin at the same x.

        p = self.p
        #########################################################

        # Geometry of main launch structure
        launch_pad = draw.Polygon([(0, p.cpw_width / 2),
                                   (-.122, .035 + p.cpw_width / 2),
                                   (-.202, .035 + p.cpw_width / 2),
                                   (-.202, -.045 + p.cpw_width / 2),
                                   (-.122, -.045 + p.cpw_width / 2),
                                   (0, -p.cpw_width / 2),
                                   (.0625, -p.cpw_width / 2),
                                   (.0625, -p.cpw_width / 2 + .0025),
                                   (-.05, -p.cpw_width / 2 + .0025),
                                   (-.05, -p.cpw_width / 2 + .0075),
                                   (.0625, -p.cpw_width / 2 + .0075),
                                   (.0625, -p.cpw_width / 2 + .01),
                                   (0, p.cpw_width / 2)])

        ind_stub = draw.Polygon([(.015, -.0005), (.07, -.0005), (.07, -.005),
                                 (.07 + p.leadin_length, -.005),
                                 (.07 + p.leadin_length, +.005), (.07, +.005),
                                 (.07, +.0005), (.015, +.0005), (.015, -.0005)])

        # Geometry pocket
        pocket = draw.Polygon([
            (0, p.cpw_width / 2 + p.cpw_gap),
            (-.122, .087 + p.cpw_width / 2 + p.cpw_gap),
            (-.25, .087 + p.cpw_width / 2 + p.cpw_gap),
            (-.25, -.109 + p.cpw_width / 2 + p.cpw_gap),
            (-.122, -.109 + p.cpw_width / 2 + p.cpw_gap),
            (0, -p.cpw_width / 2 - p.cpw_gap),
            (.07 + p.leadin_length, -p.cpw_width / 2 - p.cpw_gap),
            (.07 + p.leadin_length, +p.cpw_width / 2 + p.cpw_gap),
            (0, p.cpw_width / 2 + p.cpw_gap)
        ])

        # These variables are used to graphically locate the pin locations
        main_pin_line = draw.LineString([
            (p.leadin_length + .07, p.cpw_width / 2),
            (p.leadin_length + .07, -p.cpw_width / 2)
        ])

        # Create polygon object list
        polys1 = [main_pin_line, launch_pad, ind_stub, pocket]

        # Rotates and translates all the objects as requested. Uses package functions
        # in 'draw_utility' for easy rotation/translation
        polys1 = draw.rotate(polys1,
                             p.orientation,
                             origin=(p.leadin_length + .07, 0))
        polys1 = draw.translate(polys1, xoff=p.pos_x, yoff=p.pos_y)
        [main_pin_line, launch_pad, ind_stub, pocket] = polys1

        # Adds the object to the qgeometry table
        self.add_qgeometry('poly',
                           dict(launch_pad=launch_pad, ind_stub=ind_stub),
                           layer=p.layer)

        # Subtracts out ground plane on the layer its on
        self.add_qgeometry('poly',
                           dict(pocket=pocket),
                           subtract=True,
                           layer=p.layer)

        # Generates the pins
        self.add_pin('a', main_pin_line.coords, p.cpw_width)
