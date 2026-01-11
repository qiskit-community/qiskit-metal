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

# pylint: disable=protected-access
# pylint: disable-msg=relative-beyond-top-level
# pylint: disable-msg=broad-except
"""Saving and load metal data."""

import pickle
#from ..designs.base
from qiskit_metal.toolbox_python.utility_functions import log_error_easy

__all__ = ['save_metal', 'load_metal_design']


def save_metal(filename: str, design):
    """Save metal0.

    Args:
        filename (str): File path
        design (QDesign): Design obejct Metal_Design_Base

    Returns:
        bool: True is sucessful, False otherwise

    Raises:
        Exception: Save error
    """
    result = False

    # Do not pickle the following -- THis is issue with picking
    self = design  # cludge for lazy tying
    logger = self.logger
    self.logger = None

    # Pickle
    # TODO: Right now just does pickle. Need to serialize object into JSON
    # or similar. Then recreate components.
    try:
        pickle.dump(self, open(filename, "wb"))

        result = True
    except Exception as e:
        # handle errors here? such as PermissionError
        text = f'ERROR WHILE SAVING: {e}'
        log_error_easy(logger, post_text=text)
        # print(text)
        # logger.error(text)
        result = False

    # restore -- also need to do in the load function
    self.logger = logger
    return result


# pylint: disable-msg=import-outside-toplevel
def load_metal_design(filename: str):
    """Load metal design.

    Args:
        filename (str): File path

    Returns:
        picked QDesign: The pickled design object and updates if asked the param dicts for defaults
    """
    design = pickle.load(open(filename, "rb"))
    design.save_path = str(
        filename)  # Set the place from where we loaded the design

    # Restore
    from .. import logger
    design.logger = logger  #TODO: fix from save pikcle

    return design
