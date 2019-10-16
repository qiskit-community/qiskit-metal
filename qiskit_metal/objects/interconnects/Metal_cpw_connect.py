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
modified: Thomas McConkey 2019/10/15
'''
# pylint: disable=invalid-name

from numpy import array
from ..base_objects.Metal_Object import Metal_Object, Dict
from ...config import DEFAULT_OPTIONS
from ...draw_cpw import parse_options_user, CAP_STYLE, JOIN_STYLE, meander_between, draw_cpw_trace, LineString, to_Vec3D


DEFAULT_OPTIONS['Metal_cpw_connect'] = Dict(
    connector1='[INPUT NAME HERE]',
    connector2='[INPUT NAME HERE]',
    connector1_leadin='200um',
    connector2_leadin='200um',
    _hfss=Dict(),
    _gds=Dict(),
    _calls=['meander_between', 'connectorCPW_plotme',
            'draw_cpw_trace', 'basic_meander']
)
'''
 connector1 : connector 1 from which to begin drawing the CPW
 connector2 : connectors 2 where to end the drawing of the CPW
'''


class Metal_cpw_connect(Metal_Object):
    '''

Description:
    ----------------------------------------------------------------------------
    Creates a meandered CPW transmission line between two 'connector' points.
    The transmission line is drawn from "connector1" to "connector2". These are
    tracked in the circuit dictionary which must also have been passed in.

    Total length of the meander is found from;

Options:
    ----------------------------------------------------------------------------
    Convention: Values (unless noted) are strings with units included,
                (e.g., '30um')

    Metal_cpw_connect (options)
    ----------------------------------------------------------------------------
    connector1: string of the name of the starting connector point (as listed in circuit.connectors dictionary)
    connector2: string of the name of the ending connector point (as listed in circuit.connectors dictionary)
    connector1/2_leadin: 'buffer' length of straight CPW transmission line from the connector point
    _hfss=Dict(): options for hfss useage
    _gds=Dict(): options for gds useage
    _calls:

    draw_cpw_trace (options_cpw):
    ----------------------------------------------------------------------------


    meander_between (options_meander):
    ----------------------------------------------------------------------------



    You must pass in the circuit object, which keeps tracks of all the connects

    Conect named control points: connector1 ---> connector2,
    '''
    _img = 'Metal_cpw_connect.png'

    def __init__(self, circ, name=None, options=None,
                 connector1=None,
                 connector2=None,
                 options_cpw=None,
                 options_meander=None
                 ):

        if options is None:
            options = DEFAULT_OPTIONS['Metal_cpw_connect'] #Dict()
        if options_cpw is None:
            options_cpw = DEFAULT_OPTIONS['draw_cpw_trace']  #Dict()
        if options_meander is None:
            options_meander = DEFAULT_OPTIONS['meander_between'] #Dict()

        options = Dict(options)

        if connector1 is None:
            assert 'connector1' in options
        else:
            options.connector1 = connector1

        if connector2 is None:
            assert 'connector2' in options
        else:
            options.connector2 = connector2

        if connector1 is '' or connector1 is '[INPUT NAME HERE]':
            raise Exception('ERROR: You did not provide a name for the leading connector connector1')
        if connector2 is '' or connector2 is '[INPUT NAME HERE]':
            raise Exception('ERROR: You did not provide a name for the second connector connector2')

        if name is None:
            name = 'cpw_'+options.connector1+'_'+options.connector2

        super().__init__(circ, name, options=options)

        assert options.connector1 in self.get_connectors(
        ), f'Connector name {options.connector1} not in the set of connectors defined {self.get_connectors().keys()}'
        assert options.connector2 in self.get_connectors(
        ), f'Connector name {options.connector2} not in the set of connectors defined {self.get_connectors().keys()}'

        self.options.cpw = Dict(**self.options.cpw, **options_cpw)
        self.options.meander = Dict(**self.options.meander, **options_meander)

        self.make()

    def make(self):
        connector1_leadin_dist, connector2_leadin_dist = parse_options_user(
            self.options, 'connector1_leadin, connector2_leadin')

        # connectors
        connectors = self.get_connectors()
        c1 = connectors[self.options.connector1]
        c2 = connectors[self.options.connector2]
        #print( connector1_leadin_dist, connector2_leadin_dist, c1,c2, self.options.connector1)
        points0 = array([  # control points (user units)
            c1['pos'],
            c1['pos'] + c1['normal']*connector1_leadin_dist,
            c2['pos'] + c2['normal']*connector2_leadin_dist,
            c2['pos']
        ])

        if connector2_leadin_dist < 0:
            points0 = points0[:-1]

        # Control line
        self.points_meander = array(
            meander_between(points0, 1, self.options.meander))
        self.objects.cpw_line = LineString(self.points_meander)

        # For metal
        self.options.cpw = {
            **DEFAULT_OPTIONS['draw_cpw_trace'], **self.options.cpw, 'name': self.name}
        cpw_width, cpw_gap = parse_options_user(
            self.options.cpw, 'trace_center_width, trace_center_gap')
        self.objects.trace_center = self.objects.cpw_line.buffer(
            cpw_width/2, cap_style=CAP_STYLE.flat, join_style=JOIN_STYLE.mitre)
        self.objects.trace_gap = self.objects.trace_center.buffer(
            cpw_gap,  cap_style=CAP_STYLE.flat, join_style=JOIN_STYLE.mitre)

    def hfss_draw(self):
        options = self.options.cpw

        def to_vec3D(vec):
            return to_Vec3D(self.circ, options, vec)

        draw_cpw_trace(self.circ, to_vec3D(self.points_meander), options)
