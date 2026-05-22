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
