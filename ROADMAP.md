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

Quantum Metal is the open-source design plane for
superconducting quantum chips: a Python library where you
build a chip from `QComponent`s, attach analyses, and hand
the result to whichever solver / fab / orchestrator you
want. The library itself is solver-agnostic; the renderers
are the integration layer with the outside world (GDS,
HFSS, Q3D, gmsh, Elmer, AWS Palace, ...).

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

## Now — the lite-by-default flip (v0.7.0)

The current v0.6.x line ships every heavy dependency
(`pyside6`, `gmsh`, `pyaedt`, `pyEPR-quantum`, `qdarkstyle`)
in `[project.dependencies]`, so `pip install quantum-metal`
pulls hundreds of MB and assumes Qt is welcome. The v0.7.0
release flips this: heavies move into extras (`[gui]`,
`[fem]`, `[ansys]`, `[full]`) and the base install becomes
the orchestration-friendly minimal surface.

The work is sequenced as several smaller PRs so each lands
green:

- **Eager-import audit** `[in-progress]`
  Sweep `src/qiskit_metal/` for module-level imports of
  the heavies, classify each as already-lazy, safely
  guarded, or needs-lazification. Output drives the rest
  of the flip.
- **Lazify the heavies** `[planned, v0.7.0]`
  Move every `import pyside6 / gmsh / pyaedt / pyEPR`
  out of module top-level into functions or
  `__getattr__` shims. Friendly `ImportError`s point
  users at the right extra.
- **Test-suite skip-cleanliness** `[planned, v0.7.0]`
  Add `pytest.importorskip` where needed so the full
  suite passes on a lite install (with skips, not
  failures).
- **Expanded `tests-lite` CI matrix** `[planned, v0.7.0]`
  Current `tests-lite` runs one combo; expand to
  3.10/3.11/3.12 × ubuntu/macos/windows so the lite
  path has the same safety net as the full path.
- **v0.6.2 deprecation release** `[planned, before v0.7.0]`
  Ship `DeprecationWarning` on `import qiskit_metal`
  telling users to install `quantum-metal[full]` if they
  want the current all-in experience after v0.7.0.
- **The flip** `[planned, v0.7.0]`
  Move heavies out of base deps. Bump to v0.7.0. Update
  changelog, tutorials, README install matrix.

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
- **Plugin discovery via entry points.** External
  renderers and component libraries currently require
  monkey-patching or vendoring. A
  `qiskit_metal.renderers` and
  `qiskit_metal.qlibrary` entry-point namespace lets the
  community ship third-party packages.
- **Docs hosting reassessment.** GH Pages is current
  (years of SEO). Read the Docs config archived at
  `docs/_archive/readthedocs/` — revivable in minutes
  if/when per-PR previews, versioned docs, or the
  rebrand cutover make the switch worth it.

---

## Adoption, DevRel, and onboarding `[planned / research]`

The technical roadmap above gets us a great library. This section is about
making sure people *find* it, *try* it, and *stick with* it. Ideated May 2026
after the v0.7.0 lite-by-default flip made one-click trial finally viable.

### Quick wins (each <2 hours)

- **"Open in Colab" button** in the README `[planned]` — single biggest
  adoption lever. The lite install + `qm.view()` makes Colab a 60-second
  zero-friction trial path. Link directly to tutorial 1.2 Quick Start.
- **`CITATION.cff` file** `[planned]` — GitHub renders a "Cite this
  repository" widget on the repo landing page. Massive academic-credibility
  signal at near-zero effort. Source from existing `Qiskit_Metal.bib`.
- **Badge row refresh** `[planned]` — add PyPI downloads/month, GitHub
  stars, contributors, Python versions supported, CI status, docs.
- **Repo description + GitHub topics** `[planned]` — punchy one-liner and
  tags (`quantum-computing`, `superconducting-qubits`, `eda`,
  `quantum-chip-design`, `hfss`, `gmsh`, `quantum-hardware`) for GitHub
  search discoverability.
- **Hero animated GIF** `[planned]` — 6-second screen recording of
  `qm.view(design)` rendering a transmon inline. Show, don't tell.
- **Open Graph image** `[research]` — controls how the repo / docs preview
  when shared on Twitter/Slack/Discord.

### Medium effort (~half-day each)

- **JupyterLite tutorials in the docs** `[planned]` — `jupyterlite-sphinx`
  extension makes each notebook runnable in-browser, zero install. Major
  unlock for classroom / academic use.
- **Gallery page** (`docs/gallery.rst`) `[planned]` — eye-candy rendered
  images of representative designs (single transmon, two-qubit, surface-code
  patch, examples from `tutorials/E.Input-output-coupling/`). Showcases
  capability visually.
- **`SUPPORT.md` + `GOVERNANCE.md`** `[planned]` — currently support info is
  scattered across README/FAQ/contributor-guide. A single `SUPPORT.md`
  consolidates "where to ask, response expectations." `GOVERNANCE.md`
  matters for institutional adopters (labs, companies) deciding whether to
  commit time.
- **`.github/ISSUE_TEMPLATE/` audit + polish** `[planned]` — bug report,
  feature request, docs-issue templates. Reduces friction for first-time
  contributors and improves triage signal.
- **Codespaces / devcontainer config** (`.devcontainer/devcontainer.json`)
  `[planned]` — one-click cloud dev environment from any GitHub page.
  Pairs with the lite install for a 90-second "open and run."
- **Recipes section in docs** `[planned]` — short focused how-tos
  ("Design a CPW resonator at 5 GHz", "Sweep transmon pad gap and extract
  frequency", "Export GDS with custom layer mapping"). Each <50 LOC,
  copy-paste-runnable. Tutorials are deep dives; recipes are the
  Stack-Overflow-style "I just want to do X" entry point.

### Bigger plays (multi-day)

- **`awesome-quantum-metal` companion repo** `[research]` — curated list:
  papers using Metal, lab tooling on top of Metal, talks, integrations.
  Community-curated, standard `awesome-*` pattern.
- **Comparison page** ("Metal vs. ...") `[research]` — honest comparison
  vs. Ansys Workbench / commercial EDA / hand-coded GDS. Highly searched
  by evaluators.
- **Web-based read-only design viewer** `[research]` — overlaps with the
  Jupyter widget viewer in the renderer roadmap; a web-hosted version on
  the docs site would be a flagship demo.
- **Annual / quarterly community report** `[research]` — "State of Quantum
  Metal 202X" with downloads, contributors, papers citing, new features.
  Doubles as institutional fundraising / partnership signal.

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
