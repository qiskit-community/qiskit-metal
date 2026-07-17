# -*- coding: utf-8 -*-

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
"""Airbridge — a ground-plane crossover that hops over a CPW trace."""

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import QComponent


class Airbridge(QComponent):
    """A single airbridge: two base-metal landing pads joined by an elevated
    bridge span that crosses over a CPW.

    Unlike a GDS-export-only helper, this is a first-class ``QComponent`` — its
    geometry lives in the design's QGeometry, so it renders in ``qm.view`` and
    is exported by every renderer (GDS today; a 3D/Ansys span is tracked
    separately). The bridge metal and the landing pads are emitted on separate
    layers so the two-step fabrication (base metal + bridge metal) is
    representable.

    .. image::
        Airbridge.png

    The geometry is intentionally factored as an *elevated crossover* (a span
    that sits above the base layer, joining two feet). Only the airbridge uses
    it today; the same shape could back other elevated interconnects in future
    without changing this class.

    Default Options:
        * crossover_length: '22um' -- Gap the bridge spans, foot-to-foot.
          Usually about ``cpw_width + 2 * cpw_gap`` of the CPW being crossed.
        * bridge_width: '7.5um' -- Width of the elevated bridge span.
        * pad_width: '11um' -- Width of each base landing pad (across the CPW).
        * pad_length: '11um' -- Length of each base landing pad (along the CPW).
        * bridge_layer: '30' -- Layer of the elevated bridge span.
        * pad_layer: '31' -- Layer of the two base landing pads.
    """

    default_options = Dict(
        crossover_length="22um",
        bridge_width="7.5um",
        pad_width="11um",
        pad_length="11um",
        bridge_layer="30",
        pad_layer="31",
    )
    """Default drawing options"""

    component_metadata = Dict(short_name="airbridge", _qgeometry_table_poly="True")
    """Component metadata"""

    TOOLTIP = """Ground-plane crossover (airbridge) that hops over a CPW."""

    def make(self):
        """Convert self.options into QGeometry."""
        p = self.parse_options()

        crossover_length = p.crossover_length
        bridge_width = p.bridge_width
        pad_width = p.pad_width
        pad_length = p.pad_length

        # Center-to-center distance between the two landing pads.
        pad_offset = crossover_length / 2.0 + pad_length / 2.0

        # Two base landing pads (feet), one on each side of the crossing.
        left_pad = draw.rectangle(pad_length, pad_width, -pad_offset, 0)
        right_pad = draw.rectangle(pad_length, pad_width, +pad_offset, 0)
        pads = draw.union(left_pad, right_pad)

        # Elevated span. Length reaches both pad centers so it overlaps the
        # feet and forms a single connected conductor once fabricated.
        span = draw.rectangle(crossover_length + pad_length, bridge_width, 0, 0)

        # Reposition the whole crossover.
        geom = [span, pads]
        geom = draw.rotate(geom, p.orientation, origin=(0, 0))
        geom = draw.translate(geom, p.pos_x, p.pos_y)
        span, pads = geom

        self.add_qgeometry(
            "poly", {"bridge": span}, layer=p.bridge_layer, subtract=False
        )
        self.add_qgeometry("poly", {"pads": pads}, layer=p.pad_layer, subtract=False)
