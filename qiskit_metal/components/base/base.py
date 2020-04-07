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
from copy import deepcopy
from typing import Any, Iterable, List, Optional, TypeVar, Union

from ... import DEFAULT_OPTIONS, is_design, logger
from ...draw import BaseGeometry
from ...toolbox_python.attr_dict import Dict

#from ...elements import ElementTypes

__all__ = ['BaseComponent']

# I can't import DesignBase here, because I have ti first create the
# component class, so this is a cludge
DesignBase = TypeVar('DesignBase')


class BaseComponent():
    """
    `BaseComponent` is the base class for all Metal components and is the
    central construct from which all components in Metal are derived.

    The class defines the user interface for working with components.

    For front-end user:
        * Manipulates the dictionary of options (stored as string-string key-value
         pairs) to change the geometry and properties of the component.
        * The options of the class are stored in an options dicitonary. These
          include the geometric sizes, such as width='10um' or height='5mm', etc.
        * The `make` function parses these strings and implements the logic required
          to transform the dictionary of options (stored as strings) into shapes
          with associated properties.

    For creator user:
        * The creator user implements the `make` function (see above)
        * The class define the internal representation of a componetns
        * The class provides the interfaces for the component (creator user)
    """

    # Default options can inherit the options of other functions of objects
    # in DEFAULT_OPTIONS. Give the name of the key-value pair, where the key is
    # how you want to call the copied version of DEFAULT_OPTIONS[key]
    _inherit_options_from = {}

    # Dummy private attribute used to check if an instanciated object is
    # indeed a BaseComponent class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_component` to check.
    __i_am_component__ = True

    def __init__(self, name: str, design: DesignBase, options: Dict = None,
                 make=True):
        """Create a new Metal component and adds it to the design.

        Arguments:
            name {str} -- Name of the component.
            design {DesignBase} -- The parent design.

        Keyword Arguments:
            options {[type]} -- User options that will override the defaults. (default: {None})
            make {bool} -- Should the make function be called at the end of the init.
                    Options be used in the make funciton to create the geometry. (default: {True})
        """

        assert is_design(design), "Error you did not pass in a valid \
        Metal Design object as a parent of this component."

        self._name = name
        self._design = design  # pointer to parent

        # TODO: options:  should probably write a setter and getter?
        self.options = self.create_default_options()
        if options:
            self.options.update(options)

        # In case someone wants to store extra information or
        # analysis results
        self.metadata = Dict()

        # Names of connectors associated with this components.
        # Used to rename, etc.
        self._connector_names = set()

        # Geometry inner class to handle all geometric functions
        self.geom = _Geometry_Handler(self)

        # has the component already been made
        self._made = False

        # Logger
        self.logger = logger

        # Add the component to the parent design
        self._add_to_design()

        # Make the component geometry
        if make:
            self.do_make()

    @property
    def name(self) -> str:
        '''Name of the component
        '''
        return self._name

    @name.setter
    def name(self, new_name: str):
        '''Rename the component. Change the design dictioanries as well.
        handle components. Delete and remake.'''
        return self.design.rename_component(self.name, new_name)

    @property
    def design(self) -> DesignBase:
        '''Return a reference to the parent design object'''
        return self._design

    @property
    def connectors(self) -> set:
        '''The names of the connectors'''
        return self._connector_names

    def _add_to_design(self):
        ''' Add self to design objects dictionary.
            Function here, in case we want to generalize later.
        '''
        self.design.components[self.name] = self

    @classmethod
    def create_default_options(cls) -> Dict:
        """
        Creates default options for the Metal Componnet class required for the class
        to function; i.e., be created, made, and rendered. Provides the blank option
        structure required.

        The options can be extended by plugins, such as renderers.
        """
        # Every object should posses there -- common to all
        #options = deepcopy(DEFAULT_OPTIONS['BaseComponent'])

        # Specific object default options
        options = deepcopy(Dict(DEFAULT_OPTIONS[cls.__name__]))
        # options.update(deepcopy(default_options))

        # Specific sub-options inherited from other functions
        for key, value in cls._inherit_options_from.items():
            options[key] = deepcopy(
                Dict(DEFAULT_OPTIONS[value])
            )

        return options

    def make(self):
        '''
        Overwrite in inheritnace to define user logic to convert options dictionary into
        elements.
        Here, one creates the shapely objects, assigns them as elements.
        This method should be overwritten by the childs make function.

        This function only contains the logic, the actual call to make the element is in
        do_make() and remake()
        '''
        raise NotImplementedError()

    def do_make(self):
        """Actually make or remake the component"""
        if self._made:  # already made, just remaking
            # TODO: this is probably very inefficient, design more efficient way
            self.design.elements.delete_component(self.name)
            self.make()
        else:  # first time making
            self.make()
            self._made = True  # what if make throws an error part way?

    def delete(self):
        """
        Delete the element and remove from the design.
        Removes also all of its connectors.
        """
        raise NotImplementedError()

    def parse_value(self, value: Union[Any, List, Dict, Iterable]):
        # Maybe still should be fine as any values will be in component options still?
        # Though the data table approach and rendering directly via shapely could lead to problem
        # with variable use
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

    def parse_options(self, options: Dict = None) -> Dict:
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

        self._connector_names.add(name)

        self.design.add_connector(name=name,
                                  points=points,
                                  parent=self,
                                  chip=chip,
                                  flip=flip)

    def add_dependency(self, parent: str, child: str):
        """Add a dependency between one component and another.
        Calls parent design.

        Arguments:
            parent {str} -- The component on which the child depends
            child {str} -- The child cannot live without the parent.
        """
        self.design.add_dependency(parent, child)

##########################################
# Elements
    def add_elements(self,
                     kind: str,
                     elements: dict,
                     subtract: bool = False,
                     helper: bool = False,
                     layer: Union[int, str] = 1,  # chip will be here
                     **kwargs
                     ):
                    #  subtract: Optional[bool] = False,
                    #  layer: Optional[Union[int, str]] = 0,
                    #  type: Optional[ElementTypes] = ElementTypes.positive,
                    #  chip: Optional[str] = 'main',
                    #  **kwargs):
        r"""Add elements.

        Takes any additional options in options.

        Assumptions:
            * Assumes all elements in the elements are homogeneous in kind;
             i.e., all lines or polys etc.


        Arguments:
            kind {str} -- The kind of elements, such as 'path', 'poly', etc.
                          All elements in the dicitonary should have the same kind
            elements {Dict[BaseGeometry]} -- Key-value pairs

        Keyword Arguments:
            subtract {bool} -- Subtract from the layer (default: {False})
            helper {bool} -- Is this a helper object. If true, subtract must be false
            layer {int, str} -- TODO: The layer to which the set of elements will belong
                        (default: {0})
        """
        assert (subtract and helper) == False, "The object can't be a subtracted helper. Please"\
            " choose it to either be a helper or a a subtracted layer, but not both. Thank you."

        self.design.elements.add_elements(kind, self.name, elements, subtract=subtract,
                                          helper=helper, layer=layer, **kwargs)


############################################################################
# Geometry handling


class _Geometry_Handler:
    r"""Handles all puerly  geoemtric manipulations and methods for the
    component. Just a collections of methods.
    """

    def __init__(self, component: BaseComponent):
        self.parent = component
        self.design = component.design

    def get_all(self, element_type:str, full_table=False):
        """
        Get all shapely geometry as a dict with key being the names of the
        elements and the values as the shapely geometry.
        """
        # return {elem.full_name : elem.geom for name, elem in self.parent.elements}
        if full_table:
            return self.design.elements.get_component(self.parent.name, element_type)
        else:
            return list(self.design.elements.get_component_geometry(self.parent.name, element_type))

    def get_bounds(self):
        """
        Return the bounds of the geometry.
        Calls get_all and finds the bounds of this collection.
        Uses the shapely methods.
        """
        # for all element_type
        element_type = 'poly'
        shapes = self.get_all(element_type)
        raise NotImplementedError()

    # translate, rotate, etc. if possible


# For developers, example Outter-Inner class constructions:

# .. code-block: python

#     class Outer:
#     def __init__(self, x):
#         self.x=5
#         self.inner = self.Inner(self)

#     class Inner:

#         def __init__(self, parent):
#             self.parent=parent

#         def printme(self):
#             print(self.parent.x)

#     c = Outer(5)
#     c.inner.printme()

# NOT IN USE, some code prototype
'''
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
    def _validate_name(name:str): #include check that isn't already in use?
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
'''
