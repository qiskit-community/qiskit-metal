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
This is the main module that defines what a component is in Qiskit Metal.
See the docstring of BaseComponent
    >> ?BaseComponent

@author: Zlatko Minev, Thomas McConekey, ... (IBM)
@date: 2019
"""

from ...toolbox_python.attr_dict import Dict
# from ..elements.base import
from ...designs import is_design


__all__ = ['BaseComponent']


### NOT YET IN USE
from logging import Logger
class NameInterface():

    def __init__(self, name:str, logger:Logger):
        """Interface class for named objects.
        Objects can only be renamed by the method rename.
        The user can only acces the name readonly property.

        Arguments:
            name {str} -- Name to create the object with
            logger {Logger} -- Logger for logging errors
        """

        self.logger = logger

        if not self._validate_name(name):
            # failed validation
            self._validate_name_failed(name)

        self._name = name

    @property
    def name(self):
        return self._name

    @staticmethod
    def _validate_name(name:str):
        """Test if the name is a valid name
        Typically: isidentifier

        Arguments:
            name {str} -- Name of object

        Returns:
            bool
        """
        return name.isidentifier()

    def _validate_name_failed(self, name:str):
        """Handle the case when the name is not valid

        Arguments:
            name {str} -- name that failed

        Raises:
            NameError: [description]
        """
        err= 'The name {name} is not a valid name.'
        self.logger.error(err)
        raise NameError(err)

    def rename(self, new_name:str):
        """Rename the object. Changes the value of self.name,
        and performs any required actions to do so.

        Arguments:
            new_name {str} -- str

        Raises:
            NameError: [description]
        """

        if not self._validate_name(new_name):
            # failed validation
            self._validate_name_failed(new_name)

        self._name = new_name


#class ComponentGUIinterface


class BaseComponent():

    # Dummy private attribute used to check if an instanciated object is
    # indeed a BaseComponent class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_component` to check.
    __i_am_component__ = True

    def __init__(self, name: str, design, options=None,
                 make=True):

        assert is_design(design), "Error you did not pass in a valid \
        Metal Design object as a parent of this component."

        self.name = name
        self.design = design  # parent
        self.options = self.create_default_options()
        if options:
            self.options.update(options)

        # Elements created in make function
        self.elements = Dict()

        # In case someone want sto store extra information
        self.metadata = Dict()

        # Names of connectors associated with this components.
        # Used to rename, etc.
        self.connector_names = set()

        self._add_to_design()

        if make:
            self.make()

    def _add_to_design(self):
        ''' Add self to design objects dictionary.
            Function here, in case we want to generalize later.
        '''
        self.design.components[self.name] = self

    def get_geom_all(self):
        """
        Get all shapely geometry as a dict
        """
        return {elem.full_name : elem.geom for name, elem in self.elements}

    def get_geom_bounds(self):
        """Return the bounds of the geometry.
        Calls get_geom_all and finds the bounds of this collection.
        """
        raise NotImplementedError()


    @classmethod
    def create_default_options(cls):
        """
        Creates default options for the Metal Componnet class required for the class
        to function; i.e., be created, made, and rendered. Provides the blank option
        structure required.

        The options can be extended by plugins, such as renderers.
        """
        return Dict()

    def make(self):
        '''
        Create shapely objects, which are used to create component  elements.
        This method should be overwritten by the childs make function.
        '''
        raise NotImplementedError()

    def delete(self):
        """
        Delte the element and remove from the design.
        Removes also all of its connectors.
        """
        raise NotImplementedError()

    def rename(self):
        """
        Rename the component. Change the design dictioanries as well.
        handle components. Delete and remake.
        """
        raise NotImplementedError()

    def parse_value(self, value):
        """
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
        return self.design.parse_value(value)

    def parse_options(self, options=None):
        """
        Parse the options, converting string into interpreted values.
        Parses units, variables, strings, lists, and dicitonaries.
        Explained by example below.

        Options Arguments:
            options (dict) : default is None. If left None,
                             then self.options is used

        Calls `self.design.parse_options`.

        See `self.parse_value` for more infomation.
        """

        return self.design.parse_options(options if options else self.options)

    def add_connector(self, name, points: list, flip=False, chip=None):
        """Register a connector with the design.

        Arguments:
            two_points {list} -- List of the two point coordinates that deifne the start
                                 and end of the connector
            ops {None / dict} -- Options

        Keyword Arguments:
            name {string or None} -- By default is just the object name  (default: {None})
            chip {string or None} -- chip name or defaults to DEFAULT.chip
        """
        if name is None:
            name = self.name

        self.connector_names.add(name)

        self.design.add_connector(name=name,
                                  points=points,
                                  parent=self,
                                  chip=chip,
                                  flip=flip)
