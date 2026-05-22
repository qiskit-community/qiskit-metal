# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Implementation of :func:`qiskit_metal.viewer.view`."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from qiskit_metal.designs import QDesign
from qiskit_metal.renderers.renderer_mpl.mpl_renderer import QMplRenderer


def view(
    design: QDesign,
    ax: Optional[Axes] = None,
    *,
    figsize: Tuple[float, float] = (8.0, 8.0),
    components: Optional[Iterable[str]] = None,
    hidden_layers: Optional[Iterable[int]] = None,
    title: Optional[str] = None,
) -> Figure:
    """Render ``design`` to a matplotlib :class:`~matplotlib.figure.Figure`.

    Headless replacement for the Qt :class:`MetalGUI` plot panel for
    use in scripts, Jupyter notebooks, and cloud notebook environments
    where Qt isn't available or wanted. Returns the populated
    :class:`Figure` so callers can save, embed in subplots, or further
    customise it.

    Parameters
    ----------
    design : QDesign
        The design to render.
    ax : matplotlib.axes.Axes, optional
        If provided, render into this axes. Otherwise a new
        ``Figure`` / ``Axes`` pair of size ``figsize`` is created.
    figsize : tuple of (float, float), default (8.0, 8.0)
        Size of the new ``Figure`` in inches. Ignored when ``ax`` is
        given.
    components : iterable of str, optional
        If given, render only these named components. By default,
        every component in the design is rendered.
    hidden_layers : iterable of int, optional
        Layer numbers to hide from the rendering.
    title : str, optional
        If given, set as the axes title.

    Returns
    -------
    matplotlib.figure.Figure
        The figure containing the rendered design. If ``ax`` was
        provided, this is ``ax.figure``; otherwise it's the newly
        created figure.

    Examples
    --------
    Simplest usage — render and save::

        import qiskit_metal as qm
        from qiskit_metal.designs import DesignPlanar
        from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket

        design = DesignPlanar()
        TransmonPocket(design, "Q1",
                       options={"connection_pads": {"a": {}}})

        fig = qm.view(design)
        fig.savefig("q1.png")

    Render into an existing axes for a multi-panel figure::

        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        qm.view(design_a, ax=axes[0], title="Design A")
        qm.view(design_b, ax=axes[1], title="Design B")

    Render only one component out of a larger design::

        qm.view(design, components=["Q1"])
    """
    caller_supplied_ax = ax is not None
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    renderer = QMplRenderer(design=design)

    if hidden_layers is not None:
        renderer.hidden_layers = set(hidden_layers)

    if components is not None:
        requested = set(components)
        # ``design.components`` maps name -> QComponent. Hide every
        # component whose name isn't in the requested set.
        hidden_ids = {
            c.id for name, c in design.components.items() if name not in requested
        }
        renderer._hidden_components = hidden_ids

    ax.set_aspect("equal")
    renderer.render(ax)
    ax.autoscale_view()
    # Add a small margin so geometry doesn't sit flush against the edge.
    ax.margins(0.05)

    if title is not None:
        ax.set_title(title)

    # With the inline / Agg backend, pyplot's figure manager keeps every figure
    # created by plt.subplots() open.  IPython's post_execute hook then calls
    # plt.show(), which displays the figure (render #1); returning `fig` from
    # the cell displays it a second time (render #2).  Closing deregisters the
    # figure from the manager and prevents the duplicate.
    #
    # With interactive backends (ipympl / widget, Qt, Tk, …) we must NOT call
    # plt.close(): it destroys the live widget canvas and the figure falls back
    # to a static PNG when IPython tries to display it.  Those backends handle
    # de-duplication themselves, so no close is needed.
    # Only close figures that *we* created. If the caller supplied their own ax,
    # they own the figure lifecycle — closing it here would destroy their canvas.
    import matplotlib as _mpl

    backend = _mpl.get_backend().lower()
    if not caller_supplied_ax and ("inline" in backend or backend == "agg"):
        plt.close(fig)

    return fig
