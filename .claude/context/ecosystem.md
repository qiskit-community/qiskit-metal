# Ecosystem — who uses Quantum Metal and why decisions are made

Read this when making roadmap, API, or version decisions. For the
"how things are structured" view, see `architecture.md`.

## The three user groups

Decisions on this project should weigh impact on each:

### 1. Academic researchers (the growth lever)

Graduate students and postdocs designing superconducting circuits
for their group's experiments. Typically:

- Run on shared cloud notebooks (Colab, Binder, JupyterHub, IBM
  Quantum Lab) — **PySide6 doesn't install cleanly on most of
  these**.
- Want to iterate on a design fast, visualise, run a parameter
  sweep, commit results to a paper figure.
- Don't have Ansys licenses; do their own analysis in Python
  (qutip, scqubits, custom code).
- Will abandon a tool on the first installation failure.

**This is why the v0.6.1 headless work matters.** Pre-v0.6.1, this
group hit a wall on `pip install` or on the first `MetalGUI(design)`
call.

### 2. Industrial fab engineers (the existing base)

Engineers at IBM, Quantinuum, Rigetti, and university-spinout
labs. Typically:

- Run on a workstation with Ansys AEDT installed locally.
- Use the desktop `MetalGUI` for interactive design.
- Care deeply about HFSS / Q3D solver correctness — silent
  S-parameter errors cost weeks of fab time.
- Tolerate version pins and complex installs because the tooling
  is mature.

**This is why HFSS-touching code is a hard-touch zone.** Any
behavioural change without a validated solve is a regression that
this group eats.

### 3. Educators and outreach (the long tail)

Quantum Workshop instructors, Quantum Device Workspace (QDW), Quantum
Device Consortium (QDC), online courses, hackathons.

- Need a clean "first 30 lines" story that works on Day 1 of a
  workshop.
- Care about tutorial quality and discoverability more than
  feature depth.
- Drive adoption among new students who eventually become group 1
  or 2.

**This is why tutorial 1.4 (Headless quick view) ships, why the
"no-Qt callout" goes on every notebook, and why
`docs/headless-usage.rst` exists.**

## Repo relationships

### pyEPR (sibling)

[`zlatko-minev/pyEPR`](https://github.com/zlatko-minev/pyEPR) — the
EPR analysis library. PyPI: `pyEPR-quantum`.

Quantum Metal depends on pyEPR for:

- Ansys COM bridge (`pyEPR.ansys.parse_units`, etc.) — used by
  the legacy `renderer_ansys/` track.
- Hamiltonian / EPR analysis utilities.

**Cross-repo coordination protocol**: when a change in pyEPR's
public API affects metal, both repos get coordinated PRs. The
HFSS 2024.1+ rename was the canonical example (pyEPR PRs #172,
#176 + metal PR #1051 + the test suite in
`tests/test_pyepr_integration.py` and
`tests/test_solution_types.py` that pin the API).

The new (v0.9.5+) `pyEPR.solution_types` module is intentionally
identical in structure to metal's own
`qiskit_metal.renderers.renderer_ansys.solution_types`. They're
kept as parallel implementations rather than one importing the
other so an old pyEPR install doesn't break new metal and vice
versa.

### pyaedt (upstream)

Ansys's official Python interface to AEDT. New track at
`renderer_ansys_pyaedt/` uses it. Currently pinned `<0.24` due to
bugs in 0.24 (noted Jan 2026).

### Ansys AEDT (the proprietary backend)

HFSS and Q3D Extractor are the gold standard for superconducting
chip EM analysis. Not open source. Required for the analysis
workflow that user group 2 depends on.

### AWS Palace (the future open-source FEM path)

[`awslabs/palace`](https://github.com/awslabs/palace) — AWS's
open-source FEM solver, comparable to HFSS for many quantum-chip
use cases. **Planned integration is a major roadmap item.**
Unlocks:

- Open-source validation of HFSS-touching changes (currently a
  hard blocker on every drive-by HFSS fix — see
  `lessons-learned.md`)
- A no-Ansys solve path for user group 1 (academic researchers
  who don't have Ansys licenses)
- An on-cloud solve path (Palace runs in AWS, no local install)

Until Palace ships, HFSS-touching code stays in the hard-touch
zone.

### Quantum Device Consortium (QDC) — community

[`qdc-qcsa.vercel.app`](https://qdc-qcsa.vercel.app) — the
community organisation that now maintains Quantum Metal (post-IBM
graduation). Decision-making body for breaking changes and
roadmap.

### Quantum Device Workspace (QDW)

[`qdw-ucla.squarespace.com`](https://qdw-ucla.squarespace.com) —
annual workshop hosted at UCLA/USC. Largest single audience for
new-user adoption each year.

## Documentation philosophy

- **Sphinx**: the canonical reference site at
  https://qiskit-community.github.io/qiskit-metal/
- **Tutorials**: 40+ Jupyter notebooks in `tutorials/`,
  hand-authored, organised by topic. Each gets a "no-Qt callout"
  at the top pointing at `qm.view(design)` for users without Qt.
- **API reference**: auto-generated from docstrings via Sphinx
  autodoc.
- **Architecture docs**: under `docs/architecture/` — currently
  one file (`renderer_protocol.md`); add more here as needed.
- **Agent docs**: this directory (`.claude/`).

When writing user-facing docs, target user group 1 first (they
don't have Ansys, they're on cloud notebooks, they need it to
*just work*). User group 2 has accumulated knowledge; they don't
need hand-holding for the basics.

## Release philosophy

- **SemVer** target post-v1.0; pre-1.0 we use minor versions for
  meaningful changes and patches for bug fixes only.
- **v0.6.x line**: stabilisation of qutip 5 + pyEPR 0.9.5 + HFSS
  2024.1+ support + the new headless rendering path. Additive
  extras for `[gui]`/`[ansys]`/`[fem]`/`[full]`.
- **v0.7.0 planned**: flip the default install to lite (no Qt,
  Ansys, gmsh by default; opt-in via extras). Breaking for users
  who install via `pip install quantum-metal` and expect the
  desktop GUI to "just work" — needs migration messaging.
- **Release procedure**: see `.claude/commands/release.md`.

## Adoption strategy

Roughly:

1. **Lower the install friction** — done in v0.6.1 via the
   headless path. `pip install quantum-metal[lite]; qm.view(design)`
   works on any matplotlib-aware environment.
2. **Make the first 30 lines work** — tutorial 1.4 + the
   callouts on existing tutorials. Reader can copy-paste from any
   tutorial onto Colab and follow along.
3. **Ship a modern interactive viewer** — the "bigger project"
   (Plotly/ipympl/Jupyter widgets), planned post-v0.6.x.
   Replaces the Qt GUI for users who want pan/zoom + click-select
   without a desktop install.
4. **Unblock Ansys-free validation** — AWS Palace integration.
   Then every contributor can test HFSS-adjacent changes without
   a Windows + AEDT setup.

## What this means for your changes

When deciding whether to take on a task, weigh:

- **Does it benefit group 1?** Lower install friction, headless
  paths, tutorial coverage, lite extras — high-leverage.
- **Does it risk breaking group 2?** Anything HFSS / Q3D / `_gui/`
  touching — needs validation. Document the bug; don't fix it
  silently.
- **Does it help group 3 explain the tool?** Tutorial polish,
  docs clarity, error messages — modest leverage but compounds.
- **Does it move us toward Palace / lite-by-default / modern
  viewer?** Tier-2 / tier-3 roadmap work — coordinate with
  maintainers (you're not making the strategic call solo).

## Cross-references

- For the technical "what's where" view: `architecture.md`
- For "stuff that bit us": `lessons-learned.md`
- For specific recurring tasks: `.claude/commands/*.md`
