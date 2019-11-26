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
from ...config import DEFAULT_OPTIONS, DEFAULTS
from ...draw_cpw import parse_options_user, CAP_STYLE, JOIN_STYLE, meander_between, draw_cpw_trace, to_Vec3D
from ...draw_utility import flip_merge, orient_position, get_poly_pts
from ...draw_functions import make_connector_props, do_cut_ground, do_PerfE
from ...toolbox.parsing import parse_value_hfss

DEFAULT_OPTIONS['cpw_launcher'] = Dict({
    'chip'         : 'main',
    'base_width'   : '80um',
    'base_height'  : '80um',
    'base_gap'     : '58um',
    'launch_height': '122um',
    'cpw_width'    : DEFAULT_OPTIONS.cpw.width,
    'cpw_gap'      : DEFAULT_OPTIONS.cpw.gap,
    'mesh_gap'     : DEFAULT_OPTIONS.cpw.mesh_width,
    'pos_gap'      : '200um',                        # gap to edge of chip
    'position'     : "['X', -1, '7mm']",          # +1 or -1, '10um' position along edge
    'orientation'  : '0',                         # ignorred when triplet in position
    '_hfss'        : {
        'name' : 'Launcher',
        'chip' : 'main',
        'category' : 'launchers',
        'do_draw'  : 'True',
        'do_cut'   : 'True',
        'do_PerfE' : 'True',
        'do_mesh'  : 'false',
        'BC_name'  : 'Launchers',
        'kw_poly'  : f"{{'color':{DEFAULTS['col_in_cond']}}}"
    }
})

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

        options = {**DEFAULT_OPTIONS['make_launcher_basic'], **{
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

        ### Draw linesshapes firtst
        # Inner piece
        line_inner  = shapely.wkt.loads(f'LINESTRING (0 0, {Bw} 0, {Bw} {Bh}, {Cw} {Bh+Lh})')
        # Outside piece which gets cut from ground plane 
        line_outter = LineString(array(line_inner.coords)  + array(((0,-Bg),(+Bg,-Bg),(+Bg,0),(Cg,0))))
        #
        line_mesh = LineString(array(line_outter.coords) + array(((0,-Mg),(+Mg,-Mg),(+Mg,0),(Mg,0))))

        ### Turn into poygons
        poly_inner  = Polygon(flip_merge(line_inner))
        poly_outer = Polygon(flip_merge(line_outter))
        poly_mesh = Polygon(flip_merge(line_mesh))


        # Position
        pos  = ops['position']
        if len(pos) == 3:
            # specify from edge of chip -- done poorly, do in a more user friendly way?
            chip_size = self.self.design.get_chip_size('main') # array of 3 numbers
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
        poly_inner, poly_outer, poly_mesh = orient_position([poly_inner, poly_outer, poly_mesh],  angle, pos1)

        self.objects.update(dict(
            inner = poly_inner,
            outer = poly_outer,
            mesh = poly_mesh,
        ))

        # Connectors
        start = 3
        points = get_poly_pts(poly_inner)[start:start+2]
        self.add_connector(points, chip = ops['chip'], flip=True)


    def hfss_draw(self):
            
        # Params
        options  = self.options._hfss
        options['chip_size'] = self.design.get_chip_size(self.options.chip)
        to_vec3D = lambda vec: to_Vec3D(self.design, options, parse_value_hfss(vec))
        name     = self.name #options['name']
        
        # Make shapes in user units 
        poly0 = self.objects['inner']
        poly1 = self.objects['outer']
        polyM = self.objects['mesh']
        
        if options['do_draw']: # Draw 
            
            oDesign, oModeler = self.design.get_modeler()
            def draw(poly, name_sup, flag=None):
                ops = self.design.parse_value(options['kw_poly'])
                if not flag is None:
                    ops = {**ops,**{'transparency':flag}}
                line = oModeler.draw_polyline(to_vec3D(get_poly_pts(poly)), closed=True, **ops)
                line = line.rename(name + name_sup)
                return line
            
            Poly0 = draw(poly0,'',0)
            Poly1 = draw(poly1,'_cut')
            Poly2 = draw(polyM,'_mesh',1) if options['do_mesh'] else None
            
            do_cut_ground(options, self.design, [str(Poly1)])
            do_PerfE(options, self.design, Poly0)
            
            if options['do_mesh']:
                pass
        
            # these should be stored in the rendered or inside this  
            self.objects_hfss.update({
                'inner':Poly0,
                'outer':Poly1,
                'mesh':Poly2
            })