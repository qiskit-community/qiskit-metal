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
"""Galvanic nets: which metal shapes form one conductor, and which are ground.

Two shapes on the same chip belong to one net when they touch (shapely
distance 0) on the same layer, or on layers that meet in z. A shape is
grounded when one of its component's pins is neither open nor connected to
another pin, because that pin's trace meets the ground plane, or when its
pin is on the net of a ``short`` pin. A capacitance matrix has one row per
net, so every backend that solves for conductors reads the nets from here.

Moved from ``QElmerRenderer`` (``get_qgeometry_table``, ``assign_nets``,
``get_gnd_qgeoms``), whose output is unchanged; it needs no gmsh. See
``docs/architecture/solver_backends.md``, section 3.5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

import pandas as pd

from qiskit_metal import draw
from qiskit_metal.toolbox_metal.parsing import parse_value
from qiskit_metal.toolbox_python.utility_functions import concat_tables

if TYPE_CHECKING:
    from qiskit_metal.designs import QDesign

__all__ = [
    "GeomRef",
    "Net",
    "NetMap",
    "component_ids",
    "galvanic_nets",
    "grounded_geometries",
    "layer_thickness_z",
    "metal_geometry_table",
    "nets_for_design",
]


@dataclass(frozen=True)
class GeomRef:
    """A shape in the ``path`` or ``poly`` qgeometry table."""

    component: str
    name: str

    @property
    def elmer_name(self) -> str:
        """``<component>_<shape>``: the gmsh physical-group name."""
        return f"{self.component}_{self.name}"

    @property
    def q3d_name(self) -> str:
        """``<shape>_<component>``: the Ansys object name."""
        return f"{self.name}_{self.component}"


@dataclass(frozen=True)
class Net:
    """One conductor: its key (``"gnd"`` or 0, 1, ...), its shapes, its chip."""

    key: int | str
    members: tuple[GeomRef, ...]
    chip: str = "main"

    @property
    def is_ground(self) -> bool:
        """True for the ground net."""
        return self.key == "gnd"


@dataclass
class NetMap:
    """The nets of a design: the ground net first, then nets 0, 1, ..."""

    nets: list[Net] = field(default_factory=list)

    def as_elmer_dict(self) -> dict:
        """``{"gnd": [...], 0: [...], ...}`` of ``<component>_<shape>`` names,
        the form ``QElmerRenderer.nets`` has always had."""
        return {net.key: [m.elmer_name for m in net.members] for net in self.nets}

    def label(self, net: Net, style: Literal["q3d", "elmer"] = "q3d") -> str:
        """The name of a net in a capacitance matrix.

        ``"q3d"``: ``<shape>_<component>`` of the member that sorts first, and
        ``ground_<chip>_plane`` for ground, as Q3D names them. ``"elmer"``:
        ``<component>_<shape>`` of the last member, and ``ground_plane``, as
        ``QElmerRenderer`` labels its matrix.
        """
        if style == "q3d":
            if net.is_ground:
                return f"ground_{net.chip}_plane"
            return min(m.q3d_name for m in net.members)
        if style == "elmer":
            if net.is_ground:
                return "ground_plane"
            return net.members[-1].elmer_name
        raise ValueError(f"style must be 'q3d' or 'elmer', got {style!r}.")

    def labels(self, style: Literal["q3d", "elmer"] = "q3d") -> dict:
        """``{net key: label}`` for every net."""
        return {net.key: self.label(net, style) for net in self.nets}


# ---------------------------------------------------------------------------
# The shapes


def component_ids(design: "QDesign", components: list | None = None) -> list[int]:
    """Ids of the components to render; all of them when ``components`` is
    None or empty (or names every component).

    Raises:
        ValueError: for a name that is not in the design.
    """
    unique = set(components or [])
    unknown = sorted(name for name in unique if name not in design.name_to_id)
    if unknown:
        raise ValueError(f"Components not in the design: {unknown}.")
    if len(unique) in (0, len(design.components)):
        return list(set(design._components.keys()))
    return [design.name_to_id[name] for name in unique]


def layer_thickness_z(
    design: "QDesign", layer: int, datatype: int = 0
) -> tuple[float, float]:
    """``(thickness, z_coord)`` of a layer from the design's layer stack, in
    the design's units.

    Raises:
        ValueError: when the layer stack has no such layer.
    """
    result = design.ls.get_properties_for_layer_datatype(
        properties=["thickness", "z_coord"], layer_number=layer, datatype=datatype
    )
    if not result:
        raise ValueError(
            f"Could not find ['thickness', 'z_coord'] for the layer_number={layer}. "
            "Check your design and try again."
        )
    thickness, z = (
        parse_value(v, design.variables) if isinstance(v, str) else v for v in result
    )
    return thickness, z


def metal_geometry_table(
    design: "QDesign", comp_ids: list[int], metal_layers
) -> pd.DataFrame:
    """The ``path`` and ``poly`` shapes of the given components on the metal
    layers, not subtracted, with a ``min_z`` column (the lower face of each
    shape's layer), sorted by ``min_z``."""
    metal_layers = list(metal_layers)

    def mask(table):
        return (
            table["component"].isin(comp_ids)
            & ~table["subtract"]
            & table["layer"].isin(metal_layers)
        )

    def min_z(layer):
        thickness, z = layer_thickness_z(design, layer)
        return min(thickness + z, z)

    path_table = design.qgeometry.tables["path"]
    poly_table = design.qgeometry.tables["poly"]
    table = concat_tables(
        [path_table[mask(path_table)], poly_table[mask(poly_table)]],
        ignore_index=True,
    )
    table["min_z"] = table["layer"].apply(min_z)
    return table.sort_values(by=["min_z"], ignore_index=True)


# ---------------------------------------------------------------------------
# Ground and nets


def _names_by_id(design: "QDesign") -> dict[int, str]:
    return {comp.id: name for name, comp in design.components.items()}


def grounded_geometries(
    design: "QDesign", table: pd.DataFrame, open_pins: list | None = None
) -> list[str]:
    """``<component>_<shape>`` names of the shapes in ``table`` that are
    shorted to ground through one of their component's pins.

    A pin grounds its shape (the shape its ``middle`` point touches) unless it
    is open (in ``open_pins``) or connected to another pin; a pin on the net of
    a ``short`` pin grounds its shape too.
    """
    open_pins = open_pins if open_pins is not None else []
    names = _names_by_id(design)
    all_pins = [
        (comp, pin)
        for comp in design.components
        for pin in design.components[comp].pins
    ]

    nets_table = design.net_info
    gnd_nets = list(nets_table[nets_table["pin_name"] == "short"]["net_id"])
    port_nets_table = nets_table[~nets_table["net_id"].isin(gnd_nets)]
    port_pins = [
        (names[comp_id], pin)
        for comp_id, pin in zip(
            port_nets_table["component_id"], port_nets_table["pin_name"]
        )
    ]
    all_open_pins = set(port_pins) | {tuple(p) for p in open_pins}
    gnd_pins = [pin for pin in all_pins if pin not in all_open_pins]

    grounded = set()
    in_table = set(table["component"])
    for comp_name, pin_name in gnd_pins:
        comp = design.components[comp_name]
        if comp.id not in in_table:
            continue
        point = draw.Point(comp.pins[pin_name]["middle"])
        rows = table[table["component"] == comp.id]
        for _, row in rows.iterrows():
            if point.intersects(row["geometry"]):
                grounded.add(f"{comp_name}_{row['name']}")
    return list(grounded)


def galvanic_nets(
    design: "QDesign", table: pd.DataFrame, open_pins: list | None = None
) -> NetMap:
    """The galvanic nets of the shapes in ``table`` (from
    :func:`metal_geometry_table`).

    Returns:
        NetMap: the ground net (possibly empty) first, then nets numbered from
        0 in the order they are found.
    """
    names = _names_by_id(design)
    refs = [GeomRef(names[c], n) for c, n in zip(table["component"], table["name"])]
    phys = [ref.elmer_name for ref in refs]
    ref_of = dict(zip(phys, refs))
    chip_of = dict(zip(phys, table["chip"]))

    thickness_z = {}

    def layer_tz(layer):
        if layer not in thickness_z:
            thickness_z[layer] = layer_thickness_z(design, layer)
        return thickness_z[layer]

    # Union of touching shapes, in the order QElmerRenderer.assign_nets used.
    net_of = {k: -1 for k in phys}
    idxs = list(range(len(table)))
    netlist_id = 0
    while len(idxs) != 0:
        i = idxs.pop(0)
        row_i = table.iloc[i]
        thick_i, z_i = layer_tz(row_i["layer"])
        if net_of[phys[i]] == -1:
            net_of[phys[i]] = netlist_id
        for j in idxs:
            row_j = table.iloc[j]
            thick_j, z_j = layer_tz(row_j["layer"])
            layers_touch = (
                row_i["layer"] == row_j["layer"]
                or z_j == z_i
                or z_i + thick_i == z_j
                or z_j + thick_j == z_i
            )
            touching = row_i["geometry"].distance(row_j["geometry"]) == 0.0
            if touching and row_i["chip"] == row_j["chip"] and layers_touch:
                if net_of[phys[j]] == -1:
                    net_of[phys[j]] = net_of[phys[i]]
                elif net_of[phys[j]] != net_of[phys[i]]:
                    net_id_i = net_of[phys[i]]
                    for k, v in net_of.items():
                        if v == net_id_i:
                            net_of[k] = net_of[phys[j]]
        if -1 not in net_of.values():
            break
        netlist_id = max(net_of.values()) + 1

    grounded = set(grounded_geometries(design, table, open_pins))
    gnd_ids = {net for name, net in net_of.items() if name in grounded}

    groups = {"gnd": []}
    for name, net in net_of.items():
        if net in gnd_ids:
            groups["gnd"].append(name)
        else:
            groups.setdefault(net, []).append(name)

    nets = []
    for i, (key, members) in enumerate(groups.items()):
        key = "gnd" if key == "gnd" else i - 1
        chip = chip_of[members[0]] if members else "main"
        nets.append(Net(key, tuple(ref_of[m] for m in members), chip))
    return NetMap(nets)


def nets_for_design(
    design: "QDesign",
    components: list | None = None,
    open_pins: list | None = None,
    metal_layers=(1,),
) -> NetMap:
    """The galvanic nets of a design's selected components on its metal layers.

    Args:
        design (QDesign): a design with a layer stack (``MultiPlanar``).
        components (list, optional): component names; None: all.
        open_pins (list, optional): ``(component, pin)`` pins that end open.
        metal_layers (iterable): layer numbers that hold metal. Defaults to (1,).

    Returns:
        NetMap: the nets.
    """
    table = metal_geometry_table(
        design, component_ids(design, components), metal_layers
    )
    return galvanic_nets(design, table, open_pins)
