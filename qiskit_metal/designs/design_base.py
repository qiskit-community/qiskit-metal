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

@date: 2019
@author: Zlatko Minev, Thomas McConeky, ... (IBM)
"""
# To create a basic UML diagram
# >> pyreverse -o png -p desin_base design_base.py -A  -S

import importlib

from typing import Union, List, Iterable, Any, Dict as Dict_, TYPE_CHECKING
from datetime import datetime

import numpy as np
from numpy.linalg import norm
from ..draw import Vector

from .. import Dict, draw, logger
from ..components import is_component
from ..config import DefaultMetalOptions, DefaultOptionsRenderer
from ..toolbox_metal.import_export import load_metal_design, save_metal
from ..toolbox_metal.parsing import parse_options, parse_value
from ..elements import QElementTables
from ..toolbox_python.utility_functions import log_error_easy
from .net_info import QNet


if TYPE_CHECKING:
    # For linting typechecking, import modules that can't be loaded here under normal conditions.
    # For example, I can't import QDesign, because it requires QComponent first. We have the
    # chicken and egg issue.
    from ..components.base.base import QComponent

__all__ = ['QDesign']


class QDesign():
    """
    QDesign is the base class for Qiskit Metal Designs.
    A design is the most top-level object in all of Qiskit Metal.

    Attributes:
        components (Dict) : A dictionary that stores all the components of the design.

        variables (Dict) : The variables of the design, which can be used in the make funciton
                of a component.

        chips (Dict) : A collection of all the chips associated with the design.

        connectors (Dict) : Information on the connectors

        metadata (Dict) : A dictionary of information that the user can store
            along with the desing. This includes the name of the design,
            the time the design was created, and other notes the user might choose to store.

        default_options (dict) : Contains all the default options used for component creation and
            other functions.

        save_path (str or None) : Path that the design is saved to. Set when saved or loaded

    """

    # TODO -- Idea: Break up QDesign into several interface classes,
    # such as DesignConnectorInterface, DesignComponentInterface, etc.
    # in order to do a more Dependency Inversion Principle (DIP) style,
    # see also Dependency Injection (DI). This can also generalize nicely
    # to special flip chips, etc. to handle complexity!
    # Technically, components, connectors, variables, etc. are all separate entities
    # that can interface

    # Dummy private attribute used to check if an instanciated object is
    # indeed a QDesign class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_design` to check.
    __i_am_design__ = True

    def __init__(self, metadata: dict = None):
        """_qcomponent_latest_assigned_id -- Used to keep a tally and ID of all components within an instanziation of a design.
                                A component is added to a design by base._add_to_design with init of a comoponent.
                                During init of component, design class provides an unique id for each instance of
                                component being added to design.  Note, if a component is removed from the design,
                                the ID of removed component should not be used again.  However, if a component is
                                renamed, then the ID should continute to be used.
        """
        self._qcomponent_latest_assigned_id = 0

        # Key attributes related to physical content of the design
        # These will be saved
        self._components = Dict()
        self._connectors = Dict()
        self._variables = Dict()
        self._chips = Dict()

        self._metadata = self._init_metadata()
        if metadata:
            self.update_metadata(metadata)

        self.save_path = None  # type: str

        self.logger = logger  # type: logging.Logger

        self._elements = QElementTables(self)

        self._template_options = DefaultMetalOptions()  # used for components
        self.variables.update(self.template_options.qdesign.variables)

        # Can't really use this until DefaultOptionsRenderer.default_draw_substrate.color_plane is resolved.
        self._template_renderer_options = DefaultOptionsRenderer()  # use for renderer
        self._net_info = QNet()

    def _init_metadata(self) -> Dict:
        """Initialize default metadata dicitoanry

        Returns:
            Dict: default metadata dicitoanry
        """
        now = datetime.now()  # current date and time
        return Dict(
            design_name='my_design',
            notes='',
            time_created=now.strftime("%m/%d/%Y, %H:%M:%S"))

    def update_metadata(self, new_metadata: dict):
        """Update the metadata dictionary of the design with a
        a new metadata dictionary. This will overwrite only the new keys
        that you pass in. All other keys will be unaffected.

        Args:
            new_metadata (dict): New metadatadata dict to update
        """
        self._metadata.update(new_metadata)

#########PROPERTIES##################################################

    @property
    def components(self) -> Dict_[str, 'QComponent']:
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
    def variables(self) -> Dict_[str, str]:
        '''
        Return the Dict object that keeps track of all variables in the design.
        '''
        return self._variables

    @property
    def template_options(self) -> Dict:
        '''
        Return default_options dictionary, which contain default options used in creating Metal
        component, and in calling other drawing and key functions.
        '''
        return self._template_options

    @property
    def template_renderer_options(self) -> Dict:
        '''Return default_renderer_options dictionary, which contain default options used in creating Metal renderer.
        '''
        return self._template_renderer_options.default_options

    @property
    def metadata(self) -> Dict:
        '''
        Return the metadata Dict object that keeps track of all metadata in the design.
        '''
        return self._metadata

    @property
    def elements(self) -> QElementTables:
        '''
        Use for advanced users only. Access to the element tables.
        '''
        return self._elements

    @property
    def qcomponent_latest_assigned_id(self) -> int:
        '''
        Return unique number for each instance.
        For user of the design class to know the lastest id assigned to QComponent.
        '''
        return self._qcomponent_latest_assigned_id

#########Proxy properties##################################################

    def get_chip_size(self, chip_name: str = 'main'):
        """Utility function to return the chip size"""
        raise NotImplementedError()

    def get_chip_z(self, chip_name: str = 'main'):
        """Utility function to return the z value of a chip"""
        raise NotImplementedError()

#########General methods###################################################

    def rename_variable(self, old_key: str, new_key: str):
        """
        Renames a variable in the variables dictionary.
        Preserves order

        Arguments:
            old_key {str} -- previous variable name
            new_key {str} -- new variable name
        """
        keys = list(self._variables.keys())
        values = list(self._variables.values())

        keys[keys.index(old_key)] = new_key
        self._variables = Dict(zip(keys, values))

    def delete_all_connectors(self):
        '''
        Clear all connectors in the design.
        '''
        self.connectors.clear()
        return self.connectors

    def delete_all_components(self):
        '''
        Clear all components in the design dictionary.
        Also clears all connectors.
        '''
        # clear all the dicitonaries and element tables.
        self._components.clear()
        self.delete_all_connectors()
        # TODO: add element tables here
        self._elements.clear_all_tables()
        # TODO: add dependency handling here

    def _get_new_qcomponent_id(self):
        ''' Give new id that QComponent can use.'''
        self._qcomponent_latest_assigned_id += 1
        return self._qcomponent_latest_assigned_id

    def rebuild(self):  # remake_all_components
        """
        Remakes all components with their current parameters.
        """
        # TODO: there are some performance tricks here, we could just clear all element tables
        # and then skip the deletion of compoentns elements one by one
        # first clear all the
        # thne just make without the checks on existing
        # TODO: Handle error and print nice statemetns
        # try catch log_simple_error
        for name, obj in self.components.items():  # pylint: disable=unused-variable
            try:  # TODO: performace?
                obj.do_make()  # should we call this build?
            except:
                print(f'ERORROR in building {name}')
                log_error_easy(
                    self.logger, post_text=f'\nERROR in rebuilding component "{name}"!\n')

    def reload_component(self, component_module_name: str, component_class_name: str):
        """Reload the module and class of a given componetn and update
        all class instances. (Advanced function.)

        Arguments:
            component_module_name {str} -- String name of the module name, such as
                `qiskit_metal.components.qubits.transmon_pocket`
            component_class_name {str} -- String name of the class name inside thst module,
                such  as `TransmonPocket`
        """
        self.logger.debug(
            f'Reloading component_class_name={component_class_name}; component_module_name={component_module_name}')
        module = importlib.import_module(component_module_name)
        module = importlib.reload(module)
        new_class = getattr(module, component_class_name)

        # components that need
        for instance in filter(lambda k:
                               k.__class__.__name__ == component_class_name and
                               k.__class__.__module__ == component_module_name,
                               self.components.values()):
            instance.__class__ = new_class

        # Alternative, but reload will say not in sys.path
        # self = gui.component_window.src_widgets[-1].ui.src_editor
        # spec = importlib.util.spec_from_file_location(self.component_module_name, self.component_module_path) # type: ModuleSpec
        # module = importlib.util.module_from_spec(spec) # type: module e.g.,
        # spec.loader.exec_module(module)
        # importlib.reload(module)

    def rename_component(self, component_name: str, new_component_name: str):
        """Rename component.

        Arguments:
            component_name {str} -- Old name
            new_component_name {str} -- New name

        Returns:
            int -- Results:
                1: True name is changed.
                -1: Failed, new component name exists.
                -2: Failed, invalid new name
        """
        #
        if new_component_name in self.components:
            self.logger.info(
                f'Cannot rename {component_name} to {new_component_name}. Since {new_component_name} exists')
            return -1

        def is_valid_component_name(s: str):
            return s.isidentifier()

        # Check that the name is a valid component name
        if not is_valid_component_name(component_name):
            self.logger.info(
                f'Cannot rename {component_name} to {new_component_name}.')
            return -2

        # do rename
        component = self.components[component_name]
        component._name = new_component_name
        self.components[new_component_name] = self.components.pop(
            component_name)
        self._elements.rename_component(component_name, new_component_name)
        # TODO: handle renadming for all else: dependencies etc.

        return True

    def delete_component(self, component_name: str, force=False):
        """Deletes component and connectors attached to said component.
        If no component by that name is present, then just return True
        If component has dependencices return false and do not delete,
        unless force=True.

        Arguments:
            component_name {str} -- Name of component to delete

        Keyword Arguments:
            force {bool} -- force delete component even if it has children (default: {False})

        Returns:
            bool -- is there no such component
        """

        # Nothing to delete if name not in components
        if not component_name in self.components:
            self.logger.info('Called delete component {component_name}, but such a \
                             component is not in the design dicitonary of components.')
            return True

        # check if components has dependencies
        #   if it does, then do not delete, unless force=true
        #       logger.error('Cannot delete component{component_name}. It has dependencies. ')
        #          return false
        #   if it does not then delete

        # Do delete component ruthelessly
        return self._delete_component(component_name)

    def _delete_component(self, component_name: str):
        """Delete component without doing any checks.

        Returns:
            bool -- [description]
        """
        # Remove connectors
        connector_names = self.components[component_name].connectors
        for c_name in connector_names:
            self.connectors.pop(c_name)

        # Remove from design dictionary of components
        self.components.pop(component_name, None)

        self._elements.delete_component(component_name)

        return True


#########I/O###############################################################

    @classmethod
    def load_design(cls, path: str):
        """Load a Metal design from a saved Metal file.
        (Class method)

        Arguments:
            path {str} -- Path to saved Metal design.

        Returns:
            Loaded metal design.
            Will also update default dicitonaries.
        """
        logger.warning("Loading is a beta feature.")
        design = load_metal_design(path)
        return design

    def save_design(self, path: str = None):
        """Save the metal design to a Metal file.

        Arguments:
            path {str or None} -- Path to save the design to. If none, then tried
                                to use self.save_path if it is set. (default: None)
        """

        self.logger.warning("Saving is a beta feature.")  # TODO:

        if path is None:
            if self.save_path is None:
                self.logger.error('Cannot save design since you did not provide a path to'
                                  'save to yet. Once you save the dewisgn to a path, the then you call save '
                                  'without an argument.')
            else:
                path = self.save_path

        self.save_path = str(path)

        # Do the actual saving
        self.logger.info(f'Saving design to {path}')
        result = save_metal(path, self)
        if result:
            self.logger.info(f'Saving successful.')
        else:
            self.logger.error(f'Saving failed.')

        return result

#########Creating Components###############################################################

    def parse_value(self, value: Union[Any, List, Dict, Iterable]) -> Any:
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

    def parse_options(self, params: dict, param_names: str) -> dict:
        """
        Extra utility function that can call parse_value on individual options.
        Use self.parse_value to parse only some options from a params dictionary

        Arguments:
            params (dict) -- Input dict to pull form
            param_names (str) -- Keys of dicitonary to parse and return as a dicitonary
                                Example value: 'x,y,z,cpw_width'

        Returns:
            Dictionary of the keys contained in `param_names` with values that are parsed.
        """
        return parse_options(params, param_names, variable_dict=self.variables)

    def add_connector_as_normal(self,
                      name: str,
                      start : np.ndarray,
                      end : np.ndarray,
                      width:float,
                      parent: Union[str, 'QComponent'],
                      flip: bool = False,
                      chip: str = 'main'):
        """Give the path points

        Arguments:
            name {str} -- [description]
            points {list} -- [description]
            parent {Union[str,} -- [description]

        Keyword Arguments:
            flip {bool} -- [description] (default: {False})
            chip {str} -- [description] (default: {'main'})
        """

        if is_component(parent):
            parent = parent.name
        elif parent is None:
            parent = 'none'
        name = parent+'_'+name

        if not parent is 'none':
            self.components[parent].connectors.add(name)

        vec_normal = end - start
        vec_normal /= norm(vec_normal)
        if flip:
            vec_normal = -vec_normal

        self.connectors[name] = Dict(
            points=[], # TODO
            middle=end,
            normal=vec_normal,
            tangent=Vector.rotate(vec_normal, np.pi/2), #TODO: rotate other way sometimes?
            width=width,
            chip=chip,
            parent_name=parent
        )

    def add_connector(self,
                      name: str,
                      points: list,
                      parent: Union[str, 'QComponent'],
                      flip: bool = False,
                      chip: str = 'main'):
        """Add named connector to the design by creating a connector dicitoanry.

        Arguments:
            name {str} -- Name of connector
            points {list} -- List of two (x,y) points that define the connector
            parent {Union[str,} -- component or string or None. Will be converted to a
                                 string, which will the name of the component.

        Keyword Arguments:
            flip {bool} -- [description] (default: {False})
            chip {str} --  Optionally add options (default: {'main'})
        """
        if is_component(parent):
            parent = parent.name
        elif parent is None:
            parent = 'none'
        name = parent+'_'+name

        if not parent is 'none':
            self.components[parent].connectors.add(name)

        self.connectors[name] = make_connector(
            points, parent, flip=flip, chip=chip)

        # TODO: Add net?

    def get_connector(self, name: str):
        """Interface for components to get connector data

        Args:
            name (str): Name of the desired connector.

        Returns:
            (dict): Returns the data of the connector, see design_base.make_connector() for
                what those values are.
        """

        # For after switching to pandas, something like this?
        # return self.connectors.get(name).to_dict()

        return self.connectors[name]

    def update_component(self, component_name: str, dependencies: bool = True):
        """Update the component and any dependencies it may have.
        Mediator type function to update all children.

        Arguments:
            component_name {str} -- [description]

        Keyword Arguments:
            dependencies {bool} -- Do update all dependencies (default: {True})
        """

        # Get dependency graph

        # Remake components in order
        pass

    def get_design_name(self) -> str:
        """Get the name of the design from the metadata.

        Returns:
            str: name of design
        """
        if 'design_name' not in self.metadata:
            self.update_metadata({'design_name': 'Unnamed'})
        return self.metadata.design_name

    def set_design_name(self, name: str):
        """Set the name of the design in the metadata.

        Args:
            name (str) : Name of design
        """
        self.update_metadata({'design_name': name})

    def get_units(self):
        return self.template_options.units

####################################################################################
# Dependencies

    def add_dependency(self, parent: str, child: str):
        """Add a dependency between one component and another.

        Arguments:
            parent {str} -- The component on which the child depends
            child {str} -- The child cannot live without the parent.
        """
        # TODO: Should we allow bidirecitonal arrows as as flad in the graph?
        # Easier if we keep simply one-sided arrows
        # Note that we will have to handle renaming and deleting of components, etc.
        # Should we make a dependancy handler?
        # For now, let's table this, lower priority
        pass

    def remove_dependency(self, parent: str, child: str):
        """Remove a dependency between one component and another.

        Arguments:
            parent {str} -- The component on which the child depends
            child {str} -- The child cannot live without the parent.
        """


####################################################################################
###
# Connector
# TODO: Decide how to handle this.
#   Should this be a class?
#   Should we keep function here or just move into design?
# MAKE it so it has reference to who made it

def make_connector(points: list, parent_name: str, flip=False, chip='main'):
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
        parent_name=parent_name
    )
