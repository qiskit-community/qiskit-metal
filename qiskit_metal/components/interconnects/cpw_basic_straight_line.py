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
        pin_start_name='',
        pin_end_name='',
        cpw_width='cpw_width',
        cpw_gap='cpw_gap',
        layer='1',
        leadin=Dict(
            start='0um',
            end='0um'
        )
    )

    def make(self):
        p = self.parse_options()  # parsed options

        connectors = self.design.connectors
        connector1 = connectors[p.pin_start_name]
        connector2 = connectors[p.pin_end_name]

        pts = [connector1.middle,
               connector1.middle + connector1.normal *
               (p.cpw_width / 2 + p.leadin.start),
               connector2.middle + connector2.normal *
               (p.cpw_width / 2 + p.leadin.end),
               connector2.middle]

        line = draw.LineString(pts)

        self.add_qgeometry('path', {'center_trace': line},
                           width=p.cpw_width, layer=p.layer)
        self.add_qgeometry('path', {'gnd_cut': line},
                           width=p.cpw_width+2*p.cpw_gap, subtract=True)
