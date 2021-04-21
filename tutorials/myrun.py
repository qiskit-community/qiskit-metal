import qiskit_metal as metal
from qiskit_metal import designs, draw
from qiskit_metal import MetalGUI, Dict, open_docs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.qubits import transmon_pocket



def test():
    design = designs.DesignPlanar()
    gui = MetalGUI(design)

    TransmonPocket.default_options
    TransmonPocket.get_template_options(design)
    design.template_options.pop('qiskit_metal.qlibrary.qubits.transmon_pocket.TransmonPocket')
    TransmonPocket.get_template_options(design)
    print("CHICKENS")


if __name__ == '__main__':
    test()
