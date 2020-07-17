"""
Zlatko & Dennis component to draw a straight
CPW with correct initial corner.
"""

from qiskit_metal import draw, Dict#, QComponent
from qiskit_metal.components import QComponent
from qiskit_metal.toolbox_metal.parsing import is_true


class CpwStraightLine(QComponent):

    """
    Draw a straight CPW line connecting two pins.
    The start and end also have two extra short-point segments
    that make sure the bend at an angle is smooth.

    Example use:

    .. code-block:: python
        :linenos:

        if '__main__.CpwStraightLine' in design.template_options:
        design.template_options.pop('__main__.CpwStraightLine')

        options = {
            'pin_start_name': 'Q1_a',
            'pin_end_name': 'Q2_b',
        }
        qc = CpwStraightLine(design, 'myline', options)
        gui.rebuild()
    """

    default_options = Dict(
        pin_inputs=Dict(
            start_pin=Dict(
                component='', # Name of component to start from, which has a pin
                pin=''), # Name of pin used for pin_start
            end_pin=Dict(
                component='', # Name of component to end on, which has a pin
                pin='') # Name of pin used for pin_end
                ),        
        cpw_width='cpw_width',
        cpw_gap='cpw_gap',
        layer='1',
        leadin=Dict(
            start='0um',
            end='0um'
        )
    )
    """Default drawing options"""

    def make(self):
        """
        The make function implements the logic that creates the geoemtry
        (poly, path, etc.) from the qcomponent.options dictionary of parameters,
        and the adds them to the design, using qcomponent.add_qgeometry(...),
        adding in extra needed information, such as layer, subtract, etc.
        """
        p = self.p  # parsed options

        pin1 = self.design.components[self.options.pin_inputs.start_pin.component].pins[self.options.pin_inputs.start_pin.pin]
        pin2 = self.design.components[self.options.pin_inputs.end_pin.component].pins[self.options.pin_inputs.end_pin.pin]

        pts = [pin1.middle,
               pin1.middle + pin1.normal * (p.cpw_width / 2 + p.leadin.start),
               pin2.middle + pin2.normal * (p.cpw_width / 2 + p.leadin.end),
               pin2.middle]

        line = draw.LineString(pts)

        self.add_qgeometry('path', {'center_trace': line},
                           width=p.cpw_width, layer=p.layer)
        self.add_qgeometry('path', {'gnd_cut': line},
                           width=p.cpw_width+2*p.cpw_gap, subtract=True)

        # Generates its own pins based on the inputs
        # Note: Need to flip the points so resulting normal vector is correct.
        self.add_pin('start_pin',
                     pin1.points[::-1], p.cpw_width)
        self.add_pin('end_pin', pin2.points[::-1], p.cpw_width)
        # THEN ADD TO NETLIST - Note: Thoughts on how to have this be automated so the component designer
        # doesn't need to write this code?
        self.design.connect_pins(
            self.design.components[self.options.pin_inputs.start_pin.component].id, 
            self.options.pin_inputs.start_pin.pin, self.id, 'start_pin')
        self.design.connect_pins(
            self.design.components[self.options.pin_inputs.end_pin.component].id, 
            self.options.pin_inputs.end_pin.pin, self.id, 'end_pin')