from qiskit_metal import draw, Dict, is_true
from qiskit_metal.components.base.base import QComponent

class MyQComponent(QComponent):
    """
    Use this class as a template for your components - have fun
    """

    # Edit these to define your own tempate options for creation
    # Default drawing options
    default_options = Dict(
        width='500um',
        height='300um',
        pos_x='0um',
        pos_y='0um',
        rotation='0',
        layer='1'
    )

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(
        component_type='component'
        )
            
    """Default drawing options"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        # EDIT HERE - Replace the following with your code
        # Create some raw geometry
        # Use autocompletion for the `draw.` module (use tab key)
        rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        rect = draw.rotate(rect, p.rotation)
        geom = {'my_polygon': rect}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)
