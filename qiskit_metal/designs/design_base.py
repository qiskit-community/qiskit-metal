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
Module containing all Qiskit Metal designs.

To create a basic UML diagram
>> pyreverse -o png -p desin_base design_base.py -A  -S

@date: 2019
@author: Zlatko Minev, Thomas McConeky, ... (IBM)
"""
import numpy as np

from .. import Dict, draw, logger
from ..config import DEFAULT, DEFAULT_OPTIONS
from ..toolbox_metal.import_export import load_metal, save_metal
from ..toolbox_metal.parsing import parse_value, parse_params
from ..components import is_component

__all__ = ['is_design', 'DesignBase']

def is_design(obj):
    """Check if an object is a Metal Design, i.e., an instance of
     `DesignBase`.

    The problem is that the `isinstance` built-in method fails
    when this module is reloaded.

    Arguments:
        obj {[object]} -- Test this object

    Returns:
        [bool] -- True if is a Metal design
    """
    if isinstance(obj, Dict):
        return False

    return hasattr(obj, '__i_am_design__')


class DesignBase():
    """
    DesignBase is the base class for Qiskit Metal Designs.
    A design is the most top-level object in all of Qiskit Metal.
    """

    # Dummy private attribute used to check if an instanciated object is
    # indeed a DesignBase class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_design` to check.
    __i_am_design__ = True

    def __init__(self):
        self._components = Dict()
        self._connectors = Dict()
        self._variables = Dict()

        self._defaults = DEFAULT  # Depricated, to be removed
        self._default_options = DEFAULT_OPTIONS

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


#########Proxy properties##################################################

    def get_chip_size(self, chip_name='main'):
        raise NotImplementedError()

    def get_chip_z(self, chip_name='main'):
        raise NotImplementedError()

#########General methods###################################################

    def clear_all_connectors(self):
        '''
        Clear all connectors in the design.
        '''
        self.connectors.clear()
        return self.connectors

    def clear_all_components(self):
        '''
        Clear all components in the design dictionary.
        Also clears all connectors.
        '''
        self._components.clear()
        self.clear_all_connectors()
        return self._components

    def make_all_components(self):
        """
        Remakes all components with their current parameters.
        """
        for name, obj in self.components.items():  # pylint: disable=unused-variable
            if is_component(obj):
                obj.make()

#########I/O###############################################################

    @classmethod
    def load_design(cls, path):
        """Load a Metal design from a saved Metal file.
        (Class method)

        Arguments:
            path {str} -- Path to saved Metal design.

        Returns:
            Loaded metal design.
            Will also update default dicitonaries.
        """
        print("Beta feature. Not guaranteed to be fully implemented. ")
        return load_metal(path)

    def save_design(self, path):
        """Save the metal design to a Metal file.

        Arguments:
            path {str} -- Path to save the design to.
        """
        print("Beta feature. Not guaranteed to be fully implemented. ")
        return save_metal(self, path)

#########Creating Components###############################################################

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


####################################################################################
###
# Connector
# TODO: Decide how to handle this.
#   Should this be a class?
#   Should we keep function here or just move into design?

def make_connector(points: list, flip=False, chip='main'):
    """
    Works in user units.

    Arguments:
        points {[list of coordinates]} -- Two points that define the connector

    Keyword Arguments:
        flip {bool} -- Flip the normal or not  (default: {False})
        chip {str} -- Name of the chip the connector sits on (default: {'main'})

    Returns:
        [type] -- [description]
    """
    assert len(points) == 2

    # Get the direction vector, the unit direction vec, and the normal vector
    vec_dist, vec_dist_unit, vec_normal = draw.vec_unit_norm(points)

    if flip:
        vec_normal = -vec_normal

    return Dict(
        points=points,
        middle=np.sum(points, axis=0)/2.,
        normal=vec_normal,
        tangent=vec_dist_unit,
        width=np.linalg.norm(vec_dist),
        chip=chip
    )
