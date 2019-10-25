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
modified: Thomas McConkey 2019

.. code-block::
     ________________________________
    |______ ____           __________|
    |      |____|         |____|     |
    |        __________________      |
    |       |                  |     |
    |       |__________________|     |
    |                 |              |
    |                 x              |
    |        _________|________      |
    |       |                  |     |
    |       |__________________|     |
    |        ______                  |
    |_______|______|                 |
    |________________________________|


'''
# pylint: disable=invalid-name

from copy import deepcopy
from ...config import DEFAULT_OPTIONS, DEFAULT
from ...draw_functions import shapely, shapely_rectangle, translate, translate_objs,\
    rotate_objs, rotate_obj_dict, scale_objs, _angle_Y2X, make_connector_props,\
    Polygon, parse_options_user, parse_units_user, buffer, LineString,\
    Dict#, draw_objs
from ... import draw_hfss
from .Metal_Qubit import Metal_Qubit


DEFAULT_OPTIONS['Metal_Transmon_Pocket.connectors'] = Dict(
    pad_gap='15um',
    pad_width='125um',
    pad_height='30um',
    pad_cpw_shift='5um',
    pad_cpw_extent='25um',
    cpw_width=DEFAULT_OPTIONS.cpw.width,
    cpw_gap=DEFAULT_OPTIONS.cpw.gap,
    cpw_extend='100um',  # how far into the CPW to extend
    pocket_extent='5um',
    pocket_rise='65um',
    loc_W=+1,  # width location  only +-1
    loc_H=+1,  # height location only +-1
)


DEFAULT_OPTIONS['Metal_Transmon_Pocket'] = deepcopy(
    DEFAULT_OPTIONS['Metal_Qubit'])
DEFAULT_OPTIONS['Metal_Transmon_Pocket'].update(Dict(
    pos_x='0um',
    pos_y='0um',
    pad_gap='30um',
    inductor_width='20um',
    pad_width='455um',
    pad_height='90um',
    pocket_width='650um',
    pocket_height='650um',
    orientation='Y',  # X has dipole aligned along the +X axis, while Y has dipole aligned along the +Y axis

    _hfss=Dict(
        rect_options=dict(color=DEFAULT['col_in_cond'],
                          transparency=0),  # default options for a rectangle
        BC_name_pads='qubit_pads',
        BC_name_conn='qubit_connectors',
        mesh_name='qubit_pockets',
        mesh_name_jj='qubit_jjs',
        mesh_name_pad='qubit_pads',
        mesh_name_con='qubit_connectors',
        mesh_kw=Dict(MaxLength='100um'),
        mesh_kw_jj=Dict(MaxLength='7um'),
        mesh_kw_pad=Dict(MaxLength='35um'),
        mesh_kw_con=Dict(MaxLength='35um'),
        Lj='Lj_0',
        Cj=0,                    # Warning - do not use non zero for pyEPR analsys
        _Rj=0,                    # Warning - do not use non zero for pyEPR analsys
        category='qubits',
        chip='main',               # which chip does qubit belong to
        mesh_pocket='10um',              # How much to mesh the pokcet beyond
    ),

    _gds=Dict(

    ),
))


class Metal_Transmon_Pocket(Metal_Qubit): # pylint: disable=invalid-name
    '''
    Description:
    ----------------------------------------------------------------------------
    Create a standard pocket transmon qubit for a ground plane,
    with two pads connectored by a junction (see drawing below).

    Connectors can be added using the `options_connectors`
    dicitonary. Each connectors has a name and a list of default
    properties.

    Options:
    ----------------------------------------------------------------------------
    Convention: Values (unless noted) are strings with units included,
                (e.g., '30um')

    Pocket:
    ----------------------------------------------------------------------------
    pos_x / pos_y   - where the center of the pocket should be located on chip
                      (where the 'junction' is)
    pad_gap         - the distance between the two charge islands, which is also the
                      resulting 'length' of the pseudo junction
    inductor_width  - width of the pseudo junction between the two charge islands
                      (if in doubt, make the same as pad_gap). Really just for simulating in HFSS / other EM software
    pad_width       - the width (x-axis) of the charge island pads
    pad_height      - the size (y-axis) of the charge island pads
    pocket_width    - size of the pocket (cut out in ground) along x-axis
    pocket_height   - size of the pocket (cut out in ground) along y-axis
    orientation     - how the pocket is oreintated,'X' or 'Y', where Y applies a 90 degree
                      rotation to the pocket

    Connectors:
    ----------------------------------------------------------------------------
    pad_gap        - space between the connector pad and the charge island it is nearest to
    pad_width      - width (x-axis) of the connector pad
    pad_height     - height (y-axis) of the connector pad
    pad_cpw_shift  - shift the connector pad cpw line by this much away from qubit
    pad_cpw_extent - how long should the pad be - edge that is parallel to pocket
    cpw_width      - center trace width of the CPW line
    cpw_gap        - dielectric gap width of the CPW line
    cpw_extend     - depth the connector line extense into ground (past the pocket edge)
    pocket_extent  - How deep into the pocket should we penetrate with the cpw connector
                     (into the fround plane)
    pocket_rise    - How far up or downrelative to the center of the transmon should we
                     elevate the cpw connection point on the ground plane
    loc_W / H      - which 'quadrant' of the pocket the connector is set to, +/- 1 (check if diagram is correct)


    Sketch:
    ----------------------------------------------------------------------------

     -1
     ________________________________
-1  |______ ____           __________|          Y
    |      |____|         |____|     |          ^
    |        __________________      |          |
    |       |     island       |     |          |----->  X
    |       |__________________|     |
    |                 |              |
    |  pocket         x              |
    |        _________|________      |
    |       |                  |     |
    |       |__________________|     |
    |        ______                  |
    |_______|______|                 |
    |________________________________|   +1
                                +1
    '''

    _img = 'Metal_Transmon_Pocket1.png'

    def make(self):
        self.make_pocket()
        self.make_connectors()

#####MAKE SHAPELY POLYGONS########################################################################
    def make_pocket(self):
        '''
        Makes standard transmon in a pocket
        '''
        options = self.options

        # Pads- extracts relevant values from options dictionary
        pad_gap, inductor_width, pad_width, pad_height, pocket_width, pocket_height,\
            pos_x, pos_y = parse_options_user(self.design.params.variables, options, 'pad_gap, inductor_width, pad_width,\
                 pad_height, pocket_width, pocket_height, pos_x, pos_y')
        # then makes the shapely polygons
        pad = shapely_rectangle(pad_width, pad_height)
        pad_top = translate(pad, 0, +(pad_height+pad_gap)/2.)
        pad_bot = translate(pad, 0, -(pad_height+pad_gap)/2.)

        # the rectangle representing the josephson junction
        rect_jj = shapely_rectangle(inductor_width, pad_gap)
        rect_pk = shapely_rectangle(pocket_width, pocket_height)

        # adds the shapely polygons to this qubits object dictionary
        objects = dict(
            rect_jj=rect_jj,
            pad_top=pad_top,
            pad_bot=pad_bot,
            rect_pk=rect_pk,
        )

        #rotates and translates all the objects as requested. Uses package functions in 'draw_utility' for easy
        # rotation/translation
        objects = rotate_obj_dict(
            objects, _angle_Y2X[options['orientation']], origin=(0, 0))
        objects = translate_objs(objects, pos_x, pos_y)

        self.objects.update(objects)

        return objects

    def make_connectors(self):
        '''
        Makes standard transmon in a pocket
        '''
        for name, options_connector in self.options.connectors.items():
            ops = deepcopy(DEFAULT_OPTIONS['Metal_Transmon_Pocket.connectors'])
            ops.update(options_connector)
            options_connector.update(ops)
            self.make_connector(name, options_connector)

    def make_connector(self, name, options_connector):
        '''
        Makes individual connector

        Args:
        -------------
        name (str) : Name of the connector
        '''

        # Transmon options
        options = self.options  # for transmon
        pad_gap, _, pad_width, pad_height, pocket_width, _, pos_x, pos_y = \
            parse_options_user(self.design.params.variables, options, 'pad_gap, inductor_width, pad_width, pad_height,\
                pocket_width, pocket_height, pos_x, pos_y')

        # Connector options
        pad_gap, pad_cwidth, pad_cheight, pad_cpw_shift, cpw_width, pocket_extent,\
             pocket_rise, pad_cpw_extent, cpw_extend, cpw_gap = parse_options_user(self.design.params.variables,\
                 options_connector, 'pad_gap, pad_width, pad_height, pad_cpw_shift,\
                     cpw_width, pocket_extent, pocket_rise, pad_cpw_extent, cpw_extend, cpw_gap')

        connector_pad = shapely_rectangle(pad_cwidth, pad_cheight)
        connector_pad = translate(connector_pad, -pad_cwidth/2, pad_cheight/2)

        #print(pocket_width, pad_width, cpw_extend, pad_cpw_shift, cpw_width, pocket_rise)
        connector_wire_l = shapely.wkt.loads(f"""LINESTRING (\
                                            0 {pad_cpw_shift+cpw_width/2}, \
                                            {pad_cpw_extent}                           {pad_cpw_shift+cpw_width/2}, \
                                            {(pocket_width-pad_width)/2-pocket_extent} {pad_cpw_shift+cpw_width/2+pocket_rise}, \
                                            {(pocket_width-pad_width)/2+cpw_extend}    {pad_cpw_shift+cpw_width/2+pocket_rise}\
                                        )""")
        connector_wire = buffer(connector_wire_l, cpw_width/2)

        if 1:
            # draw a cutout for the ground plane
            _points = list(map(list, connector_wire_l.coords[-2:]))
            # extend the end of the connector by this much
            _points[-1][0] += cpw_gap
            subtract_grnd_connector = LineString(_points)
            subtract_grnd_connector = buffer(subtract_grnd_connector, cpw_width/2+cpw_gap)

        objects = dict(
            connector_pad=connector_pad,
            connector_wire=connector_wire,
            # connector_wire_l=connector_wire_l,
            subtract_grnd_connector=subtract_grnd_connector,
        )

        assert options_connector['loc_W'] in [-1, +1]
        assert options_connector['loc_H'] in [-1, +1]

        objects = scale_objs(
            objects, options_connector['loc_W'], options_connector['loc_H'], origin=(0, 0))
        objects = translate_objs(objects, options_connector['loc_W']*(pad_width)/2.,
                                 options_connector['loc_H']*(pad_height+pad_gap/2+pad_gap))
        objects = rotate_objs(
            objects, _angle_Y2X[options['orientation']], origin=(0, 0))
        objects = Dict(translate_objs(objects, pos_x, pos_y))

        # add to objects
        self.objects.connectors[name] = objects

        # add connectors to design tracker
        design = self.design
        if not design is None:
            points = Polygon(objects.connector_wire).coords_ext
            # debug: draw_objs([LineString(points)], kw=dict(lw=2,c='r'))
            design.connectors[self.name+'_'+name] = make_connector_props(\
                                points[2:2+2], options, vec_normal=points[2]-points[1])

        return objects


####MAKE HFSS COMPONENT#########################################################################
    def hfss_draw(self):
        '''
        Draw in HFSS.
        Makes a meshing recntalge for the the pocket as well.
        '''
        # custom shortcuts
        design = self.design
        name = self.name
        options = self.options
        options_hfss = self.options._hfss
        rect_options = options_hfss.rect_options
        _, oModeler = design.get_modeler() # pylint: disable=invalid-name
        oh = lambda x: parse_units_user(options_hfss[x]) # pylint: disable=invalid-name

        # Pocket: make mesh rectangle for pocket
        rect_msh = buffer(self.objects.rect_pk, oh('mesh_pocket'))
        # list of objects to draw in HFSS
        objs = [self.objects, dict(mesh=rect_msh)]

        # Pocket: Draw all pocket objects
        self.objects_hfss = Dict(draw_hfss.draw_objects_shapely(design.oModeler, objs,
                                                                self.name, pos_z=self.get_chip_elevation(), hfss_options=rect_options))
        hfss_objs = self.objects_hfss  # shortcut

        # Pocket: Subtract ground
        ground = design.get_ground_plane(options)
        oModeler.subtract(ground, [hfss_objs['rect_pk']])
        subtracts = [hfss_objs.connectors[xx]['subtract_grnd_connector'] for xx in self.objects.connectors]
        oModeler.subtract(ground, subtracts)

        if DEFAULT['do_PerfE']:
            oModeler.append_PerfE_assignment(name+'_pads' if DEFAULT['BC_individual'] else options_hfss['BC_name_pads'],
                                             [hfss_objs['pad_top'],
                                              hfss_objs['pad_bot']])

            for key in self.options.connectors:
                oModeler.append_PerfE_assignment(name+'_conn' if DEFAULT['BC_individual'] else options_hfss['BC_name_conn'],
                                                 [hfss_objs.connectors[key]['connector_pad'],
                                                  hfss_objs.connectors[key]['connector_wire']])

        # JJ line and Lumped RLC
        if 1:
            rect_jj = hfss_objs['rect_jj'] # pylint: disable=invalid-name # pyEPR.hfss.Rect
            axis = self.options.orientation.lower()
            rect_jj.make_rlc_boundary(axis, l=options_hfss['Lj'],
                                      c=options_hfss['Cj'], r=options_hfss['_Rj'],
                                      name='Lj_'+name)

            [start, end] = rect_jj.make_center_line(axis)

            poly_jj = oModeler.draw_polyline([start, end], closed=False,
                                             **{**rect_options, **dict(color=(128, 0, 128))})
            poly_jj = poly_jj.rename('JJ_'+name+'_')
            poly_jj.show_direction = True

        if DEFAULT._hfss.do_mesh:

            # Pocket
            rect_mesh = hfss_objs['mesh']
            rect_mesh.wireframe = True
            design.mesh_obj(
                rect_mesh, options_hfss['mesh_name'], **options_hfss['mesh_kw'])

            # JJ
            design.mesh_obj(
                hfss_objs['rect_jj'], options_hfss['mesh_name_jj'], **options_hfss['mesh_kw_jj'])

            # Pads
            rects = [hfss_objs[name_pad]
                     for name_pad in ['pad_top', 'pad_bot']]
            design.mesh_obj(
                rects, options_hfss['mesh_name_pad'], **options_hfss['mesh_kw_pad'])
            #print(f"rects={rects}, options_hfss['mesh_name_pad']={options_hfss['mesh_name_pad']}, options_hfss['mesh_kw_pad']={options_hfss['mesh_kw_pad']}")

            # Connectors
            if not(options_hfss['mesh_name_con'] is None):
                rects = []
                for key in self.options.connectors:
                    rects += [hfss_objs.connectors[key][name_pad]
                              for name_pad in ['connector_pad', 'connector_wire']]
                #print(f"rects={rects}, options_hfss['mesh_name_bon']={options_hfss['mesh_name_con']}, options_hfss['mesh_kw_pad']={options_hfss['mesh_kw_pad']}")
                design.mesh_obj(
                    rects, options_hfss['mesh_name_con'], **options_hfss['mesh_kw_con'])

        return hfss_objs
