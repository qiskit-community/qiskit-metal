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

# pylint: disable-msg=unnecessary-pass
# pylint: disable-msg=broad-except
#pylint: disable-msg=too-many-public-methods
"""
Qiskit Metal unit tests for speed.
"""

import unittest
from qiskit_metal.tests.custom_decorators import timeout
from qiskit_metal import designs
from qiskit_metal import MetalGUI, Headings
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.interconnects.meandered import RouteMeander
import time


class TestSpeed(unittest.TestCase):
    """
    Unit test class
    """

    def setUp(self):
        """
        Setup unit test
        """
        pass

    def tearDown(self):
        """
        Tie any loose ends
        """
        pass

    @timeout(5)
    def test_example_test(self):
        """
        Example test - Play with me to get comfortable with @timeout
        """
        time.sleep(4)


if __name__ == '__main__':
    unittest.main(verbosity=2)
