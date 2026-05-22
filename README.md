# Quantum Metal (formerly: Qiskit Metal)

[![License](https://img.shields.io/github/license/qiskit-community/qiskit-metal.svg?style=popout-square)](https://opensource.org/licenses/Apache-2.0)
[![Release](https://img.shields.io/github/release/qiskit-community/qiskit-metal.svg?style=popout-square)](https://github.com/qiskit-community/qiskit-metal/releases)
[![PyPI](https://img.shields.io/pypi/v/quantum-metal.svg?style=popout-square)](https://pypi.org/project/quantum-metal/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4618153.svg)](https://doi.org/10.5281/zenodo.4618153)
[![Discord](https://img.shields.io/badge/Discord-Join_Community-5865F2?logo=discord&logoColor=white&style=popout-square)](https://discord.gg/kaZ3UFuq)

> ![Welcome to Quantum Metal!](https://raw.githubusercontent.com/qiskit-community/qiskit-metal/main/docs/images/zkm_banner.png 'Welcome to Quantum Metal')
>
> **Quantum Metal** is an open-source framework for engineers and scientists to design superconducting quantum devices with ease.

📍 **Where we're heading:** see [ROADMAP.md](./ROADMAP.md) for the
lite-by-default install (v0.7.0, shipped), the AI-orchestration profile,
the open FEM stack (gmsh + Elmer + AWS Palace), and the upcoming
import-path rename.

---

## Install

```bash
pip install quantum-metal             # lite (v0.7.0+ default)
pip install "quantum-metal[full]"     # everything (v0.6.x compatibility)
```

Pick the install command that matches your workflow:

| | What you get | When |
|---|---|---|
| **🪶 Lite** `pip install quantum-metal` | Core API, `qm.view(design)` headless viewer, GDS export, pure-Python analyses | AI orchestration, Colab / Binder, cloud Jupyter, CI, any non-interactive workflow |
| **🖥️ GUI** `pip install "quantum-metal[gui]"` | + `MetalGUI` desktop app (PySide6, qdarkstyle) | Interactive design work |
| **🧲 Ansys** `pip install "quantum-metal[ansys]"` | + HFSS / Q3D renderers, EPR analyses (pyaedt, pyEPR-quantum) | HFSS / Q3D simulation (Windows + Ansys AEDT license) |
| **🔺 Open FEM** `pip install "quantum-metal[fem]"` | + gmsh meshing, Elmer FEM | Open-source FEM (no Ansys license needed) |
| **📦 Full** `pip install "quantum-metal[full]"` | All of the above | Migrating from v0.6.x, want zero behavior change |

Extras compose: `pip install "quantum-metal[gui,ansys]"` works.

<details>
<summary>Feature matrix — what each install gives you</summary>

| | lite | `[gui]` | `[ansys]` | `[fem]` | `[full]` |
|---|---|---|---|---|---|
| `import qiskit_metal` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `qm.view(design)` (headless matplotlib) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Build designs + components from `qlibrary` | ✅ | ✅ | ✅ | ✅ | ✅ |
| GDS export | ✅ | ✅ | ✅ | ✅ | ✅ |
| `LOManalysis`, LOM math, capacitance reductions | ✅ | ✅ | ✅ | ✅ | ✅ |
| `MetalGUI` desktop app | — | ✅ | — | — | ✅ |
| HFSS / Q3D renderers | — | — | ✅ | — | ✅ |
| EPR analyses (`EigenmodeSim`, `LumpedElementsSim`) | — | — | ✅ | — | ✅ |
| gmsh / Elmer mesher | — | — | — | ✅ | ✅ |

</details>

Source install, conda, troubleshooting, and per-persona migration recipes:
[`docs/installation.rst`](./docs/installation.rst) ·
[`docs/migration-to-v0.7.0.rst`](./docs/migration-to-v0.7.0.rst).

CI runs on **Python 3.10 / 3.11 / 3.12** across Linux, macOS, and Windows.

---

## Quick Start

Create your first quantum design in a notebook or script — **no Qt required**:

```python
import qiskit_metal as qm
from qiskit_metal import designs
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket

# Start a planar-chip quantum device design
design = designs.DesignPlanar()
design.chips.main.size.size_x = '11mm'
design.chips.main.size.size_y = '9mm'

# Add a transmon qubit with a connector pad "a"
q1 = TransmonPocket(design, 'Q1', options=dict(
    pos_x='0.5 mm', pos_y='0.25 mm',
    pad_height='90um', pad_width='455um', pad_gap='30um',
    connection_pads=dict(a=dict()),
))

# Render to an inline matplotlib figure — works in Colab, CI, any notebook
fig = qm.view(design)
fig.savefig("my_first_chip.png")
```

![Example image](https://raw.githubusercontent.com/qiskit-community/qiskit-metal/main/docs/images/1_1_Birds_eye_view_of_Qiskit_Metal_example_image.jpg)

<details>
<summary>Prefer the interactive desktop GUI?</summary>

Install with `pip install "quantum-metal[gui]"`, then replace the `qm.view(...)`
line with the GUI flow:

```python
from qiskit_metal import MetalGUI

gui = MetalGUI(design)        # launch the interactive editor
gui.rebuild()                 # re-render after edits
gui.edit_component('Q1')      # select for editing
gui.autoscale()
# ... later
gui.main_window.close()
```

See [`docs/headless-usage.rst`](./docs/headless-usage.rst) for the full
no-Qt workflow and what to use when.

</details>

**Next:** browse the [tutorial notebooks](./tutorials/) (40+ Jupyter notebooks
covering the full API) or the
[online documentation](https://qiskit-community.github.io/qiskit-metal/).

---

## Transition notices

<details>
<summary><b>Qiskit Metal → Quantum Metal</b> rebrand (in progress)</summary>

- ✅ **New project name**: Quantum Metal
- ✅ **PyPI package**: `quantum-metal` (current; the old `qiskit-metal` package
  stays archived at its pre-v0.5 state)
- ✅ **Lite-by-default install** (v0.7.0)
- 🔜 **Repository rename to `quantum-metal`** — will keep redirects so existing
  clones and links continue to work
- 🔜 **Python import path rename** (`qiskit_metal` → `quantum_metal`) — target
  v0.8 or v1.0. Plan to update your imports ahead of that release. A
  `FutureWarning` fires on `import qiskit_metal` advertising this. Suppress with
  `QISKIT_METAL_SUPPRESS_RENAME_WARNING=1`.

</details>

---

## 🌐 Ecosystem

Quantum Metal is one of the core tools in a growing community ecosystem for
superconducting quantum device design and education:

- **[Quantum Device Workshop (QDW)](https://qdw-ucla.squarespace.com/)** — annual
  workshop at UCLA/USC with invited leaders in the field. Recent speakers:
  *Michel Devoret, Andreas Wallraff, Zlatko Minev, Eli Levenson-Falk.*
  [Video recordings](https://www.youtube.com/@uclaqcsa) ·
  [Sign for 2026](https://qdw-ucla.squarespace.com/qdw2026).
- **[Quantum Device Consortium (QDC)](https://qdc-qcsa.vercel.app)** — the
  community organization stewarding Quantum Metal alongside companion tools
  (SQUADDS, SQDMetal, scqubits, pyEPR, and others).
  [Join the QDC Discord](https://discord.gg/kaZ3UFuq).

---

## 🌱 From IBM to a Community-Maintained Project

Originally developed at IBM, **conceived and led by [Dr. Zlatko K. Minev](https://www.zlatko-minev.com)**,
Quantum Metal has transitioned into a **community-driven project** supported by
universities, research groups, labs, and individual contributors worldwide.

Development continues through the **Quantum Device Consortium (QDC)**, the
broader community, and active maintainers — in close collaboration with Zlatko
Minev and contributors across QDW/QDC shaping this next chapter.

Acknowledgements for the v0.5+ community release effort and ongoing
contributors are tracked in the [changelog](./changelog.md) and the
[contributors graph](https://github.com/qiskit-community/qiskit-metal/graphs/contributors).

---

## Community and Support

- 💬 **[Discord](https://discord.gg/kaZ3UFuq)** — fastest way to reach maintainers
  and the broader community. *Primary community channel.*
- 📺 **[YouTube video tutorials](https://youtube.com/playlist?list=PLOFEBzvs-VvqHl5ZqVmhB_FcSqmLufsjb)**
- 💻 **[GitHub Issues](https://github.com/qiskit-community/qiskit-metal/issues)** — bugs and feature requests
- 🟪 **[Qiskit Slack `#metal`](https://qiskit.slack.com/archives/C01R8KP5WP7)** — legacy channel, being phased out in favor of Discord

---

## Contributing

If you'd like to contribute, please read the
[contribution guidelines](https://github.com/qiskit-community/qiskit-metal/blob/main/CONTRIBUTING.md)
and the [contributor guide in the docs](https://qiskit-community.github.io/qiskit-metal/contributor-guide.html).
This project adheres to the [code of conduct](https://github.com/qiskit-community/qiskit-metal/blob/main/CODE_OF_CONDUCT.md).
We use [GitHub issues](https://github.com/qiskit-community/qiskit-metal/issues)
for bugs and feature requests.

---

## Architecture

For a high-level walkthrough of the codebase — Core, Renderers, Analyses, GUI,
Utilities — and how they interact, see
[`README_Architecture.md`](./README_Architecture.md).

Module-level deep dive:
[`docs/overview.rst`](./docs/overview.rst) ·
[`docs/workflow.rst`](./docs/workflow.rst).

---

## Authors and Citation

Quantum Metal is the work of [many people](https://github.com/qiskit-community/qiskit-metal/pulse/monthly)
who contribute to the project at different levels. The project was **conceived
and developed by [Zlatko Minev](https://www.zlatko-minev.com)** at IBM, then
co-led with Thomas McConkey, and has since transitioned to community maintenance
through the QDC.

If you use Quantum Metal in your research, please cite it — see the
[BibTeX entry](https://github.com/qiskit-community/qiskit-metal/blob/main/Qiskit_Metal.bib).

## Changelog and Release Notes

Release notes for each version are published on the
[GitHub releases page](https://github.com/qiskit-community/qiskit-metal/releases).
Developer notes for in-flight releases live in [`changelog.md`](./changelog.md).

## License

[Apache License 2.0](https://github.com/qiskit-community/qiskit-metal/blob/main/LICENSE.txt)
