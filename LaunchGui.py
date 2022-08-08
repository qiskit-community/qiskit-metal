import sys
import os
import qiskit_metal as metal
from qiskit_metal import designs, draw
from qiskit_metal import MetalGUI, Dict, open_docs
from PySide2.QtWidgets import QApplication, QWidget

os.environ['QT_MAC_WANTS_LAYER'] = '1'

def main():
    print("Launch Python GUI")

    qApp = QApplication(sys.argv)
    design = designs.DesignPlanar()
    gui = MetalGUI(design)
    
    # Can be also launched without a
    # design instance but many features
    # are disabled at that point
    # gui = MetalGUI()

    qApp.exec_()

if __name__ == "__main__":
    main()
