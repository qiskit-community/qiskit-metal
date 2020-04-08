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
converted to v0.2: Thomas McConkey 2020-03-24


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

from copy import deepcopy
from ... import draw
from ...toolbox_python.attr_dict import Dict
from ..._defaults import DEFAULT_OPTIONS
from ..base.qubit import BaseQubit


DEFAULT_OPTIONS['TransmonPocket.con_lines'] = deepcopy(
    DEFAULT_OPTIONS['qubit.con_lines'])
DEFAULT_OPTIONS['TransmonPocket.con_lines'].update(Dict(
    pad_gap='15um',
    pad_width='125um',
    pad_height='30um',
    pad_cpw_shift='5um',
    pad_cpw_extent='25um',
    cpw_width=DEFAULT_OPTIONS.cpw.width,
    cpw_gap=DEFAULT_OPTIONS.cpw.gap,
    cpw_extend='100um',  # how far into the ground to extend the CPW line from the coupling pads
    pocket_extent='5um',
    pocket_rise='65um',
    loc_W=+1,  # width location  only +-1
    loc_H=+1,  # height location only +-1
))

DEFAULT_OPTIONS['TransmonPocket'] = deepcopy(
    DEFAULT_OPTIONS['qubit'])
DEFAULT_OPTIONS['TransmonPocket'].update(Dict(
    pos_x='0um',
    pos_y='0um',
    pad_gap='30um',
    inductor_width='20um',
    pad_width='455um',
    pad_height='90um',
    pocket_width='650um',
    pocket_height='650um',
    # 90 has dipole aligned along the +X axis,
    # while 0 has dipole aligned along the +Y axis
    orientation='0',
))


class TransmonPocket(BaseQubit):
    '''
    Description:
    ----------------------------------------------------------------------------
    Create a standard pocket transmon qubit for a ground plane,
    with two pads connectored by a junction (see drawing below).

    Connector lines can be added using the `options_con_lines`
    dicitonary. Each connector line has a name and a list of default
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
                      (if in doubt, make the same as pad_gap). Really just for simulating
                      in HFSS / other EM software
    pad_width       - the width (x-axis) of the charge island pads
    pad_height      - the size (y-axis) of the charge island pads
    pocket_width    - size of the pocket (cut out in ground) along x-axis
    pocket_height   - size of the pocket (cut out in ground) along y-axis
    orientation     - degree of qubit rotation

    Connector lines:
    ----------------------------------------------------------------------------
    pad_gap        - space between the connector pad and the charge island it is
                     nearest to
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
    loc_W / H      - which 'quadrant' of the pocket the connector is set to, +/- 1 (check
                     if diagram is correct)


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

    _img = 'transmon_pocket1.png'

    def make(self):
        """
        Create the geometry from the parsed options.
        """
        self.make_pocket()
        self.make_con_lines()

#####MAKE SHAPELY POLYGONS########################################################################
    def make_pocket(self):
        '''Makes standard transmon in a pocket.'''

        # Extract relevant numerical values from options dictionary (parse strings)
        pad_gap, inductor_width, pad_width, pad_height, pocket_width, pocket_height,\
            pos_x, pos_y, orientation = self.design.parse_options(
                self.options, 'pad_gap, inductor_width, pad_width, pad_height, '\
                'pocket_width, pocket_height, pos_x, pos_y, orientation')

        # make the pads as rectangles (shapely polygons)
        pad = draw.rectangle(pad_width, pad_height)
        pad_top = draw.translate(pad, 0, +(pad_height+pad_gap)/2.)
        pad_bot = draw.translate(pad, 0, -(pad_height+pad_gap)/2.)

        # the draw.rectangle representing the josephson junction
        rect_jj = draw.rectangle(inductor_width, pad_gap)
        rect_pk = draw.rectangle(pocket_width, pocket_height)

        # Rotate and translate all elements as needed.
        # Done with utility functions in Metal 'draw_utility' for easy rotation/translation
        # NOTE: Should modify so rotate/translate accepts elements, would allow for
        # smoother implementation.
        polys = [rect_jj, pad_top, pad_bot, rect_pk]
        polys = draw.rotate(polys, orientation, origin=(0, 0))
        polys = draw.translate(polys, pos_x, pos_y)
        [rect_jj, pad_top, pad_bot, rect_pk] = polys

        # Use the geometry to create Metal elements
        self.add_elements('poly', dict(pad_top=pad_top, pad_bot=pad_bot))
        self.add_elements('poly', dict(rect_pk=rect_pk), subtract=True)
        self.add_elements('poly', dict(rect_jj=rect_jj), helper=True)


    def make_con_lines(self):
        '''
        Makes standard transmon in a pocket
        '''
        for name, options_con_lines in self.options.con_lines.items():
            ops = deepcopy(DEFAULT_OPTIONS['TransmonPocket.con_lines'])
            ops.update(options_con_lines)
            options_con_lines.update(ops)
            self.make_con_line(name, options_con_lines)

    
    def make_con_line(self, name, options_con_line):
        '''
        Makes individual connector

        Args:
        -------------
        name (str) : Name of the connector
        '''

        # Transmon options
        options = self.options  # for transmon
        pad_gap, _, pad_width, pad_height, pocket_width, _, pos_x, pos_y,orientation = \
            self.design.parse_options(options, 'pad_gap, inductor_width, pad_width, pad_height,\
                pocket_width, pocket_height, pos_x, pos_y ,orientation')

        # Connector options
        pad_gap, pad_cwidth, pad_cheight, pad_cpw_shift, cpw_width, pocket_extent,\
             pocket_rise, pad_cpw_extent, cpw_extend, cpw_gap = self.design.parse_options(\
                 options_con_line, 'pad_gap, pad_width, pad_height, pad_cpw_shift,\
                     cpw_width, pocket_extent, pocket_rise, pad_cpw_extent, cpw_extend, cpw_gap')

        connector_pad = draw.rectangle(pad_cwidth, pad_cheight)
        connector_pad = draw.translate(connector_pad, -pad_cwidth/2, pad_cheight/2)

        #print(pocket_width, pad_width, cpw_extend, pad_cpw_shift, cpw_width, pocket_rise)
        connector_wire_path = draw.wkt.loads(f"""LINESTRING (\
                                            0 {pad_cpw_shift+cpw_width/2}, \
                                            {pad_cpw_extent}                           {pad_cpw_shift+cpw_width/2}, \
                                            {(pocket_width-pad_width)/2-pocket_extent} {pad_cpw_shift+cpw_width/2+pocket_rise}, \
                                            {(pocket_width-pad_width)/2+cpw_extend}    {pad_cpw_shift+cpw_width/2+pocket_rise}\
                                        )""")
        connector_wire_CON = draw.buffer(connector_wire_path, cpw_width/2)

        #if 1:   Shouldn't need anymore since cpw stored as linestring
            # draw a cutout for the ground plane
            #_points = list(map(list, connector_wire_path.coords[-2:]))
            # extend the end of the connector by this much
            #_points[-1][0] += cpw_gap
            #subtract_grnd_connector = draw.LineString(_points)
            #subtract_grnd_connector = draw.buffer(subtract_grnd_connector, cpw_width/2+cpw_gap)

        objects = [connector_pad, connector_wire_CON, connector_wire_path]

        assert options_con_line['loc_W'] in [-1, +1]
        assert options_con_line['loc_H'] in [-1, +1]

        objects = draw.scale(
            objects, options_con_line['loc_W'], options_con_line['loc_H'], origin=(0, 0))
        objects = draw.translate(objects, options_con_line['loc_W']*(pad_width)/2.,
                                 options_con_line['loc_H']*(pad_height+pad_gap/2+pad_gap))
        objects = draw.rotate(
            objects, orientation, origin=(0, 0))
        objects = Dict(draw.translate(objects, pos_x, pos_y))

        [connector_pad, connector_wire_CON, connector_wire_path] = objects

        self.add_elements('poly', dict(connector_pad=connector_pad))
        self.add_elements('path', dict(connector_wire_path=connector_wire_path), width=cpw_width)
        self.add_elements('path', dict(connector_wire_etch=connector_wire_path), 
            width = cpw_width + 2*cpw_gap, subtract=True)


        # add to objects
        #self.components.connectors[name] = objects

        # add connectors to design tracker
        points = draw.get_poly_pts(objects.connector_wire_CON)
        self.design.add_connector(self.name+'_'+name, points[2:2+2], flip=False) #TODO: chip
        #connectors[self.name+'_'+name] = make_connector(\
        # points[2:2+2], options, vec_normal=points[2]-points[1])