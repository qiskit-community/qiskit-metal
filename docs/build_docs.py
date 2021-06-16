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
"""An automated process to build docs locally.

Run using:     $ python <path>/build_docs.py build_docs.py needs to be
in the same folder as the Makefile
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
    cmd1 = "conda install -y -c conda-forge sphinx numpydoc sphinx-automodapi jupyter_sphinx nbsphinx"
    print(
        f'\n*** Installing pre-requisite packages to build the docs***\n$ {cmd1}'
    )
    scmd = shlex.split(cmd1)

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
    import jupyter_nbgallery
except ImportError:
    cmd2 = "python -m pip install qiskit-sphinx-theme jupyter_nbgallery"
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

try:
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
except KeyboardInterrupt:
    print("\nTerminating... please wait")
    os.remove('.buildingdocs')
    exit(1)

os.chdir(pwd)

# for local build, copy from _build to build directory
print("Copying locally to build directory\n")
import shutil

original = Path(pwd, 'docs', '_build')
destination = Path(pwd, 'docs', 'build')
if os.path.exists(destination):
    shutil.rmtree(destination)
shutil.copytree(original, destination)

print("Build Complete!")
