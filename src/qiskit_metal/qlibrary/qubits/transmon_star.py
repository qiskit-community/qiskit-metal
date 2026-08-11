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

import math

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import BaseQubit


class TransmonStar(BaseQubit):
    """The base `TransmonStar` class.

    Inherits `BaseQubit` class.

    A transmon island with ``num_points`` radial arms evenly spaced around
    the center (``TransmonCross`` generalized from a fixed 4-arm plus sign
    to an arbitrary N-pointed star). Useful when a qubit needs more physical
    connections than a 4-arm cross has room for -- e.g. a lattice qubit that
    couples directly to several neighbors (by arm-tip proximity, the same
    "nodal" coupling a plain Xmon uses) *and* carries its own readout, XY,
    and Z lines.

    Arm 0 points along +x in the qubit's own (unrotated) frame; arm i points
    at ``360/num_points * i`` degrees counter-clockwise from there. Only arms
    named in ``connection_pads`` get a claw/gap connector pad and a pin --
    every other arm is left as a bare, unconnected stub ("dangling"), free
    for direct capacitive coupling to a neighboring component's arm, or
    simply unused.

    Add connectors to it using the `connection_pads` dictionary, same as
    `TransmonCross`, except each entry also needs an ``arm_index`` (which of
    the ``num_points`` arms it attaches to). See BaseQubit for more
    information.

    Sketch:
        Below is a sketch of the qubit with ``num_points=5``
        ::

                     arm 1
                       |
            arm 2 __ (island) __ arm 0
                       |
                     arm 3   arm 4

    .. image::
        TransmonStar.png

    .. meta::
        :description: Transmon Star

    BaseQubit Default Options:
        * connection_pads: Empty Dict -- The dictionary which contains all active connection lines for the qubit.
        * _default_connection_pads: empty Dict -- The default values for the (if any) connection lines of the qubit.

    Default Options:
        * num_points: 6 -- Number of radial arms around the island
        * arm_width: '20um' -- Width of the CPW center trace making up each arm
        * arm_length: '150um' -- Length of one arm (from center)
        * arm_gap: '20um' -- Width of the CPW gap making up each arm
        * junction_arm_index: 0 -- Which arm (by index, 0 to num_points-1) carries the junction
        * _default_connection_pads: Dict
            * arm_index: 0 -- Which arm (by index, 0 to num_points-1) this connector attaches to
            * connector_type: '0' -- 0 = Claw type, 1 = gap type
            * claw_length: '30um' -- Length of the claw 'arms', measured from the connector center trace
            * ground_spacing: '5um' -- Amount of ground plane between the connector and the arm (minimum should be based on fabrication capabilities)
            * ground_spacing_back: None -- Ground plane between the cpw-side (back) of the connector and the arm. Defaults to ground_spacing when None
            * claw_width: '10um' -- The width of the CPW center trace making up the claw/gap connector
            * claw_width_back: None -- The width of the back (towards the incoming CPW) of the claw connector. Defaults to claw_width when None
            * claw_gap: '6um' -- The gap of the CPW center trace making up the claw/gap connector
            * claw_cpw_length: '40um' -- Length of the CPW lead on the connector, before the claw/gap itself
            * claw_cpw_width: '10um' -- Width of the CPW lead on the connector
    """

    default_options = Dict(
        num_points=6,
        arm_width="20um",
        arm_length="150um",
        arm_gap="20um",
        junction_arm_index=0,
        chip="main",
        _default_connection_pads=Dict(
            arm_index=0,
            connector_type="0",  # 0 = Claw type, 1 = gap type
            claw_length="30um",
            ground_spacing="5um",
            ground_spacing_back=None,  # Defaults to `ground_spacing` when None
            claw_width="10um",
            claw_width_back=None,  # Defaults to `claw_width` when None
            claw_gap="6um",
            claw_cpw_length="40um",
            claw_cpw_width="10um",
        ),
    )
    """Default options."""

    component_metadata = Dict(
        short_name="Star",
        _qgeometry_table_poly="True",
        _qgeometry_table_junction="True",
    )
    """Component metadata"""

    TOOLTIP = """N-armed star transmon."""

    ##############################################MAKE######################################################

    def make(self):
        """This is executed by the GUI/user to generate the qgeometry for the
        component."""
        self.make_island()
        self.make_connection_pads()

    ###################################TRANSMON#############################################################

    def _arm_angle_deg(self, arm_index: int) -> float:
        """Angle of ``arm_index``, in degrees, in the qubit's own
        (unrotated) frame -- arm 0 along +x, counter-clockwise from there."""
        return 360.0 * arm_index / self.p.num_points

    def make_island(self):
        """Makes the N-armed star island: N radial lines from the center,
        buffered into CPW-width arms and unioned (the same technique
        `TransmonCross` uses for its 2 crossing lines, generalized to N),
        plus a junction on one arm."""
        p = self.p

        num_points = int(p.num_points)
        arm_width = p.arm_width
        arm_length = p.arm_length
        arm_gap = p.arm_gap
        chip = p.chip

        arm_lines = [
            draw.LineString(
                [
                    (0, 0),
                    (
                        arm_length * math.cos(math.radians(self._arm_angle_deg(i))),
                        arm_length * math.sin(math.radians(self._arm_angle_deg(i))),
                    ),
                ]
            )
            for i in range(num_points)
        ]
        star_line = draw.shapely.ops.unary_union(arm_lines)
        star = star_line.buffer(arm_width / 2, cap_style=2)
        star_etch = star.buffer(arm_gap, cap_style=3, join_style=2)

        # The junction/SQUID, just past the tip of the designated arm.
        junction_angle = math.radians(self._arm_angle_deg(p.junction_arm_index))
        jj_tip = (
            arm_length * math.cos(junction_angle),
            arm_length * math.sin(junction_angle),
        )
        jj_end = (
            (arm_length + arm_gap) * math.cos(junction_angle),
            (arm_length + arm_gap) * math.sin(junction_angle),
        )
        rect_jj = draw.LineString([jj_tip, jj_end])

        polys = [star, star_etch, rect_jj]
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [star, star_etch, rect_jj] = polys

        self.add_qgeometry("poly", dict(star=star), chip=chip)
        self.add_qgeometry("poly", dict(star_etch=star_etch), subtract=True, chip=chip)
        self.add_qgeometry(
            "junction", dict(rect_jj=rect_jj), width=arm_width, chip=chip
        )

    ############################CONNECTORS##################################################################################################

    def make_connection_pads(self):
        """Goes through connector pads and makes each one -- only arms named
        in `connection_pads` get a connector; every other arm stays a bare,
        unconnected stub."""
        for name in self.options.connection_pads:
            self.make_connection_pad(name)

    def make_connection_pad(self, name: str):
        """Makes an individual connector pad on one arm.

        Args:
            name (str) : Name of the connector pad
        """
        p = self.p
        arm_width = p.arm_width
        arm_length = p.arm_length
        arm_gap = p.arm_gap
        chip = p.chip

        pc = self.p.connection_pads[name]  # parser on connector options
        c_g = pc.claw_gap
        c_l = pc.claw_length
        c_w = pc.claw_width
        c_c_w = pc.claw_cpw_width
        c_c_l = pc.claw_cpw_length
        g_s = pc.ground_spacing

        # claw_width_back / ground_spacing_back default to claw_width /
        # ground_spacing when unset, so the default geometry is unchanged.
        c_w_b = pc.claw_width_back
        if c_w_b is None:
            c_w_b = c_w
        g_s_b = pc.ground_spacing_back
        if g_s_b is None:
            g_s_b = g_s

        claw_cpw = draw.box(-c_w_b, -c_c_w / 2, -c_c_l - c_w_b, c_c_w / 2)

        if pc.connector_type == 0:  # Claw connector
            t_claw_height = 2 * c_g + 2 * c_w + 2 * g_s + 2 * arm_gap + arm_width

            claw_base = draw.box(-c_w_b, -(t_claw_height) / 2, c_l, t_claw_height / 2)
            claw_subtract = draw.box(
                0, -t_claw_height / 2 + c_w, c_l, t_claw_height / 2 - c_w
            )
            claw_base = claw_base.difference(claw_subtract)

            connector_arm = draw.shapely.ops.unary_union([claw_base, claw_cpw])
            connector_etcher = draw.buffer(connector_arm, c_g)
        else:
            connector_arm = draw.box(0, -c_w / 2, -4 * c_w, c_w / 2)
            connector_etcher = draw.buffer(connector_arm, c_g)

        port_line = draw.LineString(
            [(-c_c_l - c_w_b, -c_c_w / 2), (-c_c_l - c_w_b, c_c_w / 2)]
        )

        # The connector is built pointing toward -x (translated to a large
        # negative x below), so it needs a further 180 deg on top of the
        # arm's own angle to end up pointing outward along that arm.
        arm_angle = self._arm_angle_deg(int(pc.arm_index)) - 180

        # Rotates and translates the connector polygons (and temporary port_line)
        polys = [connector_arm, connector_etcher, port_line]
        polys = draw.translate(polys, -(arm_length + arm_gap + g_s_b + c_g), 0)
        polys = draw.rotate(polys, arm_angle, origin=(0, 0))
        polys = draw.rotate(polys, p.orientation, origin=(0, 0))
        polys = draw.translate(polys, p.pos_x, p.pos_y)
        [connector_arm, connector_etcher, port_line] = polys

        self.add_qgeometry("poly", {f"{name}_connector_arm": connector_arm}, chip=chip)
        self.add_qgeometry(
            "poly",
            {f"{name}_connector_etcher": connector_etcher},
            subtract=True,
            chip=chip,
        )

        self.add_pin(name, port_line.coords, c_c_w)
