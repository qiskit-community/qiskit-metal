---
name: tutorial-notebook
description: Write, extend or refresh a Quantum Metal tutorial notebook or a series of them -- structure and voice, a shared resource module, generating notebooks from a builder script, executing them reliably, reviewing every figure, keeping stored outputs clean, and registering them in the docs. Use when asked to create a tutorial, turn an analysis or a paper into notebooks, or re-run and fix existing notebooks.
---

# Writing tutorial notebooks

A tutorial is judged by its stored outputs: the docs site renders them
without executing anything. So the job is not done when the code runs —
it is done when every printed number, every figure and every sentence
agree with each other and with what a reader will get. The rules below
come from the five-notebook series `docs/tut/4-Analysis/4.41`–`4.45`.

## 1. Where things go

- Notebooks live once, under `docs/tut/<section>/` (numbered, hyphenated
  names) or `docs/circuit-examples/` — see "Tutorial notebooks" in
  `CLAUDE.md`. Shared helper code and input files: `docs/tut/resources/`.
- Register new notebooks: an `nbgallery` entry or glob in
  `docs/tut/index.rst`; pure-Python ones (no Ansys, gmsh, Elmer; < 3 min)
  on `_dev/notebooks-auto-refresh.txt`, the others in its external-gated
  comment block; one line in `changelog.md` under Unreleased.
- If another agent is editing the repository, work in your own git
  worktree and branch, and fast-forward onto theirs at the end.

## 2. Structure of each notebook

Title; Colab/Binder badges pointing at the notebook's own `docs/` path;
a "What you need" callout (dependencies, run time, memory); a short
motivation; "What you'll learn" (3–5 bullets); numbered sections, each
opening with the physical picture before code; a summary (a small table
of "this notebook vs reference" works well); "Where to go next"
(including one or two things to try); references with DOIs.

A series gets a table of all notebooks (what each computes, the solver,
the run time) in its first notebook, and a module README.

## 3. Shared code in a resource module

- Put reusable code (geometry builder, solver, fits) in one module under
  `docs/tut/resources/<name>/`, written to be read: sections in the order
  the notebooks use them, docstrings with the equations. Keep the teaching
  code (the formula being taught) in the notebook itself.
- Each notebook finds it relative to itself and falls back to downloading
  it from the repository's `main` branch (for Colab).
- The Colab install cell must cover system libraries too: pip cannot
  install them, and gmsh's wheel needs libGLU and a few X11 libraries
  (`lessons-learned.md`, "gmsh on Colab"). Try the notebook in Colab once
  before announcing it.
- Put the reference numbers you compare against (a paper's values) in the
  module as data, so every notebook prints "ours vs reference" from one
  source.
- Lint it like `src/` (`ruff check`, `ruff format`).

## 4. Generate, execute, review

- **Generate notebooks from a builder script** (cells as strings, written
  with `nbformat`) kept outside the repo, so a change is an edit and a
  rebuild, not hand-editing JSON. For a markdown-only change after an
  expensive run, patch the executed notebook directly and the builder too.
- **Execute in the notebook's own folder** (`nbclient` with
  `resources={"metadata": {"path": folder}}`), with a kernel registered
  inside the environment that has the dependencies
  (`python -m ipykernel install --prefix <venv> --name <name>`). The
  default `python3` kernelspec can resolve to a different Python; a
  notebook that imports only NumPy will not show it, the next one will.
- **A cell with no output after a long run is a dead kernel**, not a
  success. Check every executed notebook for errors and for missing
  outputs, not just the exit code.
- **Look at every figure** (dump the PNGs and view them). Figure-level bugs
  that tests did not catch: a sign error in an analytic overlay, arrows
  too small to see, a colormap saturated by one feature (use a log norm),
  holes in a mesh slice where the plane went through nodes, a legend over
  an inset.
- Heavy notebooks: state run time and memory up front; give one knob for a
  lighter run (mesh size, a `FINE` flag). Measure peak memory before
  claiming it.

## 5. Stored outputs are public

- No local paths, user names, machine names or folder names in outputs,
  markdown or module text. Grep the notebooks before committing
  (`/Users/`, `/home/`, temp paths, the user name).
- No log noise: quiet expected INFO messages at the source (e.g. set the
  logger level around the call that emits them) rather than deleting
  outputs by hand.
- Markdown claims must match printed outputs. Fill summary tables after
  the final run, with rounding that survives run-to-run variation (parallel
  meshers are not bit-reproducible).
- Report disagreements with a reference plainly, with both numbers.
- **Stored outputs of external-gated notebooks (Ansys, ElmerFEM, heavy
  runs) are reference answers.** Edit their markdown without re-executing
  (insert or change cells as JSON, keep outputs byte-identical, check the
  diff is insert-only); never regenerate them to "refresh".
- Notebooks that run a solver carry the "Other simulation pathways" callout
  pointing to `docs/simulation-pathways.rst`; add it to a new one.

## 6. Before handing over

All notebooks re-run top to bottom in a fresh kernel; figures reviewed;
docs registration and changelog in place; the solver or helper module
documented where the next person will look (a module README, a
`docs/architecture/` note for anything substantial, and a
`lessons-learned.md` entry for each pitfall that cost time).

## Where the rest lives

- `CLAUDE.md`, "Tutorial notebooks" — the single-tree layout, stored
  outputs, `exclude_patterns`.
- `.claude/commands/refresh-tutorial.md` — the no-Qt callout for GUI
  tutorials.
- `.claude/skills/chip-simulation/SKILL.md` — the analysis side of a
  simulation tutorial.
- Worked examples: `docs/tut/4-Analysis/4.41`–`4.45` (a paper
  reproduction with a shared solver module),
  `docs/circuit-examples/F.Small-quantum-chips/53-…` and `54-…` (a builder
  module shared by two notebooks).
