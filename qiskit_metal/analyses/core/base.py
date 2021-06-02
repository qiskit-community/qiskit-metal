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

from abc import abstractmethod, ABC
import inspect

from ... import Dict, logger


class QAnalysis(ABC):
    """`QAnalysis` is the core class from which all Metal analysis are derived.

    The class defines the user interface for working with analysis.

    For front-end user:
        * Manipulates the setup dictionary to fine-tune the analysis parameters.

    For creator user:
        * Creates a class that inherits this or the QAnalysisRenderer classes.
        * Implements the `run` and `run_***` methods to define the analysis procedures.
        * Defines the methods to communicate with the QRenderers. (see QAnalysisRenderer)
        * Defines default_setup, which describes the parameteric interface to the analysis class.

    Default Setup:
        Nested default setup parameters can be overwritten with the setup_update method,
        or directly by using the dot operator enabled by the Dict type.
    """

    default_setup = Dict()
    """Default setup"""

    def __init__(self, *args, **kwargs):
        """Creates a new Analysis object with a setup derived from the default_setup Dict.
        """
        super().__init__(*args, **kwargs)
        self._setup = self._gather_all_children_setup()

        # reference state
        self._run_kwargs = None

    @property
    def logger(self):
        """Returns the logger."""
        return logger

    @abstractmethod
    def run(self, *args, **kwargs):
        """Abstract method. Must be implemented by the subclass.
        Use as an alias for the main analysis method. Call the main analysis method run_***().
        Subclass implementation of run() must:
        * always call the main analysis method(s) named run_***().
        * never implement the analysis, which should be instead in the method run_***().
        run_***() must always call self.save_run_args(*args, **kwargs) to save the inputs.

        Example:
            def run(self, *args, **kwargs):
                self.run_sim(*args, **kwargs)
            def run_sim(self, *args, **kwargs):
                self.save_run_args(*args, **kwargs)
                <......>

        Make sure the name of the method run_***() does not conflict with that of another
        QAnalysis subclass, in case you expect them to be both inherited from the same subclass.
        """

    def save_run_args(self, **kwargs):
        """Intended to be used to store the kwargs passed to the run() method,
        for repeatibility and for later identification of the QAnalysis instance.
        """
        self._run_kwargs = kwargs

    def print_run_args(self):
        """Prints the args and kwargs that were used in the last run() of this Analysis instance.
        """
        print("This analysis object run with the following kwargs:\n"
              f"{self._run_kwargs}\n")

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
                f'the section {section} does not exist in this analysis setup')

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
