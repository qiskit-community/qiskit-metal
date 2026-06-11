# -*- coding: utf-8 -*-

# This code is part of Qiskit / Quantum Metal.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Backend-agnostic inline-display helper for matplotlib figures.

When the active matplotlib backend is interactive (``Qt6Agg`` while the
desktop ``MetalGUI`` is open, or ``TkAgg`` on some local installs),
``plt.show()`` opens a separate OS window rather than rendering inline
in a Jupyter cell — the cell output stays empty. :func:`show_inline`
writes the figure to a PNG buffer and displays via
:class:`IPython.display.Image`, producing identical inline output in
both Qt mode and the headless / Agg / inline backends. Falls back to
``plt.show()`` when IPython is not available (plain-Python scripts).
"""

from __future__ import annotations

import io
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.figure import Figure


def show_inline(
    fig: "Optional[Figure]" = None,
    *,
    dpi: int = 110,
    close: bool = True,
) -> None:
    """Display a matplotlib ``Figure`` inline regardless of the active backend.

    When ``MetalGUI`` is open, matplotlib's backend is ``Qt6Agg``, which
    makes ``plt.show()`` open a separate OS window instead of rendering
    inline in Jupyter — and the cell output stays empty. ``show_inline``
    renders the figure to a PNG buffer and displays via
    ``IPython.display.Image``: identical output in Qt mode and in the
    headless / Agg / inline backends.

    Args:
        fig: The matplotlib ``Figure`` to display. Defaults to
            ``plt.gcf()`` (the current figure) if omitted.
        dpi: PNG render DPI. Default ``110``.
        close: Close the figure after rendering (default ``True``).
            Prevents Jupyter's auto-display from rendering the figure
            a second time when ``fig`` is also the cell's last
            expression.

    Notes:
        Falls back to ``plt.show()`` when IPython is unavailable (plain
        Python sessions, scripts, CI without notebooks).

    Example:
        >>> import matplotlib.pyplot as plt
        >>> import qiskit_metal as qm
        >>> fig, ax = plt.subplots()
        >>> ax.plot([1, 2, 3])
        >>> qm.show_inline(fig)   # inline in Jupyter, .show() in scripts
    """
    import matplotlib.pyplot as plt

    if fig is None:
        fig = plt.gcf()

    try:
        from IPython.display import Image, display
    except ImportError:
        # No IPython — we're in a plain Python session. Best behaviour
        # is the standard interactive show.
        plt.show()
        return

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=dpi)
    if close:
        plt.close(fig)
    display(Image(buf.getvalue()))
