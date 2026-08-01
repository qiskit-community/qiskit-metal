# /// script
# requires-python = ">=3.10"
# ///
"""Generate the hero animated GIF for the README.

Builds a 4-qubit ring chip progressively (canvas → qubits → CPW routes →
airbridges → readout stubs → launchpads → final view) and stitches each
stage into a looping GIF, closing with the same chip's Gmsh FEM mesh
(2-D surface, pseudo-3-D) and a couple of real 3-D airbridge
renders borrowed from tutorial 2.15. Showcases the design-as-code
workflow and the open-source meshing path in a glance.

The design frames use the same ``qm.view(design)`` API end users would run,
so the GIF stays honest — what viewers see is exactly what they'd get
by pasting the equivalent ~25 lines into a notebook.

Output: docs/_static/hero.gif (~350KB at 640×640)

Run from the repo root:
    uv run --with pillow scripts/make_hero_gif.py

The mesh frames require the optional ``gmsh`` dependency ([mesh] extra).
Without it, the GIF is generated the same way minus those two frames:
    uv run --extra mesh --with pillow scripts/make_hero_gif.py
"""

import math
import os
import sys
import tempfile
from pathlib import Path

# Silence the import-path rename warning chatter (doesn't affect rendering)
os.environ.setdefault("QISKIT_METAL_SUPPRESS_RENAME_WARNING", "1")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from PIL import Image

import qiskit_metal as qm
from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.couplers.coupled_line_tee import CoupledLineTee
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.tlines.airbridge import (
    apply_airbridge_layer_stack,
    route_airbridges,
)
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
from qiskit_metal.validation import (
    ChipBoundsRule,
    CPWGapRule,
    MetalOverlapRule,
    MetalSpacingRule,
    QubitClearanceRule,
    Severity,
    ShortSegmentRule,
    validate,
)


# --- Configuration ---
OUT_PATH = Path("docs/_static/hero.gif")
# Square figure — the chip is square (axes ratio 1:1), so a square frame
# avoids the wide white bars on the sides that 16:9 / 4:3 figures leave.
FIGSIZE_INCH = (6.4, 6.4)
DPI = 100  # → 640×640 PNG frames
LOOP = 0  # 0 = infinite loop
# Padding factor applied to the final-design bbox to compute axis limits.
# Set once, used for every frame, so the chip never jumps or autoscales
# asymmetrically between frames (the "do it at the end" pattern).
AXIS_PADDING_FRAC = 0.06  # tighter — was 0.10 — zooms in for readability


def compute_centered_square_limits(design, pad_frac=AXIS_PADDING_FRAC):
    """Compute symmetric, square axis limits centered on the FINAL design bbox.

    Called once after the design is fully built, then reused for every frame
    so the chip stays geometrically centered (no autoscale drift, no per-frame
    margin shifts). This is the "do it at the very end" pattern.
    """
    xs, ys = [], []
    for name, comp in design.components.items():
        try:
            b = comp.qgeometry_bounds()  # [minx, miny, maxx, maxy]
            xs += [b[0], b[2]]
            ys += [b[1], b[3]]
        except Exception:
            continue
    if not xs:
        # Empty design — fall back to a sensible default
        return (-3.5, 3.5), (-3.5, 3.5)
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    # Square extent: take the larger dimension so the chip fits with equal
    # padding on all four sides (true geometric centering).
    half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
    half *= 1.0 + pad_frac
    return (cx - half, cx + half), (cy - half, cy + half)


def render_frame(design, title, xlim, ylim):
    """Render the current design state to a fixed-layout figure.

    xlim/ylim are passed in (computed from the FINAL design once) so the chip
    is in the same screen position in every frame.
    """
    fig = qm.view(design)
    ax = fig.gca()
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    # Title CENTERED (loc='center' is the default — not 'left' which makes the
    # whole frame look asymmetric).
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    fig.set_size_inches(*FIGSIZE_INCH)
    # Explicit subplots_adjust — DON'T use tight_layout/bbox_inches=tight here;
    # both produce varying per-frame padding which makes the GIF "jump."
    fig.subplots_adjust(left=0.10, right=0.97, top=0.92, bottom=0.10)
    return fig


def save_frame(fig, path):
    # Fixed pad_inches (no bbox_inches='tight') so every frame has identical
    # pixel dimensions — required for clean GIF stitching.
    fig.savefig(path, dpi=DPI, pad_inches=0.15, facecolor=fig.get_facecolor())
    plt.close(fig)


def _make_design():
    """Build the design from scratch — no rendering. Returns the empty design."""
    design = designs.DesignPlanar()
    design.variables["cpw_width"] = "10 um"
    design.variables["cpw_gap"] = "6 um"
    design._chips["main"]["size"]["size_x"] = "8 mm"
    design._chips["main"]["size"]["size_y"] = "8 mm"
    return design


# --- Qubit definitions ---
# 4 TransmonPockets on the ring (uniform type so the CPW pin geometry stays
# consistent — TransmonPocket has corner pins, TransmonCross has cardinal
# pins, and mixing them broke the routing). The qubit-type VARIETY comes
# instead from a single TransmonCross placed at the centre as a separate
# "qlibrary showcase" component, added in its own animation frame.

_POCKET_PADS = Dict(
    connection_pads=Dict(
        a=Dict(loc_W=+1, loc_H=+1, pad_width="120um", cpw_extend="80um"),  # NE corner
        b=Dict(loc_W=-1, loc_H=+1, pad_width="120um", cpw_extend="80um"),  # NW
        c=Dict(loc_W=-1, loc_H=-1, pad_width="120um", cpw_extend="80um"),  # SW
        d=Dict(loc_W=+1, loc_H=-1, pad_width="120um", cpw_extend="80um"),  # SE
    ),
)

# Q_SPEC: name → (pos_x, pos_y) — all pockets
Q_SPEC = {
    "Q1": ("+1.1mm", "+1.1mm"),
    "Q2": ("-1.1mm", "+1.1mm"),
    "Q3": ("-1.1mm", "-1.1mm"),
    "Q4": ("+1.1mm", "-1.1mm"),
}

# Ring routing: 4 CPW meanders connecting adjacent qubits.
RING_CPWS = [
    ("cpw_12", "Q1", "b", "Q2", "a"),  # top edge
    ("cpw_23", "Q2", "c", "Q3", "b"),  # left edge
    ("cpw_34", "Q3", "d", "Q4", "c"),  # bottom edge
    ("cpw_41", "Q4", "a", "Q1", "d"),  # right edge
]

# Readout architecture: each qubit's quarter-wave resonator taps a
# CoupledLineTee — capacitively coupled to a short local feedline stub with
# its own input/output ports, NOT wired directly to a port. This is the
# coupling building block that "Reference design 3 - Four-qubit multiplexed
# readout" (tutorials/Appendix A) chains multiple qubits onto for real
# frequency-multiplexed readout; kept as one tee per qubit here (rather
# than sharing one line across the ring) to avoid the routing/collision
# complexity of threading a single feedline past the existing ring CPWs
# and airbridges.
#
# Placement mirrors where the direct-wired launchpad used to sit (each
# qubit's outward diagonal chip corner). ``orient`` is the tee orientation
# that points its hang branch (``second_end``) back at the qubit — found
# empirically by sweeping CoupledLineTee's 8 cardinal/diagonal orientations
# and reading off each one's resulting ``second_end`` pin normal.
#
# ``mirror``: CoupledLineTee is chiral — its hang pin sits at the LOCAL +x
# end of the coupling section. For Q1/Q3's orientations that end faces the
# side the resonator approaches from, so the route flows out of the
# coupling U-bend naturally. For Q2/Q4's (mirror-image) orientations it
# faces the far side, forcing the resonator to double back underneath the
# coupling section — rendering as a cramped hook right at the tee.
# mirror=True flips the hang branch to the -x end, restoring the clean
# mirror-symmetric junction on those two corners.
# Tee distance from center. Two constraints, both enforced by the
# validators below: at ±2.0mm the resonators' outermost meander folds
# crossed the diagonal feedline outright; and the wider meander spacing
# needed for pocket clearance (see _add_readout_resonators) pushes the
# folds further out still. ±2.4mm satisfies both.
READOUT_TEES = {
    "Q1": dict(pin="a", pos=("+2.4mm", "+2.4mm"), orient="315", mirror=False),  # NE
    "Q2": dict(pin="b", pos=("-2.4mm", "+2.4mm"), orient="45", mirror=True),  # NW
    "Q3": dict(pin="c", pos=("-2.4mm", "-2.4mm"), orient="135", mirror=False),  # SW
    "Q4": dict(pin="d", pos=("+2.4mm", "-2.4mm"), orient="225", mirror=True),  # SE
}
READOUT_PORT_OFFSET_MM = 1.0  # tee's prime line -> each port, along the line

# Per-qubit readout frequency (GHz) — deliberately detuned like a real
# frequency-multiplexed readout scheme, not just cosmetic variety.
READOUT_TARGET_GHZ = {"Q1": 6.0, "Q2": 6.2, "Q3": 6.4, "Q4": 6.6}

# Effective permittivity for a Nb/Al CPW (10um trace / 6um gap) on a
# silicon substrate — the standard approximation used across the
# superconducting-qubit literature for this trace/gap/substrate combination.
CPW_EPS_EFF = 6.2


def _quarter_wave_length_mm(freq_ghz):
    """Physical length of a quarter-wave CPW resonator at ``freq_ghz``.

    lambda/4 = v_phase / (4*f), v_phase = c / sqrt(eps_eff). This is what
    makes a readout resonator resonant at its target frequency — sizing it
    arbitrarily (as the previous, now-removed, decorative stub did) isn't
    just an aesthetic shortcut, it makes the "resonator" a fiction with no
    relationship to the frequency a real device would show.
    """
    c_mm_per_s = 3e11  # speed of light, mm/s
    v_phase = c_mm_per_s / math.sqrt(CPW_EPS_EFF)
    freq_hz = freq_ghz * 1e9
    return v_phase / (4 * freq_hz)


def _qubit_factory(name):
    """Returns a function that adds a TransmonPocket `name` and rebuilds."""
    x, y = Q_SPEC[name]

    def add(design):
        TransmonPocket(design, name, options=Dict(pos_x=x, pos_y=y, **_POCKET_PADS))
        design.rebuild()

    return add


def _add_center_cross_showcase(design):
    """Add a single TransmonCross at the centre — unconnected. Used in a
    dedicated frame after the rest of the chip is built, to showcase a
    second qubit-type (rotated 45°, so it doesn't read as just a smaller
    copy of the ring's pockets) without disturbing the ring's pocket-based
    routing.
    """
    TransmonCross(
        design,
        "Qx",
        options=Dict(
            pos_x="0mm",
            pos_y="0mm",
            orientation="45",
            cross_length="180um",
            cross_gap="25um",
            cross_width="20um",
        ),
    )
    design.rebuild()


def _compute_robust_cpw_opts(design, qa, pa, qb, pb):
    """Compute CPW meander options sized to the ACTUAL pin-to-pin distance.

    Why this is dynamic, not hardcoded: ``RouteMeander`` picks
    ``meander_number = np.floor(length_direct / spacing)`` wiggles, each
    with a perpendicular excursion of ``length_excess / (meander_number*2)``.
    If ``meander_number`` packs more wiggles than the excess length can
    support, the per-wiggle excursion can end up smaller than the fillet
    radius, rendering as sharp "kinks" / castellations instead of a smooth
    wave (see #1086 — fixed in ``meandered.py`` by capping ``meander_number``
    so the excursion always clears the fillet, but that self-correction
    doesn't control exactly how many wiggles you get, only that each one is
    geometrically clean).

    This function keeps a stronger, purely aesthetic guarantee for the hero
    GIF specifically: pick ``spacing`` LARGER than the actual pin-to-pin
    distance, so ``floor()`` is guaranteed to land on 1. One big symmetric
    hump every time, regardless of route orientation or chip size. We read
    the distance from the live design's pin positions instead of hardcoding
    a value, so this keeps working if Q_SPEC changes (different qubit
    spacing, or someone forks the script for a new layout).
    """
    p1 = np.asarray(design.components[qa].pins[pa]["middle"], dtype=float)
    p2 = np.asarray(design.components[qb].pins[pb]["middle"], dtype=float)
    distance_mm = float(np.linalg.norm(p2 - p1))  # design units are mm

    spacing_mm = distance_mm * 1.10  # > distance → floor()=1
    total_length_mm = distance_mm * 1.55  # excess for one visible hump
    # Fillet must fit inside the wiggle envelope — cap at spacing/4 for safety,
    # floor at 40um so very short routes still get a visible curve.
    fillet_um = min(120, max(40, int(spacing_mm * 1000 / 4)))

    return Dict(
        lead=Dict(start_straight="180um", end_straight="180um"),
        fillet=f"{fillet_um} um",
        total_length=f"{total_length_mm:.3f}mm",
        trace_width="10 um",
        trace_gap="6 um",
        meander=Dict(spacing=f"{spacing_mm:.3f}mm", asymmetry="0um"),
        snap="false",
    )


def _cpw_factory(cpw_spec):
    """Returns a function that adds one CPW meander and rebuilds.

    CPW geometry params are computed from the LIVE design's pin positions
    inside the closure (not hardcoded), so the meander workaround is
    correct for any qubit-spacing or chip-size choice — not tied to the
    current ±1.1mm hero-GIF layout.
    """
    name, qa, pa, qb, pb = cpw_spec

    def add(design):
        RouteMeander(
            design,
            name,
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component=qa, pin=pa),
                    end_pin=Dict(component=qb, pin=pb),
                ),
                **_compute_robust_cpw_opts(design, qa, pa, qb, pb),
            ),
        )
        design.rebuild()

    return add


def _add_readout_resonators(design):
    """Each qubit's quarter-wave readout resonator, coupled to its own
    feedline stub via a CoupledLineTee (see READOUT_TEES).

    Order matters and must stay build-order-correct at each step: the tee
    needs to exist (with real pin geometry) before the resonator can target
    its ``second_end`` pin, and the tee's prime-line pins need to exist
    before the ports can be placed from their actual position/normal.
    """
    for qubit_name, spec in READOUT_TEES.items():
        tee_name = f"clt_{qubit_name}"
        x, y = spec["pos"]
        CoupledLineTee(
            design,
            tee_name,
            options=Dict(
                pos_x=x,
                pos_y=y,
                orientation=spec["orient"],
                mirror=spec["mirror"],
                coupling_length="250um",
                down_length="150um",
                fillet="70um",
                open_termination=True,
            ),
        )
        design.rebuild()

        length_mm = _quarter_wave_length_mm(READOUT_TARGET_GHZ[qubit_name])
        RouteMeander(
            design,
            f"ro_{qubit_name}",
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component=qubit_name, pin=spec["pin"]),
                    end_pin=Dict(component=tee_name, pin="second_end"),
                ),
                # Lead length must clear the fillet radius by a healthy
                # margin (see #1086) — lead==fillet still isn't enough for
                # the Gmsh path-offset renderer ("Could not create line").
                lead=Dict(start_straight="150um", end_straight="150um"),
                fillet="60 um",
                total_length=f"{length_mm:.3f}mm",
                trace_width="10 um",
                trace_gap="6 um",
                # The meander's perpendicular excursion tracks
                # meander.spacing, and the first rung folds back over the
                # qubit -- at 150um it ran 9um from the pocket edge (0.4x a
                # full CPW width). 250um clears it; see
                # _validate_min_clearance_to_pockets.
                meander=Dict(spacing="250um", asymmetry="0um"),
            ),
        )
        design.rebuild()

        # Ports placed from the tee's ACTUAL prime-line pin geometry
        # (middle + normal), not a hand-picked angle — same reasoning as
        # the removed decorative stub's placement: TransmonPocket/
        # CoupledLineTee pin directions aren't worth hand-deriving twice.
        port_names = {}
        for prime_pin in ("prime_start", "prime_end"):
            pin = design.components[tee_name].pins[prime_pin]
            middle = np.asarray(pin["middle"], dtype=float)
            normal = np.asarray(pin["normal"], dtype=float)
            port_pos = middle + normal * READOUT_PORT_OFFSET_MM
            port_orient = np.degrees(np.arctan2(normal[1], normal[0])) + 180
            port_name = f"P_{qubit_name}_{prime_pin}"
            LaunchpadWirebond(
                design,
                port_name,
                options=Dict(
                    pos_x=f"{port_pos[0]}mm",
                    pos_y=f"{port_pos[1]}mm",
                    orientation=f"{port_orient}",
                    pad_width="120um",
                    pad_height="120um",
                    pad_gap="80um",
                    lead_length="20um",
                ),
            )
            port_names[prime_pin] = port_name
        design.rebuild()

        # RouteStraight, not a Manhattan router (RoutePathfinder): each port
        # sits exactly on the tee's prime-line axis facing back at it, so
        # the feed is a single dead-straight (diagonal) segment. A Manhattan
        # router would insert axis-aligned jogs (diagonal lead → vertical →
        # horizontal → diagonal lead) between the same two pins.
        feed_opts = Dict(trace_width="10um", trace_gap="6um")
        RouteStraight(
            design,
            f"feed_{qubit_name}_in",
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component=port_names["prime_start"], pin="tie"),
                    end_pin=Dict(component=tee_name, pin="prime_start"),
                ),
                **feed_opts,
            ),
        )
        RouteStraight(
            design,
            f"feed_{qubit_name}_out",
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component=tee_name, pin="prime_end"),
                    end_pin=Dict(component=port_names["prime_end"], pin="tie"),
                ),
                **feed_opts,
            ),
        )
    design.rebuild()


# The top/bottom ring edges (cpw_12, cpw_34) are the longest uninterrupted
# CPW spans on the chip — long enough to need airbridges over the ground
# gap in a real device, so they're the natural place to show the feature.
AIRBRIDGE_CPWS = ["cpw_12", "cpw_34"]


def _add_airbridges(design):
    """Auto-place real Airbridge components along the two longest ring CPWs."""
    for cpw_name in AIRBRIDGE_CPWS:
        route_airbridges(
            design, design.components[cpw_name], pitch="350um", bridge_at_corners=True
        )
    design.rebuild()


# The hero chip is gated on qiskit_metal.validation -- the same design-rule
# module a user gets -- rather than checks written here. Four separate
# geometry defects shipped into this GIF before it existed: resonators
# crossing their feedline, resonators hugging a qubit pocket, launchpads
# off the chip edge, and route segments too short for their fillet.
#
# QubitClearanceRule is a WARNING by default because a deliberately-coupled
# structure trips it; on this layout nothing is meant to run near a pocket,
# so it is escalated to ERROR and the whole set becomes a hard gate.
HERO_DESIGN_RULES = (
    MetalOverlapRule(),
    MetalSpacingRule(),
    CPWGapRule(),
    ChipBoundsRule(),
    ShortSegmentRule(),
    QubitClearanceRule(severity=Severity.ERROR),
)


def _populate_full_design(design):
    """Apply every stage so the FINAL design exists. Used for centering compute."""
    for name in Q_SPEC:
        _qubit_factory(name)(design)
    for spec in RING_CPWS:
        _cpw_factory(spec)(design)
    _add_airbridges(design)
    _add_readout_resonators(design)
    _add_center_cross_showcase(design)
    validate(design, rules=HERO_DESIGN_RULES, strict=True)


# Close-up view for the opening frame: centered on Q1's pocket with enough
# margin to show the whole qubit + its connection stubs. (cx, cy, half) in mm.
_Q1_CLOSEUP_VIEW = (1.1, 1.1, 0.9)


def build_storyboard():
    """Returns the ordered list of
    (stage_fn, filename, title, duration_ms, view) — ``view`` is None for
    the standard full-chip limits, or an (cx, cy, half) tuple for a custom
    zoom (used by the opening close-up frames).
    """
    stages = []
    # Open ZOOMED IN on a single transmon — never an empty canvas, so even a
    # stalled first frame shows a real device, and viewers meet the star of
    # the show up close before the camera pulls back.
    stages.append(
        (
            _qubit_factory("Q1"),
            "00_transmon_closeup.png",
            "Step 1 — A transmon qubit, up close",
            1100,
            _Q1_CLOSEUP_VIEW,
        )
    )
    stages.append(
        (
            None,
            "01_zoom_out.png",
            "...zoom out — room for a full chip",
            700,
            None,
        )
    )
    # Remaining qubits appear one by one — snappy
    qubit_titles = {
        "Q2": "Step 2 — Add qubit Q2",
        "Q3": "Step 2 — Add qubit Q3",
        "Q4": "Step 2 — All 4 transmons placed",
    }
    for i, name in enumerate(qubit_titles):
        dur = 500 if name == "Q4" else 320  # slight hold on the last
        stages.append(
            (
                _qubit_factory(name),
                f"0{i + 2}_{name}.png",
                qubit_titles[name],
                dur,
                None,
            )
        )
    # Then CPWs one by one
    cpw_titles = [
        "Step 3 — Route Q1↔Q2 (CPW meander)",
        "Step 3 — Route Q2↔Q3",
        "Step 3 — Route Q3↔Q4",
        "Step 3 — Ring complete (4 resonators)",
    ]
    for i, spec in enumerate(RING_CPWS):
        dur = 550 if i == len(RING_CPWS) - 1 else 320
        stages.append(
            (_cpw_factory(spec), f"0{i + 5}_{spec[0]}.png", cpw_titles[i], dur, None)
        )
    # Airbridges over the two longest CPW spans — real QComponents, auto-placed
    # along the route's filleted centerline (see route_airbridges).
    stages.append(
        (
            _add_airbridges,
            "09_airbridges.png",
            "Step 4 — Airbridges over the long spans",
            600,
            None,
        )
    )
    # Quarter-wave readout resonators, each coupled through a tee to its
    # own feedline stub (6.0-6.6 GHz, per-qubit — READOUT_TARGET_GHZ).
    stages.append(
        (
            _add_readout_resonators,
            "10_readout.png",
            "Step 5 — Readout resonators, coupled to feedline ports",
            600,
            None,
        )
    )
    # Showcase a second qubit type (TransmonCross) appearing at the centre —
    # demonstrates the qlibrary has more than one transmon kind.
    stages.append(
        (
            _add_center_cross_showcase,
            "11_cross.png",
            "Or pick from 13+ qubit types  (TransmonCross shown)",
            800,
            None,
        )
    )
    # Final long hold so viewers register the result
    stages.append(
        (
            None,
            "12_final.png",
            "qm.view(design)   →   chip ready for fab/sim",
            1600,
            None,
        )
    )
    return stages


def build_4qubit_chip_progressively(frame_dir):
    """Yield frame_path as the design grows. Saves PNGs to frame_dir.

    Centering pattern (per the "do it at the very end" rule):
      1. Build the FINAL design first (no rendering) → compute centered limits.
      2. Replay the build step-by-step, capturing each stage with THOSE
         fixed limits (or a stage's custom close-up view, for the opening
         frames). The chip never autoscales or shifts between frames.
    """
    # === Step 1: build the full final design, get centered limits ===
    final = _make_design()
    _populate_full_design(final)
    xlim, ylim = compute_centered_square_limits(final)

    # === Step 2: replay the build progressively, snapshot each stage ===
    design = _make_design()
    for stage_fn, filename, title, _dur, view in build_storyboard():
        if stage_fn is not None:
            stage_fn(design)
        if view is None:
            frame_xlim, frame_ylim = xlim, ylim
        else:
            cx, cy, half = view
            frame_xlim, frame_ylim = (cx - half, cx + half), (cy - half, cy + half)
        fig = render_frame(design, title, frame_xlim, frame_ylim)
        p = frame_dir / filename
        save_frame(fig, p)
        yield p


def stitch_gif(frame_paths, durations_ms):
    """Combine PNG frames into a looping GIF with per-frame durations."""
    imgs = [
        Image.open(p).convert("P", palette=Image.Palette.ADAPTIVE) for p in frame_paths
    ]
    # Normalize all frames to the size of frame 0 (savefig may pad differently)
    target_size = imgs[0].size
    imgs = [im.resize(target_size, Image.Resampling.LANCZOS) for im in imgs]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    imgs[0].save(
        OUT_PATH,
        save_all=True,
        append_images=imgs[1:],
        duration=durations_ms,
        loop=LOOP,
        optimize=True,
    )


def _build_mesh_design():
    """Build a MultiPlanar replica of the hero chip for Gmsh meshing.

    ``QGmshRenderer`` requires ``MultiPlanar`` (it needs the layer-stack
    metadata to compute mesh thickness/z-coordinates) — ``DesignPlanar``,
    used for the rest of the GIF, does not carry that. The component
    factories above only take ``design`` as a parameter, so replaying them
    on a second, separately-built ``MultiPlanar`` design reproduces the
    identical final geometry.
    """
    design = designs.MultiPlanar({}, overwrite_enabled=True)
    design.variables["cpw_width"] = "10 um"
    design.variables["cpw_gap"] = "6 um"
    design._chips["main"]["size"]["size_x"] = "8 mm"
    design._chips["main"]["size"]["size_y"] = "8 mm"
    _populate_full_design(design)
    # The chip includes real Airbridge components (see _add_airbridges);
    # their elevated-span layers aren't in a fresh MultiPlanar's default
    # layer stack, and QGmshRenderer needs a z/thickness entry for every
    # layer it meshes. Register them (also needs the matching layer_types
    # passed to QGmshRenderer below — see apply_airbridge_layer_stack's
    # docstring).
    apply_airbridge_layer_stack(design)
    return design


# Metal layer IDs QGmshRenderer must treat as metal: 1 = the normal chip
# metal layer, 30/31 = the airbridge span/pad layers apply_airbridge_layer_stack
# registers.
MESH_LAYER_TYPES = dict(metal=[1, 30, 31], dielectric=[3])


# High-contrast mesh palette — the QGmshRenderer defaults (steel-blue metal,
# light-gray dielectric) wash out at hero-GIF thumbnail size. Warm metal vs.
# deep-navy substrate, plotted on a dark axes background, reads clearly even
# at 640x640.
MESH_METAL_RGBA = (240, 155, 35, 255)  # amber/copper
MESH_JJ_RGBA = (235, 45, 130, 255)  # magenta — junctions, if any render
MESH_DIELECTRIC_RGBA = (16, 42, 82, 255)  # deep navy substrate
MESH_AXES_BG = (0.04, 0.06, 0.11)


def _mesh_and_extract(design, max_size, min_size):
    """Mesh ``design`` with Gmsh (2-D surface only) and pull out plottable
    triangles + per-triangle fill color + a metal/not-metal flag.

    Only ``add_mesh(dim=2)`` is generated — the full 3-D tetrahedral volume
    mesh (vacuum box included) takes tens of seconds even for a couple of
    qubits and isn't needed; the pseudo-3-D frame extrudes this same 2-D
    surface mesh instead of asking Gmsh for a real volume mesh.
    """
    from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

    import gmsh

    gr = QGmshRenderer(design, layer_types=MESH_LAYER_TYPES)
    gr.options.mesh.max_size = max_size
    gr.options.mesh.min_size = min_size
    gr.options.colors.metal = MESH_METAL_RGBA
    gr.options.colors.jj = MESH_JJ_RGBA
    gr.options.colors.dielectric = MESH_DIELECTRIC_RGBA
    gr.render_design(mesh_geoms=False)
    gr.add_mesh(dim=2, intelli_mesh=False)

    # Pull ALL node coordinates once into a tag->xy lookup. Calling
    # gmsh.model.mesh.getNode() per-vertex (one Python<->C API round trip
    # each) instead of batching like this is 10-50x slower on a full-chip
    # mesh (tens of thousands of triangles => 3x as many vertex lookups).
    node_tags_all, node_coords_all, _ = gmsh.model.mesh.getNodes()
    node_xy = dict(
        zip(node_tags_all, np.asarray(node_coords_all).reshape(-1, 3)[:, :2])
    )

    triangles, colors, is_metal = [], [], []
    for dim, tag in gmsh.model.getEntities(dim=2):
        color = gmsh.model.getColor(dim, tag)
        if color and color[3] != 0:
            rgba = tuple(c / 255 for c in color[:3]) + (1.0,)
            metal_flag = tuple(color[:3]) == tuple(MESH_METAL_RGBA[:3]) or tuple(
                color[:3]
            ) == tuple(MESH_JJ_RGBA[:3])
        else:
            rgba = (0.55, 0.55, 0.6, 1.0)
            metal_flag = False
        elem_types, _elem_tags, elem_node_tags = gmsh.model.mesh.getElements(
            dim=2, tag=tag
        )
        for etype, node_tags in zip(elem_types, elem_node_tags):
            if etype != 2:  # only 3-node triangles
                continue
            node_tags = np.asarray(node_tags).reshape(-1, 3)
            for tri in node_tags:
                triangles.append([tuple(node_xy[n]) for n in tri])
                colors.append(rgba)
                is_metal.append(metal_flag)
    gr.close()
    return triangles, colors, is_metal


def render_mesh_frame_2d(xlim, ylim, title, max_size, min_size, edge_alpha, linewidth):
    """Render the chip's Gmsh 2-D surface mesh, top-down.

    Raises ImportError if gmsh isn't installed — the caller decides whether
    that's fatal (it isn't, for this script: the frame is just skipped).
    """
    design = _build_mesh_design()
    triangles, colors, _is_metal = _mesh_and_extract(design, max_size, min_size)

    fig, ax = plt.subplots(figsize=FIGSIZE_INCH, dpi=DPI)
    ax.add_collection(
        PolyCollection(
            triangles,
            facecolor=colors,
            edgecolor=(1, 1, 1, edge_alpha),
            linewidth=linewidth,
        )
    )
    ax.set_facecolor(MESH_AXES_BG)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.92, bottom=0.10)
    return fig


# Illustrative z-scale for the pseudo-3-D frame — NOT to physical scale.
# Real metal/junction layers are sub-micron and would be invisible next to a
# 5mm chip; both are exaggerated purely so the extruded view reads as 3-D.
MESH_3D_METAL_Z_MM = 0.05
MESH_3D_SUBSTRATE_Z_MM = -0.35


def render_mesh_frame_3d(xlim, ylim, title):
    """Render a pseudo-3-D oblique view: the 2-D surface mesh extruded —
    metal triangles raised above a substrate slab drawn from the chip
    footprint. Reuses a coarse 2-D mesh (kept small on purpose: Poly3DCollection
    z-sorts by painter's algorithm, which gets slow and visually noisy well
    before Gmsh's own triangle count would).
    """
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    design = _build_mesh_design()
    triangles, colors, is_metal = _mesh_and_extract(
        design, max_size="250um", min_size="40um"
    )

    fig = plt.figure(figsize=FIGSIZE_INCH, dpi=DPI)
    ax = fig.add_subplot(111, projection="3d")

    verts3d = [
        [(x, y, MESH_3D_METAL_Z_MM if metal else 0.0) for x, y in tri]
        for tri, metal in zip(triangles, is_metal)
    ]
    ax.add_collection3d(
        Poly3DCollection(
            verts3d, facecolor=colors, edgecolor=(1, 1, 1, 0.2), linewidths=0.15
        )
    )

    half_x = design.parse_value(design._chips["main"]["size"]["size_x"]) / 2
    half_y = design.parse_value(design._chips["main"]["size"]["size_y"]) / 2
    sub_top = tuple(c / 255 for c in MESH_DIELECTRIC_RGBA[:3]) + (1.0,)
    sub_side = tuple(c * 0.65 for c in sub_top[:3]) + (1.0,)
    z0 = MESH_3D_SUBSTRATE_Z_MM
    corners = [
        (-half_x, -half_y),
        (half_x, -half_y),
        (half_x, half_y),
        (-half_x, half_y),
    ]
    bottom = [[(x, y, z0) for x, y in corners]]
    sides = [
        [
            (corners[i][0], corners[i][1], z0),
            (corners[(i + 1) % 4][0], corners[(i + 1) % 4][1], z0),
            (corners[(i + 1) % 4][0], corners[(i + 1) % 4][1], 0.0),
            (corners[i][0], corners[i][1], 0.0),
        ]
        for i in range(4)
    ]
    ax.add_collection3d(
        Poly3DCollection(
            bottom, facecolor=sub_top, edgecolor=(0, 0, 0, 0.3), linewidths=0.3
        )
    )
    ax.add_collection3d(
        Poly3DCollection(
            sides, facecolor=sub_side, edgecolor=(0, 0, 0, 0.3), linewidths=0.3
        )
    )

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_zlim(z0 - 0.1, MESH_3D_METAL_Z_MM + 0.3)
    ax.set_box_aspect((1, 1, 0.4))
    ax.view_init(elev=32, azim=-60)
    ax.set_axis_off()
    fig.patch.set_facecolor(MESH_AXES_BG)
    # A 3-D Axes draws its own opaque background patch independent of the
    # figure's — set it to match or the (dark) figure background never
    # shows through.
    ax.set_facecolor(MESH_AXES_BG)
    # mplot3d ignores subplots_adjust margins (it keeps its own internal
    # padding) — oversize the axes position instead to crop out the
    # leftover whitespace around the chip. Kept clear of the top ~12% so
    # the figure-level title (added after, drawn on top) isn't covered by
    # the axes' own opaque background.
    ax.set_position([-0.08, -0.14, 1.16, 1.00])
    fig.suptitle(title, fontsize=13, fontweight="bold", y=0.97, color="white")
    return fig


# Closing gallery: real 3-D airbridge renders already produced by tutorial
# 2.15 (PyVista, true depth-sorted — mplot3d can't do this well, hence
# borrowing rather than re-rendering). Read straight from the notebook's
# embedded cell outputs at build time instead of duplicating the PNGs as
# separate tracked files.
AIRBRIDGE_TUTORIAL_NOTEBOOK = Path(
    "tutorials/2 From components to chip/B. Routing between QComponents/2.15 Airbridges.ipynb"
)
AIRBRIDGE_GALLERY = [
    (24, "From tutorial 2.15 — a single airbridge, in 3-D (PyVista)"),
    (26, "...a full row, tying the ground plane together"),
]

# Eigenmode field distributions from a real pyPalace (open-source FEM)
# eigenmode simulation + EPR analysis of a transmon-resonator device.
# Source: quantum-device-consortium/qdw26-workshop-materials
# (workshops/electromagnetic-simulations/notebooks/eigenmode_EPR.ipynb),
# MIT licensed. Not generated by this script — Quantum Metal doesn't have
# a Palace/eigenmode-solver integration yet (see ROADMAP.md); these PNGs
# were pulled from that notebook's committed cell outputs once and are
# tracked as static assets here (no network call at hero-gif build time).
EIGENFIELD_GALLERY = [
    (
        "docs/_static/gallery/eigenfield_qubit_mode.png",
        "Eigenmode |E| — qubit mode (pyPalace, QDW26 workshop)",
    ),
    (
        "docs/_static/gallery/eigenfield_resonator_mode.png",
        "...and the resonator mode",
    ),
]


def _extract_notebook_cell_image(notebook_path, cell_index, out_path):
    """Pull the embedded PNG output of one notebook cell out to ``out_path``.

    Returns True on success, False if the notebook/cell/image isn't there
    (e.g. the tutorial was re-run and the cell no longer has that output) —
    the caller treats that as skip-this-frame, not a hard failure.
    """
    import base64
    import json

    if not notebook_path.exists():
        return False
    nb = json.loads(notebook_path.read_text())
    cells = nb.get("cells", [])
    if cell_index >= len(cells):
        return False
    for out in cells[cell_index].get("outputs", []):
        png_b64 = out.get("data", {}).get("image/png")
        if png_b64:
            out_path.write_bytes(base64.b64decode(png_b64))
            return True
    return False


def render_gallery_frame(image_path, title):
    """Wrap an existing PNG in the same title-bar framing as the rest of
    the GIF, so a borrowed image doesn't look visually out of place."""
    img = plt.imread(image_path)
    fig, ax = plt.subplots(figsize=FIGSIZE_INCH, dpi=DPI)
    ax.imshow(img)
    ax.axis("off")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.02)
    return fig


def main():
    storyboard = build_storyboard()
    durations = [stage[3] for stage in storyboard]
    with tempfile.TemporaryDirectory() as tmp:
        frame_paths = list(build_4qubit_chip_progressively(Path(tmp)))

        # Closing frames: the same chip's Gmsh FEM mesh — a 2-D surface
        # mesh, then a pseudo-3-D extrusion. Optional — gmsh is the [mesh]
        # extra, not installed by default.
        final = _make_design()
        _populate_full_design(final)
        xlim, ylim = compute_centered_square_limits(final)
        # Coarse mesh only. A fine pass (max_size=60um, min_size=10um) was
        # shown here too, but at 640x640 its elements are smaller than a
        # pixel — it reads as flat colour next to the coarse frame while
        # being by far the slowest stage to generate. render_mesh_frame_2d
        # still takes the sizes as parameters if a finer frame is ever
        # wanted.
        mesh_stages = [
            (
                lambda: render_mesh_frame_2d(
                    xlim,
                    ylim,
                    "Under the hood — FEM mesh",
                    max_size="300um",
                    min_size="60um",
                    edge_alpha=0.7,
                    linewidth=0.5,
                ),
                "14_mesh_coarse.png",
                1600,
            ),
            (
                lambda: render_mesh_frame_3d(xlim, ylim, "...and in 3-D"),
                "15_mesh_3d.png",
                1800,
            ),
        ]
        try:
            # Import check up front — fail on the FIRST mesh attempt only,
            # so a real bug in frame 2 or 3 doesn't get silently swallowed
            # as "gmsh not installed."
            import gmsh  # noqa: F401
        except ImportError:
            print(
                "  ⓘ gmsh not installed — skipping mesh frames "
                "(install with the [mesh] extra: uv run --extra mesh ...)"
            )
        else:
            for render_fn, filename, duration in mesh_stages:
                mesh_path = Path(tmp) / filename
                save_frame(render_fn(), mesh_path)
                frame_paths.append(mesh_path)
                durations.append(duration)

        # Closing gallery: real 3-D airbridge renders borrowed from
        # tutorial 2.15. Skipped per-image if the notebook or that cell's
        # output isn't there — not fatal to the rest of the GIF.
        for i, (cell_index, gallery_title) in enumerate(AIRBRIDGE_GALLERY):
            src_path = Path(tmp) / f"gallery_src_{i}.png"
            if not _extract_notebook_cell_image(
                AIRBRIDGE_TUTORIAL_NOTEBOOK, cell_index, src_path
            ):
                print(
                    f"  ⓘ tutorial 2.15 cell {cell_index} has no image — "
                    "skipping that gallery frame"
                )
                continue
            gallery_path = Path(tmp) / f"17_gallery_{i}.png"
            save_frame(render_gallery_frame(src_path, gallery_title), gallery_path)
            frame_paths.append(gallery_path)
            durations.append(1800)

        # Closing gallery, part 2: real eigenmode field distributions from
        # an actual open-source FEM solve (see EIGENFIELD_GALLERY). Static
        # tracked assets, not a live fetch — skipped per-image if missing.
        for i, (image_path, gallery_title) in enumerate(EIGENFIELD_GALLERY):
            image_path = Path(image_path)
            if not image_path.exists():
                print(f"  ⓘ {image_path} missing — skipping that gallery frame")
                continue
            gallery_path = Path(tmp) / f"18_eigenfield_{i}.png"
            save_frame(render_gallery_frame(image_path, gallery_title), gallery_path)
            frame_paths.append(gallery_path)
            durations.append(1800)

        stitch_gif(frame_paths, durations)
    size_kb = OUT_PATH.stat().st_size // 1024
    print(
        f"✓ wrote {OUT_PATH} ({size_kb} KB, {len(durations)} frames, "
        f"{sum(durations) / 1000:.1f}s loop)"
    )
    if size_kb > 1024:
        print("  ⚠ over 1 MB — consider reducing FIGSIZE_INCH or DPI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
