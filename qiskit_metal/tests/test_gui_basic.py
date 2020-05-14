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
        print('Setup')
        # Create an example design
        self.design = designs.DesignPlanar()

        self.q1 = TransmonPocket(self.design, 'Q1', options = dict(pos_x='-1.5mm', pos_y='+0.0mm'))
        self.q2 = TransmonPocket(self.design, 'Q2', options = dict(pos_x='+1.5mm', pos_y='+0.0mm'))
        self.q3 = TransmonPocket(self.design, 'Q3', options = dict(pos_x='+0.0mm', pos_y='+1.0mm'))

        # Launch GUI
        self.gui = MetalGUI(self.design)
        #TODO: handle check to make sure we set the design correctly


    def tearDown(self):
        """
        Tie any loose ends

        Args: None

        Returns: None
        """
        pass

    def test_step1(self):
        #TODO ...
        print('Step 1')
        self.gui.autoscale()

    def test_step2(self):
        #TODO ...
        print('Step 2')


if __name__ == '__main__':
    unittest.main(verbosity=2)
