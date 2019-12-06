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
from ...toolbox_metal.parsing import parse_value, parse_params
from ...config import DEFAULT, DEFAULT_OPTIONS
from ...draw.utils import render_to_mpl, make_connector
from ...toolbox_metal.import_export import save_metal
from .Metal_Utility import is_component


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


    def delete_all_connectors(self):
        '''
        Delete all connectors in the design.
        '''
        self.connectors.clear()
        return self.connectors

    def delete_all_components(self):
        '''
        Clears the components dictionary
        '''
        self._components.clear()
        self.delete_all_connectors()
        return self._components

    def __getitem__(self, key):
        return getattr(self, key)

    def make_all_components(self):
        """
        Remakes all components with their current parameters.
        """
        for name, obj in self.components.items():  # pylint: disable=unused-variable
            if is_component(obj):
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

    def parse_value(self, value):
        """
        Main parsing function.

        Parse a string, mappable (dict, Dict), iterrable (list, tuple) to account for
        units conversion, some basic arithmetic, and design variables.
        This is the main parsing function of Qiskit Metal.

        Handled Inputs:

            Strings:
                Strings of numbers, numbers with units; e.g., '1', '1nm', '1 um'
                    Converts to int or float.
                    Some basic arithmatic is possible, see below.
                Strings of variables 'variable1'.
                    Variable interpertation will use string method
                    isidentifier `'variable1'.isidentifier()
                Strings of

            Dictionaries:
                Returns ordered `Dict` with same key-value mappings, where the values have
                been subjected to parse_value.

            Itterables(list, tuple, ...):
                Returns same kind and calls itself `parse_value` on each elemnt.

            Numbers:
                Returns the number as is. Int to int, etc.


        Arithemetic:
            Some basic arithemetic can be handled as well, such as `'-2 * 1e5 nm'`
            will yield float(-0.2) when the default units are set to `mm`.

        Default units:
            User units can be set in the design. The design will set config.DEFAULT.units

        Examples:
            See the docstring for this module.
                >> ?qiskit_metal.toolbox_metal.parsing

        Arguments:
            value {[str]} -- string to parse
            variable_dict {[dict]} -- dict pointer of variables

        Return:
            Parse value: str, float, list, tuple, or ast eval
        """
        return parse_value(value, self.variables)

    def parse_params(self, params: dict, param_names: str):
        """
        Extra utility function that can call parse_value on individual options.
        Use self.parse_value to parse only some options from a params dictionary

        Arguments:
            params (dict) -- Input dict to pull form
            param_names (str) -- eg, 'x,y,z,cpw_width'
        """
        return parse_params(params, param_names, variable_dict=self.variables)

    def add_connector(self, name: str,  points: list, flip=False, chip='main'):
        """Add named connector to the design by creating a connector dicitoanry.

        Arguments:
            name {[str]} -- Name of connector

        Keyword Arguments:
            points {[list]} --List of two points (default: {None})
            ops {[dict]} -- Optionally add options (default: {None})
        """
        self.connectors[name] = make_connector(points, flip=flip, chip=chip)
