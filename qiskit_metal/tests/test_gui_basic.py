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
@author: Zlatko K. Minev, Jeremy D. Drysdale
"""

import unittest
import inspect

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
        pass

    def tearDown(self):
        """
        Tie any loose ends

        Args: None

        Returns: None
        """
        pass

    #pylint: disable-msg=broad-except
    def test_gui_01_launch(self):
        """
        Test the functionality of launching the GUI
        01 added to the test name so it is the first GUI to launch

        Args: None

        Returns: None
        """
        try:
            design = designs.DesignPlanar()
            gui = MetalGUI(design)
            gui.autoscale()
        except Exception:
            my_name = inspect.stack()[0][3]
            self.fail(my_name + " threw an exception.  GUI failure")

    #pylint: disable-msg=broad-except
    #pylint: disable-msg=unused-variable
    def test_gui_refresh_design(self):
        """
        Test the functionality of refrshing the GUI

        Args: None

        Returns: None
        """
        try:
            pass
            design = designs.DesignPlanar()
            q_1 = TransmonPocket(design, 'Q1', options=dict(pos_x='-1.5mm', pos_y='+0.0mm'))
            q_2 = TransmonPocket(design, 'Q2', options=dict(pos_x='+1.5mm', pos_y='+0.0mm'))
            q_3 = TransmonPocket(design, 'Q3', options=dict(pos_x='+0.0mm', pos_y='+1.0mm'))
            gui = MetalGUI(design)
            gui.autoscale()
            #gui.refresh_design()
        except Exception:
            my_name = inspect.stack()[0][3]
            self.fail(my_name + " threw an exception.  GUI failure")

    #pylint: disable-msg=broad-except
    #pylint: disable-msg=unused-variable
    def test_gui_rebuild(self):
        """
        Test the functionality of rebuilding the GUI

        Args: None

        Returns: None
        """
        try:
            pass
            #design = designs.DesignPlanar()
            #q_1 = TransmonPocket(design, 'Q1', options=dict(pos_x='-1.5mm', pos_y='+0.0mm'))
            #q_2 = TransmonPocket(design, 'Q2', options=dict(pos_x='+1.5mm', pos_y='+0.0mm'))
            #q_3 = TransmonPocket(design, 'Q3', options=dict(pos_x='+0.0mm', pos_y='+1.0mm'))
            #gui = MetalGUI(design)
            #gui.autoscale()
            #gui.rebuild(False)
            #gui.rebuild(True)
        except Exception:
            my_name = inspect.stack()[0][3]
            self.fail(my_name + " threw an exception.  GUI failure")

if __name__ == '__main__':
    unittest.main(verbosity=2)
