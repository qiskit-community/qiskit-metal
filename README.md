# Quantum Metal (formerly: Qiskit Metal)

[![PyPI](https://img.shields.io/pypi/v/quantum-metal.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/quantum-metal/)
[![Python versions](https://img.shields.io/pypi/pyversions/quantum-metal.svg?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/quantum-metal/)
[![PyPI downloads](https://img.shields.io/pypi/dm/quantum-metal.svg?style=flat-square&label=PyPI%20downloads)](https://pypi.org/project/quantum-metal/)
[![License](https://img.shields.io/github/license/qiskit-community/qiskit-metal.svg?style=flat-square)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://img.shields.io/github/actions/workflow/status/qiskit-community/qiskit-metal/main.yml?branch=main&style=flat-square&label=CI&logo=github)](https://github.com/qiskit-community/qiskit-metal/actions)
[![Docs](https://img.shields.io/badge/docs-online-blue.svg?style=flat-square&logo=read-the-docs&logoColor=white)](https://qiskit-community.github.io/qiskit-metal/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4618153.svg)](https://doi.org/10.5281/zenodo.4618153)
[![GitHub stars](https://img.shields.io/github/stars/qiskit-community/qiskit-metal.svg?style=flat-square&logo=github)](https://github.com/qiskit-community/qiskit-metal/stargazers)
[![Contributors](https://img.shields.io/github/contributors/qiskit-community/qiskit-metal.svg?style=flat-square&logo=github)](https://github.com/qiskit-community/qiskit-metal/graphs/contributors)
[![Discord](https://img.shields.io/badge/Discord-Join_Community-5865F2?logo=discord&logoColor=white&style=flat-square)](https://discord.gg/kaZ3UFuq)

> ![Welcome to Quantum Metal!](https://raw.githubusercontent.com/qiskit-community/qiskit-metal/main/docs/images/zkm_banner.png 'Welcome to Quantum Metal')
>
> **Quantum Metal** is an open-source framework for engineers and scientists to design superconducting quantum devices with ease.

<p align="center">
  <img src="https://raw.githubusercontent.com/qiskit-community/qiskit-metal/main/docs/_static/hero.gif" alt="Build a 4-qubit chip in ~15 lines of Python — qubits, CPW routing, launchpads, qm.view()" width="640"/>
</p>

<p align="center"><sub><a href="./scripts/make_hero_gif.py">Regenerate this GIF</a> · <a href="./tutorials/2 From components to chip/C. My first full quantum chip design/2.21 Design a 4 qubit full chip.ipynb">Full tutorial: 2.21</a></sub></p>

### 🚀 Try it now — zero install

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/qiskit-community/qiskit-metal/blob/main/tutorials/1%20Overview/1.2%20Quick%20start.ipynb)
[![Open in GitHub Codespaces](https://img.shields.io/badge/Open_in-Codespaces-181717?logo=github&logoColor=white&style=flat-square)](https://codespaces.new/qiskit-community/qiskit-metal)

One click → working Quantum Metal in your browser in 60 seconds (lite install, no Qt required).

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
| **🔺 Open FEM mesher** `pip install "quantum-metal[mesh]"` | + gmsh meshing (foundation for Elmer / Palace) | Open-source FEM (no Ansys license). `[fem]` is a backward-compat alias. |
| **📦 Full** `pip install "quantum-metal[full]"` | All of the above | Migrating from v0.6.x, want zero behavior change |

Extras compose: `pip install "quantum-metal[gui,ansys]"` works.

<details>
<summary>Feature matrix — what each install gives you</summary>

| | lite | `[gui]` | `[ansys]` | `[mesh]` | `[full]` |
|---|---|---|---|---|---|
| `import qiskit_metal` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `qm.view(design)` (headless matplotlib) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Build designs + components from `qlibrary` | ✅ | ✅ | ✅ | ✅ | ✅ |
| GDS export | ✅ | ✅ | ✅ | ✅ | ✅ |
| `LOManalysis`, LOM math, capacitance reductions | ✅ | ✅ | ✅ | ✅ | ✅ |
| `MetalGUI` desktop app | — | ✅ | — | — | ✅ |
| HFSS / Q3D renderers | — | — | ✅ | — | ✅ |
| EPR analyses (`EigenmodeSim`, `LumpedElementsSim`) | — | — | ✅ | — | ✅ |
| gmsh mesher (for Elmer / Palace) | — | — | — | ✅ | ✅ |

`[fem]` is a backward-compatible alias of `[mesh]` — both install gmsh.

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
