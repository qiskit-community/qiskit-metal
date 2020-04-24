# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019-2020.
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

import os, fnmatch, sys, subprocess

if __name__ == '__main__':
    listOfFiles = os.listdir('.')
    pattern = "*.py"
    print("====> Running the entire test suite now...")
    for entry in listOfFiles:
        if fnmatch.fnmatch(entry, pattern):
            if (entry != sys.argv[0]):
                print("Running ", entry, " tests...")
                cmd = 'python ' + entry
                subprocess.call(cmd, shell=True)
                print("")

    print("All tests complete")
    print("Scroll up to review the results")
