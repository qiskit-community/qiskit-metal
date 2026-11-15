"""Research showcase data: papers and projects, fabricated-device gallery.

The sections of ``built-with-metal.rst`` are filled at build time (``conf.py``
replaces the ``{{ QM_PAPERS:<section> }}`` and ``{{ QM_FABRICATED }}`` tokens) from
JSON files in ``docs/_data/``:

``papers.json``
    ``{"entries": [{"title", "authors", "venue", "year", "url", "note"}, ...]}``
    ``title`` is required; the other keys are optional.

``fabricated-devices.json``
    ``{"images": [{"file", "caption", "credit", "url"}, ...]}``
    ``file`` is a path relative to ``docs/_static/fabricated/``; ``caption``
    is required, ``credit`` may be empty (shown as "Credit: not stated"), ``url`` (source or paper) is optional.
    ``_utility/import_fabricated_devices.py`` writes this file and copies the
    images.

Nothing is invented here: an empty file renders a one-line placeholder.
"""

import html
import json
import os

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_data")


def _load(name, key):
    path = os.path.join(DATA, name)
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get(key, [])


def _rst_escape(text):
    return str(text).replace("\\", "\\\\").replace("*", "\\*").replace("`", "\\`")


GROUPS = {
    "chips": "Chips and designs",
    "papers": "Papers, theses and books",
    "software": "Software built on or for Quantum Metal",
}
SELECTIONS = ("chips", "papers", "software", "mentions")


def _select(entries, sel):
    """Entries of one section; ``mentions`` collects the tier-"mention" entries of every group."""
    if sel == "mentions":
        return [e for e in entries if e.get("tier") == "mention"]
    return [
        e
        for e in entries
        if e.get("group") == GROUPS[sel] and e.get("tier", "design") != "mention"
    ]


def papers_rst(sel="papers"):
    entries = _select(_load("papers.json", "entries"), sel)
    if not entries:
        return "No entries yet. To add one, open an issue or a pull request that edits ``docs/_data/papers.json``.\n"
    out = [".. raw:: html", "", '    <ul class="qm-papers">']
    for e in entries:
        title = html.escape(e["title"])
        if e.get("url"):
            title = f'<a href="{html.escape(e["url"], quote=True)}">{title}</a>'
        meta = " · ".join(
            html.escape(str(e[k])) for k in ("authors", "venue", "year") if e.get(k)
        )
        note = (
            f'<span class="qm-paper-note">{html.escape(e["note"])}</span>'
            if e.get("note")
            else ""
        )
        out.append(
            f'    <li><span class="qm-paper-title">{title}</span>'
            f'<span class="qm-paper-meta">{meta}</span>{note}</li>'
        )
    out.append("    </ul>")
    return "\n".join(out) + "\n"


def fabricated_rst(limit=None):
    images = _load("fabricated-devices.json", "images")
    if limit is not None:
        if not images:
            return ""
        images = images[:limit]
    if not images:
        return (
            "Photographs and micrographs of devices designed with Quantum "
            "Metal will be listed here, each with its credit.\n"
        )
    out = [".. raw:: html", "", '    <div class="qm-fab-grid">']
    for im in images:
        src = "_static/fabricated/" + html.escape(im["file"], quote=True)
        cap = html.escape(im["caption"])
        credit = html.escape(im.get("credit") or "Credit: not stated")
        if im.get("url"):
            credit = f'<a href="{html.escape(im["url"], quote=True)}">{credit}</a>'
        out.append(
            f'    <figure><img src="{src}" alt="{cap}" loading="lazy">'
            f'<figcaption>{cap}<br><span class="qm-fab-credit">{credit}</span>'
            "</figcaption></figure>"
        )
    out.append("    </div>")
    return "\n".join(out) + "\n"
