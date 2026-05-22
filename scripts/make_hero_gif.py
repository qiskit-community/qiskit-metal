# /// script
# requires-python = ">=3.10"
# ///
"""Generate the hero animated GIF for the README.

Builds a 4-qubit ring chip progressively (canvas → qubits → CPW routes →
launchpads → final view) and stitches each stage into a ~6-second
looping GIF. Showcases the design-as-code workflow in a glance.

The script uses the same ``qm.view(design)`` API end users would run,
so the GIF stays honest — what viewers see is exactly what they'd get
by pasting the equivalent ~15 lines into a notebook.

Output: docs/_static/hero.gif (~500KB at 800×600)

Run from the repo root:
    uv run --with pillow scripts/make_hero_gif.py
"""

import os
import sys
import tempfile
from pathlib import Path

# Silence the v0.8 rename warning chatter (doesn't affect rendering)
os.environ.setdefault("QISKIT_METAL_SUPPRESS_RENAME_WARNING", "1")

import matplotlib.pyplot as plt
from PIL import Image

import qiskit_metal as qm
from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder


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
    design._chips["main"]["size"]["size_x"] = "5 mm"
    design._chips["main"]["size"]["size_y"] = "5 mm"
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

# Launchpads at corners (±2.0, ±2.0) — close to qubits, connected via short
# CPW feed lines to each qubit's outward (free) pin. Pin name "N" on Q1
# (NE-facing pocket pin) → P1 at the NE corner pointing back at it, etc.
# Direction matters: launchpad orientation must face inward toward its qubit.
LAUNCHPADS = [
    # (name, x, y, orient°, connect_to_qubit, connect_to_pin)
    ("P1", "+2.0mm", "+2.0mm", "225", "Q1", "a"),  # NE
    ("P2", "-2.0mm", "+2.0mm", "315", "Q2", "b"),  # NW
    ("P3", "-2.0mm", "-2.0mm", "45", "Q3", "c"),  # SW
    ("P4", "+2.0mm", "-2.0mm", "135", "Q4", "d"),  # SE
]


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
    second qubit-type without disturbing the ring's pocket-based routing.
    """
    TransmonCross(
        design,
        "Qx",
        options=Dict(
            pos_x="0mm",
            pos_y="0mm",
            cross_length="180um",
            cross_gap="25um",
            cross_width="20um",
        ),
    )
    design.rebuild()


def _compute_robust_cpw_opts(design, qa, pa, qb, pb):
    """Compute CPW meander options sized to the ACTUAL pin-to-pin distance.

    Why this is dynamic, not hardcoded: RouteMeander has a known geometry
    bug — ``meander_number = np.floor(length_direct / spacing)`` (see
    src/qiskit_metal/qlibrary/tlines/meandered.py:~166) — that produces
    different wiggle counts for geometrically-equivalent horizontal vs
    vertical routes, because tiny floating-point asymmetries in
    ``length_direct`` push the floor() result across integer boundaries.
    The per-wiggle excursion is then ``length_excess/(meander_number*2)``,
    so a one-extra-wiggle route ends up with much smaller bumps that
    render as sharp "kinks" / castellations.

    The portable workaround across ANY qubit layout: pick ``spacing``
    LARGER than the actual pin-to-pin distance, so ``floor()`` is
    guaranteed to land on 1. One big symmetric hump every time, regardless
    of route orientation or chip size. We read the distance from the live
    design's pin positions instead of hardcoding a value, so this keeps
    working if Q_SPEC changes (different qubit spacing, or someone forks
    the script for a new layout).
    """
    import numpy as np

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


def _add_launchpads_and_connections(design):
    """All 4 launchpads + their connecting CPWs in one shot (last build frame)."""
    # Use RoutePathfinder (straight + fillet) rather than RouteMeander —
    # the launchpad-to-qubit feeds are short and don't need wiggle. This
    # also removes the spurious meander-segment kinks at corners.
    feed_opts = Dict(
        lead=Dict(start_straight="60um", end_straight="60um"),
        fillet="80 um",
        trace_width="10 um",
        trace_gap="6 um",
    )
    for name, x, y, orient, q, pin in LAUNCHPADS:
        LaunchpadWirebond(
            design,
            name,
            options=Dict(
                pos_x=x,
                pos_y=y,
                orientation=orient,
                pad_width="120um",
                pad_height="120um",
                pad_gap="80um",
                lead_length="20um",
            ),
        )
        RoutePathfinder(
            design,
            f"feed_{name}",
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component=q, pin=pin),
                    end_pin=Dict(component=name, pin="tie"),
                ),
                **feed_opts,
            ),
        )
    design.rebuild()


def _populate_full_design(design):
    """Apply every stage so the FINAL design exists. Used for centering compute."""
    for name in Q_SPEC:
        _qubit_factory(name)(design)
    for spec in RING_CPWS:
        _cpw_factory(spec)(design)
    _add_launchpads_and_connections(design)
    _add_center_cross_showcase(design)


def build_storyboard():
    """Returns the ordered list of (stage_fn, filename, title, duration_ms)."""
    stages = []
    stages.append((None, "00_canvas.png", "Step 1 — Create the chip canvas", 600))
    # Qubits appear one by one — snappy, ~350ms each
    qubit_titles = [
        "Step 2 — Add qubit Q1",
        "Step 2 — Add qubit Q2",
        "Step 2 — Add qubit Q3",
        "Step 2 — All 4 transmons placed",
    ]
    for i, name in enumerate(Q_SPEC):
        dur = 500 if i == len(Q_SPEC) - 1 else 320  # slight hold on the last
        stages.append(
            (_qubit_factory(name), f"0{i + 1}_{name}.png", qubit_titles[i], dur)
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
            (_cpw_factory(spec), f"0{i + 5}_{spec[0]}.png", cpw_titles[i], dur)
        )
    # Launchpads + their connecting CPWs in one shot
    stages.append(
        (
            _add_launchpads_and_connections,
            "09_launchpads.png",
            "Step 4 — Launchpads + feed lines",
            600,
        )
    )
    # Showcase a second qubit type (TransmonCross) appearing at the centre —
    # demonstrates the qlibrary has more than one transmon kind.
    stages.append(
        (
            _add_center_cross_showcase,
            "10_cross.png",
            "Or pick from 13+ qubit types  (TransmonCross shown)",
            800,
        )
    )
    # Final long hold so viewers register the result
    stages.append(
        (None, "11_final.png", "qm.view(design)   →   chip ready for fab/sim", 1600)
    )
    return stages


def build_4qubit_chip_progressively(frame_dir):
    """Yield frame_path as the design grows. Saves PNGs to frame_dir.

    Centering pattern (per the "do it at the very end" rule):
      1. Build the FINAL design first (no rendering) → compute centered limits.
      2. Replay the build step-by-step, capturing each stage with THOSE
         fixed limits. The chip never autoscales or shifts between frames.
    """
    # === Step 1: build the full final design, get centered limits ===
    final = _make_design()
    _populate_full_design(final)
    xlim, ylim = compute_centered_square_limits(final)

    # === Step 2: replay the build progressively, snapshot each stage ===
    design = _make_design()
    for stage_fn, filename, title, _dur in build_storyboard():
        if stage_fn is not None:
            stage_fn(design)
        fig = render_frame(design, title, xlim, ylim)
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


def main():
    storyboard = build_storyboard()
    durations = [d for *_, d in storyboard]
    with tempfile.TemporaryDirectory() as tmp:
        frame_paths = list(build_4qubit_chip_progressively(Path(tmp)))
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
