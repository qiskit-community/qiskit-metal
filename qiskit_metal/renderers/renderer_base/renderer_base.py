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
"""QRenderer base class."""

import logging
import inspect
from copy import deepcopy
from typing import TYPE_CHECKING
from typing import List, Tuple, Union, Any, Iterable
from typing import Dict as Dict_
from typing import List, Tuple, Union

from qiskit_metal.designs import is_design
from qiskit_metal.qgeometries import QGeometryTables

from ... import Dict

__all__ = ['QRenderer']

if TYPE_CHECKING:
    # For linting typechecking, import modules that can't be loaded here under normal conditions.
    # For example, I can't import QDesign, because it requires Qrenderer first. We have the
    # chicken and egg issue.
    from qiskit_metal.designs import QDesign


class QRenderer():
    """Abstract base class for all Renderers of Metal designs and their
    components and qgeometry.

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
    """Name"""

    __loaded_renderers__ = set()
    __instantiated_renderers__ = dict()

    # overwrite this to add element extensions:  see ELEMENT_COLUMNS
    # should be dict of dict with keys as element type, which contain (name, dype) pairs
    # e.g. element_extensions = dict(
    #            base=dict(color=str, klayer=int),
    #            path=dict(thickness=float, material=str, perfectE=bool),
    #            poly=dict(thickness=float, material=str), )
    element_extensions = dict()
    """Element extensions dictionary"""

    # TODO: To add: default parameters for the renderer for component element values.
    element_table_data = dict()

    @classmethod
    def load(cls):
        """Load the renderer and register all its extensions. Only performed
        once.

        Once complete, the renderer is added to the class attribute
        '__loaded_renderers__' of QRenderer

        Returns:
            bool: True if success, otherwise throws an error.
        """

        # Check name
        name = cls.name

        if name in QRenderer.__loaded_renderers__:
            pass
            # print(f'Warning: Renderer name={name}, class={cls} already loaded. Doing nothing.')

        cls.populate_element_extensions()

        # Add element extensions
        # see docstring for QRenderer.element_extensions
        QGeometryTables.add_renderer_extension(cls.name, cls.element_extensions)

        # Moved to init for each renderer.
        # Add component extensions

        # to be used in the creation of default params for component qgeometry
        #raise NotImplementedError()

        # Finish and register officially as ready to use.
        QRenderer.__loaded_renderers__.add(name)

        # Reset the table for the next QRenderer.
        for table in cls.element_table_data.keys():
            cls.element_extensions.pop(table, None)

        return True

    @classmethod
    def populate_element_extensions(cls):
        """Populate cls.element_extensions which will be used to create columns
        for tables in QGeometry tables.

        The structure of cls.element_table_data should be same as
        cls.element_extensions.
        """

        for table, a_dict in cls.element_table_data.items():
            cls.element_extensions[table] = dict()
            for col_name, col_value in a_dict.items():
                # type will only tell out about the base class, won't tell you about the inheritance.
                cls.element_extensions[table][col_name] = type(col_value)

    @staticmethod
    def get_renderer(name: str):
        """Returns an already loaded and instantiated renderer.

        Args:
            name (str): rendering name

        Returns:
            QRenderer: Renderer with the given name
        """
        if not name in QRenderer.__loaded_renderers__:
            print(
                'ERROR: The renderer {name} has not yet been loaded. Please use the load function!'
            )

        if not name in QRenderer.__instantiated_renderers__:
            print(
                'ERROR: The renderer {name} has not yet been instantiated. Please instantiate the class!'
            )

        return QRenderer.__instantiated_renderers__[name]

    def __init__(self,
                 design: 'QDesign',
                 initiate=True,
                 render_template: Dict = None,
                 render_options: Dict = None):
        """
        Args:
            design (QDesign): The design
            initiate (bool): True to initiate the renderer.  Defaults to True.
            render_template (Dict, optional): Typically used by GUI for template options for GDS.  Defaults to None.
            render_options (Dict, optional):  Used to override all options.  Defaults to None.
        """

        # TODO: check that the renderer has been loaded with load_renderer

        self.status = 'Not Init'

        assert is_design(
            design), "Erorr, for the design argument you must provide a\
                                   a child instance of Metal QDesign class."

        self._design = design
        self.initiated = False

        if initiate:
            self.initate()

        # Register as an instantiated renderer.
        QRenderer.__instantiated_renderers__[self.name] = self

        # Options
        self._options = Dict()
        self.update_options(render_options=render_options,
                            render_template=render_template)

        self.status = 'Init Completed'

    @property
    def options(self) -> Dict:
        """Options for the QRenderer."""
        return self._options

    @property
    def design(self) -> 'QDesign':
        """Return a reference to the parent design object."""
        return self._design

    @property
    def logger(self) -> logging.Logger:
        """Returns the logger."""
        return self._design.logger

    @classmethod
    def _gather_all_children_default_options(cls) -> Dict:
        """From the base class of QRenderer, traverse the child classes to
        gather the .default_options for each child class.

        Note: If keys are the same for a child and grandchild, the grandchild will
        overwrite the child init method.

        Returns:
            Dict: Options from all children.
        """
        options_from_children = Dict()
        parents = inspect.getmro(cls)

        # QRenderer is not expected to have default_options dict to add to QRenderer class.
        for child in parents[len(parents) - 2::-1]:
            # There is a developer agreement so the defaults for a renderer will be in a dict named default_options.
            if hasattr(child, 'default_options'):
                options_from_children = {
                    **options_from_children,
                    **child.default_options
                }
        return options_from_children

    @classmethod
    def _get_unique_class_name(cls) -> str:
        """Returns unique class name based on the module.

        Returns:
            str: Example: 'qiskit_metal.renders.renderer_gds.gds_renderer.QGDSRenderer'
        """
        return f'{cls.__module__}.{cls.__name__}'

    @classmethod
    def _register_class_with_design(cls, design: 'QDesign', template_key: str,
                                    render_template: Dict):
        """Init function to register a renderer class with the design when
        first instantiated. Registers the renderer's template options.

        Args:
            design (QDesign): The parent design
            template_key (str): Key to use
            render_template (dict): template of render to copy
        """
        # do not overwrite
        if template_key not in design.template_options:
            if not render_template:
                render_template = cls._gather_all_children_default_options()
            design.template_options[template_key] = deepcopy(render_template)

    @classmethod
    def get_template_options(cls,
                             design: 'QDesign',
                             render_template: Dict = None,
                             logger_: logging.Logger = None,
                             template_key: str = None) -> Dict:
        """Creates template options for the Metal QRenderer class required for
        the class to function, based on the design template; i.e., be created,
        made, and rendered. Provides the blank option structure required.

        The options can be extended by plugins, such as renderers.

        Args:
            design (QDesign): A design class.
            render_template (Dict, optional): Template options to overwrite the class ones. Defaults to None.
            logger_ (logging.Logger, optional): A logger for errors. Defaults to None.
            template_key (str, optional): The design.template_options key identifier. If None, then use
                _get_unique_class_name(). Defaults to None.

        Returns:
            Dict: Dictionary of renderer's default options based on design.template_options.
        """

        # get key for templates
        if template_key is None:
            template_key = cls._get_unique_class_name()

        if template_key not in design.template_options:
            # Registers the renderer's template options.
            cls._register_class_with_design(design, template_key,
                                            render_template)

        # Only log warning, if template_key not registered within design.
        if template_key not in design.template_options:
            logger_ = logger_ or design.logger
            if logger_:
                logger_.error(
                    f'ERROR in creating renderer {cls.__name__}!\nThe default '
                    f'options for the renderer class {cls.__name__} are missing'
                )

        # Specific object render template options
        options = deepcopy(Dict(design.template_options[template_key]))

        return options

    def parse_value(self, value: Union[Any, List, Dict, Iterable]) -> Any:
        """Same as design.parse_value. See design for help.

        Returns:
            object: Parsed value of input.
        """
        return self.design.parse_value(value)

    def update_options(self,
                       render_options: Dict = None,
                       render_template: Dict = None):
        """If template options has not been set for this renderer, then gather
        all the default options for children and add to design.  The GUI would
        use this to store the template options.

        Then give the template options to render
        to store in self.options.  Then user can over-ride the render_options.

        Args:
            render_options (Dict, optional): If user wants to over-ride the template
                                             options.  Defaults to None.
            render_template (Dict, optional): All the template options for each child.
                                              Defaults to None.
        """
        self.options.update(
            self.get_template_options(self.design,
                                      render_template=render_template))

        if render_options:
            self.options.update(render_options)

    def add_table_data_to_QDesign(self, class_name: str):
        """During init of renderer, this needs to happen. In particular, each
        renderer needs to update custom columns and values within QDesign.

        Args:
            class_name (str): Name from cls.name for each renderer.
        """
        status = set()
        if not isinstance(QRenderer.name, str):
            self.logger.warning(
                f'In add_table_data_to_QDesign, cls.str={QRenderer.name} is not a str.'
            )
            return

        for table, a_dict in self.element_table_data.items():
            for col_name, col_value in a_dict.items():
                status = self.design.add_default_data_for_qgeometry_tables(
                    table, class_name, col_name, col_value)
                if 5 not in status:
                    self.logger.warning(
                        f'col_value={col_value} not added to QDesign')

    def initate(self, re_initiate=False):
        """Call any initiations steps required to be performed a single time
        before rendering, such as connecting to some API or COM, or importing
        the correct material libraries, etc.

        Overwrite `initiate_renderer`.

        Args:
            re_initiate (bool) : If False will only apply this function once.
                                 If True, will re-apply.  Defaults to False.

        Returns:
            bool: was a re_initiation applied or not
        """

        if not re_initiate:
            if self.initiated:
                return False

        self.initiated = True

        self._initate_renderer()

        return True

    def get_unique_component_ids(
            self,
            highlight_qcomponents: Union[list,
                                         None] = None) -> Tuple[list, int]:
        """Confirm the list doesn't have names of components repeated. Confirm
        that the name of component exists in QDesign. If QDesign doesn't
        contain any component, or if all components in QDesign are found in
        highlight_qcomponents, return an empty list; otherwise return a list of
        unique components to be sent to the renderer. The second returned item, an
        integer, specifies which of these 3 cases applies.

        Args:
            highlight_qcomponents (Union[list, None], optional): Components to render. Defaults to None.

        Returns:
            Tuple[list, int]: Empty or partial list of components in QDesign.
        """
        highlight_qcomponents = highlight_qcomponents if highlight_qcomponents else []
        unique_qcomponents = set(highlight_qcomponents)
        for qcomp in unique_qcomponents:
            if qcomp not in self.design.name_to_id:
                self.logger.warning(
                    f'The component={qcomp} in highlight_qcomponents not'
                    ' in QDesign.')
                return [], 2  # Invalid
        if len(unique_qcomponents) in (0, len(self.design.components)):
            return [], 1  # Everything selected
        return [self.design.name_to_id[elt] for elt in unique_qcomponents
               ], 0  # Subset selected

    def _initate_renderer(self):
        """Call any initiations steps required to be performed a single time
        before rendering, such as connecting to some API or COM, or importing
        the correct material libraries, etc.

        Returns:
            bool: Always returns True
        """
        return True

    def post_render(self):
        """Any calls that one may want to make after a rendering is
        complete."""
        pass

    def render_design(self):
        """Renders all design chips and components."""
        self.initate()
        self.render_chips()
        self.render_components()
        # ...

    def render_chips(self, all_chips):
        """Render all chips of the design. Calls render_chip for each chip.

        Args:
            all_chips (list): All chip names to render.

        Raises:
            NotImplementedError: Function not written yet
        """
        # To avoid linting message in a subclass:  Method 'render_chips' is
        # abstract in class 'QRenderer' but is not overridden,
        # have this method do something.
        type(all_chips)

        raise NotImplementedError()

    def render_chip(self, name):
        """Render the given chip.

        Args:
            name (str): Chip to render.

        Raises:
            NotImplementedError: Function not written yet
        """
        # To avoid linting message in a subclass: Method 'render_chip' is
        # abstract in class 'QRenderer' but is not overridden,
        # have this method do something.
        type(name)

        raise NotImplementedError()

    def render_components(self, selection=None):
        """Render all components of the design.
        If selection is none, then render all components.

        Args:
            selection (QComponent): Component to render.

        Raises:
            NotImplementedError: Function not written yet
        """
        # To avoid linting message in a subclass: Method 'render_component'
        # is abstract in class 'QRenderer' but is not overridden,
        # have this method do something.
        type(selection)

        raise NotImplementedError()

    def render_component(self, qcomponent):
        """Render the specified qcomponent.

        Args:
            qcomponent (QComponent): QComponent to render.

        Raises:
            NotImplementedError: Function not written yet
        """
        # To avoid linting message in a subclass: Method 'render_component'
        # is abstract in class 'QRenderer' but is not overridden,
        # have this method do something.
        type(qcomponent)

        raise NotImplementedError()

    def render_element(self, element):
        """Render the specified element.

        Args:
            element (Element): Element to render

        Raises:
            NotImplementedError: Function not written yet
        """
        # To avoid linting message in a subclass: Method 'render_element' is
        # abstract in class 'QRenderer' but is not overridden,
        # have this method do something.
        type(element)

        raise NotImplementedError()
        # if isinstance(element, path):
        #    self.render_element_path(element)

        # elif isinstance(element, poly):
        #    self.render_element_poly(element)

        # else:
        #    self.logger.error('RENDERER ERROR: Unknown element {element}')

    def render_element_path(self, path):
        """Render an element path.

        Args:
            path (str): Path to render.

        Raises:
            NotImplementedError: Function not written yet
        """
        # To avoid linting message in a subclass:  Method 'render_element_path'
        # is abstract in class 'QRenderer' but is not overridden,
        # have this method do something.
        type(path)

        raise NotImplementedError()

    def render_element_poly(self, poly):
        """Render an element poly.

        Args:
            poly (Poly): Poly to render

        Raises:
            NotImplementedError: Function not written yet
        """
        # To avoid linting message in a subclass:  Method 'render_element_poly'
        # is abstract in class 'QRenderer' but is not overridden
        # have this method do something.
        type(poly)

        raise NotImplementedError()
