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
        """Return unique number for each net in table.
       
        Returns:
            int -- For user of the design class to know the lastest id added to _net_info.
        """
        return self._qnet_latest_assigned_id

    @property
    def net_info(self) -> pd.DataFrame:
        """[summary]

        Returns:
            [type] -- [description]
        """
        return self._net_info

   
    def add_pins_to_table(self, comp1_id: int, pin1_name: str, comp2_id: int, pin2_name: str) -> int:
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

        # Confirm the component-pin combonation is NOT in _net_info, before adding them.
        for (netID, component_id, pin_name) in self._net_info.itertuples(index=False):
            if ((component_id == comp1_id) and (pin_name == pin1_name)):
                self.logger.warning(f'Component: {comp1_id} and pin: {pin1_name} are already in net_info with net_id {netID}')
                return net_id
            if ((component_id == comp2_id) and (pin_name == pin2_name)):
                self.logger.warning(f'Component: {comp2_id} and pin: {pin2_name} are already in net_info with net_id {netID}')
                return net_id
 
        net_id = self._get_new_qnet_id()

        entry1 = [net_id, comp1_id, pin1_name]
        entry2 = [net_id, comp2_id, pin2_name]
        temp_df = pd.DataFrame([entry1, entry2], columns=self.column_names)

        self._net_info = self._net_info.append(temp_df, ignore_index=True)

        #print(self._net_info)
        return net_id

        
    def delete_net_id(self, net_id_to_remove: int):
        """[summary]

        Arguments:
            net_id_to_remove {int} -- [description]

        """

        self._net_info.drop(
            self._net_info.index[self._net_info['net_id'] == net_id_to_remove], inplace=True)
        return

    def delete_all_pins_for_component(self, component_id_to_remove: int):
        all_net_id_deleted = set()

        for (netID, component_id, pin_name) in self._net_info.itertuples(index=False):
            if (component_id == component_id_to_remove):
                all_net_id_deleted.add(netID)
                
        
        for netID in all_net_id_deleted:
            self.delete_net_id(netID)

        #self._net_info.drop(
        #    self._net_info.index[self._net_info['component_id'] == component_id_to_remove], inplace=True)
        return

    def add_for_test(self):
        # for testing, need values in net_table to test.
       
        self.add_pins_to_table(1,'qubit',  3, 'qstart')
        self.add_pins_to_table(1, 'bus1',  3, 'qstartother')
        self.add_pins_to_table(2, 'bus2',  5, 'qend')
        self.add_pins_to_table(1, 'qubitextra', 3, 'qrunning')

        # id_local = self._get_new_qnet_id()
        # self._net_info = self._net_info.append(
        #     pd.Series([id_local, 1, 'qubit'], index=self._net_info.columns), ignore_index=True)
        # self._net_info = self._net_info.append(
        #     pd.Series([id_local, 3, 'qstart'], index=self._net_info.columns), ignore_index=True)

        # id_local = self._get_new_qnet_id()
        # self._net_info = self._net_info.append(
        #     pd.Series([id_local, 1, 'bus1'], index=self._net_info.columns), ignore_index=True)
        # self._net_info = self._net_info.append(
        #     pd.Series([id_local, 4, 'qstart'], index=self._net_info.columns), ignore_index=True)

        # id_local = self._get_new_qnet_id()
        # self._net_info = self._net_info.append(
        #     pd.Series([id_local, 2, 'bus2'], index=self._net_info.columns), ignore_index=True)
        # self._net_info = self._net_info.append(
        #     pd.Series([id_local, 5, 'qend'], index=self._net_info.columns), ignore_index=True)

        # id_local = self._get_new_qnet_id()
        # self._net_info = self._net_info.append(
        #     pd.Series([id_local, 1, 'qubitextra'], index=self._net_info.columns), ignore_index=True)
        # self._net_info = self._net_info.append(
        #     pd.Series([id_local, 3, 'qrunning'], index=self._net_info.columns), ignore_index=True)
        #print(self._net_info)
