---
name: chip-layout-from-images
description: Reproduce a published superconducting chip layout in Quantum Metal from its images (paper figures, talk slides, micrographs) -- for study, teaching, or as a test of an agent or a tool against a device whose answer is known. Measuring geometry from pixels, and checking the build against the image and the published data. Use when asked to "reproduce", "rebuild", "trace" or "match" a published device. For designing a new chip, use the chip-design skill.
---

# Reproducing a published chip layout from images

**What this is for.** A published device is a benchmark with a known
answer: reproducing it tests an agent, a component or a rule, and teaches
how a real chip is put together. It is not a way to take someone's design.
Reproduce only what the authors have published, credit them prominently
(paper, and the talks or slides the geometry came from), say it is a
reconstruction and not their mask, and ask a maintainer before
publishing one. New chips are designed from a specification:
`.claude/skills/chip-design/SKILL.md`, whose build and verification rules
apply here too.

Worked example: the ETH Zurich 17-qubit surface-code device (Krinner et al.,
Nature 605, 669 (2022)), rebuilt from the group's public slides. Every rule
below is here because the opposite went wrong on that build.

## 1. Workflow — one layer at a time

1. **Pick the best source.** A talk's slide deck usually beats the paper
   figure: higher resolution, uncropped, and often *layer-separated* (the
   deck steps through the chip one layer per slide). Keep a **bare**
   (un-false-colored) micrograph in the same frame for anything near a
   feature — overlay strokes are drawn wider than the metal and over it.
2. **Calibrate on the most-repeated feature**, not the scale bar: e.g. the
   launchpad ring (dozens of samples at a known pitch). It also proves the
   image is isotropic. If two images disagree, compare a *scale-free* ratio
   (feature pitch in units of pad pitch) before merging measurements — two
   near-identical chips can differ by 15%.
3. **Build in stages, never batched:** die + launchpads, qubits, couplers,
   control lines, readout, filters, feedlines, lumped couplers. After every
   stage run, in this order: DRC, a conformance check against the image,
   a render overlaid on the image at true scale.
4. **Get an independent, fresh-context audit per stage** (a subagent told to
   find defects, not to confirm). On the worked example two audit rounds
   found five defect classes that every self-check had passed.
5. **Get the physics from the papers before drawing a termination.** A
   research subagent reading the device paper and the scheme it cites
   (here Heinsoo et al. 2018) settled which end of each lambda/4 line is
   open and which shorted -- the build had one of them backwards.
6. **Validate against physics and published numbers**, not just pixels:
   e.g. traced resonator length vs measured readout frequency (r = 0.94
   across 17 qubits once the geometry was right); readout groups vs the
   stated per-feedline frequency spacing. A fix that is right usually makes
   this agreement *better* on data it never looked at.

## 2. Measuring from pixels

- **Color classes from the image's own hue histogram**, never the legend
  swatches: alpha blending over a grey micrograph shifts hues (a legend
  green came out teal and merged with cyan).
- **Loosen the gate per layer, never globally.** The palest, thinnest
  stroke (~4 px) erodes under the default gate and shatters (219 fragments
  for 17 filters; the right gate gave exactly 17).
- **Use the slide where a layer is unoccluded** (the one that introduced
  it); later layers are drawn over it.
- **Skeletonize (Zhang-Suen), don't band-average.** A geodesic band-centroid
  centerline averages across the arms of a hairpin/meander and zigzags
  across the folds while still getting the total length right.
- **Two known ends -> shortest skeleton path. One known end -> longest.**
  Shortest-between-ends ignores side stubs with no heuristics. Longest is
  exact only on a tree:
  - **fill enclosed holes first** — a pad drawn as an outline is a closed
    ring with no free end; the longest path then skips the whole far part;
  - but **don't let hole-filling merge two nets** — a coupler frame around a
    finger of *another* line gets filled into one blob; cut the path where it
    enters the thick region (distance transform separates line and pad
    cleanly).
- **Bridge crossing nicks exactly.** Where a later layer crosses, the stroke
  has a small gap (15-60 um). Find the route whose *largest* gap is smallest
  (minimax over the component graph) and paint only those gaps; refuse any
  gap above a threshold. Blunt morphological closing merges neighbors.
- **Extend ends along the stroke's principal axis**, not the last segment —
  thinning loses ragged tips (50-150 um), and a slightly tilted last segment
  marches out of the stroke's side.
- **Smooth, then resample uniformly** (arclength). Never let a downstream
  `min_segment` delete vertices from a meander: the replacement chord cuts
  the bend.

## 3. Building from measured data

The general build rules -- explicit terminations, wired airbridges,
`connect_pins` and taps, fillet limits, waivers -- are in the chip-design
skill (section 5). Specific to a traced build:

- **Measure each element's own layout from a close-up before placing it.**
  A qubit's pad angles and junction site are not the lattice's. Forcing the
  17-qubit chip's pads onto the compass points gave sideways line exits, a
  junction on a pad and floating slivers; the device close-up showed five
  pads about 72 degrees apart, and the fix removed every workaround.
- **Clean tracing noise before building, in this order:** simplify the
  traced lines (Douglas-Peucker, below a pixel) once, up front; then any
  local straightening (e.g. two coupled lines made parallel at their
  coupler); then resample. Simplifying after straightening undoes it.
- **Off a pad, the line runs along the pad's axis.** Snap the traced stretch
  that still runs along the pin normal onto it (by direction, capped at a few
  pixels), and drop the points that dip to the far side before the turn --
  otherwise a pixel of tracing offset shows as a kink right after the lead.
  Not at airbridge ends: there the trace runs straight through.
- **Measure distances from where a component is drawn**, not from its
  traced center: traced centers scattered ~50 um about the lattice here.

- **Build the whole chip from one script that reads measured data files**
  (JSON, with provenance) and hard-codes nothing; run a conformance check
  after every build.
- **When the image cannot separate a dimension, use the design standard as
  the tiebreaker, and say so.** CPW center + gap measured 14 +- 1.5 um with
  w and g unresolved; 50 ohm on silicon then fixes w ~ 8.5, g ~ 5.5 um.
- **Known path -> `PolylineCPW`, not a router.** Octilinear device lines made
  `RouteAnchors` fail or staircase.
- **Segment floor vs chord floor.** Uniform arclength spacing still gives
  short *chords* round tight bends (38 um at a 45 um step). Set
  `min_segment` below the chord floor, and `fillet` <= half of it.
- **Join lines to pins by following the trace**: drop traced points not yet
  ahead of the pin along its normal, then start at the pin. A fixed straight
  lead plus "drop points near the lead end" deleted real 45-deg jogs.
- **Get the physics of each termination from the papers** (here Heinsoo et
  al. 2018 settled which end of each lambda/4 line is open) -- the image
  does not show it.
- **Lumped capacitors: match the real cell, reuse before creating.**
  Measure topology and dimensions on the bare micrograph first.
  `CapNInterdigital(finger_count=2, finger_length=0)` is two pads across a
  gap; a finger-in-frame cell had no equivalent, so `CapFingerInFrame` was
  added -- one cross-section, tuned per instance by length.

## 4. Verify against the source

Run the chip-design skill's checks (section 6) -- shape rules, drawn
geometry, rebuild stability -- and add:

- A **conformance gate** per line: worst distance from the drawn centerline
  to the traced stroke, skipping only regions where the model is known to
  differ (e.g. 0.35 mm around qubits) and counting bridged crossings as on
  the stroke.
- **Audits check the input data too.** An independent audit of the
  capacitors found one cell 15 um off -- the measured coordinate was wrong,
  not the builder. Keep measurements in data files with their provenance so
  a correction is one line.
- **A pixel-level gate checks "on the stroke", not "centered".** A
  consistent ~1 px bias (diagonal traces pulled ~8 um toward each other)
  passed it; only an independent measurement on the bare image showed it.
- **Published numbers are the strongest check** (section 1, step 6).

## 5. Where the rest lives

- Worked example: `docs/circuit-examples/F.Small-quantum-chips/53-Wallraff_17Qubit_SurfaceCode.ipynb`
  with its builder and measured data in `resources/wallraff_17q/` beside it.
- `.claude/skills/chip-design/SKILL.md` — designing new chips; the general
  build and verification rules.
- `.claude/context/lessons-learned.md` — "Component-authoring traps":
  `add_pin` input forms, rotation vs pin angle, `connect_simple` limits,
  connection-aware DRC.
- `qiskit_metal.validation` — `validate(design, rules=..., waivers=[...])`,
  `Waiver`, `SHAPE_RULES` (self-intersection, sharp-turn, fillet-starved,
  dangling-end).
- `qiskit_metal.qlibrary.tlines.polyline_cpw.PolylineCPW` — known-path CPW,
  with `taps`.
- `qiskit_metal.qlibrary.lumped.cap_finger_in_frame.CapFingerInFrame` —
  single-finger gap capacitor (frame around a finger).
- `qiskit_metal.qlibrary.tlines.airbridge.Airbridge` — ground strap, or a
  signal crossover via pins `a`/`b`.
- `.claude/context/decision-log.md` (2026-09-26) — why the shape rules are
  opt-in for now.
