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

from ... import Dict


class QAnalysis(ABC):
    """Methods and variables that every analysis class should inherit
    Has default_setup = Dict() defined. Requires to define default_setup in all inheriting classes
    """
    default_setup = Dict(
    )
    """Default setup"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup = None

    @abstractmethod
    def run(self):
        """Abstract method. Must be implemented by the subclass.
        execute the full analysis. Needs to run after the setup steps
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

        Args:
            setup_dict (Dict): define the settings to change. The rest will be set to defaults
        """
        if isinstance(setup_dict, dict):
            self._setup = deepcopy(self.default_setup)
            self.setup_update(**setup_dict)
        else:
            print("The analysis setup has to be defined as a dictionary")

    def setup_update(self, **kwargs):
        """Intended to modify multiple setup settings at once, while retaining previous settings.
        If you intend to change a single setting, the better way is: `setup.setting1 = value`.
        """
        if not self._setup:
            self.setup = kwargs
        else:
            for k,v in kwargs.items():
                if k in self._setup:
                    self._setup[k]=v
            unsupported_keys = set(kwargs.keys()) - set(self._setup.keys())
            if unsupported_keys:
                print (f'the parameters {unsupported_keys} are unsupported, so they have been ignored')

