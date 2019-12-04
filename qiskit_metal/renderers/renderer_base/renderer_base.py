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

from ...designs import DesignBase, is_design


class RendererBase():
    """Abstract base class for all Renderes of Metal designs.

    Handles:
        designs
            components
                elements
                    paths
                    polys
            chips
    """

    def __init__(self, design: DesignBase, initiate=True):
        assert is_design(design), "Erorr, for the design argument you must provide a\
                                   a child instance of Metal DesignBase class."

        self.design = design
        self.logger = self.design.logger
        self.initiated = False

        if initiate:
            self.initate_renderer()

    def initate_renderer(self, re_initiate=False):
        '''
        Call any initiations steps required to be performed a single time before rendering,
        such as conneting to some API or COM, or importing the correct material libraries, etc.

        Overwrite `initate_renderer`

        Optional Arguments:
        ------------------
            re_initiate (bool) : If False will only apply this function once.
                                 If True, will re-apply (default: False)

        Returns:
        -------------------
            bool : was a re_initiation applied or not
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
        self.initate_renderer()
        self.render_chips()
        self.render_components()
        # ...

    def render_chips(self):
        '''
        Render all chips of the design.
        Calls render_chip for each chip.
        '''
        raise NotImplementedError()

    def render_chip(self, name):
        raise NotImplementedError()

    def render_components(self):
        '''
        Render all components of the design.
        '''
        raise NotImplementedError()

    def render_component(self, component):
        raise NotImplementedError()

    def render_element(self, element):

        if isinstance(element, path):
            self.render_element_path(element)

        elif isinstance(element, poly):
            self.render_element_poly(element)

        else:
            self.logger.error('RENDERER ERROR: Unkown element {element}')

    def render_element_path(self, path):
        raise NotImplementedError()

    def render_element_poly(self, poly):
        raise NotImplementedError()
