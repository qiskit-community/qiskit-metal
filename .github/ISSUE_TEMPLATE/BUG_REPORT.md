---
name: "\U0001F41B Bug report"
about: "Something broken or behaving unexpectedly."
title: ''
labels: bug
assignees: ''

---

<!--
⚠️ Before filing, please:
   1. Search open and closed issues for duplicates:
      https://github.com/qiskit-community/qiskit-metal/issues?q=
   2. Try with the latest release: `pip install -U quantum-metal`
   3. Skim the FAQ:
      https://qiskit-community.github.io/qiskit-metal/faq.html
-->

## Environment

- **Quantum Metal version**: <!-- e.g. 0.7.1 — `python -c "import qiskit_metal; print(qiskit_metal.__version__)"` -->
- **Python version**: <!-- e.g. 3.11.7 -->
- **Operating system**: <!-- e.g. macOS 14 (arm64), Ubuntu 24.04, Windows 11 -->
- **Install command**: <!-- e.g. `pip install quantum-metal` / `pip install "quantum-metal[full]"` / source install -->
- **Backend(s) involved** (check all that apply):
  - [ ] Core API / `qm.view(design)` (lite install)
  - [ ] `MetalGUI` desktop GUI
  - [ ] HFSS / Q3D via pyaedt
  - [ ] gmsh / Elmer FEM
  - [ ] GDS export
  - [ ] Other / unsure

## What's happening (current behavior)

<!-- Brief description of the bug. -->

## What you expected

<!-- What did you expect to happen instead? -->

## Steps to reproduce

<!--
Paste a MINIMAL self-contained script that reproduces the issue. The
smaller the script, the faster we can help. Use the lite install path
if you can (no Qt / Ansys / gmsh required).
-->

```python
# Minimal reproducer:
import qiskit_metal as qm
# ...
```

## Full traceback / error output

<!-- If you got an error, paste the FULL traceback below. -->

```
<paste traceback here>
```

## Suggested fix / additional context

<!-- Optional. Root-cause guesses, suspected modules, or a PR in mind. -->
