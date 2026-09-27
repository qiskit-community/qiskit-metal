"""Rebuilding a component keeps its pin connections.

Before the fix, ``QComponent.rebuild`` dropped every net of the component, so
connections made with ``design.connect_pins`` vanished on any rebuild (and the
partner pin kept a stale net id). Routes were unaffected because they
reconnect inside ``make``.
"""

import unittest

from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround


def _net_pairs(design):
    df = design.net_info
    return sorted(
        tuple(sorted(zip(g["component_id"], g["pin_name"])))
        for _, g in df.groupby("net_id")
    )


class TestRebuildKeepsConnections(unittest.TestCase):
    def setUp(self):
        self.design = designs.DesignPlanar()
        self.q = TransmonPocket(
            self.design, "Q1", options=dict(connection_pads=dict(a=dict()))
        )
        self.otg = OpenToGround(self.design, "OTG", options=dict(pos_x="1mm"))
        self.design.connect_pins(self.q.id, "a", self.otg.id, "open")

    def test_component_rebuild_restores_manual_connection(self):
        before = _net_pairs(self.design)
        self.q.rebuild()
        self.assertEqual(_net_pairs(self.design), before)
        self.assertNotEqual(self.q.pins["a"].net_id, 0)
        self.assertEqual(self.q.pins["a"].net_id, self.otg.pins["open"].net_id)

    def test_design_rebuild_restores_manual_connection(self):
        before = _net_pairs(self.design)
        self.design.rebuild()
        self.assertEqual(_net_pairs(self.design), before)

    def test_repeated_rebuilds_are_stable(self):
        before = _net_pairs(self.design)
        for _ in range(3):
            self.design.rebuild()
        self.assertEqual(_net_pairs(self.design), before)
        self.assertEqual(len(self.design.net_info), 2)


class TestRebuildWithRoutes(unittest.TestCase):
    def setUp(self):
        self.design = designs.DesignPlanar()
        pads = dict(connection_pads=dict(a=dict()))
        self.q1 = TransmonPocket(self.design, "Q1", options=dict(pos_x="-1mm", **pads))
        self.q2 = TransmonPocket(self.design, "Q2", options=dict(pos_x="1mm", **pads))
        self.q3 = TransmonPocket(
            self.design, "Q3", options=dict(pos_x="1mm", pos_y="1mm", **pads)
        )
        self.route = RouteStraight(
            self.design,
            "R",
            options=dict(
                pin_inputs=dict(
                    start_pin=dict(component="Q1", pin="a"),
                    end_pin=dict(component="Q2", pin="a"),
                )
            ),
        )

    def test_route_rebuild_does_not_duplicate_nets(self):
        before = _net_pairs(self.design)
        self.design.rebuild()
        self.assertEqual(_net_pairs(self.design), before)

    def test_retargeted_route_releases_old_partner(self):
        self.route.options.pin_inputs.end_pin.component = "Q3"
        self.route.rebuild()
        self.assertEqual(self.q2.pins["a"].net_id, 0)
        self.assertNotEqual(self.q3.pins["a"].net_id, 0)
        self.assertEqual(self.q3.pins["a"].net_id, self.route.pins["end"].net_id)


if __name__ == "__main__":
    unittest.main()
