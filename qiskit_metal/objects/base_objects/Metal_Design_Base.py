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
Base class for design type objects in Qiskit Metal.

This should be thought of as the 'package' level of the system. Aspects
such as gemoetries of your package cavity, 3D vs. planar or multiple chips.

Default use should be Metal_Design_Planar, which is a child of Metal_Design_Base.
Any alternative systems should be made as a child of Metal_Design_Base.

@date: 2019
@author: Zlatko K. Minev
Updated 2019/09/25 - Thomas McConkey
'''
# pylint: disable=invalid-name

import numpy as np
from shapely.geometry import LineString

from ...toolbox.parsing import parse_units_user, parse_value, parse_options_user
from ...toolbox.attribute_dictionary import Dict
from ...config import DEFAULT, DEFAULT_OPTIONS
from ...draw_functions import draw_objs
from ...backend.import_export import save_metal#, load_metal
from .Metal_Utility import is_metal_object



class Metal_Design_Base(): # pylint: disable=invalid-name
    '''
    Base class for design type objects in Qiskit Metal.
    All designs should be derived from this base class.

    Key properties:
    ----------------------
        objects (Dict) : Dict of all Metal_objects
        connectors (Dict) : Dict of all connectors associated with
                            the Metal_objects and custom connectors

    @date: 2019
    @author: Zlatko K. Minev
    '''
    __i_am_metal_design__ = True


#########INITIALIZATION##################################################
    def __init__(self,
                 objects = None,
                 connectors = None,
                 logger = None,
                 variables = None):

        self._objects = Dict() if objects is None else objects
        self._connectors =  Dict() if connectors is None else connectors
        self._variables = Dict() if variables is None else variables

        # handy in saving and keeping everyting referenced in one object
        self._DEFAULT = DEFAULT # Depricated, to be removed
        self._DEFAULT_OPTIONS = DEFAULT_OPTIONS

        if logger is None:
            from ... import logger
            self.logger = logger

#########PROPERTIES##################################################

    @property
    def objects(self):
        '''
        Returns Dict object that keeps track of all Metal objects in the design
        '''
        return self._objects

    @property
    def connectors(self):
        '''
        Return the Dict object that keeps track of all connectors in the design.
        '''
        return self._connectors

    @property
    def variables(self):
        '''
        Return the Dict object that keeps track of all variables in the design.
        '''
        return self._variables

#########COMMANDS##################################################
    def reset_all_connectors(self):
        '''
        Delete all connectors in the design.
        '''
        self.connectors.clear()
        return self.connectors

    def reset_all_objects(self):
        '''
        Resets the objects dictionary
        '''
        self._objects.clear()
        self.reset_all_connectors()
        return self._objects

    def reset_all_metal(self):
        '''
        Removes the metal device
        '''
        self.reset_all_objects()
        #self.reset_all_connectors()
        return self


    clear_all_objects = reset_all_objects

    def __getitem__(self, key):
        return getattr(self, key)

#########DRAWING##################################################
    def plot_connectors(self, ax=None):
        '''
        Plots all connectors on the active axes. Draws the 1D line that
        represents the "port" of a connector point. These are referenced for smart placement
         of Metal objects, such as when using functions like Metal_CPW_Connect.
        '''
        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()

        for name, conn in self.connectors.items():
            line = LineString(conn.points)

            draw_objs(line, ax=ax, kw=dict(lw=2,c='r'))

            ax.annotate(name, xy=conn.pos[:2], xytext=conn.pos +\
                        np.array(DEFAULT.annots.design_connectors_ofst),\
                        **DEFAULT.annots.design_connectors)

    def make_all_objects(self):
        """
        Remakes all objects with their current parameters. Easy way
        """
        #self.logger.debug('Design: Making all objects')
        for name, obj in self.objects.items(): # pylint: disable=unused-variable
            if is_metal_object(obj):
                #self.logger.debug(f' Making {name}')
                obj.make()

    def save_design(self, path):
        """Save the design as a pickled python object.
        Equivalent to
        ```python
            save_metal(r'C:/my-design.metal',design)
        ```

        Arguments:
            path {[string]} -- [path to save file]
        """
        save_metal(path, self)

    def get_option_values(self, options_dict, option_names):
        '''
        Parse a list of option names from options_dict.

        Adds units

        TODO: Remove this funciton and superseed with self.parse_value
        '''
        return parse_options_user(options_dict, option_names, self._variables)

    def parse_value(self, value):
        """Parse a value into user units.

        Example  converstions with a `design`:

        ..code-block python
            design.variables.cpw_width = '10um' # Example variable
            design.parse_value(Dict(
                string1 = '1m',
                string2 = '1mm',
                string3 = '1um',
                string4 = '1nm',
                variable1 = 'cpw_width',
                list1 = "['1m', '5um', 'cpw_width', -1, False, 'a string']",
                dict1 = "{'key1':'4e-6mm'}"
            ))

        Yields:

        ..code-block python
            {'string1': 1000.0,
            'string2': 1,
            'string3': 0.001,
            'string4': 1.0e-06,
            'variable1': 0.01,
            'list1': [1000.0, 0.005, 0.01, -1, False, 'a string'],
            'dict1': {'key1': 4e-06}}

        """
        return parse_value(value, self.variables)

    def add_connector(self, args):
        #TOOD:
        pass