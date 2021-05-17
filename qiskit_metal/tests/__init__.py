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

# pylint: disable-msg=relative-beyond-top-level
# pylint: disable-msg=import-error
"""Unit tests"""

from .. import config
if config.is_building_docs():
    from .assertions import AssertionsMixin
    from .test_analyses import TestAnalyses
    from .test_default_options import TestDefautOptions
    from .test_designs import TestDesign
    from .test_draw import TestDraw
    from .test_gui_basic import TestGUIBasic
    from .test_qgeometries import TestElements
    from .test_qlibrary_1_instantiate import TestComponentInstantiation
    from .test_qlibrary_2_options import TestComponentOptions
    from .test_qlibrary_3_functionality import TestComponentFunctionality
    from .test_renderers import TestRenderers
    from .test_speed import TestSpeed
    from .test_toolbox_metal import TestToolboxMetal
    from .test_toolbox_python import TestToolboxPython
