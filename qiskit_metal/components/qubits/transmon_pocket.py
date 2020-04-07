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
from ... import draw_utility, draw
from ...toolbox_python.attr_dict import Dict
from ..._defaults import DEFAULT_OPTIONS, DEFAULT
from ...elements.base import ElementTables
from ..base.qubit import BaseQubit

#from ... import DEFAULT, DEFAULT_OPTIONS, Dict, draw
#from ...renderers.renderer_ansys import draw_ansys
#from ...renderers.renderer_ansys.parse import to_ansys_units
#from .Metal_Qubit import Metal_Qubit

#NOTE:FIX UP THE IMPORTS
#NOTE:at what level to have the renderer options pulled in? Via base component? Should it check flags
#to see what options to include/ignore? (eg. junction inductance shouldn't be an option for CPW)
#or wait until point of element creation?


DEFAULT_OPTIONS['transmon_pocket.con_lines'] = Dict(
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
)

DEFAULT_OPTIONS['transmon_pocket'] = deepcopy(
    DEFAULT_OPTIONS['qubit'])
DEFAULT_OPTIONS['transmon_pocket'].update(Dict(
    pos_x='0um',
    pos_y='0um',
    pad_gap='30um',
    inductor_width='20um',
    pad_width='455um',
    pad_height='90um',
    pocket_width='650um',
    pocket_height='650um',
    orientation='0',  # 90 has dipole aligned along the +X axis, while 0 has dipole aligned along the +Y axis

))


class TransmonPocket(BaseQubit): # pylint: disable=invalid-name
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
                      (if in doubt, make the same as pad_gap). Really just for simulating in HFSS / other EM software
    pad_width       - the width (x-axis) of the charge island pads
    pad_height      - the size (y-axis) of the charge island pads
    pocket_width    - size of the pocket (cut out in ground) along x-axis
    pocket_height   - size of the pocket (cut out in ground) along y-axis
    orientation     - degree of qubit rotation

    Connector lines:
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

    _img = 'transmon_pocket1.png'

    def make(self):
        self.make_pocket()
        self.make_con_lines()

#####MAKE SHAPELY POLYGONS########################################################################
    def make_pocket(self):
        '''
        Makes standard transmon in a pocket
        '''
        options = self.options

        # Pads- extracts relevant values from options dictionary
        pad_gap, inductor_width, pad_width, pad_height, pocket_width, pocket_height,\
            pos_x, pos_y,orientation = self.design.get_option_values(options, 'pad_gap, \
                    inductor_width, pad_width, pad_height, pocket_width, pocket_height, \
                    pos_x, pos_y, orientation')
        # then makes the shapely polygons
        pad = draw.rectangle(pad_width, pad_height)
        pad_top = draw.translate(pad, 0, +(pad_height+pad_gap)/2.)
        pad_bot = draw.translate(pad, 0, -(pad_height+pad_gap)/2.)

        # the draw.rectangle representing the josephson junction
        rect_jj = draw.rectangle(inductor_width, pad_gap)
        rect_pk = draw.rectangle(pocket_width, pocket_height)


        #rotates and translates all the objects as requested. Uses package functions
        # in 'draw_utility' for easy rotation/translation
        #NOTE: Should modify so rotate/translate accepts elements, would allow for smoother
        #implementation.

        '''objects = dict(
            rect_jj=rect_jj,
            pad_top=pad_top,
            pad_bot=pad_bot,
            rect_pk=rect_pk,
        )'''

        [rect_jj,pad_top,pad_bot,rect_pk] = draw.rotate(
            [rect_jj,pad_top,pad_bot,rect_pk],orientation, origin=(0, 0))
        [rect_jj,pad_top,pad_bot,rect_pk] = draw.translate(
            [rect_jj,pad_top,pad_bot,rect_pk], pos_x, pos_y)

        #at this point each shapely should be 'turned into' an element, 


        '''
        for shape_names in objects:
            self.elements[shape_names] = element_handler(self.name, shape_names,objects[shape_names],\
                RENDER_OPTIONS)
            
        '''   
            
           #self.elements[names] = Dict(
           #     name = names,
           #     shape = objects[names],
           #     #THE RELEVANT OPTIONS GO HERE, no geometry, as that is in 'shape', but renderer
           #     #related stuff
           # )


        #self.components.update(objects) v0.1 method

        return objects