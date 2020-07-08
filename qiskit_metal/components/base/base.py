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
This is the main module that defines what a QComponent is in Qiskit Metal.

To see the docstring of QComponent, use:
    >> ?QComponent

@author: Zlatko Minev, Thomas McConekey, ... (IBM)
@date: 2019
"""

import logging
import inspect
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Iterable, List, Union, Optional, Dict as Dict_

import pandas as pd
import numpy as np
from ... import draw
from ... import is_design, logger
from ...draw import BaseGeometry
from ...toolbox_python.attr_dict import Dict
from ._parsed_dynamic_attrs import ParsedDynamicAttributes_Component
from ...draw import Vector
from ...toolbox_python.display import format_dict_ala_z


__all__ = ['QComponent']

if TYPE_CHECKING:
    # For linting typechecking, import modules that can't be loaded here under normal conditions.
    # For example, I can't import QDesign, because it requires QComponent first. We have the
    # chicken and egg issue.
    from ...designs import QDesign
    # from ...elements import ElementTypes
    import matplotlib


class QComponent():
    """
    `QComponent` is the base class for all Metal components and is the
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

    ''' QComponent.gather_all_children_options collects the options
        starting with the basecomponent, and stepping through the children.
        Each child adds it's options to the base options.  If the
        key is the same, the option of the youngest child is used.
    '''

    # Dummy private attribute used to check if an instanciated object is
    # indeed a QComponent class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_component` to check.
    __i_am_component__ = True

    def __init__(self, design: 'QDesign', name: str, options: Dict = None,
                 make=True, component_template: Dict = None) -> Union[None, str]:
        """Create a new Metal component and adds it's default_options to the design.

        Arguments:
            design (QDesign): The parent design.

            name (str): Name of the component.

            options (dict): User options that will override the defaults. (default: None)

            make (bool): True if the make function should be called at the end of the init.
            Options be used in the make funciton to create the geometry. (default: True)

            component_template (dict): User can overwrite the template options for the component
            that will be stored in the design, in design.template,
            and used every time a new component is instantiated.
            (default: None)


        Returns:
            str: 'NameInUse' is retruned if user requests name for new component
            which is already being used within the design.  None if init completes as expected.

        Raises:
            ValueError: User supplied design isn't a QDesign



        Note:  Information copied from QDesign class.

        self._design.overwrite_enabled (bool): 
        When True - If the string name, used for component, already
        exists in the design, the existing component will be 
        deleted from design, and new component will be generated 
        with the same name and newly generated component_id, 
        and then added to design. 

        When False - If the string name, used for component, already
        exists in the design, the existing component will be 
        kept in the design, and current component will not be generated,
        nor will be added to the design. The 'NameInUse' will be returned 
        during component generation.

        Either True or False - If string name, used for component, is NOT 
        being used in the design, a component will be generated and 
        added to design using the name.
        """

        # Make the id be None, which means it hasn't been added to design yet.
        self._id = None

        if not is_design(design):
            raise ValueError(
                "Error you did not pass in a valid Metal QDesign object as a parent of this QComponent.")

        self._design = design  # reference to parent

        if self._delete_evaluation(name) is 'NameInUse':
            return 'NameInUse'

        self._name = name
        self._class_name = self._get_unique_class_name()  # Full class name

        # Options
        self.options = self.get_template_options(design=design,
                                                 component_template=component_template)
        if options:
            self.options.update(options)

        # Parser for options
        self.p = ParsedDynamicAttributes_Component(self)

        # Build and component internals
        # Status: used to handle building of a component and checking if it succeedded or failed.
        self.status = 'not built'
        # Create an empty dict, which will populated by component designer.
        self.pins = Dict()  # TODO: should this be private?
        self._made = False

        # In case someone wants to store extra information or analysis results
        self.metadata = Dict()

        # Add the component to the parent design
        self._id = self.design._get_new_qcomponent_id()  # Create the unique id
        self._add_to_design()  # Do this after the pin checking?

        # Make the component geometry
        if make:
            self.rebuild()

        return None

    @classmethod
    def _gather_all_children_options(cls):
        '''
        From the base class of QComponent, traverse the child classes
        to gather the .default options for each child class.

        Note: if keys are the same for child and grandchild, grandchild will overwrite child
        Init method.

        Returns:
            dict: options from all children
        '''

        options_from_children = {}
        parents = inspect.getmro(cls)

        # Base.py is not expected to have default_options dict to add to design class.
        for child in parents[len(parents)-2::-1]:
            # There is a developer agreement so the defaults will be in dict named default_options.
            if hasattr(child, 'default_options'):
                options_from_children = {
                    **options_from_children, **child.default_options}

        return options_from_children

    @classmethod
    def _get_unique_class_name(cls) -> str:
        """Returns unique class name based on the module

        Returns:
            str: Example: 'qiskit_metal._components.qubits.transmon_pocket.TransmonPocket'
        """
        return f'{cls.__module__}.{cls.__name__}'

    @classmethod
    def _register_class_with_design(cls,
                                    design: 'QDesign',
                                    template_key: str,
                                    component_template: Dict):
        """Init funciton to register a component class with the design when first instantiated.
            Registers the design template options.

            Arguments:
                design (QDesign): The parent design
                template_key (str): Key to use
                component_template (dict): template of components to copy
        """
        # do not overwrite
        if template_key not in design.template_options:
            if not component_template:
                component_template = cls._gather_all_children_options()
            design.template_options[template_key] = deepcopy(
                component_template)

    @property
    def name(self) -> str:
        '''Name of the component'''
        return self._name

    @name.setter
    def name(self, new_name: str):
        '''Rename the component. Change the design dictioanries as well.
        handle components. Delete and remake.

        Returns:
            bool: True is successful, otherwise failure code
        '''
        return_code = self.design.rename_component(self.id, new_name)
        if return_code != True:
            logger.warning(
                f'In design_base.name, the new_name={new_name} was not set. ')
        return return_code

    @property
    def design(self) -> 'QDesign':
        '''Return a reference to the parent design object

        Returns:
            QDesign: design
        '''
        return self._design

    @property
    def class_name(self) -> str:
        '''Return the full name of the class: the full module name with the class name.
        e.g., qiskit_metal._components.qubits.QubitClass

        Returns:
            str: class name
        '''
        return self._class_name

    @property
    def logger(self) -> logging.Logger:
        """The Qiskit Metal Logger

        Returns:
            logging.Logger: logger
        """
        return self._design.logger

    @property
    def pin_names(self) -> set:
        '''The names of the pins

        Returns:
            set: set of pin names
        '''
        return set(self.pins.keys())

    @property
    def id(self) -> int:
        '''The unique id of component within a design.

        Returns:
            int: component id
        '''
        return self._id

    def _add_to_design(self):
        ''' Add self to design objects dictionary. Method will obtain an unique id
        for the component within a design, THEN add itself to design.
        '''
        self.design._components[self.id] = self
        self.design.name_to_id[self.name] = self._id

    @classmethod
    def get_template_options(cls,
                             design: 'QDesign',
                             component_template: Dict = None,
                             logger_: logging.Logger = None,
                             template_key: str = None) -> Dict:
        """
        Creates template options for the Metal Componnet class required for the class
        to function, based on teh design template; i.e., be created, made, and rendered.
        Provides the blank option structure required.

        The options can be extended by plugins, such as renderers.

        Arguments:
            design (QDesign): Design class. Should be the class, not the instance.

            component_template (Dict): Tempalte options to overwrite the class ones (default: None)

            logger_ (logging.Logger): A logger for errors. (default: None)

            template_key (str): The template key identifier. If None, then uses
            cls._get_unique_class_name() (default: None)

        Returns:
            Dict: dictionary of default options based on design template.
        """
        # get key for tepmlates
        if template_key is None:
            template_key = cls._get_unique_class_name()

        if template_key not in design.template_options:
            cls._register_class_with_design(
                design, template_key, component_template)

        if template_key not in design.template_options:
            logger_ = logger_ or design.logger
            if logger_:
                logger_.error(f'ERROR in the creating component {cls.__name__}!\nThe default '
                              f'options for the component class {cls.__name__} are missing')

        # Specific object template options
        options = deepcopy(Dict(design.template_options[template_key]))

        return options

    def _delete_evaluation(self, check_name: str = None):
        """design.overwrite_enabled allows user to delete an existing component within 
        the design if the name is being used.

        Args:
            check_name (str, optional): Name of new component. Defaults to None.

        Returns:
            string: Return 'NameInUse' if overwrite flag is False and 
            check_name is already being used within design. 
            Otherwise return None.
        """
        answer = self._is_name_used(check_name)
        if self._design.overwrite_enabled and answer:
            self._design.delete_component(check_name)
        elif answer:
            logger.warning(f'The name {check_name} is used in component id={answer}. '
                           'Component was not made, nor added to design.')
            return 'NameInUse'
        return None

    def make(self):
        '''
        Overwrite in inheritnace to define user logic to convert options dictionary into
        elements.
        Here, one creates the shapely objects, assigns them as elements.
        This method should be overwritten by the childs make function.

        This function only contains the logic, the actual call to make the element is in
        rebuild() and remake()

        Raises:
            NotImplementedError: Code isn't written yet
        '''
        raise NotImplementedError()

    # TODO: Maybe call this function build
    # TODO: Capture error here and save to log as the latest error
    def rebuild(self):
        """Builds the QComponent.
        This is the main action function of a QComponent, call it qc.
        It converts the qc.options into QGeometry with all of the required options, such as
        the geometry points, layer number, materials, etc. needed to render.

        The build clears the exisitng QGeometry and QPins and then calls the qc.make function,
        which is writen by the component developer to implement the logic (using the metal.
        draw module) to convert the qc.options into the QGeometry.

        *Build status:*
        The funciton also sets the build status of the component.
        It sets to `failed` when the component is created, and then it sets to `good` when it is
        done with no errors. The user can also set other statuses, which can appear if the code fails
        to reach the final line of the build, where the build status is set to `good`.
        """

        # Begin by setting the status to failed, we will change this if we succed
        self.status = 'failed'
        if self._made:  # already made, just remaking
            # TODO: this is probably very inefficient, design more efficient way
            self.design.elements.delete_component_id(self.id)
            self.design._delete_all_pins_for_component(self.id)

            self.make()
        else:  # first time making
            self.make()
            self._made = True  # what if make throws an error part way?
        self.status = 'good'

    def delete(self):
        """
        Delete the QComponent.
        Removes QGeometry, QPins, etc. from the design.
        """
        self.design.delete_component(self.name)

    # Maybe still should be fine as any values will be in component options still?
    # Though the data table approach and rendering directly via shapely could lead to problem
    # with variable use
    def parse_value(self, value: Union[Any, List, Dict, Iterable]) -> Union[Any, List, Dict, Iterable]:
        """
        Parse a string, mappable (dict, Dict), iterrable (list, tuple) to account for
        units conversion, some basic arithmetic, and design variables.
        This is the main parsing function of Qiskit Metal.

        Arguments:
            value (str): string to parse *or*
            variable_dict (dict): dict pointer of variables

        Return:
            str, float, list, tuple, or ast eval: Parse value

        Handled Inputs:
            Strings:
                Strings of numbers, numbers with units; e.g., '1', '1nm', '1 um'
                    Converts to int or float.
                    Some basic arithmatic is possible, see below.

                Strings of variables 'variable1'.
                    Variable interpertation will use string method
                    isidentifier 'variable1'.isidentifier()`

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


        """
        return self.design.parse_value(value)

    def parse_options(self, options: Dict = None) -> Dict:
        """
        Parse the options, converting string into interpreted values.
        Parses units, variables, strings, lists, and dicitonaries.
        Explained by example below.

        Arguments:
            options (dict) : default is None. If left None,
                             then self.options is used

        Returns:
            dict: Parsed value

        Calls `self.design.parse_options`.

        See `self.parse_value` for more infomation.
        """

        return self.design.parse_value(options if options else self.options)

    def _is_name_used(self, check_name: str) -> int:
        """Used to check if name of component already exists.

        Args:
            check_name (str):  Name which user requested to apply to current component.

        Returns:
            int: 0 if does not exist, otherwise
            component-id of component which is already using the name.

        Warning: If user has used this text version of the component name already,
        warning will be given to user.

        """

        if check_name in self._design.name_to_id:
            component_id = self._design.name_to_id[check_name]
            # if not self._overwrite_flag:
            #    logger.warning(f"Called _is_name_used, component_id({check_name}, id={component_id})"
            #                   " is already being used in design.")
            return component_id
        else:
            return 0


####################################################################################
# Functions for handling of pins
#
# TODO: Combine the two pin generation functions into one.
#   Simplify the data types
#   Stress test the results
#   Component name vs. id issues?
#
#   What information is truly necessary for the pins? Should they have a z-direction component?
#   Will they operate properly with non-planar designs?


    def add_pin_as_normal(self,
                          name: str,
                          start: np.ndarray,
                          end: np.ndarray,
                          width: float,
                          parent: Union[int, 'QComponent'],
                          flip: bool = False,
                          chip: str = 'main'):
        """
        Generates a pin from two points which are normal to the intended plane of the pin.
        The normal should 'point' in the direction of intended connection. Adds dictionary to
        parent component.

        Arguments:
            name (str): Name of the pin
            start (numpy.ndarray): [x,y] coordinate of the start of the normal
            end (numpy.ndarray): [x,y] coordinate of the end of the normal
            width (float): the width of the intended connection (eg. qubit bus pad arm)
            parent (Union[int,]): The id of the parent component
            flip (bool): to change the direction of intended connection (True causes a 180, default False)
            chip (str): the name of the chip the pin is located on, default 'main'

        A dictionary containing a collection of information about the pin, necessary for use in Metal:
            * points (list) - two (x,y) points which represent the edge of the pin for
              another component to attach to (eg. the edge of a CPW TL)
            * middle (numpy.ndarray) - an (x,y) which represents the middle of the points above,
              where the pin is represented.
            * normal (numpy.ndarray) - the normal vector of the pin, pointing in direction of
              intended connection
            * tangent (numpy.ndarray) - 90 degree rotation of normal vector
            * width (float) - the width of the pin
            * chip (str) - the chip the pin is on
            * parent_name - the id of the parent component
            * net_id - net_id of the pin if connected to another pin (default 0, indicates
              not connected))

        """

        vec_normal = end - start
        vec_normal /= np.linalg.norm(vec_normal)
        if flip:
            vec_normal = -vec_normal

        s_point = np.round(Vector.rotate(
            vec_normal, (np.pi/2))) * width/2 + end
        e_point = np.round(Vector.rotate(
            vec_normal, -(np.pi/2))) * width/2 + end

        self.pins[name] = Dict(
            points=[s_point, e_point],  # TODO
            middle=end,
            normal=vec_normal,
            # TODO: rotate other way sometimes?
            tangent=Vector.rotate(vec_normal, np.pi/2),
            width=width,
            chip=chip,
            parent_name=parent
        )

    def make_pin(self, points: list, parent_name: str, flip=False, chip='main'):
        """Called by add_pin, does the math for the pin generation.

        Args:
            points (list): list of two (x,y) points which represent the edge of the pin for
                    another component to attach to (eg. the edge of a CPW TL)
            parent_name (str): name of the parent
            flip (bool): True to flip (Default: False)
            chip (str): the chip the pin is on (Default: 'main')

        Returns:
            Dict: A dictionary containing a collection of information about the pin, necessary
            for use in Metal.

        Dictionar Contents:
            * points (list) - two (x,y) points which represent the edge of the pin for another
              component to attach to (eg. the edge of a CPW TL)
            * middle (numpy.ndarray) - an (x,y) which represents the middle of the points above,
              where the pin is represented.
            * normal (numpy.ndarray) - the normal vector of the pin, pointing in direction of
              intended connection
            * tangent (numpy.ndarray) - 90 degree rotation of normal vector
            * width (float) - the width of the pin
            * chip (str) - the chip the pin is on
            * parent_name - the id of the parent component
            * net_id - net_id of the pin if connected to another pin (default 0, indicates not
              connected) 

        """
        assert len(points) == 2

        # Get the direction vector, the unit direction vec, and the normal vector
        vec_dist, vec_dist_unit, vec_normal = draw.Vector.two_points_described(
            points)

        if flip:
            vec_normal = -vec_normal

        return Dict(
            points=points,
            middle=np.sum(points, axis=0)/2.,
            normal=vec_normal,
            tangent=vec_dist_unit,
            width=np.linalg.norm(vec_dist),
            chip=chip,
            parent_name=parent_name,
            net_id=0
        )

    def get_pin(self, name: str):
        """Interface for components to get pin data

        Args:
            name (str): Name of the desired pin.

        Returns:
            dict: Returns the data of the pin, see make_pin() for what those values are.
        """

        return self.pins[name]

    # TODO: Maybe rename to add_pin_as_tangent? @priti
    def add_pin(self,
                name: str,
                points: list,
                parent: Union[str, 'QComponent'],
                flip: bool = False,
                chip: str = 'main'):
        """Add the named pin to the respective component's pins subdictionary

        Arguments:
            name (str): Name of pin
            points (list): List of two (x,y) points that define the pin
            parent (Union[str,): component or string or None. Will be converted to a
                                 string, which will the name of the component.
            flip (bool): True to flip (Default: False)
            chip (str): the chip the pin is on (Default: 'main')
        """

        self.pins[name] = self.make_pin(
            points, parent, flip=flip, chip=chip)

    def connect_components_already_in_design(self, pin_name_self: str, comp2_id: int, pin2_name: str) -> int:
        """WARNING: Do NOT use this method during generation of component instance.
            This method is expecting self to be added to design._components dict.  More importantly,
            the unique id of self component needs to be in design._components dict.

        Args:
            pin_name_self (str): Name of pin within the component.
            comp2_id (int): Component within design, but not self.
            pin2_name (str): The pin of comp2_id that pin_name_self will connect to.

        Returns:
            int: A unique net_id for the connection.
        """

        net_id_rtn = 0

        if self.id not in self.design._components:
            # Component not in design.
            logger.warning(
                f'No connection made. Component_id {self.id} not in design.')
            return net_id_rtn

        if comp2_id not in self.design._components:
            # Component not in design.
            logger.warning(
                f'No connection made. Component_id {comp2_id} not in design.')
            return net_id_rtn

        if self.design._components[self._id].pins[pin_name_self].net_id:
            # Pin already in use.
            logger.warning(
                f'Component_id {self._id} not connected.  The pin {pin_name_self} is already connected to something else.')
            return net_id_rtn

        if self.design._components[comp2_id].pins[pin2_name].net_id:
            # Pin already in use.
            logger.warning(
                f'Component_id {comp2_id} not connected.  The pin {pin2_name} is already connected to something else.')
            return net_id_rtn

        net_id_rtn = self.design.connect_pins(
            self.id, pin_name_self, comp2_id, pin2_name)

        return net_id_rtn

########################################################################

    def add_dependency(self, parent: str, child: str):
        """Add a dependency between one component and another.
        Calls parent design.

        Arguments:
            parent (str): The component on which the child depends
            child (str): The child cannot live without the parent.
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
                     chip: str = 'main',
                     **kwargs
                     ):
        #  subtract: Optional[bool] = False,
        #  layer: Optional[Union[int, str]] = 0,
        #  type: Optional[ElementTypes] = ElementTypes.positive,
        #  chip: Optional[str] = 'main',
        #  **kwargs):
        r"""Add elements.

        Takes any additional options in options.

        Arguments:
            kind (str): The kind of elements, such as 'path', 'poly', etc.
                        All elements in the dicitonary should have the same kind
            elements (Dict[BaseGeometry]): Key-value pairs
            subtract (bool): Subtract from the layer (default: False)
            helper (bool): Is this a helper object. If true, subtract must be false
                           (default: False)
            layer (int, str): The layer to which the set of elements will belong
                              (default: 1)
            chip (str): Chip name (default: 'main')
            kwargs (dict): Parameters dictionary

        Assumptions:
            * Assumes all elements in the elements are homogeneous in kind;
              i.e., all lines or polys etc.
        """
        # assert (subtract and helper) == False, "The object can't be a subtracted helper. Please"\
        #    " choose it to either be a helper or a a subtracted layer, but not both. Thank you."

        self.design.elements.add_elements(kind, self.id, elements, subtract=subtract,
                                          helper=helper, layer=layer, chip=chip, **kwargs)

    def __repr__(self, *args):
        b = '\033[94m\033[1m'
        b1 = '\033[95m\033[1m'
        e = '\033[0m'

        # id = {hex(id(self))}
        # options = pprint.pformat(self.options)

        options = format_dict_ala_z(self.options)
        return f"""
 {b}name:    {b1}{self.name}{e}
 {b}class:   {b1}{self.__class__.__name__:<22s}{e}
 {b}options: {e}\n{options}
 {b}module:  {b1}{self.__class__.__module__}{e}
 {b}id:      {b1}{self.id}{e}"""

############################################################################
# Geometry handling of created elements

    @property
    def elements_types(self) -> List[str]:
        """Get a list of the names of the element tables.

        Returns:
            List[str]: Name of element table or type; e.g., 'poly' and 'path'
        """
        return self.design.elements.get_element_types()

    def qgeometry_dict(self, element_type: str) -> Dict_[str, BaseGeometry]:
        """
        Returns a dict of element geoemetry (shapely geometry) of the component
        as a python dict, where the dict keys are the names of the elements
        and the corresponding values are the shapely geometries.

        Arguments:
            element_type (str): Name of element table or type; e.g., 'poly' and 'path'

        Returns:
            List[BaseGeometry]: Geometry diction or None if an error in the name of the element
            type (ie. table)
        """
        if element_type == 'all' or self.design.elements.check_element_type(element_type):
            return self.design.elements.get_component_geometry_dict(self.name, element_type)

    def qgeometry_list(self, element_type: str = 'all') -> List[BaseGeometry]:
        """
        Returns a list of element geoemetry (shapely geometry) of the component
        as a python list of shapely geometries.

        Arguments:
            element_type (str): Name of element table or type; e.g., 'poly' and 'path'.
                                Can also specify all

        Returns:
            List[BaseGeometry]: Geometry list or None if an error in the name of the element type
            (ie. table)
        """
        if element_type == 'all' or self.design.elements.check_element_type(element_type):
            return self.design.elements.get_component_geometry_list(self.id, element_type)

    def qgeometry_table(self,  element_type: str) -> pd.DataFrame:
        """
        Returns the entire element table for the component.

        Arguments:
            element_type (str): Name of element table or type; e.g., 'poly' and 'path'

        Returns:
            pd.DataFrame: Element table for the component or None if an error in the name of
            the element type (ie. table)
        """
        if element_type == 'all' or self.design.elements.check_element_type(element_type):
            return self.design.elements.get_component(self.name, element_type)

    def qgeometry_bounds(self):
        """
        Fetched the component bound dict_value

        Returns:
            tuple: containing (minx, miny, maxx, maxy) bound values for the bounds of the
            component as a whole.

        Uses:
            design.elements.get_component_bounds
        """
        bounds = self.design.elements.get_component_bounds(self.name)
        return bounds

    def qgeometry_plot(self, ax: 'matplotlib.axes.Axes' = None, plot_kw: dict = None) -> List:
        """    Draw all the elements of the component (polys and path etc.)

        Arguments:
            ax (matplotlib.axes.Axes):  Matplotlib axis to draw on (Default: None -- gets the current axis)
            plot_kw (dict): Parameters dictionary

        Returns:
            List: The list of elements draw

        Example use:
            Suppose you had a component called q1:

                fig, ax = draw.mpl.figure_spawn()
                q1.qgeometry_plot(ax)
        """
        elements = self.qgeometry_list()
        plot_kw = {}
        draw.mpl.render(elements, ax=ax, kw=plot_kw)
        return elements
