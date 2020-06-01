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
@date: 2019/09/08
@author: Thomas McConkey

converted to v0.2: Thomas McConkey 2020-04-23
'''

from copy import deepcopy
from ... import draw
from ...toolbox_python.attr_dict import Dict
from ..base.qubit import BaseQubit

class TransmonCross(BaseQubit):  # pylint: disable=invalid-name
    '''
    Description:
    ----------------------------------------------------------------------------
    Simple Metal Transmon Cross object. Creates the A cross-shaped island,
    the "junction" on the south end, and up to 3 connectors on the remaining arms
    (claw or gap).

    'claw_width' and 'claw_gap' define the width/gap of the CPW line that
    makes up the connector. Note, DC SQUID currently represented by single
    inductance sheet

    Add connectors to it using the `connection_pads` dictonary. See BaseQubit for more
    information.

    Options:
    ----------------------------------------------------------------------------
    Convention: Values (unless noted) are strings with units included,
                (e.g., '30um')

    Main Body
    ----------------------------------------------------------------------------
        pos_x / pos_y - where the center of the Crossmon should be located on chip
        cross_width - width of the CPW center trace making up the Crossmon
        cross_length - length of one Crossmon arm (from center)
        cross_gap - width of the CPW gap making up the Crossmon
        orientation - how to orient the qubit and connectors in the end (where the +X vector should point, '+X', '-X','+Y','-Y')

    Connectors
    ----------------------------------------------------------------------------
        connectorType - string of 'Claw' or 'Gap' to define which type of connector is used.
        claw_length - length of the claw 'arms', measured from the connector center trace
        ground_spacing - amount of ground plane between the connector and Crossmon arm (minimum should be based on fabrication capabilities)
        claw_width - the width of the CPW center trace making up the claw/gap connector
        claw_gap - the gap of the CPW center trace making up the claw/gap connector
        connector_location - string of 'W', 'N', or 'E', which of the three arms where a given connector should be (South is for the junction)

    Sketch
    ----------------------------------------------------------------------------
                        claw_length
    Claw:       _________                    Gap:
                |   ________________             _________    ____________
          ______|  |                             _________|  |____________
                |  |________________
                |_________

    '''

    _img = 'Metal_Crossmon.png'

    default_options = Dict(
        pos_x='0um',
        pos_y='0um',
        cross_width='20um',
        cross_length='200um',
        cross_gap='20um',
        orientation='0',
        _default_connection_pads = Dict(
            connector_type='0', #0 = Claw type, 1 = gap type
            claw_length='30um',
            ground_spacing='5um',
            claw_width='10um',
            claw_gap='6um',
            connector_location='0' #0 => 'west' arm, 90 => 'north' arm, 180 => 'east' arm
        )
    )
##############################################MAKE######################################################
    def make(self):
        self.make_pocket()
        self.make_connection_pads()


###################################TRANSMON#############################################################
    def make_pocket(self):
        '''
        Makes a basic Crossmon, 4 arm cross.
        '''

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p

        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_gap = p.cross_gap

        #Creates the cross and the etch equivalent.
        cross_line =draw.shapely.ops.cascaded_union([draw.LineString([(0,cross_length),(0,-cross_length)]),
            draw.LineString([(cross_length,0),(-cross_length,0)])])

        cross = cross_line.buffer(cross_width/2,cap_style=2)
        cross_etch = cross.buffer(cross_gap, cap_style=3, join_style=2)

        #The junction/SQUID
        rect_jj = draw.rectangle(cross_width, cross_gap)
        rect_jj = draw.translate(rect_jj, 0, -cross_length-cross_gap/2)

        #rotate and translate
        polys = [cross,cross_etch,rect_jj]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        [cross,cross_etch,rect_jj] = polys

        #generate elements
        self.add_elements('poly', dict(cross=cross))
        self.add_elements('poly', dict(cross_etch = cross_etch), subtract=True)
        self.add_elements('poly', dict(rect_jj=rect_jj), helper=True)


############################CONNECTORS##################################################################################################
    def make_connection_pads(self):
        '''
        Goes through connectors and makes each one.
        '''
        for name in self.options.connection_pads:
            self.make_connection_pad(name)

    def make_connection_pad(self,name:str):
        '''
        Makes individual connector

        Args:
        -------------
        name (str) : Name of the connector
        '''

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p
        cross_width = p.cross_width
        cross_length = p.cross_length
        cross_gap = p.cross_gap

        pc = self.p.connection_pads[name] # parser on connector options
        c_g = pc.claw_gap
        c_l = pc.claw_length
        c_w = pc.claw_width
        g_s = pc.ground_spacing
        con_loc = pc.connector_location

        claw_cpw = draw.box(0, -c_w/2, -4*c_w, c_w/2)

        if pc.connector_type == 0: #Claw connector
            t_claw_height = 2*c_g + 2 * c_w + 2*g_s + 2*cross_gap + cross_width  # temp value

            claw_base = draw.box(-c_w, -(t_claw_height)/2, c_l, t_claw_height/2)
            claw_subtract = draw.box(0, -t_claw_height/2 + c_w, c_l, t_claw_height/2 - c_w)
            claw_base = claw_base.difference(claw_subtract)

            connector_arm = draw.shapely.ops.cascaded_union([claw_base, claw_cpw])
            connector_etcher = draw.buffer(connector_arm, c_g)
        else:
            connector_arm = claw_cpw
            connector_etcher = draw.buffer(connector_arm, c_g)
        
        
        #Making the connector 'port' for design.connector tracking (for easy connect functions). 
        # Done here so as to have the same translations and rotations as the connector. Could 
        # extract from the connector later, but since allowing different connector types, 
        # this seems more straightforward.
        port_line = draw.LineString([(-4*c_w, -c_w/2),(-4*c_w, c_w/2)])

        claw_rotate = 0
        if con_loc>135:
            claw_rotate = 180
        elif con_loc>45:
            claw_rotate = -90

        #Rotates and translates the connector polygons (and temporary port_line)
        polys = [connector_arm, connector_etcher, port_line]
        polys = draw.translate(polys, -(cross_length + cross_gap + g_s + c_g), 0)
        polys = draw.rotate(polys, claw_rotate, origin=(0, 0))
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [connector_arm, connector_etcher, port_line] = polys

        #Generates elements for the connector
        self.add_elements('poly', {f'{name}_connector_arm':connector_arm})
        self.add_elements('poly', {f'{name}_connector_etcher':connector_etcher}, subtract=True)

        port_points = list(draw.shapely.geometry.shape(port_line).coords)
        self.add_pin(name, port_points, self.id, flip=False)  # TODO: chip

