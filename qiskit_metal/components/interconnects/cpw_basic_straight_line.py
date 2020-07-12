"""
Zlatko & Dennis component to draw a straight
CPW with correct initial corner.
"""

from qiskit_metal import Dict, QComponent, draw
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
        pin_start=Dict(component='', pin=''), # make sure these are Dicts not dicts
        pin_end=Dict(component='', pin=''),
        cpw_width='cpw_width',
        cpw_gap='cpw_gap',
        layer='1',
        leadin=Dict(
            start='0um',
            end='0um'
        )
    )

    def make(self):
        """
        The make function implements the logic that creates the geoemtry
        (poly, path, etc.) from the qcomponent.options dictionary of parameters,
        and the adds them to the design, using qcomponent.add_qgeometry(...),
        adding in extra needed information, such as layer, subtract, etc.
        """
        p = self.p  # parsed options

        pin1 = self.design.components[self.options.pin_start.component].pins[self.options.pin_start.pin]
        pin2 = self.design.components[self.options.pin_end.component].pins[self.options.pin_end.pin]

        pts = [pin1.middle,
               pin1.middle + pin1.normal * (p.cpw_width / 2 + p.leadin.start),
               pin2.middle + pin2.normal * (p.cpw_width / 2 + p.leadin.end),
               pin2.middle]

        line = draw.LineString(pts)

        self.add_qgeometry('path', {'center_trace': line},
                           width=p.cpw_width, layer=p.layer)
        self.add_qgeometry('path', {'gnd_cut': line},
                           width=p.cpw_width+2*p.cpw_gap, subtract=True)
