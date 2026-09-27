"""Grid of zoomed panels, one per site, to inspect a design feature by feature.

A whole-chip render hides errors that are obvious when the same small window
is shown for every qubit side by side -- a line ending 90 degrees off, or a
standoff that varies from qubit to qubit. Optionally draws a reference image
behind each panel, e.g. a micrograph of the device being reproduced.

Typical use::

    from chip_inspect import inspect_sites
    fig = inspect_sites(design, {"D1": (0.0, 3.5), "D2": (1.6, 1.75)})

    # with a reference image behind the geometry
    fig = inspect_sites(design, sites, image="chip.png",
                        px_per_mm=133.55, origin_px=(958, 958))
"""

from __future__ import annotations

import numpy as np


def _panel_geoms(design, layers=None):
    """Every drawn shape in the design as (shapely geom, width, is_poly)."""
    out = []
    for kind in ("path", "poly"):
        table = design.qgeometry.tables.get(kind)
        if table is None or len(table) == 0:
            continue
        for _, row in table.iterrows():
            if row.get("subtract", False):
                continue
            if layers is not None and row.get("layer") not in layers:
                continue
            out.append((row.geometry, float(row.get("width", 0) or 0), kind == "poly"))
    return out


def inspect_sites(
    design,
    sites,
    image=None,
    px_per_mm=None,
    origin_px=None,
    radius=0.42,
    cols=6,
    layers=None,
    label=None,
    title=None,
    design_color="#00e5ff",
    figsize_per=3.2,
):
    """Grid of zoomed crops, one per site, design geometry over a reference image.

    Args:
        design (QDesign): the built design.
        sites (dict): ``{name: (x_mm, y_mm)}`` -- what to center each panel on.
        image (str | PIL.Image.Image | None): optional reference micrograph to
            draw behind the design. Omit it to inspect the design on its own --
            which is the right choice for published material, since a
            photograph will not register perfectly with a reconstruction and
            the near-misses read as errors that are not there.
        px_per_mm (float): image scale. Required only with ``image``.
        origin_px (tuple): pixel coordinates of the design origin (0, 0) in the
            image, ``(x, y)``, y measured downward as images are. Required only
            with ``image``.
        radius (float): half-width of each crop, in mm.
        cols (int): panels per row.
        layers (set | None): restrict drawn geometry to these layers.
        label (callable | None): ``label(name) -> str`` for the panel title;
            defaults to the site name. Use it to show a measured quantity.
        title (str | None): suptitle.

    Returns:
        matplotlib.figure.Figure
    """
    import matplotlib.pyplot as plt
    from shapely.geometry import box

    img = None
    if image is not None:
        from PIL import Image

        if px_per_mm is None or origin_px is None:
            raise ValueError("px_per_mm and origin_px are required with an image")
        img = Image.open(image) if isinstance(image, str) else image
        ox, oy = origin_px
    geoms = _panel_geoms(design, layers)

    names = list(sites)
    rows = int(np.ceil(len(names) / cols))
    fig, axes = plt.subplots(
        rows, cols, figsize=(figsize_per * cols, figsize_per * rows), squeeze=False
    )

    for ax, name in zip(axes.ravel(), names):
        cx, cy = sites[name]
        win = box(cx - radius, cy - radius, cx + radius, cy + radius)
        if img is not None:
            crop = img.crop(
                (
                    int(ox + (cx - radius) * px_per_mm),
                    int(oy - (cy + radius) * px_per_mm),
                    int(ox + (cx + radius) * px_per_mm),
                    int(oy - (cy - radius) * px_per_mm),
                )
            )
            ax.imshow(
                crop,
                extent=[cx - radius, cx + radius, cy - radius, cy + radius],
                cmap="gray",
                origin="upper",
            )
        else:
            ax.set_facecolor("#f7f7f7")

        for geom, width, is_poly in geoms:
            if not geom.intersects(win):
                continue
            clipped = geom.intersection(win)
            for part in getattr(clipped, "geoms", [clipped]):
                if part.is_empty:
                    continue
                if is_poly or part.geom_type in ("Polygon", "MultiPolygon"):
                    xs, ys = part.exterior.xy
                    ax.fill(xs, ys, color=design_color, alpha=0.35, lw=0)
                    ax.plot(xs, ys, color=design_color, lw=1.0)
                elif part.geom_type == "LineString":
                    xs, ys = part.xy
                    # Draw at the trace's real width so the panel shows metal,
                    # not a hairline that always looks like it clears everything.
                    # Width is in mm, so scale by panel size rather than by the
                    # image, which may not be there.
                    pts_per_mm = figsize_per * 72.0 / (2 * radius)
                    ax.plot(
                        xs,
                        ys,
                        color=design_color,
                        alpha=0.85,
                        lw=max(1.0, width * pts_per_mm),
                        solid_capstyle="butt",
                    )

        ax.set_title(label(name) if label else name, fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(cx - radius, cx + radius)
        ax.set_ylim(cy - radius, cy + radius)

    for ax in axes.ravel()[len(names) :]:
        ax.axis("off")
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    return fig
