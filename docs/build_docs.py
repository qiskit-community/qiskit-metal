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

# clear old tutorials - in case there were updates
import glob
raw_tutorials_path = os.path.join(path, 'tut', 'tutorials')
raw_tutorials_files = os.path.join(path, 'tut', 'tutorials', '*.ipynb')

files = glob.glob(raw_tutorials_files)
for file in files:
    os.remove(file)

# copy specific tutorials from the tutorials directory we want to explicitly include in the docs
import shutil
raw_origial_files = Path(qiskit_metal.__file__).parent.parent / 'tutorials'

files_to_copy = [[
    Path(raw_origial_files, 'Deep Dive.ipynb'),
    Path(raw_tutorials_path, 'Deep Dive.ipynb')
],
                 [
                     Path(raw_origial_files, '2 Front End User',
                          '2.1 My first custom QComponent',
                          '2.1 My First Custom QComponent.ipynb'),
                     Path(raw_tutorials_path,
                          'My First Custom QComponent.ipynb')
                 ],
                 [
                     Path(raw_origial_files, '2 Front End User',
                          '2.3 My first QDesign', 'Full Chip Design.ipynb'),
                     Path(raw_tutorials_path, 'Full Chip Design.ipynb')
                 ],
                 [
                     Path(raw_origial_files, '3 QComponent Designer',
                          '3.2 Creating a QComponent - Advanced.ipynb'),
                     Path(raw_tutorials_path, 'Creating a QComponent.ipynb')
                 ],
                 [
                     Path(raw_origial_files, '4 Plugin Developer',
                          'Create new QRenderer.ipynb'),
                     Path(raw_tutorials_path, 'Create new QRenderer.ipynb')
                 ]]

for orig, dest in files_to_copy:
    shutil.copy(orig, dest)

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
