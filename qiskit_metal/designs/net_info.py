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

"""[summary]

    Returns:
        [type] -- [description]
"""
from typing import Tuple
import pandas as pd
import logging


class QNet():
    """[summary]
    """

    def __init__(self):
        """ Hold the net information of all the USED pins within a design."""
        column_names=['net_id', 'component_id', 'pin_name']
        self._net_info = pd.DataFrame(column=column_names)

    def add_for_test(self):
    #for testing, need values in net_table to test.  
        self._net_info.append(pd.Series([2, 1, 'qubit'],index=_net_info.columns), ignore_index=True)
        self._net_info.append(pd.Series([2, 3, 'qstart'],index=_net_info.columns), ignore_index=True)
        self._net_info.append(pd.Series([1, 1, 'bus1'],index=_net_info.columns), ignore_index=True)
        self._net_info.append(pd.Series([1, 4, 'qstart'],index=_net_info.columns), ignore_index=True)
        self._net_info.append(pd.Series([3, 2, 'bus2'],index=_net_info.columns), ignore_index=True)
        self._net_info.append(pd.Series([3, 5, 'qend'],index=_net_info.columns), ignore_index=True)

    def add_net_table(self, item: tuple) -> bool:
        
        confirm = False
        
        # (i1, s2, i3, s4) = item

        # # confirm i1 and i3 are ints to represent unique component id.
        # # confirm s2 and s4 are string to represent pins on the component.

        # # i1 and i3 are not same, 
        # # i1 and i3 are ints
        # # s2 and s4 are strings

        # # check to see if net is in the table in reverse order.
        # equal_item = (i3, s4, i1, s2)

        # if equal_item not in self._net_table:
        #     self._net_table.add(item)
        #     confirm = True
        
        return confirm

    def delete_net_table(self, item: tuple) -> bool:
        confirm = False
        
        # (s1, s2, s3, s4) = item
        # equal_item = (s3, s4, s1, s2)

        # self._net_table.discard(equal_item)
        # self._net_table.discard(item)
        # confirm = True
        
        return confirm

    def is_Qomponent_pin_connected(self, component_name: str, port_name: str) -> Tuple[bool, tuple]:
        confirm = False
        aconnector = tuple()
        # comp_1 = ""
        # pin_1 = ""
        # comp_2 = ""
        # pin_2 = ""
        # for item in self._net_table:
        #     print (item)
        #     pass

        return (confirm, aconnector)
