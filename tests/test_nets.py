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
"""Galvanic nets (toolbox_metal/nets.py), moved from QElmerRenderer.

The expected nets are what QElmerRenderer produced before the move (checked
against the previous code on the same designs, together with the Elmer input
file it writes). Shapely only; no gmsh."""

import unittest

from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.qubits.transmon_pocket_6 import TransmonPocket6
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from qiskit_metal.toolbox_metal.nets import (
    component_ids,
    layer_thickness_z,
    nets_for_design,
)

ALL_OPEN = [("Q1", "coupler1"), ("Q1", "coupler2"), ("Q1", "readout")]


def transmon_4_19():
    """The design of tutorial 4.19."""
    design = designs.MultiPlanar({}, True)
    TransmonPocket6(
        design,
        "Q1",
        options=dict(
            connection_pads=dict(
                readout=dict(loc_W=0, loc_H=-1),
                coupler1=dict(loc_W=-1, loc_H=1),
                coupler2=dict(loc_W=1, loc_H=1),
            )
        ),
    )
    design.rebuild()
    return design


class TestNets(unittest.TestCase):
    def test_tutorial_4_19_nets_are_unchanged(self):
        nets = nets_for_design(transmon_4_19(), open_pins=ALL_OPEN)
        self.assertEqual(
            nets.as_elmer_dict(),
            {
                "gnd": [],
                0: ["Q1_readout_wire", "Q1_readout_connector_pad"],
                1: ["Q1_coupler1_wire", "Q1_coupler1_connector_pad"],
                2: ["Q1_coupler2_wire", "Q1_coupler2_connector_pad"],
                3: ["Q1_pad_top"],
                4: ["Q1_pad_bot"],
            },
        )

    def test_a_pin_that_is_not_open_grounds_its_shape(self):
        nets = nets_for_design(transmon_4_19(), open_pins=ALL_OPEN[:2])
        self.assertEqual(
            nets.as_elmer_dict()["gnd"],
            ["Q1_readout_wire", "Q1_readout_connector_pad"],
        )

    def test_a_route_joins_the_pads_it_connects(self):
        design = designs.MultiPlanar({}, True)
        pads = dict(a=dict(loc_W=1, loc_H=1), b=dict(loc_W=-1, loc_H=-1))
        TransmonPocket(design, "Q1", options=dict(pos_x="-1mm", connection_pads=pads))
        TransmonPocket(
            design,
            "Q2",
            options=dict(
                pos_x="1mm",
                orientation="180",
                connection_pads=dict(a=dict(loc_W=1, loc_H=1)),
            ),
        )
        RouteMeander(
            design,
            "bus",
            options=Dict(
                total_length="2.4mm",
                fillet="60um",
                meander=Dict(spacing="150um"),
                pin_inputs=Dict(
                    start_pin=Dict(component="Q1", pin="a"),
                    end_pin=Dict(component="Q2", pin="a"),
                ),
            ),
        )
        design.rebuild()
        nets = nets_for_design(design, open_pins=[("Q1", "b")]).as_elmer_dict()
        self.assertEqual(
            nets[0],
            [
                "Q1_a_wire",
                "Q2_a_wire",
                "bus_trace",
                "Q1_a_connector_pad",
                "Q2_a_connector_pad",
            ],
        )
        self.assertEqual(nets["gnd"], [])
        self.assertEqual(len(nets), 7)

    def test_names_survive_a_deleted_component(self):
        """QElmerRenderer mapped component ids to names by position, so after
        a deletion Q1's shapes were named after the next component (and the
        Elmer setup then failed with a KeyError)."""
        design = designs.MultiPlanar({}, True)
        TransmonPocket(design, "Qgone", options=dict(pos_x="-2mm"))
        TransmonPocket(design, "Q1", options=dict(connection_pads=dict(a=dict())))
        OpenToGround(design, "open1", options=dict(pos_x="1mm", orientation="0"))
        design.delete_component("Qgone")
        design.rebuild()
        nets = nets_for_design(design, open_pins=[("Q1", "a")]).as_elmer_dict()
        self.assertEqual(nets[0], ["Q1_a_wire", "Q1_a_connector_pad"])
        self.assertEqual(nets[1], ["Q1_pad_top"])

    def test_labels(self):
        nets = nets_for_design(transmon_4_19(), open_pins=ALL_OPEN)
        self.assertEqual(
            nets.labels("q3d"),
            {
                "gnd": "ground_main_plane",
                0: "readout_connector_pad_Q1",
                1: "coupler1_connector_pad_Q1",
                2: "coupler2_connector_pad_Q1",
                3: "pad_top_Q1",
                4: "pad_bot_Q1",
            },
        )
        elmer = nets.labels("elmer")
        self.assertEqual(elmer["gnd"], "ground_plane")
        self.assertEqual(elmer[0], "Q1_readout_connector_pad")
        with self.assertRaises(ValueError):
            nets.labels("hfss")

    def test_selection_and_layers(self):
        design = transmon_4_19()
        self.assertEqual(component_ids(design, ["Q1"]), component_ids(design))
        with self.assertRaisesRegex(ValueError, "not in the design"):
            component_ids(design, ["nope"])
        thickness, z = layer_thickness_z(design, 1)
        self.assertAlmostEqual(thickness, 0.002)  # default layer stack: 2 um, in mm
        self.assertAlmostEqual(z, 0.0)
        with self.assertRaises(ValueError):
            layer_thickness_z(design, 99)


if __name__ == "__main__":
    unittest.main(verbosity=2)
