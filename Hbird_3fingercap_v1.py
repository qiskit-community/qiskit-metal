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
@date: 2020/04/28
@author: John Blair
'''
#  This a 3 finger planar metal capacitor design used on the chip Hummingbird V2
#  There is no CPW tee attached to this p# TODO create image of structure


# Imports required for drawing

from copy import deepcopy
from ... import draw
from ...toolbox_python.attr_dict import Dict
from ..._defaults import DEFAULT_OPTIONS
from ..base.qubit import BaseQubit
from .Metal_Capacitor import Metal_Capacitor

# pylint: disable=invalid-name

# Define variables for the capacitor geometry


DEFAULT_OPTIONS['Metal_Capacitor_Three_Finger'] = deepcopy(
    DEFAULT_OPTIONS['Metal_Capacitor'])
DEFAULT_OPTIONS['Metal_Capacitor_Three_Finger'].update(Dict(
    cpw_width=DEFAULT_OPTIONS.cpw.width,
    finger_length = '35um',
    pocket_buffer_width = '5um',
    pos_x='0um',
    pos_y='0um',
    orientation='0',  # 90 has capacitor oriented along the x axis 


# Define default options for the connectors


DEFAULT_OPTIONS['Metal_Capacitor_Three_Finger.connectors'] = Dict(
    cpw_width=DEFAULT_OPTIONS.cpw.width,
    cpw_gap=DEFAULT_OPTIONS.cpw.gap,
    cpw_lead_length='10um',  # how far into the ground to extend the CPW line from the coupling pads
    pocket_extent='5um',
    pocket_rise='65um',
    loc_W=+1,  # width location  only +-1
    loc_H=+1,  # height location only +-1
)


class Metal_Capacitor_Three_Finger(Metal_Capacitor): 
    '''
    Description:
    ----------------------------------------------------------------------------
    Create a three finger capacitor with a ground pocket cuttout.  The width of
    the fingers is determined by the CPW width.

    Connectors can be added using the `options_connectors`
    dicitonary. Each connectors has a name and a list of default
    properties.

    Options:
    ----------------------------------------------------------------------------
    Convention: Values (unless noted) are strings with units included,
                (e.g., '30um')

    Capacitor Metal Geometry and Ground Cuttout Pocket:
    ----------------------------------------------------------------------------
    cpw_width      - center trace width of the CPW lead line and cap fingers
    finger length  - length of each finger
    pocket_buffer_width - sets size of pocket in both x and y directions over cap dimmensions
       (could be changed so x and y border sizes are different but not typically used in designs)
       this is a negative shape that is cut out of the ground plane
    pos_x / pos_y   - where the center of the pocket should be located on chip
    orientation     - degree of qubit rotation

    Connectors:
    ----------------------------------------------------------------------------
    cpw_width      - center trace width of the CPW line
    cpw_gap        - dielectric gap width of the CPW line
    cpw_lead_length - length of additional cpw line beyond the pocket edge (part already has lead up to pocket edge
                      the length of which is equal to the pocket_buffer_width)
    loc_top / bot   - connector set to top of bottom of pocket cpw line, should be at end of lead 


    Sketch:  TODO
    ----------------------------------------------------------------------------

    '''

   #  TODO _img = 'Metal_Capacitor_Three_Finger.png'

   #Define structure functions

    def make(self):
        self.make_pocket()
        self.make_con_lines()

        #####MAKE SHAPELY POLYGONS########################################################################
    def make_pocket(self):
        '''
        Makes a three finger capacitor in a pocket
        '''

        # use self.p to access parsed values (string -> numbers)
        p = self.p

                
        # make the shapely polygons for the main cap structure
        pad     = draw.rectangle(p.cpw_width*5, p.cpw_width)
        pad_top = draw.translate(pad, 0,+(p.cpw_width*2+p.finger_length)/2) 
        pad_bot = draw.translate(pad, 0,-(p.cpw_width*2+p.finger_length)/2)
        finger  = draw.rectangle(p.cpw_width, p.finger_length)
        cent_finger = draw.translate(finger, 0,+(p.cpw_width)/2)  
        left_finger = draw.translate(finger, -(p.cpw_width*2),-(p.cpw_width)/2)
        right_finger = draw.translate(finger, +(p.cpw_width*2),-(p.cpw_width)/2)

        # make the shapely polygons for the built in leads in the pocket (length=pocket_buffer_width)
        cpw_temp_1 = draw.rectangle(p.cpw_width, p.pocket_buffer_width)
        cpw_top = draw.translate(cpw_temp_1, 0,+(p.cpw_width*4+p.finger_length)/2)
        cpw_bot = draw.translate(cpw_temp_1, 0,-(p.cpw_width*4+p.finger_length)/2)

        # make the shapely polygons for pocket ground plane cuttout
        pocket  = draw.rectangle(p.pocket_buffer_width*7, p.finger_length+5*p.pocket_buffer_width)

        # adds the shapely polygons to this qubits object dictionary
        objects = dict(
            pad_top=pad_top, 
            pad_bot=pad_bot,
            cent_finger=cent_finger,
            left_finger=left_finger,
            right_finger=right_finger,
            pocket=pocket,
            cpw_top=cpw_top,
            cpw_bot=cpw_bot,            
        )

        #rotates and translates all the objects as requested. Uses package functions in 'draw_utility' for easy
        # rotation/translation
        objects = draw.translate(objects, xoff=p.position_x, yoff=p.position_y)
        objects = draw.rotate(objects, p.orientation, origin=(p.position_x,p.position_y))

        self.p.update(objects)

        return objects


#####MAKE CONNECTORS ZLATKO (older)########################################################################
    def make_con_lines(self):
        '''
        Makes an individual connector
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

        # Metal_Capacitor_Three_Finger options
        options = self.options  # for capacititor
        cpw_width, finger_length, pocket_buffer_width,\
            pos_x, pos_y,orientation = self.design.get_option_values(options, 'cpw_width, finger_length,\
                 pocket_buffer_width, pos_x, pos_y, orientation')

        # Connector options
        # (not sure how the cpw_cwidth and cpw_cheight variable definitions work)
        cpw_cwidth, cpw_cheight, cpw_lead_length, loc_top, loc_bot,\
             cpw_gap = self.design.get_option_values(\
                 options_connector, 'cpw_width, cpw_gap, cpw_lead_length, loc_top, loc_bot')


        #  THIS IS WHERE I NEED HELP
        #  not sure if we need conditionals for whether connectors present on loc_top, loc_bot 
        #  (in some rare cases one side of the cap may be grounded)

        #  Make connector pads
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
            objects, orientation, origin=(0, 0))
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



       #####MAKE CONNECTORS THOMAS (newer)########################################################################

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
        self.design.add_connector(
            self.name+'_'+name, points[2:2+2], self.name, flip=False)  # TODO: chip
        # connectors[self.name+'_'+name] = make_connector(\
        # points[2:2+2], options, vec_normal=points[2]-points[1])