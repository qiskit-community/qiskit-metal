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

Attempted version functioning as child of 'standard' transmon pocket
***This is the child version which still is a bit buggy.***
'''
# pylint: disable=invalid-name
# Modification of Transmon Pocket Object to include a charge line (would be better to just make as a child)

from copy import deepcopy
from shapely.ops import cascaded_union


from ... import DEFAULT_OPTIONS, DEFAULT, Dict
from ... import draw
from ...renderers.renderer_ansys import draw_ansys
from ...renderers.renderer_ansys.parse import to_ansys_units
from .Metal_Qubit import Metal_Qubit

from .Metal_Transmon_Pocket import Metal_Transmon_Pocket


DEFAULT_OPTIONS['Metal_Transmon_Pocket_CL.connectors'] = deepcopy(
    DEFAULT_OPTIONS['Metal_Transmon_Pocket.connectors'])


DEFAULT_OPTIONS['Metal_Transmon_Pocket_CL'] = deepcopy(
    DEFAULT_OPTIONS['Metal_Transmon_Pocket'])
DEFAULT_OPTIONS['Metal_Transmon_Pocket_CL'].update(Dict(
    make_CL=True,
    cl_gap='6um',  # the cpw dielectric gap of the charge line
    cl_width='10um',  # the cpw trace width of the charge line
    cl_length='20um',  # the length of the charge line 'arm' coupling the the qubit pocket. Measured from the base of the 90 degree bend
    cl_groundGap='6um',  # how much ground between the charge line and the qubit pocket
    # the side of the qubit pocket the charge line is placed on (before any rotations)
    cl_PocketEdge='0', #-180 to +180 from the 'left edge', will round to the nearest 90.
    cl_offCenter='100um',  # distance from the center axis the qubit pocket is built on
))


class Metal_Transmon_Pocket_CL(Metal_Transmon_Pocket):  # pylint: disable=invalid-name
    '''
    Makes a standard transmon qubit with two pads connectored by a junction.

    Can add connectors on it using the `options_connectors` dictonary
    '''

    # def __init__(self, design, name, options=None, options_connectors=None):
    #    super().__init__(design, name, options, options_connectors)

# super call not quite working
    def make(self):
        super().make()

        if self.options.make_CL == True:
            self.make_chargeLine()


#####################################################################


    def make_chargeLine(self):
        # Grab option values
        options = self.options
        name = 'Charge_Line'
        cl_gap, cl_width, cl_length, cl_groundGap, cl_PocketEdge = self.design.get_option_values(
            options, 'cl_gap, cl_width, cl_length, cl_groundGap, cl_PocketEdge')

        pad_gap, pad_height, pocket_width, pocket_height, pad_width,\
            pos_x, pos_y,orientation = self.design.get_option_values(options,
                'pad_gap, pad_height, pocket_width, pocket_height, pad_width, pos_x, pos_y, orientation')

        cl_Arm = shapely.geometry.box(0, 0, -cl_width, cl_length)
        cl_CPW = shapely.geometry.box(0, 0, -8*cl_width, cl_width)
        cl_Metal = cascaded_union([cl_Arm, cl_CPW])

        cl_Etcher = buffer(cl_Metal, cl_gap)

        port_Line = shapely.geometry.LineString([(-8*cl_width, 0), (-8*cl_width, cl_width)])

        objects = dict(
            cl_Metal=cl_Metal,
            cl_Etcher=cl_Etcher,
            port_Line=port_Line,
        )

        # Move the charge line to the side user requested
        cl_Rotate = 0
        if (abs(cl_PocketEdge) > 135) or (abs(cl_PocketEdge) <45):
            objects = translate(
                objects, -(pocket_width/2 + cl_groundGap + cl_gap), -(pad_gap + pad_height)/2)
            if (abs(cl_PocketEdge) > 135):
                cl_Rotate = 180
        else:
            objects = translate(
                objects, -(pocket_height/2 + cl_groundGap + cl_gap), -(pad_width)/2)
            cl_Rotate = 90
            if (cl_PocketEdge<0):
                cl_Rotate = -90


        # Rotate it to the pockets orientation
        objects = rotate(objects, orientation + cl_Rotate, origin=(0, 0))

        # Move to the final position
        objects = translate(objects, pos_x, pos_y)

        # Making the design connector for 'easy connect'
        design = self.design
        if not design is None:
            portPoints = list(shape(objects['port_Line']).coords)
            vNorm = (-(portPoints[1][1] - portPoints[0][1]), (portPoints[1][0]-portPoints[0][0]))
            raise NotImplemented('Update make_connector -- add to design!?')
            design.connectors[self.name+'_' +
                            name] = make_connector(portPoints, options, vec_normal=vNorm)

        # Removes temporary port_line from draw objects
        del objects['port_Line']

        # add to objects
        self.components.CL = objects

        return objects
