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

#pylint: disable-msg=unnecessary-pass
#pylint: disable-msg=broad-except
"""Qiskit Metal unit tests analyses functionality.

Test a planar design and launching the GUI.
"""

import unittest
from qiskit_metal._gui.widgets.bases.dict_tree_base import BranchNode
from qiskit_metal._gui.widgets.bases.dict_tree_base import LeafNode


class TestGUIBasic(unittest.TestCase):
    """Unit test class."""

    def setUp(self):
        """Setup unit test."""
        pass

    def tearDown(self):
        """Tie any loose ends."""
        pass

    def test_instantiate_branch_node(self):
        """Test instantiation of BranchNode in dict_tree_base.py."""
        try:
            BranchNode('my_name')
        except Exception:
            message = "BranchNode instantiation failed"
            self.fail(message)

    def test_instantiate_leaf_node(self):
        """Test instantiation of LeafNode in dict_tree_base.py."""
        try:
            LeafNode('my_label')
        except Exception:
            message = "LeafNode instantiation failed"
            self.fail(message)


if __name__ == '__main__':
    unittest.main(verbosity=2)
