from qiskit_metal import designs, draw, MetalGUI, Dict, open_docs

def main():
    design = designs.DesignPlanar()
    design.overwrite_enabled = True
    design.chips.main.size.size_x = '11mm'
    design.chips.main.size.size_y = '9mm'
    gui = MetalGUI(design)

if __name__ == "__main__":
    main()
