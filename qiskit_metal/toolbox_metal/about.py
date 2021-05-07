# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable-msg=import-error
"""Reports a summary of information on Qiskit Metal and dependencies.

Contain functions to report more detailed information to orient a user,
used for debug purposes.
"""

from pathlib import Path
from typing import Union

import os
import sys
import getpass
import inspect
import platform
import webbrowser
import numpy
import qutip

from qiskit_metal.toolbox_python.display import Color, style_colon_list

__all__ = [
    'about', 'open_docs', 'orient_me', 'get_platform_info',
    'get_module_doc_page'
]


# pylint: disable-msg=invalid-name
# pylint: disable-msg=import-outside-toplevel
# pylint: disable-msg=bare-except
def about():
    """Reports a summary of information on Qiskit Metal and dependencies.

    Returns:
        str: About message
    """
    import qiskit_metal
    from PySide2.QtCore import __version__ as QT_VERSION_STR
    from PySide2 import __version__ as PYSIDE_VERSION_STR

    try:
        import matplotlib
        #matplotlib_ver = matplotlib.__version__
    except:
        #matplotlib_ver = 'None'
        pass

    try:
        from sip import SIP_VERSION_STR
    except:
        SIP_VERSION_STR = 'Not installed'
    # Riverbank: SIP is a tool for quickly writing Python modules that interface with
    # C++ and C libraries.

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
 Qutip               {qutip.__version__}

Rendering
____________________________________
 Matplotlib          {matplotlib.__version__}

GUI
____________________________________
 PySide2 version     {PYSIDE_VERSION_STR}
 Qt version          {QT_VERSION_STR}
 SIP version         {SIP_VERSION_STR}

IBM Quantum Team"""
    print(text)

    return text


######################################################################################
# DOCS


def get_module_doc_page(module,
                        folder=r'../docs/build/html',
                        page='index.html'):
    """Get the file path to a module doc folder assumed to be inside the
    package."""
    return Path(os.path.dirname(module.__file__)) / folder / page


def open_docs(page='https://qiskit.org/documentation/metal/'):
    """Open the qiskit_metal documentation in HTML.

    Open the URL in new window, raising the window if possible.
    """
    webbrowser.open(page, new=1)


######################################################################################
# More detailed information to orient a user.
# For debug purposes.
# Main function: ``orient_me```


def orient_me(do_print: bool = True) -> Union[None, str]:
    """Full system, python, user, and environemnt information.

    Args:
        do_print(bool): Return the string if True, else format and print.
    """

    text = get_platform_info()
    text += \
        f" User and directories:\n\n"\
        f"    User              : {getpass.getuser()}\n"\
        f"    User home dirctry : {Path.home()}\n"\
        f"    Current directory : {Path.cwd()}\n\n"\
        f"    Conda default env : {os.environ.get('CONDA_DEFAULT_ENV', 'N/A')}\n"\
        f"    Conda current env : {os.environ.get('CONDA_PREFIX', 'N/A')}\n"\
        f"    Python executable : {sys.executable}\n"\

    if do_print:
        text = style_colon_list(text, Color.BOLD, Color.END)
        print(text)
        return None

    return text


def get_platform_info() -> str:
    """Returns a string with the platform information."""

    return '''

 System platform information:

    system   : %s
    node     : %s
    release  : %s
    machine  : %s
    processor: %s
    summary  : %s
    version  : %s

 Python platform information:

    version  : %s (implem: %s)
    compiler : %s

''' % (platform.system(), platform.node(), platform.release(),
       platform.machine(), platform.processor(), platform.platform(),
       platform.version(), platform.python_version(),
       platform.python_implementation(), platform.python_compiler())
