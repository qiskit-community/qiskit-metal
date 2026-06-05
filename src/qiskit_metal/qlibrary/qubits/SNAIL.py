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
"""SNAIL (Superconducting Nonlinear Asymmetric Inductive eLement).

.. code-block:
:
    |                                                              |
    |                                                              |
    |--seg a--|JJ|--seg ab--|JJ|--seg ab--|JJ|--seg b--|           |
    |          (three large junctions, upper arm)       |          |
  plate1                                              seg c--seg d--plate2
    |                                                   |          |
    |--------seg a lower--------|jj|----seg b lower-----|          |
    |              (single small junction, lower arm)              |
    |                                                              |
"""

from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core.base import QComponent


class SNAIL(QComponent):
    """A SNAIL (Superconducting Nonlinear Asymmetric Inductive eLement).

    Inherits the "QComponent" class.

    A SNAIL is a superconducting loop interrupted by ``n`` large Josephson
    junctions on one arm (here ``n = 3``) and a single smaller junction
    (tunnelling energy ``alpha * E_J``) on the opposite arm. The asymmetry
    between the two arms gives the element a tunable third-order (three-wave
    mixing) nonlinearity that a symmetric two-junction SQUID does not have,
    which makes it the building block of SNAIL parametric amplifiers (SPAs)
    and Kerr-free three-wave mixers.

    See Frattini et al., "3-wave mixing Josephson dipole element",
    Appl. Phys. Lett. 110, 222603 (2017) and Frattini et al., "Optimizing
    the Nonlinearity and Dissipation of a SNAIL Parametric Amplifier for
    Dynamic Range", Phys. Rev. Applied 10, 054020 (2018).

    The geometry follows the same rectangular-loop convention as
    ``SQUID_LOOP``. It is built from a set of rectangles: a left plate
    (``plate1``), the upper arm (``seg a`` / ``seg ab`` / ``seg b``
    separated by three ``JJ_gap`` breaks where the three large junctions
    sit), the lower arm (``seg a lower`` / ``seg b lower`` separated by a
    single ``JJ_gap_small`` break where the small junction sits), a vertical
    connector (``seg c``), a horizontal lead (``seg d``) and a right plate
    (``plate2``). The lower arm is automatically padded so that both arms
    close onto the same vertical connector, keeping the loop rectangular for
    any choice of junction count spacing.

    .. image::
        SNAIL.png

    .. meta::
        :description: SNAIL (Superconducting Nonlinear Asymmetric Inductive eLement)

    Default Options:
        * plate1_width: '5.5um' -- width of plate1 (left)
        * plate1_height: '40um' -- height of plate1 (left)
        * plate1_pos_x: '0' -- origin of plate1 (left) in x
        * plate1_pos_y: '0' -- origin of plate1 (left) in y
        * squid_gap: '10um' -- vertical space between the upper and lower arms
        * segment_a_length: '10um' -- length of seg a (first upper-arm segment)
        * segment_a_width: '1um' -- width of the upper-arm segments
        * JJ_gap: '0.5um' -- break for each of the three large junctions (upper arm)
        * segment_ab_length: '5um' -- length of the islands between the large junctions
        * segment_b_length: '5um' -- length of seg b (last upper-arm segment)
        * segment_b_width: '1um' -- width of seg b
        * JJ_gap_small: '0.3um' -- break for the single small junction (lower arm)
        * segment_lower_width: '0.6um' -- width of the lower (small-junction) arm
        * segment_c_width: '1um' -- width of the vertical connector seg c
        * segment_d_length: '10um' -- length of seg d
        * segment_d_width: '2um' -- width of seg d
        * plate2_width: '6um' -- width of plate 2 (right)
        * plate2_height: '30um' -- height of plate 2 (right)
    """

    # Default drawing options
    default_options = Dict(
        plate1_width="5.5um",
        plate1_height="40um",
        plate1_pos_x="0",
        plate1_pos_y="0",
        squid_gap="10um",
        segment_a_length="10um",
        segment_a_width="1um",
        JJ_gap="0.5um",
        segment_ab_length="5um",
        segment_b_length="5um",
        segment_b_width="1um",
        JJ_gap_small="0.3um",
        segment_lower_width="0.6um",
        segment_c_width="1um",
        segment_d_length="10um",
        segment_d_width="2um",
        plate2_width="6um",
        plate2_height="30um",
    )
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name="component")
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        half_p1 = 0.5 * p.plate1_width

        # Total horizontal span of the upper arm: three large junctions
        # (``JJ_gap`` each) separating four conducting segments
        # (seg a, two intermediate islands, seg b).
        upper_arm_length = (
            p.segment_a_length
            + 2.0 * p.segment_ab_length
            + p.segment_b_length
            + 3.0 * p.JJ_gap
        )

        # draw the left plate as a rectangle
        plate1 = draw.rectangle(
            p.plate1_width, p.plate1_height, p.plate1_pos_x, p.plate1_pos_y
        )

        # ----- Upper arm: three large junctions in series -----
        # y-centre of the upper arm
        upper_y = 0.5 * (p.squid_gap + p.segment_a_width)

        segment_a = draw.rectangle(
            p.segment_a_length,
            p.segment_a_width,
            half_p1 + 0.5 * p.segment_a_length,
            upper_y,
        )

        # first intermediate island, after seg a + first large junction
        ab1_start = half_p1 + p.segment_a_length + p.JJ_gap
        segment_ab1 = draw.rectangle(
            p.segment_ab_length,
            p.segment_a_width,
            ab1_start + 0.5 * p.segment_ab_length,
            upper_y,
        )

        # second intermediate island, after the second large junction
        ab2_start = ab1_start + p.segment_ab_length + p.JJ_gap
        segment_ab2 = draw.rectangle(
            p.segment_ab_length,
            p.segment_a_width,
            ab2_start + 0.5 * p.segment_ab_length,
            upper_y,
        )

        # seg b, after the third large junction
        b_start = ab2_start + p.segment_ab_length + p.JJ_gap
        segment_b = draw.rectangle(
            p.segment_b_length,
            p.segment_b_width,
            b_start + 0.5 * p.segment_b_length,
            0.5 * (p.squid_gap + p.segment_b_width),
        )

        # ----- Lower arm: single small junction -----
        # y-centre of the lower arm
        lower_y = -0.5 * (p.squid_gap + p.segment_lower_width)

        segment_a_lower = draw.rectangle(
            p.segment_a_length,
            p.segment_lower_width,
            half_p1 + 0.5 * p.segment_a_length,
            lower_y,
        )

        # seg b lower is padded so the lower arm closes onto the same
        # vertical connector as the (longer) upper arm.
        segment_b_lower_length = upper_arm_length - p.segment_a_length - p.JJ_gap_small
        b_lower_start = half_p1 + p.segment_a_length + p.JJ_gap_small
        segment_b_lower = draw.rectangle(
            segment_b_lower_length,
            p.segment_lower_width,
            b_lower_start + 0.5 * segment_b_lower_length,
            lower_y,
        )

        # ----- Vertical connector, horizontal lead and right plate -----
        segment_c = draw.rectangle(
            p.segment_c_width,
            p.squid_gap + p.segment_a_width + p.segment_b_width,
            half_p1 + upper_arm_length + 0.5 * p.segment_c_width,
            p.plate1_pos_y,
        )

        segment_d = draw.rectangle(
            p.segment_d_length,
            p.segment_d_width,
            half_p1 + upper_arm_length + p.segment_c_width + 0.5 * p.segment_d_length,
            p.plate1_pos_y,
        )

        plate2 = draw.rectangle(
            p.plate2_width,
            p.plate2_height,
            half_p1
            + upper_arm_length
            + p.segment_c_width
            + p.segment_d_length
            + 0.5 * p.plate2_width,
            p.plate1_pos_y,
        )

        design1 = draw.union(
            plate1,
            segment_a,
            segment_ab1,
            segment_ab2,
            segment_b,
            segment_a_lower,
            segment_b_lower,
            segment_c,
            segment_d,
            plate2,
        )

        # now translate and rotate the final structure
        design1 = draw.rotate(design1, p.orientation, origin=(0, 0))
        design1 = draw.translate(design1, p.pos_x, p.pos_y)

        geom = {"design": design1}
        self.add_qgeometry("poly", geom, layer=p.layer, subtract=False)
