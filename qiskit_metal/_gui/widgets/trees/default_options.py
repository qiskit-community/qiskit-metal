# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
#

"""
@date: 2019
@author: Zlatko K. Minev
"""

from PyQt5 import QtGui
from .amazing_tree_dict import AmazingDictTreeZKM


class TreeDefaultOptions(AmazingDictTreeZKM):

    def __init__(self, parent,
                 content_dict=None,
                 gui=None,
                 **kwargs):
        """[Handles all the dictionary of all default objects
        can edit and expand and view]

        Arguments:
            parent {[type]} -- [description]

        Keyword Arguments:
            content_dict {[type]} -- [description] (default: {None})
            headers {list} -- [description] (default: {["Property", "Value"]})
            num_columns {int} -- [description] (default: {2})
            nameme {str} -- [description] (default: {'Root dictionary'})
        """
        self.gui = gui  # used to call remake all
        super().__init__(parent, content_dict=content_dict,
                         nameme='DEFAULT_OPTIONS dictionary',
                         logger=gui.logger, **kwargs)

    def style_item_dict(self, parent, key, value, parent_key_list, item):
        """Style the row item in the case of dict

        Arguments:
            parent {[type]} -- [description]
            key {[type]} -- [description]
            value {[type]} -- [description]
            parent_key_list {[type]} -- [description]
            item {[type]} -- [description]
        """
        super().style_item_dict(parent, key, value, parent_key_list, item)

        def style_me(color):
            item.setBackground(0,  QtGui.QColor(color))
        if len(parent_key_list) < 1:
            if key.startswith('draw_'):
                style_me('#c6e6d7')
            elif key.startswith('Metal_'):
                if '.' in key:
                    style_me('#DAE4EF')
                else:
                    style_me('#c6d5e6')
            elif key.startswith('Design_'):
                style_me('#e6d7c6')
            elif key.startswith('easy'):
                style_me('#c6d5e6')
