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

# pylint: disable=invalid-name
# pylint: disable=unused-import
"""File contains some config definitions.

Mostly internal.
"""

from .toolbox_python.attr_dict import Dict
from ._defaults import DefaultMetalOptions, DefaultOptionsRenderer

renderers_to_load = Dict(
    hfss=Dict(path_name='qiskit_metal.renderers.renderer_ansys.hfss_renderer',
              class_name='QHFSSRenderer'),
    q3d=Dict(path_name='qiskit_metal.renderers.renderer_ansys.q3d_renderer',
             class_name='QQ3DRenderer'),
    gds=Dict(path_name='qiskit_metal.renderers.renderer_gds.gds_renderer',
             class_name='QGDSRenderer'),
)
"""
Define the renderes to load. Just provide the module names here.
"""

GUI_CONFIG = Dict(
    load_metal_modules=Dict(Qubits='qiskit_metal.qlibrary.qubits',
                            TLines='qiskit_metal.qlibrary.tlines',
                            Terminations='qiskit_metal.qlibrary.terminations'),
    exclude_metal_classes=['Metal_Qubit'],
    tips=[
        'Right clicking the tree elements allows you to do neat things.',
        'You can show all connector names on the plot by clicking the connector '
        'icon in the plot toolbar.',
        'The gui and the Python code work synchronously. If you modify something '
        'in the gui, it will be reflected in your Python interpreter and vice versa. '
        'Note that the gui does not automatically refresh on all events if you update '
        'variables from the Python interpreter.',
        'Changed some object parameters? Click the <b>Remake</b> button in the main '
        'toolbar to recreate the polygons.',
        """<b>Log widget:</b> Right click the logger window to be able to change the log level and
        the loggers that are shown / hidden.""",
        """<b>All component widget:</b> Double click a component to zoom into it!""",
    ],
    logger=Dict(
        style=
        ".DEBUG {color: green;}\n.WARNING,.ERROR,.CRITICAL {color: red;}\n.'\
                'ERROR,.CRITICAL {font-weight: bold;}\n",
        num_lines=500,
        level='DEBUG',
        stream_to_std=False,  # stream to jupyter notebook
    ),
    main_window=Dict(
        title='Qiskit Metal — The Quantum Builder',
        auto_size=False,  # Autosize on creation of window
    ))
"""
GUI_CONFIG

**load_metal_modules**

---------------------------
Name of class folders that contain modules that will be available to be
created in the GUI

Conventions:
Assumes that the module file name is the same as the class name contained in it.
For example, provided `qiskit_metal.qubits` has `Metal_Transmon_Pocket.py`, the
gui will do
    `from qiskit_metal.qubits.Metal_Transmon_Pocket import Metal_Transmon_Pocket`


**tips**

---------------------------
Tips that the user can define to show in the gui. These rotate each time the gui is started.


**logger**

---------------------------
Logger settings


**main_window**

---------------------------
Main window defaults
"""

log = Dict(format='%(asctime)s %(levelname)s [%(funcName)s]: %(message)s',
           datefmt='%I:%M%p %Ss')
"""
A dictionary containing the log format for standard text and date/time
"""


def is_using_ipython():
    """Check if we're in IPython.

    Returns:
        bool -- True if ran in IPython
    """
    try:
        __IPYTHON__  # pylint: disable=undefined-variable, pointless-statement
        return True
    except NameError:
        return False


def is_building_docs():
    """Checks for the existance of the .buildingdocs file which is only present
    when building the docs.

    Returns:
        bool: True if .buildingdocs exists
    """
    from pathlib import Path  # pylint: disable=import-outside-toplevel
    build_docs_file = Path(__file__).parent.parent / "docs" / ".buildingdocs"
    return Path.exists(build_docs_file)


_ipython = is_using_ipython()

####################################################################################
# USER CONFIG
