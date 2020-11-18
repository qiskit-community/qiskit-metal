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
    $ python docs/build_docs.py
"""

import shlex
import subprocess
cmd = "conda install -y -c conda-forge sphinx numpydoc sphinx_rtd_theme sphinx-automodapi jupyter_sphinx"
print(f'\n\n*** Installing pre-requisite packages to build the docs***\n$ {cmd}')
scmd = shlex.split(cmd)
result = subprocess.run(scmd, stdout=subprocess.PIPE, check=False)
stderr = result.stderr
stdout = result.stdout
returncode = result.returncode
print(f'\n****Exited with {returncode}')
if stdout:
	print(f'\n****stdout****\n{stdout.decode()}')
if stderr:
	print(f'\n****stderr****\n{stderr.decode()}')
print("Pre-requisite installation Complete!")

import os
import sys
print(sys.argv)
fn = sys.argv[0]
path = os.path.dirname(fn)

sphinxopts  = ""
sphinxbuild = "sphinx-build"
sourcedir   = path + "/."
builddir    = path + "/build"

with open(path + "/.buildingdocs", "w") as flag_file:
	flag_file.write("makedocs")
	cmd_make = sphinxbuild + " -b html " + sourcedir + " " + builddir + " " + sphinxopts
	print(f'\n\n*** Running the build***\n$ {cmd_make}')
	scmd = shlex.split(cmd_make)
	result = subprocess.run(scmd, stdout=subprocess.PIPE, check=False)
	stderr = result.stderr
	stdout = result.stdout
	returncode = result.returncode
	print(f'\n****Exited with {returncode}')
	if stdout:
		print(f'\n****stdout****\n{stdout.decode()}')
	if stderr:
		print(f'\n****stderr****\n{stderr.decode()}')

import os
os.remove(path + "/.buildingdocs")
print("Build Complete!")