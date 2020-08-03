# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
@auhtor: Zlatko Minev, ... (IBM)
@date: 2019
"""
import logging
from typing import TYPE_CHECKING
from typing import Dict as Dict_
from typing import List, Tuple, Union
from ... import Dict
from ...designs import QDesign, is_design
from ...elements import QGeometryTables

__all__ = ['QRenderer']


class QRenderer():
    """Abstract base class for all Renderers of Metal designs and their components and qgeometry.

    Handles:
        ::

            designs
                components
                    qgeometry
                        paths
                        polys
                chips

    """

    name = 'base'  # overwrite this!
    """name"""

    __loaded_renderers__ = set()
    __instantiated_renderers__ = dict()

    # overwrite this to add element extensions:  see ELEMENT_COLUMNS
    # should be dict of dict with keys as element type, which contain (name, dype) pairs
    # e.g. element_extensions = dict(
    #            base=dict(color=str, klayer=int),
    #            path=dict(thickness=float, material=str, perfectE=bool),
    #            poly=dict(thickness=float, material=str), )
    element_extensions = dict()
    """element extentions dictionary"""

    # TODO: To add: default parameters for the renderer for component element values.

    @classmethod
    def load(cls):
        """Load the renderer and register all its extensions.
        Only performed once.

        Once complete, the rendere is added to the class attribute
        '__loaded_renderers__' of QRenderer

        Returns:
            bool: True if success, otherwise throws an error.

        Raises:
            NotImplementedError: Function not written yet
        """

        # Check name
        name = cls.name

        if name in QRenderer.__loaded_renderers__:
            print(
                f'Warning: Renderer name={name}, class={cls} already loaded. Doing nothing.')

        # Add elemnet extensions
        # see docstring for QRenderer.element_extensions
        QGeometryTables.add_renderer_extension(
            cls.name, cls.element_extensions)

        # Add component extensions
        # to be used in the creation of default params for component qgeometry
        raise NotImplementedError()

        # Finish and register offically as ready to use.
        QRenderer.__loaded_renderers__.add(name)

        return True

    @staticmethod
    def get_renderer(name: str):
        """Returns an already loaded and instantiated renderer.

        Arguments:
            name (str): rendering name

        Returns:
            QRenderer: Renderer with the given name
        """
        if not name in QRenderer.__loaded_renderers__:
            print(
                'ERROR: The renderer {name} has not yet been loaded. Please use the load function!')

        if not name in QRenderer.__instantiated_renderers__:
            print(
                'ERROR: The renderer {name} has not yet been instantiated. Please instantiate the class!')

        return QRenderer.__instantiated_renderers__[name]

    def __init__(self, design: QDesign, initiate=True,  render_template: Dict = None, options: Dict = None):
        """
        Args:
            design (QDesign): The design
            initiate (bool): True to initiate the renderer (Default: True)
        """
        # TODO: check that the renderer has been loaded with load_renderer

        self.status = 'Not Init'

        assert is_design(design), "Erorr, for the design argument you must provide a\
                                   a child instance of Metal QDesign class."

        self._design = design
        self.initiated = False

        if initiate:
            self.initate()

        # Register as an instantiated renderer.
        QRenderer.__instantiated_renderers__[self.name] = self

        # Options
        self.options = self.gather_options(self, options, render_template)
        self.status = 'Init Completed'

    @property
    def design(self) -> 'QDesign':
        '''Return a reference to the parent design object'''
        return self._design

    @property
    def logger(self) -> logging.Logger:
        """Returns the logger"""
        return self._design.logger

    @classmethod
    def _gather_all_children_default_options(cls) -> Dict:
        """From the base class of QRenderer, traverse the child classes
        to gather the .default_options for each child class.

        Note: If keys are the same for a child and grandchild, the grandchild will 
        overwrite the child init method.

        Returns:
            Dict: Options from all children.
        """
        options_from_children = Dict()
        parents = inspect.getmro(cls)

        # QRenderer is not expected to have default_options dict to add to QRenderer class.
        for child in parents[len(parents)-2::-1]:
            # There is a developer agreement so the defaults for a renderer will be in a dict named default_options.
            if hasattr(child, 'default_options'):
                options_from_children = {
                    **options_from_children, **child.default_options}
        return options_from_children

    def gather_options(self, options: Dict = None, render_template: Dict = None) -> Dict:
        options = Dict()
        if cls.default_options:
            options.update(cls.default_options)

        if render_template:
            self.options.update(render_template)

        if options:
            self.options.update(options)

        return options

    def initate(self, re_initiate=False):
        '''
        Call any initiations steps required to be performed a single time before rendering,
        such as conneting to some API or COM, or importing the correct material libraries, etc.

        Overwrite `initate_renderer`

        Arguments:
            re_initiate (bool) : If False will only apply this function once.
                                 If True, will re-apply (Default: False)

        Returns:
            bool: was a re_initiation applied or not
        '''

        if not re_initiate:
            if self.initiated:
                return False

        self.initiated = True

        self._initate_renderer()

        return True

    def _initate_renderer(self):
        '''
        Call any initiations steps required to be performed a single time before rendering,
        such as conneting to some API or COM, or importing the correct material libraries, etc.

        Returns:
            bool: Always returns True
        '''
        return True

    def post_render(self):
        '''
        Any calls that one may want to make after a rendering is complete.
        '''

    def render_design(self):
        '''
        Renders all design chips and components.
        '''
        self.initate()
        self.render_chips()
        self.render_components()
        # ...

    def render_chips(self):
        '''
        Render all chips of the design.
        Calls render_chip for each chip.

        Raises:
            NotImplementedError: Function not written yet
        '''
        raise NotImplementedError()

    def render_chip(self, name):
        """Render the given chip

        Args:
            name (str): chip to render

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()

    def render_components(self, selection=None):
        '''
        Render all components of the design.
        If selection is none, then render all components.

        Args:
            selection (QComponent): component to render

        Raises:
            NotImplementedError: Function not written yet
        '''
        raise NotImplementedError()

    def render_component(self, component):
        """Render the specified component

        Args:
            component (QComponent): Component to render

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()

    def render_element(self, element):
        """Render the specified element

        Args:
            element (Element): element to render

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()
        # if isinstance(element, path):
        #    self.render_element_path(element)

        # elif isinstance(element, poly):
        #    self.render_element_poly(element)

        # else:
        #    self.logger.error('RENDERER ERROR: Unkown element {element}')

    def render_element_path(self, path):
        """Render an element path

        Args:
            path (str): Path to render

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()

    def render_element_poly(self, poly):
        """Render an element poly

        Args:
            poly (Poly): Poly to render

        Raises:
            NotImplementedError: Function not written yet
        """
        raise NotImplementedError()
