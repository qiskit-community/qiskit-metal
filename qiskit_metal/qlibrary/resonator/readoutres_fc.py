import numpy as np
import sys

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import BaseQubit

class ReadoutRes_fc(BaseQubit):
    '''
    The base ReadoutRes_fc class

    Inherits BaseQubit class

    Readout resonator for the flipchip dev. Written for the flipchip tutorial.

    '''

    default_options = Dict(
            pos_x = '0 um',
            pos_y = '0 um',
            readout_radius = '50 um',
            readout_cpw_width = '5 um',
            readout_cpw_gap = '5 um',
            readout_cpw_turnradius = '50 um',
            readout_l1 = '400 um',
            readout_l2 = '400 um',
            readout_l3 = '400 um',
            readout_l4 = '250 um',
            readout_l5 = '400 um',
            arc_step = '1 um',
            orientation = '0',
            layer = '1',
            layer_subtract = '2',
            subtract = True,
            chip = 'main',
            _default_connection_pads=Dict()
            )
    
    ''' Default drawing options ?? '''
    component_metadata = Dict(
            short_name = 'readoutres_fc',
            _qgeometry_table_poly = 'True',
            _qgeometry_table_junction = 'False')

    ''' Component metadata '''

    ##########################
    def make(self):
        ''' Make the head for readout res'''
        self.make_ro()
        return
    ##########################

    def make_ro(self):
        '''
        Create the head of the readout resonator. Contains:
            - the circular patch for coupling
            - the 45 deg line
            - the 45 deg arc
            - a short straight segment (of length w) for smooth subtraction
        '''
        # access to parsed values from the user option
        p = self.p

        # access to chip name
        chip = p.chip
        
        # local variables
        r = p.readout_radius
        w = p.readout_cpw_width
        g = p.readout_cpw_gap
        turnradius = p.readout_cpw_turnradius
        l1 = p.readout_l1
        l2 = p.readout_l2
        l3 = p.readout_l3
        l4 = p.readout_l4
        l5 = p.readout_l5


        # create the coupling patch in term of a circle
        cppatch = draw.Point(0,0).buffer(r)

        # create the extended arm
        ## useful coordinates
        x1, y1 = l1*np.cos(np.pi/4),  -l1*np.sin(np.pi/4)
        x2, y2 = x1 + turnradius*(1-np.cos(np.pi/4)),  y1 - turnradius*np.sin(np.pi/4)
        coord_init = draw.Point(x1,y1)
        coord_center = draw.Point(x1-turnradius*np.cos(np.pi/4),y1-turnradius*np.sin(np.pi/4))
        x3, y3 = x2, y2
        x4, y4 = x3, y3-l2
        x5, y5 = x4 + turnradius, y4
        coord_init1 = draw.Point(x4,y4)
        coord_center1 = draw.Point(x5,y5)
        x6, y6 = x5, y5-turnradius
        x7, y7 = x5 + l3, y6
        x8, y8 = x7, y7 + turnradius
        coord_init2 = draw.Point((x7,y7))
        coord_center2 = draw.Point((x8,y8))
        x9, y9 = x8, y8 +  turnradius
        x10, y10 = x8 - l4, y9
        x11, y11 = x10, y10 + turnradius
        coord_init3 = draw.Point((x10,y10))
        coord_center3 = draw.Point((x11,y11))
        arc3 = self.arc(coord_init3, coord_center3, -np.pi)
        x12, y12 = x11, y11 + turnradius
        x13, y13 = x12+l5, y12
        line12 = draw.LineString([(x12,y12), (x13,y13)])
        x14, y14 = x13, y13 + turnradius
        coord_init4 = draw.Point((x13,y13))
        coord_center4 = draw.Point((x14, y14))
        arc4 = self.arc(coord_init4, coord_center4, np.pi)
        ## line containing the 45deg line, 45 deg arc, and a short straight segment for smooth subtraction
        cparm_line = draw.shapely.ops.unary_union([
            draw.LineString([(0, 0), coord_init]),
            self.arc(coord_init, coord_center, -np.pi/4),
            draw.LineString([(x3,y3), (x4, y4)]),
            self.arc(coord_init1, coord_center1, np.pi/2),
            draw.LineString([(x6,y6), (x7,y7)]),
            self.arc(coord_init2, coord_center2, np.pi),
            draw.LineString([(x9, y9), (x10, y10)]),
            arc3,
            line12,
            arc4,
            draw.translate(line12, 0, 2*turnradius),
            draw.translate(arc3, 0, 4*turnradius),
            draw.translate(line12, 0, 4*turnradius),
            draw.translate(arc4, 0, 4*turnradius),
            draw.translate(line12, 0, 6*turnradius),
            draw.translate(arc3, 0, 8*turnradius),
            draw.translate(line12, 0, 8*turnradius)
            ])
        cparm = cparm_line.buffer(w/2, cap_style=2, join_style=1)
        ## fix the gap resulting from buffer
        eps = 1e-3
        cparm = draw.Polygon(cparm.exterior)
        cparm = cparm.buffer(eps, join_style=2).buffer(-eps, join_style=2)

        # create combined objects for the signal line and the etch
        ro = draw.shapely.ops.unary_union([cppatch,cparm])
        ro_etch = ro.buffer(g, cap_style=2, join_style=2)
        x15, y15 = x14, y14 + 7*turnradius
        x16, y16 = x15+g/2, y15
        port_line = draw.LineString([(x15, y15+w/2), (x15, y15-w/2)])
        subtract_patch = draw.LineString([(x16, y16-w/2-g-eps), (x16, y16+w/2+g+eps)]).buffer(g/2, cap_style=2)
        ro_etch = ro_etch.difference(subtract_patch)

        # rotate and translate
        polys = [ro, ro_etch, port_line]
        polys = draw.rotate(polys, p.orientation, origin=(0,0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)

        # update each object
        [ro, ro_etch, port_line] = polys

        # generate QGeometry
        self.add_qgeometry('poly', dict(ro=ro), chip=chip, layer=p.layer)
        self.add_qgeometry('poly', dict(ro_etch=ro_etch), chip=chip, layer=p.layer_subtract, subtract=p.subtract)
        
        # generate pins
        self.add_pin('readout', port_line.coords, width=w, gap=g, chip=chip)
        return

    def arc(self, coord_init, coord_center, angle):
        '''
        Generate x,y coordinates (in terms of shapely.geometry.Point()) of an arc with a specified initial point, rotation center, and rotation direction (specified by angle in radian (float or integer), positive is ccw).
        coord_init, and coord_center should be shapely.geometry.Point object
        '''
        # access to parse values from the user option
        p = self.p

        # local variable
        r = p.readout_cpw_turnradius
        step = p.arc_step

        # determine step number
        step_angle = step/r if angle >=0 else -step/r
        step_N = abs(int(angle/step_angle))
        laststep_flag = True if angle%step_angle!=0 else False

        # generate coordinate
        coord = [coord_init]
        point = coord_init
        for i in range(step_N):
            point = draw.rotate(point, step_angle, origin=coord_center, use_radians=True)
            coord.append(point)
        if laststep_flag:
            point = draw.rotate(coord_init, angle, origin=coord_center, use_radians=True)
            coord.append(point)
        coord = draw.LineString(coord)
        return coord
