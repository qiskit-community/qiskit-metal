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

# first install prerequisite packages
try:
    import sphinx
    import numpydoc
    import sphinx_automodapi
    import jupyter_sphinx
    import nbsphinx
except ImportError:
    cmd = "conda install -y -c conda-forge sphinx numpydoc sphinx-automodapi jupyter_sphinx nbsphinx"
    print(
        f'\n*** Installing pre-requisite packages to build the docs***\n$ {cmd}'
    )
    scmd = shlex.split(cmd)

    try:
        result = subprocess.run(scmd, stdout=subprocess.PIPE, check=False)
    except FileNotFoundError:
        # some windows systems appear to require this switch
        result = subprocess.run(scmd,
                                stdout=subprocess.PIPE,
                                check=False,
                                shell=True)
    stderr = result.stderr
    stdout = result.stdout
    returncode = result.returncode
    print(f'\n****Exited with {returncode}')
    if stdout:
        print(f'****stdout****\n{stdout.decode()}')
    if stderr:
        print(f'****stderr****\n{stderr.decode()}')
    print("Conda pre-requisite installation Complete!")

try:
    import qiskit_sphinx_theme
except ImportError:
    cmd2 = "python -m pip install qiskit-sphinx-theme"
    print(
        f'\n*** Installing pre-requisite packages to build the docs***\n$ {cmd2}'
    )
    scmd = shlex.split(cmd2)
    try:
        result = subprocess.run(scmd, stdout=subprocess.PIPE, check=False)
    except FileNotFoundError:
        # some windows systems appear to require this switch
        result = subprocess.run(scmd,
                                stdout=subprocess.PIPE,
                                check=False,
                                shell=True)
    stderr = result.stderr
    stdout = result.stdout
    returncode = result.returncode
    print(f'\n****Exited with {returncode}')
    if stdout:
        print(f'****stdout****\n{stdout.decode()}')
    if stderr:
        print(f'****stderr****\n{stderr.decode()}')
    print("Pip pre-requisite installation Complete!")

# then build the docs
pwd = os.getcwd()
import qiskit_metal
from pathlib import Path

path = Path(qiskit_metal.__file__).parent.parent / 'docs'
os.chdir(path)
print(f'\n*** Running the build***\n$ make html')

from sys import platform

if platform == "darwin":
    scmd = shlex.split("make html")
    result = subprocess.run(scmd, stdout=subprocess.PIPE, check=False)
    stderr = result.stderr
    stdout = result.stdout
    returncode = result.returncode
    print(f'\n****Exited with {returncode}')
    if stdout:
        print(f'****stdout****\n{stdout.decode()}')
    if stderr:
        print(f'****stderr****\n{stderr.decode()}')
else:
    os.system("make html")

os.chdir(pwd)

print("Build Complete!")
