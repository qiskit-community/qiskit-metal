# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
@author: Zlatko Minev
@date: 2020
"""

import os
import sys
import numpy
import inspect

__all__ = ['about']

def about():
    """
    Reports a summary of information on Qiskit Metal and dependencies.
    """
    import qiskit_metal

    import platform
    from PyQt5.QtCore import QT_VERSION_STR
    from PyQt5.Qt import PYQT_VERSION_STR

    try:
        import matplotlib
        matplotlib_ver = matplotlib.__version__
    except:
        matplotlib_ver = 'None'

    try:
        from sip import SIP_VERSION_STR
    except:
        SIP_VERSION_STR = 'Not installed'
    # Riverbank: SIP is a tool for quickly writing Python modules that interface with C++ and C libraries.

    text = f"""
Qiskit Metal        {qiskit_metal.__version__}

Basic
____________________________________
 Python              {sys.version}
 Platform            {platform.system()} {platform.machine()}
 Installation path   {os.path.dirname(inspect.getsourcefile(qiskit_metal))}

Packages
____________________________________
 Numpy               {numpy.__version__}

Rendering
____________________________________
 Matplotlib          {matplotlib.__version__}

GUI
____________________________________
 PyQt version        {PYQT_VERSION_STR}
 Qt version          {QT_VERSION_STR}
 SIP version         {SIP_VERSION_STR}

IBM Quantum Team"""
    print(text)

    return text