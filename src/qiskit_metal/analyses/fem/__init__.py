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
"""Finite-element solvers that run inside Python.

:mod:`qiskit_metal.analyses.fem.solver` meshes a chip in its package with
gmsh and solves it with scikit-fem: eigenmodes with lumped junctions, a port
reduced-order model, and electrostatics. Tutorials 4.41-4.45 use it. Needs
``gmsh`` and ``scikit-fem``, imported only when a mesh is built or a solver
runs.
"""

from qiskit_metal.analyses.fem.solver import (
    Electrostatics,
    MaxwellFEM,
    Mode,
    Package,
    PackageMesh,
    PortROM,
    emf_coupling,
    mesh_package,
    mirror_signs,
    package_from_design,
    plot_package_3d,
    unfold_quarter,
)

__all__ = [
    "Electrostatics",
    "MaxwellFEM",
    "Mode",
    "Package",
    "PackageMesh",
    "PortROM",
    "emf_coupling",
    "mesh_package",
    "mirror_signs",
    "package_from_design",
    "plot_package_3d",
    "unfold_quarter",
]
