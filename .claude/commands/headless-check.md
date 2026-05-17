# /headless-check — verify the Qt-free path locally

This command reproduces the `tests-lite` CI job locally so you can
catch a broken headless path before pushing. Use it when:

- You're about to push a change that touches `__init__.py`,
  `_gui/`, `renderer_mpl/`, or `viewer/`.
- The `tests-lite` CI job failed and you need to debug.
- A user reports `pip install quantum-metal[lite]` doesn't work.

## What "the headless path" means

After v0.6.1, this works without PySide6 / pyaedt / gmsh
installed:

```python
import qiskit_metal as qm
from qiskit_metal.designs import DesignPlanar
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket

design = DesignPlanar()
TransmonPocket(design, "Q1", options={"connection_pads": {"a": {}}})
fig = qm.view(design)
```

If this breaks on any of the listed installs being absent,
someone added a top-level Qt / Ansys / gmsh import somewhere
they shouldn't have.

## Procedure

### 1. Build a lite venv

```bash
cd /tmp
rm -rf qm_lite_check && mkdir qm_lite_check && cd qm_lite_check
uv venv --python 3.12 --quiet

# Install exactly the lite dep set. NO pyside6, pyaedt, or gmsh.
uv pip install --quiet \
    'addict>=2.4.0' \
    'gdstk>=0.9' \
    'geopandas>=1.0' \
    'matplotlib>=3.7.0' \
    'numpy>=1.24.2,<2' \
    'pandas>=2.1.1' \
    'pint>=0.21.0' \
    'pyEPR-quantum>=0.9.5' \
    'pygments>=2.14.0' \
    'qutip>=5.0.0' \
    'scipy>=1.10.0' \
    'shapely>=2.0.1' \
    'scqubits>=4.1.0' \
    'pyyaml>=6.0' \
    'pytest>=8.4.1' \
    'pytest-rich>=0.2.0'

# Install quantum-metal in editable mode, NO deps (we just hand-listed them)
uv pip install --no-deps -e /path/to/qiskit-metal
```

### 2. Confirm PySide6 isn't installed

```bash
uv pip show pyside6 2>&1 | head -2
# Expected: "warning: Package(s) not found for: pyside6"
```

If pyside6 IS installed, the test is invalid — start over from
step 1.

### 3. Smoke test

**Use `.venv/bin/python` directly, NOT `uv run python`** —
`uv run` auto-syncs the venv to pyproject.toml's full deps,
silently reinstalling pyside6 / pyaedt / gmsh and defeating the
test.

```bash
QISKIT_METAL_HEADLESS=1 .venv/bin/python -c "
import qiskit_metal as qm
from qiskit_metal.designs import DesignPlanar
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket

design = DesignPlanar()
TransmonPocket(design, 'Q1', options={'connection_pads': {'a': {}}})
fig = qm.view(design)
print('OK:', type(fig).__name__)
"
```

Expected output (4 `Renderer=... skipped` lines, then OK):

```
Renderer=gmsh skipped: an optional dependency ... 'gmsh' ... is not installed
Renderer=elmer skipped: ...
Renderer=aedt_q3d skipped: ...
Renderer=aedt_hfss skipped: ...
OK: Figure
```

If you get `ModuleNotFoundError`, find the culprit:

```bash
QISKIT_METAL_HEADLESS=1 .venv/bin/python -c "
import sys
class Block:
    def find_spec(self, name, path, target=None):
        if name.startswith('PySide6'):
            import traceback
            print(f'\\n*** Qt import attempted: {name}')
            traceback.print_stack(limit=15)
            sys.exit(0)
        return None
sys.meta_path.insert(0, Block())
import qiskit_metal
"
```

The traceback shows which module pulled in Qt.

### 4. Run the no-Qt test suite

```bash
.venv/bin/python -m pytest \
    /path/to/qiskit-metal/tests/test_viewer.py \
    /path/to/qiskit-metal/tests/test_qlibrary_idempotency.py \
    /path/to/qiskit-metal/tests/test_qlibrary_pin_sanity.py \
    /path/to/qiskit-metal/tests/test_default_options_completeness.py \
    /path/to/qiskit-metal/tests/test_solution_types.py \
    -v
```

All four files must pass on the lite venv.

### 5. Execute the canonical headless tutorial

```bash
uv pip install --quiet 'jupyter>=1.0' 'nbconvert>=7.0' 'ipykernel>=6.0'
.venv/bin/python -m ipykernel install --user --name qm_lite_check
QISKIT_METAL_HEADLESS=1 .venv/bin/jupyter nbconvert \
    --to notebook \
    --execute \
    --ExecutePreprocessor.kernel_name=qm_lite_check \
    --ExecutePreprocessor.timeout=180 \
    --output-dir /tmp/qm_lite_check/out \
    '/path/to/qiskit-metal/tutorials/1 Overview/1.4 Headless quick view (no Qt GUI).ipynb'
```

The notebook should execute cleanly (~30s).

### 6. Cleanup

```bash
rm -rf /tmp/qm_lite_check
rm -rf ~/.local/share/jupyter/kernels/qm_lite_check  # the ipykernel registration
```

## Common failure modes

| Symptom | Likely cause |
|---------|--------------|
| `ModuleNotFoundError: No module named 'PySide6'` | Some non-`_gui/` module added a top-level `from PySide6 import …`. Use the traceback hook (step 3) to find it. |
| `ModuleNotFoundError: No module named 'gmsh'` | A renderer auto-import in `_start_renderers` isn't wrapped in `try/except ImportError`. Check `designs/design_base.py:_start_renderers`. |
| `KeyError: 1` in `render_junction` | pandas 2.2 positional-indexing issue. Replace `x[1]` with `x.iloc[1]`. See `lessons-learned.md`. |
| Tests pass but `nbconvert --execute` fails with import error | Kernel issue — verify you registered the venv as `qm_lite_check` and passed `--ExecutePreprocessor.kernel_name=qm_lite_check`. |
| `uv run` re-installs PySide6 | You used `uv run` instead of `.venv/bin/python`. See `lessons-learned.md`. |

## What to report

After running, produce a short status:

```markdown
## Headless check — <date>

- Lite venv built: <yes/no>
- PySide6 absent: <confirmed/installed>
- Smoke test (qm.view): <OK / error>
- No-Qt test suite: <X/X passed>
- 1.4 notebook execute: <OK / error>

### Issues found
- ...
```
