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
The base class of all QDesigns in Qiskit Metal.

@date: 2019
@author: Zlatko Minev, Thomas McConeky, ... (IBM)
"""

import importlib
from datetime import datetime
from typing import TYPE_CHECKING, Any
from typing import Dict as Dict_
from typing import Iterable, List, Union

import pandas as pd

from .. import Dict, logger
from ..config import DefaultMetalOptions, DefaultOptionsRenderer
from ..elements import QGeometryTables
from qiskit_metal.toolbox_metal.import_export import load_metal_design, save_metal
from qiskit_metal.toolbox_metal.parsing import parse_options, parse_value
from qiskit_metal.toolbox_metal.parsing import is_true
from qiskit_metal.toolbox_python.utility_functions import log_error_easy

from .interface_components import Components
from .net_info import QNet

from .. import config
if not config.is_building_docs():
    from qiskit_metal.renderers.renderer_gds.gds_renderer import QGDSRenderer
    from qiskit_metal.renderers.renderer_ansys.ansys_renderer import QAnsysRenderer


if TYPE_CHECKING:
    # For linting, avoids circular imports.
    from ..components.base.base import QComponent
    from ..renderers.renderer_base import QRenderer
    from ..renderers.renderer_gds.gds_renderer import QGDSRenderer
    from ..renderers.renderer_ansys.ansys_renderer import QAnsysRenderer


__all__ = ['QDesign']

#:ivar var1: initial value: par2


class QDesign():
    """ QDesign is the base class for Qiskit Metal Designs.
    A design is the most top-level object in all of Qiskit Metal.
    """

    # Dummy private attribute used to check if an instanciated object is
    # indeed a QDesign class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_design` to check.
    __i_am_design__ = True

    def __init__(self, metadata: dict = None,
                 overwrite_enabled: bool = False,
                 enable_renderers: bool = True):
        """Create a new Metal QDesign.

        Arguments:
            metadata (Dict): Dictionary of metadata (default: None).

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
                        For now, gds is enabled within design.
                        TODO:Use the list in config.renderers_to_load() to determine
                        which renderers to enable.

        """

        # _qcomponent_latest_assigned_id -- Used to keep a tally and ID of all components within an
        #                   instanziation of a design.
        #                   A component is added to a design by base._add_to_design with init of a comoponent.
        #                   During init of component, design class provides an unique id for each instance of
        #                   component being added to design.  Note, if a component is removed from the design,
        #                   the ID of removed component should not be used again.  However, if a component is
        #                   renamed with an unique name, then the ID should continute to be used.
        self._qcomponent_latest_assigned_id = 0

        # Dictionary that keeps the latest ID for each unique type of component
        self._qcomponent_latest_name_id = Dict()

        # Key attributes related to physical content of the design. These will be saved

        # Where components are actaully stored.
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

        self._qgeometry = QGeometryTables(self)

        # used for components, and renderers, TODO for QDesign
        self._template_options = DefaultMetalOptions()

        self.variables.update(self.template_options.qdesign.variables)

        # Can't really use this until DefaultOptionsRenderer.default_draw_substrate.color_plane
        # is resolved.
        # Presently, self._template_options holds the templates_options for each renderers.
        # key is the unique name of renderer.
        # Also, renderer_base.options holds the latest options for each instance of renderer.
        self._template_renderer_options = DefaultOptionsRenderer()  # use for renderer

        self._qnet = QNet()

        # Dict used to populate the columns of QGeometry table i.e. path, junction, poly etc.
        self.renderer_defaults_by_table = Dict()

        # Instantiate and register renderers to Qdesign.renderers
        self._renderers = Dict()
        if enable_renderers:
            self._start_renderers()

        # Take out of the QGeometryTables init(). Add add_renderer_extension() during renderer's init().
        # Need to add columns to Junction tables before create_tables().
        self._qgeometry.create_tables()

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
        new metadata dictionary. This will overwrite only the new keys
        that you pass in. All other keys will be unaffected.

        Args:
            new_metadata (dict): New metadatadata dict to update
        """
        self._metadata.update(new_metadata)

#########PROPERTIES##################################################
    # User should not access _components directly
    # TODO make interface with __getattr__ etc, magic methods
    # @property
    # def components(self) -> Dict_[int, 'QComponent']:
    #     '''
    #     Returns Dict object that keeps track of all Metal components in the design
    #     '''
    #     return self._components

    """     @property
    def pins(self):
        '''
        Return the Dict object that keeps track of all pins in the design.
        '''
        return
    """
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
    def renderers(self) -> Dict:
        '''
        Return a Dict of all the renderers registered within QDesign.
        '''

        return self._renderers

    @property
    def chips(self) -> Dict:
        '''
        Return a Dict of information regarding chip.
        '''
        return self._chips

    @property
    def template_renderer_options(self) -> Dict:
        '''
        Return default_renderer_options dictionary, which contain default options used in creating Metal renderer.
        '''
        return self._template_renderer_options.default_options

    @property
    def metadata(self) -> Dict:
        '''
        Return the metadata Dict object that keeps track of all metadata in the design.
        '''
        return self._metadata

    @property
    def qgeometry(self) -> QGeometryTables:
        '''
        Returns the QGeometryTables (Use for advanced users only)
        '''
        return self._qgeometry

    @property
    def qcomponent_latest_assigned_id(self) -> int:
        '''
        Return unique number for each instance.
        For user of the design class to know the lastest id assigned to QComponent.
        '''
        return self._qcomponent_latest_assigned_id

    @property
    def net_info(self) -> pd.core.frame.DataFrame:
        """Provides a copy of net_info table which holds all the connections, of pins, within a design.
        An advanced user can use methods within the class of design._qnet.
        Also, an advanced user can also directly edit the table at design._qnet._net_info.

        Returns:
            pd.core.frame.DataFrame: copy of net_info table.
        """
        return self._qnet._net_info.copy(deep=True)

#########Proxy properties##################################################

    def get_chip_size(self, chip_name: str = 'main'):
        """
        Utility function to return the chip size

        Args:
            chip_name (str): Returns the size of the given chip (Default: main)

        Raises:
            NotImplementedError: Code not written yet
        """
        raise NotImplementedError()

    def get_chip_z(self, chip_name: str = 'main'):
        """
        Utility function to return the z value of a chip

        Args:
            chip_name (str): Returns the size of the given chip (Default: main)

        Raises:
            NotImplementedError: Code not written yet
        """
        #raise NotImplementedError()
        # TODO: IMPORTANT
        return 0

    def get_chip_layer(self, chip_name: str = 'main') -> int:
        """Return the chip layer number for the ground plane.

        Args:
            chip_name (str, optional): User can overwrite name of chip. Defaults to 'main'.

        Returns:
            int: layer of ground plane
        """
        # TODO: Maybe return tuple for layer, datatype
        if chip_name in self.chips:
            if 'layer_ground_plane' in self.chips:
                return int(self.chips['layer_ground_plane'])
        return 0

#########General methods###################################################

    def rename_variable(self, old_key: str, new_key: str):
        """
        Renames a variable in the variables dictionary.
        Preserves order.

        Args:
            old_key (str): previous variable name
            new_key (str): new variable name
        """

        # TODO: Change this use components with both id and name.
        keys = list(self._variables.keys())
        values = list(self._variables.values())

        keys[keys.index(old_key)] = new_key
        self._variables = Dict(zip(keys, values))

    def delete_all_pins(self) -> 'QNet':
        """
        Clear all pins in the net_Info and update the pins in components.

        Returns:
            QNet: QNet with all pins removed
        """
        df_net_info = self._qnet._net_info
        for (index, netID, comp_id, pin_name) in df_net_info.itertuples():
            self._components[comp_id].pins[pin_name].net_id = 0

        # remove rows, but save column names
        self._qnet._net_info = self._qnet._net_info.iloc[0:0]
        return self._qnet

    def connect_pins(self, comp1_id: int, pin1_name: str, comp2_id: int, pin2_name: str) -> int:
        """
        Will generate an unique net_id and placed in a net_info table.
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
        net_id = self._qnet.add_pins_to_table(
            comp1_id, pin1_name, comp2_id, pin2_name)
        if net_id:
            # update the components to hold net_id
            self._components[comp1_id].pins[pin1_name].net_id = net_id
            self._components[comp2_id].pins[pin2_name].net_id = net_id
        else:
            logger.warning(
                f'NetId was not added for {comp1_id}, {pin1_name}, {comp2_id}, {pin2_name} and will not be added to components.')
        return net_id

    # NOTE: Think nothing is using this. Remove this if no-one complains.
    #       This is replaced by design.components.find_id()
    # def get_component(self, search_name: str) -> 'QComponent':
    #     """The design contains a dict of all the components, which is correlated to
    #     a net_list connections, and qgeometry table. The key of the components dict are
    #     unique integers.  This method will search through the dict to find the component with search_name.

    #     Args:
    #         search_name (str): Name of the component

    #     Returns:
    #         QComponent: A component within design with the name search_name.

    #     *Note:* If None is returned the component wass not found. A warning through logger.warning().

    #     *Note:* If multiple components have the same name, only the first component found in the search
    #     will be returned, ALONG with logger.warning().
    #     """
    #     alist = [(value.name, key)
    #              for key, value in self._components.items() if value.name == search_name]

    #     length = len(alist)
    #     if length == 1:
    #         return_component = self._components[alist[0][1]]
    #     elif length == 0:
    #         self.logger.warning(
    #             f'Name of component:{search_name} not found. Returned None')
    #         return_component = None
    #     else:
    #         self.logger.warning(
    #             f'Component:{search_name} is used multiple times, return the first component in list: (name, component_id) {str(alist)}')
    #         return_component = self._components[alist[0][1]]

    #     return return_component

    def all_component_names_id(self) -> list:
        """Get the text names and corresponding unique ID  of each component within this design.

        Returns:
            list[tuples]: Each tuple has the text name of component and UNIQUE integer ID for component.
        """
        # TODO: This seems slow to build new list, use builtin and /or map?
        alist = [(value.name, key)
                 for key, value in self._components.items()]
        return alist

    def _delete_all_pins_for_component(self, comp_id: int) -> set:
        """
        Remove component from self._qnet._net_info.

        Args:
            comp_id (int): Component ID for which pins are to be removed

        Returns:
            Set: Set of net IDs removed
        """
        all_net_id_removed = self._qnet.delete_all_pins_for_component(comp_id)

        # reset all pins to be 0 (zero),
        pins_dict = self._components[comp_id].pins
        for key, value in pins_dict.items():
            self._components[comp_id].pins[key].net_id = 0

        return all_net_id_removed

    def delete_all_components(self):
        '''
        Clear all components in the design dictionary.
        Also clears all pins and netlist.
        '''
        # clear all the dicitonaries and element tables.

        # Need to remove pin connections before clearing the components.
        self.delete_all_pins()
        self.name_to_id.clear()
        self._components.clear()
        # TODO: add element tables here
        self._qgeometry.clear_all_tables()
        # TODO: add dependency handling here

    def _get_new_qcomponent_id(self):
        '''
        Give new id that QComponent can use.

        Returns:
            int: ID of the qcomponent
        '''
        self._qcomponent_latest_assigned_id += 1
        return self._qcomponent_latest_assigned_id

    def _get_new_qcomponent_name_id(self, prefix):
        '''
        Give new id that an auto-named QComponent can use
        based on the type of the component.

        Returns:
            int: ID of the qcomponent
        '''
        if prefix in self._qcomponent_latest_name_id:
            self._qcomponent_latest_name_id[prefix] += 1
        else:
            self._qcomponent_latest_name_id[prefix] = 1

        return self._qcomponent_latest_name_id[prefix]

    def rebuild(self):  # remake_all_components
        """
        Remakes all components with their current parameters.
        """
        # TODO: there are some performance tricks here, we could just clear all element tables
        # and then skip the deletion of components qgeometry one by one
        # first clear all the
        # thne just make without the checks on existing
        # TODO: Handle error and print nice statemetns
        # try catch log_simple_error

        for name, obj in self._components.items():  # pylint: disable=unused-variable
            try:  # TODO: performace?
                obj.rebuild()  # should we call this build?
            except:
                print(f'ERORROR in building {name}')
                log_error_easy(
                    self.logger, post_text=f'\nERROR in rebuilding component "{name}={obj.name}"!\n')

    def reload_component(self, component_module_name: str, component_class_name: str):
        """
        Reload the module and class of a given component and update
        all class instances. (Advanced function.)

        Arguments:
            component_module_name (str): String name of the module name, such as
                `qiskit_metal.components.qubits.transmon_pocket`
            component_class_name (str): String name of the class name inside thst module,
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
                               self._components.values()):
            instance.__class__ = new_class

        # Alternative, but reload will say not in sys.path
        # self = gui.component_window.src_widgets[-1].ui.src_editor
        # spec = importlib.util.spec_from_file_location(self.component_module_name, self.component_module_path) # type: ModuleSpec
        # module = importlib.util.module_from_spec(spec) # type: module e.g.,
        # spec.loader.exec_module(module)
        # importlib.reload(module)

    def rename_component(self, component_id: int, new_component_name: str):
        """Rename component.  The component_id is expected.  However, if user
        passes a string for component_id, the method assumes the component_name
        was passed.  Then will look for the id using the component_name.

        Arguments:
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
            logger.warning(f'Called rename_component, component_id={component_id}, but component_id'
                           f' is not an integer, nor a string.')
            return -3

        if a_component_id in self._components:
            # Check if name is already being used.
            if new_component_name in self.name_to_id:
                logger.warning(f'Called design.rename_component, component_id({self.name_to_id[new_component_name]}'
                               f',  is already using {new_component_name}.')
                return -2

            # Do rename
            a_component = self._components[a_component_id]

            # Remove old name from cache, add new name
            self.name_to_id.pop(a_component.name, None)
            self.name_to_id[new_component_name] = a_component.id

            # do rename
            self._components[component_id]._name = new_component_name

            return True
        else:
            logger.warning(f'Called rename_component, component_id={component_id}, but component_id'
                           f' is not in design.components dictionary.')
            return -3

        return True

    def delete_component(self, component_name: str, force=False) -> bool:
        """Deletes component and pins attached to said component.

        If no component by that name is present, then just return True
        If component has dependencices return false and do not delete,
        unless force=True.

        Arguments:
            component_name (str): Name of component to delete
            force (bool): force delete component even if it has children (Default: False)

        Returns:
            bool: is there no such component
        """

        # Nothing to delete if name not in components
        if component_name not in self.name_to_id:
            self.logger.info(f'Called delete_component {component_name}, but such a '
                             f'component is not in the design cache dicitonary of components.')
            return True
        else:
            component_id = self.name_to_id[component_name]

        # check if components has dependencies
        #   if it does, then do not delete, unless force=true
        #       logger.error('Cannot delete component{component_name}. It has dependencies. ')
        #          return false
        #   if it does not then delete

        # Do delete component ruthelessly
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
                net_id_search = self._components[component_id].pins[pin_name].net_id
                df_subset_based_on_net_id = self.net_info[(
                    self.net_info['net_id'] == net_id_search)]
                delete_this_pin = df_subset_based_on_net_id[(
                    df_subset_based_on_net_id['component_id'] != component_id)]

                # If Component is connected to anything, meaning it is part of net_info table.
                if not delete_this_pin.empty:
                    edit_component = list(delete_this_pin['component_id'])[0]
                    edit_pin = list(delete_this_pin['pin_name'])[0]

                    if self._components[edit_component]:
                        if self._components[edit_component].pins[edit_pin]:
                            self._components[edit_component].pins[edit_pin].net_id = 0

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
            logger.warning(f'Called _delete_complete, component_id: {component_id}, '
                           'but component_id is not in design.components dictionary.')
            return_response = True
            return return_response

        return return_response


#########I/O###############################################################

    @classmethod
    def load_design(cls, path: str):
        """
        Load a Metal design from a saved Metal file.
        Will also update default dicitonaries.
        (Class method)

        Arguments:
            path (str): Path to saved Metal design.

        Returns:
            QDesign: Loaded metal design.
        """
        logger.warning("Loading is a beta feature.")
        design = load_metal_design(path)
        return design

    def save_design(self, path: str = None):
        """
        Save the metal design to a Metal file.
        If no path is given, then tried to use self.save_pathif it is set.

        Arguments:
            path (str): Path to save the design to.  (Default: None)

        Returns:
            bool: True = success; False = failure
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

        Arguments:
            value (str): string to parse *or*
            variable_dict (dict): dict pointer of variables

        Return:
            str, float, list, tuple, or ast eval: Parsed value

        Handled Inputs:

            Strings:
                Strings of numbers, numbers with units; e.g., '1', '1nm', '1 um'
                    Converts to int or float.
                    Some basic arithmatic is possible, see below.
                Strings of variables 'variable1'.
                    Variable interpertation will use string method
                    isidentifier 'variable1'.isidentifier()

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
                qiskit_metal.toolbox_metal.parsing
        """
        return parse_value(value, self.variables)

    def parse_options(self, params: dict, param_names: str) -> dict:
        """
        Extra utility function that can call parse_value on individual options.
        Use self.parse_value to parse only some options from a params dictionary.

        Arguments:
            params (dict): Input dict to pull form
            param_names (str): Keys of dicitonary to parse and return as a dicitonary.
                               Example value: 'x,y,z,cpw_width'

        Returns:
            dict: Dictionary of the keys contained in `param_names` with values that are parsed.
        """
        return parse_options(params, param_names, variable_dict=self.variables)

    def get_design_name(self) -> str:
        """
        Get the name of the design from the metadata.

        Returns:
            str: name of design
        """
        if 'design_name' not in self.metadata:
            self.update_metadata({'design_name': 'Unnamed'})
        return self.metadata.design_name

    def set_design_name(self, name: str):
        """
        Set the name of the design in the metadata.

        Args:
            name (str) : Name of design
        """
        self.update_metadata({'design_name': name})

    def get_units(self):
        """
        Gets the units of the design

        Returns:
            str: units
        """
        return self.template_options.units

####################################################################################
# TODO: Dependencies

    def add_dependency(self, parent: str, child: str):
        """
        Add a dependency between one component and another.

        Arguments:
            parent (str): The component on which the child depends.
            child (str): The child cannot live without the parent.
        """
        # TODO: add_dependency Should we allow bidirecitonal arrows as as flad in the graph?
        # Easier if we keep simply one-sided arrows
        # Note that we will have to handle renaming and deleting of components, etc.
        # Should we make a dependancy handler?
        # For now, let's table this, lower priority
        pass

    def remove_dependency(self, parent: str, child: str):
        """
        Remove a dependency between one component and another.

        Arguments:
            parent (str): The component on which the child depends.
            child (str): The child cannot live without the parent.
        """

        # TODO: remove_dependency
        pass

    def update_component(self, component_name: str, dependencies: bool = True):
        """
        Update the component and any dependencies it may have.
        Mediator type function to update all children.

        Arguments:
            component_name (str): Component name to update
            dependencies (bool): True to update all dependencies (Default: True)
        """

        # TODO: Get dependency graph

        # Remake components in order
        pass


######### Renderers ###############################################################


    def _start_renderers(self):
        """ For now, load only GDS.  However, will need to determine
        if mpl needs to be loaded, because it is conencted to GUI.


        # TODO: Use Dict() from config.renderers_to_load.
        # Determine how to load exactly.
        # Zkm: i don't think we should load all by default. Just MPL and GDS.
        # Not everyone needs HFSS. Should load that separatly.
        """
        # TODO: CHANGE TO LOOP OVER CONFIG. DO NOT HARD CODE @priti

        # Every renderer using QRender as base class will have method to get unique name.
        # Add columns to junction table in the element handler
        #unique_name = a_gds._get_unique_class_name()

        # register renderers here.
        self._renderers['gds'] = QGDSRenderer(self, initiate=True)
        self._renderers['ansys'] = QAnsysRenderer(self, initiate=True)

        for render_name, a_render in self._renderers.items():
            a_render.add_table_data_to_QDesign(a_render.name)

    def add_default_data_for_qgeometry_tables(self, table_name: str, renderer_name: str, column_name: str, column_value) -> set:
        """Populate the dict (self.renderer_defaults_by_table) which will hold the data until
        a component's get_template_options(design) is executed.

        Note that get_template_options(design) will populate the columns
        of QGeometry table i.e. path, junction, poly etc.

        Example of data format is:
        self.renderer_defaults_by_table[table_name][renderer_name][column_name] = column_value
        The type for default value placed in a table column is determined by populate_element_extenstions() on line:
        cls.element_extensions[table][col_name] = type(col_value)
        in renderer_base.py.

        Dict layout and examples within parenthesis:
            key: Only if need to add data to components, for each type of table (path, poly, or junction).
            value: Dict which has

                  keys: render_name (gds), value: Dict which has
                          keys: 'filename', value: (path/filename)
                  keys: render_name (hfss), value: Dict which has
                          keys: 'inductance', value: (inductance_value)

        Args:
            table_name (str): Table used within QGeometry tables i.e. path, poly, junction.
            renderer_name (str): The name of software to export QDesign, i.e. gds, ansys.
            column_name (str): The column name within the table, i.e. filename, inductance.
            column_value (Object): The type can vary based on column. The data is placed under column_name.

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

        if renderer_name not in self.renderer_defaults_by_table[table_name].keys():
            self.renderer_defaults_by_table[table_name][renderer_name] = Dict()
            status.add(2)

        if column_name not in self.renderer_defaults_by_table[table_name][renderer_name].keys():
            self.renderer_defaults_by_table[table_name][renderer_name][column_name] = column_value
            status.add(3)
            status.add(5)
        else:
            self.renderer_defaults_by_table[table_name][renderer_name][column_name] = column_value
            status.add(4)
            status.add(5)

        return status

    def get_list_of_tables_in_metadata(self, a_metadata: dict) -> list:
        """Look at the metadata dict to get list of tables the component uses.

        Args:
            a_metadata (dict): Use dict from gather_all_childern for metadata.

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
