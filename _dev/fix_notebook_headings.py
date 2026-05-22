"""Demote rogue secondary H1s to H2 so notebooks have exactly one H1 (the title).

Why: nbsphinx renders any H1 inside a notebook as a top-level page entry in the
docs sidebar. Notebooks with multiple H1s show their internal "sections" as
sibling pages to the notebook itself in the Tutorials TOC — e.g. "QComponent
Default Options" appearing AT THE SAME LEVEL as "2.01 How to use a QComponent"
rather than nested under it.

Same fix typically resolves the "Inconsistent title style: skip from level 2
to 4" docutils errors too, because those skips often originated from
``# rogue-h1 / ### sub-item`` patterns that, after this script, become
``## now-h2 / ### sub-item`` (a clean 2→3 progression).

Run from the repo root:
    python3 _dev/fix_notebook_headings.py            # dry-run
    python3 _dev/fix_notebook_headings.py --write    # apply
"""

import json
import re
import sys
from pathlib import Path

H1_LINE_RE = re.compile(r'^(\s*)# (?!#)(.+?)\s*$')


def demote_lines_in_source(src):
    """Return (new_src, demoted_titles). Keep first H1 untouched, demote rest."""
    lines = src if isinstance(src, list) else src.split('\n')
    new_lines = []
    seen_first_h1 = False
    demoted = []
    in_code_fence = False  # don't touch lines inside ``` fenced blocks
    for raw in lines:
        line = raw.rstrip('\n')
        # Track ```fenced``` regions — markdown headings inside them are literal
        if line.lstrip().startswith('```'):
            in_code_fence = not in_code_fence
            new_lines.append(raw)
            continue
        if in_code_fence:
            new_lines.append(raw)
            continue
        m = H1_LINE_RE.match(line)
        if m:
            if not seen_first_h1:
                seen_first_h1 = True
                new_lines.append(raw)
            else:
                # Demote: prepend one more '#' to make it H2
                indent, text = m.group(1), m.group(2)
                trail = '\n' if raw.endswith('\n') else ''
                new_lines.append(f"{indent}## {text}{trail}")
                demoted.append(text[:60])
            continue
        new_lines.append(raw)
    new_src = new_lines if isinstance(src, list) else '\n'.join(new_lines)
    return new_src, demoted


def fix_notebook(path, write=False):
    nb = json.load(open(path))
    seen_first_h1_across_cells = False
    all_demoted = []
    for c in nb['cells']:
        if c['cell_type'] != 'markdown':
            continue
        src = c['source']
        # We need state across cells — process cell-by-cell tracking whether
        # we've already seen the title H1 anywhere.
        lines = src if isinstance(src, list) else src.split('\n')
        new_lines = []
        in_code_fence = False
        for raw in lines:
            line = raw.rstrip('\n')
            if line.lstrip().startswith('```'):
                in_code_fence = not in_code_fence
                new_lines.append(raw)
                continue
            if in_code_fence:
                new_lines.append(raw)
                continue
            m = H1_LINE_RE.match(line)
            if m:
                if not seen_first_h1_across_cells:
                    seen_first_h1_across_cells = True
                    new_lines.append(raw)
                else:
                    indent, text = m.group(1), m.group(2)
                    trail = '\n' if raw.endswith('\n') else ''
                    new_lines.append(f"{indent}## {text}{trail}")
                    all_demoted.append(text[:60])
                continue
            new_lines.append(raw)
        if isinstance(src, list):
            c['source'] = new_lines
        else:
            c['source'] = '\n'.join(new_lines)

    if write and all_demoted:
        with open(path, 'w') as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
            f.write('\n')
    return all_demoted


def main():
    write = '--write' in sys.argv
    print(f"Mode: {'WRITE' if write else 'DRY-RUN'}")
    print()
    nbs = sorted(
        list(Path('docs/tut').rglob('*.ipynb'))
        + list(Path('tutorials').rglob('*.ipynb'))
    )
    nbs = [p for p in nbs if '.ipynb_checkpoints' not in str(p)
           and not p.name.startswith('.')]

    total_files = 0
    total_demoted = 0
    for p in nbs:
        demoted = fix_notebook(p, write=write)
        if demoted:
            total_files += 1
            total_demoted += len(demoted)
            print(f"  · {p}")
            for t in demoted[:5]:
                print(f"      # → ##  '{t}'")
            if len(demoted) > 5:
                print(f"      ... and {len(demoted)-5} more")

    print()
    print(f"Files touched: {total_files} | Total H1→H2 demotions: {total_demoted}")
    if not write:
        print("\nDry-run only. Re-run with --write to apply.")


if __name__ == '__main__':
    main()
