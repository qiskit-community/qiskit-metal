"""Generate labeled placeholder icons for the non-catalog QComponent
scaffolds (``core/``, ``user_components/``, ``_template.py``).

These files appear in the MetalGUI Library pane as part of the file
walk, but they aren't real catalog components — they're base classes
(``QComponent``, ``BaseQubit``, ``QRoute``) and user-editable
templates. Without an icon they show the generic Quantum Metal globe,
which the user mistakes for an unbuilt thumbnail.

This script renders a small labeled icon for each scaffold so the
Library pane visually signals "this isn't a clickable component" at a
glance, and inserts the ``.. image::`` directive into each class
docstring (two-line form so the GUI scanner sees it).

USAGE
-----

  uv run python _dev/generate_scaffold_icons.py --write

Idempotent: re-running with ``--write`` overwrites the PNGs (the
generator is the source of truth) but skips docstring injection if a
directive already exists.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

os.environ.setdefault("QISKIT_METAL_HEADLESS", "1")
os.environ.setdefault("QISKIT_METAL_HEADLESS_QUIET", "1")

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "qiskit_metal"
IMG_DIR = SRC / "_gui" / "_imgs" / "components"
LOGO = SRC / "_gui" / "_imgs" / "metal_logo.png"

# (source-file path, class names in that file, icon kind, label, bg colour)
SCAFFOLDS = [
    # core/ — base / abstract classes
    (
        "qlibrary/core/base.py",
        ["QComponent"],
        "base_qcomponent.png",
        "QComponent",
        "Base class",
        "#3D5A80",
    ),
    (
        "qlibrary/core/qubit.py",
        ["BaseQubit"],
        "base_qubit.png",
        "BaseQubit",
        "Base qubit class",
        "#3D5A80",
    ),
    (
        "qlibrary/core/qroute.py",
        ["QRoute", "QRoutePoint", "QRouteLead"],
        "base_qroute.png",
        "QRoute",
        "Base route classes",
        "#3D5A80",
    ),
    (
        "qlibrary/core/design_check.py",
        ["QDesignCheck"],
        "base_design_check.png",
        "QDesignCheck",
        "Design-check helper",
        "#3D5A80",
    ),
    (
        "qlibrary/core/_parsed_dynamic_attrs.py",
        ["ParsedDynamicAttributes_Component"],
        "internal_parsed_attrs.png",
        "Parsed Attrs",
        "Internal helper",
        "#6c757d",
    ),
    # Templates / user_components — meant to be copied + edited
    (
        "qlibrary/_template.py",
        ["MyQComponent"],
        "user_template.png",
        "MyQComponent",
        "Template — copy & edit",
        "#E07A5F",
    ),
    (
        "qlibrary/user_components/my_qcomponent.py",
        ["MyQComponent"],
        "user_template.png",
        "MyQComponent",
        "User template",
        "#E07A5F",
    ),
    (
        "qlibrary/user_components/BridgeFreeJJ.py",
        ["BridgeFreeJunction"],
        "user_bridgefreejj.png",
        "BridgeFreeJunction",
        "User component",
        "#E07A5F",
    ),
]


def _render_icon(path: Path, title: str, subtitle: str, bg: str) -> None:
    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4, 4), dpi=64)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Faint Qiskit Metal logo as the background mark.
    if LOGO.exists():
        try:
            img = mpimg.imread(str(LOGO))
            ax.imshow(
                img,
                extent=(0.25, 0.75, 0.45, 0.95),
                alpha=0.15,
                zorder=1,
            )
        except Exception:
            pass

    # Title (component name) + subtitle (what kind of scaffold).
    ax.text(
        0.5,
        0.30,
        title,
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="white",
        zorder=2,
    )
    ax.text(
        0.5,
        0.18,
        subtitle,
        ha="center",
        va="center",
        fontsize=10,
        color="white",
        alpha=0.85,
        zorder=2,
    )

    fig.savefig(
        path,
        facecolor=bg,
        bbox_inches="tight",
        pad_inches=0.0,
    )
    plt.close(fig)


def _inject_directive(source_file: Path, class_name: str, img_filename: str) -> bool:
    """Two-line ``.. image::`` directive at top of class docstring."""
    import ast

    src = source_file.read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    target = None
    for node in ast.walk(tree):
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
    ds = first.value.value
    if ".. image::" in ds:
        return False
    new_ds = f".. image::\n    {img_filename}\n\n" + ds
    lineno = first.value.lineno - 1
    end_lineno = first.value.end_lineno - 1
    lines = src.splitlines(keepends=True)
    block = "".join(lines[lineno : end_lineno + 1])
    new_block = re.sub(re.escape(ds), lambda _: new_ds, block, count=1)
    if new_block == block:
        return False
    new_src = "".join(lines[:lineno]) + new_block + "".join(lines[end_lineno + 1 :])
    source_file.write_text(new_src)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    icons_rendered = set()
    docstrings_injected = 0
    for src_rel, classes, icon_name, title, subtitle, bg in SCAFFOLDS:
        src_path = SRC / src_rel
        if not src_path.exists():
            print(f"  ! missing {src_rel}; skipped")
            continue
        if icon_name not in icons_rendered:
            target = IMG_DIR / icon_name
            print(f"  [render] {icon_name}")
            if args.write:
                _render_icon(target, title, subtitle, bg)
            icons_rendered.add(icon_name)
        for cls in classes:
            tag = "[skip ]"
            if args.write and _inject_directive(src_path, cls, icon_name):
                tag = "[inject]"
                docstrings_injected += 1
            print(f"     {tag} {src_rel}::{cls}")
    print()
    print(f"Icons rendered: {len(icons_rendered)}")
    print(f"Docstrings injected: {docstrings_injected}")


if __name__ == "__main__":
    main()
