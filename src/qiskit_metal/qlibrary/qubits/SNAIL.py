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
    (Josephson energy ``alpha * E_J``) on the opposite arm. The asymmetry
    between the two arms gives the element a tunable third-order (three-wave
    mixing) nonlinearity that a symmetric two-junction SQUID does not have,
    which makes it the building block of SNAIL parametric amplifiers (SPAs)
    and Kerr-free three-wave mixers.

    Physics
    -------
    With ``phi`` the superconducting phase across the small junction and
    ``phi_ext = 2*pi*Phi_ext/Phi_0`` the reduced external flux, the SNAIL
    potential is (Frattini 2017)::

        U(phi)/E_J = - alpha*cos(phi) - n*cos((phi_ext - phi)/n)

    Taylor-expanding about its minimum ``phi_min`` gives
    ``U_eff/E_J = c2*p^2 + c3*p^3 + c4*p^4 + ...`` (``p = phi - phi_min``),
    where the coefficients ``c2, c3, c4`` are set purely by ``(n, alpha,
    Phi_ext)``. ``c2`` is the (flux-tunable) linear inductance, ``c3`` the
    three-wave-mixing strength and ``c4`` the Kerr. The useful operating
    point is the **Kerr-free** flux where ``c4 -> 0`` while ``c3`` stays
    large: pure three-wave mixing with no self-Kerr / Stark shift, which is
    what preserves gain and quantum efficiency at strong pump drive.

    ``n = 3`` is the smallest array that simultaneously (a) admits an
    ``alpha`` below the single-well bound while still giving useful inductive
    tunability, and (b) opens a region in ``(alpha, Phi_ext)`` where ``c4``
    crosses zero with ``c3`` still large. Limiting cases: ``n = 1`` is a SQUID
    (pure cosine, ``c3 = 0``, no three-wave mixing); ``n >> 1`` approaches the
    linear RF-SQUID / fluxonium regime.

    Single-well design constraint: keep ``alpha < 1/n`` (i.e. ``alpha < 1/3``
    for ``n = 3``). Above this the potential develops multiple inequivalent
    minima and becomes hysteretic (flux-qubit-like), which is unusable for
    clean three-wave mixing. The fabricated devices below sit just under the
    bound at ``alpha ~ 0.29``. (More precisely the non-hysteretic region is a
    2-D area in the ``(alpha, Phi_ext)`` plane; ``alpha < 1/n`` is the
    canonical rule of thumb, not an all-flux guarantee.)

    References
    ----------
    * Frattini et al., "3-wave mixing Josephson dipole element",
      Appl. Phys. Lett. 110, 222603 (2017), arXiv:1702.00869 -- introduces
      the SNAIL; source of ``n = 3``, ``alpha = 0.29``, ``Phi_ext = 0.41
      Phi_0``, ``I0 = 7.1 / 2.0 uA``.
    * Frattini et al., "Optimizing the Nonlinearity and Dissipation of a
      SNAIL Parametric Amplifier for Dynamic Range", Phys. Rev. Applied 10,
      054020 (2018), arXiv:1806.06093 -- arraying (``M = 1, 10, 20``) to
      raise saturation power; also uses ``alpha = 0.09``.
    * Sivak et al., "Kerr-free three-wave mixing in superconducting quantum
      circuits", Phys. Rev. Applied 11, 054060 (2019), arXiv:1902.10575 --
      Kerr-free operation, ``M = 20`` array, resonator tunable 6.2-7.2 GHz.
    * Miano et al., "Frequency-tunable Kerr-free three-wave mixing with a
      gradiometric SNAIL", Appl. Phys. Lett. 120, 184002 (2022),
      arXiv:2112.09785 -- restates the ``alpha < 1/3`` bound; two-loop
      gradiometric variant (not drawn here).
    * Josephson inductance relation: ``L_J = Phi_0/(2*pi*I0) = hbar/(2*e*I0)``
      (``Phi_0 = h/2e``); ``I0 = 1 uA -> L_J = 329 pH``.

    Typical device parameters (measured values are from Frattini 2017 and
    recur in Frattini 2018 / Sivak 2019; inductances are computed from the
    critical currents). Useful when choosing junction inductances for a
    renderer/analysis:

        * ``n = 3`` large junctions, each ``I0 ~ 7.1 uA``
          -> ``L_J ~ 46 pH`` (the ``Lj`` default).
        * one small junction, ``I0 ~ 2.0 uA`` -> ``L_J ~ 165 pH`` (the
          ``Lj_small`` default), i.e. ``L_J,small = L_J,large / alpha`` with
          ``alpha = I0_small / I0_large ~ 0.29``.
        * Kerr-free point near ``alpha ~ 0.29``, ``Phi_ext ~ 0.41 * Phi_0``;
          reported flux bias points cluster in ``Phi_ext/Phi_0 ~ 0.33-0.45``.
        * the three nominally-identical large junctions are made from two
          Dolan bridges (Al-on-Si); SNAILs are typically arrayed in series
          (``M = 10-20``) to raise saturation power -- this class draws one.
        * NOTE: the source papers specify the element *electrically*
          (critical currents, ``alpha``, flux) and do not tabulate on-chip
          junction overlap areas or loop dimensions, so the *layout*
          dimensions below are schematic (SQUID_LOOP-scale), not lifted from
          a published mask. Only the electrical parameters are grounded.

    Junction representation in Quantum Metal
    ----------------------------------------
    A Josephson junction has two distinct representations in this library,
    and this component deliberately uses only the first:

    1. **Schematic / analysis** -- a 2-point ``LineString`` in the
       ``junction`` qgeometry table with a ``width``. The Ansys/HFSS and
       pyEPR renderers turn each such row into a *lumped* Josephson
       inductance (``hfss_inductance``). This is what ``TransmonPocket`` does
       and what makes the element EM-/EPR-analyzable. It is a meshing
       placeholder, **not** the physical junction.
    2. **Physical / fabrication** -- the real sub-micron junction geometry
       (overlapping fingers/pads on a separate e-beam layer), drawn by the
       dedicated p-cells ``jj_dolan`` (Dolan, Appl. Phys. Lett. 31, 337,
       1977) and ``jj_manhattan`` (Pop et al., Nature 508, 369, 2014). Those
       carry the real ``um``-scale dimensions for the GDS mask and, per their
       own docstrings, **must not be rendered for EM simulation**.

    ``SNAIL`` emits the four junctions as the schematic LineStrings (three
    large sharing ``Lj``, one small with ``Lj_small``) -- the analysis path.
    For a fabrication-faithful mask, overlay a ``jj_dolan`` / ``jj_manhattan``
    p-cell at each junction location on the e-beam layer and exclude the
    schematic junctions from the GDS export. Keeping the two representations
    in separate components is intentional: the physical junction has features
    that break EM meshing, while the lumped line is exactly what the
    simulator wants. ``alpha`` is ultimately set by the *physical* junction
    overlap areas / critical currents at fabrication; here the asymmetry is
    expressed for analysis through ``Lj`` vs ``Lj_small`` and marked
    geometrically by the narrower default ``segment_lower_width`` on the
    small-junction (lower) arm.

    Geometry
    --------
    Follows the same rectangular-loop convention as ``SQUID_LOOP``, built
    from rectangles: a left plate (``plate1``), the upper arm (``seg a`` /
    ``seg ab`` / ``seg b`` separated by three ``JJ_gap`` breaks where the
    three large junctions sit), the lower arm (``seg a lower`` / ``seg b
    lower`` separated by a single ``JJ_gap_small`` break where the small
    junction sits), a vertical connector (``seg c``), a horizontal lead
    (``seg d``) and a right plate (``plate2``). The lower arm is
    automatically padded so that both arms close onto the same vertical
    connector, keeping the loop rectangular for any junction spacing.

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
        * Lj: '0.046nH' -- Josephson inductance of each large junction
          (~46 pH, from I0 ~ 7.1 uA in Frattini et al. 2017); written to the
          ``junction`` qgeometry table for HFSS/pyEPR
        * Lj_small: '0.165nH' -- Josephson inductance of the small junction
          (~165 pH, from I0 ~ 2.0 uA; equals Lj / alpha with alpha ~ 0.29)
        * inductor_width: '1um' -- width of the rendered junction strips
          (for HFSS/other EM software meshing; not the physical junction size)
        * pin_width: '5um' -- width of the connection pins on plate1/plate2

    Pins: ``a`` (left, on plate1) and ``b`` (right, on plate2) so the SNAIL
    can be wired into a larger design with a route. The four junctions are
    emitted to the ``junction`` qgeometry table (three large with ``Lj``,
    one small with ``Lj_small``) so the element is HFSS-eigenmode / pyEPR
    analyzable; keep ``Cj = Rj = 0`` (the renderer default) for pyEPR.
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
        Lj="0.046nH",
        Lj_small="0.165nH",
        inductor_width="1um",
        pin_width="5um",
    )
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(
        short_name="component",
        _qgeometry_table_poly="True",
        _qgeometry_table_junction="True",
    )
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
        # The lower arm spans the same horizontal distance as the (longer)
        # upper arm so both arms close onto the shared vertical connector.
        # The single small junction is centred on the arm: this keeps both
        # lower segments at equal, positive length for any ``JJ_gap_small``
        # up to the full arm span, avoiding the silent negative-width
        # rectangle (and broken loop) that an "extend seg b to fill"
        # scheme produces when the small-junction gap is large.
        lower_y = -0.5 * (p.squid_gap + p.segment_lower_width)
        lower_seg_length = max(0.0, 0.5 * (upper_arm_length - p.JJ_gap_small))

        segment_a_lower = draw.rectangle(
            lower_seg_length,
            p.segment_lower_width,
            half_p1 + 0.5 * lower_seg_length,
            lower_y,
        )

        segment_b_lower = draw.rectangle(
            lower_seg_length,
            p.segment_lower_width,
            half_p1 + upper_arm_length - 0.5 * lower_seg_length,
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

        # ----- Josephson junctions as 2-point lines (junction table) -----
        # Each junction is a LineString spanning its gap, rendered by HFSS /
        # pyEPR as a *lumped* Josephson inductance (the schematic / analysis
        # representation, as in TransmonPocket). This is not the physical
        # junction: for a fabrication mask, overlay a jj_dolan / jj_manhattan
        # p-cell at each location on the e-beam layer. See the class docstring
        # ("Junction representation in Quantum Metal").
        # Three large junctions on the upper arm, one small on the lower arm.
        jj_large_1 = draw.LineString(
            [(half_p1 + p.segment_a_length, upper_y), (ab1_start, upper_y)]
        )
        jj_large_2 = draw.LineString(
            [(ab1_start + p.segment_ab_length, upper_y), (ab2_start, upper_y)]
        )
        jj_large_3 = draw.LineString(
            [(ab2_start + p.segment_ab_length, upper_y), (b_start, upper_y)]
        )
        jj_small = draw.LineString(
            [
                (half_p1 + lower_seg_length, lower_y),
                (half_p1 + upper_arm_length - lower_seg_length, lower_y),
            ]
        )

        # ----- Connection pins on the outer edges of the two plates -----
        # Point-order sets the outward normal: pin ``a`` points -x off
        # plate1, pin ``b`` points +x off plate2.
        x_left = p.plate1_pos_x - half_p1
        x_right = (
            half_p1
            + upper_arm_length
            + p.segment_c_width
            + p.segment_d_length
            + p.plate2_width
        )
        pin_a_line = draw.LineString(
            [
                (x_left, p.plate1_pos_y - 0.5 * p.pin_width),
                (x_left, p.plate1_pos_y + 0.5 * p.pin_width),
            ]
        )
        pin_b_line = draw.LineString(
            [
                (x_right, p.plate1_pos_y + 0.5 * p.pin_width),
                (x_right, p.plate1_pos_y - 0.5 * p.pin_width),
            ]
        )

        # rotate and translate every object together so they stay aligned
        objects = [
            design1,
            jj_large_1,
            jj_large_2,
            jj_large_3,
            jj_small,
            pin_a_line,
            pin_b_line,
        ]
        objects = draw.rotate(objects, p.orientation, origin=(0, 0))
        objects = draw.translate(objects, p.pos_x, p.pos_y)
        (
            design1,
            jj_large_1,
            jj_large_2,
            jj_large_3,
            jj_small,
            pin_a_line,
            pin_b_line,
        ) = objects

        self.add_qgeometry("poly", {"design": design1}, layer=p.layer, subtract=False)

        # three large junctions share Lj; the small junction uses Lj_small.
        # ``hfss_inductance`` is the column the Ansys renderer reads per row.
        self.add_qgeometry(
            "junction",
            dict(
                jj_large_1=jj_large_1,
                jj_large_2=jj_large_2,
                jj_large_3=jj_large_3,
            ),
            width=p.inductor_width,
            hfss_inductance=p.Lj,
            layer=p.layer,
        )
        self.add_qgeometry(
            "junction",
            dict(jj_small=jj_small),
            width=p.inductor_width,
            hfss_inductance=p.Lj_small,
            layer=p.layer,
        )

        self.add_pin("a", list(pin_a_line.coords), width=p.pin_width)
        self.add_pin("b", list(pin_b_line.coords), width=p.pin_width)
