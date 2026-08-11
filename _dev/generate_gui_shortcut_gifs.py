# /// script
# requires-python = ">=3.10"
# ///
"""Generate the animated GIFs for the GUI shortcuts docs page.

``docs/gui-shortcuts.rst`` already has static SVG diagrams
(``_dev/generate_gui_shortcut_diagrams.py``) explaining the key bindings.
These GIFs show what the interaction actually looks like: a selected
component (red highlight box, same style ``MetalGUI.highlight_components``
draws) moving, rotating, and surviving a rebuild -- with a keycap badge in
the corner of each frame showing which key is being pressed.

Headless by design, same principle as ``scripts/make_hero_gif.py``: every
frame is a plain ``qm.view(design)`` render plus a hand-drawn highlight
rectangle matching the real highlight's exact style (red edge, light red
fill) -- no live Qt window, no display, nothing a viewer wouldn't also get
from the documented API. The nudge/rotate arithmetic mirrors
``MetalGUI.nudge_component``/``rotate_component`` (same step sizes) without
requiring a QApplication to call them.

``rebuild.gif`` additionally distinguishes a per-component rebuild
(``component.rebuild()``, what a real arrow-key nudge does -- the route
does NOT re-route) from a full design rebuild (``design.rebuild()``, what
pressing R does -- the route re-routes), so the route visibly lags during
the move frames and snaps into place on the R frame, matching real
``MetalGUI`` behavior instead of glossing over it.

Keycap badges are rasterized from the vendored SVGs in
``_dev/assets/keyicons/`` (subset of georgemblack/svg-keyboard-icons, MIT
-- see that folder's README) via the ``rsvg-convert`` CLI
(``brew install librsvg`` if missing).

Output: docs/images/gui-shortcuts/{move,rotate,rebuild}.gif

Run from the repo root:
    uv run --with pillow --with matplotlib python _dev/generate_gui_shortcut_gifs.py
"""

import io
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QISKIT_METAL_SUPPRESS_RENAME_WARNING", "1")
os.environ.setdefault("QISKIT_METAL_HEADLESS", "1")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import Rectangle
from PIL import Image

import qiskit_metal as qm
from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "docs" / "images" / "gui-shortcuts"
ICON_DIR = REPO / "_dev" / "assets" / "keyicons"

FIGSIZE_INCH = (4.2, 4.2)
DPI = 110
LOOP = 0  # infinite

# Same constants as MetalGUI.nudge_component / rotate_component's callers
# in mpl_canvas.py -- the coarse (Shift) step is what's actually visible at
# chip scale; the plain 0.05mm step is imperceptible in a wide view, and the
# fine (Alt) step (NUDGE_STEP_MM * NUDGE_FINE_FACTOR = 0.005mm) needs both a
# tight zoom and several presses aggregated per frame to read as motion at all.
NUDGE_STEP_MM = 0.05
NUDGE_COARSE_MM = 0.5
NUDGE_FINE_MM = 0.005
ROTATE_STEP_DEG = 90.0
ROTATE_FINE_DEG = 15.0

# Same palette as the real highlight_components() in mpl_canvas.py, so
# these frames look like an actual screenshot, not a reinterpretation.
HIGHLIGHT_EDGE = "r"
HIGHLIGHT_FACE = (1, 0, 0, 0.05)

# --- Keycap badges --------------------------------------------------------

ICON_RASTER_PX = 240  # rsvg-convert output size; downscaled by IMAGE_ZOOM
ICON_ZOOM = 0.16
ICON_GAP_PX = 18  # gap between icons in a combo badge, e.g. Shift + Q
ICON_ANCHOR = (0.96, 0.06)  # axes-fraction anchor, bottom-right corner
_icon_cache = {}


def _rasterize_icon(name: str) -> Image.Image:
    if name not in _icon_cache:
        svg_path = ICON_DIR / f"{name}.svg"
        result = subprocess.run(
            [
                "rsvg-convert",
                "-w",
                str(ICON_RASTER_PX),
                "-h",
                str(ICON_RASTER_PX),
                str(svg_path),
            ],
            capture_output=True,
            check=True,
        )
        _icon_cache[name] = Image.open(io.BytesIO(result.stdout)).convert("RGBA")
    return _icon_cache[name]


def _key_badge_image(key):
    """``key`` is an icon name, a tuple of icon names composed left-to-right
    (e.g. ``("shift", "q")``), or None for no badge."""
    names = (key,) if isinstance(key, str) else tuple(key)
    icons = [_rasterize_icon(n) for n in names]
    h = max(im.height for im in icons)
    w = sum(im.width for im in icons) + ICON_GAP_PX * (len(icons) - 1)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for im in icons:
        canvas.paste(im, (x, (h - im.height) // 2), im)
        x += im.width + ICON_GAP_PX
    return canvas


def add_key_badge(ax, key):
    if key is None:
        return
    oi = OffsetImage(np.array(_key_badge_image(key)), zoom=ICON_ZOOM)
    ab = AnnotationBbox(
        oi,
        ICON_ANCHOR,
        xycoords="axes fraction",
        box_alignment=(1, 0),
        frameon=False,
        pad=0,
        annotation_clip=False,
    )
    ax.add_artist(ab)


# --- Design helpers --------------------------------------------------------


def _make_design():
    design = designs.DesignPlanar()
    design._chips["main"]["size"]["size_x"] = "4mm"
    design._chips["main"]["size"]["size_y"] = "4mm"
    TransmonPocket(
        design,
        "Q1",
        options=dict(pos_x="0mm", pos_y="0mm", pad_width="425um"),
    )
    design.rebuild()
    return design


def _axis_limits_for_path(design, name, positions_mm, pad_frac=0.35):
    """Bounding box covering every position the component visits, so the
    frame never re-centers or jumps between steps."""
    comp = design.components[name]
    base_x, base_y = float(comp.options.pos_x[:-2]), float(comp.options.pos_y[:-2])
    half_w = 0.6  # generous half-width around the qubit footprint, in mm

    xs, ys = [], []
    for dx, dy in positions_mm:
        xs += [base_x + dx - half_w, base_x + dx + half_w]
        ys += [base_y + dy - half_w, base_y + dy + half_w]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 * (1 + pad_frac)
    return (cx - half, cx + half), (cy - half, cy + half)


def render_frame(design, name, caption, xlim, ylim, key=None):
    """One qm.view() frame with a hand-drawn highlight box on ``name`` and
    an optional keycap badge in the corner."""
    fig = qm.view(design)
    ax = fig.gca()

    bounds = design.components[name].qgeometry_bounds()
    ax.add_patch(
        Rectangle(
            (bounds[0], bounds[1]),
            bounds[2] - bounds[0],
            bounds[3] - bounds[1],
            linewidth=1.5,
            edgecolor=HIGHLIGHT_EDGE,
            facecolor=HIGHLIGHT_FACE,
            zorder=99,
        )
    )

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(caption, fontsize=11, fontweight="bold", pad=8)
    add_key_badge(ax, key)
    fig.set_size_inches(*FIGSIZE_INCH)
    fig.subplots_adjust(left=0.06, right=0.97, top=0.90, bottom=0.06)
    return fig


def save_frame(fig, path):
    fig.savefig(path, dpi=DPI, pad_inches=0.12, facecolor=fig.get_facecolor())
    plt.close(fig)


def _write_gif(frame_paths, out_path, hold_frames=(), duration_ms=550, hold_ms=1400):
    """Stitch PNG frames into a looping GIF.

    Args:
        hold_frames: 0-based indices that should linger longer than the
            rest (e.g. the "R rebuild()" beat) -- done by literal frame
            repetition, since GIF87a per-frame duration support is patchy
            across viewers but repeated frames always work.
    """
    frames = [Image.open(p).convert("P", palette=Image.ADAPTIVE) for p in frame_paths]
    durations = [
        hold_ms if i in hold_frames else duration_ms for i in range(len(frames))
    ]
    # optimize=True silently drops/merges frames Pillow judges too similar
    # to their predecessor (confirmed: a 6-frame sequence with two frames
    # at the same qubit position -- differing only in caption text --
    # saved as 5). Correctness over file size: optimize stays off.
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=LOOP,
        optimize=False,
    )
    reloaded = Image.open(out_path)
    n_written = 0
    try:
        while True:
            reloaded.seek(n_written)
            n_written += 1
    except EOFError:
        pass
    if n_written != len(frames):
        raise RuntimeError(
            f"{out_path.name}: wrote {len(frames)} frames but the GIF "
            f"contains {n_written} -- Pillow dropped/merged frames again."
        )


def make_move_gif(tmp_dir: Path):
    """A small square path (coarse/Shift step), out and back, then a
    zoomed-in coda showing the fine (Alt) step -- 0.005mm is imperceptible
    at the coarse loop's zoom, so several presses are aggregated per frame
    and the caption says so rather than implying one key send that far."""
    design = _make_design()
    name = "Q1"
    step = NUDGE_COARSE_MM

    # (dx, dy, key) at each step, relative to start; traces a closed square
    # so frame N+1 loops cleanly back into frame 0.
    deltas = [
        (step, 0, "rightarrow"),
        (step, 0, "rightarrow"),
        (0, -step, "downarrow"),
        (0, -step, "downarrow"),
        (-step, 0, "leftarrow"),
        (-step, 0, "leftarrow"),
        (0, step, "uparrow"),
        (0, step, "uparrow"),
    ]
    path = [(0, 0, None)]
    for dx, dy, key in deltas:
        px, py, _ = path[-1]
        path.append((px + dx, py + dy, key))

    wide_xlim, wide_ylim = _axis_limits_for_path(
        design, name, [(x, y) for x, y, _ in path]
    )

    frame_paths = []
    base_x = float(design.components[name].options.pos_x[:-2])
    base_y = float(design.components[name].options.pos_y[:-2])
    for i, (dx, dy, key) in enumerate(path):
        design.components[name].options.pos_x = f"{base_x + dx}mm"
        design.components[name].options.pos_y = f"{base_y + dy}mm"
        design.rebuild()
        caption = (
            "click to select the component" if key is None else "arrow keys move it"
        )
        fig = render_frame(design, name, caption, wide_xlim, wide_ylim, key=key)
        p = tmp_dir / f"move_{i:02d}.png"
        save_frame(fig, p)
        frame_paths.append(p)

    # Fine-step coda: zoomed in tight on just the qubit -- 10 aggregated Alt
    # presses per frame (10 * 0.005mm = 0.05mm, the same magnitude as one
    # plain unmodified press) is the least that reads as motion at all.
    presses_per_frame = 10
    fine_step = presses_per_frame * NUDGE_FINE_MM
    fine_deltas = [
        (0, -fine_step, "alt", "downarrow"),
        (0, -fine_step, "alt", "downarrow"),
        (0, fine_step, "alt", "uparrow"),
        (0, fine_step, "alt", "uparrow"),
    ]
    fine_path = [(0, 0, None, None)]
    for dx, dy, mod_key, dir_key in fine_deltas:
        px, py, _, _ = fine_path[-1]
        fine_path.append((px + dx, py + dy, mod_key, dir_key))

    # A tight, fixed-width crop around just the qubit body -- the shared
    # helper's 0.6mm padding is calibrated for the coarse loop and would
    # swamp a 0.05mm shift entirely.
    fine_half = 0.3
    fine_xlim, fine_ylim = (-fine_half, fine_half), (-fine_half, fine_half)
    for i, (dx, dy, mod_key, dir_key) in enumerate(fine_path):
        design.components[name].options.pos_x = f"{base_x + dx}mm"
        design.components[name].options.pos_y = f"{base_y + dy}mm"
        design.rebuild()
        if dir_key is None:
            caption = "zoomed in for the fine step"
            key = None
        else:
            caption = f"Alt + arrow key -- {presses_per_frame} fine steps shown here"
            key = (mod_key, dir_key)
        fig = render_frame(design, name, caption, fine_xlim, fine_ylim, key=key)
        p = tmp_dir / f"move_fine_{i:02d}.png"
        save_frame(fig, p)
        frame_paths.append(p)

    _write_gif(frame_paths, OUT_DIR / "move.gif", hold_frames={len(path)})


def make_rotate_gif(tmp_dir: Path):
    """A full 90-degree-step rotation back to start, then a 15-degree
    fine-step wiggle (Shift) that also returns to net zero."""
    design = _make_design()
    name = "Q1"

    # (label, degrees-this-step, key)
    steps = [
        ("start", 0, None),
        ("Q  (or [ / E / ])  → 90°", 90, "q"),
        ("90°", 90, "q"),
        ("90°", 90, "q"),
        ("90°  (full circle)", 90, "q"),
        ("Shift + Q  → 15° (fine)", 15, ("shift", "q")),
        ("Shift + Q  → 15°", 15, ("shift", "q")),
        ("Shift + E  → -15°", -15, ("shift", "e")),
        ("Shift + E  → -15° (back to start)", -15, ("shift", "e")),
    ]

    xlim, ylim = _axis_limits_for_path(design, name, [(0, 0)], pad_frac=0.5)

    frame_paths = []
    current = 0.0
    for i, (caption, delta, key) in enumerate(steps):
        current = (current + delta) % 360.0
        design.components[name].options.orientation = str(current)
        design.rebuild()
        fig = render_frame(design, name, caption, xlim, ylim, key=key)
        p = tmp_dir / f"rotate_{i:02d}.png"
        save_frame(fig, p)
        frame_paths.append(p)

    _write_gif(frame_paths, OUT_DIR / "rotate.gif", duration_ms=650)


def _make_two_qubit_meander_design():
    """Q1 fixed, Q2 movable, joined by a meandered CPW -- moving Q2 and
    rebuilding re-routes the meander to follow it. A meander (vs. a
    straight line) makes the re-route obviously dramatic rather than a
    subtle length change, and gives the route enough visual presence to
    carry the frame on its own."""
    design = designs.DesignPlanar()
    design._chips["main"]["size"]["size_x"] = "8mm"
    design._chips["main"]["size"]["size_y"] = "8mm"

    TransmonPocket(
        design,
        "Q1",
        options=dict(
            pos_x="-1.7mm",
            pos_y="0mm",
            pad_width="350um",
            connection_pads=dict(a=dict(loc_W=+1, loc_H=0)),
        ),
    )
    TransmonPocket(
        design,
        "Q2",
        options=dict(
            pos_x="1.7mm",
            pos_y="0mm",
            pad_width="350um",
            connection_pads=dict(a=dict(loc_W=-1, loc_H=0)),
        ),
    )
    RouteMeander(
        design,
        "cpw1",
        options=dict(
            pin_inputs=dict(
                start_pin=dict(component="Q1", pin="a"),
                end_pin=dict(component="Q2", pin="a"),
            ),
            total_length="7mm",
            fillet="90um",
            lead=dict(start_straight="0.4mm", end_straight="0.4mm"),
            meander=dict(spacing="0.3mm", asymmetry="0um"),
        ),
    )
    design.rebuild()
    return design


# (dx, dy, rebuild-kind, caption, key) -- rebuild-kind is "component" (only
# Q2's own geometry updates, matching a real arrow-key nudge: the route is
# NOT touched) or "full" (design.rebuild(), matching R: every route
# re-routes). This is what actually produces the lag-then-snap effect
# instead of asserting it in a caption while secretly always rebuilding
# everything.
REBUILD_STEPS = [
    (0, 0, "full", "Q2 selected — CPW connects Q1 ↔ Q2", None),
    (
        0,
        -NUDGE_COARSE_MM,
        "component",
        "arrow key → moves it (route lags)",
        "downarrow",
    ),
    (0, -2 * NUDGE_COARSE_MM, "component", "arrow key → moves it again", "downarrow"),
    (
        0,
        -2 * NUDGE_COARSE_MM,
        "full",
        "R → rebuild() — CPW re-routes, selection stays",
        "r",
    ),
    (
        0,
        -3 * NUDGE_COARSE_MM,
        "component",
        "arrow key → still moving it, no re-click",
        "downarrow",
    ),
    (0, 0, "full", "back to start", None),
]


def _run_rebuild_steps(design):
    """Replay REBUILD_STEPS on ``design``, yielding (caption, key) after
    each step's rebuild is applied -- shared by the bounds pre-walk and the
    actual render pass so both see identical geometry."""
    name = "Q2"
    base_x = float(design.components[name].options.pos_x[:-2])
    base_y = float(design.components[name].options.pos_y[:-2])
    for dx, dy, rebuild_kind, caption, key in REBUILD_STEPS:
        design.components[name].options.pos_x = f"{base_x + dx}mm"
        design.components[name].options.pos_y = f"{base_y + dy}mm"
        if rebuild_kind == "component":
            design.components[name].rebuild()
        else:
            design.rebuild()
        yield caption, key


def make_rebuild_gif(tmp_dir: Path):
    """Move Q2 (component-only rebuild -- the route lags, matching a real
    arrow-key nudge), then R (full rebuild -- the route snaps to follow,
    and the selection/highlight survives so the very next arrow key keeps
    moving Q2 with no re-click)."""
    # Pass 1: replay the sequence once just to collect the bounding box of
    # every component at every step (route included), so the frame never
    # re-centers or clips mid-sequence.
    bounds_design = _make_two_qubit_meander_design()
    xs, ys = [], []
    for _ in _run_rebuild_steps(bounds_design):
        for comp in bounds_design.components.values():
            b = comp.qgeometry_bounds()
            xs += [b[0], b[2]]
            ys += [b[1], b[3]]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 * 1.15
    xlim, ylim = (cx - half, cx + half), (cy - half, cy + half)

    # Pass 2: replay again on a fresh design, this time actually rendering.
    design = _make_two_qubit_meander_design()
    frame_paths = []
    for i, (caption, key) in enumerate(_run_rebuild_steps(design)):
        fig = render_frame(design, "Q2", caption, xlim, ylim, key=key)
        p = tmp_dir / f"rebuild_{i:02d}.png"
        save_frame(fig, p)
        frame_paths.append(p)

    # Hold on the "R rebuild()" frame (index 3) a little longer so it reads
    # as a distinct beat rather than flashing past.
    _write_gif(frame_paths, OUT_DIR / "rebuild.gif", hold_frames={3})


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        make_move_gif(tmp_dir)
        print(f"wrote {(OUT_DIR / 'move.gif').relative_to(REPO)}")
        make_rotate_gif(tmp_dir)
        print(f"wrote {(OUT_DIR / 'rotate.gif').relative_to(REPO)}")
        make_rebuild_gif(tmp_dir)
        print(f"wrote {(OUT_DIR / 'rebuild.gif').relative_to(REPO)}")


if __name__ == "__main__":
    sys.exit(main())
