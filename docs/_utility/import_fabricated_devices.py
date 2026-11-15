"""Copy staged device images into the docs and write the gallery manifest.

Usage::

    python docs/_utility/import_fabricated_devices.py SRC_DIR

``SRC_DIR`` holds ``manifest.json`` and the image files it names. The manifest
is a list, or an object with an ``images`` list. Per entry, the first present
key of each group is used:

* file: ``file``, ``filename``, ``path``, ``image``
* caption: ``caption``, ``title``, ``description``
* credit: ``credit``, ``credits``, ``attribution``
* link (optional): ``url``, ``link``, ``source_url``, ``source``

Skipped, and reported: entries without a file or caption; entries with
``third_party_permission_likely`` true (they need the owner's approval first);
entries whose ``device_kind`` is ``layout`` (renders and layouts, not fabricated
devices). A missing credit is kept empty and shown as "Credit: not stated".
Nothing is filled in. Images go to ``docs/_static/fabricated/`` and the manifest to
``docs/_data/fabricated-devices.json`` (see ``docs/qm_showcase.py``).
"""

import json
import shutil
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent


def _first(entry, keys):
    for k in keys:
        if entry.get(k):
            return str(entry[k])
    return ""


def main(src):
    src = Path(src)
    raw = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    entries = raw.get("images", []) if isinstance(raw, dict) else raw
    dst = DOCS / "_static" / "fabricated"
    dst.mkdir(parents=True, exist_ok=True)
    out, skipped = [], []
    for e in entries:
        name = _first(e, ("file", "filename", "path", "image"))
        caption = _first(e, ("caption", "title", "description"))
        credit = _first(e, ("credit", "credits", "attribution"))
        link = _first(e, ("url", "link", "source_url", "source"))
        if link and not link.startswith(("http://", "https://")):
            link = ""
        if (
            not (name and caption and (src / name).is_file())
            or e.get("third_party_permission_likely")
            or e.get("device_kind") == "layout"
        ):
            skipped.append(name or str(e)[:60])
            continue
        shutil.copyfile(src / name, dst / Path(name).name)
        item = {
            "file": Path(name).name,
            "caption": caption,
            "credit": credit,
        }  # may be ""
        if link:
            item["url"] = link
        out.append(item)
    manifest = DOCS / "_data" / "fabricated-devices.json"
    manifest.write_text(
        json.dumps({"images": out}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"imported {len(out)}; skipped {len(skipped)}: {skipped}")


if __name__ == "__main__":
    main(sys.argv[1])
