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
.qm-card { font-family: var(--jp-ui-font-family, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif); font-size: 13px; line-height: 1.4; color: inherit;
  background: transparent; text-align: left; border: 1px solid rgba(128,128,128,.3);
  border-radius: 10px; padding: 10px 14px 6px 14px; margin: 4px 0 10px 0;
  max-width: 1100px; }
.qm-card .qm-title { display: flex; flex-wrap: wrap; align-items: baseline;
  gap: 8px; margin: 0 0 8px 0; }
.qm-card .qm-name { font-size: 16px; font-weight: 650; }
.qm-card .qm-badge { font-size: 11px; font-weight: 600; padding: 1px 8px;
  border-radius: 999px; background: rgba(59,130,246,.16); color: inherit;
  border: 1px solid rgba(59,130,246,.35); }
.qm-card .qm-meta { font-size: 12px; opacity: .7; }
.qm-card details { margin: 4px 0 8px 0; }
.qm-card summary { cursor: pointer; font-weight: 600; padding: 3px 0;
  list-style-position: inside; }
.qm-card summary .qm-meta { font-weight: 400; margin-left: 6px; }
.qm-card table { border-collapse: separate; border-spacing: 0; margin: 4px 0 6px 0;
  color: inherit; background: transparent; width: auto; }
.qm-card table th, .qm-card table td { text-align: left !important;
  vertical-align: top; padding: 3px 10px; border: 0 !important; color: inherit;
  background: transparent; }
.qm-card table th { font-size: 11px; font-weight: 650; text-transform: uppercase;
  letter-spacing: .04em; opacity: .75; border-bottom: 1px solid rgba(128,128,128,.35) !important; }
.qm-card table tbody tr:nth-child(even) td { background: rgba(128,128,128,.06); }
.qm-card table tbody tr:hover td { background: rgba(59,130,246,.08); }
.qm-card td.qm-key { font-family: var(--jp-code-font-family, ui-monospace, monospace);
  white-space: nowrap; }
.qm-card td.qm-val { font-family: var(--jp-code-font-family, ui-monospace, monospace);
  white-space: nowrap; }
.qm-card td.qm-doc { opacity: .78; max-width: 40em; white-space: normal; }
.qm-card tr.qm-group td { font-weight: 650; opacity: .9; }
.qm-card tr.qm-changed td { background: rgba(245,158,11,.14) !important; }
.qm-card tr.qm-changed td.qm-key { box-shadow: inset 3px 0 0 rgba(245,158,11,.9); }
.qm-card .qm-dot { display: inline-block; width: .6em; height: .6em;
  border-radius: 50%; background: rgba(245,158,11,.9); margin-right: 4px; }
.qm-card .qm-legend { font-size: 11px; opacity: .75; margin: 0 0 4px 0; }
.qm-card img { max-width: 320px; height: auto; display: block; margin: 2px 0 8px 0;
  border-radius: 6px; }
</style>
"""

_MISSING = object()


def component_html(
    component: QComponent,
    docs: bool = True,
    parsed: bool = True,
    pins: bool = True,
    image: bool = True,
) -> str:
    """HTML card for a component: options, pins, and a picture.

    Options changed from the class's defaults are highlighted.

    Args:
        component: The component.
        docs: Add a column with each option's description from the docstrings.
        parsed: Add a column with each option's parsed value (design units).
        pins: Add a table of the component's pins and what they connect to.
        image: Add a picture of the component.
    """
    esc = html.escape
    descriptions = option_docs(type(component)) if docs else {}
    renderers = _renderer_docs(component.design) if docs else {}
    defaults = _defaults(component)
    head = ["option", "value"] + (["parsed"] if parsed else [])
    head += ["description"] if docs else []
    rows: list[str] = []
    counts = {"options": 0, "changed": 0}

    def walk(options, path, depth):
        for key, value in options.items():
            here = path + (str(key),)
            pad = f"padding-left:{10 + 16 * depth}px"
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
            counts["options"] += 1
            default = _default_at(defaults, here)
            # Only an option with a known class default can be "changed";
            # some are added at build time (a route's trace_gap) or computed.
            changed = default is not _MISSING and str(default) != str(value)
            counts["changed"] += changed
            title = f' title="default: {esc(repr(default))}"' if changed else ""
            cells = [
                f'<td class="qm-key" style="{pad}"{title}>{esc(str(key))}</td>',
                f'<td class="qm-val">{esc(repr(value))}</td>',
            ]
            if parsed:
                cells.append(f'<td class="qm-val">{esc(_parsed(component, here))}</td>')
            if docs:
                cells.append(f'<td class="qm-doc">{esc(doc)}</td>')
            css = ' class="qm-changed"' if changed else ""
            rows.append(f"<tr{css}>" + "".join(cells) + "</tr>")

    walk(component.options, (), 0)
    n_pins = len(component.pins)
    n_connected = sum(1 for pin in component.pins.values() if pin.get("net_id"))
    parts = [
        _STYLE,
        '<div class="qm-card">',
        '<div class="qm-title">'
        f'<span class="qm-name">{esc(component.name)}</span>'
        f'<span class="qm-badge">{esc(type(component).__name__)}</span>'
        f'<span class="qm-meta">id {esc(str(component.id))} &middot; '
        f"{counts['options']} options, {counts['changed']} changed &middot; "
        f"{n_pins} pins, {n_connected} connected</span></div>",
    ]
    if image:
        parts.append(_image_html(component))
    parts += [
        "<details open><summary>Options"
        f'<span class="qm-meta">{counts["changed"]} changed from the defaults</span>'
        "</summary>",
        '<div class="qm-legend"><span class="qm-dot"></span>changed from the '
        "class default (hover the name for the default)</div>"
        if counts["changed"]
        else "",
        "<table><thead><tr>"
        + "".join(f"<th>{h}</th>" for h in head)
        + "</tr></thead><tbody>",
        *rows,
        "</tbody></table></details>",
    ]
    if pins and component.pins:
        parts.append(
            f'<details open><summary>Pins<span class="qm-meta">{n_pins} pins, '
            f"{n_connected} connected</span></summary>{_pins_html(component)}</details>"
        )
    parts.append("</div>")
    return "\n".join(parts)


def _defaults(component: QComponent):
    try:
        return type(component).get_template_options(component.design)
    except Exception:  # noqa: BLE001 -- display only; never raise from a repr
        return {}


def _default_at(defaults, path: tuple[str, ...]):
    """The class default for an option path, or _MISSING if it has none."""

    def lookup(node, keys):
        # Membership, not indexing: Metal's Dict returns an empty Dict for a
        # missing key instead of raising.
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return _MISSING
            node = node[key]
        return node

    found = lookup(defaults, path)
    if found is _MISSING and len(path) >= 3 and path[0] == "connection_pads":
        # A pad takes its defaults from _default_connection_pads.
        found = lookup(defaults, ("_default_connection_pads",) + path[2:])
    return found


def _parsed(component: QComponent, path: tuple[str, ...]) -> str:
    value = component.p
    try:
        for key in path:
            value = value[key]
    except Exception:  # noqa: BLE001 -- display only; never raise from a repr
        return ""
    return repr(value)


def _image_html(component: QComponent) -> str:
    """The component drawn alone, framed to its bounds, as an <img>.

    Drawn on a standalone Agg figure -- no pyplot, no GUI event loop -- so it
    is safe headless, in a notebook, and next to the desktop GUI.
    """
    import base64
    import io

    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    from qiskit_metal.viewer.view import view

    try:
        x0, y0, x1, y1 = component.qgeometry_bounds()
        pad = 0.08 * max(x1 - x0, y1 - y0, 1e-3)
        fig = Figure(figsize=(3.6, 3.6))
        FigureCanvasAgg(fig)
        ax = fig.add_subplot()
        view(component.design, ax=ax, components=[component.name], chip_outline=False)
        ax.set_xlim(x0 - pad, x1 + pad)
        ax.set_ylim(y0 - pad, y1 + pad)
        ax.set_aspect("equal")
        ax.tick_params(labelsize=7)
        ax.set_title("")
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=110, bbox_inches="tight")
    except Exception:  # noqa: BLE001 -- display only; never raise from a repr
        return ""
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
            f"<td>{esc(target) or '&mdash;'}</td></tr>"
        )
    return (
        "<table><thead><tr><th>pin</th><th>middle (mm)</th><th>normal</th>"
        "<th>width (mm)</th><th>connected to</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def components_html(design, limit: int = 200) -> str:
    """HTML table of a design's components: name, class, id, pins, connections."""
    esc = html.escape
    net = getattr(design, "net_info", None)
    connected: dict = {}
    if net is not None and len(net):
        for cid in net["component_id"]:
            connected[cid] = connected.get(cid, 0) + 1
    rows = []
    items = list(design.components.items())
    for name, comp in items[:limit]:
        rows.append(
            f'<tr><td class="qm-key">{esc(name)}</td>'
            f'<td><span class="qm-badge">{esc(type(comp).__name__)}</span></td>'
            f'<td class="qm-val">{esc(str(comp.id))}</td>'
            f'<td class="qm-val">{len(comp.pins)}</td>'
            f'<td class="qm-val">{connected.get(comp.id, 0)}</td></tr>'
        )
    more = (
        f'<div class="qm-meta">&hellip; and {len(items) - limit} more</div>'
        if len(items) > limit
        else ""
    )
    return (
        "<table><thead><tr><th>component</th><th>class</th><th>id</th><th>pins</th>"
        "<th>connected</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
        + more
    )


def components_card(design, limit: int = 200) -> str:
    """``design.components`` as a card."""
    return (
        f'{_STYLE}<div class="qm-card"><div class="qm-title">'
        f'<span class="qm-name">Components</span>'
        f'<span class="qm-meta">{len(design.components)} in '
        f"{html.escape(type(design).__name__)}</span></div>"
        f"{components_html(design, limit)}</div>"
    )


def design_html(design, limit: int = 200) -> str:
    """HTML card for a design: chips, counts by class, variables, components."""
    esc = html.escape
    counts: dict[str, int] = {}
    for comp in design.components.values():
        counts[type(comp).__name__] = counts.get(type(comp).__name__, 0) + 1

    def chip_row(name, chip):
        size = chip.get("size", {})
        return (
            f'<tr><td class="qm-key">{esc(str(name))}</td>'
            f'<td class="qm-val">{esc(str(size.get("size_x", "")))} &times; '
            f"{esc(str(size.get('size_y', '')))}</td>"
            f'<td class="qm-val">({esc(str(size.get("center_x", "")))}, '
            f"{esc(str(size.get('center_y', '')))})</td></tr>"
        )

    chips = "".join(chip_row(n, c) for n, c in design.chips.items())
    classes = "".join(
        f'<tr><td><span class="qm-badge">{esc(k)}</span></td>'
        f'<td class="qm-val">{v}</td></tr>'
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1])
    )
    variables = "".join(
        f'<tr><td class="qm-key">{esc(str(k))}</td>'
        f'<td class="qm-val">{esc(repr(v))}</td></tr>'
        for k, v in design.variables.items()
    )
    net = getattr(design, "net_info", None)
    n_nets = len(set(net["net_id"])) if net is not None and len(net) else 0

    def section(title, meta, body, open_=True):
        return (
            f"<details{' open' if open_ else ''}><summary>{title}"
            f'<span class="qm-meta">{meta}</span></summary>{body}</details>'
        )

    return "\n".join(
        [
            _STYLE,
            '<div class="qm-card"><div class="qm-title">'
            f'<span class="qm-name">{esc(getattr(design, "name", "") or "design")}</span>'
            f'<span class="qm-badge">{esc(type(design).__name__)}</span>'
            f'<span class="qm-meta">{len(design.components)} components &middot; '
            f"{n_nets} connections</span></div>",
            section(
                "Chips",
                f"{len(design.chips)}",
                "<table><thead><tr><th>chip</th><th>size</th><th>center</th></tr>"
                "</thead><tbody>" + chips + "</tbody></table>",
            ),
            section(
                "Components by class",
                f"{len(counts)} classes",
                "<table><thead><tr><th>class</th><th>count</th></tr></thead><tbody>"
                + classes
                + "</tbody></table>",
            )
            if classes
            else "",
            section(
                "Variables",
                f"{len(design.variables)}",
                "<table><thead><tr><th>variable</th><th>value</th></tr></thead><tbody>"
                + variables
                + "</tbody></table>",
            )
            if variables
            else "",
            section(
                "Components",
                f"{len(design.components)}",
                components_html(design, limit),
                open_=len(design.components) <= 30,
            )
            if design.components
            else "",
            "</div>",
        ]
    )
