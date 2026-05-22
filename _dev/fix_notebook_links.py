"""Fix broken inter-notebook links in docs/tut/ and tutorials/.

The v0.7.0 docs/tut/ rename moved notebooks to hyphenated paths. Some markdown
cells still link to the old space-separated paths, breaking nbsphinx during
the docs build. Also fixes references to 2.4 (renumbered to 3.1) and the
bare 3.2 reference.

Run from repo root:
    python3 _dev/fix_notebook_links.py            # dry-run
    python3 _dev/fix_notebook_links.py --write
"""

import json
import sys
from pathlib import Path

# (search_pattern, replacement, fixup_description) — applied as literal string replace
REPLACEMENTS = [
    # 1.4 Headless quick view — multiple wrong path forms (space or %20 encoded)
    ("1 Overview/1.4 Headless quick view (no Qt GUI).ipynb",
     "1-Overview/1.4-Headless-quick-view-%28no-Qt-GUI%29.ipynb",
     "1.4 link: space → hyphen + parens encoded"),
    ("1%20Overview/1.4%20Headless%20quick%20view%20%28no%20Qt%20GUI%29.ipynb",
     "1-Overview/1.4-Headless-quick-view-%28no-Qt-GUI%29.ipynb",
     "1.4 link: %20 → hyphen"),
    # 2.4 QRenderer Introduction — renumbered to 3.1 Introduction to QRenderers
    ("../2 From components to chip/2.4 QRenderer Introduction.ipynb",
     "../3-Renderers/3.1-Introduction-to-QRenderers.ipynb",
     "2.4 reference: renumbered → 3.1"),
    ("../2%20From%20components%20to%20chip/2.4%20QRenderer%20Introduction.ipynb",
     "../3-Renderers/3.1-Introduction-to-QRenderers.ipynb",
     "2.4 reference: renumbered → 3.1 (%20 form)"),
    # 3.2 Export GDS — same-folder reference, no prefix
    ("3.2 Export your design to GDS.ipynb",
     "3.2-Export-your-design-to-GDS.ipynb",
     "3.2 link: space → hyphen"),
    ("3.2%20Export%20your%20design%20to%20GDS.ipynb",
     "3.2-Export-your-design-to-GDS.ipynb",
     "3.2 link: %20 → hyphen"),
]


def fix_notebook(path, replacements, write=False):
    """Apply text replacements to a notebook JSON. Returns (n_replacements, descriptions)."""
    text = Path(path).read_text()
    original = text
    applied = []
    for old, new, desc in replacements:
        if old in text:
            count = text.count(old)
            text = text.replace(old, new)
            applied.append((desc, count))

    if write and text != original:
        # Validate as JSON before writing
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            print(f"  ✗ skipping {path}: produced invalid JSON ({e})")
            return [], False
        Path(path).write_text(text)

    return applied, text != original


def main():
    write = '--write' in sys.argv
    print(f"Mode: {'WRITE' if write else 'DRY-RUN'}")
    print()

    # Scan both folders
    nbs = sorted(
        list(Path('docs/tut').rglob('*.ipynb')) +
        list(Path('tutorials').rglob('*.ipynb'))
    )
    nbs = [p for p in nbs
           if '.ipynb_checkpoints' not in str(p) and not p.name.startswith('.')]

    total_files = 0
    total_replacements = 0
    for p in nbs:
        applied, changed = fix_notebook(p, REPLACEMENTS, write=write)
        if applied:
            total_files += 1
            tag = '✓' if write else '·'
            for desc, count in applied:
                total_replacements += count
                print(f"  {tag} [{count}x] {desc}  in  {p}")

    print()
    print(f"Files touched: {total_files} | Replacements: {total_replacements}")
    if not write:
        print("\nDry-run only. Re-run with --write to apply.")


if __name__ == '__main__':
    main()
