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

class NeedsRenderer():
    """Just a way to centralize the selection and naming of the renderer.
    Could refactor code to transform this class into a class-less function.
    """
    def __init__(self, design: 'QDesign', renderer_name: str, *args, **kwargs):
        """Variables and method needed from all those Analysis types that need a renderer.

        Args:
            design (QDesign): The Metal design you are working on.
            renderer_name (str): A string corresponding to the name of the renderer you intend to use.
        """
        super().__init__(*args, **kwargs)

        # pointer to find renderers
        self.design = design

        # verify renderer existance
        self.renderer_name = renderer_name
        self.renderer = self.select_renderer(renderer_name)

    def select_renderer(self, renderer_name: str):
        """Makes sure the renderer has been registered with qiskit-metal. If yes it sets the analysis
        class variables to be able to reach it easily. Else it throws an error.

        Args:
            renderer_name (str): A string corresponding to the name of the renderer you intend to use.

        Returns:
            QRenderer: The renderer to be used in the analysis.
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

    def _initialize_renderer(self):
        """Starts the renderer by executing the routine of the selected renderer.
        """
        self.renderer.start()

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
            pathlib.WindowsPath: path to png formatted screenshot.
        """
        return self.renderer.save_screenshot()
