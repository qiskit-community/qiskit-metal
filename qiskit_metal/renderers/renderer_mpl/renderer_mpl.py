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

from ..renderer_base import RendererGUIBase
from ...config import DEFAULT, Dict
from .toolbox_mpl import render_to_mpl

__all__ = ['RendererMPL']

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


class RendererMPL(RendererGUIBase):
    """
    Renderer for matplotlib.

    Should alow for some GUI interaction.

    TODO: How do we handle component selection, etc.
    """
    name = 'mpl'
    element_extensions = dict()

    def render_shapely(self, obj, kw=None):
        # TODO: simplify, specialize, and update this function
        # right now, this is just calling the V0.1 old style
        render_to_mpl(obj, ax=self.ax, kw= {} or kw)


    def render_connectors(self):
        '''
        Plots all connectors on the active axes. Draws the 1D line that
        represents the "port" of a connector point. These are referenced for smart placement
            of Metal components, such as when using functions like Metal_CPW_Connect.

        TODO: add some filter for sense of what components are visibile?
              or on what chip the connectors are
        '''

        for name, conn in self.design.connectors.items():

            line = LineString(conn.points)

            self.render_shapely(line, kw=DEFAULT.annot_conectors.line_kw)

            self.ax.annotate(name, xy=conn.middle[:2], xytext=conn.middle +
                             np.array(DEFAULT.annot_conectors.ofst),
                             **DEFAULT.annot_conectors.annotate_kw)
