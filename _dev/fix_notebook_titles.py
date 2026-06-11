"""Ensure every numbered notebook has its X.YY prefix in the H1 title.

Two operations:
  1. For notebooks WITH an H1 but missing the X.YY prefix: prepend it.
  2. For notebooks WITHOUT an H1: insert a new markdown cell at the top
     with `# X.YY <title derived from filename>`.

Run from repo root:
    python3 _dev/fix_notebook_titles.py            # dry-run
    python3 _dev/fix_notebook_titles.py --write
"""

import json
import re
import sys
import uuid
from pathlib import Path


def get_h1_info(nb):
    """Return (cell_idx, line_idx, h1_text) for the first H1, or None."""
    for ci, c in enumerate(nb['cells']):
        if c['cell_type'] != 'markdown':
            continue
        src = c['source']
        lines = src if isinstance(src, list) else src.split('\n')
        for li, raw in enumerate(lines):
            line = raw.rstrip('\n')
            if line.lstrip().startswith('# ') and not line.lstrip().startswith('## '):
                return ci, li, line.lstrip()[2:].strip()
        return None
    return None


def derive_title_from_filename(stem):
    """`4.04-New-LOM-and-Fluxonium-Example` → `4.04 New LOM and Fluxonium Example`."""
    m = re.match(r'^(\d+\.\d+)[-_ ]+(.*)$', stem)
    if not m:
        return stem.replace('-', ' ')
    num, rest = m.group(1), m.group(2)
    # Hyphens → spaces, but preserve all-caps acronyms (LOM, EPR, CPB etc.) as-is
    title = rest.replace('-', ' ')
    return f"{num} {title}"


def has_correct_prefix(title, num):
    """Does the title already start with the X.YY prefix?"""
    # Accept "1.4 Headless..." or "1.4: Headless..." or "1.4. Headless..."
    return bool(re.match(rf'^{re.escape(num)}[\s.:]+', title))


def fix_notebook(path, write=False):
    nb_path = Path(path)
    m = re.match(r'^(\d+\.\d+)', nb_path.stem)
    if not m:
        return 'no-number', None
    num = m.group(1)

    nb = json.load(open(nb_path))
    h1 = get_h1_info(nb)

    if h1 is None:
        # Insert a new H1 markdown cell at the top
        title = derive_title_from_filename(nb_path.stem)
        new_cell = {
            "cell_type": "markdown",
            "id": uuid.uuid4().hex[:8],
            "metadata": {},
            "source": [f"# {title}"],
        }
        nb['cells'].insert(0, new_cell)
        action = f"inserted H1: '# {title}'"

    else:
        ci, li, title = h1
        if has_correct_prefix(title, num):
            return 'ok', None
        # Prepend the number to the existing H1
        new_title = f"{num} {title}"
        c = nb['cells'][ci]
        src = c['source']
        if isinstance(src, list):
            # Find the line in source list and rewrite
            for idx, raw in enumerate(src):
                if raw.lstrip().startswith('# ') and not raw.lstrip().startswith('## '):
                    prefix_indent = raw[:len(raw) - len(raw.lstrip())]
                    src[idx] = f"{prefix_indent}# {new_title}" + (
                        '\n' if raw.endswith('\n') else '')
                    break
            c['source'] = src
        else:
            # String source — single replacement
            c['source'] = re.sub(
                r'^(\s*)# (.*)$',
                lambda mm: f"{mm.group(1)}# {new_title}" if mm.group(2).strip() == title else mm.group(0),
                src, count=1, flags=re.MULTILINE)
        action = f"prepended: '# {title}' → '# {new_title}'"

    if write:
        with open(nb_path, 'w') as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
            f.write('\n')
    return 'changed', action


def main():
    write = '--write' in sys.argv
    print(f"Mode: {'WRITE' if write else 'DRY-RUN'}")
    print()

    nbs = sorted(
        list(Path('docs/tut').rglob('*.ipynb')) +
        list(Path('tutorials').rglob('*.ipynb'))
    )
    nbs = [p for p in nbs if '.ipynb_checkpoints' not in str(p)
           and not p.name.startswith('.')]

    changed = 0
    ok = 0
    skipped = 0
    for p in nbs:
        status, action = fix_notebook(p, write=write)
        if status == 'no-number':
            skipped += 1
        elif status == 'ok':
            ok += 1
        elif status == 'changed':
            changed += 1
            print(f"  · {p}")
            print(f"      {action}")

    print()
    print(f"Changed: {changed} | Already OK: {ok} | Skipped (no number): {skipped}")
    if not write:
        print("\nDry-run only. Re-run with --write to apply.")


if __name__ == '__main__':
    main()
