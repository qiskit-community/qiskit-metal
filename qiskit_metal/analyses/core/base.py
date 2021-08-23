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

from abc import abstractmethod, ABC
import inspect
from typing import Any, Union

from copy import deepcopy
from qiskit_metal import logger, Dict
from qiskit_metal.analyses.sweep_and_optimize.sweeper import Sweeper


class QAnalysis(ABC):
    """`QAnalysis` is the core class from which all Metal analysis classes are derived.

    The class defines the user interface for working with analysis.

    For front-end user:
        * Manipulates the setup dictionary to fine-tune the analysis parameters.

    For creator user:
        * Creates a class that inherits this or the QSimulation classes.
        * Implements the `run` and `run_***` methods to define the analysis procedures.
        * Defines the methods to communicate with the QRenderers. (see QSimulation)
        * Defines default_setup, which describes the parameteric interface to the analysis class.

    Default Setup:
        Nested default setup parameters can be overwritten with the setup_update method,
        or directly by using the dot operator enabled by the Dict type.
    """

    default_setup = Dict()
    """Default setup."""

    data_labels = list()
    """Default data labels."""

    def __init__(self, *args, **kwargs):
        """Creates a new Analysis object with a setup derived from the default_setup Dict.
        """
        super().__init__(*args, **kwargs)
        self._setup, self._supported_data_labels = self._gather_from_all_children(
        )

        # first self.clear_data()
        self._variables = Dict()

        # Keep a reference to Sweeper class.
        self._sweeper = None

    def _initialize_sweep(self):
        """Create a new instance of Sweeper
        """
        self._sweeper = Sweeper(self)

    @property
    def logger(self):
        """Returns the logger."""
        return logger

    @abstractmethod
    def run(self, *args, **kwargs):
        """Abstract method. Must be implemented by the subclass.
        Use as an alias for the main analysis method. Call the main analysis method run_***().
        Subclass implementation of run() must:
        * always call the main analysis method(s) named `run_***()`.
        * never implement the analysis, which should be instead in the method run_***().

        `run_***()` must always call self.save_run_args(`*args`, `**kwargs`) to save the inputs.

        Example:

            ::

                def run(self, *args, **kwargs):
                    self.run_sim(*args, **kwargs)
                def run_sim(self, *args, **kwargs):
                    self.save_run_args(*args, **kwargs)
                    <......>

        Make sure the name of the method `run_***()` does not conflict with that of another
        QAnalysis subclass, in case you expect them to be both inherited from the same subclass.
        """

    def run_sweep(self, *args, **kwargs):
        """User requests sweeper based on arguments from
        Sweeper.run_sweep().
        """
        if not self._sweeper:
            self._initialize_sweep()

        all_sweep, return_code = self._sweeper.run_sweep(*args, **kwargs)
        return all_sweep, return_code

    def save_run_args(self, **kwargs):
        """Intended to be used to store the kwargs passed to the run() method,
        for repeatability and for later identification of the QAnalysis instance.
        """
        self._setup.run = None
        self._setup.run = Dict(kwargs)

    def set_data(self, data_name: str, data: Any):
        """Stores data in a structure for later retrieval.
        Could be output, intermediate or even input data.
        Current implementation uses Dict()

        Args:
            data_name (str): Label for the data. Used a storage key.
            data (Any): Free format
        """
        if data_name not in self._supported_data_labels:
            self.logger.warning(
                'No %s in the list of supported variables. The variable will still be added. '
                'However, make sure this was not a typo', {data_name})
        self._variables[data_name] = data

    def get_data(self, data_name: str = None):
        """Retrieves the analysis module data.
        Returns `None` if nothing is found.

        Args:
            data_name (str, optional): Label to query for data. If not specified, the
                entire dictionary is returned. Defaults to None.

        Returns:
            Any: The data associated with the label, or the entire list of labels and data.
        """
        if data_name is None:
            return self._variables
        return self._variables[data_name]

    def get_data_labels(self) -> list:
        """Retrieves the list of data labels currently set.
        Returns `None` if nothing is found.

        Returns:
            list: list of data names
        """
        return self._variables.keys()

    @property
    def supported_data(self):
        """Getter: Set that contains the names of the variables supported from the analysis.

        Returns:
            set: list of supported variable names.
        """
        return self._supported_data_labels

    def clear_data(self, data_name: Union[str, list] = None):
        """Clear data. Can optionally specify one or more labels to delete those labels and data.

        Args:
            data_name (Union[str, list], optional): Can list specific labels to clean.
                Defaults to None.
        """
        if data_name is None:
            self._variables = Dict()
        else:
            if isinstance(data_name, str):
                self._variables[data_name] = None
            else:
                for name in data_name:
                    if name in self._variables[name]:
                        del self._variables[name]

    def print_run_args(self):
        """Prints the args and kwargs that were used in the last run() of this Analysis instance.
        """
        print("This analysis object run with the following kwargs:\n"
              f"{self._setup.run}\n")

    @property
    def setup(self):
        """Getter: Dictionary intended to be used to modify the analysis behavior.

        Returns:
            Dict: Current setup.
        """
        return self._setup

    @setup.setter
    def setup(self, setup_dict):
        """Setter: Dictionary intended to be used to modify the analysis behavior. You can only
        pass to this method those settings that are already defined in the default_setup list.
        Non specified keys, will be assigned the default_setup value.

        Args:
            setup_dict (Dict): Define the settings to change. The rest will be set to defaults.
        """
        if isinstance(setup_dict, dict):
            # first reset the setup
            self._setup, _ = self._gather_from_all_children()
            # then apply specified variables
            self.setup_update(**setup_dict)
        else:
            print("The analysis setup has to be defined as a dictionary")

    def setup_update(self, section: str = None, **kwargs):
        """Intended to modify multiple setup settings at once, while retaining previous settings.
        If you intend to change a single setting, the better way is: `setup.setting1 = value`.

        Args:
            section (str): Setup section that contains the setup keys to update.
        """
        if section in self._setup or section is None:
            unsupported_keys = list()
            for k, v in kwargs.items():
                if section is None:
                    s = self._setup
                else:
                    s = self._setup[section]
                if k in s:
                    s[k] = v
                else:
                    unsupported_keys.append(k)
            if unsupported_keys:
                print(
                    f'the parameters {unsupported_keys} are unsupported, so they have been ignored'
                )
        else:
            print(
                f'the section {section} does not exist in this analysis setup')

    @classmethod
    def _gather_from_all_children(cls):
        """From the QAnalysis core class, traverse the child classes to
        gather the default_setup and data_labels for each child class.

        For default_setup: If the same key is found twice, the youngest child will be picked.

        Returns:
            (dict, set): dict = setup, set = supported_data_labels
        """
        setup_from_children = Dict()
        labels_from_children = set()
        parents = inspect.getmro(cls)

        # len-2: base.py is not expected to have default_setup and data_labels.
        for child in parents[len(parents) - 2::-1]:
            # The template default options are in the attribute `default_setup`.
            if hasattr(child, 'default_setup'):
                setup_from_children.update(deepcopy(child.default_setup))
            # The data_labels are in the attribute `data_labels`.
            if hasattr(child, 'data_labels'):
                labels_from_children.update(child.data_labels)

        return setup_from_children, labels_from_children
