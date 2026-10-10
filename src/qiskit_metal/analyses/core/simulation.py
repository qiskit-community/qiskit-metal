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

from abc import abstractmethod
from typing import Optional
from qiskit_metal.designs import QDesign
from qiskit_metal import Dict
from qiskit_metal import config

from qiskit_metal.analyses.core import QAnalysis
import importlib


class QSimulation(QAnalysis):
    """A subclass of `QAnalysis`, intended to standardize across all Analysis classes
    select and name renderers.

    Default Setup:
        * name (str): Name of simulation setup. Defaults to "Setup".

    Data Labels:
        * sim_setup_name (str): Name given to the current setup.
    """

    default_setup = Dict(name="Setup", reuse_selected_design=True, reuse_setup=True)
    """Default setup"""

    # supported labels for data generated from the simulation
    data_labels = ["sim_setup_name"]
    """Default data labels."""

    study_kind: str | None = None
    """The study this class runs: ``"eigenmode"``, ``"electrostatic"`` or
    ``"driven"``. Checked against the renderer's declared capabilities before a
    run (see ``analyses/simulation/capabilities.py``)."""

    def __init__(
        self,
        design: Optional["QDesign"] = None,
        renderer_name: str | None = None,
        *args,
        **kwargs,
    ):
        """Variables and method needed from all those Analysis types that need a renderer.

        Args:
            design (QDesign): The Metal design you are working on. Defaults to None.
            renderer_name (str): Name of the renderer you intend to use. Defaults to None.
        """
        super().__init__(*args, **kwargs)

        # pointer to find renderers
        self.design = design
        if self.design is None:
            self.logger.info(
                "You did not specify a design, so you will need to provide manual inputs"
                " for the analysis."
            )

        # verify renderer existence
        self.renderer_name = renderer_name
        self.renderer = None
        if self.renderer_name is None:
            self.logger.info(
                "You did not specify a renderer, so you are expected to manually provide "
                " the analysis input information."
            )
        else:
            self.renderer = self.select_renderer(renderer_name)

    def select_renderer(self, renderer_name: str):
        """Makes sure the renderer exists in qiskit-metal. If yes it sets the analysis
        class variables to be able to reach it easily. Else it raises an error.

        Args:
            renderer_name (str): Name of the renderer you intend to use.

        Returns:
            (QRenderer): The renderer to be used in the analysis.

        Raises:
            ValueError: If the renderer is unknown, misconfigured, or was not
                started for the design (usually because an optional dependency
                is not installed). The message names the available renderers.
        """
        if self.design is None:
            # we want to setup a renderer from scratch

            # renderer_ref is None if renderer_name does not exist
            renderer_ref = config.renderers_to_load.get(renderer_name)
            if not renderer_ref:
                self._raise_renderer_unavailable(
                    renderer_name, "it is not in config.renderers_to_load"
                )
            if not (renderer_ref.path_name and renderer_ref.class_name):
                self._raise_renderer_unavailable(
                    renderer_name,
                    "it is not properly configured in config.renderers_to_load "
                    "(it needs both a path_name and a class_name key)",
                )

            # if the path_name exists, grab the class
            if not importlib.util.find_spec(renderer_ref.path_name):
                self._raise_renderer_unavailable(
                    renderer_name, f"the module {renderer_ref.path_name} was not found"
                )
            class_renderer = getattr(
                importlib.import_module(renderer_ref.path_name),
                renderer_ref.class_name,
                None,
            )
            if class_renderer is None:
                self._raise_renderer_unavailable(
                    renderer_name,
                    f"the class {renderer_ref.class_name} was not found in "
                    f"{renderer_ref.path_name}",
                )
            # initiate=False, as for renderers registered with a design:
            # the connection is made by start() / run_sim(), not here.
            return class_renderer(None, initiate=False)

        # the renderer would have been already registered within the design object
        renderer = self.design.renderers.get(renderer_name)
        if not renderer:
            if config.renderers_to_load.get(renderer_name):
                reason = (
                    "it is configured but was not started for this design, usually "
                    "because an optional dependency is not installed (see the log "
                    "from creating the design; e.g. `pip install quantum-metal[ansys]` "
                    "for hfss / q3d)"
                )
            else:
                reason = "it is not in config.renderers_to_load"
            self._raise_renderer_unavailable(renderer_name, reason)
        return renderer

    def _raise_renderer_unavailable(self, renderer_name: str, reason: str):
        """Raise ``ValueError`` for a renderer that cannot be used (#1230)."""
        if self.design is not None:
            available = sorted(self.design.renderers.keys())
            where = "started for this design"
        else:
            available = sorted(config.renderers_to_load.keys())
            where = "configured"
        raise ValueError(
            f'Renderer "{renderer_name}" is not available for '
            f"{self.__class__.__name__}: {reason}. Renderers {where}: "
            f"{', '.join(available) or 'none'}."
        )

    def _check_backend(self):
        """Raise a clear error, before anything is rendered, when the renderer
        cannot run this class's study (e.g. an eigenmode study on ``"q3d"``).
        Renderers that declare no capabilities are not checked.

        Raises:
            BackendCapabilityError: naming the renderers that can run it.
        """
        if self.renderer_name is None or self.study_kind is None:
            return
        from qiskit_metal.analyses.simulation.capabilities import check_study

        registered = self.design.renderers.keys() if self.design is not None else ()
        check_study(
            self.renderer_name,
            self.study_kind,
            type(self).__name__,
            registered=registered,
            renderer=self.renderer,
        )

    def start(self):
        """Starts the renderer by executing the routine of the selected renderer."""
        self._initialize_renderer()

    def _initialize_renderer(self):
        """Starts the renderer by executing the routine of the selected renderer."""
        self.renderer.start()

    def _render(self, solution_type, vars_to_initialize, **design_selection) -> str:
        """Renders the design from qiskit metal into the selected renderer.
        First it decides the tentative name of the design. Then it runs the renderer method
        that executes the design rendering. It returns the final design name.

        Args:
            solution_type (str): The type of simulation solution to apply.
                Supported so far: eigenmode, capacitive, drivenmodal
            vars_to_initialize (Dict): The variables to initialize, i.e. Ljx, Cjx.

        Returns:
            (str): Final design name that the renderer used.
        """
        if self.design is None:
            return self.renderer.get_active_design_name()
        # need a default renderer-design name. Use the name of the metal-design.
        base_name = self.design.name
        # if a renderer-design name was provided as input to run(), use that as a base
        if "name" in design_selection:
            if design_selection["name"] is not None:
                base_name = design_selection["name"]
            del design_selection["name"]
        design_name = base_name + "_" + self.renderer_name
        design_name = self.renderer.execute_design(
            design_name,
            solution_type=solution_type,
            force_redraw=self.setup.reuse_selected_design,
            vars_to_initialize=vars_to_initialize,
            **design_selection,
        )
        return design_name

    def close(self):
        """Stops the renderer by executing the routine of the selected renderer."""
        self._close_renderer()

    def _close_renderer(self):
        """Stops the renderer by executing the routine of the selected renderer."""
        self.renderer.stop()

    @property
    def renderer_initialized(self):
        """Reports whether the renderer is initialized or stopped."""
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
        return self.get_data("sim_setup_name")

    @sim_setup_name.setter
    def sim_setup_name(self, data: str):
        """Setter

        Args:
            data (str): Name of the setup being executed.
        """
        if not isinstance(data, str):
            self.logger.warning(
                "Unsupported type %s. Only accepts str. Please try again.", {type(data)}
            )
            return
        self.set_data("sim_setup_name", data)
