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
"""Named physical groups with roles.

A finite-element solver sets materials on volumes and boundary conditions on
surfaces, both picked by physical-group tag. ``QGmshRenderer.physical_groups``
names the groups; :class:`PhysicalGroupMap` says what each one *is*: a
conductor on a given net, the ground plane, a dielectric of a given material,
the vacuum, a junction sheet, an outer wall. Solvers query it by role and
attribute instead of matching substrings of names.

Plain data; filled by ``QGmshRenderer.group_map``. See
``docs/architecture/solver_backends.md``, section 3.5.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, fields
from enum import Enum

__all__ = ["PhysicalGroup", "PhysicalGroupMap", "Role"]


class Role(str, Enum):
    """What a physical group is."""

    CONDUCTOR = "conductor"
    """Metal of a component: a volume, or its surfaces."""
    GROUND = "ground"
    """The ground plane of a metal layer: a volume, or its surfaces."""
    DIELECTRIC = "dielectric"
    """A dielectric layer: a volume, or its surfaces."""
    VACUUM = "vacuum"
    """The vacuum around the chip."""
    JUNCTION = "junction"
    """A Josephson junction's sheet, or (dim 1) its line."""
    PORT = "port"
    """A port: a lumped port's sheet or line, or a wave port's face."""
    OUTER_FACE = "outer_face"
    """Outer walls of the model; ``side`` is set for one wall."""
    SYMMETRY_FACE = "symmetry_face"
    """A face on a symmetry plane."""
    INTERFACE = "interface"
    """A thin lossy interface layer, for surface participation."""


@dataclass(frozen=True)
class PhysicalGroup:
    """One gmsh physical group.

    Attributes:
        name (str): its name in the mesh.
        dim (int): 3 for a volume, 2 for surfaces.
        tag (int): its gmsh physical tag.
        role (Role): what it is.
        layer (int, optional): its layer in the layer stack.
        component (str, optional): the component it comes from.
        qgeometry (str, optional): the component's shape name.
        net (str, optional): the net label of a conductor or ground
            (``<shape>_<component>`` or ``ground_<chip>_plane``).
        material (str, optional): the layer stack's material name.
        side (str, optional): ``"x-"`` ... ``"z+"`` for one outer wall (or
            the wall a wave port sits on).
        surfaces_of (str, optional): for a group of surfaces, the name of the
            volume group they bound.
        port (str, optional): the port's name, for a port group.
        direction (tuple, optional): unit vector (x, y) along which a lumped
            port's voltage is taken, from the first node to the second.
    """

    name: str
    dim: int
    tag: int
    role: Role
    layer: int | None = None
    component: str | None = None
    qgeometry: str | None = None
    net: str | None = None
    material: str | None = None
    side: str | None = None
    surfaces_of: str | None = None
    port: str | None = None
    direction: tuple | None = None


_FIELDS = {f.name for f in fields(PhysicalGroup)}


class PhysicalGroupMap:
    """The physical groups of a rendered model, queried by attribute.

    Example:
        ``group_map.tags(role=Role.CONDUCTOR, dim=2, net="pad_top_Q1")`` gives
        the tags of the surfaces of the ``pad_top_Q1`` net.
    """

    def __init__(self, groups=()):
        self._groups = list(groups)

    def __iter__(self) -> Iterator[PhysicalGroup]:
        return iter(self._groups)

    def __len__(self) -> int:
        return len(self._groups)

    def __repr__(self) -> str:
        return f"PhysicalGroupMap({len(self)} groups)"

    def select(self, **attrs) -> list[PhysicalGroup]:
        """The groups whose attributes equal all of ``attrs``."""
        unknown = set(attrs) - _FIELDS
        if unknown:
            raise ValueError(f"Unknown attributes {sorted(unknown)}.")
        return [
            g
            for g in self._groups
            if all(getattr(g, key) == value for key, value in attrs.items())
        ]

    def tags(self, **attrs) -> list[int]:
        """The tags of :meth:`select`."""
        return [g.tag for g in self.select(**attrs)]

    def get(self, name: str) -> PhysicalGroup | None:
        """The group with this name, or None."""
        for group in self._groups:
            if group.name == name:
                return group
        return None

    def nets(self) -> list[str]:
        """Net labels of the conductors and ground, in first-seen order."""
        return list(dict.fromkeys(g.net for g in self._groups if g.net is not None))
