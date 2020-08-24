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

from qiskit_metal import draw
from qiskit_metal.toolbox_python.attr_dict import Dict
from qiskit_metal.components.base.base import QComponent
from qiskit_metal.toolbox_python.utility_functions import log_error_easy


class FakeCPW(QComponent):
    """A fake cpw just to test pin generation and netlist functionality

    Inherits QComponent class
    """
    component_metadata = Dict(
        short_name='cpw'
        )
    """Component metadata"""

    default_options = Dict(
        line_width='10um',
        line_gap='6um',
        pin_inputs=Dict(start_pin=Dict(component='', pin=''),
                        end_pin=Dict(component='', pin=''))
    )
    """Default drawing options"""

    def make(self):
        """ This is executed by the user to generate the qgeometry for the component.
        """
        p = self.p
        #########################################################
        component_start = p.pin_inputs['start_pin']['component']
        pin_start = p.pin_inputs['start_pin']['pin']
        component_end = p.pin_inputs['end_pin']['component']
        pin_end = p.pin_inputs['end_pin']['pin']

        starting_pin_dic = self.design.components[component_start].pins[pin_start]
        ending_pin_dic = self.design.components[component_end].pins[pin_end]
        # Add check if component_end is int? Better to do that check in base? Though that would
        # overwrite the option value, possibly confuse the user?

        # Creates the CPW geometry
        fake_cpw_line = draw.LineString(
            [starting_pin_dic['middle'], ending_pin_dic['middle']])
        # Adds the CPW to the qgeometry table
        self.add_qgeometry(
            'path', {f'{self.name}_cpw_line': fake_cpw_line}, width=p.line_width)

        # Generates its own pins based on the inputs
        # Note: Need to flip the points so resulting normal vector is correct.
        self.add_pin('fake_cpw_start',
                     starting_pin_dic.points[::-1], p.line_width)
        self.add_pin('fake_cpw_end', ending_pin_dic.points[::-1], p.line_width)

        # THEN ADD TO NETLIST - Note: Thoughts on how to have this be automated so the component designer
        # doesn't need to write this code?
        self.design.connect_pins(
            self.design.components[component_start].id, pin_start, self.id, 'fake_cpw_start')
        self.design.connect_pins(
            self.design.components[component_end].id, pin_end, self.id, 'fake_cpw_end')
