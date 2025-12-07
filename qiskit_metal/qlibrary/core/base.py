# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""This is the main module that defines what a QComponent is in Qiskit Metal.

To see the docstring of QComponent in Jupyter notebook, use:
>> ?QComponent
"""
# pylint: disable=too-many-lines, too-many-public-methods

import logging
import inspect
import random
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Iterable, List, Union, Tuple, Dict as Dict_
from datetime import datetime
import pandas as pd
import numpy as np
import pprint
from inspect import signature

from qiskit_metal import draw
from qiskit_metal import is_design, logger

import qiskit_metal.qlibrary as qlibrary
from qiskit_metal import config
from qiskit_metal.draw import BaseGeometry
from qiskit_metal.toolbox_python.attr_dict import Dict
from qiskit_metal.toolbox_python.display import format_dict_ala_z
from qiskit_metal.qlibrary.core._parsed_dynamic_attrs import ParsedDynamicAttributes_Component

if not config.is_building_docs():
    from ...draw import Vector

__all__ = ['QComponent']

if TYPE_CHECKING:
    # For linting typechecking, import modules that can't be loaded here under normal conditions.
    # For example, I can't import QDesign, because it requires QComponent first. We have the
    # chicken and egg issue.
    from ...designs import QDesign
    import matplotlib


class QComponent():
    """`QComponent` is the core class for all Metal components and is the
    central construct from which all components in Metal are derived.

    The class defines the user interface for working with components.

    For front-end user:
        * Manipulates the dictionary of options (stored as string-string key-value
          pairs) to change the geometry and properties of the component.
        * The options of the class are stored in an options dictionary. These
          include the geometric sizes, such as width='10um' or height='5mm', etc.
        * The `make` function parses these strings and implements the logic required
          to transform the dictionary of options (stored as strings) into shapes
          with associated properties.

    For creator user:
        * The creator user implements the `make` function (see above)
        * The class define the internal representation of a components
        * The class provides the interfaces for the component (creator user)

    Default Options:
        * pos_x/_y: '0.0um' -- The x/y position of the center of the QComponent.
        * orientation: '0.0' -- The primary direction in degrees of the QComponent.
          Expressed counter-clockwise orientation.
        * chip: 'main' -- Chip holding the QComponent.
        * layer: '1' -- Manufacturing layer used for the QComponent.

        Nested default options can be overwritten with the update function.
        The following code demonstrates how the update works.

        .. code-block:: python
            :linenos:

            from qiskit_metal import Dict
            default = Dict(
                a=1,
                b=2,
                c=Dict(
                    d=3,
                    e=4,
                    f=Dict(
                        g=6,
                        h=7
                    )
                )
            )
            overwrite = Dict(
                a=10,
                b=20,
                c=Dict(
                    d=30,
                    f=Dict(
                        h=70
                    )
                ),
                z=33
            )
            default.update(overwrite)
            default

        >> {'a': 10, 'b': 20, 'c': {'d': 30, 'e': 4, 'f': {'g': 6, 'h': 70}}, 'z': 33}
    """
    # pylint: disable=too-many-instance-attributes

    default_options = Dict(pos_x='0.0um',
                           pos_y='0.0um',
                           orientation='0.0',
                           chip='main',
                           layer='1')
    """Default drawing options"""

    component_metadata = Dict()
    """Component metadata"""

    TOOLTIP = """QComponent"""

    options = {}
    """A dictionary of the component-designer-defined options.
    These options are used in the make function to create the QGeometry and QPins.
    All options should have string keys and preferrable string values.
    """

    # Dummy private attribute used to check if an instantiated object is
    # indeed a QComponent class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_component` to check.
    __i_am_component__ = True

    def __init__(self,
                 design: 'QDesign',
                 name: str = None,
                 options: Dict = None,
                 make=True,
                 component_template: Dict = None) -> Union[None, str]:
        """Create a new Metal component and adds it's default_options to the
        design.

        Args:
            design (QDesign): The parent design.
            name (str): Name of the component. Auto-named if possible.
            options (dict): User options that will override the defaults.  Defaults to None.
            make (bool): True if the make function should be called at the end of the init.
                Options be used in the make function to create the geometry.  Defaults to True.
            component_template (dict): User can overwrite the template options for the component
                that will be stored in the design, in design.template,
                and used every time a new component is instantiated.  Defaults to None.

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
            nor will be added to the design. The variable design.self.status
            will still be NotBuilt, as opposed to Initialization Successful.

            Either True or False - If string name, used for component, is NOT
            being used in the design, a component will be generated and
            added to design using the name.
        """

        # Make the id be None, which means it hasn't been added to design yet.
        self._id = None
        self._made = False

        self._component_template = component_template

        # Status: used to handle building of a component and checking if it succeeded or failed.
        self.status = 'Not Built'
        if not is_design(design):
            raise ValueError(
                "Error you did not pass in a valid Metal QDesign object as a '\
                'parent of this QComponent.")

        self._design = design  # reference to parent
        # pylint: disable=literal-comparison
        if self._delete_evaluation(name) == 'NameInUse':
            raise ValueError(
                f"{name} already exists! Please choose a different name for your new QComponent"
            )

        self._name = name
        self._class_name = self._get_unique_class_name()  # Full class name
        #: A dictionary of the component-designer-defined options.
        #: These options are used in the make function to create the QGeometry and QPins.
        #: All options should have string keys and preferrable string values.
        self.options = self.get_template_options(
            design=design, component_template=component_template)
        if options:
            self.options.update(options)

        # Parser for options
        self.p = ParsedDynamicAttributes_Component(self)
        # Should put this earlier so could pass in other error messages?
        self._error_message = ''
        if self._check_pin_inputs():
            self.logger.warning(self._error_message)
            return
        # Build and component internals

        #: Dictionary of pins. Populated by component designer in make function using `add_pin`.
        self.pins = Dict()

        #: Metadata allows a designer to store extra information or analysis results.
        self.metadata = Dict()

        # Add the component to the parent design
        self._id = self.design._get_new_qcomponent_id()  # Create the unique id
        self._add_to_design()  # Do this after the pin checking?

        #: Stores the latest status of the component. Values include:
        #: ``Initialization Successful``, ``Build Failed``, etc.
        self.status = 'Initialization Successful'

        # Used for short name, and renderers adding information to tables.
        self.a_metadata = self._gather_all_children_metadata()

        # Auto naming - add id to component based on type
        if name is None:
            prefix = self.a_metadata
            # limit names to 24 characters
            name_trunc = 24
            # if no prefix, use class name
            if "short_name" not in prefix:
                short_name = self.__class__.__name__[:name_trunc]
            else:
                short_name = prefix['short_name'][:name_trunc]
            name_id = self.design._get_new_qcomponent_name_id(short_name)
            # rename loop to make sure that no components manually named by the user conflicts
            while self.design.rename_component(self._id, short_name + "_" +
                                               str(name_id)) != 1:
                name_id = self.design._get_new_qcomponent_name_id(short_name)

        # Add keys for each type of table.  add_qgeometry() will update bool if the table is used.
        self.qgeometry_table_usage = Dict()
        self.populate_to_track_table_usage()

        # Make the component geometry
        if make:
            self.rebuild()

    @classmethod
    def _gather_all_children_options(cls) -> dict:
        """From the QComponent core class, traverse the child classes to
        gather the `default_options` for each child class.

        Collects the options starting with the basecomponent,
        and stepping through the children.
        Each child adds it's options to the base options.  If the
        key is the same, the option of the youngest child is used.

        Note: if keys are the same for child and grandchild,
        grandchild will overwrite child

        Init method.

        Returns:
            dict: options from all children
        """

        options_from_children = {}
        parents = inspect.getmro(cls)

        # len-2: generic "object" does not have default_options.
        for child in parents[len(parents) - 2::-1]:
            # The template default options are in a class dict attribute `default_options`.
            if hasattr(child, 'default_options'):
                options_from_children = {
                    **options_from_children,
                    **child.default_options
                }

        if qlibrary.core.qroute.QRoute in parents:
            options_from_children.pop("pos_x", None)
            options_from_children.pop("pos_y", None)
            options_from_children.pop("orientation", None)

        return options_from_children

    @classmethod
    def _gather_all_children_metadata(cls) -> dict:
        """From the QComponent core class, traverse the child classes to
        gather the component_metadata for each child class.

        Note: if keys are the same for child and grandchild, grandchild will overwrite child
        Init method.

        Returns:
            dict: Metadata from all children.
        """

        metadata_from_children = {}
        parents = inspect.getmro(cls)
        # Base.py is not expected to have component_metadata dict to add to design class.
        for child in parents[len(parents) - 2::-1]:
            # There is a developer agreement so the defaults will be in dict named component_metadata.
            if hasattr(child, 'component_metadata'):
                metadata_from_children = {
                    **metadata_from_children,
                    **child.component_metadata
                }

        return metadata_from_children

    @classmethod
    def _get_unique_class_name(cls) -> str:
        """Returns unique class name based on the module.

        Returns:
            str: Example: 'qiskit_metal.qlibrary.qubits.transmon_pocket.TransmonPocket'
        """
        return f'{cls.__module__}.{cls.__name__}'

    @classmethod
    def _register_class_with_design(cls, design: 'QDesign', template_key: str,
                                    component_template: Dict):
        """Init function to register a component class with the design when
        first instantiated. Registers the design template options.

        Args:
            design (QDesign): The parent design
            template_key (str): Key to use
            component_template (dict): Template of components to copy, with renderer options
        """
        # do not overwrite
        if template_key not in design.template_options:
            # if not component_template:
            #     component_template = cls._gather_all_children_options()
            children_options = cls._gather_all_children_options()
            options_template_renderer = {
                **children_options,
                **component_template
            }
            # design.template_options[template_key] = deepcopy(
            #     component_template)
            design.template_options[template_key] = deepcopy(
                options_template_renderer)

    @property
    def name(self) -> str:
        """Name of the component."""
        return self._name

    @name.setter
    def name(self, new_name: str):
        """Rename the component. Change the design dictionaries as well. handle
        components. Delete and remake.

        Returns:
            bool: True is successful, otherwise failure code
        """
        return_code = self.design.rename_component(self.id, new_name)
        if return_code is not True:
            logger.warning(
                f'In design_base.name, the new_name={new_name} was not set. ')
        return return_code

    @property
    def design(self) -> 'QDesign':
        """Return a reference to the parent design object.

        Returns:
            QDesign: design
        """
        return self._design

    @property
    def class_name(self) -> str:
        """Return the full name of the class: the full module name with the
        class name. e.g., qiskit_metal.qlibrary.qubits.TransmonPocket.

        Returns:
            str: Class name
        """
        return self._class_name

    @property
    def logger(self) -> logging.Logger:
        """The Qiskit Metal Logger.

        Returns:
            logging.Logger: Logger
        """
        return self._design.logger

    @property
    def pin_names(self) -> set:
        """The names of the pins.

        Returns:
            set: Set of pin names
        """
        return set(self.pins.keys())

    @property
    # pylint: disable=invalid-name
    def id(self) -> int:
        """The unique id of component within a design.

        Returns:
            int: Component id
        """
        return self._id

    def _add_to_design(self):
        """Add self to design objects dictionary.

        Method will obtain an unique id for the component within a
        design, THEN add itself to design.
        """
        # pylint: disable=protected-access
        self.design._components[self.id] = self
        self.design.name_to_id[self.name] = self._id

    @classmethod
    def get_template_options(cls,
                             design: 'QDesign',
                             component_template: Dict = None,
                             logger_: logging.Logger = None,
                             template_key: str = None) -> Dict:
        """Creates template options for the Metal Component class required for
        the class to function, based on the design template; i.e., be created,
        made, and rendered. Provides the blank option structure required.

        The options can be extended by plugins, such as renderers.

        Args:
            design (QDesign): Design class. Should be the class, not the instance.
            component_template (Dict): Template options to overwrite the class ones (default: None)
            logger_ (logging.Logger): A logger for errors.  Defaults to None.
            template_key (str): The template key identifier. If None, then uses
                cls._get_unique_class_name().  Defaults to None.

        Returns:
            Dict: dictionary of default options based on design template.
        """
        # get key for templates
        if template_key is None:
            template_key = cls._get_unique_class_name()

        renderer_key_values = cls._get_table_values_from_renderers(design)
        # Think
        if component_template is not None:
            renderer_and_component_template = {
                **renderer_key_values,
                **component_template
            }
        else:
            renderer_and_component_template = renderer_key_values

        if template_key not in design.template_options:
            cls._register_class_with_design(design, template_key,
                                            renderer_and_component_template)

        if template_key not in design.template_options:
            logger_ = logger_ or design.logger
            if logger_:
                logger_.error(
                    f'ERROR in the creating component {cls.__name__}!\nThe default '
                    f'options for the component class {cls.__name__} are missing'
                )

        # Specific object template options
        template_options = deepcopy(Dict(design.template_options[template_key]))

        return template_options

    def _delete_evaluation(self, check_name: str = None):
        """When design.overwrite_enabled, the user is allowed to delete an
        existing component within the design if the name is being used.

        Args:
            check_name (str, optional): Name of new component.  Defaults to None.

        Returns:
            string: Return 'NameInUse' if overwrite flag is False and
            check_name is already being used within design.
            Otherwise return None.
        """
        answer = self._is_name_used(check_name)
        if self._design.overwrite_enabled and answer:
            self._design.delete_component(check_name)
        elif answer:
            logger.warning(
                f'The QComponent name `{check_name}` is already in use, '
                f'by a component (with QComponent id={answer}).\n'
                f'QComponent NOT made, nor added to the design. \n'
                'To force overwrite a QComponent with an existing name '
                'use the flag:\n`design.overwrite_enabled = True`.')
            return 'NameInUse'
        return None

    def make(self):
        """The make function implements the logic that creates the geometry
        (poly, path, etc.) from the qcomponent.options dictionary of
        parameters, and the adds them to the design, using
        qcomponent.add_qgeometry(...), adding in extra needed information, such
        as layer, subtract, etc.

        Use the qiskit_metal.draw module to create the geometry.

        **Note:**
            * This method should be overwritten by the children make function.
            * This function only contains the logic, the actual call to make the element is in
              rebuild()

        Raises:
            NotImplementedError: Overwrite this function by subclassing.
        """
        raise NotImplementedError()

    def to_script(self,
                  thin: bool = False,
                  is_part_of_chip: bool = False) -> Tuple:
        """

        Args:
            thin: If true then any key in the QComponent's options whose value
              is the same value as the default will not be included in the body
            is_part_of_chip: If true, body will not include header code


        Returns: Code that if copy-pasted into a .py file would generate
        an instance of this class with the same properties as the instance calling
        this function

        """

        def is_default_options(k):
            """ Returns true if option's key value is the same as the default value """
            temp_option = self.get_template_options(self.design)
            def_options = self.default_options

            if (k in def_options and def_options[k] == self.options[k]):
                return True

            if (k in temp_option and temp_option[k] == self.options[k]):
                return True

            return False

        module = self._get_unique_class_name()
        cls = '.'.join(module.split('.')[:-1])
        obj_name = module.split('.')[-1]

        ### constructing imports ###

        #header
        if not is_part_of_chip:
            header = """
from qiskit_metal import designs, MetalGUI

design = designs.DesignPlanar()

gui = MetalGUI(design)
            """
        else:
            header = ""

        # component import
        comp_import = f"""from {cls} import {obj_name}"""

        full_import = header + comp_import

        ### constructing qcomponent instantiation ###

        ## setting up options
        if thin:
            body_options = {}
            for k in self.options:
                if not is_default_options(k):
                    body_options[k] = self.options[k]
        else:
            body_options = self.options

        if len(body_options) < 1:
            str_options = ""
        else:
            pp = pprint.PrettyPrinter(width=41, compact=False)
            str_options = f"""options={pp.pformat(body_options)}"""

        ## setting up component-specific args
        # get init from child?
        to_ignore = {
            'self', 'name', 'design', 'make', 'kwargs', 'options', 'args'
        }
        class_signature = signature(self.__class__.__init__)

        failed = set()
        params = dict()
        str_params = ""
        for _, param in class_signature.parameters.items():
            if not param.name in to_ignore:
                param_name = param.name
                if param_name in self.__dict__:
                    param_name = param.name
                    param_val = self.__dict__[param.name]
                    if type(param_val) is str:
                        param_val = f"'{param_val}'"
                    params[param_name] = param_val
                elif '_' + param_name in self.__dict__:
                    priv_param_name = '_' + param_name
                    param_val = self.__dict__[priv_param_name]
                    if type(param_val) is str:
                        param_val = f"'{param_val}'"
                    params[param_name] = param_val
                else:
                    failed.add(param_name)
        for k, v in params.items():
            str_params += f"""
{k}={v},"""

        str_failed = ""
        if len(failed) > 0:
            str_failed += """

            # WARNING"""
        for k in failed:
            str_failed += f"""
#{k} failed to have a value"""

        ## setting up metadata
        if len(self.metadata) > 1:
            str_meta_d = f"""
{self.name}.meta = {self.metadata}
        """
        else:
            str_meta_d = ""

        ## cleaning up
        strname = self.name
        if not strname.isidentifier():
            if "-" in strname:
                strname = strname.replace("-", "")
            if not strname.isidentifier():
                strname = cls + str(random.randint(1000))

        other_args = ""
        if str_options != "":
            other_args += """,
""" + str_options

        if str_params != "":
            other_args += """,
""" + str_params

        ## setting up instantiation
        body = f"""
{str_failed}
{strname} = {obj_name}(
design,
name='{strname}'{other_args}
)
{str_meta_d}
"""

        return full_import, body

    def rebuild(self):
        """Builds the QComponent.

        This is the main action function of a
        QComponent, call it qc. It converts the qc.options into QGeometry with
        all of the required options, such as the geometry points, layer number,
        materials, etc. needed to render.

        The build clears the existing QGeometry and QPins and then calls the qc.make function,
        which is written by the component developer to implement the logic (using the metal.
        draw module) to convert the qc.options into the QGeometry.

        *Build status:*
        The function also sets the build status of the component.
        It sets to `failed` when the component is created, and then it sets to `good` when it is
        done with no errors. The user can also set other statuses, which can appear if the code
        fails to reach the final line of the build, where the build status is set to `good`.

        Raises:
            Exception: Component build failure
        """
        self.status = 'failed'
        try:
            if self._made:  # already made, just remaking
                self.design.qgeometry.delete_component_id(self.id)

                # pylint: disable=protected-access
                self.design._delete_all_pins_for_component(self.id)

            self.make()
            self._made = True
            self.status = 'good'

            self.design.build_logs.add_success(
                f"{str(datetime.now())} -- Component: {self.name} successfully built"
            )

        except Exception as error:
            self.logger.error(
                f'ERROR in building component name={self.name}, error={error}')
            self.design.build_logs.add_error(
                f"{str(datetime.now())} -- Component: {self.name} failed with error\n: {error}"
            )
            raise error

    def delete(self):
        """Delete the QComponent.

        Removes QGeometry, QPins, etc. from the design.
        """
        self.design.delete_component(self.name)

    # Maybe still should be fine as any values will be in component options still?
    # Though the data table approach and rendering directly via shapely could lead to problem
    # with variable use
    def parse_value(
        self, value: Union[Any, List, Dict, Iterable]
    ) -> Union[Any, List, Dict, Iterable]:
        """Parse a string, mappable (dict, Dict), iterable (list, tuple) to
        account for units conversion, some basic arithmetic, and design
        variables. This is the main parsing function of Qiskit Metal.

        Args:
            value (str): String to parse *or*
            variable_dict (dict): dict pointer of variables

        Return:
            str, float, list, tuple, or ast eval: Parse value

        Handled Inputs:
            Strings:
                Strings of numbers, numbers with units; e.g., '1', '1nm', '1 um'
                    Converts to int or float.
                    Some basic arithmetic is possible, see below.

                Strings of variables 'variable1'.
                    Variable interpretation will use string method
                    isidentifier 'variable1'.isidentifier()`

            Dictionaries:
                Returns ordered `Dict` with same key-value mappings, where the values have
                been subjected to parse_value.

            Itterables(list, tuple, ...):
                Returns same kind and calls itself `parse_value` on each element.

            Numbers:
                Returns the number as is. Int to int, etc.


        Arithmetic:
            Some basic arithmetic can be handled as well, such as `'-2 * 1e5 nm'`
            will yield float(-0.2) when the default units are set to `mm`.

        Default units:
            User units can be set in the design. The design will set config.DEFAULT.units

        Examples:
            See the docstring for this module.
                >> ?qiskit_metal.toolbox_metal.parsing
        """
        return self.design.parse_value(value)

    def parse_options(self, options: Dict = None) -> Dict:
        """Parse the options, converting string into interpreted values. Parses
        units, variables, strings, lists, and dictionaries. Explained by
        example below.

        Args:
            options (dict) : If left None, then self.options is used.  Defaults to None.

        Returns:
            dict: Parsed value

        Calls `self.design.parse_options`.

        See `self.parse_value` for more information.
        """
        return self.design.parse_value(options if options else self.options)

    def _is_name_used(self, check_name: str) -> int:
        """Used to check if name of component already exists.

        Args:
            check_name (str): Name which user requested to apply to current component.

        Returns:
            int: 0 if does not exist, otherwise
            component-id of component which is already using the name.

        Warning: If user has used this text version of the component name already,
        warning will be given to user.
        """

        if check_name in self._design.name_to_id:
            component_id = self._design.name_to_id[check_name]
            # if not self._overwrite_flag:
            #    logger.warning(f"Called _is_name_used, "
            #                   f"component_id({check_name}, id={component_id})"
            #                   " is already being used in design.")
            return component_id
        return 0

####################################################################################
# Functions for handling of pins

    def add_pin(
            self,
            name: str,  # Should be static based on component designer's choice
            points: np.ndarray,
            width: float,
            input_as_norm: bool = False,
            chip: str = None,
            gap: float = None):  # gap defaults to 0.6 * width
        """Adds a pin from two points which are normal/tangent to the intended
        plane of the pin. The normal should 'point' in the direction of
        intended connection. Adds the new pin as a subdictionary to parent
        component's pins dictionary.

        Args:
            * name (str): name of the pin
            * points (numpy.ndarray): [[x1,y1],[x2,y2]] for the normal/tangent line
            * width (float): the width of the intended connection (eg. qubit bus pad arm)
            * input_as_norm (bool): Indicates if the points are tangent or normal to the pin plane.
              Defaults to False.. Make True for normal.
            * parent (Union[int,]): The id of the parent component.
            * chip (str): the name of the chip the pin is located on. Defaults to None, which is 
            converted to self.options.chip.
            * gap (float): the dielectric gap of the pin for the purpose of representing as a port
              for simulations.  Defaults to None which is converted to 0.6 * width.

        Dictionary containing pins information:
            * points (numpy.ndarray) - two (x,y) points which represent the edge of the pin for
              another component to attach to (eg. the edge of a CPW TL)
            * middle (numpy.ndarray) - an (x,y) which represents the middle of the points above,
              where the pin is represented.
            * normal (numpy.ndarray) - the normal vector of the pin, pointing in direction of
              intended connection
            * tangent (numpy.ndarray) - 90 degree rotation of normal vector
            * width (float) - the width of the pin
            * chip (str) - the chip the pin is on
            * parent_name - the id of the parent component
            * net_id - net_id of the pin if connected to another pin.  Defaults to 0, indicates
              not connected))

        ::

            * = pin
            . = outline of component

        ---> = the list being passed in as 'points' [[x1,y1],[x2,y2]]


        normal vector

        ::

            ..........
                     .
            --------->*
                     .
            ..........

        tangent vector

        ::

            ..........^
                     .|
                     .*
                     .|
            ..........|
        """
        assert len(points) == 2

        if gap is None:
            gap = width * 0.6
        if chip is None:
            chip = self.options.chip

        rounding_val = self.design.template_options['PRECISION']
        points = np.around(
            points, rounding_val)  #Need points to remain as shapely geom?

        if input_as_norm:
            middle_point = points[1]
            vec_normal = points[1] - points[0]
            vec_normal /= np.linalg.norm(vec_normal)

            s_point = np.round(Vector.rotate(
                vec_normal, (np.pi / 2))) * width / 2 + points[1]
            e_point = np.round(Vector.rotate(
                vec_normal, -(np.pi / 2))) * width / 2 + points[1]
            points = [s_point, e_point]
            tangent_vector = Vector.rotate(vec_normal, np.pi / 2)

        else:
            vec_dist, tangent_vector, vec_normal = draw.Vector.two_points_described(
                points)
            middle_point = np.sum(points, axis=0) / 2.
            width = np.linalg.norm(vec_dist)

        pin_dict = Dict(
            points=points,
            middle=np.around(middle_point, rounding_val),
            normal=np.around(vec_normal, rounding_val),
            tangent=np.around(tangent_vector, rounding_val),
            width=np.around(width, rounding_val),
            gap=np.around(gap, rounding_val),
            chip=chip,
            parent_name=self.id,
            net_id=0,
            # Place holder value for potential future property (auto-routing cpw with
            # length limit)
            length=0)

        self.pins[name] = pin_dict

    def get_pin(self, name: str) -> Dict:
        """Interface for components to get pin data.

        Args:
            name (str): Name of the desired pin.

        Returns:
            dict: Returns the data of the pin, see make_pin() for what those values are.
        """

        return self.pins[name]

    def _check_pin_inputs(self):
        """Checks that the pin_inputs are valid, sets an error message
        indicating what the error is if the inputs are not valid. Checks
        regardless of user passing the component name or component id (probably
        a smoother way to do this check).

        3 Error cases:
            - Component does not exist
            - Pin does not exist
            - Pin is already attached to something

        Returns:
            str: Status test, or None
        """
        # Add check for if user inputs nonsense?
        # pylint: disable=protected-access
        false_component = False
        false_pin = False
        pin_in_use = False
        for pin_check in self.options.pin_inputs.values():
            component = pin_check['component']
            pin = pin_check['pin']
            if isinstance(component, str):
                if component not in self.design.components:
                    false_component = True
                elif pin not in self.design.components[component].pins:
                    false_pin = True
                elif self.design.components[component].pins[pin].net_id:
                    pin_in_use = True
            elif isinstance(component, int):
                if component not in self.design._components:
                    false_component = True
                elif pin not in self.design._components[component].pins:
                    false_pin = True
                elif self.design._components[component].pins[pin].net_id:
                    pin_in_use = True
            # Should modify to allow for multiple error messages to be returned.
            if false_component:
                self._error_message = (
                    f'Component {component} does not exist. {self.name} has not been built. '
                    'Please check your pin_input values.')
                return 'Component Does Not Exist'
            if false_pin:
                self._error_message = (
                    f'Pin {pin} does not exist in component {component}. '
                    f'{self.name} has not been built. Please check your pin_input values.'
                )
                return 'Pin Does Not Exist'
            if pin_in_use:
                self._error_message = (
                    f'Pin {pin} of component {component} is already in use. '
                    f'{self.name} has not been built. Please check your pin_input values.'
                )
                return 'Pin In Use'
        return None

    # This method does not appear to be being used anywhere.
    def connect_components_already_in_design(self, pin_name_self: str,
                                             comp2_id: int,
                                             pin2_name: str) -> int:
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
        # pylint: disable=protected-access

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
                f'Component_id {self._id} not connected.  The pin '
                f'{pin_name_self} is already connected to something else.')
            return net_id_rtn

        if self.design._components[comp2_id].pins[pin2_name].net_id:
            # Pin already in use.
            logger.warning(
                f'Component_id {comp2_id} not connected.  The pin '
                f'{pin2_name} is already connected to something else.')
            return net_id_rtn

        net_id_rtn = self.design.connect_pins(self.id, pin_name_self, comp2_id,
                                              pin2_name)

        return net_id_rtn

########################################################################

    def add_dependency(self, parent: str, child: str):
        """Add a dependency between one component and another. Calls parent
        design.

        Args:
            parent (str): The component on which the child depends
            child (str): The child cannot live without the parent.
        """
        self.design.add_dependency(parent, child)

##########################################
# QGeometry

    def add_qgeometry(
            self,
            kind: str,
            geometry: dict,
            subtract: bool = False,
            helper: bool = False,
            layer: Union[int, str] = None,  # chip will be here
            chip: str = None,
            **kwargs):
        r"""Add QGeometry.

        Takes any additional options in options.

        Args:
            kind (str): The kind of QGeometry, such as 'path', 'poly', etc.
                        All geometry in the dictionary should have the same kind,
                        such as Polygon or LineString.
            geometry (Dict[BaseGeometry]): Key-value pairs of name of the geometry
                you want to add and the value should be a shapely geometry object, such
                as a Polygon or a LineString.
            subtract (bool): Subtract from the layer.  Defaults to False.
            helper (bool): Is this a helper object. If true, subtract must be false
                           Defaults to False.
            layer (int, str): The layer to which the set of QGeometry will belong
                              Defaults to None, which is converted to self.options.chip.
            chip (str): Chip name. Defaults to None, which is converted to 
            self.options.chip.
            kwargs (dict): Parameters dictionary

        Assumptions:
            * Assumes all geometry in the `geometry` argument are homogeneous in kind;
              i.e., all lines or polys etc.
        """
        # assert (subtract and helper) == False, "The object can't be a subtracted helper. Please"\
        #    " choose it to either be a helper or a a subtracted layer, but not both. Thank you."

        if layer is None:
            layer = self.options.layer
        if chip is None:
            chip = self.options.chip

        if kind in self.qgeometry_table_usage.keys():
            self.qgeometry_table_usage[kind] = True
        else:
            self.logger.warning(
                f'Component with classname={self.class_name} does not know about '
                f'table name "{kind}".')

        renderer_key_values = self._get_specific_table_values_from_renderers(
            kind)
        for key in renderer_key_values:
            if key in self.options:
                renderer_key_values[key] = deepcopy(self.options[key])

        # # if not already in kwargs, add renderer information to it.
        renderer_and_options = {**renderer_key_values, **kwargs}

        # When self.options is instantiated, the template_options are populated.
        # renderer_and_options = {**self.options, **kwargs}

        self.design.qgeometry.add_qgeometry(kind,
                                            self.id,
                                            geometry,
                                            subtract=subtract,
                                            helper=helper,
                                            layer=layer,
                                            chip=chip,
                                            **renderer_and_options)

    def _get_specific_table_values_from_renderers(self, kind: str) -> Dict:
        """Populate a dict to combine with options for the qcomponent.

        Based on kind, which the table name, the component-developer denotes in the metadata,
        assume those qgeometry.tables are used for the component. The method
        will search a dict populated by all the renderers during their init.

        Args:
            kind (str): Name of table, like junction, path, or poly.

        Returns:
            Dict: key is column names for tables, value is data for the column.
        """
        all_renderers_key_value = dict()

        # design.renderer_defaults_by_table[table_name][renderer_name][column_name]
        if kind in self.design.renderer_defaults_by_table:
            for name_renderer, renderer_data in self.design.renderer_defaults_by_table[
                    kind].items():
                if len(renderer_data) > 0:
                    for col_name, col_value in renderer_data.items():
                        render_col_name = f'{name_renderer}_{col_name}'
                        all_renderers_key_value[render_col_name] = col_value

        return all_renderers_key_value

    @classmethod
    def _get_table_values_from_renderers(cls, design: 'QDesign') -> Dict:
        """Populate a dict to combine with options for the qcomponent.

        Based on tables the component-developer denotes in the metadata,
        assume those qgeometry.tables are used for the component. The method
        will search a dict populated by all the renderers during their init.

        Returns:
            Dict: key is column names for tables, value is data for the column.
        """
        metadata_dict = cls._gather_all_children_metadata()
        tables_list = design.get_list_of_tables_in_metadata(metadata_dict)

        all_renderers_key_value = dict()
        # design.renderer_defaults_by_table[table_name][renderer_name][column_name]
        for table in tables_list:
            if table in design.renderer_defaults_by_table:
                for name_renderer, renderer_data in design.renderer_defaults_by_table[
                        table].items():
                    if len(renderer_data) > 0:
                        for col_name, col_value in renderer_data.items():
                            render_col_name = f'{name_renderer}_{col_name}'
                            all_renderers_key_value[render_col_name] = col_value
        return all_renderers_key_value

######################################

    def __repr__(self, *args):
        # pylint: disable=invalid-name

        b = '\033[95m\033[1m'
        b1 = '\033[94m\033[1m'
        e = '\033[0m'

        # id = {hex(id(self))}
        # options = pprint.pformat(self.options)

        options = format_dict_ala_z(self.options)
        text = f"{b}name:    {b1}{self.name}{e}\n"\
            f"{b}class:   {b1}{self.__class__.__name__:<22s}{e}\n"\
            f"{b}options: {e}\n{options}\n"\
            f"{b}module:  {b1}{self.__class__.__module__}{e}\n"\
            f"{b}id:      {b1}{self.id}{e}\n"
        return text


############################################################################
# Geometry handling of created qgeometry

    @property
    def qgeometry_types(self) -> List[str]:
        """Get a list of the names of the element tables.

        Returns:
            List[str]: Name of element table or type; e.g., 'poly' and 'path'
        """
        return self.design.qgeometry.get_element_types()

    def qgeometry_dict(  # pylint: disable=inconsistent-return-statements
            self, element_type: str) -> Dict_[str, BaseGeometry]:
        """Returns a dict of element qgeometry (shapely geometry) of the
        component as a python dict, where the dict keys are the names of the
        qgeometry and the corresponding values are the shapely geometries.

        Args:
            element_type (str): Name of element table or type; e.g., 'poly' and 'path'

        Returns:
            List[BaseGeometry]: Geometry diction or None if an error in the name of the element
            type (ie. table)
        """

        if element_type == 'all' or self.design.qgeometry.check_element_type(
                element_type):
            return self.design.qgeometry.get_component_geometry_dict(
                self.name, element_type)

    def qgeometry_list(  # pylint: disable=inconsistent-return-statements
            self,
            element_type: str = 'all') -> List[BaseGeometry]:
        """Returns a list of element qgeometry (shapely geometry) of the
        component as a python list of shapely geometries.

        Args:
            element_type (str): Name of element table or type; e.g., 'poly' and 'path'.
                                Can also specify all

        Returns:
            List[BaseGeometry]: Geometry list or None if an error in the name of the element type
            (ie. table)
        """

        if element_type == 'all' or self.design.qgeometry.check_element_type(
                element_type):
            return self.design.qgeometry.get_component_geometry_list(
                self.name, element_type)

    def qgeometry_table(  # pylint: disable=inconsistent-return-statements
            self, element_type: str) -> pd.DataFrame:
        """Returns the entire element table for the component.

        Args:
            element_type (str): Name of element table or type; e.g., 'poly' and 'path'

        Returns:
            pd.DataFrame: Element table for the component or None if an error in the name of
            the element type (ie. table)
        """

        if element_type == 'all' or self.design.qgeometry.check_element_type(
                element_type):
            return self.design.qgeometry.get_component(self.name, element_type)

    def qgeometry_bounds(self) -> Tuple:
        """Fetched the component bound dict_value.

        Returns:
            tuple: containing (minx, miny, maxx, maxy) bound values for the bounds of the
            component as a whole.

        Uses:
            design.qgeometry.get_component_bounds
        """
        bounds = self.design.qgeometry.get_component_bounds(self.name)
        return bounds

    def qgeometry_plot(self,
                       ax: 'matplotlib.axes.Axes' = None,
                       plot_kw: dict = None) -> List:
        """Draw all the qgeometry of the component (polys and path etc.)

        Args:
            ax (matplotlib.axes.Axes): Matplotlib axis to draw on.  Defaults to None.
                                       When None, it gets the current axis.
            plot_kw (dict): Parameters dictionary.

        Returns:
            List: The list of qgeometry draw

        Example use:
            Suppose you had a component called q1:

                fig, ax = draw.mpl.figure_spawn()
                q1.qgeometry_plot(ax)
        """
        qgeometry = self.qgeometry_list()
        plot_kw = {}
        draw.mpl.render(qgeometry, ax=ax, kw=plot_kw)
        return qgeometry

    def populate_to_track_table_usage(self) -> None:
        """Use the element_handler to get a list of all the table names used in
        QGeometry.

        The dict qgeometry_able_usage should get updated by
        add_qgeometry(). This dict is used to get a summary tables used
        for this component.
        """
        for table_name in self.design.qgeometry.tables.keys():
            self.qgeometry_table_usage[table_name] = False
