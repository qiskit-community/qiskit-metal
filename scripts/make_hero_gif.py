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
FIGSIZE_INCH = (8.0, 6.0)
DPI = 100  # → 800×600 PNG frames
LOOP = 0  # 0 = infinite loop
# Hold the final frame longer so viewers register the result
FRAME_DURATIONS_MS = [1100, 1100, 1600, 1100, 1800]
FRAME_TITLES = [
    "Step 1 — Create the chip canvas",
    "Step 2 — Add 4 transmon qubits",
    "Step 3 — Route the resonators (CPW meanders)",
    "Step 4 — Add launchpad wirebonds",
    "qm.view(design)   →   chip ready for fab/sim",
]
# Padding factor applied to the final-design bbox to compute axis limits.
# Set once, used for every frame, so the chip never jumps or autoscales
# asymmetrically between frames (a known matplotlib pitfall the user has
# fought multiple times — see "centering" note below).
AXIS_PADDING_FRAC = 0.10  # 10% padding around the final bbox


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
    design._chips["main"]["size"]["size_x"] = "6 mm"
    design._chips["main"]["size"]["size_y"] = "6 mm"
    return design


def _add_qubits(design):
    qubit_opts = Dict(
        pad_width="425 um", pad_height="250 um",
        pocket_width="600 um", pocket_height="600 um",
        connection_pads=Dict(
            a=Dict(loc_W=+1, loc_H=+1, pad_width="120um", cpw_extend="80um"),
            b=Dict(loc_W=-1, loc_H=+1, pad_width="120um", cpw_extend="80um"),
            c=Dict(loc_W=-1, loc_H=-1, pad_width="120um", cpw_extend="80um"),
            d=Dict(loc_W=+1, loc_H=-1, pad_width="120um", cpw_extend="80um"),
        ),
    )
    TransmonPocket(design, "Q1", options=Dict(pos_x="+1.5mm", pos_y="+1.5mm", **qubit_opts))
    TransmonPocket(design, "Q2", options=Dict(pos_x="-1.5mm", pos_y="+1.5mm", **qubit_opts))
    TransmonPocket(design, "Q3", options=Dict(pos_x="-1.5mm", pos_y="-1.5mm", **qubit_opts))
    TransmonPocket(design, "Q4", options=Dict(pos_x="+1.5mm", pos_y="-1.5mm", **qubit_opts))
    design.rebuild()


def _add_routing(design):
    cpw_opts = Dict(
        lead=Dict(start_straight="100um", end_straight="100um"),
        fillet="90 um", total_length="3 mm",
        trace_width="10 um", trace_gap="6 um",
    )

    def cpw(name, qa, pa, qb, pb):
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

    cpw("cpw_12", "Q1", "b", "Q2", "a")  # top edge
    cpw("cpw_23", "Q2", "c", "Q3", "b")  # left edge
    cpw("cpw_34", "Q3", "d", "Q4", "c")  # bottom edge
    cpw("cpw_41", "Q4", "a", "Q1", "d")  # right edge
    design.rebuild()


def _add_launchpads(design):
    LaunchpadWirebond(design, "P1", options=Dict(pos_x="+2.8mm", pos_y="0mm", orientation="180"))
    LaunchpadWirebond(design, "P2", options=Dict(pos_x="0mm", pos_y="+2.8mm", orientation="270"))
    LaunchpadWirebond(design, "P3", options=Dict(pos_x="-2.8mm", pos_y="0mm", orientation="0"))
    LaunchpadWirebond(design, "P4", options=Dict(pos_x="0mm", pos_y="-2.8mm", orientation="90"))
    design.rebuild()


def _populate_full_design(design):
    """Apply every stage so the FINAL design exists. Used for centering compute."""
    _add_qubits(design)
    _add_routing(design)
    _add_launchpads(design)


def build_4qubit_chip_progressively(frame_dir):
    """Yield frame_path as the design grows. Saves PNGs to frame_dir.

    Centering pattern (per the user's "do it at the very end" rule):
      1. Build the FINAL design first (no rendering) → compute centered limits.
      2. Replay the build step-by-step, capturing each stage with THOSE
         fixed limits. The chip never autoscales or shifts between frames.
    """
    # === Step 1: build the full final design, get centered limits ===
    final = _make_design()
    _populate_full_design(final)
    xlim, ylim = compute_centered_square_limits(final)

    # === Step 2: replay the build progressively, snapshot each stage ===
    stages = [
        # (stage_fn or None for empty, frame filename, title)
        (None,              "01_canvas.png",     FRAME_TITLES[0]),
        (_add_qubits,       "02_qubits.png",     FRAME_TITLES[1]),
        (_add_routing,      "03_routing.png",    FRAME_TITLES[2]),
        (_add_launchpads,   "04_launchpads.png", FRAME_TITLES[3]),
        # Final hold — same content as frame 4, different title
        (None,              "05_final.png",      FRAME_TITLES[4]),
    ]
    design = _make_design()
    for stage_fn, filename, title in stages:
        if stage_fn is not None:
            stage_fn(design)
        fig = render_frame(design, title, xlim, ylim)
        p = frame_dir / filename
        save_frame(fig, p)
        yield p


def stitch_gif(frame_paths):
    """Combine PNG frames into a looping GIF with per-frame durations."""
    imgs = [Image.open(p).convert("P", palette=Image.Palette.ADAPTIVE) for p in frame_paths]
    # Normalize all frames to the size of frame 0 (savefig may pad differently)
    target_size = imgs[0].size
    imgs = [im.resize(target_size, Image.Resampling.LANCZOS) for im in imgs]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    imgs[0].save(
        OUT_PATH, save_all=True, append_images=imgs[1:],
        duration=FRAME_DURATIONS_MS, loop=LOOP, optimize=True,
    )


def main():
    with tempfile.TemporaryDirectory() as tmp:
        frame_paths = list(build_4qubit_chip_progressively(Path(tmp)))
        stitch_gif(frame_paths)
    size_kb = OUT_PATH.stat().st_size // 1024
    print(f"✓ wrote {OUT_PATH} ({size_kb} KB, {len(FRAME_DURATIONS_MS)} frames, "
          f"{sum(FRAME_DURATIONS_MS)/1000:.1f}s loop)")
    if size_kb > 1024:
        print(f"  ⚠ over 1 MB — consider reducing FIGSIZE_INCH or DPI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
