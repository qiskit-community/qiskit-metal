# /// script
# requires-python = ">=3.10"
# ///
"""Generate the v0.8.1 interactive-canvas hero GIF: click-select, arrow-move,
rotate, rebuild (selection survives, CPW re-routes), fit-view, and a closing
flash of the shortcuts help dialog.

Unlike ``_dev/generate_gui_shortcut_gifs.py`` (headless ``qm.view()`` frames
with a hand-drawn highlight box, for the docs page), this drives a REAL
``MetalGUI`` through genuine ``QTest``-injected mouse/keyboard events and
grabs the actual widget -- ``gui.plot_win`` (the canvas + its own toolbar,
nothing else: no docks, no window chrome, no file paths) -- so what's in
the GIF is pixel-for-pixel what a user's screen shows.

Local-only: writes to the path given on the command line (default: the
system temporary folder). Does NOT touch docs/, assets/, or any publishing
pipeline -- nothing here uploads or posts anything.

Run from the repo root (needs a Qt platform plugin; offscreen is fine and
is what makes this reproducible without a real display):
    QT_QPA_PLATFORM=offscreen uv run --with pillow python \\
        _dev/generate_hero_canvas_gif.py [output_path.gif]
"""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QISKIT_METAL_HEADLESS", "0")
os.environ.setdefault("QISKIT_METAL_GUI_NO_ACTIVATE", "1")

from PIL import Image
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

REPO = Path(__file__).resolve().parent.parent
# Outside the repo tree on purpose: "keep all work local" means this file
# shouldn't even be a candidate for `git add -A` to sweep up by accident.
# Pass a different path on the command line to save elsewhere.
DEFAULT_OUT = Path(tempfile.gettempdir()) / "hero-canvas-081.gif"

# Per-frame durations, ms -- most steps quick and punchy; the rebuild beat
# and the closing help-dialog flash linger so they read as distinct beats
# rather than flashing past. Keeps total loop length in the 8-12s
# target without needing a large frame count (see the docstring above for
# why this repo favors discrete keyframes over literal 12-15fps capture).
DUR_QUICK = 350
DUR_NORMAL = 550
DUR_REBUILD_HOLD = 1400
DUR_HELP_HOLD = 1300


def _pump(app, n=20):
    for _ in range(n):
        app.processEvents()


def _click_canvas_at_data_coords(gui, app, x_mm, y_mm):
    """A real QTest click at the screen position corresponding to a data
    coordinate, DPI-corrected (see tests/test_gui_nudge.py for why: mpl
    transforms are physical pixels, Qt wants logical)."""
    canvas = gui.canvas
    ax = canvas.figure.axes[0]
    disp_x, disp_y = ax.transData.transform((x_mm, y_mm))
    dpr = canvas.devicePixelRatioF()
    pos = QPoint(int(disp_x / dpr), int((canvas.figure.bbox.height - disp_y) / dpr))
    for _attempt in range(4):
        QTest.mousePress(canvas, Qt.LeftButton, Qt.NoModifier, pos)
        _pump(app, 10)
        QTest.mouseRelease(canvas, Qt.LeftButton, Qt.NoModifier, pos)
        _pump(app, 20)
        if gui.selected_component is not None:
            return
        QTest.qWait(150)


def _grab(gui, frame_paths, tmp_dir, tag):
    """Grab exactly canvas + its own toolbar -- gui.plot_win -- crops out
    every other dock, the window title bar, and any file path."""
    pix = gui.plot_win.grab()
    p = tmp_dir / f"frame_{len(frame_paths):02d}_{tag}.png"
    pix.save(str(p))
    frame_paths.append(p)
    return p


def _build_design():
    """Two transmons joined by a CPW -- minimal on purpose, and it's what
    makes the rebuild step worth showing (the route re-routes, not just a
    static redraw)."""
    from qiskit_metal import designs
    from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
    from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight

    design = designs.DesignPlanar()
    design._chips["main"]["size"]["size_x"] = "6mm"
    design._chips["main"]["size"]["size_y"] = "6mm"
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
    RouteStraight(
        design,
        "cpw1",
        options=dict(
            pin_inputs=dict(
                start_pin=dict(component="Q1", pin="a"),
                end_pin=dict(component="Q2", pin="a"),
            ),
            fillet="90um",
        ),
    )
    return design


def _write_gif(frame_paths, durations, out_path):
    frames = [Image.open(p).convert("P", palette=Image.ADAPTIVE) for p in frame_paths]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    reloaded = Image.open(out_path)
    n = 0
    try:
        while True:
            reloaded.seek(n)
            n += 1
    except EOFError:
        pass
    if n != len(frames):
        raise RuntimeError(
            f"wrote {len(frames)} frames but the GIF contains {n} -- two "
            "adjacent frames were pixel-identical and got coalesced. "
            "Check the step choreography for a duplicate."
        )
    size_kb = out_path.stat().st_size / 1024
    print(f"wrote {out_path} — {n} frames, {size_kb:.0f} KB")
    if size_kb > 8192:
        print(
            "WARNING: over ~8MB -- some platforms flatten large GIFs to "
            "their first frame on upload. Consider fewer/smaller frames "
            "before handing this off."
        )


def main(out_path: Path):
    import tempfile

    app = QApplication.instance() or QApplication(sys.argv)

    from qiskit_metal._gui.main_window import MetalGUI

    design = _build_design()
    gui = MetalGUI(design)
    try:
        gui.main_window.show()
        _pump(app, 20)
        gui.rebuild()
        gui.autoscale()
        _pump(app, 20)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            frame_paths = []
            durations = []

            def step(tag, dur):
                _grab(gui, frame_paths, tmp_dir, tag)
                durations.append(dur)

            # 1. Click Q2 to select it.
            _click_canvas_at_data_coords(gui, app, 1.7, 0.0)
            step("selected", DUR_NORMAL)

            # 2. Arrow keys nudge it a few times -- visibly moving.
            canvas = gui.canvas
            for i in range(3):
                QTest.keyClick(app.focusWidget() or canvas, Qt.Key_Down)
                _pump(app, 20)
                step(f"move{i}", DUR_QUICK)

            # 3. Rotate 90 degrees, twice, so it reads clearly.
            for i in range(2):
                QTest.keyClick(app.focusWidget() or canvas, Qt.Key_Q)
                _pump(app, 20)
                step(f"rotate{i}", DUR_NORMAL)

            # 4. Rebuild -- hold so the CPW re-route + surviving selection
            #    is legible, not a flash.
            QTest.keyClick(app.focusWidget() or canvas, Qt.Key_R)
            _pump(app, 30)
            step("rebuild", DUR_REBUILD_HOLD)

            # 5. One more nudge with NO re-click, proving the selection
            #    really did survive the rebuild.
            QTest.keyClick(app.focusWidget() or canvas, Qt.Key_Down)
            _pump(app, 20)
            step("move_after_rebuild", DUR_NORMAL)

            # 6. Fit view -- quick, just to show it's instant.
            QTest.keyClick(app.focusWidget() or canvas, Qt.Key_A)
            _pump(app, 20)
            step("fit_view", DUR_QUICK)

            # 7. Closing beat: flash the shortcuts help dialog (answers
            #    "where do I find these"), then close it.
            QTest.keyClick(app.focusWidget() or canvas, Qt.Key_Question)
            _pump(app, 30)
            dialog = getattr(gui.plot_win, "_help_dialog", None)
            if dialog is not None and dialog.isVisible():
                pix = dialog.grab()
                p = tmp_dir / f"frame_{len(frame_paths):02d}_help.png"
                pix.save(str(p))
                frame_paths.append(p)
                durations.append(DUR_HELP_HOLD)
                dialog.close()
                _pump(app, 10)
            else:
                print("NOTE: help dialog did not open; skipping that beat.")

            _write_gif(frame_paths, durations, out_path)
    finally:
        gui.main_window.force_close = True
        gui.main_window.close()


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    sys.exit(main(out))
