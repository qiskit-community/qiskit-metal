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
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander


# --- Configuration ---
OUT_PATH = Path("docs/_static/hero.gif")
FIGSIZE_INCH = (7.2, 5.4)
DPI = 100  # → 720×540 PNG frames (smaller than v1's 800×600)
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
    half *= (1.0 + pad_frac)
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
    fig.savefig(path, dpi=DPI, pad_inches=0.15,
                facecolor=fig.get_facecolor())
    plt.close(fig)


def _make_design():
    """Build the design from scratch — no rendering. Returns the empty design."""
    design = designs.DesignPlanar()
    design.variables["cpw_width"] = "10 um"
    design.variables["cpw_gap"] = "6 um"
    design._chips["main"]["size"]["size_x"] = "5 mm"
    design._chips["main"]["size"]["size_y"] = "5 mm"
    return design


# Standard TransmonPocket geometry — uses library defaults (pad 455×90 um,
# pocket 650×650 um) so the shape is the canonical "thin pads + square
# pocket" transmon every superconducting-qubit reader recognises. Only the
# connection_pads dict is customised (4 pins at the corners for ring routing).
_QUBIT_OPTS = Dict(
    connection_pads=Dict(
        a=Dict(loc_W=+1, loc_H=+1, pad_width="120um", cpw_extend="80um"),
        b=Dict(loc_W=-1, loc_H=+1, pad_width="120um", cpw_extend="80um"),
        c=Dict(loc_W=-1, loc_H=-1, pad_width="120um", cpw_extend="80um"),
        d=Dict(loc_W=+1, loc_H=-1, pad_width="120um", cpw_extend="80um"),
    ),
)

# Tighter qubit ring: ±1.0 mm (was ±1.5) — pulls components closer together
# so the whole chip fits in a more zoomed-in view.
Q_POS = {
    "Q1": ("+1.0mm", "+1.0mm"),
    "Q2": ("-1.0mm", "+1.0mm"),
    "Q3": ("-1.0mm", "-1.0mm"),
    "Q4": ("+1.0mm", "-1.0mm"),
}

# Ring routing: 4 CPW meanders connecting adjacent qubits (Q1↔Q2 top edge,
# Q2↔Q3 left, Q3↔Q4 bottom, Q4↔Q1 right). The order is also the build order
# (each frame adds one CPW).
RING_CPWS = [
    ("cpw_12", "Q1", "b", "Q2", "a"),  # top edge
    ("cpw_23", "Q2", "c", "Q3", "b"),  # left edge
    ("cpw_34", "Q3", "d", "Q4", "c"),  # bottom edge
    ("cpw_41", "Q4", "a", "Q1", "d"),  # right edge
]

# Launchpads at corners (±1.9, ±1.9) — closer to qubits than v1's ±2.8 — and
# connected to each qubit's outward pin via a short CPW. Direction matters:
# the launchpad orientation must face inward toward its qubit.
LAUNCHPADS = [
    # (name, x, y, orient°, connect_to_qubit, connect_to_pin)
    ("P1", "+1.9mm", "+1.9mm", "225", "Q1", "a"),  # NE
    ("P2", "-1.9mm", "+1.9mm", "315", "Q2", "b"),  # NW
    ("P3", "-1.9mm", "-1.9mm",  "45", "Q3", "c"),  # SW
    ("P4", "+1.9mm", "-1.9mm", "135", "Q4", "d"),  # SE
]


def _qubit_factory(name):
    """Returns a function that adds qubit `name` and rebuilds."""
    def add(design):
        x, y = Q_POS[name]
        TransmonPocket(design, name, options=Dict(pos_x=x, pos_y=y, **_QUBIT_OPTS))
        design.rebuild()
    return add


def _cpw_factory(cpw_spec):
    """Returns a function that adds one CPW meander and rebuilds."""
    name, qa, pa, qb, pb = cpw_spec
    cpw_opts = Dict(
        lead=Dict(start_straight="60um", end_straight="60um"),
        fillet="60 um", total_length="2 mm",
        trace_width="10 um", trace_gap="6 um",
    )

    def add(design):
        RouteMeander(
            design, name,
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component=qa, pin=pa),
                    end_pin=Dict(component=qb, pin=pb),
                ),
                **cpw_opts,
            ),
        )
        design.rebuild()
    return add


def _add_launchpads_and_connections(design):
    """All 4 launchpads + their connecting CPWs in one shot (last build frame)."""
    feed_opts = Dict(
        lead=Dict(start_straight="40um", end_straight="40um"),
        fillet="40 um", total_length="0.6 mm",
        trace_width="10 um", trace_gap="6 um",
    )
    for name, x, y, orient, q, pin in LAUNCHPADS:
        LaunchpadWirebond(design, name, options=Dict(
            pos_x=x, pos_y=y, orientation=orient,
            pad_width="120um", pad_height="120um",
            pad_gap="80um", lead_length="20um",
        ))
        RouteMeander(
            design, f"feed_{name}",
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
    for name in Q_POS:
        _qubit_factory(name)(design)
    for spec in RING_CPWS:
        _cpw_factory(spec)(design)
    _add_launchpads_and_connections(design)


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
    for i, name in enumerate(Q_POS):
        dur = 500 if i == len(Q_POS) - 1 else 320  # slight hold on the last
        stages.append((_qubit_factory(name), f"0{i+1}_{name}.png", qubit_titles[i], dur))
    # Then CPWs one by one
    cpw_titles = [
        "Step 3 — Route Q1↔Q2 (CPW meander)",
        "Step 3 — Route Q2↔Q3",
        "Step 3 — Route Q3↔Q4",
        "Step 3 — Ring complete (4 resonators)",
    ]
    for i, spec in enumerate(RING_CPWS):
        dur = 550 if i == len(RING_CPWS) - 1 else 320
        stages.append((_cpw_factory(spec), f"0{i+5}_{spec[0]}.png", cpw_titles[i], dur))
    # Launchpads + their connecting CPWs in one shot
    stages.append((_add_launchpads_and_connections, "09_launchpads.png",
                   "Step 4 — Launchpads + feed lines", 700))
    # Final long hold so viewers register the result
    stages.append((None, "10_final.png",
                   "qm.view(design)   →   chip ready for fab/sim", 1700))
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
    imgs = [Image.open(p).convert("P", palette=Image.Palette.ADAPTIVE) for p in frame_paths]
    # Normalize all frames to the size of frame 0 (savefig may pad differently)
    target_size = imgs[0].size
    imgs = [im.resize(target_size, Image.Resampling.LANCZOS) for im in imgs]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    imgs[0].save(
        OUT_PATH, save_all=True, append_images=imgs[1:],
        duration=durations_ms, loop=LOOP, optimize=True,
    )


def main():
    storyboard = build_storyboard()
    durations = [d for *_, d in storyboard]
    with tempfile.TemporaryDirectory() as tmp:
        frame_paths = list(build_4qubit_chip_progressively(Path(tmp)))
        stitch_gif(frame_paths, durations)
    size_kb = OUT_PATH.stat().st_size // 1024
    print(f"✓ wrote {OUT_PATH} ({size_kb} KB, {len(durations)} frames, "
          f"{sum(durations)/1000:.1f}s loop)")
    if size_kb > 1024:
        print(f"  ⚠ over 1 MB — consider reducing FIGSIZE_INCH or DPI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
