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
"""
=================================================
Renderers (:mod:`qiskit_metal.renderers`)
=================================================

.. currentmodule:: qiskit_metal.renderers

.. _qrenderer:

Renderer Base
---------------

.. autosummary::
    :toctree: ../stubs/

    QRenderer
    QRendererGui
    QRendererAnalysis


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


GDS Renderer
---------------

.. autosummary::
    :toctree: ../stubs/

    QGDSRenderer
    Cheesing


Ansys Renderer
---------------

.. autosummary::
    :toctree: ../stubs/

    QAnsysRenderer
    QHFSSRenderer
    QQ3DRenderer
    QPyaedt
    QQ3DPyaedt
    QHFSSPyaedt
    QHFSSDrivenmodalPyaedt
    QHFSSEigenmodePyaedt



GMSH Renderer
---------------

.. autosummary::
    :toctree: ../stubs/

    QGmshRenderer
    Vec3DArray



"""

from .setup_default import setup_renderers

from .. import config
if config.is_building_docs():
    from .renderer_base.renderer_base import QRenderer
    from .renderer_base.renderer_gui_base import QRendererGui
    from .renderer_base.rndr_analysis import QRendererAnalysis

    from .renderer_gds.gds_renderer import QGDSRenderer
    from .renderer_gds.make_cheese import Cheesing

    from .renderer_mpl.mpl_canvas import PlotCanvas
    from .renderer_mpl.mpl_interaction import MplInteraction
    from .renderer_mpl.mpl_interaction import ZoomOnWheel
    from .renderer_mpl.mpl_interaction import PanAndZoom
    from .renderer_mpl.mpl_renderer import QMplRenderer
    from .renderer_mpl.extensions.animated_text import AnimatedText

    from .renderer_mpl import mpl_interaction
    from .renderer_mpl import mpl_toolbox

    from .renderer_ansys.ansys_renderer import QAnsysRenderer
    from .renderer_ansys.hfss_renderer import QHFSSRenderer
    from .renderer_ansys.q3d_renderer import QQ3DRenderer

    from .renderer_gmsh.gmsh_utils import Vec3DArray
    from .renderer_gmsh.gmsh_renderer import QGmshRenderer

    from .renderer_ansys_pyaedt.pyaedt_base import QPyaedt
    from .renderer_ansys_pyaedt.q3d_renderer_aedt import QQ3DPyaedt
    from .renderer_ansys_pyaedt.hfss_renderer_aedt import QHFSSPyaedt
    from .renderer_ansys_pyaedt.hfss_renderer_drivenmodal_aedt import QHFSSDrivenmodalPyaedt
    from .renderer_ansys_pyaedt.hfss_renderer_eigenmode_aedt import QHFSSEigenmodePyaedt
