# /refresh-tutorial — apply the standard no-Qt callout to a tutorial

The callout makes the headless rendering path discoverable from
every GUI-using tutorial. This is the same pattern applied to 1.1,
1.2, and all of `2 From components to chip/` in PRs #1061 and
#1062. Use this command when:

- Adding the callout to a folder we haven't covered yet (3-Renderers,
  4-Analysis, Appendix A/B/C, quick-topics)
- A new tutorial lands and needs the callout

## What the callout looks like

A single markdown cell inserted as the second cell of the notebook
(after the title):

```markdown
> 💡 **Using this tutorial without the Qt GUI**
> 
> This tutorial uses the desktop `MetalGUI`. To follow along on
> Colab, Binder, JupyterHub, or any environment where Qt isn't
> available, **replace any `gui.rebuild()` / `gui.screenshot()`
> call with `qm.view(design)`** — it renders the design to a
> matplotlib `Figure` you can display inline or save with
> `fig.savefig(...)`.
> 
> See [1.4 Headless quick view](...) for a complete runnable
> walkthrough and `docs/headless-usage.rst` for the full reference.
```

The relative link path to `1.4` depends on which folder the
tutorial lives in. For `2 From components to chip/A/.../*.ipynb`
the path is:

```
../../1%20Overview/1.4%20Headless%20quick%20view%20%28no%20Qt%20GUI%29.ipynb
```

For a tutorial directly under `tutorials/3 Renderers/*.ipynb`:

```
../1%20Overview/1.4%20Headless%20quick%20view%20%28no%20Qt%20GUI%29.ipynb
```

## Procedure

### 1. Decide scope

Either a single notebook or a whole folder. Don't try to do all
remaining tutorials in one PR — the diff gets too noisy to review.
One folder per PR is the sweet spot.

Current state of callouts (as of v0.6.1):

| Folder | Callout applied? |
|--------|------------------|
| `1 Overview/` | ✅ 1.1, 1.2 (1.3 skipped — empty; 1.4 is the canonical headless) |
| `2 From components to chip/` (all of A, B, C, D) | ✅ |
| `3 Renderers/` | ❌ |
| `4 Analysis/` | ❌ |
| `Appendix A Full design flow examples/` | ❌ |
| `Appendix B Quick topics/` | ❌ |
| `Appendix C Circuit examples/` | ❌ |

### 2. Write the injection script

```python
import json
from pathlib import Path

# Adjust the relative path based on folder depth!
RELATIVE_LINK = ("../../1%20Overview/"
                 "1.4%20Headless%20quick%20view%20%28no%20Qt%20GUI%29.ipynb")

CALLOUT = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "> 💡 **Using this tutorial without the Qt GUI**\n",
        "> \n",
        "> This tutorial uses the desktop `MetalGUI`. To follow "
        "along on Colab, Binder, JupyterHub, or any environment "
        "where Qt isn't available, **replace any `gui.rebuild()` / "
        "`gui.screenshot()` call with `qm.view(design)`** — it "
        "renders the design to a matplotlib `Figure` you can "
        "display inline or save with `fig.savefig(...)`.\n",
        "> \n",
        f"> See [1.4 Headless quick view]({RELATIVE_LINK}) for a "
        "complete runnable walkthrough and "
        "[`docs/headless-usage.rst`](../../../docs/headless-usage.rst) "
        "for the full reference."
    ]
}

# Adjust target folder
TARGET = Path("tutorials/3 Renderers")
notebooks = sorted(TARGET.rglob("*.ipynb"))

for nb_path in notebooks:
    with open(nb_path) as f:
        nb = json.load(f)
    # Idempotent: skip if callout already present
    first_md = next((c for c in nb["cells"] if c["cell_type"] == "markdown"), None)
    if first_md and "Using this tutorial without the Qt GUI" in "".join(first_md["source"]):
        print(f"  SKIP (has callout): {nb_path.name}")
        continue
    nb["cells"].insert(1, CALLOUT)
    with open(nb_path, "w", encoding="utf-8") as f:
        # CRITICAL: ensure_ascii=False preserves unicode (χ, ε, etc.)
        # — without it the diff balloons with \uXXXX escapes.
        # See .claude/context/lessons-learned.md "json.dump".
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"  added: {nb_path}")
```

### 3. Run and verify

```bash
python3 your_injection_script.py
git diff --stat tutorials/
```

Expect: N files, ~11 insertions each (the callout is 11 lines),
**0 deletions**. If you see deletions, you broke an existing cell.

### 4. Validate JSON + cell count

```bash
python3 -c "
import json, glob
for p in sorted(glob.glob('tutorials/3 Renderers/**/*.ipynb', recursive=True)):
    with open(p) as f:
        nb = json.load(f)
    has = any('Using this tutorial without the Qt GUI' in ''.join(c['source'])
              for c in nb['cells'] if c['cell_type'] == 'markdown')
    print(f'{\"OK\" if has else \"MISSING\"}: {p}')
"
```

### 5. Commit, push, open PR

```bash
git add tutorials/
git commit -m "tutorials: add no-Qt callouts to <folder> (N notebooks)"
git push -u origin claude/tutorial-refresh-<folder>
```

Then open a PR with body matching the pattern from PRs #1061 and
#1062 (purely-additive, no notebooks re-executed, etc.).

## Critical pitfalls

### `ensure_ascii=False`

If you forget this and save a notebook containing `χ` or `ε`, the
JSON serialiser escapes them to `χ` and the diff balloons with
hundreds of bogus lines. See `lessons-learned.md`.

### Don't re-execute the notebook

The original GUI screenshots are part of the documentation value.
Re-executing would discard them. Inject the callout in place; leave
all outputs alone.

### Relative link depth

`../../` for tutorials inside `2 From components to chip/X/...`
(two levels deep), but `../` for tutorials directly under
`tutorials/3 Renderers/`. Get the depth wrong and the link
404s.

### Idempotency

Always check whether the callout is already present before
inserting — otherwise re-running on the same folder duplicates the
callout. The script template above handles this.

## What this command is NOT

- Not a full notebook rewrite. The GUI-driven path stays as-is;
  only the callout points users at the headless alternative.
- Not a re-execution. Outputs and screenshots are preserved
  exactly.
- Not a way to fix individual notebook bugs. If the tutorial has a
  real issue, file it separately.
