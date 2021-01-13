# Import Qiskit Metal

import qiskit_metal as metal
from qiskit_metal import designs, draw
from qiskit_metal import MetalGUI, Dict, open_docs


design = designs.DesignPlanar()
gui = MetalGUI(design)

# Select a QComponent to create (The QComponent is a python class named `TransmonPocket`)
from qiskit_metal.components.qubits.transmon_pocket import TransmonPocket

TransmonPocket.get_template_options(design)

q1 = TransmonPocket(design, 'Q1', options = dict(pos_x='+0.5mm', pos_y='+0.5mm'))

gui.edit_component('Q1')

gui.edit_component_source('Q1')

