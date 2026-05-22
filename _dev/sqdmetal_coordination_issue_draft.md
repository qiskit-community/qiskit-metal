# Draft GitHub issue for sqdlab/SQDMetal

**Where to file**: <https://github.com/sqdlab/SQDMetal/issues/new>
**Status**: DRAFT — not filed. Local scratch in `_dev/`.
**Read time**: ~2 min.

---

## Title

Ideation / open thinking: how (if at all) might Quantum Metal and SQDMetal coordinate on Palace?

## Labels (suggested)

`discussion` · `question`

## Body (copy-paste ready — no blockquote markers)

---

Hi SQDLab team — friendly hello from the Quantum Metal / QDC maintainers 👋

This is more "thinking out loud" than a concrete ask. We've been brainstorming how Quantum Metal might offer a first-class Palace path one day, and pretty quickly landed on "the obvious starting point is to talk to the people who've already done this well." Hence this issue — we'd love your take while everything's still ideas, rather than show up with a half-built thing later.

### What we're noodling on

The idea of making AWS Palace a first-class peer to HFSS/Q3D inside Quantum Metal — not replacing Ansys (existing users would keep working) but giving academic users and AI-orchestration workflows a real no-AEDT option for eigenmode + capacitance + EPR + S-parameter analyses.

Nothing decided. Just an idea we've been kicking around and wanted to think through with you before going further.

### Why we wanted to talk to you first

[`SQDMetal/PALACE/`](https://github.com/sqdlab/SQDMetal/tree/main/SQDMetal/PALACE) already covers all four of those services end-to-end, accepts Quantum Metal `QDesign` objects directly, and is more actively maintained than Quantum Metal is right now. The work is real and the math is already there — it would feel silly to reimplement it in parallel when the community win is to coordinate (in some form, or none at all if that's what fits best).

### One thing we noticed while reading around

Currently SQDMetal's `pyproject.toml` has three properties that make "Quantum Metal pip-depends on SQDMetal" structurally tricky:

1. SQDMetal lists `quantum-metal` in `install_requires` → circular dep.
2. `requires-python = ">=3.11,<3.12"` → Quantum Metal supports 3.10–3.12.
3. `mph` (COMSOL bindings) is a hard dep → would forcibly pull COMSOL onto every Quantum Metal user installing `[palace]`.

Not at all a criticism — these all make sense for your existing user base (SQDMetal-installs-Quantum-Metal is the natural direction, and the Python pin / COMSOL coupling presumably reflects what your users actually run). It's just context for whichever direction this conversation goes.

### A few coordination shapes we've been kicking around

Sketching these less as a proposal and more as "here's the spectrum we see — does any of these (or some fourth thing we haven't thought of) fit how you'd want this to work?"

1. **Promote SQDMetal as the canonical Palace path** from Quantum Metal docs (no code coupling). Lowest coordination cost; keeps SQDMetal fully independent. Trade-off: users running `pip install quantum-metal[palace]` wouldn't get Palace from us — they'd switch libraries mentally. Lightweight and friendly; might honestly be the right answer.

2. **Spin out a shared `quantum-metal-palace` package** that both projects consume. Independent versioning, distributed governance. Quantum Metal maintainers can help with extracting / packaging / publishing if you'd like — happy to do the grunt work.

3. **Upstream the SQDMetal/PALACE module to Quantum Metal** as `renderer_palace/`, with SQDLab folks as `CODEOWNERS`. The COMSOL bits stay in SQDMetal; the Palace path lives in Quantum Metal where the packaging is cleaner. Quantum Metal maintainers would happily drive most of the merge / migration work (history preservation, refactor to fit our `QRendererAnalysis` protocol, CI integration) so this wouldn't become a workload on you. Sidesteps the three packaging notes above because Quantum Metal's `pyproject.toml` is the one in control.

### A few things we're curious about

- Does any of those resonate (or actively not resonate) from your side?
- Are there constraints (funding, IP, lab affiliation, planned features we don't know about) that shape what's feasible or desirable?
- Are there pain points we could help solve as part of this — e.g. shared CI for the Palace path, joint Docker-image ownership for the "Palace + gmsh + Jupyter" runtime, unified geometry processing on top of Quantum Metal's `qgeometry`?
- Is "no formal coordination, we each keep doing our thing" actually the answer? Genuinely fine if so.

### What Quantum Metal could bring to whichever shape we land on

CI matrix (3.10/3.11/3.12 × ubuntu/macos/windows), docs site, PyPI distribution, JupyterLite tutorials, the QDC community network (Discord, QDW conference). Plus maintainer time on the merge / migration / refactoring work itself if shape 2 or 3 ends up interesting — we wouldn't want this to land as extra workload on you. For shapes 2 and 3, CODEOWNERS / governance would keep SQDLab in the driver's seat for the Palace module.

### No urgency at all

We'd rather take 6 weeks and land it well than rush — or take longer, or land it nowhere if that's the right outcome. Happy to:

- Continue async in this thread
- **Discuss at [QDW 2026](https://qdw-ucla.squarespace.com/) if and how this makes sense** — would be lovely to think this through in person if any of you are attending

Background reading (once it lands publicly): the fuller scoping analysis at [`_dev/palace_replaces_ansys.md`](https://github.com/qiskit-community/qiskit-metal/blob/main/_dev/palace_replaces_ansys.md) in Quantum Metal. To be clear, that doc is internal Metal-side thinking — it contains a "tentative working preference" so the conversation has something concrete to push back on, but nothing in it is decided. The architecture phasing only applies *if* we end up building, and the shape depends on what works for you.

Looking forward to hearing whatever shape (or non-shape!) feels right to you.

Cheers,
the Quantum Metal / QDC maintainers

---

## If they say...

| Response | Our move |
|---|---|
| "Option 1 — just promote SQDMetal from your docs" | Update Quantum Metal docs to point at SQDMetal as the recommended Palace path. No code coupling. Keep SQDMetal links prominent in our install / headless / migration docs. |
| "Option 2 — shared `quantum-metal-palace` package" | Joint kickoff. Quantum Metal maintainers help extract / package / publish so it doesn't fall on SQDLab. Agree on package name, owner repo, governance, release cadence. Both projects depend on it. |
| "Option 3 — upstream into Quantum Metal" | Open a coordinated PR. Quantum Metal maintainers drive the merge / migration / refactor work; SQDLab folks become `CODEOWNERS` for `renderer_palace/`. Migrate module with attribution and full git history. |
| "We need time / let us think" | Don't push. Start Phase 1 in our scoping doc against SQDMetal/PALACE as a reference (Apache 2.0 lets us read & learn) with explicit attribution. Re-engage when they're ready. |
| (No response in 2 weeks) | Re-ping once. Two more weeks of silence → proceed with option 1 ("promote from docs, attribute, link") and document we tried. Door stays open. |
| "We have concerns about [X]" | Listen first. Don't ship anything that touches their work until they're comfortable. |
| "Let's chat at QDW" | Great — bring the SCOPING doc + this draft, hash it out in person. |

---

## What this draft deliberately does NOT do

- Demand a response on any timeline.
- Pitch Quantum Metal as the "real" home for Palace integration.
- Critique their packaging choices — only describe the constraints
  factually and note they're presumably reasonable for their user base.
- Assume option 1 (upstream) is what they'll pick. All three are real
  offers.
- Mention v0.8.0 release deadlines (don't put their work on our calendar).
- Hide the AI-orchestration framing — we're honest about why we care.
