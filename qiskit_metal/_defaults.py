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

"""
File contains basic dicitonaries. File contains a class to contain the basic dictionaries.

Created 2019

@author: Zlatko K. Minev
"""

from copy import deepcopy

# logger is not set up for the current order of operations in qiskit_metal.__init__().
#from . import logger
#from .toolbox_python.utility_functions import log_error_easy

from .toolbox_python.attr_dict import Dict
################################################################################
# Default Paramters

class DefaultOptionsGeneric():
    """Encapsulate generic data used throughout qiskit metal classes.


    Arguments:
        object {[type]} -- [description]
    """

    default_generic = Dict(
        units='mm',
        chip='main',
        buffer_resolution=16,  # for shapely buffer
        buffer_mitre_limit=5.0,
    )


    def __init__(self,
                 generic: Dict = default_generic):
        #self.logger = logger

        # Do Not edit the class variable
        #self.cpw = deepcopy(cpw)
        self.generic = deepcopy(generic)

        # custom default options
        self.default_options = Dict()
        self.default_options['generic'] = self.generic

    # customize the key/value pairs
    def update_default_options(self,
                               cust_key: str = None,
                               cust_value: Dict = None):
        """[Allow instance of class to update the default_options]

        Keyword Arguments:
            cust_key {str} -- Type of component. (default: {None})
            cust_value {Dict} --  The key/value pairs to describe component. (default: {None})
        """

        assert(cust_key is not None), f'ERROR: Need a key, update_default_options has {cust_key}'
        self.default_options[cust_key] = cust_value
        
        '''
        if cust_key is None:
            #raise Exception(f'ERROR: Need a key, update_default_options has {cust_key}')
            #print(f'ERROR: Need a key, update_default_options has {cust_key}')
        else:
            self.default_options[cust_key] = cust_value
        '''
        


# Can't really use this until default_draw_substrate.color_plane is resolved.
class DefaultOptionsRenderer():
    """Encapsulate generic data used throughout qiskit metal classes for renderers.


    Arguments:
        object {[type]} -- [description]
    """

    '''
        This class is a skeleton and is expected to be updated when the renderer is updated. 
    '''


    # These are potential dicts that could be used for renderers.  
    
    default_bounding_box = Dict(draw_bounding_box=[
        [0, 0], [0, 0], ['0.890mm', '0.900mm']
    ],)

    default_draw_substrate = Dict(draw_substrate={
        'pos_xy': "['0um', '0um']",
        'size': "['8.5mm', '6.5mm', '-0.750mm']",
        'elevation': 0,
        'ground_plane': 'ground_plane',
        'substrate': 'substrate',
        'material': 'silicon',
        # 'color_plane': DEFAULT.colors.ground_main,      #this needs to change
        'transparency_plane': 0,
        'transparency_substrate': 0,
        'wireframe_substrate': False
    })

    '''
    DEFAULT_OPTIONS['draw_cpw_trace'] = {
        'func_draw': 'draw_cpw_trace',
        'chip': 'main',
        'name': 'CPW1',         # Name of the line
        'trace_center_width': DEFAULT_OPTIONS.cpw.width,         # Center trace width
        'trace_center_gap': DEFAULT_OPTIONS.cpw.gap,
        'trace_mesh_gap': DEFAULT_OPTIONS.cpw.mesh_width,          # For mesh rectangle
        'fillet': DEFAULT_OPTIONS.cpw.fillet,        # Fillt
        # name of ground plane to subtract from, maybe make also automatic
        'ground_plane': 'ground_plane',
        'do_only_lines': 'False',        # only draw the lines
        'do_mesh':  DEFAULT._hfss.do_mesh,  # Draw trace for meshing
        'do_subtract_ground': 'True',         # subtract from ground plane
        # keep_originals when perfomring subtraction
        'do_sub_keep_original': 'False',
        'do_assign_perfE':  True,
        'BC_individual':  False,
        'BC_name': 'CPW_center_traces',
        'category': 'cpw',
        'do_add_connectors':  True,
        'units': 'mm',           # default units
        # dictionary 100,120,90
        'poly_default_options': {'transparency': 0.95, 'color': DEFAULT['col_in_cond']},
        'mesh_name': 'cpw',
        'mesh_kw': Dict(MaxLength='0.1mm')
    }


    '''
    def __init__(self,
                 draw_substrate: Dict = default_draw_substrate,
                 bounding_box: Dict = default_bounding_box):
        #self.logger = logger

        # Do Not edit the class variable
        self.draw_substrate = deepcopy(draw_substrate)
        self.bounding_box = deepcopy(bounding_box)

        # custom default options
        self.default_options = {}
        self.default_options.update(self.draw_substrate)
        self.default_options.update(self.bounding_box)

    # customize the key/value pairs
    def update_default_options(self,
                               cust_key: str = None,
                               cust_value: Dict = None):
        """[Allow instance of class to update the default_options]

        Keyword Arguments:
            cust_key {str} -- Type of component. (default: {None})
            cust_value {Dict} --  The key/value pairs to describe component. (default: {None})
        """
        assert(cust_key is not None), f'ERROR: Need a key, update_default_options has {cust_key}'
        self.default_options[cust_key] = cust_value
        
