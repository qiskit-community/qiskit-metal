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

from abc import abstractmethod
from qiskit_metal.designs import QDesign  # pylint: disable=unused-import

from . import QAnalysis
from ... import Dict


class QAnalysisRenderer(QAnalysis):
    """A subclass of `QAnalysis`, intended to standardize across all Analysis classes
    select and name renderers.

    Default Setup:
        * name (str): Name of simulation setup. Defaults to "Setup".

    Data Labels:
        * sim_setup_name (str): Name given to the current setup.
    """

    default_setup = Dict(sim=Dict(name="Setup"))
    """Default setup"""

    # supported labels for data generated from the simulation
    data_labels = ['sim_setup_name']
    """Default data labels."""

    def __init__(self, design: 'QDesign', renderer_name: str, *args, **kwargs):
        """Variables and method needed from all those Analysis types that need a renderer.

        Args:
            design (QDesign): The Metal design you are working on.
            renderer_name (str): Name of the renderer you intend to use.
        """
        super().__init__(*args, **kwargs)

        # pointer to find renderers
        self.design = design

        # verify renderer existence
        self.renderer_name = renderer_name
        self.renderer = self.select_renderer(renderer_name)

    def select_renderer(self, renderer_name: str):
        """Makes sure the renderer has been registered with qiskit-metal. If yes it sets the
        analysis class variables to be able to reach it easily. Else it throws an error.

        Args:
            renderer_name (str): Name of the renderer you intend to use.

        Returns:
            (QRenderer): The renderer to be used in the analysis.
        """
        # did user select a usable renderer (registered)?
        try:
            renderer = self.design.renderers[renderer_name]
            if not renderer:
                self.design.logger.error(
                    f"Cannot find the renderer \"{renderer_name}\" registered with qiskit-metal"
                )
        except KeyError:
            self.design.logger.error(
                f"Cannot find a renderer {renderer_name} registered with qiskit-metal"
            )
        return renderer

    def start(self):
        """Starts the renderer by executing the routine of the selected renderer.
        """
        self._initialize_renderer()

    def _initialize_renderer(self):
        """Starts the renderer by executing the routine of the selected renderer.
        """
        self.renderer.start()

    def _render(self, solution_type, **design_selection) -> str:
        """Renders the design from qiskit metal into the selected renderer.
        First it decides the tentative name of the design. Then it runs the renderer method
        that executes the design rendering. It returns the final design name.

        Args:
            solution_type (str): The type of simulation solution to apply.
                Supported so far: eigenmode, capacitive, drivenmodal

        Returns:
            (str): Final design name that the renderer used.
        """
        base_name = self.design.name
        if "name" in design_selection:
            if design_selection["name"] is not None:
                base_name = design_selection["name"]
            del design_selection["name"]
        design_name = base_name + "_" + self.renderer_name
        design_name = self.renderer.execute_design(design_name,
                                                   solution_type=solution_type,
                                                   **design_selection)
        return design_name

    def close(self):
        """Stops the renderer by executing the routine of the selected renderer.
        """
        self._close_renderer()

    def _close_renderer(self):
        """Stops the renderer by executing the routine of the selected renderer.
        """
        self.renderer.stop()

    @property
    def renderer_initialized(self):
        """Reports whether the renderer is initialized or stopped.
        """
        return self.renderer.initialized

    def save_screenshot(self):
        """Saves the screenshot.

        Returns:
            (pathlib.WindowsPath): Path to png formatted screenshot.
        """
        return self.renderer.save_screenshot()

    def run(self, *args, **kwargs):
        """Alias for run_sim() necessary to implement super-class method, while
        preventing method name collision when sim and non-sim QAnalysis classes are inherited.
        """
        self.run_sim(*args, **kwargs)

    @abstractmethod
    def run_sim(self, *args, **kwargs):
        """Abstract method. Must be implemented by the subclass.
        Write in here the code to launch the simulations.
        You will be able to execute this with the alias run().
        """

    @property
    def sim_setup_name(self) -> str:
        """Getter

        Returns:
            str: Name of the setup being executed.
        """
        return self.get_data('sim_setup_name')

    @sim_setup_name.setter
    def sim_setup_name(self, data: str):
        """Setter

        Args:
            data (str): Name of the setup being executed.
        """
        if not isinstance(data, str):
            self.logger.warning(
                'Unsupported type %s. Only accepts str. Please try again.',
                {type(data)})
            return
        self.set_data('sim_setup_name', data)
