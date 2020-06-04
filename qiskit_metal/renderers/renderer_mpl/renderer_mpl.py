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
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString

from ..renderer_base.renderer_gui_base import QRendererGui
from ...config import DEFAULT, Dict
from .toolbox_mpl import render

__all__ = ['QRendererMPL']

DEFAULT['renderer_mpl'] = Dict(
    annot_conectors=Dict(
        ofst=[0.025, 0.025],
        annotate_kw=dict(  # called by ax.annotate
            color='r',
            arrowprops=dict(color='r', shrink=0.1, width=0.05, headwidth=0.1)
        ),
        line_kw=dict(lw=2, c='r')
    ),
)


class QRendererMPL(QRendererGui):
    """
    Renderer for matplotlib in a GUI environment.

    TODO: How do we handle component selection, etc.
    """
    name = 'mpl'
    element_extensions = dict()

    def render_shapely(self, obj, kw=None):
        # TODO: simplify, specialize, and update this function
        # right now, this is just calling the V0.1 old style
        render(obj, ax=self.ax, kw= {} or kw)


    def render_pins(self):
        '''
        Plots all pins on the active axes. Draws the 1D line that
        represents the "port" of a pin point. These are referenced for smart placement
            of Metal components, such as when using functions like Metal_CPW_Connect.

        TODO: add some filter for sense of what components are visibile?
              or on what chip the pins are
        '''
        #can this be just one loop?
        for component_id in self.design.components.keys():
            for pin_name in self.design.components[component_id].pins.keys():
            
                line = LineString(self.design.components[component_id].pins[pin_name].points)

                self.render_shapely(line, kw=DEFAULT.annot_conectors.line_kw) #what is annot_conectors?

                self.ax.annotate(name, xy=conn.middle[:2], xytext=conn.middle +
                             np.array(DEFAULT.annot_conectors.ofst),
                             **DEFAULT.annot_conectors.annotate_kw)
