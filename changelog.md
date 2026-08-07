# Changelog Note Scratchpad for Developers

This log is used by developers to jot notes.

For the offical user-facing changelog for a particular release can be found in the correspondent Github release page. For example, you can find the changelog for the `0.0.4` release [here](https://github.com/Qiskit/qiskit-metal/releases/tag/0.0.4)

The changelog for all releases can be found in the release page: [![Releases](https://img.shields.io/github/release/Qiskit/qiskit-metal.svg?style=popout-square)](https://github.com/Qiskit/qiskit-metal/releases)

## Unreleased

### Fixed

- **`TransmonCross` `connector_location='270'`** placed the connector on the east arm instead of the south arm. The rotation chain had no branch above 225 degrees, so 270 matched the `> 135` test. (#1173, closes #1052)
- **`connector_location` now wraps mod 360.** The chain saturated at its top branch, so out-of-range angles landed arbitrarily — `'360'` resolved to south rather than west, `'-90'` to west rather than south. In-range angles, including the half-way values 45/135/225, keep their existing arm.

### Changed

- **`TransmonCrossFL` warns when a connection pad resolves to the south arm** while `make_fl` is True. That arm carries the flux line, and the claw polygon overlaps it. The south arm also carries the junction on the base `TransmonCross`; at default options the claw clears it by ~11um, with the etch region within ~5um. Both constraints are now documented on the class docstrings.

## Quantum Metal v0.8.0 (airbridges + design-rule checking; no breaking changes)

Minor release: two new feature areas, one deprecation, and one default-behaviour
change to the matplotlib viewer. No API breaks. See *Upgrade notes*.

> **Skipped version: there is no 0.7.7.** A `v0.7.7` tag and GitHub Release exist
> on `a7efeeb1`, but that commit's `pyproject.toml` still read `0.7.6`, so the
> publish workflow built a `0.7.6` wheel and PyPI rejected it as a duplicate.
> Nothing was ever published under 0.7.7 — PyPI went 0.7.6 → 0.8.0. The tag is
> left in place rather than rewritten. Tag *after* the version bump merges; this
> is the same ordering that broke v0.6.0 (`.claude/commands/release.md`).

### Added (v0.8.0-only)

- **`Airbridge` QComponent + `route_airbridges` auto-placement.** Bridges are placed on the filleted centreline, idempotently, with `bridge_at_corners` to control corner behaviour. Tutorial 2.15 covers the flow end to end, including GDS export with coloured layers. (#1138, #1142)
- **Experimental 3D airbridges** via layer-stack elevation, with support posts so the route and its bridges connect in a 3D mesh, plus a ready-to-run Elmer capacitance path. (#1144, #1150)
- **`qiskit_metal.validation` — design-rule checking.** `validate(design)` returns a `ValidationResult` of structured `Finding`s; `strict=True` raises `DesignRuleViolation` for build scripts and CI. Seven rules with configurable thresholds: `metal-overlap`, `metal-spacing`, `cpw-gap`, `chip-bounds`, `short-segment`, `qubit-clearance`, `ground-continuity`. Rules are layer-aware (an airbridge crossing a CPW is not a short) and net-aware (a route abutting its own pin is not a short). Defaults follow published superconducting-chip rule sets where one exists; the one project heuristic is labelled as such. Tutorial 2.24 walks a deliberately broken design through detection, fix, threshold tuning, and writing a custom rule. (#1168, #1169)
- **Die outline in the viewer.** `QMplRenderer` draws each chip's extent, so `qm.view` and the Qt `MetalGUI` both show where the chip ends. (#1168)

### Fixed (v0.8.0-only)

- **`RouteMeander` sharp kinks** when `meander_number` is too tight for the requested geometry. (#1167, closes #1086)
- **`RouteMeander` `IndexError`** when the start/end-direction parity adjustment takes `meander_number` from 1 to 0, skipping the zero-meander early return. (#1168)
- **GDS export of routes with short lead segments.** (#1141)
- **Gmsh 3D render of routes with sub-width lead segments.** (#1144)
- **`design.to_python_script()` output** now starts a Qt event loop correctly across install variants. (#1159 by @saschabuehrle, hardened in #1160)
- **Reference designs 2 and 3** placed launchpads 1.76 mm and 3.26 mm outside the default 9×6 mm die, so a corner of ground plane was clipped on every render. Both now set an explicit chip size, and `tests/test_reference_designs.py` gates all three against the design rules. (#1168)

### Deprecated (v0.8.0-only)

- **`QDesignCheck`** — construction emits a `DeprecationWarning`. It detects only crossing outlines, so it misses an overlap where one trace sits entirely inside another, and it is blind to layers and to pin connections. Use `qiskit_metal.validation.validate` instead. The class keeps working; no removal date set. (#1168)

### CI / infrastructure (v0.8.0-only)

- `uv.lock` ↔ `pyproject.toml` consistency guard. (#1137)
- Ruff rule set pinned so a ruff release cannot break CI; the safely-fixable subset of ruff 0.16's expanded defaults adopted, plus a second tier. (#1161, #1163, #1165)
- Decision log for non-obvious choices and deferrals. (#1162, #1164)
- Flaky gmsh meshing test isolated. (#1165)

### Upgrade notes

No API changes. One visible default change: the matplotlib viewer now draws the die outline, and because the outline participates in autoscaling, a design whose components sit well inside the die is framed to the whole die rather than to the components. Pass `qm.view(design, chip_outline=False)`, or set `renderer.options.chip_outline = False`, for the previous framing.

`QDesignCheck` users will see a `DeprecationWarning`; behaviour is unchanged.

## Quantum Metal v0.7.5 (Windows GUI crash fix + routing/qubit fixes; no breaking changes)

Patch release. Additive — no breaking changes.

### Fixed (v0.7.5-only)

- **`MetalGUI` no longer crashes at `show()` on Windows** (the on-screen crash, distinct from the exit-teardown segfault fixed in v0.7.4). Root cause was **persisted-state corruption**: Metal saves window geometry / dock layout to the registry (`HKCU\Software\QiskitMetal\MainWindow`) on close, and after a display-configuration change (tablet-mode toggle, undock, DPI change on 2-in-1 laptops with WDDM 3.2) Qt's `restoreState()` handed `show()` an inconsistent widget tree that fast-failed (`__fastfail(7)`) at first paint — the "works on the first run, crashes after" pattern several Windows 11 users reported. Fix: persisted UI state is invalidated when the saved Qt version differs from the running one, and is **cleared** (not just logged) if restoration raises, so one bad shutdown can't brick every future session. Reporter-validated (6/6 clean runs). One-shot escape hatch: `QISKIT_METAL_RESET_UI_SETTINGS=1`. (#1122, closes #1048; builds on #1104 / #1110)
- **Auto-routing no longer passes straight through a component.** `RouteAnchors.unobstructed()` returned `True` when both segment endpoints lay inside a component's bounding box even though the segment crossed the actual (non-rectangular) contour, so routed paths could penetrate e.g. a circular pad. The contour is now checked in that case too. (#1113, closes #1036; reimplements the community fix #1038 by @Jinyuan426, with a regression test)
- **`design.to_python_script()` output is runnable again.** Exported `.metal.py` scripts that use numpy arrays now include `from numpy import array` in the header. (#1043 by @saschabuehrle, closes #1042)

### Added (v0.7.5-only)

- **`TransmonCross` non-uniform claw options.** New per-connection-pad `claw_width_back` / `ground_spacing_back` let the back of a claw connector (facing the incoming CPW) use a different width / ground spacing than the sides — e.g. MIT-LL "candle" qubits. Both default to `None` (fall back to `claw_width` / `ground_spacing`), so existing designs render byte-for-byte identically. (#1115; reimplements #957 by @clarkmiyamoto)
- **Windows Qt software-OpenGL default.** On Windows, `import qiskit_metal` sets `QT_OPENGL=software` before PySide6 imports (opt out with `QISKIT_METAL_QT_HARDWARE_GL=1`) — harm-reduction for fragile integrated-GPU / WDDM 3.2 driver stacks. (#1122)
- **Reference full-chip design tutorials.** Three executed, headless-rendered end-to-end examples — single transmon + readout resonator, two coupled transmons, and 4-qubit multiplexed readout — under *Tutorials → Full-Chip Design Examples* on the docs site. (#1108)

### Docs (v0.7.5-only)

- Component-gallery cards now deep-link to each component's own API page with real descriptions (registry-aware, so new components self-link). (#1108)
- `ROADMAP.md` now renders inline on the docs site as a single source of truth; site TOC restructured for clarity. (#1118–#1121)

### Security / CI (v0.7.5-only)

- Cleared 10 Dependabot advisories in the dev/docs toolchain (`starlette`, `bleach`, `jupyter-server`, `jupyterlab`, `tornado`) — lockfile-only, no runtime impact for installed users. (#1111)
- Hardened the CI `apt` setup against flaky third-party runner sources (azure-cli / Microsoft repos) that were failing jobs before any test ran. (#1112)
- Windows on-screen GUI init hardening + `QISKIT_METAL_DEBUG_INIT` diagnostic + a `tests-gui-display-windows` CI job. (#1110)

### Upgrade notes

No API changes; drop-in upgrade from 0.7.4. Windows users hitting the GUI crash: just upgrade — the fix is automatic. If a machine is already in a poisoned state, `QISKIT_METAL_RESET_UI_SETTINGS=1` (or deleting `HKCU\Software\QiskitMetal\MainWindow`) clears it once.

## Quantum Metal v0.7.4 (new SNAIL component + crash fixes; no breaking changes)

Patch release. Additive — no breaking changes.

### Added (v0.7.4-only)

- **`SNAIL` QComponent** (`qiskit_metal.qlibrary.qubits.SNAIL`) — a Superconducting Nonlinear Asymmetric Inductive eLement: a loop with three large Josephson junctions on one arm and one smaller junction on the other. Emits the four junctions to the `junction` qgeometry table (three large at `Lj`, one small at `Lj_small`) so it renders as lumped Josephson inductances under HFSS-eigenmode / pyEPR, and exposes pins `a`/`b` for routing. Default junction inductances and the documented physics (`alpha`, Kerr-free flux, `alpha < 1/n` constraint) are grounded in Frattini et al. 2017/2018 and Sivak et al. 2019. (#1100, closes #1099)

### Fixed (v0.7.4-only)

- **`EigenmodeSim.plot_convergences()` raised `NameError: plot_convergence_f_vspass`.** A prior lazify-imports refactor removed the `from pyEPR.reports import (...)` line from `analyses/simulation/eigenmode.py` on the mistaken belief the four plot helpers were unused — they are called inside the method. Restored as a lazy use-site import (keeps the no-pyEPR import path clean). (#1102, closes #1101)
- **`analyses/sweep_and_optimize/sweeping.py` was entirely unimportable.** `Sweeping._extract_min_passes` used an unquoted `Union[None, float]` return annotation without importing `Union`, so `class Sweeping` raised `NameError` at definition time. It went unnoticed because nothing in the package or tests imported the module. Added the missing `Union` import. (#1102)
- **`MetalGUI` segfaulted at interpreter exit** (in a Jupyter kernel: "the kernel appears to have died"). At finalization PySide6 destroyed the `QApplication` while the window was still alive, dispatching an event through the main window's `QMenuBar` event filter whose target was half-deleted → SIGSEGV. Fixed with a one-shot `atexit` handler that deletes top-level Qt widgets while the interpreter / `QApplication` are still alive. (#1104, addresses #1048)

### CI (v0.7.4-only)

- **`tests-gui-display`** — first CI job to launch the real on-screen Qt `MetalGUI` (under Xvfb), so GUI-lifecycle crashes like #1048 can't regress unnoticed. Every other job runs headless. (#1104)

## Quantum Metal v0.7.3 (Qt-mode polish + `qm.show_inline`; no breaking changes)

Patch release rolling up the v0.7.2 line. v0.7.2 was never tagged to PyPI; everything below shipped together as **v0.7.3**.

### Added (v0.7.3-only)

- **`qm.show_inline(fig)`** — backend-agnostic figure display. When the active matplotlib backend is interactive (`Qt6Agg` while the desktop `MetalGUI` is open, or `TkAgg` on some local installs), `plt.show()` opens a separate OS window rather than rendering inline in Jupyter. `qm.show_inline(fig)` saves to a PNG buffer and displays via `IPython.display.Image` — identical cell output in Qt mode and headless (Agg / inline) mode. Falls back to `plt.show()` when IPython is unavailable. Lives at `src/qiskit_metal/viewer/show_inline.py`; exported at top level.
- **`PlotCanvas.zoom_on_components(component_names)`** — the Qt canvas now mirrors `MetalGUIHeadless.zoom_on_components`: computes the bounding box of the named components with 10 % padding, sets the axis limits, refreshes the canvas.

### Fixed (v0.7.3-only)

- **`gui.highlight_components(...)` silently inert in Qt mode** — the canvas method at `mpl_canvas.py:692` appended rectangles + text to the axes correctly, but the resulting redraw was missing some Qt event-loop flushes. The visual highlight only appeared after a second manual `gui.refresh_plot()`. Fix: `canvas.refresh()` now follows `self.draw()` with `self.draw_idle()`, scheduling a redraw on the next event-loop tick so the annotations actually render on the first call. (Headless `MetalGUIHeadless.highlight_components` was unaffected — it draws synchronously.)
- **Double-click on a QComponents-table row crashed with `AttributeError: 'PlotCanvas' object has no attribute 'zoom_on_components'`.** The desktop GUI calls `gui.canvas.zoom_on_components([name])` on double-click; that method existed on `MetalGUIHeadless` but not on the Qt canvas. Added — see above.

### Highlights (carried from v0.7.2)



**Follow-up to v0.7.1** centered on making "lite Colab/Binder users" and
"desktop GUI users" walk the same tutorial path. v0.7.0 + v0.7.1 split
the install into lite vs full extras; v0.7.2 makes that split invisible
to the user. No breaking changes.

### Highlights

- **New `qm.gui(design)` factory** auto-picks the desktop `MetalGUI`
  (Qt) when PySide6 + a display are available, and a new
  `MetalGUIHeadless` (inline matplotlib) otherwise. The
  `MetalGUIHeadless` class mirrors `MetalGUI`'s tutorial-facing surface
  (`gui.rebuild()`, `gui.screenshot()`, `gui.edit_component(...)`,
  `gui.highlight_components(...)`, `gui.zoom_on_components(...)`,
  `gui.main_window`), so tutorial code is identical on Colab, Binder,
  headless servers, and the desktop. Detection covers
  `QISKIT_METAL_HEADLESS=1`, Google Colab, Binder env vars, Linux
  without `DISPLAY`, and missing PySide6.
- **Colab + Binder badges on every numbered tutorial and circuit
  example** — 90+ notebooks across `tutorials/` and
  `docs/circuit-examples/`. One click in the docs site → a running
  notebook in the browser via the lite install.
- **Section 1 tutorials restructured for hands-on flow**:
  1.1 Quick start (was: Bird's eye view), 1.2 Bird's eye view (was: 1.1),
  1.3 Build a 4-qubit chip (new — promoted from end of old 1.1),
  1.4 Saving & exporting (was: 1.3), 1.5 Parametric (unchanged).
  Old 1.4 Headless + 1.6 Shape library dropped (subsumed by `qm.gui`
  + the new gallery).
- **QComponent Gallery** (`docs/qcomponents-gallery.rst`) — visual
  catalog of every component shipped, grouped by category, each card
  linking through to autodoc. Auto-generated at every docs build from
  a single source of truth in `src/qiskit_metal/_gui/_imgs/components/`.
- **Tutorial CI gate**: 22 lite-runnable notebooks now execute on
  every PR via `_dev/rerun_auto.py`. Split into auto-refresh (17
  matplotlib-only) and frozen-Qt (5 with hand-curated Qt screenshots
  — CI verifies pass/fail without clobbering committed outputs).

### Added

- `src/qiskit_metal/viewer/headless_gui.py` — `MetalGUIHeadless` class,
  `_is_headless_environment()` detector, and the `gui()` factory.
  Exposed at the top level as `qm.gui` and `qm.MetalGUIHeadless`.
- One-time onboarding banner in `MetalGUIHeadless` explaining the
  active mode and how to install desktop GUI extras. Suppress with
  `QISKIT_METAL_HEADLESS_QUIET=1`.
- `qm.MetalGUI` is now a lazy attribute via `__getattr__`. `import
  qiskit_metal` no longer pulls in PySide6; the import only fires when
  Qt is actually requested. Clean `ImportError` on lite installs
  pointing at `pip install 'quantum-metal[gui]'` + the factory.
- Bottom-right corner watermark on headless figures: faint logo +
  "Qiskit / Quantum Metal" text (same spec as the desktop `MetalGUI`
  canvas), painted via an inset axes so it never offsets the parent
  `dataLim`.
- `open_docs(force=False)` — suppresses the browser pop in headless /
  CI / Linux-without-DISPLAY contexts; displays the URL as a clickable
  HTML link instead.
- `docs/qcomponents-gallery.rst` + `_dev/generate_qcomponent_gallery.py`
  — auto-generated visual gallery with grid-card layout per category.
- `docs/architecture.rst` + mermaid architecture diagram (also
  rendered natively on GitHub from `.claude/context/architecture.md`).
- Sphinx `builder-inited` hook in `docs/conf.py` regenerates gallery
  RST + thumbnail PNGs at every docs build. Adds `sphinxcontrib-mermaid`
  to docs deps.
- 7 scaffold icons (`base_qcomponent.png`, `base_qubit.png`,
  `user_template.png`, ...) so the MetalGUI Library pane no longer
  shows the globe placeholder for `core/` and `user_components/`
  classes.
- 22 auto-generated QComponent thumbnails for `Route*`, `Tunable*`,
  `Resonator*`, `ShortToGround`, `OpenToGround`, `ReadoutResFC` etc.
  `_dev/generate_qlibrary_thumbnails.py` renders default instantiations;
  `SPECIAL_RECIPES` covers components needing pins or anchors.
- `scripts/check_qlibrary_images.py` — CI gate that fails on broken or
  one-line `.. image::` directives in any component class.
- `_dev/rerun_auto.py` + two whitelist files
  (`notebooks-auto-refresh.txt` / `notebooks-frozen-qt.txt`) drive
  the new tutorial-execute CI step.

### Fixed

- **Watermark autoscale bug** in `_axis_set_watermark_img` (shared by
  desktop `MetalGUI` + new headless renderer): the watermark image
  previously expanded the parent axes' `dataLim` on every redraw,
  pushing the chip off-center after `gui.autoscale()` or `gui.rebuild()`.
  Now rendered into an inset axes that doesn't contribute to the
  parent `dataLim`.
- **Wide-chip letterboxing** in headless renders: switched
  `ax.set_aspect("equal")` to `adjustable="datalim"` so a 6 mm × 2 mm
  layout no longer collapses into a thin band with whitespace.
- `edit_component` no longer noisy in headless mode — true no-op now;
  the docstring points users at `design.components['<name>'].options`.
- `screenshot(display=True)` no longer double-displays in Jupyter
  (returning the figure after `display(Image(...))` triggered the
  cell's auto-display of the last expression).
- `find_id` warning silenced — replaced `design.components.get(name)`
  with `name in design.components` checks (`Components` isn't a dict;
  `.get` was being interpreted as a component lookup).
- `WARNING [_maybe_warn_lite_flip]` from v0.7.0 removed at source +
  scrubbed from 9 notebooks where it had been cached in output cells.
- `RouteMeander` docstring inline literal across a line break rewritten
  to a valid double-backtick literal.
- `JJ_Dolan.png`, `JJ_Manhattan.png`, `squid_loop.png` —
  case-sensitive filename mismatches in the corresponding docstrings
  fixed. Invisible on macOS HFS+ but broke the Library pane on Linux.
- 11 one-line `.. image:: foo.png` directives split to the two-line
  form the MetalGUI scanner regex requires.
- Tutorial 1.2 cell that printed `<Figure size 2400x1000 with 2 Axes>`
  instead of rendering inline now displays a PNG buffer via
  `IPython.display.Image` — backend-agnostic.

### Changed

- MetalGUI Library pane defaults to the **Library** tab on launch
  instead of QComponents (the latter is empty before any components
  exist).
- `MetalGUI` Library pane filters the `qlibrary/` tree to `*.py` only.
- `Quantum Metal` → `Qiskit / Quantum Metal` in both viewers' title
  strip and corner watermark.
- README hero strip: 3 cards → 4. New "🧩 Component Gallery" card.
- Tutorial 1.1 ↔ 1.2 swap. 1.4 Headless + 1.6 Shape library dropped.
- 2.01 + 2.02 merged into a single "QComponent lifecycle" notebook.
- `docs/qcomponents-gallery.rst`, `docs/images/qlibrary/`, and
  `docs/apidocs/*.png` are now generated at every docs build via the
  `builder-inited` hook and **gitignored**. Was: 100+ duplicate PNG
  blobs committed across two directories.
- `Opening documentation` quick-topic notebook no longer calls
  `open_docs()` automatically — line is commented; user opts in.
- 75+ stale `:doc:` references to the dropped 1.4 Headless tutorial
  swept to point at 1.1 Quick start.
- 41 numbered tutorials had `%load_ext autoreload` / `%autoreload 2`
  stripped (104 cells total) — these break in Colab.

### Deprecated

- Nothing. `MetalGUI(design)` direct construction remains fully
  supported; `qm.gui(design)` is an additive convenience.

### Migration

See `docs/migration-to-v0.7.0.rst` for the v0.7.2 "prefer
`qm.gui(design)` over `MetalGUI(design)`" section.


## Quantum Metal v0.7.1 (UX + docs polish; no breaking changes)

**Follow-up to v0.7.0** focused on adoption / DevRel polish, build-time
quality, and a friendlier ElmerFEM error surface. No breaking changes —
v0.7.0 users can upgrade in place.

### Highlights

- **ElmerFEM UX**: missing-binary errors now print actionable install
  instructions (platform-specific) instead of a bare ``FileNotFoundError``
  from ``subprocess.run``. Windows install-path lookup unpinned from
  Elmer 9.0 (globs ``Elmer *-Release/bin/``, so Elmer 10.x ships
  cleanly with no code change). Also fixed a pre-existing bug where
  passing an explicit ``elmersolver=`` path silently skipped the
  subprocess call.
- **New ``[mesh]`` extra** for the gmsh dependency (canonical name for
  the universal mesher — used by Elmer today, will feed Palace and
  future open FEM backends). ``[fem]`` kept as a backward-compatible
  alias; both extras install gmsh.
- **Docs build: zero warnings.** Previously failed with ~50+ warnings
  + several errors (heading hierarchy, nbformat validation, duplicate
  substitutions, ambiguous cross-refs). All fixed at source.
- **README modernization**: 482 → 225 lines, headless-first Quick Start,
  Colab + Codespaces "try it now" buttons, hero animated GIF showing a
  4-qubit chip built in 5 frames.
- **``CITATION.cff``** added for GitHub's "Cite this repository" widget.

### Bug fixes

- ``elmer_runner._resolve_elmer_binary`` — friendly errors when ElmerFEM
  binaries are missing; auto-detects newer Windows release directories.
- ``elmer_runner.run_elmersolver`` — explicit-path code path no longer
  skipped due to indentation bug; ``encoding="utf=8"`` typo fixed.
- ``analyses/__init__.py`` — added missing autosummary blocks so the
  rendered Analyses overview page is actually useful.
- ``_gui/main_window*.py`` — RST docstring lint pass (bullet lists,
  paragraph spacing); PySide2 → PySide6 in docstrings (we've shipped
  PySide6 since v0.5).
- ``contributor-guide.rst`` — example directives no longer accidentally
  fire at build time and generate phantom RST files.

### Docs

- Sphinx ``conf.py``: added ``intersphinx`` for python/matplotlib/numpy/
  pandas, ``nitpick_ignore`` for ``logger``/``figure``,
  ``nbsphinx_codecell_lexer="python3"`` (silenced ~1500 warnings).
- Tutorial notebook normalisation (nbformat cell IDs across 108
  notebooks) + heading-hierarchy fixes across 1.1/1.2/4.05.
- New ``scripts/check_tutorials_sync.py`` CI gate ensures ``tutorials/``
  and ``docs/tut/`` cell content stays byte-identical.
- ``README_Gmsh_Elmer.md`` → ``README_Open_FEM_Stack.md`` (broader scope:
  gmsh + Elmer + future Palace).
- Stripped v0.5/v0.6 era qualifiers across installation, migration,
  headless-usage, workflow, contributor-guide, FAQ.
- Dead links fixed (gohlke wheels site retired in 2022); rebrand pass
  across all auxiliary READMEs.

### Hygiene

- ``[tool.ruff]`` — added ``extend-exclude`` for ``_dev/``, ``docs/_archive/``,
  ``docs/_build/`` (scratch / generated dirs).
- ``ipython>=8.0`` and ``ipywidgets>=8.1`` added to docs deps (silence
  nbsphinx lexer and ipywidgets-path warnings).
- ``ROADMAP.md`` — new "Adoption, DevRel, and onboarding" section
  capturing follow-up ideas (Colab embeds, JupyterLite, gallery page,
  SUPPORT.md / GOVERNANCE.md, devcontainer, recipes section, etc.).
- CI matrix: ``tests-extras`` now runs both ``mesh`` and ``fem`` (alias)
  paths so neither can regress silently.

### Compatibility matrix

| | v0.7.0 | **v0.7.1** |
|---|---|---|
| Python | 3.10 / 3.11 / 3.12 | 3.10 / 3.11 / 3.12 |
| Default install | lite (no Qt / Ansys / gmsh) | same |
| ``[gui]`` extra | PySide6, qdarkstyle | same |
| ``[ansys]`` extra | pyaedt, pyEPR-quantum | same |
| ``[fem]`` extra | gmsh | same (alias for new ``[mesh]``) |
| ``[mesh]`` extra | — | **new** (canonical name; gmsh) |
| ``[full]`` extra | all of above | same |

## Quantum Metal v0.6.2 (deprecation-notice release)

**Pre-flip release.** All v0.6.x install behaviour is unchanged
— but a `FutureWarning` now fires on `import qiskit_metal` letting
users know v0.7.0 will move the heavy dependencies (PySide6,
qdarkstyle, pyaedt, pyEPR-quantum, gmsh) out of base into opt-in
extras. To preserve current behaviour, install with
`pip install 'quantum-metal[full]'` before upgrading to v0.7.0.

This release also lazifies the last remaining eager heavy-dep
import — gmsh — so the `tests-lite` CI matrix can validate the
full v0.7.0 install behaviour ahead of the actual deps flip.

### What landed

- **gmsh lazification** in `renderer_gmsh/gmsh_utils.py` and
  `renderer_gmsh/gmsh_renderer.py`: same `try/except` +
  `_require_gmsh()` pattern as the pyEPR/pyaedt lazification in
  v0.6.x. `QGmshRenderer.__init__` raises a clear
  `ImportError: ... pip install 'quantum-metal[fem]'` when gmsh
  isn't available. The `_start_renderers` skip-and-log path
  catches it.
- **gmsh version pin tighten**: `gmsh>=4.11.1` → `gmsh>=4.15.0,<5`.
  The dev env already ships gmsh 4.15.0 (bumped in v0.5.3.post1
  but the floor wasn't updated). Upper bound caps before any
  future gmsh 5 lands.
- **`FutureWarning` on `import qiskit_metal`** advertising the
  v0.7.0 lite-flip. Fires once per process via Python's standard
  warning deduplication. Suppress with
  `QISKIT_METAL_SUPPRESS_LITE_FLIP_WARNING=1`.
- **Version bumped** to 0.6.2.

### Nothing else changed

- Public API: unchanged
- Test behaviour: unchanged (all 458 tests still pass)
- Install behaviour: unchanged (heavies still in base)
- Headless / lite paths: unchanged

The next release (v0.7.0) will flip `pyproject.toml`'s base
dependencies and the warning becomes truth.

## Quantum Metal v0.7.0 (lite-by-default release)

**Headline: lite-by-default install.** `pip install quantum-metal`
no longer pulls PySide6, qdarkstyle, pyaedt, pyEPR-quantum, or gmsh
— those move into opt-in extras (`[gui]` / `[ansys]` / `[fem]` /
`[full]`). The base install is now small, fast, and friendly to AI
orchestration, Colab / Binder, cloud Jupyter, headless CI, and any
non-interactive workflow.

See [`ROADMAP.md`](./ROADMAP.md) and
[`docs/migration-to-v0.7.0.rst`](./docs/migration-to-v0.7.0.rst) for
the full migration recipes.

### Breaking change — what to do

`pip install quantum-metal` no longer pulls the heavies. Pick the
install command that matches your workflow:

| Command | What you get |
|---|---|
| `pip install quantum-metal` | Lite: designs + `qm.view()` + GDS + pure-Python analyses |
| `pip install "quantum-metal[gui]"` | + `MetalGUI` desktop app (PySide6, qdarkstyle) |
| `pip install "quantum-metal[ansys]"` | + HFSS/Q3D renderers + EPR analyses (pyaedt, pyEPR) |
| `pip install "quantum-metal[fem]"` | + gmsh / Elmer mesher |
| `pip install "quantum-metal[full]"` | All of the above — v0.6.x compatibility set |

The full feature matrix is in `README.md` and `docs/installation.rst`.

### Why

- **AI orchestration loops**, cloud Jupyter, Colab / Binder, and
  headless CI no longer install or ignore hundreds of MB of Qt + AEDT
  they'll never use. Base install drops from ~1 GB to a few dozen MB.
- **Academic and educational users** without Ansys licenses can now
  install + use the full design/analysis path without artificially
  needing pyaedt.
- **Tutorial notebooks** that don't need Ansys / gmsh now run on lite.

### What didn't change

- `import qiskit_metal` (the import path stays for v0.7.x; see the
  upcoming import-rename heads-up below)
- Public API on `QDesign`, `QComponent`, `QRenderer`
- The Python API surface — every class, function, and method is
  unchanged

### Upcoming next: import path rename

A future major release will rename the Python import path from
`qiskit_metal` to `quantum_metal` to match the PyPI package name.
No version has been set for the cutover. A `FutureWarning` now fires on
`import qiskit_metal` advertising this. Plan to update your imports
ahead of that release; an alias/shim period will be considered
during the cutover. See the README rebrand notice for details.

Silence the warning with `QISKIT_METAL_SUPPRESS_RENAME_WARNING=1`.

### CI

- **`tests-extras` matrix added** — exercises `[gui]`, `[ansys]`,
  and `[fem]` install pathways individually so a regression on any
  one extra surfaces in CI (previously only the full + lite paths
  were tested).

### Docs

- **README** redesigned with a 5-card install-pathway grid + feature
  matrix.
- **`docs/installation.rst`** expanded with the same 5-card grid and
  a more thorough install-pathway breakdown.
- **`docs/index.rst`** updated to reflect the v0.5 → v0.7
  transition state and the upcoming import-rename heads-up.
- Various "Qiskit Metal" → "Quantum Metal" rebrand cleanups
  throughout README / docs / install pages.

## Quantum Metal v0.6.2 (deprecation-notice release)

**Pre-flip release.** All v0.6.x install behaviour was unchanged
— but a `FutureWarning` fired on `import qiskit_metal` advising
users of the upcoming v0.7.0 lite-flip. Also lazified the last
remaining eager heavy-dep import (gmsh) and tightened the gmsh pin
to `>=4.15.0,<5`.

### What landed

- **gmsh lazification** in `renderer_gmsh/gmsh_utils.py` and
  `renderer_gmsh/gmsh_renderer.py`: same `try/except` +
  `_require_gmsh()` pattern as the pyEPR/pyaedt lazification.
- **gmsh version pin tighten**: `gmsh>=4.11.1` → `gmsh>=4.15.0,<5`.
- **`FutureWarning` on `import qiskit_metal`** advertising the
  v0.7.0 lite-flip. Repurposed in v0.7.0 to advertise the upcoming
  import path rename.
- **Docs CI**: `docs.yml` now also runs on PRs (build-only; deploy
  only on push-to-main).
- **Version bumped** to 0.6.2.

## Quantum Metal v0.6.1 (May 2026)

Patch release after the v0.6.0 tag-only failure (PyPI publish step
failed during the v0.6.0 cut; `pip install quantum-metal==0.6.0`
404s. Don't tag-and-walk-away on releases — verify PyPI received
the wheel before announcing). See `.claude/commands/release.md`
post-mortem.

User-visible changes vs v0.6.0:

- Sphinx docs build warnings resolved
- Tutorial notebook heading-level hierarchy normalized (nbsphinx
  was choking on `# → ###` skips)
- qutip 5 + pyEPR 0.9.5+ version sync — fixes `np.array([Qobj])`
  stacking issue, `np.absolute(Qobj)` issue, and the HFSS 2024.1+
  solution-type rename
- Ruff auto-fixes + trailing-whitespace cleanup

## Quantum Metal v0.6.0 (May 2026)

**Major release.** Foundation for the lite-by-default flip in
v0.7.0. All changes here are additive — current users on v0.5.x
upgrade without code changes.

### Highlights

- **`qm.view(design)`** — standalone matplotlib viewer that works
  without PySide6 / Qt installed. Renders in a Jupyter notebook
  inline or to a file. The headless entry point for tutorials,
  CI, agent workflows, and any environment where you don't want
  to install a Qt binding. See `docs/headless-usage.rst`.
- **Lazy Qt initialization** — `import qiskit_metal` no longer
  requires PySide6 at module-load time. Set
  `QISKIT_METAL_HEADLESS=1` to skip the Qt-backend probe entirely;
  `MetalGUI` still works on full installs.
- **`[gui]` / `[ansys]` / `[fem]` / `[full]` optional-dependency
  extras** added to `pyproject.toml`. In v0.6.x they're
  informational (every extra's deps are also in base), but the
  `tests-lite` CI job exercises the lite-install path so it stays
  green for v0.7.0's flip.
- **`tests-lite` CI matrix entry** — runs the full test suite on
  a venv built without PySide6 / pyaedt / gmsh, catching any
  regression on the lite path.
- **`qutip 5` + `pyEPR 0.9.5+` compatibility** — fixes
  `np.array([Qobj])` no longer stacking, `np.absolute(Qobj)` no
  longer working directly, and the HFSS 2024.1+
  `solution_type` rename (`"DrivenModal"` →
  `"HFSS Modal Network"`).
- **Pandas 2.2 compatibility** — uses `.iloc[]` for positional
  indexing where 2.2 stopped doing the old positional-fallback.
- **Type annotations** on the core public API methods of
  `QComponent`, `QDesign`, and the renderer bases — unlocks
  downstream type-checking for orchestration tools.

### New tests

- `test_pin_normals_point_outward` — static sanity check that
  every component's pins point away from the component centroid.
  Catches HFSS port-flip bugs at component-author time, not at
  HFSS-eval time. One known failing case logged:
  `LaunchpadWirebondDriven.in` (see `KNOWN_INWARD_PINS`).
- Static AST audit that every `self.options.X` access has a
  matching key in `default_options`. Catches typos that would
  silently fall through.
- `test_view_hides_layers` — gates the new `qm.view(design)`
  `hidden_layers={...}` parameter.

### Tutorials

- Every tutorial notebook now has a "no Qt required" callout
  near the top, explaining when the tutorial does and doesn't
  need `MetalGUI`.
- New `1.4 Headless Quick View.ipynb` — short notebook showing
  the `qm.view(design)` path end-to-end with no Qt.
- The headless tutorial path is exercised in CI via
  `nbconvert --execute` on `1.4 Headless Quick View.ipynb`
  inside the `tests-lite` job.

### Infrastructure

- `CLAUDE.md` + `.claude/` directory: documents the repo's
  hard-touch zones, recurring tasks, and lessons-learned for
  future AI agents.
- `tests-lite` uses `.venv/bin/python` directly (not `uv run`)
  because `uv run` was re-syncing the venv and overwriting the
  custom lite-install state. See
  `.claude/context/lessons-learned.md`.

### Known issues

- `LaunchpadWirebondDriven.in` pin normal points inward (HFSS
  validation blocked the fix in v0.6.0; documented in
  `tests/test_qlibrary_pin_sanity.py::KNOWN_INWARD_PINS`).
- 13 ruff findings in HFSS / `_gui/` deferred to v0.6.1+ for
  validation environment. (**Resolved** in v0.6.1+ via the
  ruff-sweep PR #1070, with one caveat documented in
  `.claude/context/lessons-learned.md`.)
- v0.6.0 PyPI publish failed; install
  `quantum-metal>=0.6.1` instead. (**Fixed** in v0.6.1.)

## Quantum Metal v0.5.3.post1 (Jan 23, 2026)
- Pinned pyaedt to less than v0.24 due to bugs. 
- Updated gmsh dependency 4.11.1 → 4.15.0

## Quantum Metal v0.5.3 (Jan 17, 2026)

- Various dependency updates. 
- Removed descartes and cython dependencies (unused).
- pandas, geopandas, scqubits and qutip updates to latest major version. Should fix [#1027](Ihttps://github.com/qiskit-community/qiskit-metal/issues/1027).
- Updates to contributor guide to fix inconsistent headline levels. Also convert example images to rst source code blocks. 
- Update various parts in the docs to indicate near-term versioning updates. 
- Update uv version to 0.9.24 in CI. Remove step to upgrade runner packages in CI for workflows speedup. 
- Convert package from [flat layout to src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/#src-layout-vs-flat-layout). This is a forward looking change that will help decouple source code from docs and tests. In this configurations, the any package code must be imported using the package name, instead of relative imports as before. This also requires installing the package in the virtual environment (either as editable or via the wheel) to import it, which we already support in our uv-based workflows. 
- Fixed floating `QLabel` bug in `MetalGUI` [#1031](https://github.com/qiskit-community/qiskit-metal/issues/1031).
- New CI workflow to bump version using uv, commit and push a git tag and create a draft release. This also triggers the PyPI release. 
- Update CI workflows to use Python 3.12.


## Quantum Metal v0.5.2 (Dec 11, 2025)

- We have adopted uv as a project/dependency management tool. 
- Tasks are still run using tox, but with the tox-uv plugin. 
- We adopted ruff for linting and formatting. We have a good starting configuration for linting, but it needs some work before it could be considered stable. 
- The GitHub actions workflows have been updates with these changes. 
    - Python 3.12 is the slowest to build wheels in CI, partly because qutip and pandas take a very long time to build on this version. This needs to be investigated. 
- New developer onboarding instuctions added to `README_developers.md`. The old instructions in`README_developers.md` have been retained with a note for usage on older versions of `qiskit-metal`. 
- Development install instructions have been added to documentation in the "Contributor Guide". 
- Installation instructions have been updates. More updates to come. 
- Single source package version from `pyproject.toml`.
- Updated to contributor docs to add instructions on bumping package version using uv. 



## QISKIT METAL v0.5 (2025)

### Major Updates

This release addresses significant package changes and ports:

- **PyQt5 to PySide6**: A complete overhaul of the GUI.
- **GDSPY to GDSTK**: Replaced GDSPY with the more robust GDSTK library.
- **PYAEDT to Ansys (v1.0)**: Major update with a new syntax. Extensive testing required.
- **Installation Improvements**: Transitioned to `venv` for faster environment setup, moving away from `conda`. Also, most package versions have been floated and upgraded.
- **Docs**:
    - Migrate qiskit_sphinx_theme to the new theme
    - Add divs on the front page to tuts etc
    - Add user content and showcase page

---

### GUI Enhancements

1. **Traceback Reporting**: Added detailed traceback reporting in the logging system to aid debugging.
2. **Model Reset Issue**: Fixed the issue causing the warning: *"metal: WARNING: endResetModel called on LibraryFileProxyModel(0x17fda8200) without calling beginResetModel first (No context available from Qt)"*.
3. **MPL Renderer Issue**: Resolved the error: *"Ignoring fixed y limits to fulfill fixed data aspect with adjustable data limits. Ignoring fixed x limits to fulfill fixed data aspect with adjustable data limits."*.
4. **UI Button Update**: Added a red border style to the "Create Component" button in the UI for better visibility.

---

### PYAEDT Update

- **FutureWarning**: The `pyaedt` module has been restructured and is now an alias for the new package structure based on `ansys.aedt.core`. To avoid issues in future versions, please update your imports to use the new architecture. Additionally, several files have been renamed to follow the PEP 8 naming conventions. For more information, refer to the [Ansys AEDT documentation](https://aedt.docs.pyansys.com/version/stable/release_1_0.html).
