"""Merge outputs from tutorials/ → docs/tut/ for notebooks where cells match by source.

Strategy:
- For each code cell in docs/tut/, find a code cell in tutorials/ with identical source
- If found AND tutorials/ cell has outputs AND docs/tut/ cell has no/fewer outputs:
  - Copy tutorials/'s outputs into docs/tut/'s cell
- Leave all other cells alone (markdown, structural fixes, new cells)

Dry-run mode: report what WOULD change without writing. Default.
Write mode: --write flag to actually modify docs/tut/ notebooks.
"""

import json
import sys
from pathlib import Path


def srcjoin(c):
    s = c.get('source', '')
    return ''.join(s) if isinstance(s, list) else s


def build_source_to_outputs(nb):
    """Map: normalized source → list of outputs (from cells that have outputs)."""
    idx = {}
    for c in nb['cells']:
        if c['cell_type'] != 'code':
            continue
        outs = c.get('outputs') or []
        if not outs:
            continue
        key = srcjoin(c).strip()
        if key and key not in idx:
            idx[key] = outs
    return idx


def count_images(outputs):
    n = 0
    for o in outputs:
        data = o.get('data', {})
        for mime in ('image/png', 'image/svg+xml', 'image/jpeg'):
            if mime in data:
                n += 1
                break
    return n


def merge_outputs(docs_path, tut_path, write=False, mode='conservative'):
    """Returns (cells_updated, outputs_delta). Writes docs_path if write=True.

    mode='conservative' — only fill cells where docs/tut/ has NO outputs.
    mode='replace_if_more' — also replace when tutorials/ has more outputs OR more images.
    """
    docs_nb = json.load(open(docs_path))
    tut_nb = json.load(open(tut_path))

    tut_idx = build_source_to_outputs(tut_nb)

    cells_updated = 0
    outputs_delta = 0
    for c in docs_nb['cells']:
        if c['cell_type'] != 'code':
            continue
        key = srcjoin(c).strip()
        if not key or key not in tut_idx:
            continue
        existing = c.get('outputs') or []
        new_outs = tut_idx[key]

        should_replace = False
        if not existing:
            should_replace = True
        elif mode == 'replace_if_more':
            if len(new_outs) > len(existing) or count_images(new_outs) > count_images(existing):
                should_replace = True

        if should_replace:
            outputs_delta += len(new_outs) - len(existing)
            c['outputs'] = new_outs
            cells_updated += 1

    if write and cells_updated:
        with open(docs_path, 'w') as f:
            json.dump(docs_nb, f, indent=1, ensure_ascii=False)
            f.write('\n')

    return cells_updated, outputs_delta


# Map: docs/tut path → tutorials path (manually built from earlier inventory)
PAIRS = [
    # Section 1
    ("docs/tut/1-Overview/1.1-Bird's-eye-view-of-Qiskit-Metal.ipynb",
     "tutorials/1 Overview/1.1 Bird's eye view of Qiskit Metal.ipynb"),
    ("docs/tut/1-Overview/1.2-Quick-start.ipynb",
     "tutorials/1 Overview/1.2 Quick start.ipynb"),
    ("docs/tut/1-Overview/1.3-Saving-Your-Chip-Design.ipynb",
     "tutorials/1 Overview/1.3 Saving Your Chip Design.ipynb"),
    ("docs/tut/1-Overview/1.4-Headless-quick-view-(no-Qt-GUI).ipynb",
     "tutorials/1 Overview/1.4 Headless quick view (no Qt GUI).ipynb"),
    ("docs/tut/1-Overview/1.5-Parametric-design---iterate-and-compare.ipynb",
     "tutorials/1 Overview/1.5 Parametric design - iterate and compare.ipynb"),
    ("docs/tut/1-Overview/1.6-QComponent-shape-library.ipynb",
     "tutorials/1 Overview/1.6 QComponent shape library.ipynb"),
    # Section 2
    ("docs/tut/2-From-components-to-chip/2.01-How-to-use-a-QComponent.ipynb",
     "tutorials/2 From components to chip/A. Using QComponents/2.01 How to use a QComponent.ipynb"),
    ("docs/tut/2-From-components-to-chip/2.02-How-to-copy-a-QComponent.ipynb",
     "tutorials/2 From components to chip/A. Using QComponents/2.02 How to copy a QComponent.ipynb"),
    ("docs/tut/2-From-components-to-chip/2.11-Routing-101.ipynb",
     "tutorials/2 From components to chip/B. Routing between QComponents/2.11 Routing 101.ipynb"),
    ("docs/tut/2-From-components-to-chip/2.12-Simple-Meander.ipynb",
     "tutorials/2 From components to chip/B. Routing between QComponents/2.12 Simple Meander.ipynb"),
    ("docs/tut/2-From-components-to-chip/2.13-Hybrid-Auto-and-AStar.ipynb",
     "tutorials/2 From components to chip/B. Routing between QComponents/2.13 Hybrid Auto and AStar.ipynb"),
    ("docs/tut/2-From-components-to-chip/2.14-Get-them-all-with-MixedRoute.ipynb",
     "tutorials/2 From components to chip/B. Routing between QComponents/2.14 Get them all with MixedRoute.ipynb"),
    ("docs/tut/2-From-components-to-chip/2.21-Design-a-4-qubit-full-chip.ipynb",
     "tutorials/2 From components to chip/C. My first full quantum chip design/2.21 Design a 4 qubit full chip.ipynb"),
    ("docs/tut/2-From-components-to-chip/2.22-Design-100-qubits-programmatically.ipynb",
     "tutorials/2 From components to chip/C. My first full quantum chip design/2.22 Design 100 qubits programmatically.ipynb"),
    ("docs/tut/2-From-components-to-chip/2.23-Modify-chip-options.ipynb",
     "tutorials/2 From components to chip/C. My first full quantum chip design/2.23 Modify chip options.ipynb"),
    ("docs/tut/2-From-components-to-chip/2.31-Create-a-QComponent-Basic.ipynb",
     "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.31 Create a QComponent - Basic.ipynb"),
    ("docs/tut/2-From-components-to-chip/2.32-Create-a-QComponent-Advanced.ipynb",
     "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.32 Create a QComponent - Advanced.ipynb"),
    ("docs/tut/2-From-components-to-chip/2.33-Add-my-QComponent-to-a-reusable-python-file.ipynb",
     "tutorials/2 From components to chip/D. How do I make my custom QComponent/2.33 Add my QComponent to a reusable python file.ipynb"),
    # Section 3
    ("docs/tut/3-Renderers/3.1-Introduction-to-QRenderers.ipynb",
     "tutorials/3 Renderers/3.1 Introduction to QRenderers.ipynb"),
    ("docs/tut/3-Renderers/3.2-Export-your-design-to-GDS.ipynb",
     "tutorials/3 Renderers/3.2 Export your design to GDS.ipynb"),
    ("docs/tut/3-Renderers/3.5-Render-your-design-to-Gmsh.ipynb",
     "tutorials/3 Renderers/3.5 Render your design to Gmsh.ipynb"),
    # Skip 3.3 and 3.4 — docs/tut/ already has more outputs there
]


if __name__ == '__main__':
    write_mode = '--write' in sys.argv
    aggressive = '--replace-if-more' in sys.argv
    mode = 'replace_if_more' if aggressive else 'conservative'
    print(f"Mode: {mode} | {'WRITE' if write_mode else 'DRY-RUN'}")
    print(f"{'notebook':<60} {'cells':>6} {'Δouts':>7}")
    print('-' * 80)
    total_cells, total_outs = 0, 0
    for docs_p, tut_p in PAIRS:
        if not Path(docs_p).exists() or not Path(tut_p).exists():
            print(f"⚠ MISSING: {docs_p if not Path(docs_p).exists() else tut_p}")
            continue
        cells, outs = merge_outputs(docs_p, tut_p, write=write_mode, mode=mode)
        total_cells += cells
        total_outs += outs
        marker = ' ←' if cells > 0 else ''
        print(f"{Path(docs_p).name:<60} {cells:>6} {outs:>+7}{marker}")
    print('-' * 80)
    print(f"{'TOTAL':<60} {total_cells:>6} {total_outs:>+7}")
    if not write_mode:
        print()
        print("Re-run with --write to apply. Add --replace-if-more for aggressive merge.")
