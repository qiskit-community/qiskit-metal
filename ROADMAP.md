# Quantum Metal — Roadmap

This file describes the direction Quantum Metal is heading.
Items are grouped by status: what we're working on now,
what's planned next, and what we're researching with no
firm timeline. Linked PRs and issues are the source of truth
for "is this done yet."

If something here matters to your work, open an issue or
ping us on Discord — the order and emphasis below shift
based on user demand and contributor availability.

| Symbol | Meaning |
|---|---|
| `[shipped]` | Released, in current `main`. |
| `[in-progress]` | Active development. PR open or imminent. |
| `[planned]` | Scoped, on the queue. Will be picked up in the indicated release. |
| `[research]` | Direction set, design not finalized. Help wanted. |

---

## Vision

Quantum Metal is the open-source **chip-design layer** for
superconducting quantum hardware: a Python library where
you build a chip from `QComponent`s, attach analyses, and
hand the result to whichever solver / fab / orchestrator
you want. The library itself is solver-agnostic; the
renderers are the integration layer with the outside world
(GDS, HFSS, Q3D, gmsh, Elmer, AWS Palace, ...).

We sit inside a broader open-source ecosystem — design
discovery ([SQuADDS](https://github.com/LFL-Lab/SQuADDS)),
Palace simulation wrappers ([SQDMetal](https://github.com/sqdlab/SQDMetal),
[pypalace](https://pypalace.readthedocs.io/)),
mesh utilities, quantization tools. Full map:
[`docs/ecosystem.rst`](./docs/ecosystem.rst) (rendered at
the docs site). Items below are about Metal's own
direction; ecosystem-level coordination is tracked
alongside.

Two things shape the next year:

1. **Lite-by-default.** `import qiskit_metal` should be
   fast, dependency-light, and never assume Qt / AEDT / gmsh
   / Palace are present. Heavy backends are opt-in extras.
2. **Orchestration-friendly.** Quantum Metal is increasingly
   used inside AI-driven design loops where an LLM or
   optimization agent generates designs, dispatches them to
   one or more backend solvers, and iterates on the result.
   The library's surface should be predictable, scriptable,
   and minimal — no GUI prompts, no hidden state, no
   "did you remember to install AEDT" surprises.

---

## Lite-by-default flip (v0.7.0) `[shipped]`

The v0.6.x line shipped every heavy dependency in `[project.dependencies]`,
so `pip install quantum-metal` pulled hundreds of MB and assumed Qt was
welcome. **v0.7.0 flipped this**: heavies moved into opt-in extras
(`[gui]` / `[ansys]` / `[mesh]` / `[full]`) and the base install became
the orchestration-friendly minimal surface.

Items shipped under this initiative (across v0.6.1 → v0.7.1):

- ✅ Eager-import audit + lazification of `pyside6`, `gmsh`, `pyaedt`,
  `pyEPR-quantum`. Module top-level imports moved into functions or
  `__getattr__` shims; friendly `ImportError`s point users at the right
  extra.
- ✅ Test-suite skip-cleanliness via `pytest.importorskip` so the full
  suite passes on a lite install (with skips, not failures).
- ✅ `tests-lite` and `tests-extras` CI matrices — both run cleanly on
  every PR. `tests-extras` runs `gui` / `ansys` / `mesh` / `fem`
  independently.
- ✅ `v0.6.2` deprecation release with `FutureWarning` advertising the
  upcoming flip + the `[full]` opt-in path for stay-the-same users.
- ✅ `v0.7.0` the actual flip — heavies out of base deps. README, install
  matrix, migration guide all updated.
- ✅ `v0.7.1` cleanup — added `[mesh]` as the canonical name for the
  gmsh extra (`[fem]` kept as a backward-compatible alias); the
  `README_Open_FEM_Stack.md` rename; ElmerFEM error-message UX fix.

---

## Downstream ecosystem rollout `[in-progress]`

The v0.7.0 / 0.7.1 lite flip changed the install surface
downstream packages depend on (extras-by-default, lazified
Qt / pyaedt / gmsh, friendlier `ImportError` UX, the
`MetalGUI` → `qm.view()` headless path). To finish the
rollout, each downstream package needs install instructions,
lockfiles, and pins updated against `quantum-metal>=0.7.1`.

Coordination plan: file an issue on each downstream repo
with a recipe for the upgrade, link to
`docs/migration-to-v0.7.0.rst`, and point at a worked
example.

Worked example to point at:
[qdw26-workshop PR #1](https://github.com/quantum-device-consortium/qdw26-workshop-materials/pull/1)
swapped a forked-Metal pin for mainline
`quantum-metal[full]>=0.7.1` and includes the Apple-Silicon
Docker pin, `schemdraw` addition, and palace auto-discovery
fixes — a full migration in one diff.

Per-issue contents:

1. New install command (`pip install quantum-metal[ansys]`,
   `[mesh]`, `[full]`, etc. — whichever extras that
   downstream actually uses).
2. Any lazy-import / `ImportError` UX changes that affect
   their code paths.
3. Link to `docs/migration-to-v0.7.0.rst`.
4. Reminder about the `qiskit_metal` → `quantum_metal`
   import-path rename targeted for v0.8 / v1.0, so they can
   plan import updates ahead of that release.

Known downstream packages:

- **[SQuADDS](https://github.com/LFL-Lab/SQuADDS)**
  (LFL-Lab @ USC) — design-discovery database, consumes
  Metal `QDesign` objects. **`[planned]`** — issue to file.
- **[SQDMetal](https://github.com/sqdlab/SQDMetal)**
  (SQDLab @ UQ) — Palace simulation wrapper. **`[planned]`**
  — issue to file; same migration plus the
  `MetalGUI` → `qm.view()` story for headless Docker /
  Brev contexts.
- **[pypalace](https://pypalace.readthedocs.io/)**
  (Northwestern) — Palace wrapper. **`[planned]`** —
  issue to file.
- **[pyEPR](https://github.com/zlatko-minev/pyEPR)** —
  **`[shipped]`** — co-maintained, compatibility through
  v0.7.1 verified.
- **[QDW 2026 workshop materials](https://github.com/quantum-device-consortium/qdw26-workshop-materials)**
  — **`[shipped]`**, PR #1 merged; the canonical worked
  example referenced above.

If you maintain a package that depends on Metal and we
haven't listed it, please open an issue here so we can
add it (and help with the upgrade).

---

## Next — AI-orchestration profile (v0.7.x – v0.8.0)

Once the lite flip lands, `pip install quantum-metal`
becomes the recommended entry point for agents, optimizers,
and any non-interactive workflow. This section ships
explicit support for that use case:

- **`docs/orchestration.rst`** `[planned, v0.7.x]`
  End-to-end recipe: instantiate a design, build geometry,
  export GDS, run analyses, all in <50 LOC, all without
  Qt or AEDT. Includes the "what extras do I need for
  what backend" matrix.
- **Stable programmatic API contract** `[planned, v0.7.x]`
  Document which methods / attributes on `QDesign`,
  `QComponent`, and the renderer base classes are
  considered public and stable for downstream
  orchestrators. Internal-only helpers get an `_` prefix
  or a `@_internal` marker where they aren't already.
- **Determinism guarantees** `[research]`
  Identify and fix sources of non-determinism in design
  → geometry construction (dict ordering, float
  comparisons, random IDs), so that two runs of the same
  design produce the same artifact. Important for diffing
  agent outputs.
- **Renderer dispatch by string name** `[research]`
  Currently most code paths assume the GUI or the user
  knows which renderer to call. A
  `design.render(backend="palace")`-style dispatch makes
  orchestrators much easier to write.

---

## Open FEM stack — gmsh + Elmer + AWS Palace `[research]`

Today the only validated analysis path for full-field
solving is the Ansys HFSS / Q3D bridge. This is excellent
for industrial users but excludes everyone without an AEDT
license — and blocks our own CI from validating the
HFSS-specific bugs in the deferred list (see
`tests/test_qlibrary_pin_sanity.py::KNOWN_INWARD_PINS`).

The open FEM stack is the long-term answer. Three pieces:

- **gmsh mesher** — `renderer_gmsh/` already exists. The
  next step is tighter mesh control and port / boundary
  tagging that both Elmer and Palace can consume.
- **gmsh version audit** `[research]` — we currently pin
  `gmsh>=4.11.1` (no upper bound) with 4.15.0 shipped in
  the dev env. The 30 distinct `gmsh.*` API entry points
  we use are all stable core OCC + meshing + lifecycle
  calls, but with gmsh 5 on the horizon we should
  (a) tighten the pin to `>=4.15.0,<5`, (b) walk the API
  call sites against the latest 4.x release notes to spot
  anything deprecated, and (c) survey newer 4.x APIs
  (e.g. richer mesh refinement, boundary-tag protocol
  improvements) that would unblock cleaner Palace and
  Elmer integration. Likely lands as one small PR for
  the pin tighten + a research note for the API survey.
- **Elmer eigenmode solver** — `renderer_elmer/` already
  exists. The integration needs a parity-check pass to
  confirm it still works against current Elmer releases,
  plus documentation of its scope (what kinds of designs
  / analyses it does and doesn't handle today).
- **AWS Palace** — open-source Maxwell solver from AWS.
  Native MPI, modern CMake build, eigenmode + driven +
  electrostatic. A `renderer_palace/` module following
  the `QRendererAnalysis` protocol would unblock
  HFSS-free CI validation of the entire qlibrary, plus
  give academic users a free path to full-field
  analysis.

Initial proof-of-concept order:
1. Validate `renderer_gmsh/` outputs against current gmsh
2. Build a minimal `renderer_palace/` for eigenmode only
3. Cross-validate one canonical design (e.g.
   `TransmonPocket`) against a known HFSS result
4. Document the gmsh-tag → Palace-port boundary contract
   so other open solvers can plug in

If you work on Palace, gmsh, or Elmer and want to help
shape this — please open an issue or reach out on Discord.
External contributor leverage is enormous here.

---

## Architectural items `[research]`

Longer-horizon things that aren't blocking anything today
but are worth tracking:

- **PEP 561 type hints across `QComponent` / `QDesign`
  / `QRenderer`.** Today the type surface is partial;
  full hints unlock static analysis for orchestrators
  and make the LLM-driven code-generation path more
  reliable.
- **Plugin discovery via entry points** `[planned, v0.8.x]`
  External renderers and component libraries currently
  require monkey-patching or vendoring. A
  `qiskit_metal.renderers` and `qiskit_metal.qlibrary`
  entry-point namespace lets the community ship third-party
  packages — and gives lab and community PDKs a clean
  `pip install <pdk>` distribution channel without
  requiring any change to Metal itself.
- **Functional component API alongside class hierarchy** `[research]`
  Add a `@qm.cell`-decorator path so a component can be a
  Python function returning a `QComponent`, in parallel to
  the existing class-based subclassing. Doesn't replace
  the class API. Motivation: LLM / agent codegen is
  measurably more reliable against pure functions returning
  values than against class hierarchies with stateful
  side-effects, so a functional surface is a useful
  on-ramp for the AI-orchestration profile above.
- **JAX-differentiable parametric components** `[research]`
  Inverse-design / qubit-frequency tuning via `grad()` is
  unlocked once a small set of geometric primitives are
  JAX-traceable. Start with `TransmonPocket` as a pilot
  (pad width / gap → frequency gradient via an analytical
  capacitance model, no FEM in the loop). Big win for the
  research audience that currently hand-rolls finite-difference
  sweeps; pairs naturally with EPR analysis for
  Hamiltonian-aware optimisation.
- **Docs hosting reassessment.** GH Pages is current
  (years of SEO). Read the Docs config archived at
  `docs/_archive/readthedocs/` — revivable in minutes
  if/when per-PR previews, versioned docs, or the
  rebrand cutover make the switch worth it.

---

## Group and lab adoption pathway

The next-tier adopters for Metal — research groups, university
labs, multi-PI consortia — evaluate against a recurring set of
questions: *Is it maintained? Can we plug our own PDK in?
Does the GDS round-trip cleanly through downstream tooling?
Will it scale to Python-agent-driven design loops?* This
section groups items aimed at those questions. Several
overlap with the Adoption / DevRel section below; the cut is
by *audience* — DevRel is about attracting individual users,
this section is about clearing the path for groups and labs.

*Items in this section reflect open-source community
direction discussed within the Quantum Device Consortium
(QDC) and the broader contributor base. They are
aspirations, not commitments by any individual contributor
or their employer.*

### High impact, low effort

- **Ship a Metal `.lyp` layer-property file** `[planned, v0.7.x]`
  Users who open a Metal-exported GDS in KLayout currently
  see grey-on-grey because no layer colours / names ship
  with our GDS files. A one-page `.lyp` under
  `docs/_static/` (linked from the GDS export docs) gives
  them a named, coloured view out of the box. KLayout is
  the de-facto open-source viewer in the GDS-handoff path;
  making this handoff frictionless removes a real papercut.
  ~2 hours.
- **"Metal → KLayout" how-to page** `[planned, v0.7.x]`
  Document the GDS-export → KLayout-DRC / visual inspection
  flow, paired with the `.lyp` and a starter DRC deck
  (below). Most superconducting-design flows in the
  community already do both — making the combination
  first-class instead of folklore reduces onboarding
  friction. ~3 hours.
- **"Built for AI agents" docs page** `[planned, v0.7.x]`
  Companion to `docs/orchestration.rst` already on the
  roadmap. The lite-by-default flip and `qm.view()`
  removed the dependency surface that made agent-driven
  workflows painful; this page makes the workflow
  visible. Importantly, position Metal *with* the
  ecosystem here — design discovery via
  [SQuADDS](https://github.com/LFL-Lab/SQuADDS), solver
  dispatch via [SQDMetal](https://github.com/sqdlab/SQDMetal)
  / [pypalace](https://pypalace.readthedocs.io/),
  quantisation via [pyEPR](https://github.com/zlatko-minev/pyEPR)
  and [scqubits](https://github.com/scqubits/scqubits) —
  rather than implying Metal does it all. The story is the
  composable open-source stack, not Metal in isolation.
  ~3 hours.

### High impact, medium effort

- **Tighten release cadence to monthly minimum** `[planned]`
  Even pure-docs / test-only point releases. Prospective
  adopters check commit + release pulse before committing
  engineering time, and read steady cadence as a
  maintenance signal more strongly than raw feature
  surface. Quarterly is fine for features; monthly is
  cheap and changes the perception.
- **Starter DRC deck for superconducting basics** `[planned]`
  A `qm.drc(design, deck="sc_basics")` helper that shells
  out to KLayout with a minimal rule set: min line width,
  min gap, JJ overlap minimums, ground-plane keep-outs.
  Doesn't need to be comprehensive — needs to *exist*, so
  PDK authors and labs have a template to extend instead
  of starting from blank.
- **"When to use Quantum Metal" docs page** `[planned]`
  Use-case-driven framing (not framework-comparison):
  which problems Metal is shaped for (qubit-first design
  with energy-participation analysis, Hamiltonian
  extraction, integration with the open-source SC qubit
  toolchain), which adjacent workflows hand off elsewhere
  (mask-level DRC, process-specific PDK rules, photonics).
  Highly searched by evaluators; framing the fit ourselves
  is more useful to readers than leaving them to
  assemble it.
- **Gallery + thumbnail component icons**
  `[promoted from research]`
  Already on the Adoption list and the Wish-list. Promote
  to planned: visual component catalogue is a natural
  strength of the class-based qlibrary and is currently
  under-used. Pairs with the "When to use Metal" page
  above as the visual half of the answer.

### High impact, high effort

- **Reference PDK** (`metal-pdk-academic` or similar)
  `[research]`
  Demonstrates the entry-points pattern from a realistic
  angle, so subsequent community PDKs have a worked example
  to follow. Without one, the entry-points hook is
  abstract.
- **Hosted web design viewer** `[research]`
  Already on the Adoption / Bigger plays list. Flagship
  demo plus a real adoption unlock — closes the "I want
  to look at a Metal design without installing anything"
  gap that today forces evaluators to clone the repo
  before they see a chip.

### Wish-list

- **Salt-style extension marketplace / index page** `[wish]`
  The simpler `awesome-quantum-metal` (already on the
  adoption list) covers most of the need; a richer
  in-app discovery surface is a stretch goal.
- **Format converters to / from adjacent Python design
  libraries** `[wish]`
  Quantum and RF design teams increasingly use multiple
  Python frameworks side by side. Clean component-level
  converters would make Metal a friendly neighbour in
  mixed pipelines. Best owned jointly with the relevant
  project teams if there's interest.
- **Annual "State of Quantum Metal" report** `[wish]`
  Already on the Adoption list as research. Doubles as
  community visibility for grant proposals and external
  reporting.

---

---

## Adoption, DevRel, and onboarding

Making sure people *find* the project, *try* it, and *stick with* it.
Ideated post-v0.7.0 lite-by-default flip (which finally made one-click
trial viable).

### Shipped (v0.7.1)

- ✅ **"Open in Colab" button** in the README → tutorial 1.2 Quick Start
- ✅ **"Open in Codespaces" button** in the README
- ✅ **`CITATION.cff`** — GitHub "Cite this repository" widget on the repo page
- ✅ **Badge row refresh** — PyPI downloads, Python versions, CI, docs, stars, contributors
- ✅ **Repo description + GitHub topics** — punchy one-liner + tags for
  GitHub-search discoverability
- ✅ **Hero animated GIF** — 4-qubit chip built in 5 frames, embedded in README
- ✅ **Issue-template modernization** — Bug / Feature / Docs templates
  refreshed with v0.7.0 install paths, code-block sections for repros and
  tracebacks, and ROADMAP / FAQ pointers. Issues (not Discord) are the
  canonical route for support requests so nothing gets lost in chat
  scrollback. `.github/ISSUE_TEMPLATE/config.yml` surfaces Docs / Roadmap
  / PyPI links plus Discord as a community-chat link (NOT a support route).
- ✅ **JupyterLite tutorials on the docs site** — every notebook runnable
  in-browser via the Pyodide kernel, zero install. Lives under `/lite/`
  on the published docs site.

### Quick wins on deck (each <2 hours)

- **Open Graph image** `[research]` — controls how the repo / docs preview
  when shared on Twitter / Slack / Discord. Currently uses the GitHub
  default which is much weaker than a designed image would be.

### Medium effort (~half-day each)

- **Gallery page** (`docs/gallery.rst`) `[planned]` — eye-candy rendered
  images of representative designs (single transmon, two-qubit, surface-code
  patch, examples from `tutorials/E.Input-output-coupling/`). Showcases
  capability visually.
- **`SUPPORT.md` + `GOVERNANCE.md`** `[planned]` — currently support info is
  scattered across README / FAQ / contributor-guide. A single `SUPPORT.md`
  consolidates "where to ask, response expectations." `GOVERNANCE.md`
  matters for institutional adopters (labs, companies) deciding whether to
  commit time.
- **Devcontainer config** (`.devcontainer/devcontainer.json`)
  `[planned]` — one-click cloud dev environment from any GitHub page.
  Pairs with the lite install for a 90-second "open and run." (Note:
  Codespaces *button* already shipped in v0.7.1 — this is the
  devcontainer that customizes the env it launches into.)
- **Recipes section in docs** `[planned]` — short focused how-tos
  ("Design a CPW resonator at 5 GHz", "Sweep transmon pad gap and extract
  frequency", "Export GDS with custom layer mapping"). Each <50 LOC,
  copy-paste-runnable. Tutorials are deep dives; recipes are the
  Stack-Overflow-style "I just want to do X" entry point.

### Bigger plays (multi-day)

- **`awesome-quantum-metal` companion repo** `[research]` — curated list:
  papers using Metal, lab tooling on top of Metal, talks, integrations.
  Community-curated, standard `awesome-*` pattern.
- **"When to use Metal" page** `[research]` — use-case-driven
  framing of which problems Metal is shaped for and which
  workflows hand off elsewhere. Highly searched by evaluators.
  (Superseded direction for the older "comparison page" idea —
  see the parallel item under "Group and lab adoption pathway".)
- **Web-based read-only design viewer** `[research]` — overlaps with the
  Jupyter widget viewer in the renderer roadmap; a web-hosted version on
  the docs site would be a flagship demo.
- **Annual / quarterly community report** `[research]` — "State of Quantum
  Metal 202X" with downloads, contributors, papers citing, new features.
  Community visibility artefact, useful for grant proposals and
  external reporting.

---

## Docs build cleanup `[research]`

Items deferred during the May 2026 docs-build pass (see PR #1085).
The build is now clean (0 warnings) but a few latent fragilities remain:

- **Analyses-module alias-path documentation.** Classes in
  ``qiskit_metal.analyses`` are reachable through two paths:
  (1) the alias path via ``__init__.py`` re-export
  (``qiskit_metal.analyses.EPRanalysis``), and (2) the real submodule
  path (``qiskit_metal.analyses.quantization.energy_participation_ratio.EPRanalysis``).
  Autodoc currently registers each class under both, which is
  benign for users but emits ``duplicate object description``
  warnings whenever the per-class stubs are reached via *both* an
  autosummary toctree and an automodule member walk simultaneously.
  Today this is avoided by careful toctree structuring; ideally we
  pick one canonical documentation path per class. Options:
  (a) stop re-exporting from ``__init__.py`` and require users to
  import from submodules (breaking API change — not desirable);
  (b) add ``:no-index:`` to all 16 per-class stubs in
  ``docs/apidocs/qiskit_metal.analyses.*.rst`` so only the
  ``automodule`` walk wins;
  (c) regenerate the stubs to use the full submodule path in their
  ``currentmodule`` directives. (c) is the cleanest if we ever
  re-run ``sphinx-autogen`` to refresh the stubs.

- **Sphinx-autosummary code-block leak.** Sphinx's autosummary
  extension scans *every* ``.rst`` file for ``.. autosummary::``
  and ``.. automodule::`` directives, **including those nested
  inside ``.. code-block:: rst`` / ``.. code-block:: python``
  blocks** used for documentation examples. PR #1085 worked around
  this by escaping directive names (``.\.``) in the contributor
  guide so the examples don't accidentally fire at build time, but
  the underlying behavior is a foot-gun: any future docs example
  that includes a real autosummary directive will silently
  generate phantom RST files in ``docs/``. Possible fixes:
  (a) replace the in-text examples with ``literalinclude`` of a
  fixture file (out of scope of autosummary's scanner);
  (b) configure autosummary to ignore specific directories.

---

## Known bug-triage queue `[needs re-verification]`

10 issues triaged on 2026-05-22. **All reports are on Metal 0.5.x or earlier**
(0.1.5 / 0.5.2.post4 / 0.5.3.post1); none re-verified against v0.7.x. Before
acting on any, reproduce on a current `quantum-metal[full]` install — some
may have been fixed by the lite-flip / renderer-protocol / Qt6 work and just
need closing.

**Real bugs with reproducer + community-proposed fix:**

- [#1036](https://github.com/qiskit-community/qiskit-metal/issues/1036)
  `RoutePathFinder` path-penetrates-component — `unobstructed()` returns
  True when both segment endpoints lie inside a component bounding box even
  though the segment intersects the actual contour. Reporter included
  reproducer + proposed fix. **High value: real correctness bug, easy win.**
- [#1086](https://github.com/qiskit-community/qiskit-metal/issues/1086)
  `RouteMeander` produces asymmetric geometry for rotated routes (filed
  2026-05-22 with HFSS-validation rubric, workaround already in
  `scripts/make_hero_gif.py`).

**Easy / small fixes:**

- [#1042](https://github.com/qiskit-community/qiskit-metal/issues/1042)
  `design.to_python_script()` omits `from numpy import array` from the
  generated header. One-line fix in the export template. Good first-PR.

**Ansys 2025R1 compatibility cluster** (likely related):

- [#1041](https://github.com/qiskit-community/qiskit-metal/issues/1041)
  `EPR Analysis: TypeError: tuple indices must be integers or slices,
  not Quantity` in pyEPR's `DistributedAnalysis`.
- [#1046](https://github.com/qiskit-community/qiskit-metal/issues/1046)
  `sim.save_screenshot()` throws COM/RPC error on Ansys 2025R1.

  Both on Metal 0.5.x + old `renderer_ansys` COM path. Worth re-trying
  with v0.7.x + the new `renderer_ansys_pyaedt` (no COM); may already
  be resolved.

**Qt6 / native crashes — `qm.view()` headless alternative now exists:**

- [#1048](https://github.com/qiskit-community/qiskit-metal/issues/1048)
  MetalGUI segfaults at `main_window.show()` on Ubuntu 24.04 + PySide6
  6.11.0. Plain `QMainWindow().show()` works, so it's a Metal-specific
  Qt6 interaction. v0.7.0's `qm.view()` is the documented headless path
  for these users; longer-term plan is the Jupyter `qm.gui()` widget.

**Needs reproducer:**

- [#1052](https://github.com/qiskit-community/qiskit-metal/issues/1052)
  Xmon angle bug — bus angle 270° doesn't put pin at bottom. Reporter
  posted screenshots but left "Steps to reproduce" + "Expected behavior"
  sections blank.

**Filed by us (info-only, needs external action):**

- [#1079](https://github.com/qiskit-community/qiskit-metal/issues/1079)
  HFSS / Q3D runtime validation needed for the lite-flip lazy-imports
  (PR #1078). Needs someone with an AEDT license to spot-check.

---

## External workshops & training `[reference]`

Curated workshop materials that exercise Metal end-to-end.  Not maintained
as part of this repo — version pins float independently.

- **QDW 2025 — `tutorials_quantum_device_design`** `[frozen, pre-v0.5]`
  https://github.com/zlatko-minev/tutorials_quantum_device_design

  4-notebook walkthrough: layout → transmon+resonator → qubit-qubit
  coupling → end-to-end project. Uses **Palace** (open FEM) via
  **SQDMetal**. Pinned to `pyepr-quantum==0.8.5.7` + `pyaedt==0.6.46`,
  Metal pre-v0.5 era. Historical reference — bringing it forward would
  mean re-validating against current SQDMetal + Palace + Metal chain
  (high effort, not planned).

- **QDW 2026 — `qdw26-workshop-materials`** `[active, near-mainline]`
  https://github.com/quantum-device-consortium/qdw26-workshop-materials

  Same 4-notebook progression, now Dockerized with `uv` lockfile.
  Currently pinned to `abhishekchak52/qiskit-metal@gui-import-isolation`
  (a pre-release fork of what is now v0.7.0 lite-flip). **Quick
  follow-up:** swap that pin for mainline `quantum-metal>=0.7.1` from
  PyPI (one-line change, removes the fork dependency).

---

## GUI / UX wishes `[wish-list]`

Small UX improvements collected from real use. Lower priority than the
roadmap items above, but tracked here so they don't get lost.

- **Thumbnail icons for every qubit / component in the GUI library
  toolbar** `[wish]` — the left-side component browser currently shows
  a flat text list of `TransmonPocket`, `TransmonCross`,
  `TransmonInterdigitated`, etc. A small (~64×64) preview icon next to
  each name would let users pick a geometry visually instead of having
  to remember which class is which shape. Applies to both the Qt
  `MetalGUI` (`src/qiskit_metal/_gui/widgets/qlibrary_display/`) and
  the future Jupyter `qm.gui()` library panel (planning in
  `_dev/jupyter_gui/feature-map.md`). Implementation: render each
  component once headlessly via `qm.view(component)` and cache as PNG
  in `docs/_static/component_icons/` — same reproducible-asset pattern
  the hero GIF (`scripts/make_hero_gif.py`) uses. Existing assets in
  `_imgs/components/` may already cover some.

---

## How to help

- **Use it and file issues.** Especially: anything that
  bit you when you went off the happy path.
- **Try the lite install** once v0.7.0 ships (or now,
  with `pip install quantum-metal --no-deps` followed by
  the deps you actually want) and tell us what breaks.
- **Bring a backend.** If you maintain or work with an
  open-source EM solver and want to see it as a
  first-class Quantum Metal target, the renderer
  protocol is documented at
  `docs/architecture/renderer_protocol.md`.
- **Join the conversation.** Discord:
  https://discord.gg/kaZ3UFuq. QDC governance page:
  https://qdc-qcsa.vercel.app.
