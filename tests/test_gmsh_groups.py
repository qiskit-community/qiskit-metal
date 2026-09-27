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
"""QGmshRenderer.group_map: every physical group with its role, net and
material (renderers/renderer_gmsh/groups.py). Needs gmsh; skipped without."""

import unittest


def _gmsh_importable():
    try:
        import gmsh  # noqa: F401

        return True
    except Exception:
        return False


OPEN = [("Q1", "coupler1"), ("Q1", "coupler2"), ("Q1", "readout")]


def _design():
    from qiskit_metal import designs
    from qiskit_metal.qlibrary.qubits.transmon_pocket_6 import TransmonPocket6

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


@unittest.skipUnless(_gmsh_importable(), "gmsh not installed (optional [mesh] extra)")
class TestGroupMap(unittest.TestCase):
    def render(self, **options):
        from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

        renderer = QGmshRenderer(_design())
        renderer.options.update(options)
        renderer.render_design(open_pins=OPEN, mesh_geoms=False)
        return renderer

    def test_every_group_once_with_the_right_dimension(self):
        import gmsh

        r = self.render()
        try:
            named = {
                (name, tag)
                for entries in r.physical_groups.values()
                for name, tag in entries.items()
            }
            mapped = [(g.name, g.tag) for g in r.group_map]
            self.assertEqual(len(mapped), len(set(mapped)))
            self.assertEqual(set(mapped), named)
            for group in r.group_map:
                with self.subTest(group=group.name):
                    self.assertTrue(
                        gmsh.model.getEntitiesForPhysicalGroup(
                            group.dim, group.tag
                        ).size
                    )
        finally:
            r.close()

    def test_roles_nets_and_materials(self):
        from qiskit_metal.renderers.renderer_gmsh.groups import Role

        r = self.render()
        r.close()
        gm = r.group_map  # built after close: no gmsh session needed
        pad = gm.get("Q1_pad_top_sfs")
        self.assertEqual(
            (pad.role, pad.dim, pad.net), (Role.CONDUCTOR, 2, "pad_top_Q1")
        )
        self.assertEqual(
            (pad.component, pad.qgeometry, pad.surfaces_of),
            ("Q1", "pad_top", "Q1_pad_top"),
        )
        self.assertEqual(gm.get("Q1_readout_wire").net, "readout_connector_pad_Q1")
        ground = gm.get("ground_plane_(layer 1)")
        self.assertEqual(
            (ground.role, ground.net, ground.material),
            (Role.GROUND, "ground_main_plane", "pec"),
        )
        substrate = gm.get("dielectric_(layer 3)")
        self.assertEqual(
            (substrate.role, substrate.dim, substrate.material),
            (Role.DIELECTRIC, 3, "silicon"),
        )
        self.assertEqual(gm.get("vacuum_box").role, Role.VACUUM)
        self.assertEqual(gm.get("vacuum_box_sfs").role, Role.OUTER_FACE)
        junction = gm.get("Q1_rect_jj")
        self.assertEqual(
            (junction.role, junction.component, junction.qgeometry),
            (Role.JUNCTION, "Q1", "rect_jj"),
        )
        self.assertEqual(
            gm.tags(role=Role.CONDUCTOR, dim=2, net="pad_top_Q1"),
            [r.physical_groups[1]["Q1_pad_top_sfs"]],
        )
        self.assertEqual(gm.nets()[:1], ["readout_connector_pad_Q1"])
        self.assertIn("ground_main_plane", gm.nets())
        self.assertEqual(gm.select(side="x-"), [])  # outer walls are opt-in
        with self.assertRaises(ValueError):
            gm.select(colour="red")

    def test_outer_wall_groups_are_opt_in(self):
        import gmsh

        r = self.render(outer_face_groups=True)
        try:
            walls = {g.side: g for g in r.group_map if g.side}
            self.assertEqual(sorted(walls), ["x+", "x-", "y+", "y-", "z+", "z-"])
            each = set()
            for g in walls.values():
                each |= set(gmsh.model.getEntitiesForPhysicalGroup(2, g.tag))
            outer = set(
                gmsh.model.getEntitiesForPhysicalGroup(
                    2, r.physical_groups["global"]["vacuum_box_sfs"]
                )
            )
            self.assertEqual(each, outer)
        finally:
            r.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
