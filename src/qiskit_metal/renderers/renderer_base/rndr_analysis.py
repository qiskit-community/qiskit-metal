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

from qiskit_metal.renderers.renderer_base import QRenderer
from qiskit_metal import Dict
from abc import abstractmethod, ABC

from qiskit_metal.designs import QDesign, is_design

__all__ = ['QRendererAnalysis']


class QRendererAnalysis(QRenderer):
    """Abstract base class for all Renderers intended for Analysis.
    """

    def __init__(self, design: 'QDesign', initiate=False, options: Dict = None):
        """
        Args:
            design (QDesign): The design.
            initiate (bool): True to initiate the renderer (Default: False).
            settings (Dict, optional): Used to override default settings. Defaults to None.
        """
        super().__init__(design=design,
                         initiate=initiate,
                         render_options=options)

    @abstractmethod
    def initialized(self):
        """Abstract method. Must be implemented by the subclass.
        Is renderer ready to be used?
        Implementation must return boolean True if successful. False otherwise.
        """
        return True

    @abstractmethod
    def render_chips(self):
        """Abstract method. Must be implemented by the subclass.
        Render all chips of the design.
        Calls render_chip for each chip.
        """
        pass

    @abstractmethod
    def render_chip(self, name):
        """Abstract method. Must be implemented by the subclass.
        Render the given chip.

        Args:
            name (str): chip to render
        """
        pass

    @abstractmethod
    def render_components(self, selection=None):
        """Abstract method. Must be implemented by the subclass.
        Render all components of the design.
        If selection is none, then render all components.

        Args:
            selection (QComponent): Component to render.
        """
        pass

    @abstractmethod
    def render_component(self, component):
        """Abstract method. Must be implemented by the subclass.
        Render the specified component.

        Args:
            component (QComponent): Component to render.
        """
        pass

    @abstractmethod
    def render_element(self, element):
        """Abstract method. Must be implemented by the subclass.
        Render the specified element

        Args:
            element (Element): Element to render.
        """
        pass
        # if isinstance(element, path):
        #    self.render_element_path(element)

        # elif isinstance(element, poly):
        #    self.render_element_poly(element)

        # else:
        #    self.logger.error('RENDERER ERROR: Unkown element {element}')

    @abstractmethod
    def render_element_path(self, path):
        """Abstract method. Must be implemented by the subclass.
        Render an element path.

        Args:
            path (str): Path to render.
        """
        pass

    @abstractmethod
    def render_element_poly(self, poly):
        """Abstract method. Must be implemented by the subclass.
        Render an element poly.

        Args:
            poly (Poly): Poly to render.
        """
        pass

    @abstractmethod
    def save_screenshot(self, path: str = None, show: bool = True):
        """Save the screenshot.

        Args:
            path (str, optional): Path to save location.  Defaults to None.
            show (bool, optional): Whether or not to display the screenshot.  Defaults to True.

        Returns:
            pathlib.WindowsPath: path to png formatted screenshot. 
        """
        pass


# class Cap():
#     def
