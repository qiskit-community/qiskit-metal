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

from ... import draw
from ...toolbox_python.attr_dict import Dict
from ..base import QComponent

from ...toolbox_python.utility_functions import log_error_easy


class FakeCPW(QComponent):
    """A fake cpw just to test pin generation and netlist functionality

    Inherits QComponent class
    """
    default_options = Dict(
        line_width='10um',
        line_gap='6um',
        component_start=0,
        pin_start=0,
        component_end=0,
        pin_end=0
        # pin_start = dict(), #for now assuming the dictionary of the pin is passed, it
        # #could instead be just the pin and component id.
        # pin_end = dict()
    )
    """Default drawing options"""

    def make(self):
        """ This is executed by the user to generate the elements for the component.
        """
        component_start = self.options['component_start']
        pin_start = self.options['pin_start']
        component_end = self.options['component_end']
        pin_end = self.options['pin_end']

        # Check if component was deleted from design.
        if component_end not in self.design._components:
            self.logger.warning(
                f'Key={component_end, } not a key in design._components. {self.name} NOT built.')
            return

        if component_start not in self.design._components:
            self.logger.warning(
                f'Key={component_start} not a key in design._components. {self.name} NOT built.')
            return

        # NOTE: This code could be moved to a parent class specifically handling components
        # which take pins as inputs, eg. QInterconnect
        # Should the check be in the init such that the component isn't made if non-viable
        # pins are passed in?
        #
        if self.design._components[component_start].pins[pin_start].net_id:
            print(
                f'Given pin {component_start} {pin_start} already in use. Component not created.')
            log_error_easy(self.logger, post_text=f'\nERROR in building component "{self.name}"!'
                           'Inelligeable pin passed to function.\n')
            return
        if self.design._components[component_end].pins[pin_end].net_id:
            print(
                f'Given pin {component_end} {pin_end} already in use. Component not created.')
            log_error_easy(self.logger, post_text=f'\nERROR in building component "{self.name}"!'
                           'Inelligeable pin passed to function.\n')
            return
        #########################################################

        starting_pin_dic = self.design._components[component_start].pins[pin_start]
        ending_pin_dic = self.design._components[component_end].pins[pin_end]

        fake_cpw_line = draw.LineString(
            [starting_pin_dic['middle'], ending_pin_dic['middle']])
        self.add_elements(
            'path', {f'{self.name}_cpw_line': fake_cpw_line}, width=self.p.line_width)

        self.add_pin('fake_cpw_start', starting_pin_dic.points,
                     self.id, flip=True)
        self.add_pin('fake_cpw_end', ending_pin_dic.points, self.id, flip=True)

        # THEN ADD TO NETLIST - THIS SHOULD PROBABLY BE LARGELY HANDLED BY A DESIGN METHOD
        self.design.connect_pins(
            component_start, pin_start, self.id, 'fake_cpw_start')
        self.design.connect_pins(
            component_end, pin_end, self.id, 'fake_cpw_end')

        #start_netID = self.design._net_info.add_pins_to_table(component_start,pin_start,self.id,'fake_cpw_start')
        #end_netID = self.design._net_info.add_pins_to_table(component_end,pin_end,self.id,'fake_cpw_end')
