# -*- coding: utf-8 -*-

# This code is part of Qiskit / Quantum Metal.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
"""Headless drop-in replacement for ``MetalGUI``.

In environments without an X display (Colab, Binder, JupyterHub, CI,
``QISKIT_METAL_HEADLESS=1``), the desktop Qt ``MetalGUI`` cannot run.
``MetalGUIHeadless`` provides the **same tutorial-facing surface**
(``rebuild`` / ``edit_component`` / ``autoscale`` / ``screenshot`` /
``highlight_components`` / ``zoom_on_components`` / ``main_window``)
but renders inline via ``qm.view(design)`` instead of opening a Qt
window. The factory :func:`qiskit_metal.gui` picks between
``MetalGUI`` and ``MetalGUIHeadless`` based on the environment, so
tutorial code that uses ``gui = qm.gui(design)`` works in both
contexts unchanged.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from qiskit_metal.designs import QDesign


_logger = logging.getLogger(__name__)


class _NoOpMainWindow:
    """Stub for ``gui.main_window`` so tutorial calls like
    ``gui.main_window.close()`` are no-ops in headless mode."""

    def close(self) -> None:  # noqa: D401
        """No-op in headless mode."""
        return None

    def show(self) -> None:
        """No-op in headless mode."""
        return None

    def raise_(self) -> None:
        """No-op in headless mode."""
        return None


class MetalGUIHeadless:
    """Headless drop-in for :class:`MetalGUI`.

    Mirrors the public surface used by the tutorial notebooks so the
    same code runs in Colab / Binder / CI without Qt. Inline rendering
    is delegated to :func:`qiskit_metal.viewer.view`.

    Args:
        design (QDesign): The Quantum Metal design to view.
        figsize (tuple[float, float], optional): Matplotlib figure size
            in inches for inline renders. Defaults to ``(8, 6)``.
        autoscale (bool, optional): If True, every ``rebuild()`` /
            ``screenshot()`` re-fits the view to the design extent.
            Defaults to True.

    Example:
        >>> from qiskit_metal import designs
        >>> import qiskit_metal as qm
        >>> design = designs.DesignPlanar()
        >>> gui = qm.gui(design)           # picks MetalGUI or MetalGUIHeadless
        >>> # ... add components ...
        >>> gui.rebuild()
        >>> gui.autoscale()
        >>> gui.screenshot("my_chip.png")

    Notes:
        - ``edit_component(name)`` prints the component's options table
          instead of opening a Qt edit panel.
        - ``highlight_components(names)`` remembers the names for the
          next render but the highlight color rendering is best-effort
          (matplotlib backend, not the polished Qt highlight).
        - ``zoom_on_components(names)`` computes a bbox from component
          ``qgeometry_bounds()`` and sets it as the next render limits.
        - ``main_window`` is a stub whose ``close()`` is a no-op.
    """

    def __init__(
        self,
        design: "QDesign",
        figsize: tuple = (8, 6),
        autoscale: bool = True,
    ) -> None:
        self._design = design
        self._figsize = figsize
        self._autoscale_default = autoscale
        self._highlighted: List[str] = []
        self._zoom_bounds: Optional[tuple] = None  # (xmin, ymin, xmax, ymax)
        self._last_figure: Optional["Figure"] = None
        self.main_window = _NoOpMainWindow()

    # ── Tutorial-facing surface (mirrors MetalGUI) ───────────────────────

    @property
    def design(self) -> "QDesign":
        """The active design."""
        return self._design

    def set_design(self, design: "QDesign") -> None:
        """Swap the active design and re-render."""
        self._design = design
        self.rebuild()

    def rebuild(self, autoscale: bool = False) -> Optional["Figure"]:
        """Rebuild the design geometry and re-render the inline figure.

        Args:
            autoscale (bool): If True, reset zoom bounds before
                rendering. Default matches :class:`MetalGUI`'s
                behavior (no autoscale unless requested).

        Returns:
            matplotlib.figure.Figure: The re-rendered figure (also
            displayed inline in Jupyter).
        """
        # Mirror MetalGUI: rebuild() recomputes geometry from current
        # component options. design.rebuild() is the underlying call.
        self._design.rebuild()

        if autoscale:
            self._zoom_bounds = None

        return self._render()

    def refresh(self) -> Optional["Figure"]:
        """Alias for :meth:`rebuild` (matches MetalGUI's refresh)."""
        return self.rebuild()

    def autoscale(self) -> Optional["Figure"]:
        """Clear any zoom bounds and re-render at full design extent."""
        self._zoom_bounds = None
        return self._render()

    def edit_component(self, name: str) -> None:
        """Print the component's options table (Qt edit panel substitute).

        In Qt ``MetalGUI`` this opens the component editor dock. In
        headless mode we print the component's options so the user
        can still inspect and (manually) edit them.
        """
        if name not in self._design.components:
            print(f"[MetalGUIHeadless] No component named '{name}' in design.")
            return
        comp = self._design.components[name]
        print(f"=== Component: {name} ({type(comp).__name__}) ===")
        try:
            from pprint import pprint

            pprint(dict(comp.options))
        except Exception:
            print(comp.options)

    def highlight_components(self, component_names: List[str]) -> Optional["Figure"]:
        """Mark components for highlighting on the next render.

        Args:
            component_names (List[str]): Components to highlight.

        Returns:
            The newly rendered figure (with highlight applied).
        """
        self._highlighted = list(component_names)
        return self._render()

    def zoom_on_components(self, components: List[str]) -> Optional["Figure"]:
        """Zoom the next render to fit the given components.

        Computes a bounding box from each component's
        ``qgeometry_bounds()`` and uses it as the render limits.
        """
        if not components:
            self._zoom_bounds = None
            return self._render()

        xmins, ymins, xmaxs, ymaxs = [], [], [], []
        for name in components:
            if name not in self._design.components:
                continue
            comp = self._design.components[name]
            try:
                xmin, ymin, xmax, ymax = comp.qgeometry_bounds()
                xmins.append(xmin)
                ymins.append(ymin)
                xmaxs.append(xmax)
                ymaxs.append(ymax)
            except Exception:  # pragma: no cover
                continue

        if xmins:
            # Add 10% padding around the framed components.
            xmin, ymin = min(xmins), min(ymins)
            xmax, ymax = max(xmaxs), max(ymaxs)
            dx = (xmax - xmin) * 0.1 or 0.1
            dy = (ymax - ymin) * 0.1 or 0.1
            self._zoom_bounds = (xmin - dx, ymin - dy, xmax + dx, ymax + dy)

        return self._render()

    def screenshot(
        self,
        name: str = "shot",
        type_: str = "png",
        display: bool = True,
        disp_ops: Optional[dict] = None,
    ) -> Optional["Figure"]:
        """Render the current view and save to disk; display inline.

        Mirrors :meth:`MetalGUI.screenshot` so tutorial code is
        unchanged. The headless version saves the matplotlib figure
        rather than a Qt grab.

        Args:
            name (str): File stem (no extension). Saved as
                ``{name}.{type_}`` in the current working directory.
            type_ (str): File extension / matplotlib format. Default
                ``"png"``.
            display (bool): If True, also display inline in Jupyter.
            disp_ops (dict, optional): Reserved for compatibility.
                Currently a ``{"width": int}`` key sets the saved
                figure width in pixels.

        Returns:
            matplotlib.figure.Figure: The rendered figure.
        """
        fig = self._render(display_inline=False)
        if fig is None:
            return None

        path = Path(f"{name}.{type_}")
        save_kwargs = {"bbox_inches": "tight"}
        if disp_ops and "width" in disp_ops:
            # Crude width control: dpi ~ pixels / inches
            width_in = self._figsize[0]
            save_kwargs["dpi"] = max(50, int(disp_ops["width"] / width_in))
        fig.savefig(path, **save_kwargs)

        if display:
            try:
                from IPython.display import Image, display as ipy_display

                ipy_display(Image(filename=str(path)))
            except Exception:  # pragma: no cover
                pass

        return fig

    # ── Internal helpers ─────────────────────────────────────────────────

    def _render(self, display_inline: bool = True) -> Optional["Figure"]:
        """Re-render the design with current zoom + highlight state."""
        try:
            # Import here so headless module stays lite-install-safe.
            from qiskit_metal.viewer import view as qm_view
        except ImportError as exc:  # pragma: no cover
            _logger.warning("MetalGUIHeadless: cannot import viewer: %s", exc)
            return None

        fig = qm_view(self._design)
        self._last_figure = fig

        try:
            ax = fig.gca()
            if self._zoom_bounds is not None:
                xmin, ymin, xmax, ymax = self._zoom_bounds
                ax.set_xlim(xmin, xmax)
                ax.set_ylim(ymin, ymax)

            # Best-effort highlight: redraw highlighted components as
            # an overlay rectangle behind the existing geometry.
            if self._highlighted:
                for name in self._highlighted:
                    comp = self._design.components.get(name)
                    if comp is None:
                        continue
                    try:
                        xmin, ymin, xmax, ymax = comp.qgeometry_bounds()
                        from matplotlib.patches import Rectangle

                        rect = Rectangle(
                            (xmin, ymin),
                            xmax - xmin,
                            ymax - ymin,
                            linewidth=2.0,
                            edgecolor="#FF8C00",  # vivid orange — visible against the chip
                            facecolor="#FF8C00",
                            alpha=0.18,
                            zorder=10,
                        )
                        ax.add_patch(rect)
                    except Exception:  # pragma: no cover
                        continue
        except Exception as exc:  # pragma: no cover
            _logger.debug("MetalGUIHeadless: post-render decoration skipped: %s", exc)

        return fig


def _is_headless_environment() -> bool:
    """Detect Colab / Binder / no-display / explicit-headless environments.

    Returns True if Quantum Metal should fall back to inline matplotlib
    rendering instead of opening a Qt window.
    """
    import os

    # Explicit override — always honored.
    if os.environ.get("QISKIT_METAL_HEADLESS") == "1":
        return True

    # Google Colab.
    try:
        import google.colab  # noqa: F401

        return True
    except ImportError:
        pass

    # Binder advertises itself via env vars.
    if os.environ.get("BINDER_REQUEST") or os.environ.get("BINDER_SERVICE_HOST"):
        return True

    # Linux session without an X display.
    import sys

    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True

    # PySide6 not installed → must be headless.
    try:
        import PySide6  # noqa: F401
    except ImportError:
        return True

    return False


def gui(
    design: "QDesign",
    *,
    force_headless: Optional[bool] = None,
    **kwargs,
):
    """Return the right GUI object for the current environment.

    Picks :class:`MetalGUIHeadless` in environments without a display
    (Colab, Binder, no PySide6, ``QISKIT_METAL_HEADLESS=1``); otherwise
    returns the Qt-based :class:`MetalGUI`. Tutorial code that uses
    ``gui = qm.gui(design)`` runs in both contexts unchanged.

    Args:
        design (QDesign): The design to view.
        force_headless (bool, optional): Force the headless path
            regardless of environment. Useful for testing.
        **kwargs: Forwarded to the chosen class' constructor.

    Returns:
        :class:`MetalGUI` or :class:`MetalGUIHeadless`.

    Example:
        >>> import qiskit_metal as qm
        >>> from qiskit_metal import designs
        >>> design = designs.DesignPlanar()
        >>> gui = qm.gui(design)  # Qt locally, headless in Colab
    """
    use_headless = (
        force_headless if force_headless is not None else _is_headless_environment()
    )

    if use_headless:
        return MetalGUIHeadless(design, **kwargs)

    try:
        # Import here so the lite install (no PySide6) never tries to
        # touch Qt-coupled modules.
        from qiskit_metal._gui.main_window import MetalGUI

        return MetalGUI(design, **kwargs)
    except ImportError:
        _logger.info(
            "qm.gui(): PySide6 / MetalGUI unavailable; falling back to headless."
        )
        return MetalGUIHeadless(design, **kwargs)
