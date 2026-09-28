# This code is part of Quantum Metal.
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
"""A single-finger gap capacitor: a frame electrode wrapped around a finger."""

from qiskit_metal import Dict, draw
from qiskit_metal.qlibrary.core import QComponent


class CapFingerInFrame(QComponent):
    """Two-pin gap capacitor with one electrode framing the other.

    Inherits `QComponent` class.

    .. image::
        CapFingerInFrame.png

    The ``frame`` electrode is a rectangular ring with a slot in one long
    side. The ``finger`` electrode is a bar inside the ring, reached by a
    short stub that passes through the slot. The two electrodes couple across
    a uniform ``cap_gap`` on every side of the bar, so the capacitance is set
    mainly by ``frame_length`` at a fixed cross-section -- one cell design can
    be tuned per instance by length alone.

    This is the cell used on the ETH Zurich 17-qubit surface-code device
    (Krinner et al., Nature 605, 669 (2022)) both as the series input
    capacitor of each readout feedline and as the coupler between each
    Purcell filter and its feedline, where the length varies per qubit.

    ::

                      y
                      ^
          +-----------|-----------+
          |  +-----------------+  |
          |  |  +-----------+  |  |
        --+  |  |  finger   |===+====   <- finger pin (+x)
     frame|  |  +-----------+  |  |          stub through the slot
      pin |  +-----------------+  |
          +-----------------------+        -> x
            frame (ring, slot on +x)

    ``(0, 0)`` is the center of the frame. At orientation 0 the frame pin
    faces -x and the finger pin +x; both sit on the frame's outer metal edge.
    The finger's length and width are derived -- the opening inside the frame
    less ``cap_gap`` on every side -- so the geometry cannot be made
    inconsistent.

    The defaults are the input-capacitor cell of the device above, measured
    from its micrograph; the gap widths there are unresolved, and ``cap_gap``
    and ``ground_gap`` of 10 um fit every measured centerline spacing.

    Default Options:
        * frame_length: '245um' -- Outer metal length of the frame, along y
        * frame_width: '72um' -- Outer metal width of the frame, along x
        * frame_trace: '16um' -- Width of the frame conductor
        * cap_gap: '10um' -- Gap between finger and frame, all round, and
          either side of the finger stub in the slot
        * ground_gap: '10um' -- Gap between the frame and the ground plane
        * frame_cpw_width: 'cpw_width' -- Trace width of the line on the frame pin
        * finger_cpw_width: 'cpw_width' -- Trace width of the finger stub and
          of the line on the finger pin
    """

    default_options = Dict(
        frame_length="245um",
        frame_width="72um",
        frame_trace="16um",
        cap_gap="10um",
        ground_gap="10um",
        frame_cpw_width="cpw_width",
        finger_cpw_width="cpw_width",
    )
    """Default options"""

    component_metadata = Dict(short_name="cap", _qgeometry_table_poly="True")
    """Component metadata"""

    TOOLTIP = """Single-finger gap capacitor: frame electrode around a finger."""

    def make(self):
        """Build the component."""
        p = self.p
        L, W, t, g = p.frame_length, p.frame_width, p.frame_trace, p.cap_gap
        sw = p.finger_cpw_width

        finger_w = W - 2 * t - 2 * g
        finger_l = L - 2 * t - 2 * g
        if finger_w <= 0 or finger_l <= 0:
            raise ValueError(
                f"{self.name}: no room for the finger -- frame_width/frame_length "
                f"must exceed 2*(frame_trace + cap_gap); got finger "
                f"{finger_w:.4g} x {finger_l:.4g}"
            )
        if sw + 2 * g >= L - 2 * t:
            raise ValueError(
                f"{self.name}: the finger stub's slot (finger_cpw_width + "
                "2*cap_gap) does not fit inside the frame"
            )

        ring = draw.subtract(draw.rectangle(W, L), draw.rectangle(W - 2 * t, L - 2 * t))
        slot = draw.rectangle(t, sw + 2 * g, W / 2 - t / 2, 0)
        frame = draw.subtract(ring, slot)

        finger = draw.rectangle(finger_w, finger_l)
        stub_x0 = finger_w / 2
        stub = draw.rectangle(W / 2 - stub_x0, sw, (stub_x0 + W / 2) / 2, 0)
        finger = draw.union(finger, stub)

        etch = draw.rectangle(W + 2 * p.ground_gap, L + 2 * p.ground_gap)

        # Pins: each given as a line ALONG the connection, inner point first,
        # so the outward normal runs from inside the cell to the pin.
        frame_pin = draw.LineString([(-W / 2 + t / 2, 0), (-W / 2, 0)])
        finger_pin = draw.LineString([(W / 2 - t / 2, 0), (W / 2, 0)])

        items = [frame, finger, etch, frame_pin, finger_pin]
        items = draw.rotate(items, p.orientation, origin=(0, 0))
        items = draw.translate(items, p.pos_x, p.pos_y)
        frame, finger, etch, frame_pin, finger_pin = items

        self.add_qgeometry(
            "poly", {"frame": frame, "finger": finger}, layer=p.layer, chip=p.chip
        )
        self.add_qgeometry(
            "poly", {"etch": etch}, subtract=True, layer=p.layer, chip=p.chip
        )
        self.add_pin(
            "frame", frame_pin.coords, width=p.frame_cpw_width, input_as_norm=True
        )
        self.add_pin(
            "finger", finger_pin.coords, width=p.finger_cpw_width, input_as_norm=True
        )
