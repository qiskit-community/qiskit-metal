# 17-qubit surface-code chip: builder and measured geometry

Used by `53-Wallraff_17Qubit_SurfaceCode.ipynb`.

- `wallraff_17q.py` builds the layout in stages from `geometry.json`.
- `geometry.json` holds the geometry measured from published micrographs of
  the device; its `_source` field gives the sources.
- `chip_inspect.py` draws a grid of zoomed panels, one per qubit.

Device: S. Krinner, N. Lacroix et al., Nature 605, 669 (2022).
