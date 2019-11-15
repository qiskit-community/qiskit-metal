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
'''
#TODO: Add taper options

import shapely

from numpy import array
from shapely.geometry import LineString, Polygon

from ..base_objects.Metal_Object import Metal_Object, Dict
from ...config import DEFAULT_OPTIONS
from ...draw_cpw import parse_options_user, CAP_STYLE, JOIN_STYLE, meander_between, draw_cpw_trace, to_Vec3D
from ...draw_utility import flip_merge, orient_position, get_poly_pts
from ...draw_functions import make_connector_props

DEFAULT_OPTIONS['cpw_launcher'] = Dict({
    'name'         : 'Launch',
    'base_width'   : '80um',
    'base_height'  : '80um',
    'base_gap'     : '58um',
    'launch_height': '122um',
    'cpw_width'    : DEFAULT_OPTIONS.cpw.width,
    'cpw_gap'      : DEFAULT_OPTIONS.cpw.gap,
    'mesh_gap'     : DEFAULT_OPTIONS.cpw.mesh_width,
    'pos_gap'      : '200um',                        # gap to edge of chip
    'position'     : "['X', -1, '7mm']",          # +1 or -1, '10um' position along edge
    'orientation'  : '0', # ignorred when triplet in position
    'chip_size'    : "['8.5mm', '6.5mm', '-750um']", # should get this
    }
)

class cpw_launcher(Metal_Object):
    """
    Planar CPW Launcher

    Description:
    ----------------------------------------------------------------------------
    For making basic CPW chip 'edge' launchers. Simple linear taper to CPW transmission line.
    Assumes chip  is centered  at (0,0)

    Options:
    ----------------------------------------------------------------------------
    Convention: Values (unless noted) are strings with units included,
                (e.g., '30um')

    make_launcher_basic
    ----------------------------------------------------------------------------
    name: string of the launcher's name
    base_width: width of the wirebond pad (side parallel to chip edge)
    base_height: length of the wirebond pad (side orthogonal to chip edge)
    base_gap: dielectric gap between ground and pad
    launch_height: length of taper
    cpw_width: center trace width of the CPW transmission line
    cpw_gap: dielectric gap of the CPW transmission line
    mesh_gap: width for HFSS mesh operations on the CPW transmission line
    position: [which edge the launcher is based on, positive or negative edge, position along the edge from origin]
    pos_gap: how far from the chip edge the launcher is placed
    chip_size: [X_width of the chip, Y_width of the chip, Z_height of the chip]

    Example use: ????

    .. code-block:: python

        options = combinekw(DEFAULT_OPTIONS['make_launcher_basic'], {
            'position'     : ['X', -1, '7mm']
        })
        poly, poly1, polyM, line, line1, lineM = make_launcher_basic(options)
        for p in reversed((poly, poly1, polyM)):
            p.draw()

    """

    def make(self):
        '''
        Draw in natural space and do so symmetrically

        Create Shapely Objects
        '''

        # Dimensions
        ops = self.parse_options()

        Bw = ops['base_width']
        Bh = ops['base_height']
        Lh = ops['launch_height']
        Cw = ops['cpw_width']
        Cg = ops['cpw_gap']
        Bg = ops['base_gap']
        Mg = ops['mesh_gap']

        Mg  = 0 if Mg is None else Mg
        Bw /= 2.
        Cw /= 2.

        line  = shapely.wkt.loads(f'LINESTRING (0 0, {Bw} 0, {Bw} {Bh}, {Cw} {Bh+Lh})')
        poly  = Polygon(flip_merge(line))
        # Outside path and mesh
        line1 = LineString(array(line.coords)  + array(((0,-Bg),(+Bg,-Bg),(+Bg,0),(Cg,0))))

        lineM = LineString(array(line1.coords) + array(((0,-Mg),(+Mg,-Mg),(+Mg,0),(Mg,0))))

        poly1 = Polygon(flip_merge(line1))
        polyM = Polygon(flip_merge(lineM))


        # Position
        pos  = ops['position']
        if len(pos) == 3:
            # specify from edge of chip -- done poorly, do in a more user friendly way?
            chip_size = self.design.get_chip_size('main') # array of 3 numbers
            arg = {'X':1, 'Y':0}[pos[0]]

            posY = pos[1]*chip_size[arg]/2. - ops['pos_gap']
            pos1 = self.parse_value((pos[2], posY))
            pos1 = pos1 if pos[0] == 'X' else tuple(reversed(pos1))

            angle = {('X',-1):0, ('X',+1):180, ('Y',-1):-90, ('Y',+1):90}.get(tuple(pos[:2]))

        elif len(pos) == 2:
            pos1 = pos
            angle = ops['orientation']

        else:
            raise ValueError("Cannot interpreit position of chip. Check how you specified it!! See the help of this class. ")

        # Move and orient
        poly, poly1, polyM = orient_position([poly, poly1, polyM],  angle, pos1)

        self.objects.update(dict(
            poly = poly,
            poly1 = poly1,
            polyM = polyM,
        ))

        # Connectors
        start = 3
        self.design.connectors[self.name] = \
            make_connector_props(get_poly_pts(poly)[start:start+2],
                                 self.options, unparse=False)



    def hfss_draw(self):
        pass