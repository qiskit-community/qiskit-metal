from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core.base import QComponent


class Airbridge_forGDS(QComponent):
    """
    The base "Airbridge" inherits the "QComponent" class.
    
    NOTE TO USER: This component is designed for GDS export only. 
    This QComponent should NOT be rendered for EM simulation.
    
    Default Options:
        * crossover_length: '22um' -- Distance between the two outer squares (aka bridge length).
                                      Usually, this should be the same length as (cpw_width + 2 * cpw_gap)
        * bridge_width: '7.5um' -- Width of bridge element
        * inner_length: '8um' -- Length of inner square.
        * outer_length: '11um' -- Length of outer square.
        * square_layer: 30 -- GDS layer of inner squares.
        * bridge_layer: 31 -- GDS layer of bridge + outer squares.
    """

    # Default drawing options
    default_options = Dict(crossover_length='22um',
                           bridge_width='7.5um',
                           inner_length='8um',
                           outer_length='11um',
                           square_layer=30,
                           bridge_layer=31)
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='airbridge')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""
        # Parse options
        p = self.parse_options()
        crossover_length = p.crossover_length
        bridge_width = p.bridge_width
        inner_length = p.inner_length
        outer_length = p.outer_length

        # Make the inner square structure
        left_inside = draw.rectangle(inner_length, inner_length, 0, 0)
        right_inside = draw.translate(left_inside,
                                      crossover_length / 2 + outer_length / 2,
                                      0)
        left_inside = draw.translate(left_inside,
                                     -(crossover_length / 2 + outer_length / 2),
                                     0)

        inside_struct = draw.union(left_inside, right_inside)

        # Make the outer square structure
        left_outside = draw.rectangle(outer_length, outer_length, 0, 0)
        right_outside = draw.translate(left_outside,
                                       crossover_length / 2 + outer_length / 2,
                                       0)
        left_outside = draw.translate(
            left_outside, -(crossover_length / 2 + outer_length / 2), 0)

        # Make the bridge structure
        bridge = draw.rectangle(crossover_length, bridge_width, 0, 0)
        bridge_struct = draw.union(bridge, left_outside, right_outside)

        ### Final adjustments to allow repositioning
        final_design = [bridge_struct, inside_struct]
        final_design = draw.rotate(final_design, p.orientation, origin=(0, 0))
        final_design = draw.translate(final_design, p.pos_x, p.pos_y)
        bridge_struct, inside_struct = final_design

        ### Add everything as a QGeometry
        self.add_qgeometry('poly', {'bridge_struct': bridge_struct},
                           layer=p.bridge_layer,
                           subtract=False)
        self.add_qgeometry('poly', {'inside_struct': inside_struct},
                           layer=p.square_layer,
                           subtract=False)
