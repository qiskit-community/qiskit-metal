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


# Get Qiskit Metal version from metadata without importing the package
from importlib.metadata import metadata, version

metal_metadata = metadata("quantum-metal")

"""Qiskit Metal"""
__version__ = metal_metadata["Version"]
__license__ = metal_metadata["License-Expression"]
__author__ = metal_metadata["Author"]
__copyright__ = "Copyright IBM 2019-2020"
__status__ = "Development"

###########################################################################
### Windows OS catch for library geopandas not installed with setup.py
### TODO: Check if this is still needed with uv_build.

import os

if os.name == "nt":
    try:
        import geopandas
    except ImportError:
        print(
            " \
            QISKIT METAL INFORMATION: >>>>>>>>>> One last installation step. <<<<<<<<<<<\n \
            >>>>>> Packages fiona and gdal have a known install issue on Windows. <<<<<<\n \
            >>>>>>>>>> geopandas depends on fiona, and fiona depends on gdal. <<<<<<<<<<\n \
            >> To prevent the unavoidable pip installation fail, we excluded geopandas <\n \
            >>>>>> from the list of qiskit-metal package dependencies in Windows. <<<<<<\n \
            >>>>>>>> Before you can use Qiskit Metal, please install geopandas. <<<<<<<<\n \
            >>>> For more information, you can follow the instructions on this FAQ <<<<<\n \
            >>>>>>>>>>>>> https://qiskit-community.github.io/qiskit-metal/faq.html <<<<<<<<<<<<<<\n"
        )
        raise


###########################################################################
### Basic Setups
## Qt backend setup is now opt-in.
##
## Historically this module always called ``__setup_Qt_backend()`` at
## import time, which forced ``import qiskit_metal`` to drag in PySide6
## (PyQt6) and switch matplotlib's backend to ``QtAgg``. That's the
## right behavior for users running the desktop ``MetalGUI``, but it
## broke headless / Jupyter / Colab / Binder workflows where PySide6
## either isn't installed or shouldn't be used.
##
## The function is still here (renamed and public as
## ``setup_qt_backend``), but is no longer called on import. It is
## invoked automatically by ``MetalGUI.__init__`` so users running the
## desktop GUI don't have to think about it. Headless users — the
## ``qm.view(design)`` path — never trigger it.

_qt_backend_initialized = False


def setup_qt_backend():
    """Configure Qt application attributes and switch matplotlib to
    the ``QtAgg`` backend.

    Idempotent — safe to call multiple times; subsequent calls are
    no-ops. Called automatically by ``MetalGUI.__init__``. End users
    rarely need to call this directly.

    Set the ``QISKIT_METAL_HEADLESS`` environment variable to any
    non-empty value to skip the matplotlib-backend switch (useful in
    test runners and CI).
    """
    global _qt_backend_initialized
    if _qt_backend_initialized:
        return

    # When in vscode and in debug-mode, may want to comment
    # next line out, "os.environ["QT_API"] = "pyside2""
    os.environ["QT_API"] = "pyside6"

    from PySide6 import QtCore  # , QtWidgets
    from PySide6.QtCore import Qt

    def set_attribute(name: str, value=True):
        """Describes attributes that change the behavior of
        application-wide features."""
        if hasattr(Qt, name):
            attr = getattr(Qt, name)
            if not QtCore.QCoreApplication.testAttribute(attr) == value:
                QtCore.QCoreApplication.setAttribute(attr, value)

    if QtCore.QCoreApplication.instance() is None:
        # No application launched yet — set the global attributes
        # before the first QApplication is constructed.
        set_attribute("AA_ShareOpenGLContexts")
        set_attribute("AA_EnableHighDpiScaling")
        set_attribute("AA_UseHighDpiPixmaps")

    if not os.getenv("QISKIT_METAL_HEADLESS", None):
        import matplotlib as mpl

        mpl.use("QtAgg")
        import matplotlib.pyplot as plt

        plt.ion()  # interactive

    _qt_backend_initialized = True


## Setup logging
from qiskit_metal import config
from qiskit_metal.toolbox_python._logging import setup_logger

logger = setup_logger(
    "metal", config.log.format, config.log.datefmt, capture_warnings=True
)  # type: logging.Logger
del setup_logger

###########################################################################
### User-accessible scope

# Metal Dict
from qiskit_metal.toolbox_python.attr_dict import Dict

# Due to order of imports
from qiskit_metal._is_design import is_component, is_design

# Core modules for user to use
from qiskit_metal.toolbox_metal.parsing import is_true
from qiskit_metal import (
    analyses,
    designs,
    draw,
    qgeometries,
    qlibrary,
    renderers,
    toolbox_metal,
    toolbox_python,
)

# Metal GUI and the matplotlib plotting helper are lazy attributes —
# importing them eagerly pulls in PySide6 (via ``_gui.main_window``)
# and Qt-tainted matplotlib helpers (via ``mpl_interaction``). For
# headless users running ``qm.view(design)`` from a script or Jupyter
# notebook, this means ``import qiskit_metal`` no longer requires
# PySide6 to be installed.
#
# Access via ``qm.MetalGUI`` or ``qm.plt`` — both work as before, but
# only trigger the heavy import on first use.


def __getattr__(name):
    if name == "MetalGUI":
        from qiskit_metal._gui.main_window import MetalGUI

        return MetalGUI
    if name == "plt":
        from qiskit_metal.renderers.renderer_mpl import mpl_toolbox

        return mpl_toolbox
    raise AttributeError(f"module 'qiskit_metal' has no attribute {name!r}")


# Utility functions
from qiskit_metal.toolbox_python.display import Headings

# Common-use
from qiskit_metal.qlibrary import QComponent

# Import default renderers
from qiskit_metal.renderers import setup_renderers
from qiskit_metal.toolbox_metal.about import about, open_docs

# Headless matplotlib viewer (``qm.view(design)``) — no Qt required.
from qiskit_metal.viewer import view


# -----------------------------------------------------------------------------
# Upcoming-breaking-change notice: package & import path rename
# -----------------------------------------------------------------------------
# Heads-up for current users: a future major release (target v0.8 or v1.0)
# will rename the Python import path from ``qiskit_metal`` to
# ``quantum_metal`` to match the PyPI package name. Update your imports
# ahead of that release. The PyPI package ``quantum-metal`` already
# ships as the canonical wheel; only the import path is changing next.
#
# Fires once per process via Python's default warning deduplication.
# Silence with ``QISKIT_METAL_SUPPRESS_RENAME_WARNING=1`` or via
# ``warnings.filterwarnings("ignore", category=FutureWarning, module="qiskit_metal")``.
def _maybe_warn_import_rename() -> None:
    import os
    import warnings

    if os.environ.get("QISKIT_METAL_SUPPRESS_RENAME_WARNING") == "1":
        return

    msg = (
        "A future major release of quantum-metal (target v0.8 / v1.0) "
        "will rename the Python import path from `qiskit_metal` to "
        "`quantum_metal` to match the PyPI package name. Plan to "
        "update your imports ahead of that release. See ROADMAP.md "
        "and the README rebrand notice. Suppress this warning with "
        "QISKIT_METAL_SUPPRESS_RENAME_WARNING=1."
    )

    # Log via metal's logger so the message is *visible* by default. The
    # logger fires regardless of ``logging.captureWarnings(True)`` (set
    # by ``setup_logger`` higher in this file), which would otherwise
    # silently redirect a plain ``warnings.warn`` to a no-handler logger.
    logger.warning("[FutureWarning] %s", msg)

    # Also raise via the warnings module so programmatic callers (tests,
    # ``warnings.catch_warnings``, etc.) can detect the upcoming change.
    warnings.warn(msg, FutureWarning, stacklevel=1)


_maybe_warn_import_rename()
del _maybe_warn_import_rename
