# Archived: Read the Docs config

This directory holds the Read the Docs (RTD) build configuration
that was developed and **proven working** in PR
[#1069](https://github.com/qiskit-community/qiskit-metal/pull/1069),
but **not adopted** as the current docs host.

Docs publishing currently lives on **GitHub Pages** via
`.github/workflows/docs.yml`, deployed to
https://qiskit-community.github.io/qiskit-metal/. Years of SEO,
inbound links, and search-engine authority pointed at that URL
made a hard cutover too expensive for now.

This config is archived here so a future maintainer can revive it
in minutes if/when the rebrand cutover, per-PR doc previews, or
the versioned-docs UX become worth the switch.

## How to revive

1. `git mv docs/_archive/readthedocs/readthedocs.yaml .readthedocs.yaml`
2. Sign in at https://readthedocs.org/ → **Import a Project** →
   `qiskit-community/qiskit-metal`, project name `quantum-metal`
3. **Important** — `qiskit-community` org restricts third-party
   GitHub Apps. Have an org owner install the Read the Docs
   GitHub App on the org (Settings → Integrations →
   Installations) or whitelist it under
   Settings → Third-party Access. Without this, RTD can't attach
   the webhook and you only get manual rebuilds.
4. Trigger a build on the RTD dashboard. First build takes
   ~5–10 min.
5. Update the three URL sites that point at the GH Pages address
   so they show `https://quantum-metal.readthedocs.io/`:
   - `pyproject.toml` `urls.documentation`
   - `src/qiskit_metal/toolbox_metal/about.py` `open_docs()` default
   - `src/qiskit_metal/_gui/main_window.py` `open_web_help()`
6. Decide on the transition window for the existing GH Pages
   site. Recommended: leave it running for 2–4 weeks with a
   banner pointing to the new URL, then delete
   `.github/workflows/docs.yml` and disable Pages in repo
   settings.

## What's known to work

PR #1069 reached a green RTD build on the
`claude/docs-to-rtd` branch. The config in this directory is the
last-known-good version, with all fixes incorporated:

- **`uv sync --group docs`** — uses the PEP 735 dependency group
  declared in `[dependency-groups]` of `pyproject.toml`, not a
  PEP 631 extra. (`--extra docs` fails with "extra not defined";
  the local `tox -e docs` path uses the same group.)
- **`QT_API=pyside6`** — required because
  `renderers/__init__.py:99` eagerly imports `mpl_canvas` during
  docs build, which pulls `matplotlib.backends.backend_qt5agg`.
  Without the hint, matplotlib probes for PyQt5/PySide2 and
  fails. RTD's minimal image only has PySide6 (the project's
  binding); the hint makes the legacy qt5agg alias resolve to
  the modern Qt-agnostic backend_qtagg. This is set in
  `docs/conf.py`, NOT here, so it works for any docs build path.
- **System libs in `apt_packages`**: `graphviz`, `pandoc`,
  `libglu1-mesa`, `libxcursor1`, `libxft2`, `libxinerama1`,
  `libxrender1`, `libfontconfig1`. The gmsh Python wrapper
  dlopens libGLU and X11 libs at module load time; GH Actions
  runners have these by default, RTD's image does not.

## Why these issues hit RTD but not GH Pages

GHA runners come pre-loaded with hundreds of system libraries
and ship more of the python ecosystem implicitly through their
toolchain caches. RTD's build image is minimal and only installs
what `apt_packages` declares. The GH Pages workflow currently
gets a number of system deps "for free" that it never asks for —
which is convenient but means the workflow's dep declaration
doesn't reflect reality.

If the v0.7.0 lite-by-default flip ships before any RTD revival,
many of these workarounds become unnecessary — moving pyside6,
gmsh, and pyaedt out of base `[project.dependencies]` means
``import qiskit_metal`` during a docs build won't pull them in at
all, so no `QT_API` hint, no libGLU apt deps, no `mpl_canvas`
import chain to worry about.

## Related history

- Original migration PR (with full discussion of pro/con, red-team,
  and what made us choose the parallel-and-decide-later path):
  https://github.com/qiskit-community/qiskit-metal/pull/1069
- The `tests-lite` CI job in `.github/workflows/main.yml` already
  proves the codebase runs without Qt / gmsh / pyaedt — that's
  the foundation for the lite flip.
