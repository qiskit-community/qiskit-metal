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
from shapely.geometry import shape
from shapely.affinity import scale

from ...config import Dict, DEFAULT_OPTIONS
from ...draw_functions import shapely, shapely_rectangle, translate, translate_objs,\
    rotate_objs, rotate_obj_dict, scale_objs, _angle_Y2X, make_connector_props,\
    Polygon, parse_options_user, parse_units_user, buffer
from .Metal_Transmon_Pocket import Metal_Transmon_Pocket


DEFAULT_OPTIONS['Metal_Transmon_Pocket_CL.connectors'] = deepcopy(
    DEFAULT_OPTIONS['Metal_Transmon_Pocket.connectors'])


DEFAULT_OPTIONS['Metal_Transmon_Pocket_CL'] = deepcopy(
    DEFAULT_OPTIONS['Metal_Transmon_Pocket'])
DEFAULT_OPTIONS['Metal_Transmon_Pocket_CL'].update(Dict(
    make_CL='ON',
    cl_gap='6um',  # the cpw dielectric gap of the charge line
    cl_width='10um',  # the cpw trace width of the charge line
    cl_length='20um',  # the length of the charge line 'arm' coupling the the qubit pocket. Measured from the base of the 90 degree bend
    cl_groundGap='6um',  # how much ground between the charge line and the qubit pocket
    # the side of the qubit pocket the charge line is placed on (before any rotations)
    cl_PocketEdge='W', #placeholder for now
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

        if self.options.make_CL == 'ON':
            self.make_chargeLine()


#####################################################################


    def make_chargeLine(self):
        # Grab option values
        options = self.options
        name = 'Charge_Line'
        cl_gap, cl_width, cl_length, cl_groundGap = parse_options_user(
            options, 'cl_gap, cl_width, cl_length, cl_groundGap',
            self.design.params.variables)

        pad_gap, pad_height, pocket_width, pocket_height, pad_width,\
            pos_x, pos_y = parse_options_user(options,
                'pad_gap, pad_height, pocket_width, pocket_height, pad_width, pos_x, pos_y',
                self.design.params.variables)

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
        cl_PocketEdge = options['cl_PocketEdge']
        # Move the charge line to the side user requested
        cl_Rotate = 0
        if (cl_PocketEdge.upper() == 'W') or (cl_PocketEdge.upper() == 'E'):
            objects = translate_objs(
                objects, -(pocket_width/2 + cl_groundGap + cl_gap), -(pad_gap + pad_height)/2)
            if (cl_PocketEdge.upper() == 'E'):
                cl_Rotate = 180
        elif (cl_PocketEdge.upper() == 'N') or (cl_PocketEdge.upper() == 'S'):
            objects = translate_objs(
                objects, -(pocket_height/2 + cl_groundGap + cl_gap), -(pad_width)/2)
            cl_Rotate = 90
            if (cl_PocketEdge.upper() == 'N'):
                cl_Rotate = -90


        # Rotate it to the pockets orientation
        objects = rotate_objs(objects, _angle_Y2X[options['orientation']] + cl_Rotate, origin=(0, 0))

        # Move to the final position
        objects = translate_objs(objects, pos_x, pos_y)

        # Making the design connector for 'easy connect'
        design = self.design
        if not design is None:
            portPoints = list(shape(objects['port_Line']).coords)
            vNorm = (-(portPoints[1][1] - portPoints[0][1]), (portPoints[1][0]-portPoints[0][0]))
            design.connectors[self.name+'_' +
                            name] = make_connector_props(portPoints, options, vec_normal=vNorm)

        # Removes temporary port_line from draw objects
        del objects['port_Line']

        # add to objects
        self.objects.CL = objects

        return objects

#Super call not quite working
    # def hfss_draw(self):
    #     '''
    #     Draw in HFSS.
    #     Makes a meshing recntalge for the the pocket as well.
    #     '''
    #     super().hfss_draw()

    #     if options.make_CL == 'ON': #checks if this qubit has a charge line, and if it does etches the appropriate section
    #         oModeler.subtract(ground, [hfss_objs.CL['cl_Etcher']])

    #     #attaches the different relevant geometries to perfect E boundaries (as equivalent thin film superconductor)
    #     if DEFAULT['do_PerfE']:
    #        if options.make_CL == 'ON':
    #             oModeler.append_PerfE_assignment(name+'_CL' if DEFAULT['BC_individual'] else options_hfss['BC_name_conn'], hfss_objs.CL['cl_Metal'])

    #    # if DEFAULT._hfss.do_mesh:

    #     return hfss_objs
