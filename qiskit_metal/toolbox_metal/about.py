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
Reports a summary of information on Qiskit Metal and dependencies

@author: Zlatko Minev
@date: 2020
"""

import os
import sys
import numpy
import inspect
import webbrowser
from pathlib import Path


__all__ = ['about']


def about():
    """
    Reports a summary of information on Qiskit Metal and dependencies.

    Returns:
        str: About message
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


def get_module_doc_page(module, folder=r'../docs/build/html', page='index.html'):
    """
    Get the file path to a module doc folder assumed to be inside the package.
    """
    return Path(os.path.dirname(module.__file__)) / folder / page


def open_docs(page='index.html'):
    """
    Open the qiskit_metal documentation in HTML. Open the URL in new window,
    raising the window if possible.
    """
    import qiskit_metal
    module = qiskit_metal
    filepath = get_module_doc_page(module, page=page)
    if filepath.is_file():
        webbrowser.open(f"file://{filepath}", new=1)
        print(f'Opened {module.__name__} docs in a new webbrowser page.')
    else:
        print(f'Error: Could not find the doc file {filepath}.'
              'Check the folder path.')
