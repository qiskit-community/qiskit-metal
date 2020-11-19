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
An automated process to build docs locally.

Run using:
    $ python <path>/build_docs.py
build_docs.py needs to be in the same folder as the Makefile
"""

import shlex
import subprocess
import os
import sys

cmd = "conda install -y -c conda-forge sphinx numpydoc sphinx_rtd_theme sphinx-automodapi jupyter_sphinx"
print(f'\n*** Installing pre-requisite packages to build the docs***\n$ {cmd}')
scmd = shlex.split(cmd)
result = subprocess.run(scmd, stdout=subprocess.PIPE, check=False, shell=True)
stderr = result.stderr
stdout = result.stdout
returncode = result.returncode
print(f'\n****Exited with {returncode}')
if stdout:
	print(f'****stdout****\n{stdout.decode()}')
if stderr:
	print(f'****stderr****\n{stderr.decode()}')
print("Pre-requisite installation Complete!")

print(sys.argv)
fn = sys.argv[0]
path = os.path.dirname(fn)
pwd = os.getcwd()

os.chdir(path)
print(f'\n*** Running the build***\n$ make html')
os.system("make html")
os.chdir(pwd)

print("Build Complete!")
