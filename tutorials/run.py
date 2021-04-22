from qiskit_metal import MetalGUI, designs


def test():
    design = designs.DesignPlanar()
    gui = MetalGUI(design)
    gui.qApp.exec_()


if __name__ == '__main__':
    test()