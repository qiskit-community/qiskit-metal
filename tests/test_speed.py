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

# pylint: disable-msg=unnecessary-pass
# pylint: disable-msg=broad-except
# pylint: disable-msg=too-many-public-methods
# pylint: disable-msg=import-error
"""Qiskit Metal unit tests for speed."""

import unittest
import time
from .custom_decorators import timeout


class TestSpeed(unittest.TestCase):
    """Unit test class."""

    def setUp(self):
        """Setup unit test."""
        pass

    def tearDown(self):
        """Tie any loose ends."""
        pass

    @timeout(5)
    def test_example_test(self):
        """
        Example test - Play with me to get comfortable with @timeout.
        """
        time.sleep(4)
        self.assertEqual(4, 2 + 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
