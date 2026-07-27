# Decision log

Append-only record of **decisions and deferrals** — the things
`git log` doesn't capture.

Git already records *what* changed and PRs record *how*. What gets lost is
**why we chose this over the alternative**, and **what we deliberately did
not do**. Those are the expensive things to reconstruct six months later,
usually at the moment someone is about to undo them.

Scope rules, so this stays useful instead of becoming a diary:

- One entry per batch of work that made a **non-obvious choice** or left a
  **deliberate deferral**. Routine fixes need no entry — the PR is enough.
- Record the **road not taken** and why. That's the load-bearing part.
- Link PR/issue numbers rather than restating them.
- Keep it factual and terse (see the "public commits" section of
  `CLAUDE.md`). No strategy, no commentary about people.
- Newest entry at the top.

Related: `lessons-learned.md` is for things that *bit us in production*;
this file is for choices we made on purpose.

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
