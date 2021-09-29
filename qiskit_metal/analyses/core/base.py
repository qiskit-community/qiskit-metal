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
import numpy as np
import pandas as pd
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

    def set_data(self,
                 name: str,
                 value: Union[np.ndarray, pd.DataFrame, int, float],
                 value_unit: str,
                 index_names: list = None,
                 index_values: list = None,
                 index_units: list = None):
        """Stores data in a structure for later retrieval.
        Could be output, intermediate or even input data.
        Current implementation uses Dict()

        Args:
            name (str): Label for the data. Used a storage key.
            value (np.ndarray, pd.DataFrame, int, float): data value(s) in one of these formats.
            value_unit (str): units of the value(s).
            index_names (list(int or str), optional): Use required only for dim(value)>1.
                Can be a list of strings or numbers. Strings shall be one for each dimension
                of the data. For example we would have 3 strings for a 3-dimensional numpy array.
                If the index_labels strings are already contains in the data structure (example,
                column names in pandas, or dtype labels in numpy), you can provide the number of
                the column that contains the index. Defaults to None.
            index_values (list(list(int or str)), optional): The actual index to associate with each
                element. Defaults to None.
            index_units (list(str), optional): If the index_values are numerical, they will need a
                unit to be specified. While if the index_values are strings, specify `None`.
                Defaults to None.

        .. code-block:: python
            # Always define units for all indexes. Here is a pandas example:
            name = "capacitance_matrix"
            values = pd.DataFrame()
                pass  ports   bus1_pad	bus2_pad	ground_plane	readout_pad
                1   bus1_pad	49.77794	-0.42560	-33.50861	-0.20494
                1   bus2_pad	-0.42560	54.01885	-35.77522	-1.01319
                1   ground_plane	-33.50861	-35.77522	237.69029	-36.55732
                1   readout_pad	-0.20494	-1.01319	-36.55732	59.92347
                2   bus1_pad	49.77794	-0.42560	-33.50861	-0.20494
                2   bus2_pad	-0.42560	54.01885	-35.77522	-1.01319
                2   ground_plane	-33.50861	-35.77522	237.69029	-36.55732
                2   readout_pad	-0.20494	-1.01319	-36.55732	59.92347
                .....
            index_names = [1,0] # since we specify 2 indices, but there is >1 columns left in the
                                 # dataframe, that will be assumed to be an additional dimension
            index_values = [1,0] # optional because we specified index_labels as column numbers.
            index_units = [None, None, None] # optional because the two indices have no units.
                                             # the third element can be added to specify the units
                                             # of the database data haders. Defaults None.

            # Here is a numpy example:
            name = "capacitance_matrix"
            values = np.array()
                [[[49.77794,  -0.42560,  -33.50861, -0.20494 ],
                  [-0.42560,  54.01885,  -35.77522, -1.01319 ],
                  [-33.50861, -35.77522, 237.69029, -36.55732],
                  [-0.20494,  -1.01319,  -36.55732, 59.92347 ]],
                 [[49.77794,  -0.42560,  -33.50861, -0.20494 ],
                  [-0.42560,  54.01885,  -35.77522, -1.01319 ],
                  [-33.50861, -35.77522, 237.69029, -36.55732],
                  [-0.20494,  -1.01319,  -36.55732, 59.92347 ]],
                .....]
            index_names = [ports, ports, pass]
            index_values = [[bus1_pad, bus2_pad, ground_plane, readout_pad_Q1],
                            [bus1_pad, bus2_pad, ground_plane, readout_pad_Q1],
                            [1,2,...]]
            index_units = [None, None, None] # optional because the two indices have no units.

        """
        if name not in self._supported_data_labels:
            self.logger.warning(
                'No %s in the list of supported variables. The variable will still be added and'
                ' you can access it thorugh get_data(), but it will not be used in the algorithms.'
                ' Please, make sure this was not a typo', {name})

        # break-up and store the data in simple form. Different treatment for different sources.
        new_data = Dict()
        new_data.value = value
        new_data.value_unit = value_unit
        new_data.index_names = index_names
        new_data.index_values = index_values
        new_data.index_units = index_units

        # TODO: will need to implement value_unit validation to be compatible with everything else.
        if isinstance(value, np.ndarray):
            # numpy array
            if len(np.shape(value)) == len(value) == 1:
                # single value - no need for index
                if any(elem is not None for elem in [index_names, index_values, index_units]):
                    self.logger.warning(
                        'You provided index information for non indexable data.'
                        ' Data is being saved as-is but you might want to revisit this.'
                        ' For reference, here the index information you provided:'
                        f' index_names={index_names},\nindex_values={index_values},'
                        f'\nindex_units={index_units}.')
            else:
                # data has one or more dimensions - needs index
                if any(elem is None for elem in [index_names, index_values, index_units]):
                    self.logger.warning(
                        f'You provided data with one or more dimensions (shape = {np.shape(value)})'
                        ' However you did not provide one or more of the index information.'
                        ' Data is being saved as-is but you will need to re-define it by running'
                        ' this command again, with all the index inputs.'
                        ' For reference, here the index information you provided:'
                        f' index_names={index_names},\nindex_values={index_values},'
                        f'\nindex_units={index_units}.')

        elif isinstance(value, pd.DataFrame):
            # pandas DataFrame
            if any(elem is None for elem in [index_names, index_units]):
                self.logger.warning(
                    f'You provided data without specifying the index. Please provide both the'
                    f' following: index_names={index_names},\nindex_units={index_units}'
                    ' (current values passed). Data is being saved as-is but will be'
                    ' overwritten when you run again this method.')
            elif len(index_values) is None:
                if any(not isinstance(elem, int) for elem in index_names):
                    self.logger.warning(
                        'You need to provide index_values for any index_name that is not '
                        ' represented as a column int number. Please correct and re-try.')
            else:
                for elem in index_names:
                    if isinstance(elem, int):
                        if len(value.columns) <= elem:
                            f'Index column is out of bound. You asked to use index column {index_names[0]}'
                            f' However, there is only {value.columns} columns in the data.'
                            ' Please correct your information and run again this method.')
                if len(index_names) == 1 and not isinstance(index_names[0], int):
                    self.logger.warning(
                        f'Your inputs are inconsistent. Please make sure your index_names provided data without specifying the index. Please provide both the'
                        f' following: index_names={index_names},\nindex_units={index_units}'
                        ' (current values passed). Data is being saved as-is but will be'
                        ' overwritten when you run again this method.')

        else:
            # numerical values or others
            pass # we already save as-is

        self._variables[name] = new_data

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
