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

#pylint: disable-msg=unnecessary-pass

"""
Qiskit Metal unit tests analyses functionality.

Test a planar deisgn and launching the GUI.

Created on  2020
@author: Zlatko K. Minev
"""

import unittest

from qiskit_metal import designs
from qiskit_metal import MetalGUI
from qiskit_metal.components.qubits.transmon_pocket import TransmonPocket
import time
import warnings


class TestGUIBasic(unittest.TestCase):
    """
    Unit test class
    """

    def setUp(self):
        """
        Setup unit test

        Args: None

        Returns: None
        """
        pass

    def tearDown(self):
        """
        Tie any loose ends

        Args: None

        Returns: None
        """
        pass

    def test_gui_01_launch(self):
        self.design = designs.DesignPlanar()
        self.gui = MetalGUI(self.design)
        self.gui.autoscale()
        
        
    def test_gui_refresh_design(self):
        self.design = designs.DesignPlanar()
        self.q1 = TransmonPocket(self.design, 'Q1', options = dict(pos_x='-1.5mm', pos_y='+0.0mm'))
        self.q2 = TransmonPocket(self.design, 'Q2', options = dict(pos_x='+1.5mm', pos_y='+0.0mm'))
        self.q3 = TransmonPocket(self.design, 'Q3', options = dict(pos_x='+0.0mm', pos_y='+1.0mm'))
        self.gui = MetalGUI(self.design)
        self.gui.autoscale()
        self.gui.refresh_design()

    def test_gui_rebuild(self):
        self.design = designs.DesignPlanar()
        self.q1 = TransmonPocket(self.design, 'Q1', options = dict(pos_x='-1.5mm', pos_y='+0.0mm'))
        self.q2 = TransmonPocket(self.design, 'Q2', options = dict(pos_x='+1.5mm', pos_y='+0.0mm'))
        self.q3 = TransmonPocket(self.design, 'Q3', options = dict(pos_x='+0.0mm', pos_y='+1.0mm'))
        self.gui = MetalGUI(self.design)
        self.gui.autoscale()
        self.gui.rebuild(False)
        self.gui.rebuild(True)

if __name__ == '__main__':
    unittest.main(verbosity=2)
