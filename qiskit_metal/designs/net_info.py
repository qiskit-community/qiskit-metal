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
from .. import logger


class QNet():
    """[summary]
    """

    def __init__(self):
        """ Hold the net information of all the USED pins within a design."""
        self.column_names = ['net_id', 'component_id', 'pin_name']
        self._net_info = pd.DataFrame(columns=self.column_names)
        self._qnet_latest_assigned_id = 0
        self.logger = logger  # type: logging.Logger

    def _get_new_qnet_id(self) -> int:
        self._qnet_latest_assigned_id += 1
        return self._qnet_latest_assigned_id

    @property
    def qnet_latest_assigned_id(self) -> int:
        '''
        Return unique number for each net in table.
        For user of the design class to know the lastest id added to _net_info.
        '''
        return self._qnet_latest_assigned_id

    def add_for_test(self):
        # for testing, need values in net_table to test.
        id_local = self._get_new_qnet_id()
        self._net_info = self._net_info.append(
            pd.Series([id_local, 1, 'qubit'], index=self._net_info.columns), ignore_index=True)
        self._net_info = self._net_info.append(
            pd.Series([id_local, 3, 'qstart'], index=self._net_info.columns), ignore_index=True)

        id_local = self._get_new_qnet_id()
        self._net_info = self._net_info.append(
            pd.Series([id_local, 1, 'bus1'], index=self._net_info.columns), ignore_index=True)
        self._net_info = self._net_info.append(
            pd.Series([id_local, 4, 'qstart'], index=self._net_info.columns), ignore_index=True)

        id_local = self._get_new_qnet_id()
        self._net_info = self._net_info.append(
            pd.Series([id_local, 2, 'bus2'], index=self._net_info.columns), ignore_index=True)
        self._net_info = self._net_info.append(
            pd.Series([id_local, 5, 'qend'], index=self._net_info.columns), ignore_index=True)
        print(self._net_info)
        pass

    def add_to_net_table(self, comp1_id: int, pin1_name: str, comp2_id: int, pin2_name: str) -> int:
        """Add two entries into the _net_info table.

        Arguments:
            comp1_id {int} -- [description]
            pin1_name {str} -- [description]
            comp2_id {int} -- [description]
            pint2 {str} -- [description]

        Returns:
            int -- 0 if not added to list, otherwise the netid
        """

        assert isinstance(comp1_id, int), self.logger.error(
            f'Expected an int, but have {comp1_id}.')
        assert isinstance(comp2_id, int), self.logger.error(
            f'Expected an int, but have {comp2_id}.')
        assert isinstance(pin1_name, str), self.logger.error(
            f'Expected a string, but have {pin1_name}.')
        assert isinstance(pin2_name, str), self.logger.error(
            f'Expected a string, but have {pin2_name}.')



        net_id = 0   # Zero mean false, the pin was not added to _net_info
        net_id = self._get_new_qnet_id()

        entry1 = [net_id, comp1_id, pin1_name]
        entry2 = [net_id, comp2_id, pin2_name]
        temp_df = pd.DataFrame([entry1, entry2], columns=self.column_names)

        self._net_info = self._net_info.append(temp_df)

        print(self._net_info)
        return net_id

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
