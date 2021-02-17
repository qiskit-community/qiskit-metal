# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""
Qiskit Metal main unit test functionality.

Created on Wed Apr 22 08:55:40 2020
@author: Jeremy D. Drysdale
"""

import os
import fnmatch
import sys
import subprocess

if __name__ == '__main__':
    LIST_OF_FILES = os.listdir('.')
    PATTERN = "test*.py"
    print("====> Running the entire test suite now...")
    ERRORS_EXIST = 0
    for entry in LIST_OF_FILES:
        if fnmatch.fnmatch(entry, PATTERN):
            if entry != sys.argv[0]:
                print("Running ", entry, " tests...")
                cmd = 'pytest ' + entry
                error_back = subprocess.call(cmd, shell=True)
                if error_back != 3221225477:  # access violation
                    ERRORS_EXIST += error_back
                print("")

    print("All tests complete")
    if ERRORS_EXIST == 0:
        print("Congratulations, all the tests PASSED!")
        print("Have a nice day...")
    else:
        print("One or more tests have FAILED!")
        print("Scroll up to review the results")
