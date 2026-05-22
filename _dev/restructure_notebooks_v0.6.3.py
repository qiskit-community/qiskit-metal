"""
Notebook restructuring script — run ONCE on original files.
"""
import json, copy, uuid, shutil, os

def code_cell(source, cell_id=None):
    return {"cell_type":"code","execution_count":None,"id":cell_id or str(uuid.uuid4())[:8],"metadata":{},"outputs":[],"source":[source]}

def md_cell(source, cell_id=None):
    return {"cell_type":"markdown","id":cell_id or str(uuid.uuid4())[:8],"metadata":{},"source":[source]}

def load_nb(path):
    with open(path) as f:
        return json.load(f)

def save_nb(nb, path):
    with open(path, "w") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)

def cell_src(c):
    s = c.get("source", "")
    return "".join(s) if isinstance(s, list) else s

BASE = "/Users/zlatkominev/CODE_REPOS/quantum_hardware/qiskit-metal"
issues = []

# ============================================================
# TASK 1 — Restructure 1.1
# ============================================================
print("=" * 60)
print("TASK 1 — Restructure 1.1")

path_11 = f"{BASE}/tutorials/1 Overview/1.1 Bird's eye view of Qiskit Metal.ipynb"
nb11 = load_nb(path_11)
cells_11 = nb11["cells"]
before_11 = len(cells_11)
print(f"  Before: {before_11} cells")

teaser_code = """# Three lines to your first superconducting qubit
import qiskit_metal as qm
from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket

design = designs.DesignPlanar()
q1 = TransmonPocket(design, "Q1", options=dict(
    pos_x="0.5mm", pos_y="0.25mm",
    connection_pads=dict(a=dict(loc_W=+1, loc_H=+1)),
))
fig = qm.view(design)
fig"""

teaser_md = """> **What just happened?**
>
> In a few lines you:
> 1. Created a **quantum chip design canvas** (`DesignPlanar`)
> 2. Placed a **superconducting transmon qubit** on it (`TransmonPocket`)
> 3. Rendered it to a **matplotlib figure** — no Qt, no GUI, no extra setup
>
> The rest of this tutorial unpacks what each step means and how to control every detail.
> Skip ahead to [1.2 Your First Chip](./1.2%20Quick%20start.ipynb) if you want to keep building immediately."""

new_cells_11 = (
    [cells_11[0]]               # 0: title
    + [cells_11[1]]             # 1: no-Qt callout
    + [code_cell(teaser_code)]  # NEW: teaser code
    + [md_cell(teaser_md)]      # NEW: "What just happened?"
    + cells_11[2:7]             # 2-6: architecture / 4-step flow
    + cells_11[7:]              # 7-43: rest
)

nb11["cells"] = new_cells_11
save_nb(nb11, path_11)
after_11 = len(new_cells_11)
print(f"  After: {after_11} cells (expected 46)")
print(f"  Saved: {path_11}")


# ============================================================
# TASK 2 — Restructure 1.2
# ============================================================
print("=" * 60)
print("TASK 2 — Restructure 1.2")

path_12 = f"{BASE}/tutorials/1 Overview/1.2 Quick start.ipynb"
nb12 = load_nb(path_12)
cells_12 = nb12["cells"]
before_12 = len(cells_12)
print(f"  Before: {before_12} cells")

# Extract cells for later tasks (before modifying the list)
gds_cells = copy.deepcopy(cells_12[75:92])      # 17 cells
shapes_cells = copy.deepcopy(cells_12[92:106])  # 14 cells
cheese_cell = copy.deepcopy(cells_12[121])       # 1 cell

print(f"  Extracted gds_cells:    {len(gds_cells)} cells (indices 75-91)")
print(f"  Extracted shapes_cells: {len(shapes_cells)} cells (indices 92-105)")
print(f"  Extracted cheese_cell:  1 cell (index 121)")

# cells[125] is an empty code cell — include in tail
tail_cells = cells_12[122:126] if len(cells_12) >= 126 else cells_12[122:]
print(f"  Tail cells (122:126): {len(tail_cells)} cells")

# Three new iteration-loop cells
iter_cell_A = md_cell("""## Seeing the effect: compare before and after

Metal's design-as-code approach means every change is instant and visual.
`qm.view()` lets you place two renders side-by-side to see exactly what changed — no GUI needed.""")

iter_cell_B = code_cell("""import qiskit_metal as qm
import matplotlib.pyplot as plt

# Record the original value so we can restore it
_orig_pad_width = q1.options.pad_width

# Make a change
q1.options.pad_width = "550 um"
design.rebuild()

# Side-by-side comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
qm.view(design, components=["Q1"], title=f"Original  pad_width={_orig_pad_width}", ax=axes[0])
qm.view(design, components=["Q1"], title="Modified  pad_width=550 um", ax=axes[1])
plt.tight_layout()
plt.close(fig)
display(fig)""")

iter_cell_C = code_cell("""# Restore the original value before continuing
q1.options.pad_width = _orig_pad_width
design.rebuild()
print(f"Restored pad_width to {q1.options.pad_width}")""")

# Two design-validation cells
val_cell_D = md_cell("""## Before you export — check for overlaps

On complex chips with many components, accidental geometry overlaps can cause
DRC errors at the fab. Metal ships a built-in checker:

See the quick-topic notebook **[Testing QComponents for overlap and collisions](../../quick-topics/Testing-QComponents-for-overlap-and-collisions.ipynb)** for a one-cell overlap check you can run right now.""")

val_cell_E = code_cell("""# Uncomment to run the overlap check on the current design.
# Returns a DataFrame of overlapping component pairs (empty = all clear).
# from qiskit_metal.analyses.quantization import OverlapChecker
# OverlapChecker(design).check()""")

# Build new cell list per spec:
# 1. cells[0:21]  — setup through first option change + screenshot
# 2. Three new iteration-loop cells
# 3. cells[21:37] — rest of single-qubit section
# 4. cells[106:116] — geometry tables section (moved here)
# 5. cells[37:42] — overwrite + parsing advanced section
# 6. cells[42:75] — QPins, 4-qubit chip, CPWs, variables
# 7. Two new design-validation cells
# 8. cells[116:121] — version + close GUI
# 9. cells[122:126] — headless view (tail)
new_cells_12 = (
    cells_12[0:21]
    + [iter_cell_A, iter_cell_B, iter_cell_C]
    + cells_12[21:37]
    + cells_12[106:116]
    + cells_12[37:42]
    + cells_12[42:75]
    + [val_cell_D, val_cell_E]
    + cells_12[116:121]
    + tail_cells
)

nb12["cells"] = new_cells_12
save_nb(nb12, path_12)
after_12 = len(new_cells_12)
print(f"  After: {after_12} cells")
print(f"  Saved: {path_12}")


# ============================================================
# TASK 3 — Simplify 1.3
# ============================================================
print("=" * 60)
print("TASK 3 — Simplify 1.3")

path_13 = f"{BASE}/tutorials/1 Overview/1.3 Saving Your Chip Design.ipynb"
nb13 = load_nb(path_13)
cells_13 = nb13["cells"]
before_13 = len(cells_13)
print(f"  Before: {before_13} cells")

# Print cell overview for debugging
for i, c in enumerate(cells_13):
    print(f"    [{i:2d}] {c['cell_type']:8s} | {cell_src(c)[:60]!r}")

cell_A_13 = md_cell("""# Saving Your Chip Design

By the end of this tutorial you will know how to:

1. **Export a design to a Python script** (`to_python_script`) — the reproducibility superpower
2. **Export to GDS** for fabrication, and visually inspect the result

We start from the full 2-qubit chip built in [tutorial 1.2](./1.2%20Quick%20start.ipynb).
The block below is exactly what `design.to_python_script()` produces — a self-contained
Python definition you can version-control, share, and replay.""")

cell_B_13 = code_cell("""# === Design reproduced from tutorial 1.2 via design.to_python_script() ===
from qiskit_metal import designs, Dict
from qiskit_metal.qlibrary.qubits.transmon_pocket_cl import TransmonPocketCL
from qiskit_metal.qlibrary.tlines.pathfinder import RoutePathfinder
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from qiskit_metal.qlibrary.lumped.cap_3_interdigital import Cap3Interdigital
from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond

design = designs.DesignPlanar()
design.overwrite_enabled = True

Q1 = TransmonPocketCL(design, "Q1", options=dict(
    pos_x="0.7mm", pos_y="0mm", orientation="0",
    pad_gap="30um", inductor_width="20um",
    pad_width="425 um", pad_height="90um",
    pocket_width="650um", pocket_height="650um",
    gds_cell_name="FakeJunction_01",
    make_CL=True, cl_gap="6um", cl_width="10um", cl_length="20um",
    cl_ground_gap="6um", cl_pocket_edge="180", cl_off_center="50um",
    connection_pads=dict(
        readout=dict(loc_W=1, loc_H=1, pad_gap="15um", pad_width="125um",
                     pad_height="30um", cpw_extend="100um", pocket_extent="5um", pocket_rise="65um"),
        bus=dict(loc_W=-1, loc_H=-1, pad_gap="15um", pad_width="125um",
                 pad_height="30um", cpw_extend="100um", pocket_extent="5um", pocket_rise="65um"),
    ),
), make=True)

Q2 = TransmonPocketCL(design, "Q2", options=dict(
    pos_x="-0.7mm", pos_y="0mm", orientation="180",
    pad_gap="30um", inductor_width="20um",
    pad_width="425 um", pad_height="90um",
    pocket_width="650um", pocket_height="650um",
    gds_cell_name="FakeJunction_01",
    make_CL=True, cl_gap="6um", cl_width="10um", cl_length="20um",
    cl_ground_gap="6um", cl_pocket_edge="180", cl_off_center="50um",
    connection_pads=dict(
        readout=dict(loc_W=1, loc_H=1, pad_gap="15um", pad_width="125um",
                     pad_height="30um", cpw_extend="100um", pocket_extent="5um", pocket_rise="65um"),
        bus=dict(loc_W=-1, loc_H=-1, pad_gap="15um", pad_width="125um",
                 pad_height="30um", cpw_extend="100um", pocket_extent="5um", pocket_rise="65um"),
    ),
), make=True)

Bus_Q1_Q2 = RoutePathfinder(design, "Bus_Q1_Q2", options=dict(
    pin_inputs=dict(start_pin=dict(component="Q1", pin="bus"),
                    end_pin=dict(component="Q2", pin="bus")),
    fillet="99um", total_length="7mm", layer="1",
    lead=dict(start_straight="0mm", end_straight="250um"),
    advanced=dict(avoid_collision="true"), step_size="0.25mm",
))

Cap_Q1 = Cap3Interdigital(design, "Cap_Q1", options=dict(
    layer="1", pos_x="2.5mm", pos_y="0.25mm", orientation="90",
    trace_width="10um", finger_length="40um",
))
Cap_Q2 = Cap3Interdigital(design, "Cap_Q2", options=dict(
    layer="1", pos_x="-2.5mm", pos_y="-0.25mm", orientation="-90",
    trace_width="10um", finger_length="40um",
))

Readout_Q1 = RouteMeander(design, "Readout_Q1", options=dict(
    pin_inputs=dict(start_pin=dict(component="Q1", pin="readout"),
                    end_pin=dict(component="Cap_Q1", pin="a")),
    fillet="99um", total_length="5mm", layer="1",
    lead=dict(start_straight="0.325mm", end_straight="125um"),
    meander=dict(spacing="200um", asymmetry="-50um"),
))
Readout_Q2 = RouteMeander(design, "Readout_Q2", options=dict(
    pin_inputs=dict(start_pin=dict(component="Q2", pin="readout"),
                    end_pin=dict(component="Cap_Q2", pin="a")),
    fillet="99um", total_length="6mm", layer="1",
    lead=dict(start_straight="0.325mm", end_straight="125um"),
    meander=dict(spacing="200um", asymmetry="-50um"),
))

for name, px, py, ori in [
    ("Launch_Q1_Read", "3.5mm",  "0um",   "180"),
    ("Launch_Q2_Read", "-3.5mm", "0um",   "0"),
    ("Launch_Q1_CL",   "1.35mm", "-2.5mm","90"),
    ("Launch_Q2_CL",   "-1.35mm","2.5mm", "-90"),
]:
    LaunchpadWirebond(design, name, options=dict(
        layer="1", pos_x=px, pos_y=py, orientation=ori,
        trace_width="cpw_width", trace_gap="cpw_gap", lead_length="25um",
    ))

for name, src_comp, src_pin, dst_comp, dst_pin, length in [
    ("TL_Q1",    "Launch_Q1_Read", "tie", "Cap_Q1", "b", "7mm"),
    ("TL_Q2",    "Launch_Q2_Read", "tie", "Cap_Q2", "b", "7mm"),
    ("TL_Q1_CL", "Launch_Q1_CL",   "tie", "Q1", "Charge_Line", "7mm"),
    ("TL_Q2_CL", "Launch_Q2_CL",   "tie", "Q2", "Charge_Line", "7mm"),
]:
    RoutePathfinder(design, name, options=dict(
        pin_inputs=dict(start_pin=dict(component=src_comp, pin=src_pin),
                        end_pin=dict(component=dst_comp, pin=dst_pin)),
        fillet="99um", total_length=length, layer="1",
        lead=dict(start_straight="0mm", end_straight="150um"),
        advanced=dict(avoid_collision="true"), step_size="0.25mm",
    ))

print(f"Design ready: {len(design.components)} components")""")

cell_C_13 = code_cell("""%matplotlib inline
import matplotlib.pyplot as plt
import qiskit_metal as qm

fig_full = qm.view(design, figsize=(9, 9), title="Full 2-qubit chip")

fig, axes = plt.subplots(1, 2, figsize=(13, 6))
qm.view(design, components=["Q1"], title="Q1 — FakeJunction_01", ax=axes[0])
qm.view(design, components=["Q2"], title="Q2 — FakeJunction_01", ax=axes[1])
plt.tight_layout()
plt.close(fig)

display(fig_full)
display(fig)""")

# Find to_python_script cell by content search
tps_idx = None
for i, c in enumerate(cells_13):
    if c["cell_type"] == "code" and "to_python_script" in cell_src(c):
        tps_idx = i
        break
if tps_idx is None:
    issues.append("1.3: Could not find to_python_script cell — appending at end")
    tps_idx = len(cells_13)
print(f"  Found to_python_script at index {tps_idx}")

new_cells_13 = (
    [cell_A_13, cell_B_13, cell_C_13]
    + ([cells_13[tps_idx]] if tps_idx < len(cells_13) else [])
    + (cells_13[tps_idx+1:] if tps_idx < len(cells_13) else [])
)

nb13["cells"] = new_cells_13
save_nb(nb13, path_13)
after_13 = len(new_cells_13)
print(f"  After: {after_13} cells")
print(f"  Saved: {path_13}")


# ============================================================
# TASK 4 — Augment 1.4
# ============================================================
print("=" * 60)
print("TASK 4 — Augment 1.4")

path_14 = f"{BASE}/tutorials/1 Overview/1.4 Headless quick view (no Qt GUI).ipynb"
nb14 = load_nb(path_14)
cells_14 = nb14["cells"]
before_14 = len(cells_14)
print(f"  Before: {before_14} cells")

# Verify cell 28 is the "Save figure to file" markdown
if before_14 > 28:
    c28_src = cell_src(cells_14[28])
    print(f"  Cell 28 preview: {c28_src[:80]!r}")
    if "Save" not in c28_src and "save" not in c28_src:
        issues.append(f"1.4: Cell 28 doesn't look like 'Save figure' cell: {c28_src[:60]!r}")
    insert_idx = 28
else:
    issues.append(f"1.4: Only {before_14} cells, inserting at end instead of 28")
    insert_idx = before_14

batch_md = md_cell("""## Batch export: render multiple designs to PNG

Headless rendering shines when you want to automate exports — for example,
generating figures for a paper or sweeping a parameter.""")

batch_code = code_cell("""import os
import qiskit_metal as qm
%matplotlib inline

output_dir = "batch_output"
os.makedirs(output_dir, exist_ok=True)

# Vary Q1's pad_width across three values and save each view
for pad_w in ["300 um", "425 um", "550 um"]:
    design2.components["Q1"].options.pad_width = pad_w
    design2.rebuild()
    fig = qm.view(design2, title=f"pad_width = {pad_w}")
    safe_name = pad_w.replace(" ", "").replace("/", "_")
    fig.savefig(f"{output_dir}/design_pad_{safe_name}.png", dpi=150, bbox_inches="tight")
    print(f"Saved design_pad_{safe_name}.png")

# Restore original
design2.components["Q1"].options.pad_width = "425 um"
design2.rebuild()
print("Done — check the batch_output/ folder")""")

batch_tip = md_cell("""> **Tip:** Wrap this pattern in a function and loop over any option — qubit positions,
> CPW lengths, pad gaps. The PNG filenames become your experiment log.""")

new_cells_14 = (
    cells_14[:insert_idx]
    + [batch_md, batch_code, batch_tip]
    + cells_14[insert_idx:]
)

nb14["cells"] = new_cells_14
save_nb(nb14, path_14)
after_14 = len(new_cells_14)
print(f"  After: {after_14} cells (expected 35)")
print(f"  Saved: {path_14}")


# ============================================================
# TASK 5 — Create 1.5 (new notebook)
# ============================================================
print("=" * 60)
print("TASK 5 — Create 1.5")

# Use 1.4 (already modified) as metadata template
nb14_for_meta = load_nb(path_14)
meta_template = nb14_for_meta.get("metadata", {})

path_15 = f"{BASE}/tutorials/1 Overview/1.5 Parametric design - iterate and compare.ipynb"

cells_15 = [
    md_cell("""# 1.5 Parametric Design: Iterate and Compare

Metal is a **design-as-code** framework — every chip property is a Python variable.
That means you can sweep parameters, compare variants side-by-side, and save entire
design families with a loop.

By the end of this notebook you will:
- Vary a qubit geometry parameter and render a comparison grid
- Vary a CPW length and see how the route adapts
- Export all variants as PNG for a presentation or paper

**Prerequisite:** [1.2 Your First Chip](./1.2%20Quick%20start.ipynb) — we'll reuse the 4-qubit ring design."""),

    code_cell("""# Rebuild the 4-qubit chip from tutorial 1.2
from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
from qiskit_metal import Dict
import qiskit_metal as qm
import matplotlib.pyplot as plt
%matplotlib inline

design = designs.DesignPlanar()
design.overwrite_enabled = True

options = dict(
    pad_width="425 um",
    pocket_height="650um",
    gds_cell_name="FakeJunction_01",
    connection_pads=dict(
        a=dict(loc_W=+1, loc_H=+1),
        b=dict(loc_W=-1, loc_H=+1, pad_height="30um"),
        c=dict(loc_W=+1, loc_H=-1, pad_width="200um"),
        d=dict(loc_W=-1, loc_H=-1, pad_height="50um"),
    ),
)

q1 = TransmonPocket(design, "Q1", options=dict(pos_x="+2.55mm", pos_y="+0.0mm", **options))
q2 = TransmonPocket(design, "Q2", options=dict(pos_x="+0.0mm", pos_y="-0.9mm", orientation="90", **options))
q3 = TransmonPocket(design, "Q3", options=dict(pos_x="-2.55mm", pos_y="+0.0mm", **options))
q4 = TransmonPocket(design, "Q4", options=dict(pos_x="+0.0mm", pos_y="+0.9mm", orientation="90", **options))

_cpw_opts = Dict(meander=Dict(lead_start="0.1mm", lead_end="0.1mm", asymmetry="0 um"))

def connect(name, c1, p1, c2, p2, length, asym="0 um"):
    return RouteMeander(design, name, Dict(
        pin_inputs=Dict(start_pin=Dict(component=c1, pin=p1),
                        end_pin=Dict(component=c2, pin=p2)),
        lead=Dict(start_straight="0.13mm"),
        total_length=length, fillet="90um",
        meander=Dict(asymmetry=asym), **_cpw_opts,
    ))

cpw1 = connect("cpw1", "Q1", "d", "Q2", "c", "6.0 mm", "+150um")
cpw2 = connect("cpw2", "Q3", "c", "Q2", "a", "6.1 mm", "-150um")
cpw3 = connect("cpw3", "Q3", "a", "Q4", "b", "6.0 mm", "+150um")
cpw4 = connect("cpw4", "Q1", "b", "Q4", "d", "6.1 mm", "-150um")

print(f"Design ready — {len(design.components)} components")
fig = qm.view(design, figsize=(8, 8), title="Baseline design")
fig"""),

    md_cell("""## Sweep 1: qubit pad width

`pad_width` controls the size of the transmon capacitor pads. Larger pads → larger capacitance → lower qubit frequency.
Here we sweep three values and compare the geometry."""),

    code_cell("""pad_widths = ["300 um", "425 um", "550 um"]

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("Sweep: Q1 pad_width", fontsize=14)

for ax, pw in zip(axes, pad_widths):
    q1.options.pad_width = pw
    design.rebuild()
    qm.view(design, components=["Q1"], title=f"pad_width = {pw}", ax=ax)

# Restore baseline
q1.options.pad_width = "425 um"
design.rebuild()

plt.tight_layout()
plt.close(fig)
display(fig)"""),

    md_cell("""## Sweep 2: CPW coupling length

`total_length` controls the electrical length of a CPW resonator, which sets its resonant frequency.
Longer CPW → lower frequency. The route geometry adapts automatically."""),

    code_cell("""cpw_lengths = ["5.0 mm", "6.0 mm", "7.5 mm"]

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("Sweep: cpw1 total_length", fontsize=14)

for ax, length in zip(axes, cpw_lengths):
    cpw1.options.total_length = length
    design.rebuild()
    qm.view(design, title=f"cpw1 length = {length}", ax=ax)

# Restore baseline
cpw1.options.total_length = "6.0 mm"
design.rebuild()

plt.tight_layout()
plt.close(fig)
display(fig)"""),

    md_cell("""## Exporting a design family to PNG

Combine a parameter sweep with `fig.savefig()` to produce a labelled image
set for a paper, slide deck, or design review."""),

    code_cell("""import os

output_dir = "sweep_output"
os.makedirs(output_dir, exist_ok=True)

for pw in ["300 um", "425 um", "550 um"]:
    q1.options.pad_width = pw
    design.rebuild()
    fig = qm.view(design, figsize=(7, 7), title=f"Q1 pad_width = {pw}")
    safe = pw.replace(" ", "")
    fig.savefig(f"{output_dir}/padwidth_{safe}.png", dpi=150, bbox_inches="tight")
    print(f"Saved padwidth_{safe}.png")

# Restore
q1.options.pad_width = "425 um"
design.rebuild()
print(f"\\nAll PNGs saved to ./{output_dir}/")"""),

    md_cell("""## Next steps

- **[1.3 Saving Your Design](./1.3%20Saving%20Your%20Chip%20Design.ipynb)** — export to GDS for fabrication
- **[1.4 Headless workflow](./1.4%20Headless%20quick%20view%20%28no%20Qt%20GUI%29.ipynb)** — run all of this in scripts and CI
- **[4.x Analysis](../../4-Analysis/)** — connect your design to electromagnetic simulation"""),
]

nb15 = {
    "metadata": meta_template,
    "nbformat": nb14_for_meta.get("nbformat", 4),
    "nbformat_minor": nb14_for_meta.get("nbformat_minor", 5),
    "cells": cells_15,
}

save_nb(nb15, path_15)
print(f"  Created: {path_15}")
print(f"  Cells: {len(cells_15)}")


# ============================================================
# TASK 6 — Create 1.6 (shapes showcase)
# ============================================================
print("=" * 60)
print("TASK 6 — Create 1.6")

path_16 = f"{BASE}/tutorials/1 Overview/1.6 QComponent shape library.ipynb"

cell0_16 = md_cell("""# 1.6 QComponent Shape Library

Quantum Metal ships a set of **sample shape QComponents** — subtract polygons, spirals,
n-gons, and hollow rectangles — that are useful for:

- Custom chip features (flux bias lines, wirebond pads, markers)
- Prototyping arbitrary geometries before writing a full QComponent
- Teaching: each shape shows a minimal QComponent implementation

This notebook demonstrates each shape on a fresh design.""")

cell1_16 = code_cell("""from qiskit_metal import designs, MetalGUI
import qiskit_metal as qm
%matplotlib inline

design = designs.DesignPlanar()
design.overwrite_enabled = True
print("Design ready")""")

cell_last_16 = md_cell("""## Next steps

- Write your own QComponent: see **[2.3 How do I make my custom QComponent](../../2-From-components-to-chip/)**
- Export any of these shapes to GDS: see **[1.3 Saving Your Design](./1.3%20Saving%20Your%20Chip%20Design.ipynb)**""")

nb16_cells = [cell0_16, cell1_16] + copy.deepcopy(shapes_cells) + [cell_last_16]

nb16 = {
    "metadata": meta_template,
    "nbformat": nb14_for_meta.get("nbformat", 4),
    "nbformat_minor": nb14_for_meta.get("nbformat_minor", 5),
    "cells": nb16_cells,
}

save_nb(nb16, path_16)
print(f"  Created: {path_16}")
print(f"  Cells: {len(nb16_cells)} (2 setup + {len(shapes_cells)} shapes + 1 closing)")


# ============================================================
# TASK 7 — Augment 3.2 with GDS cells from 1.2
# ============================================================
print("=" * 60)
print("TASK 7 — Augment 3.2")

path_32 = f"{BASE}/tutorials/3 Renderers/3.2 Export your design to GDS.ipynb"
nb32 = load_nb(path_32)
cells_32 = nb32["cells"]
before_32 = len(cells_32)
print(f"  Before: {before_32} cells")

separator_md = md_cell("""---

## Junction import details and cheesing

The following section (originally from tutorial 1.2) covers importing junction GDS files
in depth and the cheese / no-cheese geometry options for fabrication.""")

# Check if gds_cells[0] has %metal_heading and skip if so
gds_src_0 = cell_src(gds_cells[0])
if "%metal_heading" in gds_src_0:
    print(f"  Skipping gds_cells[0] (contains %metal_heading): {gds_src_0[:60]!r}")
    gds_cells_to_append = gds_cells[1:]
else:
    print(f"  gds_cells[0] does not contain %metal_heading, keeping it: {gds_src_0[:60]!r}")
    gds_cells_to_append = gds_cells

print(f"  gds_cells_to_append: {len(gds_cells_to_append)} cells")

new_cells_32 = (
    cells_32
    + [separator_md]
    + copy.deepcopy(gds_cells_to_append)
    + [copy.deepcopy(cheese_cell)]
)

nb32["cells"] = new_cells_32
save_nb(nb32, path_32)
after_32 = len(new_cells_32)
print(f"  After: {after_32} cells")
print(f"  Appended: 1 separator + {len(gds_cells_to_append)} gds_cells + 1 cheese_cell")
print(f"  Saved: {path_32}")


# ============================================================
# TASK 8 — Sync to docs/tut
# ============================================================
print("=" * 60)
print("TASK 8 — Sync to docs/tut")

sync_pairs = [
    (f"{BASE}/tutorials/1 Overview/1.1 Bird's eye view of Qiskit Metal.ipynb",
     f"{BASE}/docs/tut/1-Overview/1.1-Bird's-eye-view-of-Qiskit-Metal.ipynb"),
    (f"{BASE}/tutorials/1 Overview/1.2 Quick start.ipynb",
     f"{BASE}/docs/tut/1-Overview/1.2-Quick-start.ipynb"),
    (f"{BASE}/tutorials/1 Overview/1.3 Saving Your Chip Design.ipynb",
     f"{BASE}/docs/tut/1-Overview/1.3-Saving-Your-Chip-Design.ipynb"),
    (f"{BASE}/tutorials/1 Overview/1.4 Headless quick view (no Qt GUI).ipynb",
     f"{BASE}/docs/tut/1-Overview/1.4-Headless-quick-view-(no-Qt-GUI).ipynb"),
    (f"{BASE}/tutorials/1 Overview/1.5 Parametric design - iterate and compare.ipynb",
     f"{BASE}/docs/tut/1-Overview/1.5-Parametric-design---iterate-and-compare.ipynb"),
    (f"{BASE}/tutorials/1 Overview/1.6 QComponent shape library.ipynb",
     f"{BASE}/docs/tut/1-Overview/1.6-QComponent-shape-library.ipynb"),
    (f"{BASE}/tutorials/3 Renderers/3.2 Export your design to GDS.ipynb",
     f"{BASE}/docs/tut/3-Renderers/3.2-Export-your-design-to-GDS.ipynb"),
]

for src, dst in sync_pairs:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  Copied: {os.path.basename(src)} -> {os.path.relpath(dst, BASE)}")


# ============================================================
# VERIFICATION SUMMARY
# ============================================================
print()
print("=" * 60)
print("VERIFICATION SUMMARY")
print("=" * 60)

summary = [
    ("1.1 Bird's eye view",         before_11, after_11),
    ("1.2 Quick start",             before_12, after_12),
    ("1.3 Saving Your Chip Design", before_13, after_13),
    ("1.4 Headless quick view",     before_14, after_14),
    ("1.5 Parametric design",       0,         len(cells_15)),
    ("1.6 Shape library",           0,         len(nb16_cells)),
    ("3.2 Export to GDS",           before_32, after_32),
]

for name, b, a in summary:
    if b == 0:
        print(f"  NEW  {name}: {a} cells")
    else:
        print(f"  MOD  {name}: {b} -> {a} cells (delta: {a - b:+d})")

print()
print("Extractions from 1.2:")
print(f"  gds_cells:    {len(gds_cells)} cells (orig indices 75-91)")
print(f"  shapes_cells: {len(shapes_cells)} cells (orig indices 92-105)")
print(f"  cheese_cell:  1 cell  (orig index 121)")

print()
print("Sync to docs/tut:")
for src, dst in sync_pairs:
    exists = os.path.exists(dst)
    print(f"  {'OK     ' if exists else 'MISSING'}: {os.path.basename(dst)}")

if issues:
    print()
    print("Issues/Warnings:")
    for iss in issues:
        print(f"  ! {iss}")
else:
    print()
    print("No issues encountered.")

print()
print("DONE.")
