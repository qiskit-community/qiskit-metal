from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent

class SPole(QComponent):
    
    default_options = Dict(width = 'cpw_width',
                           gap = 'cpw_gap')
    
    def make(self):
        p = self.p
        self.options.pos_x, self.options.pos_y =self.get_pin_location(p.name, p.pin)

        # Draw SPole
        pole = draw.rectangle(p.width, p.width, 0, 0)
        pole_etch = draw.rectangle(p.width + 2 * p.gap, p.width + 2 * p.gap, 0, 0)
        
        # Rotate and Translate
        polys = [pole, pole_etch]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, self.options.pos_x, self.options.pos_y)
        
        [pole, pole_etch] = polys
        
        for layer in p.layers:
            self.add_qgeometry('poly', {'pole': pole},
                               subtract=False,
                               layer=layer,
                               chip=p.chip)
            self.add_qgeometry('poly', {'pole_etch': pole_etch},
                               subtract=True,
                               layer=layer,
                               chip=p.chip)
            
    def get_pin_location(self, name, pin):
        pos = self.design.components[name].pins[pin].middle
        return pos

