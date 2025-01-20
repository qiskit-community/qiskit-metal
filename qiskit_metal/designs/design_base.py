# -*- coding: utf-8 -*-
# pylint: disable=too-many-lines, cyclic-import
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
"""The base class of all QDesigns in Qiskit Metal."""

import importlib
#import inspect
#import os
from datetime import datetime
from typing import Any, Dict as Dict_, Iterable, List, TYPE_CHECKING, Union

import pandas as pd

from qiskit_metal.qgeometries.qgeometries_handler import QGeometryTables
from qiskit_metal.toolbox_metal.parsing import is_true, parse_options, parse_value
from qiskit_metal.designs.interface_components import Components
from qiskit_metal.designs.net_info import QNet
from qiskit_metal import Dict, config, logger
from qiskit_metal.config import DefaultMetalOptions, DefaultOptionsRenderer
from qiskit_metal.toolbox_metal.exceptions import QiskitMetalDesignError

if not config.is_building_docs():
    from qiskit_metal.toolbox_metal.import_export import load_metal_design, save_metal
    from qiskit_metal.toolbox_python._logging import LogStore

if TYPE_CHECKING:
    # For linting, avoids circular imports.
    from qiskit_metal.qlibrary.core.base import QComponent
    from qiskit_metal.renderers.renderer_base import QRenderer
    from qiskit_metal.renderers.renderer_gds.gds_renderer import QGDSRenderer

__all__ = ['QDesign']

#:ivar var1: initial value: par2


class QDesign():
    """QDesign is the base class for Qiskit Metal Designs.

    A design is the most top-level object in all of Qiskit Metal.
    """
    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    # Dummy private attribute used to check if an instantiated object is
    # indeed a QDesign class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_design` to check.
    __i_am_design__ = True

    def __init__(self,
                 metadata: dict = None,
                 overwrite_enabled: bool = False,
                 enable_renderers: bool = True):
        """Create a new Metal QDesign.

        Args:
            metadata (Dict): Dictionary of metadata.  Defaults to None.

            overwrite_enabled (bool): When True - If the string name, used for component, already
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

            enable_renderers: Enable the renderers during the init() of design.
                        The list in config.renderers_to_load() to determine
                        which renderers to enable.
        """

        # _qcomponent_latest_assigned_id -- Used to keep a tally and ID of all components within an
        # instantiation of a design.
        # A qcomponent is added to a design by base._add_to_design with init of a qcomponent.
        # During init of component, design class provides an unique id for each instance of
        # component being added to design.  Note, if a component is removed from the design,
        # the ID of removed component should not be used again.  However, if a component is
        # renamed with an unique name, then the ID should continute to be used.
        self._qcomponent_latest_assigned_id = 0

        # Dictionary that keeps the latest ID for each unique type of component
        self._qcomponent_latest_name_id = Dict()

        # Key attributes related to physical content of the design. These will be saved

        # Where components are actually stored.
        # i.e.  key=id and part of value (_components[id].name)
        self._components = Dict()

        # User-facing interface for user to view components by using name (str) for key access to
        # QComponents, instead of id (int).
        self.components = Components(self)

        self.overwrite_enabled = overwrite_enabled

        # Cache for component ids.  Hold the reverse of _components dict,
        self.name_to_id = Dict()

        self._variables = Dict()
        self._chips = Dict()

        self._metadata = self._init_metadata()
        if metadata:
            self.update_metadata(metadata)

        self.save_path = None  # type: str

        self.logger = logger  # type: logging.Logger
        self.build_logs = LogStore("Build Logs", 30)

        self._qgeometry = QGeometryTables(self)

        # Used for QComponents, and QRenderers
        self._template_options = DefaultMetalOptions()

        self.variables.update(self.template_options.qdesign.variables)

        # Can't really use this until DefaultOptionsRenderer.default_draw_substrate.color_plane
        # is resolved.
        # Presently, self._template_options holds the templates_options for each renderers.
        # key is the unique name of renderer.
        # Also, renderer_base.options holds the latest options for each instance
        # of renderer.
        self._template_renderer_options = DefaultOptionsRenderer(
        )  # use for renderer

        self._qnet = QNet()

        # Dict used to populate the columns of QGeometry table i.e. path,
        # junction, poly etc.
        self.renderer_defaults_by_table = Dict()

        # Instantiate and register renderers to Qdesign.renderers
        self._renderers = Dict()
        if enable_renderers:
            self._start_renderers()

        # Take out of the QGeometryTables init().
        # Add add_renderer_extension() during renderer's init().
        # Need to add columns to Junction tables before create_tables().
        self._qgeometry.create_tables()

        # Assign unique name to this design
        self.name = self._assign_name_design()

    def _assign_name_design(self, name: str = "Design") -> str:
        # TODO: make this name unique, for when we will have multiple designs
        return name

    @classmethod
    def _init_metadata(cls) -> Dict:
        """Initialize default metadata dictionary.

        Returns:
            Dict: default metadata dictionary
        """
        now = datetime.now()  # current date and time
        return Dict(design_name='my_design',
                    notes='',
                    time_created=now.strftime("%m/%d/%Y, %H:%M:%S"))

    def update_metadata(self, new_metadata: dict):
        """Update the metadata dictionary of the design with a new metadata
        dictionary. This will overwrite only the new keys that you pass in. All
        other keys will be unaffected.

        Args:
            new_metadata (dict): New metadatadata dict to update
        """
        self._metadata.update(new_metadata)

#########PROPERTIES##################################################

    @property
    def variables(self) -> Dict_[str, str]:
        """Return the Dict object that keeps track of all variables in the
        design."""
        return self._variables

    @property
    def template_options(self) -> Dict:
        """Return default_options dictionary, which contain default options
        used in creating Metal component, and in calling other drawing and key
        functions."""
        return self._template_options

    @property
    def renderers(self) -> Dict:
        """Return a Dict of all the renderers registered within QDesign."""

        return self._renderers

    @property
    def chips(self) -> Dict:
        """Return a Dict of information regarding chip."""
        return self._chips

    @property
    def template_renderer_options(self) -> Dict:
        """Return default_renderer_options dictionary, which contain default
        options used in creating Metal renderer."""
        return self._template_renderer_options.default_options

    @property
    def metadata(self) -> Dict:
        """Return the metadata Dict object that keeps track of all metadata in
        the design."""
        return self._metadata

    @property
    def qgeometry(self) -> 'QGeometryTables':
        """Returns the QGeometryTables (Use for advanced users only)"""
        return self._qgeometry

    @property
    def qnet(self) -> 'QNet':
        """Returns the QNet (Use for advanced users only)"""
        return self._qnet

    @property
    def qcomponent_latest_assigned_id(self) -> int:
        """Return unique number for each instance.

        For user of the design class to know the lastest id assigned to
        QComponent.
        """
        return self._qcomponent_latest_assigned_id

    @property
    def net_info(self) -> pd.DataFrame:
        """Provides a copy of net_info table which holds all the connections,
		of pins, within a design. An advanced user can use methods within the
		class of design._qnet. Also, an advanced user can also directly edit
		the table at design._qnet._net_info.

        Returns:
            pd.DataFrame: copy of net_info table.
        """
        # pylint: disable=protected-access
        return self._qnet._net_info.copy(deep=True)

#########Proxy properties##################################################

    def get_chip_size(self, chip_name: str = 'main') -> dict:
        """Utility function to get a dictionary containing chip dimensions
        (size and center).

        Args:
            chip_name (str): Name of the chip.

        Returns:
            dict: Dictionary of chip dimensions,
            including central coordinates and widths along x, y, and z axes.
        """
        return self._chips[chip_name]['size']

    def get_chip_z(self, chip_name: str = 'main') -> str:
        """Utility function to return the z value of a chip.

        Args:
            chip_name (str): Returns the size of the given chip.  Defaults to 'main'.

        Returns:
            str: String representation of the chip height.
        """
        chip_info = self.get_chip_size(chip_name)
        return chip_info['center_z']

    def get_chip_layer(self, chip_name: str = 'main') -> int:
        """Return the chip layer number for the ground plane.

        Args:
            chip_name (str, optional): User can overwrite name of chip.  Defaults to 'main'.

        Returns:
            int: Layer of ground plane
        """
        if chip_name in self.chips:
            if 'layer_ground_plane' in self.chips:
                return int(self.chips['layer_ground_plane'])
        return 0

#########General methods###################################################

    def rename_variable(self, old_key: str, new_key: str):
        """Renames a variable in the variables dictionary. Preserves order.

        Args:
            old_key (str): Previous variable name
            new_key (str): New variable name
        """

        keys = list(self._variables.keys())
        values = list(self._variables.values())

        keys[keys.index(old_key)] = new_key
        self._variables = Dict(zip(keys, values))

    def delete_all_pins(self) -> 'QNet':
        """Clear all pins in the net_Info and update the pins in components.

        Returns:
            QNet: QNet with all pins removed
        """
        # pylint: disable=protected-access
        df_net_info = self._qnet._net_info
        for (_, _, comp_id, pin_name) in df_net_info.itertuples():
            self._components[comp_id].pins[pin_name].net_id = 0

        # remove rows, but save column names
        self._qnet._net_info = self._qnet._net_info.iloc[0:0]
        return self._qnet

    def connect_pins(self, comp1_id: int, pin1_name: str, comp2_id: int,
                     pin2_name: str) -> int:
        """Will generate an unique net_id and placed in a net_info table.
        Update the components.pin_name with the net_id.

        Component's pin will know if pin is connected to another component,
        if there is a non-zero net_id.

        Args:
            comp1_id (int):  Unique id of component used for pin1_name.
            pin1_name (str): Name of pin in comp1_id.
            comp2_id (int): Unique id of component used for pin2_name.
            pin2_name (str): Name of pin in comp2_id.

        Returns:
            int: Unique net_id of connection used in the netlist.

        Note: If not added to netlist, the net_id will be 0 (zero).
        """
        net_id = 0
        net_id = self._qnet.add_pins_to_table(comp1_id, pin1_name, comp2_id,
                                              pin2_name)
        if net_id:
            # update the components to hold net_id
            self._components[comp1_id].pins[pin1_name].net_id = net_id
            self._components[comp2_id].pins[pin2_name].net_id = net_id
        else:
            logger.warning(
                f'NetId was not added for {comp1_id}, {pin1_name},'
                f' {comp2_id}, {pin2_name} and will not be added to components.'
            )
        return net_id

    #  This is replaced by design.components.find_id()
    # def get_component(self, search_name: str) -> 'QComponent':
    #     """The design contains a dict of all the components, which is correlated to
    #     a net_list connections, and qgeometry table. The key of the components dict are
    #     unique integers.  This method will search through the dict to find
    #     the component with search_name.

    #     Args:
    #         search_name (str): Name of the component

    #     Returns:
    #         QComponent: A component within design with the name search_name.

    #     *Note:* If None is returned the component was not found.
    #     A warning through logger.warning().

    #     *Note:* If multiple components have the same name, only the first component
    #     found in the search will be returned, ALONG with logger.warning().
    #     """
    #     a_list = [(value.name, key)
    #              for key, value in self._components.items() if value.name == search_name]

    #     length = len(a_list)
    #     if length == 1:
    #         return_component = self._components[a_list[0][1]]
    #     elif length == 0:
    #         self.logger.warning(
    #             f'Name of component:{search_name} not found. Returned None')
    #         return_component = None
    #     else:
    #         self.logger.warning(
    #             f'Component:{search_name} is used multiple times, '
    #             f'return the first component in list: (name, component_id) {str(a_list)}')
    #         return_component = self._components[a_list[0][1]]

    #     return return_component

    def all_component_names_id(self) -> list:
        """Get the text names and corresponding unique ID  of each component
        within this design.

        Returns:
            list[tuples]: Each tuple has the text name of component and
                        UNIQUE integer ID for component.
        """
        alist = [(value.name, key) for key, value in self._components.items()]
        return alist

    def _delete_all_pins_for_component(self, comp_id: int) -> set:
        """Remove component from self._qnet._net_info.

        Args:
            comp_id (int): Component ID for which pins are to be removed

        Returns:
            Set: Set of net IDs removed
        """
        all_net_id_removed = self._qnet.delete_all_pins_for_component(comp_id)

        # reset all pins to be 0 (zero),
        pins_dict = self._components[comp_id].pins
        for key, _ in pins_dict.items():
            self._components[comp_id].pins[key].net_id = 0

        return all_net_id_removed

    def delete_all_components(self):
        """Clear all components in the design dictionary.

        Also clears all pins and netlist.
        """
        # clear all the dictionaries and element tables.

        # Need to remove pin connections before clearing the components.
        self.delete_all_pins()
        self.name_to_id.clear()
        self._components.clear()

        self._qgeometry.clear_all_tables()

    def _get_new_qcomponent_id(self):
        """Give new id that QComponent can use.

        Returns:
            int: ID of the qcomponent
        """
        self._qcomponent_latest_assigned_id += 1
        return self._qcomponent_latest_assigned_id

    def _get_new_qcomponent_name_id(self, prefix):
        """Give new id that an auto-named QComponent can use based on the type
        of the component.

        Returns:
            int: ID of the qcomponent
        """
        if prefix in self._qcomponent_latest_name_id:
            self._qcomponent_latest_name_id[prefix] += 1
        else:
            self._qcomponent_latest_name_id[prefix] = 1

        return self._qcomponent_latest_name_id[prefix]

    def rebuild(self):  # remake_all_components
        """Remakes all components with their current parameters."""
        for _, obj in self._components.items():  # pylint: disable=unused-variable
            obj.rebuild()

    def rename_component(self, component_id: int, new_component_name: str):
        """Rename component.  The component_id is expected.  However, if user
        passes a string for component_id, the method assumes the component_name
        was passed.  Then will look for the id using the component_name.

        Args:
            component_id (int): id of component within design, can pass a string for component_name
            new_component_name (str): New name

        Returns:
            int: Results

        Results:
            1: True name is changed. (True)

            -1: Failed, new component name exists.

            -2: Failed, invalid new name; it is already being used by another component.

            -3: Failed, component_id does not exist.
        """
        # We are using component_id,
        # and assuming id is created as being unique.
        # We also want the string (name) to be unique.

        if isinstance(component_id, int):
            a_component_id = component_id
        elif isinstance(component_id, str):
            component_name = str(component_id)
            a_component_id = self.name_to_id[component_name]
            if a_component_id is None:
                return -3
        else:
            logger.warning(
                f'Called rename_component, component_id={component_id}, but component_id'
                f' is not an integer, nor a string.')
            return -3

        if a_component_id in self._components:
            # Check if name is already being used.
            if new_component_name in self.name_to_id:
                logger.warning(
                    f'Called design.rename_component,'
                    f' component_id({self.name_to_id[new_component_name]}'
                    f',  is already using {new_component_name}.')
                return -2

            # Do rename
            a_component = self._components[a_component_id]

            # Remove old name from cache, add new name
            self.name_to_id.pop(a_component.name, None)
            self.name_to_id[new_component_name] = a_component.id

            # do rename
            # pylint: disable=protected-access
            self._components[component_id]._name = new_component_name

            return True
        logger.warning(
            f'Called rename_component, component_id={component_id}, but component_id'
            f' is not in design.components dictionary.')
        return -3

    def delete_component(self,
                         component_name: str,
                         force: bool = False) -> bool:
        #pylint: disable=unused-argument
        """Deletes component and pins attached to said component.

        If no component by that name is present, then just return True
        If component has dependencices return false and do not delete,
        unless force=True.

        Args:
            component_name (str): Name of component to delete.
            force (bool): Force delete component even if it has children.
                          Defaults to False.

        Returns:
            bool: Is there no such component
        """

        # Nothing to delete if name not in components
        if component_name not in self.name_to_id:
            self.logger.info(
                f'Called delete_component {component_name}, but such a '
                f'component is not in the design cache dictionary of components.'
            )
            return True
        component_id = self.name_to_id[component_name]

        # check if components has dependencies
        #   if it does, then do not delete, unless force=true
        #       logger.error('Cannot delete component{component_name}. It has dependencies. ')
        #          return false
        #   if it does not then delete

        # Do delete component ruthlessly
        return self._delete_component(component_id)

    def _delete_component(self, component_id: int) -> bool:
        """Delete component without doing any checks.

        Args:
            component_id (int): ID of component to delete

        Returns:
            bool: True if component_id not in design.
        """
        # Remove pins - done inherently from deleting the component, though needs checking
        # if is on the net list or not

        return_response = False

        if component_id in self._components:
            # id in components dict
            # Need to remove pins before popping component.

            # For components to delete, which  connected to any other component,
            # need to set the net_id to zero of OTHER component
            #  before deleting from net_id table.
            for pin_name in self._components[component_id].pins:
                # make net_id be zero for every component which is connected to it.
                net_id_search = self._components[component_id].pins[
                    pin_name].net_id
                df_subset_based_on_net_id = self.net_info[(
                    self.net_info['net_id'] == net_id_search)]
                delete_this_pin = df_subset_based_on_net_id[(
                    df_subset_based_on_net_id['component_id'] != component_id)]

                # If Component is connected to anything, meaning it is part of net_info
                # table.
                if not delete_this_pin.empty:
                    edit_component = list(delete_this_pin['component_id'])[0]
                    edit_pin = list(delete_this_pin['pin_name'])[0]

                    if self._components[edit_component]:
                        if self._components[edit_component].pins[edit_pin]:
                            self._components[edit_component].pins[
                                edit_pin].net_id = 0

            # pins of component to delete.
            self._qnet.delete_all_pins_for_component(component_id)

            # Even though the qgeometry table has string for component_id, dataframe is
            # storing as an integer.
            self._qgeometry.delete_component_id(component_id)

            # Before poping component from design registry, remove name from cache
            component_name = self._components[component_id].name
            self.name_to_id.pop(component_name, None)

            # remove from design dict of components
            self._components.pop(component_id, None)
        else:
            # if not in components dict
            logger.warning(
                f'Called _delete_complete, component_id: {component_id}, '
                'but component_id is not in design.components dictionary.')
            return_response = True
            return return_response

        return return_response

    def copy_multiple_qcomponents(  # pylint: disable=dangerous-default-value
        self,
        original_qcomponents: list,
        new_component_names: list,
        all_options_superimpose: list = list()) -> Dict:
        """The lists in the arguments are all used in parallel.  If the length
        of original_qcomponents and new_component_names are not the same, no
        copies will be made and an empty Dict will be returned. The length of
        all_options_superimposes needs to be either empty or exactly the length
        of original_qcomponents, otherwise, an empty dict will be returned.

        Args:
            original_qcomponents (list): Must be a list of original QComponents.
            new_component_names (list): Must be a list of QComponent names.
            all_options_superimpose (list, optional): Must be list of dicts
              with options to superimpose on options from original_qcomponents.
              The list can be of both populated and empty dicts.
              Defaults to empty list().

        Returns:
            Dict: Number of keys will be the same length of original_qcomponent.
                Each key will be the new_component_name.
                Each value will be either a QComponent or None.
                If the copy did not happen, the value will be None, and the
                key will extracted from new_componet_names.
        """
        copied_info = dict()
        length = len(original_qcomponents)
        if length != len(new_component_names):
            return copied_info

        num_options = len(all_options_superimpose)

        if num_options > 0 and num_options != length:
            return copied_info

        for index, item in enumerate(original_qcomponents):
            if num_options > 0:
                a_copy = self.copy_qcomponent(item, new_component_names[index],
                                              all_options_superimpose[index])
            else:
                a_copy = self.copy_qcomponent(item, new_component_names[index])

            copied_info[new_component_names[index]] = a_copy

        return copied_info

    def copy_qcomponent(  # pylint: disable=dangerous-default-value, inconsistent-return-statements
        self,
        original_qcomponent: 'QComponent',
        new_component_name: str,
        options_superimpose: dict = dict()) -> Union['QComponent', None]:
        """Copy a qcomponent in QDesign and
        add it to QDesign._components using
        options_overwrite.

        Args:
            original_class (QComponent): The QComponent to copy.
            new_component_name (str): The name should not already
              be in QDesign, if it is, the copy fill fail.
            options_superimpose (dict): Can use different options
              for copied QComponent. Will start with the options
              in original QComponent, and then superimpose with
              options_superimpose. An example would be x and y locations.

        Returns:
            union['QComponent', None]: None if not copied, otherwise, a QComponent instance.
        """
        # overwrite original option with new options
        options = {**original_qcomponent.options, **options_superimpose}
        path_class_name = original_qcomponent.class_name
        module_path = path_class_name[:path_class_name.rfind('.')]
        class_name = path_class_name[path_class_name.rfind('.') + 1:]
        if new_component_name not in self.name_to_id:
            if importlib.util.find_spec(module_path):
                qcomponent_class = getattr(importlib.import_module(module_path),
                                           class_name, None)
                a_qcomponent = qcomponent_class(self,
                                                new_component_name,
                                                options=options)
                return a_qcomponent
            return None
        # else:
        #    #The new name is already in QDesign.
        #    return None

#########I/O###############################################################

    @classmethod
    def load_design(cls, path: str):
        """Load a Metal design from a saved Metal file. Will also update
        default dictionaries. (Class method).

        Args:
            path (str): Path to saved Metal design.

        Returns:
            QDesign: Loaded metal design.
        """
        logger.warning("Loading is a beta feature.")
        design = load_metal_design(path)
        return design

    def save_design(self, path: str = None):
        """Save the metal design to a Metal file. If no path is given, then
        tried to use self.save_path if it is set.

        Args:
            path (str): Path to save the design to.  Defaults to None.

        Returns:
            bool: True if successful; False if failure
        """

        self.logger.warning("Saving is a beta feature.")

        if path is None:
            if self.save_path is None:
                self.logger.error(
                    'Cannot save design since you did not provide a path to'
                    'save to yet. Once you save the design to a path, the then you call save '
                    'without an argument.')
            else:
                path = self.save_path

        self.save_path = str(path)

        # Do the actual saving
        self.logger.info(f'Saving design to {path}')
        result = save_metal(path, self)
        if result:
            self.logger.info('Saving successful.')
        else:
            self.logger.error('Saving failed.')

        return result

#########Creating Components##############################################

    def parse_value(self, value: Union[Any, List, Dict, Iterable]) -> Any:
        """Main parsing function. Parse a string, mappable (dict, Dict),
        iterable (list, tuple) to account for units conversion, some basic
        arithmetic, and design variables.

        Args:
            value (str): String to parse *or*
            variable_dict (dict): dict pointer of variables

        Return:
            str, float, list, tuple, or ast eval: Parsed value

        Handled Inputs:

            Strings:
                Strings of numbers, numbers with units; e.g., '1', '1nm', '1 um'
                    Converts to int or float.
                    Some basic arithmetic is possible, see below.
                Strings of variables 'variable1'.
                    Variable interpertation will use string method
                    isidentifier 'variable1'.isidentifier()

            Dictionaries:
                Returns ordered `Dict` with same key-value mappings, where the values have
                been subjected to parse_value.

            Iterables(list, tuple, ...):
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
                qiskit_metal.toolbox_metal.parsing
        """
        return parse_value(value, self.variables)

    def parse_options(self, params: dict, param_names: str) -> dict:
        """Extra utility function that can call parse_value on individual
        options. Use self.parse_value to parse only some options from a params
        dictionary.

        Args:
            params (dict): Input dict to pull form
            param_names (str): Keys of dictionary to parse and return as a dictionary.
                               Example value: 'x,y,z,cpw_width'

        Returns:
            dict: Dictionary of the keys contained in `param_names` with values that are parsed.
        """
        return parse_options(params, param_names, variable_dict=self.variables)

    def get_design_name(self) -> str:
        """Get the name of the design from the metadata.

        Returns:
            str: Name of design
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
        """Gets the units of the design.

        Returns:
            str: units
        """
        return self.template_options.units

####################################################################################
# Dependencies

    def add_dependency(self, parent: str, child: str):
        """Add a dependency between one component and another.

        Args:
            parent (str): The component on which the child depends.
            child (str): The child cannot live without the parent.
        """

    def remove_dependency(self, parent: str, child: str):
        """Remove a dependency between one component and another.

        Args:
            parent (str): The component on which the child depends.
            child (str): The child cannot live without the parent.
        """

    def update_component(self, component_name: str, dependencies: bool = True):
        """Update the component and any dependencies it may have. Mediator type
        function to update all children.

        Args:
            component_name (str): Component name to update
            dependencies (bool): True to update all dependencies.  Defaults to True.
        """
        # Get dependency graph
        # Remake components in order


######### Renderers ###############################################################

    def _start_renderers(self):
        """Start the renderers.

        First import the renderers identified in
        config.renderers_to_load. Then register them into QDesign.
        Finally populate self.renderer_defaults_by_table
        """

        for renderer_key, import_info in config.renderers_to_load.items():
            if 'path_name' in import_info:
                path_name = import_info.path_name
            else:
                self.logger.warning(
                    f'Renderer={renderer_key} is not registered in QDesign.  '
                    f'Looking for key="path_name" and value in config.renderers_to_load.'
                )
                continue

            if 'class_name' in import_info:
                class_name = import_info.class_name
            else:
                self.logger.warning(
                    f'Renderer={renderer_key} is not registered in QDesign.  '
                    f'Looking for key="class_name" and value in config.renderers_to_load.'
                )
                continue

            # check if module_name exists
            if importlib.util.find_spec(path_name):
                class_renderer = getattr(importlib.import_module(path_name),
                                         class_name, None)

                # check if class_name is in module
                if class_renderer is not None:
                    a_renderer = class_renderer(self, initiate=False)

                    # register renderers here.
                    self._renderers[renderer_key] = a_renderer
                else:
                    self.logger.warning(
                        f'Renderer={renderer_key} is not registered in QDesign.  '
                        f'The class_name={class_name} was not found.')
                    continue
            else:
                self.logger.warning(
                    f'Renderer={renderer_key} is not registered in QDesign.  '
                    f'The module_name={path_name} was not found.')
                continue

        for _, a_render in self._renderers.items():
            a_render.add_table_data_to_QDesign(a_render.name)

    def add_default_data_for_qgeometry_tables(self, table_name: str,
                                              renderer_name: str,
                                              column_name: str,
                                              column_value) -> set:
        """Populate the dict (self.renderer_defaults_by_table) which will hold
        the data until a component's get_template_options(design) is executed.

        Note that get_template_options(design) will populate the columns
        of QGeometry table i.e. path, junction, poly etc.

        Example of data format is:
        self.renderer_defaults_by_table[table_name][renderer_name][column_name] =
        column_value

        The type for default value placed in a table column is determined by
        populate_element_extentions() on line:
        cls.element_extensions[table][col_name] = type(col_value)
        in renderer_base.py.

        Dict layout and examples within parenthesis:
            key: Only if need to add data to components,
            for each type of table (path, poly, or junction).
            value: Dict which has

                  keys: render_name (gds), value: Dict which has
                          keys: 'filename', value: (path/filename)
                  keys: render_name (hfss), value: Dict which has
                          keys: 'inductance', value: (inductance_value)

        Args:
            table_name (str): Table used within QGeometry tables
                                i.e. path, poly, junction.
            renderer_name (str): The name of software to export QDesign,
                                i.e. gds, Ansys.
            column_name (str): The column name within the table,
                                i.e. filename, inductance.
            column_value (Object): The type can vary based on column.
                                The data is placed under column_name.

        Returns:
            set: Each integer in the set has different meanings.
                * 1 - added key for table_name
                * 2 - added key for renderer_name
                * 3 - added new key for column_name
                * 4 - since column_name already existed, column_value replaced previous column_value
                * 5 - Column value added
                * 6 - Expected str, got something else.
        """

        status = set()  # Empty Set

        if not isinstance(table_name, str):
            status.add(6)
            return status

        if not isinstance(renderer_name, str):
            status.add(6)
            return status

        if not isinstance(column_name, str):
            status.add(6)
            return status

        if table_name not in self.renderer_defaults_by_table.keys():
            self.renderer_defaults_by_table[table_name] = Dict()
            status.add(1)

        if renderer_name not in self.renderer_defaults_by_table[
                table_name].keys():
            self.renderer_defaults_by_table[table_name][renderer_name] = Dict()
            status.add(2)

        if column_name not in self.renderer_defaults_by_table[table_name][
                renderer_name].keys():
            self.renderer_defaults_by_table[table_name][renderer_name][
                column_name] = column_value
            status.add(3)
            status.add(5)
        else:
            self.renderer_defaults_by_table[table_name][renderer_name][
                column_name] = column_value
            status.add(4)
            status.add(5)

        return status

    def get_list_of_tables_in_metadata(self, a_metadata: dict) -> list:
        """Look at the metadata dict to get list of tables the component uses.

        Args:
            a_metadata (dict): Use dict from gather_all_children for metadata.

        Returns:
            list: List of tables, the component-developer, denoted as being used in metadata.
        """

        uses_table = list()
        for table_name in self.qgeometry.get_element_types():
            search = f'_qgeometry_table_{table_name}'
            table_status = search in a_metadata.keys()
            if table_status:
                if is_true(self.parse_value(a_metadata[search])):
                    uses_table.append(table_name)

        return uses_table

    def to_python_script(self, thin=True, printout: bool = False):
        """
        Generates a python script from current chip
        Args:
            printout (bool): Whether to print the script

        Returns:
            str: Python script for current chip
        """
        header = """
from qiskit_metal import designs, MetalGUI

design = designs.DesignPlanar()

gui = MetalGUI(design)
"""
        footer = """
gui.rebuild()
gui.autoscale()
        """
        # all imports at front
        # option -- only the options of the component that are different from the default options are specified.
        # vertically aligned dictionary (pretty print)
        imports = set()
        body = ""
        for comp_name in self.components:
            comp = self.components[comp_name]
            i, c = comp.to_script(thin=thin, is_part_of_chip=True)
            imports.add(i)
            body += c
            body += """
"""
        str_import = ""
        for i in imports:
            str_import += f"""
{i}
"""

        python_script = str_import + header + body + footer
        if printout:
            print(python_script)
        return python_script
