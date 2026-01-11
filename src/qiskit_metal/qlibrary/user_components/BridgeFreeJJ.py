import qiskit_metal as metal
import numpy as np
from qiskit_metal import Dict, draw
from qiskit_metal.qlibrary.core import QComponent


class BridgeFreeJunction(QComponent):
    """
    Bridge-free Josephson Junction.
    Reference: F. Lecocq, et al., Nanotechnology, 22, 302-315, (2011).


        Default Options:
        * JJ_width: '4um' -- The width of lower JJ metal region
        * JJ_height: '4um' -- The height of lower JJ metal region
        * teta_1: '30' -- Evaporation angle of the first evaporation (˚)
        * teta_2: '30' -- Evaporation angle of the second evaporation (˚)
        * wire_length: '30 um' -- The length of the connecting wires.
        * wire_width: '0.5 um' -- The width of the connecting wires.
        * resist_t1 : '300 nm' -- Thickness of the first (bottom) resist layer.
        * resist_t2 : '200 nm' -- Thickness of the first (top) resist layer.

    """

    default_options = Dict(
        JJ_width='4. um',
        JJ_height='4. um',
        teta_1='30',  #
        teta_2='30',  #
        wire_length='30um',  #
        wire_width='0.5 um',  #
        resist_t1=
        '.3um',  # Thickness of the first (lower) resist layer. Option is 200 nm.
        resist_t2='.2um',
        orientation='0',
        layer='53',
        layer_2='545.',
        layer_3='55.',
        layer_4='1.',
        pos_x='0',
        pos_y='0')

    component_metadat = Dict(short_name='Bf_JJ',
                             _qgeometry_table_poly='True',
                             _qgeometry_table_junction='True',
                             _qgeometry_table_path='True')

    def make(self):
        name = 'bf_JJ'
        p = self.parse_options()  # Parse the string options into numbers
        resist_t1 = p.resist_t1
        resist_t2 = p.resist_t2
        teta_1 = p.teta_1  # This angle is considered as the angle between the beam in
        # the area (-x,y) and the vertical line
        teta_2 = p.teta_2

        # We need different openings for wires. For the purpose, we define hight_total and hight_bottom.
        # The bottom is required for the undercut layer, corresponding to the low dose.
        h_tot = resist_t1 + resist_t2
        h_bot = resist_t1

        # Extra lengths we need to consider for a successful shadow evaporation
        # shadow side for the first evaporation
        shift_1_t = h_tot / np.tan(np.pi * teta_1 / 180)
        shift_1_b = h_bot / np.tan(np.pi * teta_1 / 180)

        # shadow side for the second evaporation
        shift_2_t = h_tot / np.tan(np.pi * teta_2 / 180)
        shift_2_b = h_bot / np.tan(np.pi * teta_2 / 180)

        #if shift parts are thiner than the wire, the shadow wire will not get removed after lift-off;
        #meaning that we will have shortcut.
        if (shift_2_t < p.wire_width) or (shift_1_t < p.wire_width):
            raise ValueError

        #Define the wire at the left side of the junction.
        wire_l = draw.box(-(p.wire_length + p.JJ_width / 2.),
                          -p.wire_width / 2. - shift_2_t, -p.JJ_width / 2.,
                          p.wire_width / 2. - shift_2_b)

        # Define the wire at the right side of the junction.
        wire_r = draw.box(p.JJ_width / 2., -p.wire_width / 2. + shift_1_b,
                          p.JJ_width / 2. + p.wire_length,
                          p.wire_width / 2. + shift_1_t)

        # Draw the Junction area as a box
        JJ = draw.box(-p.JJ_width / 2., -p.JJ_height / 2. - shift_2_t,
                      p.JJ_width / 2., p.JJ_height / 2. + shift_1_t)

        # Define the feature as a union of the Josephson Junction and the wires.
        Junction = draw.union(JJ, wire_l, wire_r)

        # Define undercut layer at the left wire
        undercut_l = draw.box(-(p.wire_length + p.JJ_width / 2.),
                              p.wire_width / 2., -p.JJ_width / 2.,
                              p.wire_width / 2. + shift_2_b)

        # Define undercut layer at the right wire
        undercut_r = draw.box(p.JJ_width / 2., -p.wire_width / 2.,
                              p.JJ_width / 2. + p.wire_length,
                              -p.wire_width / 2. - shift_1_b)

        # Define undercut layer below the junction (for the bottom electrode)
        undercut_jj_low = draw.box(-p.JJ_width / 2.,
                                   -p.JJ_height / 2. - shift_2_t,
                                   p.JJ_width / 2,
                                   -p.JJ_height / 2. - shift_2_t - shift_1_b)

        # Define undercut layer above the junction (for the top electrode)
        undercut_jj_up = draw.box(-p.JJ_width / 2.,
                                  p.JJ_height / 2. + shift_1_t, p.JJ_width / 2,
                                  p.JJ_height / 2. + shift_1_t + shift_2_b)

        #Define undercut layer as a union of the all undercuts.
        undercut = draw.union(undercut_jj_low, undercut_jj_up, undercut_l,
                              undercut_r)

        Junction_items = [Junction, undercut]
        Junction_items = draw.rotate(Junction_items,
                                     p.orientation,
                                     origin=(0, 0))

        Junction_items = draw.translate(Junction_items, p.pos_x, p.pos_y)

        [Junction, undercut] = Junction_items

        #Add features to the geometery
        self.add_qgeometry('poly', {'undercut': undercut}, layer=p.layer_3)

        self.add_qgeometry('poly', {'Junction': Junction}, layer=p.layer)
