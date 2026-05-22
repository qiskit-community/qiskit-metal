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
# Keep the same axis across every frame so the chip doesn't jump
AXIS_LIMITS_MM = ((-3.5, 3.5), (-3.5, 3.5))


def render_frame(design, title):
    """Render the current design state to a matplotlib Figure with title overlay."""
    fig = qm.view(design)
    ax = fig.gca()
    ax.set_xlim(*AXIS_LIMITS_MM[0])
    ax.set_ylim(*AXIS_LIMITS_MM[1])
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title, fontsize=13, fontweight="bold", loc="left", pad=8)
    fig.set_size_inches(*FIGSIZE_INCH)
    fig.tight_layout()
    return fig


def save_frame(fig, path):
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.15,
                facecolor=fig.get_facecolor())
    plt.close(fig)


def build_4qubit_chip_progressively(frame_dir):
    """Yield (frame_path, frame_index) as the design grows. Saves PNGs to frame_dir."""
    design = designs.DesignPlanar()
    design.variables["cpw_width"] = "10 um"
    design.variables["cpw_gap"] = "6 um"
    design._chips["main"]["size"]["size_x"] = "6 mm"
    design._chips["main"]["size"]["size_y"] = "6 mm"

    # --- Frame 1: empty chip ---
    fig = render_frame(design, FRAME_TITLES[0])
    p = frame_dir / "01_canvas.png"
    save_frame(fig, p)
    yield p

    # --- Add 4 qubits at corners of a 1.5mm-radius ring ---
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

    # --- Frame 2: qubits placed ---
    fig = render_frame(design, FRAME_TITLES[1])
    p = frame_dir / "02_qubits.png"
    save_frame(fig, p)
    yield p

    # --- Add 4 CPW meander routes (Q1↔Q2, Q2↔Q3, Q3↔Q4, Q4↔Q1) ---
    fillet = "90 um"
    cpw_opts = Dict(
        lead=Dict(start_straight="100um", end_straight="100um"),
        fillet=fillet, total_length="3 mm", trace_width="10 um", trace_gap="6 um",
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

    # --- Frame 3: with routing ---
    fig = render_frame(design, FRAME_TITLES[2])
    p = frame_dir / "03_routing.png"
    save_frame(fig, p)
    yield p

    # --- Add 4 launchpads at the chip edges ---
    LaunchpadWirebond(design, "P1", options=Dict(pos_x="+2.8mm", pos_y="0mm", orientation="180"))
    LaunchpadWirebond(design, "P2", options=Dict(pos_x="0mm", pos_y="+2.8mm", orientation="270"))
    LaunchpadWirebond(design, "P3", options=Dict(pos_x="-2.8mm", pos_y="0mm", orientation="0"))
    LaunchpadWirebond(design, "P4", options=Dict(pos_x="0mm", pos_y="-2.8mm", orientation="90"))
    design.rebuild()

    # --- Frame 4: with launchpads ---
    fig = render_frame(design, FRAME_TITLES[3])
    p = frame_dir / "04_launchpads.png"
    save_frame(fig, p)
    yield p

    # --- Frame 5: final "qm.view(design)" hold ---
    fig = render_frame(design, FRAME_TITLES[4])
    p = frame_dir / "05_final.png"
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
