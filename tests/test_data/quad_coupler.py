from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent
import numpy as np


class QuadCoupler(QComponent):
    """Generates a one pin (+) structure comprised of a rectangular coupling pad
    capacitively coupled with any other component.

    .. meta::
        General Quadrilateral Coupler
    """

    component_metadata = Dict(short_name='cpw', _qgeometry_table_path='True')
    """Component metadata"""

    default_options = Dict(pad_width='40um',
                           pad_height='60um',
                           pad_gap='6um',
                           cpw_stub_width='10um',
                           cpw_stub_height='30um',
                           fillet='25um')
    """Default connector options"""

    def make(self):
        p = self.p

        coupler_pad = draw.rectangle(p.pad_width, p.pad_height)
        coupler_sub_pad = draw.rectangle(p.pad_width + p.pad_gap * 2,
                                         p.pad_height + p.pad_gap * 2)

        yoff = (p.pad_height + p.cpw_stub_height) / 2
        cpw_conn = draw.LineString([[0, -p.pad_height / 2],
                                    [0, -p.pad_height / 2 - p.cpw_stub_height]])
        cpw_conn_sub = draw.LineString(
            [[0, -p.pad_height / 2], [0,
                                      -p.pad_height / 2 - p.cpw_stub_height]])

        items = [coupler_pad, coupler_sub_pad, cpw_conn, cpw_conn_sub]
        items = draw.rotate(items, p.orientation, origin=(0, 0))
        items = draw.translate(items, p.pos_x, p.pos_y)
        coupler_pad, coupler_sub_pad, cpw_conn, cpw_conn_sub = items

        self.add_qgeometry('poly', {'quad_coupler': coupler_pad}, layer=p.layer)
        self.add_qgeometry('poly', {'quad_coupler_sub': coupler_sub_pad},
                           layer=p.layer,
                           subtract=True)

        self.add_qgeometry('path', {'stub': cpw_conn},
                           layer=p.layer,
                           width=p.cpw_stub_width)
        self.add_qgeometry('path', {'stub_sub': cpw_conn_sub},
                           layer=p.layer,
                           width=p.cpw_stub_width + p.pad_gap * 2,
                           subtract=True)

        pin_list = cpw_conn.coords
        self.add_pin('in',
                     points=np.array(pin_list),
                     width=p.cpw_stub_width,
                     input_as_norm=True)
