# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from copy import deepcopy
from abc import abstractmethod, ABC
import inspect

from ... import Dict, config, logger


class QAnalysis(ABC):
    """Methods and variables that every analysis class should inherit
    Has default_setup = Dict() defined. Requires to define default_setup in all inheriting classes
    """
    default_setup = Dict()
    """Default setup"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup = self._gather_all_children_setup()

    @property
    def logger(self):
        """Returns the logger."""
        return logger

    @abstractmethod
    def run(self):
        """Abstract method. Must be implemented by the subclass.
        Use as an alias for the main run method. Call the main run method run_***().
        Make sure the method names run_***() between two QAnalysis subclsses is unique,
        in case you expect them to be both inherited from the same subclass.
        """
        pass

    @property
    def setup(self):
        """Getter: Dictionary intended to be used to modify the analysis behavior

        Returns:
            Dict: current setup
        """
        return self._setup

    @setup.setter
    def setup(self, setup_dict):
        """Setter: Dictionary intended to be used to modify the analysis behavior. You can only
        pass to this method those settings that are already defined in the default_setup list.
        Non specified keys, will be assigned the default_setup value.

        Args:
            setup_dict (Dict): define the settings to change. The rest will be set to defaults
        """
        if isinstance(setup_dict, dict):
            # first reset the setup
            self._setup = self._gather_all_children_setup()
            # then apply specified variables
            self.setup_update(**setup_dict)
        else:
            print("The analysis setup has to be defined as a dictionary")

    def setup_update(self, section: str, **kwargs):
        """Intended to modify multiple setup settings at once, while retaining previous settings.
        If you intend to change a single setting, the better way is: `setup.setting1 = value`.

        Args:
            section (str): setup section that contains the setup keys to update
        """
        if section in self._setup:
            unsupported_keys = list()
            for k, v in kwargs.items():
                if k in self._setup[section]:
                    self._setup[section][k] = v
                else:
                    unsupported_keys.append(k)
            if unsupported_keys:
                print(
                    f'the parameters {unsupported_keys} are unsupported, so they have been ignored'
                )
        else:
            print(
                f'the section {section} does not exist in this analysis setup'
            )

    def _gather_all_children_setup(self):
        """From the QAnalysis core class, traverse the child classes to
        gather the default_setup for each child class.

        If the key is the same, the setup option of the youngest child is used.
        """

        setup_from_children = Dict()
        parents = inspect.getmro(self.__class__)

        # len-2: base.py is not expected to have default_setup dict to add to design class.
        for child in parents[len(parents) - 2::-1]:
            # The template default options are in a class dict attribute `default_setup`.
            if hasattr(child, 'default_setup'):
                setup_from_children.update(child.default_setup)

        return setup_from_children
