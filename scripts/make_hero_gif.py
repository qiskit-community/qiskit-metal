# /// script
# requires-python = ">=3.10"
# ///
"""Generate the hero animated GIF for the README.

Builds a 4-qubit ring chip progressively (canvas → qubits → CPW routes →
readout stubs → launchpads → final view) and stitches each stage into a
looping GIF, with a closing frame showing the same chip's Gmsh FEM surface
mesh. Showcases the design-as-code workflow and the open-source meshing
path in a glance.

The design frames use the same ``qm.view(design)`` API end users would run,
so the GIF stays honest — what viewers see is exactly what they'd get
by pasting the equivalent ~20 lines into a notebook.

Output: docs/_static/hero.gif (~500KB at 800×600)

Run from the repo root:
    uv run --with pillow scripts/make_hero_gif.py

The closing mesh frame requires the optional ``gmsh`` dependency
([mesh] extra). Without it, the GIF is generated the same way minus that
one frame:
    uv run --extra mesh --with pillow scripts/make_hero_gif.py
"""

import os
import sys
import tempfile
from pathlib import Path

# Silence the v0.8 rename warning chatter (doesn't affect rendering)
os.environ.setdefault("QISKIT_METAL_SUPPRESS_RENAME_WARNING", "1")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from PIL import Image

import qiskit_metal as qm
from qiskit_metal import Dict, designs
from qiskit_metal.qlibrary.qubits.transmon_cross import TransmonCross
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
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

# Each qubit has exactly one connection pad left unused by the ring +
# launchpad wiring (see RING_CPWS / LAUNCHPADS below) — that free pin gets
# a short open-stub readout resonator, purely for visual density (mimics
# the individual-readout topology in "Reference design 1").
FREE_PIN = {"Q1": "c", "Q2": "d", "Q3": "a", "Q4": "b"}

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


def _add_readout_stubs(design):
    """Add one open-stub readout resonator per qubit, on its free pin.

    Placement is read from the LIVE pin geometry (``middle`` + ``normal``)
    rather than a hardcoded angle — ``TransmonPocket``'s ``loc_W``/``loc_H``
    are scale factors, not simple side-selectors, so a per-qubit hand-picked
    angle would silently be wrong for some corners. Reading the actual pin
    normal keeps this correct regardless of chip layout.
    """
    otg_offset_mm = 1.0  # distance from the qubit pin to the open termination
    for qubit_name, pin_name in FREE_PIN.items():
        pin = design.components[qubit_name].pins[pin_name]
        middle = np.asarray(pin["middle"], dtype=float)
        normal = np.asarray(pin["normal"], dtype=float)
        angle_deg = np.degrees(np.arctan2(normal[1], normal[0]))
        otg_pos = middle + normal * otg_offset_mm

        otg_name = f"ro_open_{qubit_name}"
        OpenToGround(
            design,
            otg_name,
            options=Dict(
                pos_x=f"{otg_pos[0]}mm",
                pos_y=f"{otg_pos[1]}mm",
                orientation=f"{angle_deg}",
            ),
        )
        RouteMeander(
            design,
            f"ro_{qubit_name}",
            options=Dict(
                pin_inputs=Dict(
                    start_pin=Dict(component=qubit_name, pin=pin_name),
                    end_pin=Dict(component=otg_name, pin="open"),
                ),
                # Lead length must clear the fillet radius (see the feed_opts
                # comment above and #1086) — otherwise the Gmsh path-offset
                # renderer can't build the corner arc ("Could not create line").
                lead=Dict(start_straight="80um", end_straight="80um"),
                fillet="40 um",
                total_length="1.5mm",
                trace_width="10 um",
                trace_gap="6 um",
                meander=Dict(spacing="450um", asymmetry="0um"),
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


def _add_launchpads_and_connections(design):
    """All 4 launchpads + their connecting CPWs in one shot (last build frame)."""
    # Use RoutePathfinder (straight + fillet) rather than RouteMeander —
    # the launchpad-to-qubit feeds are short and don't need wiggle. This
    # also removes the spurious meander-segment kinks at corners.
    feed_opts = Dict(
        # Lead length must clear the fillet radius, same constraint as
        # RouteMeander's length_perp vs fillet fix (#1086) — a lead shorter
        # than the fillet leaves too little straight run for the corner
        # arc, which the Gmsh path-offset renderer can't handle ("Could not
        # create line").
        lead=Dict(start_straight="100um", end_straight="100um"),
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
    _add_readout_stubs(design)
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
    # Individual readout resonators (open stubs) on each qubit's free pin.
    stages.append(
        (
            _add_readout_stubs,
            "09_readout_stubs.png",
            "Step 4 — Individual readout resonators",
            600,
        )
    )
    # Launchpads + their connecting CPWs in one shot
    stages.append(
        (
            _add_launchpads_and_connections,
            "10_launchpads.png",
            "Step 5 — Launchpads + feed lines",
            600,
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
        )
    )
    # Final long hold so viewers register the result
    stages.append(
        (None, "12_final.png", "qm.view(design)   →   chip ready for fab/sim", 1600)
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
    design._chips["main"]["size"]["size_x"] = "5 mm"
    design._chips["main"]["size"]["size_y"] = "5 mm"
    _populate_full_design(design)
    return design


def render_mesh_frame(xlim, ylim, title):
    """Mesh the final chip with Gmsh and render its 2-D surface mesh.

    Only the 2-D surface mesh is generated (``add_mesh(dim=2)``) — the full
    3-D tetrahedral volume mesh ``QGmshRenderer`` is built for (vacuum box
    included) takes tens of seconds even for a couple of qubits and isn't
    needed for a flat top-down illustration.

    Raises ImportError if gmsh isn't installed — the caller decides whether
    that's fatal (it isn't, for this script: the frame is just skipped).
    """
    from qiskit_metal.renderers.renderer_gmsh.gmsh_renderer import QGmshRenderer

    design = _build_mesh_design()
    gr = QGmshRenderer(design)
    gr.options.mesh.max_size = "150um"
    gr.options.mesh.min_size = "20um"
    gr.render_design(mesh_geoms=False)
    gr.add_mesh(dim=2, intelli_mesh=False)

    import gmsh

    triangles, colors = [], []
    for dim, tag in gmsh.model.getEntities(dim=2):
        color = gmsh.model.getColor(dim, tag)
        elem_types, _elem_tags, elem_node_tags = gmsh.model.mesh.getElements(
            dim=2, tag=tag
        )
        for etype, node_tags in zip(elem_types, elem_node_tags):
            if etype != 2:  # only 3-node triangles
                continue
            node_tags = np.asarray(node_tags).reshape(-1, 3)
            for tri in node_tags:
                coords = [gmsh.model.mesh.getNode(int(n))[0][:2] for n in tri]
                triangles.append(coords)
                if color and color[3] != 0:
                    colors.append(tuple(c / 255 for c in color[:3]) + (1.0,))
                else:
                    colors.append((0.6, 0.6, 0.65, 1.0))
    gr.close()

    fig, ax = plt.subplots(figsize=FIGSIZE_INCH, dpi=DPI)
    ax.add_collection(
        PolyCollection(
            triangles, facecolor=colors, edgecolor=(0, 0, 0, 0.15), linewidth=0.2
        )
    )
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.92, bottom=0.10)
    return fig


def main():
    storyboard = build_storyboard()
    durations = [d for *_, d in storyboard]
    with tempfile.TemporaryDirectory() as tmp:
        frame_paths = list(build_4qubit_chip_progressively(Path(tmp)))

        # Closing frame: the same chip's Gmsh FEM surface mesh. Optional —
        # gmsh is the [mesh] extra, not installed by default.
        final = _make_design()
        _populate_full_design(final)
        xlim, ylim = compute_centered_square_limits(final)
        try:
            mesh_fig = render_mesh_frame(
                xlim, ylim, "Under the hood — FEM surface mesh (open-source Gmsh)"
            )
        except ImportError:
            print(
                "  ⓘ gmsh not installed — skipping mesh frame "
                "(install with the [mesh] extra: uv run --extra mesh ...)"
            )
        else:
            mesh_path = Path(tmp) / "13_mesh.png"
            save_frame(mesh_fig, mesh_path)
            frame_paths.append(mesh_path)
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
