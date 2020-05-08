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
#from ..._defaults import DEFAULT_OPTIONS
from ..base.qubit import BaseQubit


# DEFAULT_OPTIONS['TransmonPocket.con_lines'] = deepcopy(
#     DEFAULT_OPTIONS['qubit.con_lines'])
# DEFAULT_OPTIONS['TransmonPocket.con_lines'].update(Dict(
#     pad_gap='15um',
#     pad_width='125um',
#     pad_height='30um',
#     pad_cpw_shift='5um',
#     pad_cpw_extent='25um',
#     cpw_width=DEFAULT_OPTIONS.cpw.width,
#     cpw_gap=DEFAULT_OPTIONS.cpw.gap,
#     cpw_extend='100um',  # how far into the ground to extend the CPW line from the coupling pads
#     pocket_extent='5um',
#     pocket_rise='65um',
#     loc_W='+1',  # width location  only +-1
#     loc_H='+1',  # height location only +-1
# ))

# DEFAULT_OPTIONS['TransmonPocket'] = deepcopy(
#     DEFAULT_OPTIONS['qubit'])
# DEFAULT_OPTIONS['TransmonPocket'].update(Dict(
#     pos_x='0um',
#     pos_y='0um',
#     pad_gap='30um',
#     inductor_width='20um',
#     pad_width='455um',
#     pad_height='90um',
#     pocket_width='650um',
#     pocket_height='650um',
#     # 90 has dipole aligned along the +X axis,
#     # while 0 has dipole aligned along the +Y axis
#     orientation='0',
# ))


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

    default_options = Dict(
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
        con_lines = Dict(
            pad_gap='15um',
            pad_width='125um',
            pad_height='30um',
            pad_cpw_shift='5um',
            pad_cpw_extent='25um',
            cpw_width='10um',
            cpw_gap='6um',
            cpw_extend='100um',  # how far into the ground to extend the CPW line from the coupling pads
            pocket_extent='5um',
            pocket_rise='65um',
            loc_W='+1',  # width location  only +-1
            loc_H='+1',  # height location only +-1
        )
    )



    def make(self):
        """
        Create the geometry from the parsed options.
        """
        self.make_pocket()
        self.make_con_lines()

#####MAKE SHAPELY POLYGONS########################################################################
    def make_pocket(self):
        '''Makes standard transmon in a pocket.'''

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p

        # since we will reuse these options, parse them once and define them as varaibles
        pad_width = p.pad_width
        pad_height = p.pad_height
        pad_gap = p.pad_gap

        # make the pads as rectangles (shapely polygons)
        pad = draw.rectangle(pad_width, pad_height)
        pad_top = draw.translate(pad, 0, +(pad_height+pad_gap)/2.)
        pad_bot = draw.translate(pad, 0, -(pad_height+pad_gap)/2.)

        # the draw.rectangle representing the josephson junction
        rect_jj = draw.rectangle(p.inductor_width, pad_gap)
        rect_pk = draw.rectangle(p.pocket_width, p.pocket_height)

        # Rotate and translate all elements as needed.
        # Done with utility functions in Metal 'draw_utility' for easy rotation/translation
        # NOTE: Should modify so rotate/translate accepts elements, would allow for
        # smoother implementation.
        polys = [rect_jj, pad_top, pad_bot, rect_pk]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
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
            #Isn't this already being handled in the qubit base class?
            ops = deepcopy(
                self.design.template_options[self.unique_dict_key]['con_lines'])
            ops.update(options_con_lines)
            options_con_lines.update(ops)
            # make the connector
            self.make_con_line(name)

    def make_con_line(self, name:str):
        '''
        Makes individual connector

        Args:
        -------------
            name (str) : Name of the connector
        '''

        # self.p allows us to directly access parsed values (string -> numbers) form the user option
        p = self.p
        pc = self.p.con_lines[name] # parser on connector options

        # define commonly used variables once
        cpw_width = pc.cpw_width
        cpw_extend = pc.cpw_extend
        pad_width = pc.pad_width
        pad_height = pc.pad_height
        pad_cpw_shift = pc.pad_cpw_shift
        pad_cpw_extent = pc.pad_cpw_extent
        pocket_rise = pc.pocket_rise
        pocket_extent = pc.pocket_extent

        ### Define the geometry
        # Connector pad
        connector_pad = draw.rectangle(pad_width, pad_height, -pad_width/2, pad_height/2)
        # Connector CPW wire
        connector_wire_path = draw.wkt.loads(f"""LINESTRING (\
            0 {pad_cpw_shift+cpw_width/2}, \
            {pc.pad_cpw_extent}                           {pad_cpw_shift+cpw_width/2}, \
            {(p.pocket_width-p.pad_width)/2-pocket_extent} {pad_cpw_shift+cpw_width/2+pocket_rise}, \
            {(p.pocket_width-p.pad_width)/2+cpw_extend}    {pad_cpw_shift+cpw_width/2+pocket_rise}\
                                        )""")
        # for connector cludge
        connector_wire_CON = draw.buffer(connector_wire_path, cpw_width/2.) # helper for the moment

        # Position the connector, rot and tranlate
        loc_W, loc_H = float(pc.loc_W), float(pc.loc_H)
        if float(loc_W) not in [-1., +1.] or float(loc_H) not in [-1., +1.]:
            self.logger.info('Warning: Did you mean to define a transmon wubit with loc_W and'\
                ' loc_H that are not +1 or -1?? Are you sure you want to do this?')
        objects = [connector_pad, connector_wire_path, connector_wire_CON]
        objects = draw.scale(objects, loc_W, loc_H, origin=(0, 0))
        objects = draw.translate(objects, loc_W*(p.pad_width)/2.,
                                 loc_H*(p.pad_height+p.pad_gap/2+p.pad_gap))
        objects = draw.rotate_position(objects, p.orientation, [p.pos_x, p.pos_y])
        [connector_pad, connector_wire_path, connector_wire_CON] = objects

        self.add_elements('poly', {f'{name}_connector_pad':connector_pad})
        self.add_elements('path', {f'{name}_wire':connector_wire_path}, width=cpw_width)
        self.add_elements('path', {f'{name}_wire_sub':connector_wire_path},
                          width=cpw_width + 2*pc.cpw_gap, subtract=True)

        # add connectors to design tracker
        points = draw.get_poly_pts(connector_wire_CON)
        self.design.add_connector(name, points[2:2+2], self.name, flip=False)  # TODO: chip
 
