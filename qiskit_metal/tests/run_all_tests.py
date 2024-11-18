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
"""Qiskit Metal main unit test functionality."""
import os
import fnmatch
import sys
import subprocess

if __name__ == '__main__':
    LIST_OF_FILES = os.listdir('.')
    PATTERN = "test*.py"
    print("====> Running the entire test suite now...")
    ERRORS_EXIST = 0

    # Open log files
    with open("test_results.log", "w") as results_log, open("test_errors.log", "w") as errors_log:
        for entry in LIST_OF_FILES:
            if fnmatch.fnmatch(entry, PATTERN):
                if entry != sys.argv[0]:
                    print(f"Running {entry} tests...")
                    results_log.write(f"Running {entry} tests...\n")
                    
                    # Run the test and capture output
                    result = subprocess.run(
                        f"python {entry}",
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Write the stdout and stderr to test_results.log
                    results_log.write(result.stdout)
                    results_log.write(result.stderr)
                    results_log.write("\n")
                    
                    # If there's an error, write it to test_errors.log
                    if result.returncode != 0:
                        ERRORS_EXIST += 1
                        errors_log.write(f"Error in {entry}:\n")
                        errors_log.write(result.stderr)
                        errors_log.write("\n")
                    
                    print("")

        print("All tests complete")
        results_log.write("All tests complete\n")
        if ERRORS_EXIST == 0:
            print("Congratulations, all the tests PASSED!")
            print("Have a nice day...")
            results_log.write("Congratulations, all the tests PASSED!\n")
            results_log.write("Have a nice day...\n")
        else:
            print("One or more tests have FAILED!")
            print("Scroll up to review the results")
            results_log.write("One or more tests have FAILED!\n")
            results_log.write("Scroll up to review the results\n")
