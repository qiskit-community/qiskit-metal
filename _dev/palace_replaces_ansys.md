# Making Palace a first-class peer to Ansys in Quantum Metal

**Audience**: Quantum Metal maintainers (and any SQDMetal folks who care
to peek). **Status**: scoping analysis — internal thinking to help us
reason about the option space. **Not a commitment.**

> A note on what this doc is and isn't:
>
> - It's Metal-side scoping: how we'd architect a Palace path **if** we
>   build one, and how that interacts with prior work in the community.
> - The "recommended" path below is our tentative working preference,
>   not a decision. It's framed concretely so the conversation has
>   something to push back on, not because anything is locked in.
> - Coordination with SQDMetal is the gating question. The shape of any
>   integration depends on what works for them — see
>   [`sqdmetal_coordination_issue_draft.md`](./sqdmetal_coordination_issue_draft.md)
>   for the open conversation. Outcomes range from "we partner deeply"
>   to "we just promote SQDMetal from our docs and don't ship our own
>   Palace integration at all" — both are genuinely fine.
> - Phase numbers and week estimates are illustrative ranges, not
>   commitments. Calendar reality depends on who picks this up and how
>   the coordination conversation lands.

> "Replace" is shorthand. HFSS / Q3D stay supported in Metal for years;
> too many users have AEDT licenses and existing workflows. This doc is
> about making **Palace a first-class peer** to Ansys: default for new
> tutorials, recommended path for users without AEDT, both backends
> coexisting in the analysis layer.

---

## 1. What Ansys does in the workflow today

Four services that downstream analyses consume, plus a fifth thing
(live AEDT GUI) that Palace can't replace because it's batch/CLI:

| # | Service | Ansys tool | Consumed by | Output shape |
|---|---|---|---|---|
| 1 | Capacitance matrix | Q3D electrostatic | `LOManalysis` | Maxwell C matrix |
| 2 | Eigenmode freqs + Q | HFSS Eigenmode | `EigenmodeSim` | mode freqs, Q, field snapshots |
| 3 | EPR (participation ratios, anharmonicity, cross-Kerr) | HFSS Eigenmode + field integration | `EPRanalysis` | participation matrix + derived |
| 4 | S-parameters / impedance | HFSS Driven Modal | `ScatteringImpedanceSim` | S-params, Z matrix |

"First-class peer" means Palace produces data with the same downstream
shape for #1–#4, so the analysis classes don't need to know which
backend ran.

---

## 2. Palace ↔ Ansys solver mapping — and where the cracks are

| Ansys service | Palace equivalent | Difficulty | Where it gets thorny |
|---|---|---|---|
| Q3D electrostatic | Palace `Electrostatic` | 🟢 same physics | Mesh-convergence behavior differs; coarse-mesh results may diverge from Q3D |
| HFSS Eigenmode | Palace `Eigenmode` | 🟢 modes + Q | Loss models are younger; Q on lossy geometries needs careful validation |
| HFSS Driven Modal | Palace `Driven` (freq-domain) | 🟡 port tagging is real work | Adaptive frequency-sweep more limited than HFSS; wave-port impedance has fewer knobs |
| HFSS → EPR | Palace eigenmode + field integration + EPR | 🔴 hardest | pyEPR was written against HFSS field-export format; doesn't read `.pvtu` |

EPR is the hard one because of plumbing, not physics. Two routes:

- **(a)** Teach pyEPR to read Palace `.pvtu`. Cross-project change.
- **(b)** Do the EPR field integration ourselves in `renderer_palace/`,
  hand pyEPR pre-computed participation matrices. **Conservative default.**

### Honest gaps vs HFSS

Palace covers the four categories; it doesn't match HFSS at every edge.
Real differences a user can hit:

- **PML / absorbing boundaries** — HFSS has decades of tuning recipes;
  Palace's PML is younger.
- **Frequency-dependent materials** — both support it; HFSS has more
  packaged material libraries and forum recipes.
- **Convergence diagnostics** — HFSS's adaptive-solve + S-conv / Δf-conv
  reporting is more mature.
- **Edge cases** — complex 3D (flip-chip with TSVs, airbridges) likely
  converges faster in HFSS today. Not because Palace can't, but because
  the recipes aren't written down.
- **Documentation** — 20+ years of HFSS forum posts vs. Palace's young
  community.

None of these block "first-class peer". They're reasons to be honest
with users about when each tool fits better, and to validate against
designs that are well-understood in both — not just one.

---

## 3. Prior art and allies — SQDMetal

[sqdlab/SQDMetal](https://github.com/sqdlab/SQDMetal) is community-aligned
(self-described as "an extension of Qiskit Metal", Apache 2.0, accepts
`QDesign` objects directly). More active than Metal right now: ~30
commits in 6 months, 6+ contributors, MRU 2026-05-20. **They are friends,
not competitors.**

Their PALACE module covers all four services above end-to-end, including
EPR-flavoured analysis on Palace outputs.

**Honest caveats on the prior-art claim:**

1. **I haven't independently verified their EPR math** against a known
   HFSS result. Their integration runs and produces numbers; whether
   those numbers agree with HFSS within the release-gate tolerance (§5)
   is something we have to *actually validate*, not assume. Strong
   starting point, not a guarantee.
2. **Packaging tension** — their `pyproject.toml` declares `quantum-metal`
   as a hard dep (circular if we depend on them), pins Python 3.11-only,
   and treats COMSOL bindings (`mph`) as mandatory not optional. We
   can't simply `pip install sqdmetal` from Metal. The fix has to be on
   their side, or take the form of a shared module.
3. **Coordination friction is real** — aligning on architecture, code
   review across two teams, joint release cadence. Realistic adds
   4–6 weeks of calendar vs going alone. Worth it for the community
   signal and the existing work; we shouldn't pretend it's free.

**Default operating mode**: coordinate from week 1. Open the
conversation, share this doc, agree on integration shape before cutting
production code.

---

## 4. Integration shapes (architecture on Metal's side)

Independent of *who* does the work — that's the SQDMetal coordination
question. These are about how the renderer fits Metal.

### A. API-compatible renderer; analyses unchanged

`QPalaceRenderer(QRendererAnalysis)` matches the public API of
`QHFSSPyaedt` / `QQ3DPyaedt` method-for-method. Existing analyses work
unchanged. User swap:

```python
sim = EigenmodeSim(design, renderer="palace")    # was "hfss_pyaedt"
```

- **Pros**: smallest user change; analyses don't change; opt-in via `[palace]` extra.
- **Cons**: carries forward HFSS API idiosyncrasies; "API-compatible" ≠
  "drop-in identical results" (mesh / convergence differ); hides EPR
  approach (a vs b) inside the renderer.

### B. Strategy pattern in analysis classes

Refactor `EigenmodeSim`, `LumpedElementsSim`, `ScatteringImpedanceSim` to
dispatch to a backend interface. Renderers emit normalized data; analyses
transform it.

- **Pros**: right long-term shape; aligns with the
  `design.render(backend=...)` direction on the roadmap; new solvers
  plug in cheaply.
- **Cons**: touches mature analysis code; destabilization risk on the
  HFSS path while we build the Palace path; bigger upfront design.

### C. Minimal v1 — skip EPR

`renderer_palace/` covers capacitance + eigenmode-freq only. EPR and
S-params slip to v2. HFSS stays the path for EPR users for now.

- **Pros**: smallest scope; sidesteps EPR risk for v1.
- **Cons**: doesn't help academic users without AEDT (who need EPR);
  full peer-status story stays incomplete; v2 is a bigger push.

### D. Workflow-first parallel path

Don't try to match Ansys's renderer API. New Palace-native tutorials
replace 4.01 / 4.02 / 4.11 / 4.12 as the primary path; renderer API is
whatever fits Palace cleanly.

- **Pros**: not constrained by HFSS API; lets Palace's strengths
  (AMR, MPI, no licensing) drive the story.
- **Cons**: two parallel workflow paths to maintain; user mental-model
  split right when we unified it with lite-by-default.

| Option | First-class peer? | EPR risk | Existing analyses touched? |
|---|---|---|---|
| A | ✅ full | 🔴 | 🟢 no |
| B | ✅ full + future-proof | 🔴 | 🔴 yes (mature code) |
| C | 🟡 partial | ✅ skipped | 🟢 no |
| D | 🟡 augments not peers | 🟡 separable | 🟢 no |

---

## 5. Working preference (tentative, subject to the SQDMetal conversation)

If we end up building, our current best-guess shape would be:
**Architecture: Option A. Coordination: co-developed with SQDMetal from
week 1, whatever "co-developed" ends up meaning to them.**

But the entire plan below is contingent on the
[SQDMetal coordination conversation](./sqdmetal_coordination_issue_draft.md)
landing in a way that makes sense for both sides. Any of these are
acceptable outcomes:

- They prefer **option 1** (we just promote SQDMetal from our docs) →
  the phased plan below collapses to "update some docs"; we ship no
  Palace renderer of our own. Smallest possible footprint and
  arguably the right answer.
- They prefer **option 2** (shared `quantum-metal-palace` package) →
  phasing below largely applies but lives in a separate repo we
  co-own.
- They prefer **option 3** (upstream their PALACE module into Metal) →
  the plan below is what it looks like.
- They prefer **no formal coordination** → we re-evaluate. We do not
  fork without their blessing.

Coordinate first; phase second.

### Phase 0 — coordination (calendar 2–4 weeks; engineering ~3 days)

Open the conversation with SQDLab. Share this doc. Propose three
coordination shapes and let them pick:

1. **Co-maintained module upstreamed into Metal** as `renderer_palace/`,
   with SQDLab as `CODEOWNERS`. Cleanest packaging (Metal's pyproject is
   not circularly self-dependent, supports 3.10–3.12, doesn't require
   COMSOL).
2. **Shared `quantum-metal-palace` package** that both projects consume.
   They publish; both depend.
3. **Status quo** — they keep SQDMetal/PALACE; Metal vendors with
   attribution if needed. Last resort.

Calendar dominated by their response cycle; engineering is small (read
their code, write a coordination proposal, exchange a few rounds). **Do
this before cutting Phase 1 code.**

### Phase 1 — capacitance + eigenmode-freq (4–8 weeks)

Ship the renderer skeleton covering services #1 and #2 (cap matrix +
eigenmode freqs+Q). Wire through `LOManalysis` and the freq half of
`EigenmodeSim`. Cross-validate (see "Validation" below).

This is Option C's scope — covers the LOM tutorial workflow. Ship as
v0.8.x preview with `[palace]` extra, labeled experimental.

Estimate range reflects:
- Best case 4w: SQDMetal co-developing, their module ports cleanly.
- Worst case 8w: more refactoring of their meshing pipeline to align
  with our `QGmshRenderer`, coordination latency.

### Phase 2 — EPR (4–8 weeks)

Port SQDMetal's field-integration to `renderer_palace/` (approach (b);
keep pyEPR unchanged). Wire through `EPRanalysis`. Validate.

Estimate range:
- Best case 4w: their EPR code is correct and ports easily.
- Worst case 8w: cross-validation fails first attempt, need to dig into
  field-integration math (real risk).

If we miss the validation gate, Phase 2 slips and v0.8.x ships Phase 1
scope only.

### Phase 3 — S-parameters (3–4 weeks; can slip to v0.9)

`Driven` solver + port tagging + `ScatteringImpedanceSim` integration.
Lowest priority of the four services in tutorials today.

### Phase 4 — Docker image (4–6 weeks calendar; can run concurrent with Phase 2+)

`quay.io/qdc/quantum-metal-palace:VERSION` bundling Quantum Metal lite +
Palace (built) + gmsh + Jupyter. **This is the actual user-adoption
unlock** — Palace's C++ build (CMake / MPI / MFEM / libCEED) is what
keeps newcomers out, not the renderer code.

Estimate accounts for: base-image choice, MFEM + libCEED build pinning,
keeping it under ~2 GB, joint testing, ongoing maintenance for each
Palace release. **Realistic minimum 4w, not "1 week concurrent".**
Propose joint ownership with SQDLab; both projects' users benefit.

### Phase 5 — tutorial migration (1–2 weeks)

Migrate **one** Section-4 tutorial (4.02 Eigenmode + EPR) to use Palace
as the primary path; keep an HFSS variant labeled "for AEDT users".
**Don't migrate every tutorial** — let users self-select. We'll learn
what to convert next based on which existing Ansys tutorials get the
most JupyterLite hits and issue reports.

### Honest total

**12–28 weeks** of engineering, **with SQDMetal co-development**, **for
the v1 first-class-peer story**. Add coordination calendar (2–4w upfront,
ongoing review latency). HFSS path stays in place throughout.

If we go alone (no SQDMetal coordination), estimates roughly double on
Phases 1 and 2.

### Validation — what counts as "it works"

Not one design. Three:

| Design | Source | What we measure |
|---|---|---|
| **Simple**: `TransmonPocket` default options | `tutorials/1 Overview/1.2` | cap matrix elements, single-mode freq, Q |
| **Medium**: transmon + CPW readout resonator coupled | `tutorials/4 Analysis/4.02` | 2-mode freqs, EPR matrix, χ |
| **Complex**: 4-qubit ring chip | `tutorials/2.../C.../2.21 Design a 4 qubit full chip` | 8+ modes, EPR cross-coupling |

For each, **document the HFSS reference result** (mesh settings, solve
settings, version) so the comparison is reproducible. Without a documented
HFSS reference, the comparison is meaningless.

**Release gates** (Palace vs HFSS, on each of the three designs):

| Quantity | Target | What "fail" means |
|---|---|---|
| Eigenmode frequencies | ±2% | Either a real physics gap or a port/boundary mismodel — dig in. |
| Capacitance matrix elements | ±5% | Mesh-convergence issue most likely; bump mesh and re-test. |
| Q values | ±20% | Loss-model differences expected; document, accept if explainable. |
| EPR participation ratios | ±10% on dominant element; ±25% on sub-dominant | Sub-dominant slop tolerable; if dominant fails, EPR ships v0.8.x |

Failure mode for v0.8.0 release:
- If Phase 1 designs all pass → ship Phase 1.
- If Phase 2 EPR fails on the Complex design only → ship Phase 2 anyway,
  document the gap, file follow-up for v0.8.x.
- If Phase 2 EPR fails on Simple or Medium → Phase 2 slips out of v0.8.0
  entirely; ship Phase 1 alone, EPR comes later.

---

## 6. What this still doesn't solve

1. **Palace build pain** — Phase 4 Docker image, but users wanting to
   build from source still have a C++ problem.
2. **EPR correctness** — release gate is concrete but still a real risk.
3. **AEDT GUI workflow** — gone. Inherent Palace limitation.
4. **HFSS edge cases** — flip-chip / TSV / airbridge designs likely
   work better in HFSS for the foreseeable future. We document this; we
   don't try to fix it in v1.
5. **Resource constraint** — 12–28 engineering weeks assumes someone is
   doing them. Today that's Metal maintainer(s) + SQDLab contributors +
   community. **If the people aren't there, calendar stretches further.**
   Real assumption to validate before kickoff.
6. **License check on Palace itself** — AWS Palace is Apache 2.0
   (verified). Same for SQDMetal. Same for Quantum Metal. No compatibility
   issues.
7. **Long-term maintenance** — Palace ships new releases; JSON schema
   evolves. We pin to a tested version and bump deliberately. Tracking
   cost is real, ~2–4 weeks per Palace major bump.

---

## 7. What needs to happen next (no decision in this doc)

This doc doesn't decide anything. Two questions to answer next, in this
order:

**Step 1 — open the SQDMetal conversation.** Send the issue draft at
[`sqdmetal_coordination_issue_draft.md`](./sqdmetal_coordination_issue_draft.md)
to the SQDLab team. Their answer drives everything else.

**Step 2 — depending on their answer, then we pick from these:**

Architecture (only matters if we end up building):

- Option A with phased delivery — our tentative preference if we build
- Option C (capacitance + eigenmode-freq only, no EPR for v1) — if EPR cross-validation risk is the dealbreaker
- Option B (strategy pattern first, defer Palace 3–4 months) — if we'd rather invest in the long-term shape
- Option D (workflow-first parallel, not full peer)

Coordination shape (depends entirely on SQDMetal's preference):

- Option 1 from the SQDMetal issue (we just promote them from our docs, no code coupling)
- Option 2 (shared `quantum-metal-palace` package)
- Option 3 (upstream their PALACE module into Metal)
- No formal coordination (we re-evaluate; don't fork without their blessing)

**Suggested cadence:**

- Day 1: send the SQDMetal issue.
- Days 2–14: their response window. No internal Phase-1 work yet — we don't want to walk into the conversation with code that presumes an answer.
- Week 3+: based on their response, pick the architecture + coordination combination from above; start whatever shape of work it implies (which may be "very little").

If they're slow or unresponsive: re-ping after 2 weeks. If still silence after another week, we re-think — most likely landing on option 1 (just promote them from our docs) since starting our own integration without their blessing would be poor community practice.
