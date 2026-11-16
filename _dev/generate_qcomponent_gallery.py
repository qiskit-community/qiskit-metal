"""Generate the visual QComponent gallery page for the Sphinx docs.

Walks every ``QComponent`` subclass in ``qlibrary/``, groups by parent
folder (``qubits``, ``couplers``, ``tlines``, ``resonators``,
``terminations``, ``lumped``, ``sample_shapes``), copies the matching
thumbnail PNG from ``_gui/_imgs/components/`` into
``docs/images/qlibrary/``, and emits ``docs/qcomponents-gallery.rst``
— a grid of clickable cards (one per component) using
``sphinx-design``.

Each card → ``apidocs/qiskit_metal.qlibrary.<ClassName>.html`` (the
autosummary-generated API page) so users can click a component image
to read its API.

USAGE
-----

  # regenerate the gallery + copy the latest thumbnails
  uv run python _dev/generate_qcomponent_gallery.py --write

  # dry-run; print what would be emitted
  uv run python _dev/generate_qcomponent_gallery.py

The script is idempotent and safe to wire into a pre-build step or CI.
"""

from __future__ import annotations

import argparse
import ast
import functools
import importlib
import inspect
import os
import re
import shutil
import sys
from pathlib import Path

os.environ.setdefault("QISKIT_METAL_HEADLESS", "1")
os.environ.setdefault("QISKIT_METAL_HEADLESS_QUIET", "1")

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
sys.path.insert(0, str(SRC))

QLIB = SRC / "qiskit_metal" / "qlibrary"
IMG_SRC = SRC / "qiskit_metal" / "_gui" / "_imgs" / "components"
DOCS = REPO / "docs"
GALLERY_IMG = DOCS / "images" / "qlibrary"
GALLERY_RST = DOCS / "qcomponents-gallery.rst"
# Autodoc renders class docstrings into ``docs/_build/.doctrees/apidocs/``
# and resolves ``.. image:: foo.png`` relative to that path, which means
# the PNG must live at ``docs/apidocs/foo.png`` (it's added to source
# tree; Sphinx copies it to ``_images/`` at build time). Mirror every
# thumbnail there so autodoc's class pages don't trip "image file not
# readable" warnings.
APIDOCS_IMG = DOCS / "apidocs"

CATALOG_DIR = DOCS / "catalog"
THUMBS = REPO / "_dev" / "generate_qlibrary_thumbnails.py"
# Option keys consumed by renderers rather than by the component's geometry;
# shown in a collapsed block on each catalog page.
RENDERER_PREFIXES = ("gds_", "hfss_", "q3d_", "aedt_", "elmer_", "gmsh_")

SKIP_DIRS = {"core", "user_components"}
SKIP_NAMES = {"MyQComponent", "BridgeFreeJunction"}

CATEGORY_LABELS = {
    "qubits": "🧬 Qubits",
    "couplers": "🔗 Couplers",
    "tlines": "🌊 Transmission lines & routes",
    "resonators": "📡 Resonators",
    "terminations": "🔌 Terminations",
    "lumped": "⚡ Lumped elements",
    "sample_shapes": "🔺 Sample shapes",
}

# Class name -> notebooks that use it, as ``(docname, link text)``. Docnames
# are relative to ``docs/`` without the ``.ipynb`` suffix. Each card gets an
# "Example" link per entry; ``_check_example_docnames`` fails the run when a
# docname does not exist.
EXAMPLES = {
    "TransmonCross": [("circuit-examples/A.Qubits/01-Transmon_cross", "Example")],
    "TransmonPocket": [("circuit-examples/A.Qubits/02-Transmon_floating", "Example")],
    "TransmonConcentric": [
        ("circuit-examples/A.Qubits/03-concentric_transmon", "Example")
    ],
    "TransmonInterdigitated": [
        ("circuit-examples/A.Qubits/04-Interdigitated_Transmon", "Example"),
        ("tut/quick-topics/QComponent-Interdigitated-transmon", "Tutorial"),
    ],
    "TransmonCrossFL": [("circuit-examples/A.Qubits/05-Transmon_cross_fl", "Example")],
    "TransmonPocket6": [
        ("circuit-examples/A.Qubits/06-Transmon_floating_6", "Example")
    ],
    "TransmonPocketCL": [
        ("circuit-examples/E.Input-output-coupling/43-TransmonPocketCL", "Example")
    ],
    "jj_dolan": [
        ("circuit-examples/A.Qubits/08-JJ-Dolan", "Example"),
        ("tut/quick-topics/JJ-Demo-Notebook", "Tutorial"),
    ],
    "jj_manhattan": [
        ("circuit-examples/A.Qubits/09-JJ-Manhattan", "Example"),
        ("tut/quick-topics/JJ-Demo-Notebook", "Tutorial"),
    ],
    "TransmonPocketTeeth": [
        ("circuit-examples/A.Qubits/10-Transmon_floating_teeth", "Example")
    ],
    "StarQubit": [("circuit-examples/A.Qubits/11-Star_shaped_qubit", "Example")],
    "RouteMeander": [("circuit-examples/B.Resonators/11-Resonator_Meander", "Example")],
    "RouteMixed": [
        ("tut/2-From-components-to-chip/2.14-Get-them-all-with-MixedRoute", "Tutorial")
    ],
    "Airbridge": [("tut/2-From-components-to-chip/2.15-Airbridges", "Tutorial")],
    "LaunchpadWirebondCoupled": [
        ("circuit-examples/E.Input-output-coupling/41-LaunchPad", "Example")
    ],
    "Cap3Interdigital": [
        ("tut/quick-topics/QComponent-3-fingers-capacitor", "Tutorial")
    ],
}

IMG_REF_RE = re.compile(r"\.\. image::[\r\n]+\s*(\S+)")
META_DESC_RE = re.compile(r"\.\. meta::\s*\n\s*:description:\s*([^\n]+)")

# Generic docstring lead-ins that say nothing useful on a gallery card, e.g.
#   ``The base `TransmonCross` class.``
#   ``Inherits `BaseQubit` class.``
#   ``The base "JJ_Dolan" inherits the "QComponent" class.``
# We skip these so the card subtitle is the first *substantive* sentence.
BOILERPLATE_RE = re.compile(
    r"^(the\s+base\b.*\bclass\s*\.?\s*|inherits\b.*\bclass\s*\.?\s*)$",
    re.IGNORECASE,
)


def _docstring_of(cls):
    return inspect.getdoc(cls) or ""


def _image_filename(cls) -> str | None:
    """Filename listed in the class docstring, or None."""
    m = IMG_REF_RE.search(_docstring_of(cls))
    return m.group(1).strip() if m else None


def _short_description(cls) -> str:
    """First non-empty line of docstring (skipping image/meta directives),
    truncated and sanitized for safe RST."""
    ds = _docstring_of(cls)
    # Drop the directives, then take the first real line.
    ds = IMG_REF_RE.sub("", ds)
    ds = META_DESC_RE.sub("", ds)
    display = _meta_display_name(cls).strip().rstrip(".").lower()
    for line in ds.splitlines():
        line = line.strip()
        if not line or line.startswith(".."):
            continue
        # Skip generic "The base X class" / "Inherits Y class" lead-ins and a
        # line that merely restates the card title — neither helps the reader.
        if BOILERPLATE_RE.match(line):
            continue
        if line.upper().startswith("NOTE TO USER"):
            continue
        if line.rstrip(".").lower() == display:
            continue
        if len(line) > 100:
            line = line[:97].rstrip() + "..."
        # Sanitize problematic inline markup:
        #   - lone backticks → escaped backticks (avoid "Inline interpreted
        #     text without end-string" warnings).
        #   - asterisks → escaped (would otherwise start emphasis).
        # We don't try to preserve markup; this is just a card subtitle.
        n_bt = line.count("`")
        if n_bt % 2 == 1:
            line = line.replace("`", r"\`")
        # Strip leading/trailing colons that confuse RST inline-target parser.
        line = line.rstrip(":")
        return line
    return ""


def _meta_display_name(cls) -> str:
    """Pull the GUI display name from ``.. meta:: :description:`` if set,
    otherwise the class name."""
    m = META_DESC_RE.search(_docstring_of(cls))
    return m.group(1).strip() if m else cls.__name__


def _iter_component_classes():
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
        except Exception:
            continue
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if obj.__module__ != mod.__name__:
                continue
            if not issubclass(obj, QComponent) or obj is QComponent:
                continue
            if name in SKIP_NAMES:
                continue
            category = py.relative_to(QLIB).parts[0]
            yield category, py, obj


def _group_by_category():
    groups: dict[str, list] = {}
    for category, py, cls in _iter_component_classes():
        groups.setdefault(category, []).append((py, cls))
    # Sort components alphabetically within each category.
    for v in groups.values():
        v.sort(key=lambda x: x[1].__name__.lower())
    return groups


@functools.cache
def _autosummary_registry() -> frozenset[str]:
    """Class names Sphinx autosummary registers as
    ``qiskit_metal.qlibrary.<Name>`` (each gets a per-class apidoc page at
    build time). Parsed from the ``.. autosummary::`` blocks in
    ``qlibrary/__init__.py`` so a just-added component — whose generated
    ``.rst`` isn't committed yet (e.g. SNAIL) — still links to its own page,
    while a class deliberately left out of the autosummary (e.g. SmileyFace)
    correctly falls back to the index."""
    try:
        doc = ast.get_docstring(ast.parse((QLIB / "__init__.py").read_text())) or ""
    except Exception:
        return frozenset()
    names: set[str] = set()
    in_block = False
    for line in doc.splitlines():
        if ".. autosummary::" in line:
            in_block = True
            continue
        if in_block:
            s = line.strip()
            if not s or s.startswith(":"):  # blank or option line (:toctree:)
                continue
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", s):
                names.add(s)
            else:  # prose / category header ends the block
                in_block = False
    return frozenset(names)


def _apidoc_doc_target(cls) -> str:
    """Link target for a component card.

    Prefer the per-class autosummary page
    ``apidocs/qiskit_metal.qlibrary.<ClassName>`` when that class is in the
    autosummary registry (or its ``.rst`` already exists on disk), falling
    back to the qlibrary index otherwise.

    We use the registry rather than a runtime ``hasattr`` on
    ``qiskit_metal.qlibrary``: the class re-exports in ``qlibrary/__init__``
    are gated behind ``config.is_building_docs()``, so at gallery-generation
    time the runtime attribute is absent and every card would otherwise fall
    back to the index."""
    page = f"qiskit_metal.qlibrary.{cls.__name__}"
    if (
        cls.__name__ in _autosummary_registry()
        or (APIDOCS_IMG / f"{page}.rst").exists()
    ):
        return f"apidocs/{page}"
    return "apidocs/qlibrary"


def _check_example_docnames() -> None:
    """Fail when an ``EXAMPLES`` entry points at a notebook that is missing."""
    missing = [
        doc
        for entries in EXAMPLES.values()
        for doc, _ in entries
        if not (DOCS / f"{doc}.ipynb").is_file()
    ]
    if missing:
        raise SystemExit(f"EXAMPLES refers to missing notebooks: {sorted(missing)}")


def _example_links(cls) -> str:
    """Footer text of ``:doc:`` links for a card, or an empty string."""
    entries = EXAMPLES.get(cls.__name__, [])
    return " | ".join(f":doc:`{label} </{doc}>`" for doc, label in entries)


def _render_card(cls, copied_img: str, catalog=()) -> str:
    """One ``grid-item-card`` block for the gallery."""
    display = _meta_display_name(cls)
    desc = _short_description(cls)
    link_doc = (
        f"catalog/{cls.__name__}"
        if cls.__name__ in catalog
        else _apidoc_doc_target(cls)
    )
    img_rel = f"images/qlibrary/{copied_img}" if copied_img else None

    lines = [
        f"   .. grid-item-card:: {display}",
        f"      :link: {link_doc}",
        "      :link-type: doc",
        "      :class-card: sd-shadow-sm",
        "      :text-align: center",
        "",
    ]
    if img_rel:
        lines += [
            f"      .. image:: {img_rel}",
            "         :alt: " + display,
            "         :width: 180px",
            "         :align: center",
            "",
        ]
    if desc:
        lines += [f"      {desc}", ""]
    lines += [f"      .. rubric:: ``{cls.__name__}``", ""]
    examples = _example_links(cls)
    if examples:
        lines += ["      +++", f"      {examples}", ""]
    return "\n".join(lines)


def _emit_gallery_rst(groups, copied_lookup, catalog=()):
    out = [
        ".. _qcomponents-gallery:",
        "",
        "##############################",
        "Component catalog",
        "##############################",
        "",
        "Every component shipped with Quantum Metal at a glance — click a card "
        "for its catalog entry: default options, pins, and a link to the API "
        "reference. The same thumbnails ship inside the "
        "desktop ``MetalGUI`` Library pane and the headless preview, "
        "regenerated from source by ``_dev/generate_qlibrary_thumbnails.py``.",
        "",
        ".. note::",
        "",
        "   Adding a new ``QComponent``? Run "
        "   ``uv run python _dev/generate_qlibrary_thumbnails.py "
        "   --write --inject-docstrings`` and then "
        "   ``uv run python _dev/generate_qcomponent_gallery.py --write`` "
        "   to refresh this page.",
        "",
        "Cards with an **Example** or **Tutorial** link point to a notebook "
        "that uses the component. All component notebooks are listed under "
        ":doc:`circuit-examples/component-examples`.",
        "",
    ]
    if catalog:
        out += [
            ".. toctree::",
            "   :hidden:",
            "   :glob:",
            "",
            "   catalog/*",
            "",
        ]
    # Stable category order
    order = list(CATEGORY_LABELS) + [k for k in groups if k not in CATEGORY_LABELS]
    for cat in order:
        if cat not in groups:
            continue
        title = CATEGORY_LABELS.get(cat, cat.replace("_", " ").title())
        # Pad the underline; emoji + multi-byte chars sometimes count
        # narrower in ``len()`` than they render in terminal/RST, which
        # trips Sphinx's "Title underline too short" warning. Adding a
        # few extra ``=`` is always safe.
        underline = "=" * (len(title) + 4)
        out += [
            title,
            underline,
            "",
            ".. grid:: 1 2 3 4",
            "   :gutter: 3",
            "",
        ]
        for _, cls in groups[cat]:
            img = copied_lookup.get(cls.__name__, "")
            out.append(_render_card(cls, img, catalog))
            out.append("")
    return "\n".join(out) + "\n"


def _copy_thumbnails(groups, write: bool) -> dict[str, str]:
    """Copy each component's thumbnail PNG into docs/images/qlibrary/
    and docs/apidocs/. Returns ``{class_name: copied_filename}``.

    Two destinations:
      - ``docs/images/qlibrary/`` — the visual gallery on the docs site
        (referenced by ``docs/qcomponents-gallery.rst``).
      - ``docs/apidocs/`` — the autodoc class pages (Sphinx resolves
        ``.. image:: foo.png`` from each class docstring relative to
        the .rst file's directory, which sits under ``docs/apidocs/``).
        The filename here must match the docstring directive verbatim.
    """
    GALLERY_IMG.mkdir(parents=True, exist_ok=True)
    APIDOCS_IMG.mkdir(parents=True, exist_ok=True)
    out = {}
    for _, members in groups.items():
        for _, cls in members:
            ref = _image_filename(cls)
            candidates = []
            if ref:
                candidates.append(IMG_SRC / ref)
            candidates += [
                IMG_SRC / f"{cls.__name__}.png",
                IMG_SRC / f"{cls.__name__.lower()}.png",
            ]
            src = next((p for p in candidates if p.exists()), None)
            if src is None:
                continue
            gallery_name = f"{cls.__name__}.png"
            if write:
                shutil.copyfile(src, GALLERY_IMG / gallery_name)
                # docs/apidocs/ — name must match the docstring directive
                # verbatim (the renderer resolves whatever filename the
                # docstring references, not the class name).
                if ref:
                    shutil.copyfile(src, APIDOCS_IMG / ref)
                else:
                    shutil.copyfile(src, APIDOCS_IMG / gallery_name)
            out[cls.__name__] = gallery_name
    return out


def _load_thumbnail_recipes():
    """Import the thumbnail script for its recipes (pins, anchors, points)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_qm_thumbs", THUMBS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._populate_special_recipes()
    return mod


def _fmt_value(val) -> str:
    text = repr(val) if not isinstance(val, str) else f"'{val}'"
    text = " ".join(text.split())
    if len(text) > 70:
        text = text[:67] + "..."
    return text.replace("`", "'")


def _flatten(opts, prefix=""):
    for key, val in opts.items():
        name = f"{prefix}{key}"
        if hasattr(val, "items") and val:
            yield from _flatten(val, name + ".")
        else:
            yield name, val


def _csv_table(rows, header):
    out = [".. csv-table::", f"   :header: {header}", "   :widths: 40, 60", ""]
    for name, val in rows:
        out.append(
            '   "``{}``", "``{}``"'.format(name, _fmt_value(val).replace('"', '""'))
        )
    return out


def _catalog_page(cls, design, comp, category, thumb) -> str:
    """RST for one component's catalog entry, built from a live instance."""
    name = cls.__name__
    display = _meta_display_name(cls)
    opts = cls.get_template_options(design)
    flat = list(_flatten(opts))
    geom = [(k, v) for k, v in flat if not k.startswith(RENDERER_PREFIXES)]
    rend = [(k, v) for k, v in flat if k.startswith(RENDERER_PREFIXES)]
    pins = sorted(comp.pins) if hasattr(comp, "pins") else []
    bases = [b.__name__ for b in cls.__mro__[1:] if b.__name__ != "object"]
    desc = _short_description(cls)
    title = f"{display}"
    out = [f".. _catalog-{name}:", "", title, "=" * max(len(title), 4), ""]
    if desc:
        out += [desc, ""]
    if thumb:
        out += [
            f".. image:: ../images/qlibrary/{thumb}",
            f"   :alt: {display}",
            "   :width: 220px",
            "",
        ]
    out += [
        f"**Class** ``{name}`` · **Module** ``{cls.__module__}`` · "
        f"**Category** {category.replace('_', ' ')}",
        "",
        f"**Inherits** {' → '.join(f'``{b}``' for b in bases[:3])}",
        "",
        "Usage",
        "-----",
        "",
        ".. code-block:: python",
        "",
        "   from qiskit_metal import designs",
        f"   from {cls.__module__} import {name}",
        "",
        "   design = designs.DesignPlanar()",
        f'   comp = {name}(design, "{name[0].lower() + name[1:]}1", options=dict())',
        "",
        "Pins",
        "----",
        "",
    ]
    if pins:
        out += [", ".join(f"``{p}``" for p in pins), ""]
        out += [
            "Pin names of the instance built for this page; some components "
            "add or rename pins from their options.",
            "",
        ]
    else:
        out += [
            "None with the default options. Pins appear when the options "
            "define connection pads, ports, or flux lines.",
            "",
        ]
    out += ["Default options", "---------------", ""]
    if geom:
        out += _csv_table(geom, '"Option", "Default"') + [""]
    else:
        out += ["No component-specific options.", ""]
    if rend:
        out += [
            ".. dropdown:: Renderer options",
            "",
            "   Consumed by the GDS and Ansys renderers.",
            "",
        ]
        out += [
            "   " + ln if ln else "" for ln in _csv_table(rend, '"Option", "Default"')
        ]
        out += [""]
    out += ["More", "----", ""]
    refs = [f":doc:`API reference </{_apidoc_doc_target(cls)}>`"]
    ex = _example_links(cls)
    if ex:
        refs.append(ex)
    out += [" | ".join(refs), ""]
    return "\n".join(out) + "\n"


def _write_catalog(groups, copied, write: bool) -> set:
    """Build every component headlessly and write one page each. Returns
    the class names that got a page; a failing component is skipped."""
    import logging

    thumbs = _load_thumbnail_recipes()
    logging.disable(logging.WARNING)
    done = set()
    if write:
        CATALOG_DIR.mkdir(parents=True, exist_ok=True)
        for old in CATALOG_DIR.glob("*.rst"):
            old.unlink()
    for category, members in groups.items():
        for _, cls in members:
            try:
                design, comp = thumbs._build_design_for(cls)
                text = _catalog_page(
                    cls, design, comp, category, copied.get(cls.__name__, "")
                )
            except Exception as exc:
                print(f"  ! catalog: skipped {cls.__name__}: {exc!r}"[:200])
                continue
            if write:
                (CATALOG_DIR / f"{cls.__name__}.rst").write_text(text)
            done.add(cls.__name__)
    logging.disable(logging.NOTSET)
    return done


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="actually copy images and write docs/qcomponents-gallery.rst",
    )
    args = parser.parse_args()

    _check_example_docnames()
    groups = _group_by_category()
    print(
        f"Found {sum(len(v) for v in groups.values())} components across "
        f"{len(groups)} categories: {', '.join(groups)}"
    )
    copied = _copy_thumbnails(groups, write=args.write)
    catalog = _write_catalog(groups, copied, write=args.write)
    rst = _emit_gallery_rst(groups, copied, catalog)
    if args.write:
        GALLERY_RST.write_text(rst)
        print(f"Wrote {GALLERY_RST.relative_to(REPO)}")
        print(f"Copied {len(copied)} thumbnails into {GALLERY_IMG.relative_to(REPO)}/")
    else:
        print(f"--- {GALLERY_RST.relative_to(REPO)} (preview, head) ---")
        print("\n".join(rst.splitlines()[:40]))
        print(f"... ({len(rst.splitlines())} lines total)")


if __name__ == "__main__":
    main()
