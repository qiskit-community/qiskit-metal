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
"""Module containing Design interface components."""
from copy import deepcopy
from typing import TYPE_CHECKING, List, Union
#from typing import Any, Optional, TypeVar, Dict as Dict_, Iterable
from qiskit_metal.qlibrary.core._parsed_dynamic_attrs import is_ipython_magic
from qiskit_metal import logger
from qiskit_metal import config

if not config.is_building_docs():
    # Only import QComponent if the docs are NOT being built
    from ..qlibrary.core import QComponent

if TYPE_CHECKING:
    # For linting typechecking, import modules that can't be loaded here under normal conditions.
    # For example, I can't import QDesign, because it requires QComponent first. We have the
    # chicken and egg issue.
    from .design_base import QDesign


class Components:
    """This is a user interface for the design._components dict.

    The keys are unique integers, however, this interface allows user to
    treat the keys as strings.
    """

    def __init__(self, design: 'QDesign'):
        """Set up variables and logger which are used to emulate a dict which
        is referencing design._components.

        Args:
            design (QDesign): Need to have a Qdesign class so this class can
                              reference design._components.
        """
        self._design = design
        self.logger = logger  # type: logging.Logger
        self.components = design._components
        self.name_list = list()
        self.name_list_idx = 0

    def __len__(self) -> int:
        """Give number of components in design.

        Returns:
            int: Total number of components registered within the design.
        """
        return len(self.components)

    def get_list_ints(self, component_names: List[str]) -> List[int]:
        """Provide corresponding ints to be used as keys for dict:
        design._components, when list of names is provided.

        Args:
            component_names (List[str]): Names of components which user wants to know
                                         the int to be used as a key.

        Returns:
            List[int]: Corresponding ints that user can use as keys into design._components
        """
        component_ints = [self.find_id(item) for item in component_names]
        return component_ints

    def find_id(self, name: str, quiet: bool = False) -> int:
        """Find id of component.  The id is the key for a dict which holds all
        of the components within design.

        Args:
            name (str): Text name of component.  The name is assumed to be unique.
            quiet (bool): Allow warning messages to be generated.

        Returns:
            int: Key to use in  _components.
            If 0 is returned it means the name is not in dict.

        Raises:
            AttributeError: The given name is a magic method not in the dictionary
        """

        if name in self._design.name_to_id:
            component_id = self._design.name_to_id[name]
            return component_id
        if not is_ipython_magic(name):
            # Name not registered, not in cache for components' names.
            # IPython checking methods
            # https://github.com/jupyter/notebook/issues/2014
            if not quiet:
                self.logger.warning(
                    f'In Components.find_id(), the name={name} is not used in design._components'
                )
            return 0

        raise AttributeError(name)

    # def is_name_used(self, new_name: str) -> int:
    #     """Check to see if name being used in components.

    #      Args:
    #          new_name (str): name to check
    #
    #      Returns:
    #          int: If the name does not exist, 0 is returned, otherwise the
    #          component-id of component which is already using the name.
    #     """

    #     all_names = [(value.name, key)
    #                  for (key, value) in self.components.items()]
    #     search_result = [
    #         item for item in all_names if new_name == item[0]]
    #     if len(search_result) != 0:
    #         self.logger.warning(
    #             f'Called interface_components, '
    #             f' component_id({search_result[0][0]}, id={search_result[0][1]})'
    #             f' is already using name={new_name}.')
    #         return search_result[0][1]
    #     else:
    #         return 0

    def __getitem__(self,
                    name: str,
                    quiet: bool = False) -> Union[None, 'QComponent']:
        """Get the QComponent based on string name vs the unique id of
        QComponent.

        Args:
            name (str): Name of component.
            quiet (bool): Allow warning messages to be generated.

        Returns:
            QComponent: Class which describes the component.  None if
            name not found in design._components.

        Raises:
            AttributeError: The given name is a magic method not in the dictionary
        """
        component_id = int(self.find_id(name))
        if component_id:
            return self._design._components[component_id]
        else:
            # IPython checking methods
            # https://github.com/jupyter/notebook/issues/2014
            if not is_ipython_magic(name):
                if not quiet:
                    self.logger.warning(
                        f'In Components.__getitem__, name={name} is not '
                        f'registered in the design class. Return '
                        f'None for QComponent.')
                return None
            else:
                raise AttributeError(name)

            return None

        raise AttributeError(name)

    def __setitem__(self, name: str, value: 'QComponent'):
        """Replace QComponent for an existing name. Use this at your own risk.
        There are netids used for pins within a component.  The netids are used
        in the net_info table and qgeometry tables.

        Args:
            name (str): Name of QComponent.  If not in design._components,
                        then will be added to dict.
                        If in dict, the value(QComponent) will replace existing QComponent.
            value (QComponent): QComponent to add under the given name
        """
        if not isinstance(value, QComponent):
            self.logger.warning(
                f'The value is NOT a QComponent.  Nothing has been assigned to name={name}'
            )
            return

        component_id = self.find_id(name)
        if component_id:
            self.logger.debug(
                f'The name={name} already exists in design._components.  '
                f'A component_id={component_id} will be replaced.')
            self.components[component_id] = deepcopy(value)
        else:
            self.logger.warning(
                f'Usualy new components are added to design during init.  '
                f'The name={name} is not in design._components, and added as a new component.'
            )
            value.name = name
            value._add_to_design()

    def __getattr__(self, name: str) -> Union['QComponent', None]:
        """Provide same behavior as __getitem__.

        Args:
            name (str): Name of component used to find the QComponent in
                    design._components dict, vs using unique int id.

        Returns:
            QComponent: Class which describes the component. None if
                        name not found in design._components.
        """
        quiet = True
        return self.__getitem__(name, quiet)

    # def __setattr__(self, name: str, value: 'QComponent'):
    #     """Provide same behavior as __setitem__.

    #     Args:
    #         name (str): Name of component used to find the QComponent in
    #                   design._components dict, vs using unique int id.
    #         value (QComponent): Component with the name used in arguments.
    #     """
    #     pass
    #     #self.__setitem__(name, value)

    def __contains__(self, item: str) -> int:
        """Look for item in design._components in the value.

        Args:
            item (str): Name in the value of design._components.

        Returns:
            int: 0 if item is not in design._components.name otherwise an int which can be used as
                 key for design._components[]
        """
        if not isinstance(item, str):
            # self.logger.debug(f'Search with string in __contains__ {item}.')
            return 0
        quiet = True
        return self.find_id(item, quiet)

    # def __delitem__(self, name: str):
    #     """Will delete component from design class along with deleting the
    #      net_info and element tables.

    #     Args:
    #         name (str): Name of component to delete from design._components.
    #     """
    #     component_id = self.is_name_used(name)
    #     self._design.delete_component(component_id)

    def __repr__(self) -> str:
        """Print the design._component dict.

        Returns:
            str : String to print design._component dict.
        """

        return str(self._design._components.__repr__())

    #     #     def __repr__(self):
    #     #         # make sure to define representation for print purpose
    #     #         # Why every class needs one?  https://dbader.org/blog/python-repr-vs-str
    #     #         return str(self.__actual_place_I_store_components__.give_me_repr())

    def __dir__(self) -> List:
        """Provide all the names in design._components.

        Returns:
            list: List of all the names used in design._components.
        """
        all_names = [(value.name) for (key, value) in self.components.items()]
        return all_names

        #     def __dir__(self):
        #         # For autocompletion
        #         return list(self.__get_dict__().keys())

    def __iter__(self) -> iter:
        """Give iterator for design._components.

        Returns:
            iter: for design._components , the keys are names of the components.
        """
        for value in self._design._components.values():
            new_key = value.name
            yield new_key

    def items(self) -> list:
        """Get a list of all the items.

        Returns:
            list: List of (key, value) pairs.
        """
        all_items = [
            (value.name, value) for (key, value) in self.components.items()
        ]
        return all_items

    def values(self) -> list:
        """Get the list of all the values.

        Returns:
            list: List of just the values.
        """
        all_items = [value for (key, value) in self.components.items()]

        return all_items

    def keys(self) -> list:
        """Get the list of all the keys.

        Returns:
            list: List of just the keys.
        """
        all_items = [value.name for (key, value) in self.components.items()]

        return all_items

        #     #### Down the line for serialization and pickling. Skip for now
        #     def __getstate__(self):
        #         """
        #         Serialize the object.
        #         """
        #         # something like
        #         return self.__actual_place_I_store_components__.__getstate__()
        #     def __setstate__(self, state):
        #         """
        #         Deserialize the object.
        #         """
        #         pass
