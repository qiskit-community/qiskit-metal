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
Base class for design type components in Qiskit Metal.

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

from ... import Dict
from ...toolbox_metal.parsing import parse_value, parse_options
from ...config import DEFAULT, DEFAULT_OPTIONS
from ...draw.functions import draw_objs, make_connector
from ...toolbox_metal.import_export import save_metal
from .Metal_Utility import is_metal_object


class Metal_Design_Base():  # pylint: disable=invalid-name
    '''
    Base class for design type components in Qiskit Metal.
    All designs should be derived from this base class.

    Key properties:
    ----------------------
        components (Dict) : Dict of all Metal_objects
        connectors (Dict) : Dict of all connectors associated with
                            the Metal_objects and custom connectors

    @date: 2019
    @author: Zlatko K. Minev
    '''
    __i_am_metal_design__ = True


#########INITIALIZATION##################################################


    def __init__(self,
                 components=None,
                 connectors=None,
                 logger=None,
                 variables=None):

        self._components = Dict() if components is None else components
        self._connectors = Dict() if connectors is None else connectors
        self._variables = Dict() if variables is None else variables

        # handy in saving and keeping everyting referenced in one object
        self._defaults = DEFAULT  # Depricated, to be removed
        self._default_options = DEFAULT_OPTIONS

        if logger is None:
            from ... import logger
            self.logger = logger

#########PROPERTIES##################################################

    @property
    def components(self):
        '''
        Returns Dict object that keeps track of all Metal components in the design
        '''
        return self._components

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

    @property
    def defaults(self):
        '''
        Return DEFAULT dictionary, which contains some key Metal DEFAULT params used
        in various Metal functions. These include default units, etc.

        Think of these as global defaults.
        '''
        return self._defaults

    @property
    def default_options(self):
        '''
        Return handle to the dicitonary of default options used in creating Metal
        component, and in calling other drawing and key functions.
        '''
        return self._default_options


#########COMMANDS##################################################


    def reset_all_connectors(self):
        '''
        Delete all connectors in the design.
        '''
        self.connectors.clear()
        return self.connectors

    def reset_all_objects(self):
        '''
        Resets the components dictionary
        '''
        self._components.clear()
        self.reset_all_connectors()
        return self._components

    def reset_all_metal(self):
        '''
        Removes the metal device
        '''
        self.reset_all_objects()
        # self.reset_all_connectors()
        return self

    clear_all_objects = reset_all_objects

    def __getitem__(self, key):
        return getattr(self, key)

#########DRAWING##################################################
    def plot_connectors(self, ax=None):
        '''
        Plots all connectors on the active axes. Draws the 1D line that
        represents the "port" of a connector point. These are referenced for smart placement
         of Metal components, such as when using functions like Metal_CPW_Connect.
        '''
        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()

        for name, conn in self.connectors.items():
            line = LineString(conn.points)

            draw_objs(line, ax=ax, kw=dict(lw=2, c='r'))

            ax.annotate(name, xy=conn.middle[:2], xytext=conn.middle +
                        np.array(DEFAULT.annots.design_connectors_ofst),
                        **DEFAULT.annots.design_connectors)

    def make_all_objects(self):
        """
        Remakes all components with their current parameters. Easy way
        """
        #self.logger.debug('Design: Making all components')
        for name, obj in self.components.items():  # pylint: disable=unused-variable
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

    def add_connector(self, name: str,  points: list, flip=False, chip='main'):
        """Add named connector to the design by creating a connector dicitoanry.

        Arguments:
            name {[str]} -- Name of connector

        Keyword Arguments:
            points {[list]} --List of two points (default: {None})
            ops {[dict]} -- Optionally add options (default: {None})
        """
        self.connectors[name] = make_connector(points, flip=flip, chip=chip)
