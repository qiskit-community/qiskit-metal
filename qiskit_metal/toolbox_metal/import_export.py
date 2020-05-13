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

# pylint: disable=protected-access

'''
Saving and load metal data

@author: Zlatko K. Minev (IBM)
@date: 2019-09
'''

import pickle
#from ..designs.base
from ..toolbox_python.utility_functions import log_error_easy

def save_metal(filename : str, design):
    """
    filename: str path
    design : design obejct Metal_Design_Base
    """
    result = False

    # Do not pickle the following -- THis is issue with picking
    self = design # cludge for lazy tying
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


def load_metal_design(filename : str, do_update=True):
    """
    Returns the pickled design object and updates if asked the param dicts for
    defaults

    do_update: True
        updates DEFAULT, DEFAULT_OPTIONS with the params saved in the file
    """
    design = pickle.load(open(filename, "rb"))
    design.save_path = str(filename) # Set the place from where we loaded the design

    # Restore
    from .. import logger
    design.logger = logger #TODO: fix from save pikcle

    if do_update:
        from ..config import DEFAULT, DEFAULT_OPTIONS

        DEFAULT.clear()
        DEFAULT_OPTIONS.clear()

        # Will this work? I need to change the pointers,
        # so that they are linked after
        DEFAULT.update(design._defaults)
        DEFAULT_OPTIONS.update(design._default_options)

    return design
