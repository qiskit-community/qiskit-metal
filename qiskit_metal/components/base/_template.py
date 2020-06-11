from qiskit_metal import Dict, QComponent
from qiskit_metal import draw, is_true

class MyQComponent(QComponent):

    # EDIT HERE
    # Define the default tempate options
    default_options = Dict(
        width='500um',
        height='300um',
        pos_x='0um',
        pos_y='0um',
        rotation='0',
        layer='1'
    )

    def make(self):

        p = self.parse_options()  # Parse the string options into numbers

        # EDIT HERE - Replace the following with your code

        # Create some raw geometry -- See autocompletion for the `draw` module
        rect = draw.rectangle(p.width, p.height, p.pos_x, p.pos_y)
        rect = draw.rotate(rect, p.rotation)
        # Create QGeometry from a polygon
        geom = {'my_polygon': rect}
        self.add_elements('poly', geom, layer=p.layer, subtract=False)