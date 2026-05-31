"""Auto-generate library-pane thumbnails for every QComponent class.

The MetalGUI Library pane scans each ``qlibrary/**/*.py`` source file for
a ``.. image:: <filename>`` directive in the top class' docstring, then
loads ``src/qiskit_metal/_gui/_imgs/components/<filename>`` as the
thumbnail. Components without either the directive *or* the file fall
back to the generic Qiskit Metal globe placeholder.

This script renders a 256x256 PNG of each component instantiated with
either:

  1. Its default options (``ComponentClass(design, "X")``) — the
     happy path; most qubits and lumped elements work this way.

  2. A hand-tuned recipe in ``SPECIAL_RECIPES`` for components that
     need pins, ports, or specific options to render meaningfully
     (Routes need two pins to wire between; couplers may need
     connection_pads; etc.). Add a new entry here whenever you ship
     a component that the default-instantiation path can't render.

Writes the PNG to ``src/qiskit_metal/_gui/_imgs/components/<ClassName>.png``
and (optionally) inserts a ``.. image:: <ClassName>.png`` directive at
the top of the class docstring if one is missing.

USAGE
-----

  # dry-run — list what would happen, render nothing
  uv run python _dev/generate_qlibrary_thumbnails.py

  # render and write PNGs (no docstring edits)
  uv run python _dev/generate_qlibrary_thumbnails.py --write

  # also insert ``.. image::`` directives into docstrings that lack one
  uv run python _dev/generate_qlibrary_thumbnails.py --write --inject-docstrings

NOTES FOR FUTURE AGENTS
-----------------------

  - If a component fails with "needs pins" or similar, add it to
    ``SPECIAL_RECIPES`` below. The recipe is a callable that takes a
    ``DesignPlanar`` and returns the component instance you want to
    render; pin setup happens inside.
  - Renders use the headless ``qm.view(design)`` path, so this runs
    under ``QISKIT_METAL_HEADLESS=1`` without Qt.
  - Generated PNGs are deliberately checked in — the GUI loads them at
    import time and we want the experience to work offline.
  - For components with strong existing screenshots (transmon_pocket,
    transmon_cross, etc.), the script SKIPS regeneration unless
    ``--force`` is passed. We don't want auto-renders to overwrite
    higher-quality hand-curated images.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import os
import sys
from pathlib import Path

os.environ.setdefault("QISKIT_METAL_HEADLESS", "1")
os.environ.setdefault("QISKIT_METAL_HEADLESS_QUIET", "1")

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
sys.path.insert(0, str(SRC))

IMG_DIR = SRC / "qiskit_metal" / "_gui" / "_imgs" / "components"
QLIB = SRC / "qiskit_metal" / "qlibrary"

# Components we deliberately don't auto-render. Template / scaffold
# classes that aren't real library entries, plus user_components/
# (intended as user-editable scratch files, not catalog items).
SKIP_NAMES = {"MyQComponent", "BridgeFreeJunction"}
SKIP_DIRS = {"core", "user_components"}


def _two_launchpad_design(LaunchpadCls):
    """Build a small design with two launchpads facing each other so a
    Route component has something to terminate against."""
    from qiskit_metal.designs import DesignPlanar

    design = DesignPlanar()
    design.overwrite_enabled = True
    p1 = LaunchpadCls(design, "P1", options=dict(pos_x="-1.5mm", pos_y="0mm"))
    p2 = LaunchpadCls(
        design, "P2", options=dict(pos_x="+1.5mm", pos_y="0mm", orientation="180")
    )
    return design, p1, p2


def _route_recipe(RouteCls):
    """Build a one-route demo design between two launchpads."""

    def recipe(_design_unused=None):
        from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond

        design, p1, p2 = _two_launchpad_design(LaunchpadWirebond)
        comp = RouteCls(
            design,
            "R1",
            options=dict(
                pin_inputs=dict(
                    start_pin=dict(component="P1", pin="tie"),
                    end_pin=dict(component="P2", pin="tie"),
                ),
                fillet="90um",
            ),
        )
        return design, comp

    return recipe


def _coupler_with_pads_recipe(ComponentCls, opts=None):
    """Build a design with the component and a coupling pad for context."""

    def recipe(_design_unused=None):
        from qiskit_metal.designs import DesignPlanar

        design = DesignPlanar()
        design.overwrite_enabled = True
        comp = ComponentCls(design, "X1", options=opts or {})
        return design, comp

    return recipe


# Hand-tuned per-component recipes for things that can't render with
# bare defaults. Each value is a callable(unused) -> (design, component).
# Add to this when a new component lands and the default-instantiation
# path doesn't produce a meaningful render.
SPECIAL_RECIPES = {}


def _anchored_route_recipe(RouteCls):
    """Recipe for routes that require an explicit ``anchors`` dict."""

    def recipe(_design_unused=None):
        import numpy as np

        from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond

        design, p1, p2 = _two_launchpad_design(LaunchpadWirebond)
        comp = RouteCls(
            design,
            "R1",
            options=dict(
                pin_inputs=dict(
                    start_pin=dict(component="P1", pin="tie"),
                    end_pin=dict(component="P2", pin="tie"),
                ),
                anchors={0: np.array([0.0, 0.6])},
                fillet="90um",
            ),
        )
        return design, comp

    return recipe


def _populate_special_recipes():
    """Populate ``SPECIAL_RECIPES`` lazily so we can ``import`` the
    qlibrary modules safely (some have heavy imports)."""
    try:
        from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
        from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder
        from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
        from qiskit_metal.qlibrary.tlines.mixed_path import RouteMixed
        from qiskit_metal.qlibrary.tlines.framed_path import RouteFramed
        from qiskit_metal.qlibrary.tlines.anchored_path import RouteAnchors

        for cls in (RouteMeander, RoutePathfinder, RouteStraight, RouteFramed):
            SPECIAL_RECIPES[cls.__name__] = _route_recipe(cls)
        # RouteAnchors / RouteMixed need an explicit anchors dict.
        SPECIAL_RECIPES["RouteAnchors"] = _anchored_route_recipe(RouteAnchors)
        SPECIAL_RECIPES["RouteMixed"] = _anchored_route_recipe(RouteMixed)
    except ImportError as exc:
        print(f"  ! could not register route recipes: {exc}")


def _iter_component_classes():
    """Yield ``(file_path, class_obj)`` for every QComponent subclass in
    ``qlibrary/`` excluding skip dirs/names."""
    from qiskit_metal.qlibrary.core import QComponent

    for py in QLIB.rglob("*.py"):
        if py.name.startswith("_"):
            continue
        if any(part in SKIP_DIRS for part in py.parts):
            continue
        rel = py.relative_to(SRC).with_suffix("")
        modname = ".".join(rel.parts)
        try:
            mod = importlib.import_module(modname)
        except Exception as exc:
            print(f"  ! skip {modname}: import failed ({exc})")
            continue
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if obj.__module__ != mod.__name__:
                continue
            if not issubclass(obj, QComponent) or obj is QComponent:
                continue
            if name in SKIP_NAMES:
                continue
            yield py, obj


def _build_design_for(cls):
    """Return (design, component) for ``cls`` using a recipe if present,
    otherwise default instantiation in a planar design."""
    if cls.__name__ in SPECIAL_RECIPES:
        return SPECIAL_RECIPES[cls.__name__](None)
    from qiskit_metal.designs import DesignPlanar

    design = DesignPlanar()
    design.overwrite_enabled = True
    comp = cls(design, "X1")
    return design, comp


def _render_to_png(design, out_path, size_px=256):
    """Render ``design`` via ``qm.view`` and write a square PNG."""
    import matplotlib.pyplot as plt
    import qiskit_metal as qm

    fig = qm.view(design)
    if fig is None:
        return False
    # Square, tight crop, no axes — pure thumbnail.
    ax = fig.axes[0]
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.set_size_inches(4, 4)
    fig.savefig(
        out_path,
        dpi=size_px // 4,
        bbox_inches="tight",
        pad_inches=0.05,
        facecolor="white",
    )
    plt.close(fig)
    return True


_IMG_DIRECTIVE_RE = ".. image::"


def _inject_image_directive(source_file, class_name, img_filename):
    """Insert ``.. image:: <img_filename>`` into the class docstring."""
    import ast
    import re

    src = source_file.read_text()
    tree = ast.parse(src)
    target = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            target = node
            break
    if target is None or not target.body:
        return False
    first = target.body[0]
    if not (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return False
    docstring = first.value.value
    if _IMG_DIRECTIVE_RE in docstring:
        return False
    # IMPORTANT: the MetalGUI library-pane scanner uses the regex
    # ``\.\. image::[\r\n]+([^\r\n]+)`` (see file_model_qlibrary.py),
    # which requires the filename on a separate line from the directive
    # marker. ``.. image:: foo.png`` on one line *parses* in Sphinx but
    # is invisible to the GUI scanner. Always emit two lines.
    new_doc = f".. image::\n    {img_filename}\n\n" + docstring
    # Find the actual source span of the docstring literal and replace
    # in-place to preserve everything else (quoting, indentation).
    lineno = first.value.lineno - 1
    end_lineno = first.value.end_lineno - 1
    lines = src.splitlines(keepends=True)
    block = "".join(lines[lineno : end_lineno + 1])
    # Replace the docstring literal content via a regex-aware swap.
    pattern = re.escape(docstring)
    new_block = re.sub(pattern, lambda _: new_doc, block, count=1)
    if new_block == block:
        return False
    new_src = "".join(lines[:lineno]) + new_block + "".join(lines[end_lineno + 1 :])
    source_file.write_text(new_src)
    return True


def verify_image_references():
    """Walk every ``.. image::`` directive in ``qlibrary/`` and report:

    1. Broken refs — file doesn't exist (case-sensitive; macOS's
       case-insensitive FS masks these locally).
    2. One-line directives — ``.. image:: foo.png`` parses in Sphinx
       but is *invisible* to the MetalGUI scanner regex
       ``\\.\\. image::[\\r\\n]+([^\\r\\n]+)``. Must be two lines.
    3. Components with a matching PNG on disk but no directive at all
       (the GUI then falls back to the globe placeholder).

    Returns a dict of issue lists. Empty lists everywhere = healthy.
    """
    import re

    actual = {p.name for p in IMG_DIR.iterdir() if p.suffix.lower() in (".png", ".jpg")}
    actual_lower = {p.lower(): p for p in actual}
    issues = {"broken_refs": [], "one_line_directives": [], "orphan_pngs": []}

    # Two-line directive (what the GUI actually accepts)
    two_line = re.compile(r"\.\. image::[\r\n]+\s*(\S+)")
    # One-line directive (what Sphinx accepts but the GUI doesn't)
    one_line = re.compile(r"\.\. image::[ \t]+(\S+)")

    # Walk everything as text, plus AST-walk for "PNG exists but no directive"
    import ast

    for py in QLIB.rglob("*.py"):
        if any(part in SKIP_DIRS for part in py.parts):
            continue
        text = py.read_text()
        rel = py.relative_to(REPO)
        # Broken refs (either format)
        for ref in two_line.findall(text) + [
            m for m in one_line.findall(text) if m.endswith((".png", ".jpg"))
        ]:
            if ref not in actual:
                suggestion = actual_lower.get(ref.lower(), "(not found)")
                issues["broken_refs"].append((rel, ref, suggestion))
        # One-line directives that point at real PNGs (GUI can't see them)
        for ref in one_line.findall(text):
            if not ref.endswith((".png", ".jpg")):
                continue
            # If a two-line directive at the same position also matched, skip
            if ref in two_line.findall(text):
                continue
            issues["one_line_directives"].append((rel, ref))
        # Orphan PNGs: class has matching PNG on disk but no directive
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name in SKIP_NAMES:
                continue
            ds = ast.get_docstring(node) or ""
            if "image::" in ds:
                continue
            png = f"{node.name}.png"
            if png in actual:
                issues["orphan_pngs"].append((rel, node.name, png))

    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", action="store_true", help="actually write the PNG files"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help=(
            "only check that every docstring ``.. image::`` reference "
            "resolves to an existing file under _imgs/components/ "
            "(case-sensitive — catches Linux-CI breakage)"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing PNGs (default: skip if present)",
    )
    parser.add_argument(
        "--inject-docstrings",
        action="store_true",
        help="insert ``.. image::`` into docstrings missing one",
    )
    args = parser.parse_args()

    if args.verify:
        issues = verify_image_references()
        total = sum(len(v) for v in issues.values())
        if not total:
            print("All ``.. image::`` directives in qlibrary/ resolve cleanly.")
            return
        if issues["broken_refs"]:
            print("Broken image references (file not found, case-sensitive):")
            for py, ref, sug in issues["broken_refs"]:
                print(f"  {py}: {ref!r}  → did you mean {sug!r}?")
        if issues["one_line_directives"]:
            print(
                "\nOne-line ``.. image:: foo.png`` — invisible to MetalGUI "
                "scanner. Must split across two lines:"
            )
            for py, ref in issues["one_line_directives"]:
                print(f"  {py}: {ref!r}")
        if issues["orphan_pngs"]:
            print(
                "\nPNG exists but class has no ``.. image::`` directive "
                "(GUI shows placeholder):"
            )
            for py, cls, png in issues["orphan_pngs"]:
                print(f"  {py}: class {cls} -> {png}")
        sys.exit(1)

    _populate_special_recipes()

    rendered, skipped, failed, injected = [], [], [], []
    for src_file, cls in sorted(_iter_component_classes(), key=lambda x: x[1].__name__):
        name = cls.__name__
        out = IMG_DIR / f"{name}.png"
        if out.exists() and not args.force:
            skipped.append(name)
            tag = "exists"
        else:
            tag = "render"
            try:
                design, _comp = _build_design_for(cls)
                ok = False
                if args.write:
                    ok = _render_to_png(design, out)
                else:
                    # Dry-run: try building the design to surface errors,
                    # but don't save.
                    ok = True
                if ok:
                    rendered.append(name)
                else:
                    failed.append((name, "render returned False"))
            except Exception as exc:
                failed.append((name, f"{type(exc).__name__}: {exc}"))
                tag = "fail"

        if args.inject_docstrings and args.write:
            try:
                if _inject_image_directive(src_file, name, f"{name}.png"):
                    injected.append(name)
            except Exception as exc:
                print(f"  ! docstring injection failed for {name}: {exc}")

        print(f"  [{tag:6s}] {name}")

    print()
    print(f"Rendered: {len(rendered)}")
    print(f"Skipped (already exist): {len(skipped)}")
    print(f"Docstring directives injected: {len(injected)}")
    print(f"Failed: {len(failed)}")
    if failed:
        print()
        print("FAILURES — add a recipe to SPECIAL_RECIPES:")
        for name, err in failed:
            print(f"  - {name}: {err}")


if __name__ == "__main__":
    main()
