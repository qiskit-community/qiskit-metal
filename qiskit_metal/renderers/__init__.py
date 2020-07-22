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
=================================================
Renderers (:mod:`qiskit_metal.renderers`)
=================================================

.. currentmodule:: qiskit_metal.renderers

Created on Tue May 14 17:13:40 2019

@author: Zlatko

Renderer Base
---------------

.. autosummary::
    :toctree: ../stubs/

    QRenderer
    QRendererGui


MPL Renderer
---------------

.. autosummary::
    :toctree: ../stubs/

    PlotCanvas
    MplInteraction
    ZoomOnWheel
    PanAndZoom
    QMplRenderer
    AnimatedText


MPL Submodules
---------------

.. autosummary::
    :toctree: ../stubs/

    mpl_interaction
    mpl_toolbox


GDS Renderer
---------------

.. autosummary::
    :toctree: ../stubs/

    GDSRender


"""

from .setup_default import setup_renderers

from .. import config
if config.is_building_docs():
    from .renderer_base.renderer_base import QRenderer
    from .renderer_base.renderer_gui_base import QRendererGui
    from .renderer_mpl.mpl_canvas import PlotCanvas
    from .renderer_mpl.mpl_interaction import MplInteraction
    from .renderer_mpl.mpl_interaction import ZoomOnWheel
    from .renderer_mpl.mpl_interaction import PanAndZoom
    from .renderer_mpl.mpl_renderer import QMplRenderer
    from .renderer_mpl.extensions.animated_text import AnimatedText
    from .renderer_gds.gds_renderer import GDSRender

    from .renderer_mpl import mpl_interaction
    from .renderer_mpl import mpl_toolbox
