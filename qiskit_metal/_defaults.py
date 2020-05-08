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


# When rest of metal code stops using DEFAULT_OPTIONS, delete this dict.
# The Dict has moved to DefaultOptionsGeneric
DEFAULT_OPTIONS = Dict(
    cpw=Dict(
        width='10um',
        gap='6um',
        mesh_width='6um',
        fillet='90um',
    )
)

r"""
DEFAULT_OPTIONS:
------------------------
    Dictionary of the needed options for all functions defined in this module.
    Each options should also have a default value.

    This dictionary pointer should not be overwritten. Rather, update the dictionary values.
"""

# When rest of metal code stops using DEFAULT, delete this dict.
# The Dict has moved to DefaultOptionsGeneric
DEFAULT = Dict(
    units='mm',
    chip='main',
    buffer_resolution=16,  # for shapely buffer
    buffer_mitre_limit=5.0,
)

r"""
Default paramters for many basic functions:
------------------------

:chip:           Default name of chip to draw on.

.. sectionauthor:: Zlatko K Minev <zlatko.minev@ibm.com>
"""


class DefaultOptionsGeneric():
    """Encapsulate generic data used throughout qiskit metal classes.


    Arguments:
        object {[type]} -- [description]
    """
    # Class Variable-
    # Shared by all instances of the class.
    # Defined outside of all methods.
    # If user selects reset, need to keep track of defaults.

    default_generic = Dict(
        units='mm',
        chip='main',
        buffer_resolution=16,  # for shapely buffer
        buffer_mitre_limit=5.0,
    )

    default_cpw = Dict(
        width='10um',
        gap='6um',
        mesh_width='6um',
        fillet='90um',
    )

    # Instance Variables
    # Variables are owned by instances of the class.
    # For each object and instance of the class.
    # Instance variables are defined within methods.

    def __init__(self,
                 cpw: Dict = default_cpw,
                 generic: Dict = default_generic):
        #self.logger = logger

        # Do Not edit the class variable
        self.cpw = deepcopy(cpw)
        self.generic = deepcopy(generic)

        # custom default options
        self.default_options = Dict(cpw=Dict(self.cpw))
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

        if cust_key is None:
            print(f'ERROR: Need a key, update_default_options has {cust_key}')
            # log_error_easy(self.logger,
            # post_text=f'Need a key, update_default_option has {cust_key}')
        else:
            self.default_options[cust_key] = cust_value


### Can't really use this until default_draw_substrate.color_plane is resolved. 
class DefaultOptionsRenderer():
    """Encapsulate generic data used throughout qiskit metal classes for renderers.


    Arguments:
        object {[type]} -- [description]
    """

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

        if cust_key is None:
            print(f'ERROR: Need a key, update_default_options has {cust_key}')
            # log_error_easy(self.logger,
            # post_text=f'Need a key, update_default_option has {cust_key}')
        else:
            self.default_options[cust_key] = cust_value
