from IPython import get_ipython
from PyQt5.QtWidgets import QApplication

ipython = get_ipython()
qApp = QApplication.instance()
print('ipython = ', ipython, '\nqQApp = ', qApp)

if qApp is None:
    if ipython:
        print('***>>> LAUNCH: gui qt5')
        ipython.magic('gui qt5')
    else:
        print('***>>> LAUNCH: QApplication')
        qApp = QApplication(['qiskit-metal'])
        #qApp.exec_() # don't do this, this is a blocking call
else:
    print('***>>> LAUNCH: None')
qApp = QApplication.instance()
print('qApp = ', qApp)


# SIMPLE LAUNCH to test
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout
window = QMainWindow()
widget = QWidget()
window.setCentralWidget(widget)
layout = QVBoxLayout()
layout.addWidget(QPushButton('Top'))
layout.addWidget(QPushButton('Bottom'))
widget.setLayout(layout)
window.show()
window.raise_()



"""
Irrelevant notes from Zlatko:
------------------------------------

import IPython
import ipykernel
from ipykernel import zmqshell
from IPython import get_ipython
from IPython import start_ipython
from  IPython.core.magics.basic import BasicMagics
start_ipython()

ipykernel.zmqshell.ZMQInteractiveShell

p = get_ipython()
p.run_line_magic('gui', 'qt')
import IPython
IPython.embed()
"""