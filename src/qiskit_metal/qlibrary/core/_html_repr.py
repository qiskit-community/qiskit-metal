# This code is part of Quantum Metal.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""HTML view of a QComponent: its options (with their documentation) and pins.

The option descriptions come from the ``Default Options:`` sections of the
class docstrings along the MRO, which list options as
``* name: 'value' -- description``, nested by indentation.
"""

from __future__ import annotations

import html
import math
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import QComponent

_HEADER = re.compile(r"^(\s*)(?:Default|Common) Options:\s*$")
_BULLET = re.compile(r"^(\s*)\*\s+([A-Za-z_][\w/]*)\s*(?::|=)?\s*(.*)$")


def option_docs(cls: type) -> dict[tuple[str, ...], str]:
    """``{option path: description}`` parsed from the class docstrings.

    Walks the MRO from the base up, so a subclass's description of an option
    replaces its parent's (unless the subclass lists it without one). A path is a tuple of keys, e.g.
    ``("lead", "start_straight")``. ``pos_x/_y`` documents both ``pos_x`` and
    ``pos_y``.
    """
    docs: dict[tuple[str, ...], str] = {}
    for klass in reversed(cls.__mro__):
        for path, text in _parse(klass.__doc__ or "").items():
            if text or path not in docs:  # an empty entry keeps the parent's text
                docs[path] = text
    return docs


def _parse(doc: str) -> dict[tuple[str, ...], str]:
    out: dict[tuple[str, ...], str] = {}
    lines = doc.expandtabs().splitlines()
    i = 0
    while i < len(lines):
        header = _HEADER.match(lines[i])
        i += 1
        if not header:
            continue
        stack: list[tuple[int, str]] = []  # (indent, key) of enclosing bullets
        last: list[tuple[str, ...]] = []  # paths the previous bullet documented
        last_indent = -1
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                # A blank line ends the block unless more bullets follow.
                nxt = next((n for n in lines[i + 1 :] if n.strip()), "")
                if not _BULLET.match(nxt):
                    break
                i += 1
                continue
            bullet = _BULLET.match(line)
            indent = len(line) - len(line.lstrip())
            if bullet:
                depth, name, rest = (
                    len(bullet.group(1)),
                    bullet.group(2),
                    bullet.group(3),
                )
                while stack and stack[-1][0] >= depth:
                    stack.pop()
                parents = tuple(key for _, key in stack)
                description = rest.split(" -- ", 1)[1].strip() if " -- " in rest else ""
                last = [parents + (key,) for key in _expand(name)]
                for path in last:
                    out[path] = description
                last_indent = depth
                stack.append((depth, _expand(name)[0]))
            elif last and indent > last_indent:
                # Continuation of the previous bullet's description.
                for path in last:
                    out[path] = (out[path] + " " + line.strip()).strip()
            else:
                break
            i += 1
    return out


def _expand(name: str) -> list[str]:
    """``pos_x/_y`` -> ``["pos_x", "pos_y"]``; other names unchanged."""
    if "/" not in name:
        return [name]
    first, *others = name.split("/")
    stem = first.rsplit("_", 1)[0]
    return [first] + [
        stem + other if other.startswith("_") else other for other in others
    ]


def _doc_for(
    path: tuple[str, ...], docs: dict[tuple[str, ...], str], renderers: dict
) -> str:
    if path in docs and docs[path]:
        return docs[path]
    # A pad under connection_pads is documented under _default_connection_pads.
    if len(path) >= 3 and path[0] == "connection_pads":
        alt = ("_default_connection_pads",) + path[2:]
        if docs.get(alt):
            return docs[alt]
    # A renderer's column, carried as ``<renderer name>_<column>``.
    if len(path) == 1:
        for name in sorted(renderers, key=len, reverse=True):
            if path[0].startswith(name + "_"):
                text = renderers[name].get(path[0][len(name) + 1 :])
                if text:
                    return text.format(renderer=name)
    # Otherwise, a unique description of the same leaf name.
    matches = {d for p, d in docs.items() if p[-1] == path[-1] and d}
    return matches.pop() if len(matches) == 1 else ""


def _renderer_docs(design) -> dict[str, dict[str, str]]:
    """``{renderer name: element_table_docs}`` for the renderers that add options."""
    from qiskit_metal.renderers.renderer_base.renderer_base import QRenderer

    out = {}
    classes = {type(r) for r in getattr(design, "renderers", {}).values()}
    for cls in classes:
        name = getattr(cls, "name", None)
        if isinstance(name, str):
            out[name] = dict(getattr(cls, "element_table_docs", {}) or {})
    for name in getattr(QRenderer, "__loaded_renderers__", set()):
        out.setdefault(name, dict(QRenderer.element_table_docs))
    return out


_STYLE = """
<style>
.qm-comp { font-family: var(--jp-ui-font-family, sans-serif); font-size: 13px;
  color: inherit; background: transparent; text-align: left; }
.qm-comp h4 { margin: 0.2em 0 0.4em 0; font-weight: 600; color: inherit; }
.qm-comp .qm-sub { opacity: 0.7; font-weight: 400; }
.qm-comp table { border-collapse: collapse; margin: 0 0 0.8em 0; color: inherit;
  background: transparent; }
.qm-comp table th, .qm-comp table td { border: 1px solid rgba(128, 128, 128, 0.35);
  padding: 2px 8px; text-align: left !important; vertical-align: top;
  background: transparent; color: inherit; }
.qm-comp table th { background: rgba(128, 128, 128, 0.14); font-weight: 600; }
.qm-comp td.qm-key { font-family: var(--jp-code-font-family, monospace);
  white-space: nowrap; }
.qm-comp td.qm-val { font-family: var(--jp-code-font-family, monospace); }
.qm-comp td.qm-doc { opacity: 0.8; max-width: 38em; }
.qm-comp tr.qm-group td { font-weight: 600; background: rgba(128, 128, 128, 0.07); }
.qm-comp img { max-width: 100%; display: block; margin: 0 0 0.8em 0; }
</style>
"""


def component_html(
    component: QComponent,
    docs: bool = True,
    parsed: bool = True,
    pins: bool = True,
    image: bool = False,
) -> str:
    """HTML for a component: header, options table, pins, and optionally a picture.

    Args:
        component: The component.
        docs: Add a column with each option's description from the docstrings.
        parsed: Add a column with each option's parsed value (design units).
        pins: Add a table of the component's pins and what they connect to.
        image: Add a picture of the component (drawn with ``qm.view``).
    """
    esc = html.escape
    descriptions = option_docs(type(component)) if docs else {}
    renderers = _renderer_docs(component.design) if docs else {}
    head = ["option", "value"] + (["parsed"] if parsed else [])
    head += ["description"] if docs else []
    rows: list[str] = []

    def walk(options, path, depth):
        for key, value in options.items():
            here = path + (str(key),)
            pad = f"padding-left:{8 + 16 * depth}px"
            doc = _doc_for(here, descriptions, renderers) if docs else ""
            if isinstance(value, dict):
                blanks = len(head) - 1 - (1 if docs else 0)
                cells = [f'<td class="qm-key" style="{pad}">{esc(str(key))}</td>']
                cells += ["<td></td>"] * blanks
                if docs:
                    cells.append(f'<td class="qm-doc">{esc(doc)}</td>')
                rows.append('<tr class="qm-group">' + "".join(cells) + "</tr>")
                walk(value, here, depth + 1)
                continue
            cells = [
                f'<td class="qm-key" style="{pad}">{esc(str(key))}</td>',
                f'<td class="qm-val">{esc(repr(value))}</td>',
            ]
            if parsed:
                cells.append(f'<td class="qm-val">{esc(_parsed(component, here))}</td>')
            if docs:
                cells.append(f'<td class="qm-doc">{esc(doc)}</td>')
            rows.append("<tr>" + "".join(cells) + "</tr>")

    walk(component.options, (), 0)
    parts = [
        _STYLE,
        '<div class="qm-comp">',
        f"<h4>{esc(component.name)} "
        f'<span class="qm-sub">{esc(type(component).__name__)} &middot; '
        f"id {esc(str(component.id))}</span></h4>",
    ]
    if image:
        parts.append(_image_html(component))
    parts += [
        "<table><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr>",
        *rows,
        "</table>",
    ]
    if pins and component.pins:
        parts.append(_pins_html(component))
    parts.append("</div>")
    return "\n".join(parts)


def _parsed(component: QComponent, path: tuple[str, ...]) -> str:
    value = component.p
    try:
        for key in path:
            value = value[key]
    except Exception:  # noqa: BLE001 -- display only; never raise from a repr
        return ""
    return repr(value)


def _image_html(component: QComponent) -> str:
    """The component drawn on its design, framed to its bounds, as an <img>."""
    import base64
    import io

    import matplotlib.pyplot as plt

    from qiskit_metal.viewer.view import view

    try:
        x0, y0, x1, y1 = component.qgeometry_bounds()
    except Exception:  # noqa: BLE001 -- no geometry: nothing to draw
        return ""
    pad = 0.15 * max(x1 - x0, y1 - y0, 1e-3)
    fig = view(component.design)
    try:
        ax = fig.axes[0]
        ax.set_xlim(x0 - pad, x1 + pad)
        ax.set_ylim(y0 - pad, y1 + pad)
        ax.set_aspect("equal")
        fig.set_size_inches(4.5, 4.5)
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=90, bbox_inches="tight")
    finally:
        plt.close(fig)
    data = base64.b64encode(buffer.getvalue()).decode()
    return (
        f'<img alt="{html.escape(component.name)}" src="data:image/png;base64,{data}">'
    )


def _pins_html(component: QComponent) -> str:
    esc = html.escape
    names = {c.id: n for n, c in component.design.components.items()}
    net = getattr(component.design, "net_info", None)
    rows = []
    for name, pin in component.pins.items():
        middle = ", ".join(f"{float(v):.4f}" for v in pin["middle"])
        nx, ny = (float(v) for v in pin["normal"])
        angle = math.degrees(math.atan2(ny, nx)) % 360
        target = ""
        if net is not None and len(net) and pin.get("net_id"):
            same = net[
                (net["net_id"] == pin["net_id"]) & (net["component_id"] != component.id)
            ]
            target = ", ".join(
                f"{names.get(cid, cid)}.{pname}"
                for cid, pname in zip(same["component_id"], same["pin_name"])
            )
        rows.append(
            f'<tr><td class="qm-key">{esc(name)}</td>'
            f'<td class="qm-val">({esc(middle)})</td>'
            f'<td class="qm-val">{angle:.1f}&deg;</td>'
            f'<td class="qm-val">{float(pin.get("width", 0)):.4g}</td>'
            f"<td>{esc(target)}</td></tr>"
        )
    return (
        "<table><tr><th>pin</th><th>middle (mm)</th><th>normal</th>"
        "<th>width (mm)</th><th>connected to</th></tr>" + "".join(rows) + "</table>"
    )


def components_html(design, limit: int = 200) -> str:
    """HTML table of a design's components: name, class, id, pins, connections."""
    esc = html.escape
    net = getattr(design, "net_info", None)
    connected = {}
    if net is not None and len(net):
        for cid in net["component_id"]:
            connected[cid] = connected.get(cid, 0) + 1
    rows = []
    items = list(design.components.items())
    for name, comp in items[:limit]:
        rows.append(
            f'<tr><td class="qm-key">{esc(name)}</td>'
            f"<td>{esc(type(comp).__name__)}</td>"
            f'<td class="qm-val">{esc(str(comp.id))}</td>'
            f'<td class="qm-val">{len(comp.pins)}</td>'
            f'<td class="qm-val">{connected.get(comp.id, 0)}</td></tr>'
        )
    more = (
        f'<p class="qm-sub">&hellip; and {len(items) - limit} more</p>'
        if len(items) > limit
        else ""
    )
    return (
        "<table><tr><th>component</th><th>class</th><th>id</th><th>pins</th>"
        "<th>connected</th></tr>" + "".join(rows) + "</table>" + more
    )


def design_html(design, limit: int = 200) -> str:
    """HTML summary of a design: chips, counts by class, variables, components."""
    esc = html.escape
    counts: dict[str, int] = {}
    for comp in design.components.values():
        counts[type(comp).__name__] = counts.get(type(comp).__name__, 0) + 1
    chips = "".join(
        f'<tr><td class="qm-key">{esc(str(name))}</td>'
        f'<td class="qm-val">{esc(str(chip.get("size", {}).get("size_x", "")))} x '
        f"{esc(str(chip.get('size', {}).get('size_y', '')))}</td>"
        f'<td class="qm-val">({esc(str(chip.get("size", {}).get("center_x", "")))}, '
        f"{esc(str(chip.get('size', {}).get('center_y', '')))})</td></tr>"
        for name, chip in design.chips.items()
    )
    classes = "".join(
        f"<tr><td>{esc(k)}</td><td class='qm-val'>{v}</td></tr>"
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1])
    )
    variables = "".join(
        f'<tr><td class="qm-key">{esc(str(k))}</td><td class="qm-val">{esc(repr(v))}</td></tr>'
        for k, v in design.variables.items()
    )
    net = getattr(design, "net_info", None)
    n_nets = len(set(net["net_id"])) if net is not None and len(net) else 0
    return "\n".join(
        [
            _STYLE,
            '<div class="qm-comp">',
            f"<h4>{esc(getattr(design, 'name', '') or 'design')} "
            f'<span class="qm-sub">{esc(type(design).__name__)} &middot; '
            f"{len(design.components)} components &middot; {n_nets} connections"
            "</span></h4>",
            "<table><tr><th>chip</th><th>size</th><th>center</th></tr>"
            + chips
            + "</table>",
            "<table><tr><th>class</th><th>count</th></tr>" + classes + "</table>"
            if classes
            else "",
            "<table><tr><th>variable</th><th>value</th></tr>" + variables + "</table>"
            if variables
            else "",
            components_html(design, limit) if design.components else "",
            "</div>",
        ]
    )
