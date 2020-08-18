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
@date: 2020/08/12
@author: John Blair
'''
#  This a launch structure used on BlueJayV2, used for wire bonding
#  There is no CPW tee attached to this p# TODO create image of structure


# Imports required for drawing

import numpy as np
from qiskit_metal import draw
from qiskit_metal.toolbox_python.attr_dict import Dict
from qiskit_metal.components.base.base import QComponent

# Define class and options for the launch geometry

class LaunchV1(QComponent):

    """    Inherits QComponent class"""

    '''
    Description:
    ----------------------------------------------------------------------------
    Create a launch with a ground pocket cuttout.  Geometry is hardcoded set of
    polygon points for now. The (0,0) point is the center of the end of the launch.


    Options:
    ----------------------------------------------------------------------------
    Convention: Values (unless noted) are strings with units included,
                (e.g., '30um')

    Launch Metal Geometry and Ground Cuttout Pocket:
    ----------------------------------------------------------------------------
    cpw_width - center trace width of the CPW lead line and cap fingers
    cpw_gap - gap of the cpw line
    leadin_length  - length of the cpw line attached to the end of the launch                                
    pos_x / pos_y   - where the center of the pocket should be located on chip
    orientation     - degree of qubit rotation
    pocket is a negative shape that is cut out of the ground plane

    Connectors:
    ----------------------------------------------------------------------------
    There are two connectors on the capacitor at either end
    The connector attaches directly to the built in lead length and only needs a width defined
    cpw_width      - center trace width of the CPW line where the connector is placed
    
    

    Sketch:  TODO
    ----------------------------------------------------------------------------

    '''

   #  TODO _img = 'LaunchV1.png'



   #Define structure functions    

    default_options = Dict(
        layer = '1',
        cpw_width = '10um',
        cpw_gap = '6um',
        leadin_length = '65um',
        position_x = '100um',
        position_y = '100um',
        orientation = '0' #90 for 90 degree turn
    )

    def make(self):
        """ This is executed by the user to generate the qgeometry for the component.
        """
        p = self.p
        #########################################################
       
        # Geometry of main launch structure
        launch_pad = draw.Polygon([(0, p.cpw_width/2), (-.122, .035+p.cpw_width/2),
                           (-.202,.035+p.cpw_width/2), (-.202,-.045+p.cpw_width/2),
                           (-.122,-.045+p.cpw_width/2),(0,-p.cpw_width/2),
                           (p.leadin_length,-p.cpw_width/2),(p.leadin_length,+p.cpw_width/2),
                           (0, p.cpw_width/2)])

        # Geometry pocket
        pocket  = draw.Polygon([(0, p.cpw_width/2+p.cpw_gap), 
                        (-.122, .087+p.cpw_width/2+p.cpw_gap),
                           (-.25,.087+p.cpw_width/2+p.cpw_gap), 
                        (-.25,-.109+p.cpw_width/2+p.cpw_gap),
                           (-.122,-.109+p.cpw_width/2+p.cpw_gap),
                        (0,-p.cpw_width/2-p.cpw_gap), 
                        (p.leadin_length,-p.cpw_width/2-p.cpw_gap),
                       (p.leadin_length,+p.cpw_width/2+p.cpw_gap),
                       (0, p.cpw_width/2+p.cpw_gap)])

        # These variables are used to graphically locate the pin locations 
        main_pin_line = draw.LineString([(p.leadin_length,p.cpw_width/2),
                        (p.leadin_length,-p.cpw_width/2)])
                
        # create polygon object list         
        polys1 = [main_pin_line, launch_pad, pocket]

        #rotates and translates all the objects as requested. Uses package functions in 'draw_utility' for easy
        # rotation/translation
        polys1 = draw.rotate(polys1, p.orientation, origin=(p.leadin_length,0))
        polys1 = draw.translate(polys1, xoff=p.position_x, yoff=p.position_y)
        [main_pin_line, launch_pad, pocket] = polys1  

        # Adds the object to the qgeometry table 
        self.add_qgeometry('poly', dict(launch_pad=launch_pad), layer=p.layer)
        
        #subtracts out ground plane on the layer its on
        self.add_qgeometry('poly', dict(pocket=pocket), subtract=True, layer=p.layer) 
 
        # add pin extensions
        self.add_qgeometry('path', {'a': main_pin_line}, width=0, layer=p.layer)

        # Generates the pins                
        self.add_pin('a', main_pin_line.coords, p.cpw_width)        