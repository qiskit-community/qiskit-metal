# Quantum Metal in the open-source SC-quantum design ecosystem

**Status**: 🟡 research / analysis. Not a commitment to anything specific.
**Audience**: Quantum Metal maintainers. **Companion to**:
[`palace_replaces_ansys.md`](./palace_replaces_ansys.md) +
[`sqdmetal_coordination_issue_draft.md`](./sqdmetal_coordination_issue_draft.md).

---

## TL;DR

Quantum Metal sits at the **chip-design** layer. Around it, distinct
layers each have one (or several) actively-maintained open-source
projects that already integrate with us — or could. Today there's no
shared map; users discover this ecosystem by accident.

**Recommendation**: ship a single `ECOSYSTEM.md` (or `docs/ecosystem.rst`)
that maps the layers, names the tools, links to each, and labels the
current integration status with Metal. Add a brief "Used with" section
to the main `README.md` that points there. **Reach out to the active
adjacents** (SQDMetal, SQuADDS, pypalace) with a light touch — let them
know we're framing this as an ecosystem and want their links / blurbs
to be accurate.

**Don't** try to coordinate every project into a single governance
structure. The ecosystem is healthier when projects stay independent
but are well-mapped.

---

## The layered model

```
                     ┌─────────────────────────────────────────┐
   Design discovery  │  SQuADDS (LFL-Lab) — qubit design DB    │
                     │  ✅ already uses Qiskit Metal           │
                     └────────────────────┬────────────────────┘
                                          │
   ┌──────────────────────────────────────▼────────────────────────────┐
   │  CHIP DESIGN  ────  Quantum Metal (us) ───────────────────────────│
   │  Build QDesigns from QComponents, render to backends              │
   └──┬──────────┬──────────┬──────────┬──────────────┬───────────────┘
      │          │          │          │              │
      ▼          ▼          ▼          ▼              ▼
   GDS         GUI        Ansys      Open FEM      Quantization
   (gdstk)   (PySide6)    (pyaedt)   (gmsh/Elmer)  (pyEPR, scqubits, qutip)
   in core   [gui]        [ansys]    [mesh]        in core
                                       │
                                       ├── SQDMetal (sqdlab)     ✅ active; their PALACE module
                                       │   wraps Palace ← uses our QDesign
                                       ├── pypalace (Northwestern) 🟡 newer; also Palace
                                       │   wrapper; uses Qiskit Metal gmsh export
                                       ├── meshwell (simbilod)   🟡 2.5D meshing helper
                                       │   on top of gmsh/OCC; GPL-3.0
                                       └── AWS Palace            ← the solver itself
                                                  (open-source, Apache 2.0)
```

The picture above is the actual relationship — Metal in the center, the
ecosystem branching out at each backend axis. None of these are
competitors. **All are doing useful things at adjacent layers.**

---

## Inventory — each project with its actual role

### Already deeply integrated with Metal (in our codebase or required deps)

| Tool | Role | License | Status |
|---|---|---|---|
| [pyEPR-quantum](https://github.com/zlatko-minev/pyEPR) | EPR quantization from HFSS field data | BSD-3 | In our `[ansys]` extra |
| [scqubits](https://github.com/scqubits/scqubits) | Closed-form qubit-spectra / quantization | BSD-3 | In our base deps |
| [QuTiP](https://github.com/qutip/qutip) | Quantum dynamics | BSD-3 | In our base deps |
| [gmsh](https://gmsh.info/) | Mesh generation | GPL-2.0 | In our `[mesh]` extra |
| [Elmer FEM](https://www.elmerfem.org/) | Open FEM solver (capacitance / LOM) | LGPL | External binary, driven via subprocess |
| [pyaedt](https://github.com/ansys/pyaedt) | Python wrapper for Ansys AEDT | MIT | In our `[ansys]` extra |
| [Qiskit](https://github.com/Qiskit/qiskit) | Algorithm / circuit library | Apache 2.0 | Historical namespace (we're "Quantum Metal" now) |

### Community-aligned, separate projects that touch Metal

| Tool | Role | License | Integration with Metal today |
|---|---|---|---|
| **[SQDMetal](https://github.com/sqdlab/SQDMetal)** (SQDLab @ UQ) | Simulation wrapper for QDesign → Palace / COMSOL / capacitance / inductance / driven / eigenmode | Apache 2.0 | Accepts our `QDesign` objects directly. **Active outreach** ([draft issue](./sqdmetal_coordination_issue_draft.md)) on Palace coordination. |
| **[SQuADDS](https://github.com/LFL-Lab/SQuADDS)** (LFL-Lab @ USC, Sadman Shanto) | Validated qubit design database + interpolation tools; physics-based parameter prediction across geometries | MIT | Heavy Qiskit Metal integration; uses HFSS, Palace, and physics models. Has its own MCP server for AI agents (!). Lead dev Sadman was a v0.5 Metal contributor. |
| **[pypalace](https://pypalace.readthedocs.io/)** (Firas Abouzahr @ Northwestern) | Python toolkit for AWS Palace — config builders, mesh utils, sim launcher, LOM analysis | unclear (need to verify) | Supports gmsh export from Qiskit Metal layouts. **Recent / smaller** than SQDMetal. |
| **[AWS Palace](https://github.com/awslabs/palace)** (AWS Center for Quantum Computing) | Maxwell solver (eigenmode + driven + electrostatic + magnetostatic + AMR) | Apache 2.0 | No direct integration with Metal yet — the entire point of the scoping doc. |
| **[meshwell](https://github.com/simbilod/meshwell)** (Simon Bilodeau, single maintainer) | 2.5D meshing on top of gmsh + OCC via Shapely geometry inputs | **GPL-3.0** ⚠️ | Not currently used by Metal. Could be useful for cleaner extruded geometry, but the **GPL-3.0 vs our Apache 2.0** would force us into copyleft if we depend at runtime. |

### Adjacent ecosystem tools (not Metal-specific but worth knowing)

| Tool | Role | License | Why it's in the picture |
|---|---|---|---|
| [KQCircuits](https://github.com/iqm-finland/KQCircuits) (IQM) | GDS-based superconducting-circuit design framework | GPL-3.0 | The other major open-source SC design tool. Different philosophy (GDS-first vs `QComponent`-first). Some shared users. |
| [gdsfactory](https://github.com/gdsfactory/gdsfactory) | Broader photonic / circuit design with very large user base | MIT | More photonic than SC but increasingly used in SC too. Some users come to Metal from gdsfactory. |
| [CircuitQ](https://github.com/PhilippAumann/CircuitQ) | Quantization of arbitrary superconducting circuits | MIT | Adjacent to scqubits; narrower scope; smaller community. |
| [KLayout](https://github.com/KLayout/klayout) | GDS viewer/editor | GPL-3.0 | Where users open our GDS exports for inspection. Standard fab-pipeline tool. |
| [ParaView](https://www.paraview.org/) / [PyVista](https://github.com/pyvista/pyvista) | Field-data visualization (.pvtu, .vtk) | BSD | Where users view Palace / Elmer simulation outputs. SQDMetal's `PVDVTU_Viewer` builds on PyVista. |
| [meshio](https://github.com/nschloe/meshio) | Mesh format conversion | MIT | Useful glue if mesh formats diverge between tools. |

---

## Hard architecture question: how does pypalace fit?

**The complication**: there are now **two Python-side wrappers for Palace that integrate with Qiskit Metal** — SQDMetal/PALACE and pypalace.

What we know:
- **SQDMetal/PALACE** — mature, multi-contributor, comprehensive (eigenmode + capacitance + driven + inductance + PVD/VTU viewer), Apache 2.0.
- **pypalace** — newer (release status unclear), apparently single-maintainer (Northwestern), supports gmsh export from Metal layouts and LOM analysis.

**Three honest scenarios for how this resolves:**

1. **One emerges as the obvious choice.** If SQDMetal's Palace module is significantly more complete and active (looks that way today), pypalace may converge on it or fade. Metal coordinates with whichever ends up canonical.
2. **They have distinct niches.** pypalace might be optimized for a different workflow (e.g. AI-agent-driven sims, or specific Northwestern-group workflows). Both stay relevant.
3. **They merge or one absorbs the other.** Unlikely without active facilitation, but possible if both teams talk.

**What this means for our SQDMetal outreach (issue #1089's draft)**:

We should **briefly acknowledge pypalace exists** in the SQDMetal issue — not as a competing offer but as honest disclosure: *"we've also seen pypalace; we don't know how it intersects with your work and would value your read."* Otherwise the SQDMetal team finds out via the rendered issue and wonders why we didn't mention it.

**What this means for our action items**:

- Open a **lighter-touch issue** at pypalace too, after the SQDMetal conversation gets going. Same ideation framing: *"hi, we're mapping the ecosystem, would love to understand how you'd like to be referenced from Quantum Metal docs and what coordination (if any) makes sense."*
- **Do NOT** try to force a merger. Both teams should make their own calls. We just don't want to silently bless one project as canonical.

**What this means for the scoping doc** (`palace_replaces_ansys.md`):

Add pypalace as an alternative in §3 (Prior art and allies). Doesn't change the recommendation but makes the analysis honest.

---

## SQuADDS: a different conversation

SQuADDS is at a **different layer** than SQDMetal / pypalace. It's not "another Palace wrapper" — it's the **design-discovery / parameter-interpolation database** that sits *above* the chip-design layer (Metal) and uses Metal to generate designs from database queries.

The relationship to Metal is already strong:
- Heavy Metal integration (tutorials, codebase)
- Sadman Ahmed Shanto (lead dev) was a v0.5 Metal contributor
- They have their own MCP server for AI agents — directly aligned with our AI-orchestration roadmap
- Published in *Quantum* journal (Sept 2024), 26 releases, 55 stars

**Action**: This isn't a coordination issue like SQDMetal — we're already aligned. The action is making the relationship **visible in our docs**:
- Add SQuADDS prominently to the ecosystem map
- Link to their MCP server from our AI-orchestration ROADMAP entry (it's a real example of the orchestration profile we said we want)
- Light outreach to Sadman to coordinate cross-linking and ensure our descriptions of each other are accurate

**Possible follow-up later**: a Metal tutorial that uses SQuADDS to pull a known design from their database, render in Metal, simulate in Palace. End-to-end ecosystem demo. Compelling story for QDW.

---

## meshwell: probably skip for now

**Verdict**: don't depend on it.

Why:
- **GPL-3.0** vs our Apache 2.0 — if we depend at runtime, we'd have to relicense Metal or carry a license-incompatibility risk.
- We don't have a strong need today. Our `QGmshRenderer` uses gmsh directly via its Python bindings.
- It's a single-maintainer project at the moment.

When we *might* revisit:
- If we hit specific 2.5D meshing edge cases that meshwell's Shapely-based abstractions handle cleanly and gmsh's raw API doesn't.
- If meshwell relicenses or dual-licenses (unlikely but possible).

Worth noting in our ecosystem map for completeness, but not actionable for us right now.

---

## Did we miss any popular repos?

Yes — several worth knowing about, added to the ecosystem map.

### Now included in `docs/ecosystem.rst`

**Built on Metal (the headline category)**:
- **[ML_qubit_design](https://github.com/CosmiQuantum/ML_qubit_design)**
  (Fermilab + Northwestern, Olivia Seidel as primary contact) — ML-based
  inverse design predicting Quantum Metal parameters from target qubit
  properties via multi-layer perceptrons. Notebook-driven research
  project, modest stars (~5), 287 commits. **Important to highlight
  because it exemplifies the "built on Metal" story** — they explicitly
  use Quantum Metal simulation data as training material. AI-orchestration
  adjacent.

**SC-quantum-design adjacent**:
- **[KQCircuits](https://github.com/iqm-finland/KQCircuits)** (IQM
  Finland) — the other major open-source SC chip design framework.
  GDS-centric philosophy vs our QComponent-centric. Some users straddle.
- **[CircuitQ](https://github.com/PhilippAumann/CircuitQ)** — small but
  active quantization tool, alternative to scqubits for arbitrary circuits.

**Photonics-adjacent FEM** (noted briefly, not prominent):
- **[femwell](https://github.com/HelgeGehring/femwell)** (Helge Gehring,
  ex-gdsfactory team) — photonics-focused FEM library (eigenmode +
  thermal + RF CPW). 1,549 commits, 170 stars, GPL-3.0. **Listed for
  completeness because it can do RF CPW eigenmodes**, but the primary
  use-case is photonic, not SC-quantum. License (GPL-3.0) would also
  block runtime depending the way it would for meshwell.

**Visualization / glue**:
- **[PyVista](https://github.com/pyvista/pyvista)** — standard Python
  ParaView wrapper. Both SQDMetal and pypalace use it.
- **[meshio](https://github.com/nschloe/meshio)** — mesh format
  conversion. Useful glue when formats diverge.

### Deliberately downplayed: gdsfactory

`gdsfactory` was prominent in the previous draft. Re-reading honestly:
they're a much broader project (primarily photonic, growing into SC)
with a different design philosophy and a much larger user base than us.
Listing them prominently in our ecosystem could read as either:

- "Look, gdsfactory uses us!" (false — they don't, they have their own
  stack), or
- "We're competing for users with gdsfactory" (true-ish — some SC users
  evaluate both).

The right framing is a brief mention in "Other design tools (different
scope)" alongside KQCircuits, not in the headline "Built on Metal" or
"Solvers we integrate with" sections. That's what `docs/ecosystem.rst`
now does. We acknowledge them without amplifying.

### What we still don't highlight

- **[Qiskit](https://github.com/Qiskit/qiskit)** — historical namespace,
  not a design tool. Mention only when explaining the rebrand.
- Commercial-only tools (CST Studio, IE3D, etc.) — outside the
  open-source ecosystem story.

The honest answer to "did we miss any": **the SC-quantum design
ecosystem has 10–15 distinct active projects across the layers**. We
list every one that either (a) builds on Metal directly, (b) is a
solver / library we integrate with, or (c) is widely-known enough that
users will encounter it. The ecosystem doc curates this — it isn't
exhaustive.

---

## Concrete deliverables

### Recommended for this round

1. **Ship an ecosystem doc** — either as `ECOSYSTEM.md` at repo root or `docs/ecosystem.rst` in the docs site. Probably `docs/ecosystem.rst` so it renders into the published docs and is searchable. Roughly the structure of the "Inventory" section above.
2. **Add an "Ecosystem" section to `README.md`** that's 5 lines max and links to the full ecosystem doc. Don't bloat the README.
3. **Update `ROADMAP.md`** to reference the ecosystem doc and acknowledge tools beyond Metal.
4. **Light update to the SQDMetal issue draft** — add one sentence acknowledging pypalace exists.
5. **Add pypalace mention to `palace_replaces_ansys.md`** §3 — honest disclosure that there are two existing Palace wrappers in the Metal ecosystem.

### Recommended for follow-up (not this PR)

6. **Light outreach to SQuADDS** — Sadman Shanto. Coordinate cross-linking and accurate descriptions; possibly propose a joint tutorial later.
7. **Light outreach to pypalace** — Firas Abouzahr. After the SQDMetal conversation gets traction, same ideation-style "we're mapping the ecosystem" issue.
8. **Joint QDW 2026 panel?** "Ecosystem of open-source SC quantum design tools." Brings SQDMetal, SQuADDS, pypalace, Metal teams together publicly. Maybe a poster session. Low cost, high community signal.

### Explicitly **not** recommended

- A single governance body. The ecosystem is healthier when projects stay independent.
- A monorepo / mega-package. Same reason.
- Forks or vendoring without conversation.
- Trying to be exhaustive — we'll never list every tool. Curate the meaningful ones.

---

## Sources / references

- [SQDMetal](https://github.com/sqdlab/SQDMetal) (Apache 2.0; SQDLab @ UQ)
- [SQuADDS](https://github.com/LFL-Lab/SQuADDS) (MIT; LFL-Lab @ USC)
- [pypalace](https://pypalace.readthedocs.io/en/latest/) (Northwestern)
- [AWS Palace](https://github.com/awslabs/palace) (Apache 2.0; AWS CQC)
- [meshwell](https://github.com/simbilod/meshwell) (GPL-3.0; simbilod)
- [pyEPR](https://github.com/zlatko-minev/pyEPR) (BSD-3)
- [scqubits](https://github.com/scqubits/scqubits) (BSD-3)
- [KQCircuits](https://github.com/iqm-finland/KQCircuits) (GPL-3.0; IQM Finland)
- [gdsfactory](https://github.com/gdsfactory/gdsfactory) (MIT)
- [CircuitQ](https://github.com/PhilippAumann/CircuitQ) (MIT)
- [SQuADDS paper, Quantum journal Sept 2024](https://arxiv.org/abs/2312.13483)
- [SQDMetal paper, arXiv Nov 2025](https://arxiv.org/pdf/2511.01220)
