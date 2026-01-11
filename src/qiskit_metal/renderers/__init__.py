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
    :toctree: .

    QRenderer
    QRendererGui
    QRendererAnalysis


MPL Renderer
---------------

.. autosummary::
    :toctree: .

    PlotCanvas
    MplInteraction
    ZoomOnWheel
    PanAndZoom
    QMplRenderer
    AnimatedText


GDS Renderer
---------------

.. autosummary::
    :toctree: .

    QGDSRenderer
    Cheesing


Ansys Renderer
---------------

.. autosummary::
    :toctree: .

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
    :toctree: .

    QGmshRenderer
    Vec3DArray



"""

from qiskit_metal.renderers.setup_default import setup_renderers

from qiskit_metal import config
if config.is_building_docs():
    from qiskit_metal.renderers.renderer_base.renderer_base import QRenderer
    from qiskit_metal.renderers.renderer_base.renderer_gui_base import QRendererGui
    from qiskit_metal.renderers.renderer_base.rndr_analysis import QRendererAnalysis

    from qiskit_metal.renderers.renderer_gds.gds_renderer import QGDSRenderer
    from qiskit_metal.renderers.renderer_gds.make_cheese import Cheesing

    from qiskit_metal.renderers.renderer_mpl.mpl_canvas import PlotCanvas
    from qiskit_metal.renderers.renderer_mpl.mpl_interaction import MplInteraction
    from qiskit_metal.renderers.renderer_mpl.mpl_interaction import ZoomOnWheel
    from qiskit_metal.renderers.renderer_mpl.mpl_interaction import PanAndZoom
    from qiskit_metal.renderers.renderer_mpl.mpl_renderer import QMplRenderer
    from qiskit_metal.renderers.renderer_mpl.extensions.animated_text import AnimatedText

    from qiskit_metal.renderers.renderer_mpl import mpl_interaction
    from qiskit_metal.renderers.renderer_mpl import mpl_toolbox

    from qiskit_metal.renderers.renderer_ansys.ansys_renderer import QAnsysRenderer
    from qiskit_metal.renderers.renderer_ansys.hfss_renderer import QHFSSRenderer
    from qiskit_metal.renderers.renderer_ansys.q3d_renderer import QQ3DRenderer

    from qiskit_metal.renderers.renderer_gmsh.gmsh_utils import Vec3DArray
    from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

    from qiskit_metal.renderers.renderer_ansys_pyaedt.pyaedt_base import QPyaedt
    from qiskit_metal.renderers.renderer_ansys_pyaedt.q3d_renderer_aedt import QQ3DPyaedt
    from qiskit_metal.renderers.renderer_ansys_pyaedt.hfss_renderer_aedt import QHFSSPyaedt
    from qiskit_metal.renderers.renderer_ansys_pyaedt.hfss_renderer_drivenmodal_aedt import QHFSSDrivenmodalPyaedt
    from qiskit_metal.renderers.renderer_ansys_pyaedt.hfss_renderer_eigenmode_aedt import QHFSSEigenmodePyaedt
