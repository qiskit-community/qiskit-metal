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
@date: 2019
@author: Zlatko K Minev
modified: Thomas McConkey - Added Charge Line


Pocket "axis"
        _________________
        |               |
        |_______________|       ^
        ________x________       |  N
        |               |       |
        |_______________|

Child of 'standard' transmon pocket
'''
# pylint: disable=invalid-name
# Modification of Transmon Pocket Object to include a charge line (would be better to just make as a child)

from copy import deepcopy
from ... import draw
from ...toolbox_python.attr_dict import Dict
from ..._defaults import DEFAULT_OPTIONS
from .transmon_pocket import TransmonPocket


DEFAULT_OPTIONS['TransmonPocketCL.con_lines'] = deepcopy(
    DEFAULT_OPTIONS['TransmonPocket.con_lines'])


DEFAULT_OPTIONS['TransmonPocketCL'] = deepcopy(
    DEFAULT_OPTIONS['TransmonPocket'])
DEFAULT_OPTIONS['TransmonPocketCL'].update(Dict(
    make_CL=True,
    cl_gap='6um',  # the cpw dielectric gap of the charge line
    cl_width='10um',  # the cpw trace width of the charge line
    cl_length='20um',  # the length of the charge line 'arm' coupling the the qubit pocket. Measured from the base of the 90 degree bend
    cl_ground_gap='6um',  # how much ground between the charge line and the qubit pocket
    # the side of the qubit pocket the charge line is placed on (before any rotations)
    cl_pocket_edge='0', #-180 to +180 from the 'left edge', will round to the nearest 90.
    cl_off_center='100um',  # distance from the center axis the qubit pocket is built on
))


class TransmonPocketCL(TransmonPocket):  # pylint: disable=invalid-name
    '''

    Description:
    ----------------------------------------------------------------------------
    Create a standard pocket transmon qubit for a ground plane,
    with two pads connectored by a junction (see drawing below).

    Connector lines can be added using the `options_con_lines`
    dicitonary. Each connector line has a name and a list of default
    properties.

    This is a child of TransmonPocket, see TransmonPocket for the variables and
    description of that class.

    Options:
    ----------------------------------------------------------------------------
    Convention: Values (unless noted) are strings with units included,
                (e.g., '30um')

    Charge Line:
    ----------------------------------------------------------------------------

    '''

    # def __init__(self, design, name, options=None, options_connectors=None):
    #    super().__init__(design, name, options, options_connectors)


    def make(self):
        super().make()

        if self.options.make_CL == True:
            self.make_charge_line()


#####################################################################


    def make_charge_line(self):
        # Grab option values
        name = 'Charge_Line'
        
        p = self.p

        cl_arm = draw.box(0, 0, -p.cl_width, p.cl_length)
        cl_cpw = draw.box(0, 0, -8*p.cl_width, p.cl_width)
        cl_metal = draw.cascaded_union([cl_arm, cl_cpw])

        cl_etcher = draw.buffer(cl_metal, p.cl_gap)

        port_line = draw.LineString([(-8*p.cl_width, 0), (-8*p.cl_width, p.cl_width)])

        polys = [cl_metal, cl_etcher, port_line]

        # Move the charge line to the side user requested
        cl_rotate = 0
        if (abs(p.cl_pocket_edge) > 135) or (abs(p.cl_pocket_edge) <45):
            polys = draw.translate(polys, -(p.pocket_width/2 + p.cl_ground_gap + p.cl_gap),
             -(p.pad_gap + p.pad_height)/2)
            if (abs(p.cl_pocket_edge) > 135):
                p.cl_rotate = 180
        else:
            polys = draw.translate(
                polys, -(p.pocket_height/2 + p.cl_groundGap + p.cl_gap), -(p.pad_width)/2)
            cl_rotate = 90
            if (p.cl_pocket_edge<0):
                cl_rotate = -90


        # Rotate it to the pockets orientation
        polys = draw.rotate(polys, p.orientation + cl_rotate, origin=(0, 0))

        # Move to the final position
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        [cl_metal, cl_etcher, port_line] = polys

        # Making the design connector for 'easy connect'
        points = draw.get_poly_pts(port_line)
        self.design.add_connector(name, points, self.name, flip=False)  # TODO: chip

        self.add_elements('poly', dict(cl_metal=cl_metal))
        self.add_elements('poly', dict(cl_etcher = cl_etcher), subtract=True)
