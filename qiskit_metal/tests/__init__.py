# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019-2020.
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
Tests (:mod:`qiskit_metal.tests`)
=================================================

.. currentmodule:: qiskit_metal.tests

Qiskit Metal main unit test functionality.

Created on Wed Apr 22 08:55:40 2020

@author: Jeremy D. Drysdale

Tests
---------------

.. autosummary::
    :toctree: ../stubs/

    TestAnalyses
    TestComponentInstantiation
    TestComponentOptions
    TestComponentFunctionality
    TestDefautOptions
    TestDesign
    TestDraw
    TestElements
    TestGUIBasic
    TestRenderers
    TestToolboxMetal
    TestToolboxPython


Support
---------------

.. autosummary::
    :toctree: ../stubs/

    AssertionsMixin

"""

from .. import config
if config.is_building_docs():
    from .assertions import AssertionsMixin
    from .test_analyses import TestAnalyses
    from .test_components_1_instantiate import TestComponentInstantiation
    from .test_components_2_options import TestComponentOptions
    from .test_components_3_functionality import TestComponentFunctionality
    from .test_default_options import TestDefautOptions
    from .test_designs import TestDesign
    from .test_draw import TestDraw
    from .test_elements import TestElements
    from .test_gui_basic import TestGUIBasic
    from .test_renderers import TestRenderers
    from .test_toolbox_metal import TestToolboxMetal
    from .test_toolbox_python import TestToolboxPython
