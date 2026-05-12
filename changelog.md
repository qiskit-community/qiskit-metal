# Changelog Note Scratchpad for Developers

This log is used by developers to jot notes.

For the offical user-facing changelog for a particular release can be found in the correspondent Github release page. For example, you can find the changelog for the `0.0.4` release [here](https://github.com/Qiskit/qiskit-metal/releases/tag/0.0.4)

The changelog for all releases can be found in the release page: [![Releases](https://img.shields.io/github/release/Qiskit/qiskit-metal.svg?style=popout-square)](https://github.com/Qiskit/qiskit-metal/releases)

## Quantum Metal v0.5.3.post1 (Jan 23, 2026)

### PyAEDT Version Constraint

**What changed:** Pinned pyaedt dependency to `>=0.21,<0.24` (previously `~=0.21`)

**When:** January 23, 2026

**Why:** During testing of pyaedt v0.24.0 (released January 2026), compatibility issues were discovered with Quantum Metal's Ansys renderer integration. The team found that version 0.24.0 introduced regressions that affected the stability and reliability of simulations.

**Specific issues identified:**
- Compatibility problems with the existing Ansys HFSS, Q3D, and Eigenmode renderer implementations
- Potential breaking changes in pyaedt's API that would require significant refactoring
- The pyaedt v0.24.0 release includes major internal restructuring and new features that need thorough testing before adoption

**Resolution plan:** The constraint will be evaluated and potentially relaxed once:
1. The pyaedt v0.24.x series stabilizes with bug fixes
2. Quantum Metal's renderer code is updated to accommodate any API changes
3. Comprehensive testing is performed across all renderer types

**Note for users:** If you need features from pyaedt v0.24+, please open an issue describing your use case. For now, pyaedt versions 0.21.x through 0.23.x are fully supported and recommended.

### Other Changes
- Updated gmsh dependency 4.11.1 → 4.15.0

## Quantum Metal v0.5.3 (Jan 17, 2026)

- Various dependency updates. 
- Removed descartes and cython dependencies (unused).
- pandas, geopandas, scqubits and qutip updates to latest major version. Should fix [#1027](Ihttps://github.com/qiskit-community/qiskit-metal/issues/1027).
- Updates to contributor guide to fix inconsistent headline levels. Also convert example images to rst source code blocks. 
- Update various parts in the docs to indicate near-term versioning updates. 
- Update uv version to 0.9.24 in CI. Remove step to upgrade runner packages in CI for workflows speedup. 
- Convert package from [flat layout to src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/#src-layout-vs-flat-layout). This is a forward looking change that will help decouple source code from docs and tests. In this configurations, the any package code must be imported using the package name, instead of relative imports as before. This also requires installing the package in the virtual environment (either as editable or via the wheel) to import it, which we already support in our uv-based workflows. 
- Fixed floating `QLabel` bug in `MetalGUI` [#1031](https://github.com/qiskit-community/qiskit-metal/issues/1031).
- New CI workflow to bump version using uv, commit and push a git tag and create a draft release. This also triggers the PyPI release. 
- Update CI workflows to use Python 3.12.


## Quantum Metal v0.5.2 (Dec 11, 2025)

- We have adopted uv as a project/dependency management tool. 
- Tasks are still run using tox, but with the tox-uv plugin. 
- We adopted ruff for linting and formatting. We have a good starting configuration for linting, but it needs some work before it could be considered stable. 
- The GitHub actions workflows have been updates with these changes. 
    - Python 3.12 is the slowest to build wheels in CI, partly because qutip and pandas take a very long time to build on this version. This needs to be investigated. 
- New developer onboarding instuctions added to `README_developers.md`. The old instructions in`README_developers.md` have been retained with a note for usage on older versions of `qiskit-metal`. 
- Development install instructions have been added to documentation in the "Contributor Guide". 
- Installation instructions have been updates. More updates to come. 
- Single source package version from `pyproject.toml`.
- Updated to contributor docs to add instructions on bumping package version using uv. 



## QISKIT METAL v0.5 (2025)

### Major Updates

This release addresses significant package changes and ports:

- **PyQt5 to PySide6**: A complete overhaul of the GUI.
- **GDSPY to GDSTK**: Replaced GDSPY with the more robust GDSTK library.
- **PYAEDT to Ansys (v1.0)**: Major update with a new syntax. Extensive testing required.
- **Installation Improvements**: Transitioned to `venv` for faster environment setup, moving away from `conda`. Also, most package versions have been floated and upgraded.
- **Docs**:
    - Migrate qiskit_sphinx_theme to the new theme
    - Add divs on the front page to tuts etc
    - Add user content and showcase page

---

### GUI Enhancements

1. **Traceback Reporting**: Added detailed traceback reporting in the logging system to aid debugging.
2. **Model Reset Issue**: Fixed the issue causing the warning: *"metal: WARNING: endResetModel called on LibraryFileProxyModel(0x17fda8200) without calling beginResetModel first (No context available from Qt)"*.
3. **MPL Renderer Issue**: Resolved the error: *"Ignoring fixed y limits to fulfill fixed data aspect with adjustable data limits. Ignoring fixed x limits to fulfill fixed data aspect with adjustable data limits."*.
4. **UI Button Update**: Added a red border style to the "Create Component" button in the UI for better visibility.

---

### PYAEDT Update

- **FutureWarning**: The `pyaedt` module has been restructured and is now an alias for the new package structure based on `ansys.aedt.core`. To avoid issues in future versions, please update your imports to use the new architecture. Additionally, several files have been renamed to follow the PEP 8 naming conventions. For more information, refer to the [Ansys AEDT documentation](https://aedt.docs.pyansys.com/version/stable/release_1_0.html).
