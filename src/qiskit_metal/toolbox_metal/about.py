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

"""Reports a summary of information on Qiskit Metal and dependencies.

Contain functions to report more detailed information to orient a user,
used for debug purposes.
"""

import inspect
import os
import platform
import sys
import webbrowser
from pathlib import Path
from typing import Union

import numpy
import qutip

from qiskit_metal.toolbox_python.display import Color, style_colon_list

__all__ = ["about", "open_docs", "get_platform_info", "get_module_doc_page"]


def about():
    """Reports a summary of information on Qiskit Metal and dependencies.

    Returns:
        str: About message
    """
    import qiskit_metal

    # PySide6 is an optional extra (``quantum-metal[gui]``) — the lite
    # install path omits it, so about() must not require it.
    try:
        from PySide6 import __version__ as PYSIDE_VERSION_STR
        from PySide6.QtCore import __version__ as QT_VERSION_STR
    except ImportError:
        QT_VERSION_STR = "Not installed"
        PYSIDE_VERSION_STR = "Not installed"

    import matplotlib

    try:
        from sip import SIP_VERSION_STR
    except ImportError:
        SIP_VERSION_STR = "Not installed"
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
 PySide6 version     {PYSIDE_VERSION_STR}
 Qt version          {QT_VERSION_STR}
 SIP version         {SIP_VERSION_STR}

IBM Quantum Team"""
    print(text)

    return text


######################################################################################
# DOCS


def get_module_doc_page(module, folder=r"../docs/build/html", page="index.html"):
    """Get the file path to a module doc folder assumed to be inside the
    package."""
    return Path(os.path.dirname(module.__file__)) / folder / page


def open_docs(page="https://qiskit-community.github.io/qiskit-metal/", force=False):
    """Open the Quantum / Qiskit Metal documentation in a web browser.

    Args:
        page: URL to open. Defaults to the published docs site.
        force: If True, always pop the browser, even in headless / CI /
            notebook-execute contexts. Defaults to False so that
            running this cell during ``tox -e docs``, nbsphinx
            notebook execution, "Restart & Run All", or on a headless
            Linux server / Colab kernel won't repeatedly launch the
            user's browser. In those cases the URL is printed instead.
    """
    headless = (
        os.environ.get("QISKIT_METAL_HEADLESS") == "1"
        or os.environ.get("CI") == "true"
        or os.environ.get("BINDER_REQUEST")
        or os.environ.get("BINDER_SERVICE_HOST")
        or "DISPLAY" not in os.environ
        and sys.platform.startswith("linux")
    )
    if headless and not force:
        try:
            from IPython.display import HTML, display

            display(
                HTML(
                    f"Quantum Metal docs: "
                    f'<a href="{page}" target="_blank">{page}</a> '
                    f"(headless / CI session — browser pop suppressed; "
                    f"call <code>open_docs(force=True)</code> to override)"
                )
            )
        except Exception:
            print(f"Quantum Metal docs: {page}")
        return
    webbrowser.open(page, new=1)

    ######################################################################################
    # More detailed information to orient a user.
    # For debug purposes.
    # Main function: ``orient_me```

    # def orient_me(do_print: bool = True) -> Union[None, str]:
    """Full system, python, user, and environemnt information.

    Args:
        do_print(bool): Return the string if True, else format and print.
    """


#    text = get_platform_info()
#    text += \
#        f" User and directories:\n\n"\
#        f"    User              : {getpass.getuser()}\n"\
#        f"    User home dirctry : {Path.home()}\n"\
#        f"    Current directory : {Path.cwd()}\n\n"\
#        f"    Conda default env : {os.environ.get('CONDA_DEFAULT_ENV', 'N/A')}\n"\
#        f"    Conda current env : {os.environ.get('CONDA_PREFIX', 'N/A')}\n"\
#       f"    Python executable : {sys.executable}\n"\

#    if do_print:
#        text = style_colon_list(text, Color.BOLD, Color.END)
#        print(text)
#        return None

#    return text


def get_platform_info() -> str:
    """Returns a string with the platform information."""

    return """

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

""" % (
        platform.system(),
        platform.node(),
        platform.release(),
        platform.machine(),
        platform.processor(),
        platform.platform(),
        platform.version(),
        platform.python_version(),
        platform.python_implementation(),
        platform.python_compiler(),
    )
