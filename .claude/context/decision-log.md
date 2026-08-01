# Decision log

> **Before adding an entry — this file is public.** It is committed,
> searchable, and permanent, like every other file in the repo. Write only
> what you would be comfortable seeing quoted, out of context, by someone
> outside the project.
>
> Record **technical facts and the reasoning behind them**. Leave out:
>
> - strategy, positioning, roadmap intent, or anything about adoption,
>   competitors, or other projects beyond neutral technical fact;
> - commentary about people — contributors, maintainers, reviewers — beyond
>   standard attribution (name + link). No characterisations, no assessments
>   of anyone's work or motives, no notes on how a contribution was handled;
> - anything from a private conversation with the maintainer, including how
>   or why a piece of work was prioritised;
> - self-narration ("we decided to…", "we accepted…") where a plain statement
>   of the technical choice would do.
>
> If it belongs in chat with the maintainer, it stays in chat. When in doubt,
> write the shorter, drier version — or leave it out. See also the
> "Public commits, PRs, and files" section of `CLAUDE.md`.

Append-only record of **decisions and deferrals** — the things
`git log` doesn't capture.

Git already records *what* changed and PRs record *how*. What gets lost is
**why one approach was chosen over the alternative**, and **what was
deliberately not done**. Those are the expensive things to reconstruct six
months later, usually at the moment someone is about to undo them.

Scope rules, so this stays useful instead of becoming a diary:

- One entry per batch of work that made a **non-obvious choice** or left a
  **deliberate deferral**. Routine fixes need no entry — the PR is enough.
- Record the **road not taken** and why. That's the load-bearing part.
- Link PR/issue numbers rather than restating them.
- Keep it factual and terse — see the callout above.
- Newest entry at the top.

Related: `lessons-learned.md` is for things that *bit us in production*;
this file is for choices we made on purpose.

---

## 2026-08-01 — design-rule checking: what the rules assume, and what they refuse to claim

PR #1168. Issue #1169.

### `ground-continuity` reports a split, not a floating island

The obvious formulation of the rule — "the ground plane must be one
connected sheet, anything else is floating" — is wrong here, and asserting
it would have made the rule actively misleading.

The check works on one layer at a time, because that is the only way the
overlap and spacing rules can avoid flagging every airbridge as a short.
But an airbridge is also the standard way to *reconnect* ground regions
that a ring of CPW gaps has isolated. On the README hero chip the rule
finds a 2-way split: the ground inside the qubit ring, tied back to the
outer ground by airbridges on layer 30, which a layer-1 check cannot see.

So the rule is a WARNING that reports the split and says explicitly that
it sees only same-layer metal. A split with bridges over every boundary is
a correct design; a split without them is not. The finding tells you which
question to ask rather than answering it wrongly.

Not done: cross-layer connectivity, which would let the rule distinguish
the two cases. It needs a model of which layers are galvanically joined —
`layer_start` / `layer_end` on the chip is not enough, since an airbridge
spans without shorting what it passes over. Left on the roadmap.

`max_void_size` (arXiv:2604.11379 R9's 50 µm parasitic-cavity threshold)
is implemented but **off by default**: enabled, it flags 10 voids on the
hero chip, almost all of them transmon pockets — deliberate voids far
wider than 50 µm. A rule whose default output is dominated by
false positives trains people to ignore it.

### Thresholds are cited or labelled as guesses

`metal-spacing` (2 µm) and `cpw-gap` (3 µm) come from arXiv:2604.11379
(R8, R1). `qubit-clearance` (3× CPW width) does not come from anywhere —
it is a project heuristic, and both the docstring and the tutorial say so
in those words. The alternative, quietly shipping it alongside the cited
values, would have implied a provenance it does not have.

### `QDesignCheck` deprecated rather than fixed or deleted

It uses `shapely.crosses`, which is false when one geometry is wholly
inside the other — so it misses the common case of a trace overlapping
within another trace's width. Fixing that means changing what it detects,
which is a behaviour change on a public class for no gain over
`validation`. Removing it breaks anyone importing it. So: a
`DeprecationWarning` on construction, behaviour untouched, no removal
date.

### Die outline: drawn in the shared renderer, and it changes framing

`QMplRenderer.render` draws it, not the Qt layer, so `qm.view` and
`MetalGUI` get it from one place and `_gui/` (a hard-touch zone) stays
untouched.

It is a patch rather than a line, so it participates in autoscaling — a
design whose components sit well inside the die is now framed to the die.
That is the point of the feature, and it is a visible default change for
small designs. The alternative, `ax.add_artist` (drawn but not
autoscaled), was rejected: for a correctly-laid-out chip the outline would
then fall just outside the view and never be seen, which is precisely the
case the feature exists for. Escape hatch is
`qm.view(design, chip_outline=False)`.

---

## 2026-07-27 — `to_python_script` robustness, and the ruff CI break

PRs #1159, #1160, #1161. Issues closed: #1157, #1134, #1127, #1130, #1135.

### Exported-script event loop

`QDesign.to_python_script()` generated a script that never started the Qt
event loop, so a standalone run opened the MetalGUI window and exited
immediately. #1159 added the event loop; #1160 hardened it and added test
coverage.

An unconditional `gui.qApp.exec_()` is wrong in three ways that only appear
across install variants, which is why the final guard has three conditions
rather than one:

| | |
|---|---|
| `exec_()` | PySide6 deprecated alias for `exec()` |
| unconditional call | blocks on *import*, and inside an existing Qt loop (Jupyter `%gui qt`) |
| `gui.qApp` may be `None` | headless machines where no `QApplication` could be built (`main_window_base._setup_qApp`) |

Result: `if __name__ == "__main__" and gui.qApp is not None: gui.qApp.exec()`.

**Deferred:** in `QComponent.to_script`, a component name that is not a valid
Python identifier makes the generated *variable name* fall back to the full
module path (`qiskit_metal.qlibrary...`). That is what made #1157 (missing
`import qiskit_metal`) possible. Adding the import resolves it; changing the
fallback would change generated variable names, so the fallback was left as
is deliberately.

### Ruff rule set is now pinned by config, not by ruff's release schedule

`lint` and `format` went red on every open PR at once, in files nobody had
touched. Cause: `[tool.ruff.lint]` declared only `ignore`, never `select`, so
ruff applied its **default** rule set — and that default is version-dependent.
CI installs the newest ruff, which moved to 0.16.0 and expanded the defaults
from ~0 findings to **3837**.

Fixed in #1161 by declaring `select` explicitly (the rule groups the repo was
actually enforcing) and excluding `*.md` (0.16 began reformatting Python code
blocks embedded in Markdown, which would have rewritten the README
quick-start). Config only; verified under both ruff 0.15.22 and 0.16.0.

**Deliberately not done: adopting ruff 0.16's new rules.** ~3.8k findings,
~2k of which need `--unsafe-fixes` or manual work, much of it inside the
`_gui/` and Ansys hard-touch zones that cannot be validated here. Adopting a
rule group is now a one-line, reviewable change to `select`. Assessment of
what each group would cost, and which ones contain real bugs rather than
style, is in the ruff-0.16 section below.

### Ruff 0.16: what the deferred rules actually are

Recorded so the next person doesn't have to re-derive it.

**Contains genuine latent bugs — worth doing first:**

- `W605` invalid escape sequence (22, all auto-fixable). Two are live
  regexes written as non-raw strings:
  `re.sub("\W|^(?=\d)", ...)` in `toolbox_python/utility_functions.py`, and the
  MetalGUI `.. image::` thumbnail scanner in
  `_gui/.../file_model_qlibrary.py`. These work today only because Python
  preserves unknown escapes; that is deprecated and becomes a syntax error.
  The rest are LaTeX in non-raw docstrings.
- `B006` mutable argument default (16, needs `--unsafe-fixes`). Classic
  shared-state bug class. Sites include `designs/design_base.py`,
  `renderer_elmer/`, and `renderer_ansys/` (hard-touch).

**Style only — no runtime behavior change:**
`C408` unnecessary `dict()`/`list()` calls (1661, the bulk of the noise),
`UP006` (165) / `UP045` (146) / `UP007` (145) / `UP035` (85) typing
modernization, `RUF013` implicit `Optional` (119), `B018` useless expression
(57), `SIM102` (55), `PIE790` (51), `SIM118` (40), `PERF102` (27),
`UP031` (27).

Counts are per-rule and reproducible with
`uvx ruff@0.16.0 check --select <RULE> --statistics`.

**Risky for this repo specifically:**

- `I001` unsorted imports (366 findings across **283 files**, including
  `qiskit_metal/__init__.py`, `_gui/__init__.py`, `_gui/main_window*.py`).
  Import *order* is load-bearing here because of the lazy-Qt design — the
  package must import without PySide6. Auto-sorting these risks breaking the
  lite/headless path in a way that only `tests-lite` would catch. Do this one
  alone, never bundled.
- `RUF012` mutable class default (41). Would flag `default_options` on
  `QComponent` subclasses, which is the library's core idiom. Adopting it
  means annotating them `ClassVar` — a wide, mechanical change to the public
  component surface. Probably not worth it.
- `BLE001` blind except (250). Many are deliberate defensive catches around
  COM/Qt calls (see #1132). Would need case-by-case review, not a sweep.

Suggested order if picked up: `W605` → `B006` → the pure-style groups → and
`I001` on its own, gated on `tests-lite` passing.
