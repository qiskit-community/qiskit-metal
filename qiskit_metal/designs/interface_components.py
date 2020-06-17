
import importlib
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, TypeVar, Union, Dict as Dict_
from .. import logger
from ..components.base.base import QComponent

if TYPE_CHECKING:
    # For linting typechecking, import modules that can't be loaded here under normal conditions.
    # For example, I can't import QDesign, because it requires QComponent first. We have the
    # chicken and egg issue.
    from .design_base import QDesign


class Components:
    """This is a user interface for the design._components dict.  The keys are unique integers,
    however, this interface allows user to treat the keys as strings. 
    """

    def __init__(self, design: 'QDesign'):
        self._design = design
        self.logger = logger  # type: logging.Logger
        self.components = design._components
        self.name_list = list()
        self.name_list_idx = 0

    def __len__(self) -> int:
        """ Give number of components in design.

        Returns:
            int: Total number of components registered within the design.
        """
        return len(self.components)

    def find_id(self, name: str) -> int:
        """Find id of component.  The id is the key for a dict which holds all of the components within design.
            Assume the name is not used multiple times. If it is, the first search result will be used.

        Args:
            name (str): Text name of compnent.  The name is assumed to be unique.

        Returns:
            int: key to use in  _components
                 0 means the name is not in dict
        """
        all_names = [(value.name, key)
                     for (key, value) in self.components.items()]
        search_result = [
            item for item in all_names if name == item[0]]
        length = len(search_result)
        if (length == 1):
            # Good, we found a single component match.
            return search_result[0][1]
        elif (length == 0):
            # Name not in dict.
            self.logger.warning(
                f'In Components.find_id(), the name={name} is not used in design._components ')
            return 0

        elif (length > 1):
            # Really unfortunate, the dict has multiple coponents with same name, use the first search result.
            self.logger.warning(
                f'In Components.find_id(), the name={name} is used multiple times in design._components.  Returning the key, for QComponent, with lowest id.')
            return search_result[0][1]

    # def is_name_used(self, new_name: str) -> int:
    #     """Check to see if name being used in components.

    #      Returns:
    #          int -- Results:
    #      Returns:
    #         int: 0 if does not exist
    #         component-id of component which is already using the name.
    #     """

    #     all_names = [(value.name, key)
    #                  for (key, value) in self.components.items()]
    #     search_result = [
    #         item for item in all_names if new_name == item[0]]
    #     if len(search_result) != 0:
    #         self.logger.warning(
    #             f'Called interface_components, component_id({search_result[0][0]}, id={search_result[0][1]}) is already using name={new_name}.')
    #         return search_result[0][1]
    #     else:
    #         return 0

    def __getitem__(self, name: str) -> 'QComponent':
        """Get the QComponent based on string name vs the unique id of QComponent.

        Args:
            name (str): Name of component.

        Returns:
            QComponent: Class which describes the component.
        """
        component_id = self.find_id(name)
        if component_id:
            return self.components[component_id]
        else:
            self.logger.warning(
                f'In Components.__getitem__, name={name} is not registered in the design class. Return None for QComponent.')
            return None

    def __setitem__(self, name: str, value: 'QComponent'):
        """Replace QComponent for an existing name. Use this at your own risk.
        There are netids used for pins within a component.  The netids are used in
        the net_info table and elements tables.

        Args:
            name (str): Name of QComponent.  If not in design._components, then will be added to dict.
                                             If in dict, the value(QComponent) will replace existing QComponent.
            value (QComponent): [description]
        """
        if not isinstance(value, QComponent):
            self.logger.warning(
                f'The value is NOT a QComponent.  Nothing has been assigned to name={name}')
            return

        component_id = self.find_id(name)
        if component_id:
            self.logger.debug(
                f'The name={name} already exists in design._components.  A component_id={component_id} will be replaced.')
            self.components[component_id] = deepcopy(value)
        else:
            self.logger.warning(
                f'Usualy new components are added to design during init.  The name={name} is not in design._components, and added as a new component.')
            value.name = name
            value._add_to_design()

    # def __getattr__(self, name: str) -> 'QComponent':
    #     """Provide same behavior as __getitem__.

    #     Args:
    #         name (str): Name of component used to find the QComponent in desing._components dict, vs using unique int id.
    #     """

    #     pass
    #     # self.__getitem__(name)

    # def __setattr__(self, name: str, value: 'QComponent'):
    #     """Provide same behavior as __setitem__.

    #     Args:
    #         name (str): Name of component used to find the QComponent in desing._components dict, vs using unique int id.
    #         value (QComponent): Component with the name used in arguments.
    #     """
    #     pass
    #     #self.__setitem__(name, value)

    def __contains__(self, item: str) -> int:
        """Look for item in design._components in the value.

        Args:
            item (str): Name in the value of design._components.

        Returns:
            int: 0 if item is not in design._components.name
                 int which can be used as key for design._components[]
        """
        if not isinstance(item, str):
            self.logger.warning(f'Search with string in this object.')
            return 0

        return self.find_id(item)

    # def __delitem__(self, name: str):
    #     """Will delete component from design class along with deleting the net_info and element tables.

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

        return str(self._design._components.__repr__(self))

    #     #     def __repr__(slef):
    #     #         # make sure to define repreentation for print purpose
    #     #         # Why every calss needs one?  https://dbader.org/blog/python-repr-vs-str
    #     #         return str(self.__actual_place_I_store_components__.give_me_repr())

    def __dir__(self) -> List:
        """Provide all the names in design._components.

        Returns:
            list: List of all the names used in design._components.
        """
        all_names = [(value.name)
                     for (key, value) in self.components.items()]
        return all_names

        #     def __dir__(self):
        #         # For autocompletion
        #         return list(self.__get_dict__().keys())

    def __iter__(self) -> iter:
        """Give iterator for design._components

        Returns:
            iter: for design._components , the keys are unique intergers, value is QComponent.
        """
        # return iter(self._design._components)
        self.name_list = [(value.name, key)
                          for (key, value) in self.components.items()]
        self.name_list_idx = 0
        return iter(self._design._components)

    def __next__(self):
        if (len(self.components) == 0):
            raise StopIteration

        rtn_key = self.name_list[self.name_list_idx][0]  # string

        true_key = self.name_list[self.name_list_idx][1]  # int
        rtn_value = self._design._components[true_key]  # QComponent
        self.name_list_idx += 1
        return (rtn_key, rtn_value)

    #     pass

        #     #     def __iter__(self):
        #     #         """
        #     #         This method is called when an iterator is required for a container.
        #     #         This method should return a new iterator object that can iterate over
        #     #         all the objects in the container. For mappings, it should iterate over
        #     #         the keys of the container.
        #     #         Iterator objects also need to implement this method; they are required
        #     #         to return themselves. For more information on iterator objects, see
        #     #         Iterator Types.
        #     #         """
        #     # #     #### Down the line for serializaton and pickling. Skip for now
        #     # #     def __getstate__(self):
        #     # #         """
        #     # #         Serialize the object.
        #     # #         """
        #     # #         # something like
        #     # #         return self.__actual_place_I_store_components__.__getstate__()
        #     # #     def __setstate__(self, state):
        #     # #         """
        #     # #         Deserialize the object.
        #     # #         """
        #     # #         pass
