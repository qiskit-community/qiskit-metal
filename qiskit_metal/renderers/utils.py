import re
from ..designs.design_base import QDesign


def get_clean_name(name: str) -> str:
    """Create a valid variable name from the given one by removing having it
    begin with a letter or underscore followed by an unlimited string of
    letters, numbers, and underscores.

    Args:
        name (str): Initial, possibly unusable, string to be modified.

    Returns:
        str: Variable name consistent with Python naming conventions.
    """
    # Remove invalid characters
    name = re.sub("[^0-9a-zA-Z_]", "", name)
    # Remove leading characters until we find a letter or underscore
    name = re.sub("^[^a-zA-Z_]+", "", name)
    return name


def get_min_bounding_box(design: QDesign, qcomp_ids: list[int], case: int,
                         logger) -> tuple[float]:
    """
    Determine the max/min x/y coordinates of the smallest rectangular, axis-aligned
    bounding box that will enclose a selection of components to render, given by
    self.qcomp_ids. This method is only used when box_plus_buffer is True.

    Returns:
        Tuple[float]: min x, min y, max x, and max y coordinates of bounding box.
    """
    min_x_main = min_y_main = float("inf")
    max_x_main = max_y_main = float("-inf")
    if case == 2:  # One or more components not in QDesign.
        logger.warning("One or more components not found.")
    elif case == 1:  # All components rendered.
        for qcomp in design.components:
            min_x, min_y, max_x, max_y = design.components[
                qcomp].qgeometry_bounds()
            min_x_main = min(min_x, min_x_main)
            min_y_main = min(min_y, min_y_main)
            max_x_main = max(max_x, max_x_main)
            max_y_main = max(max_y, max_y_main)
    else:  # Strict subset rendered.
        for qcomp_id in qcomp_ids:
            min_x, min_y, max_x, max_y = design.components[
                qcomp_id].qgeometry_bounds()
            min_x_main = min(min_x, min_x_main)
            min_y_main = min(min_y, min_y_main)
            max_x_main = max(max_x, max_x_main)
            max_y_main = max(max_y, max_y_main)
    return min_x_main, min_y_main, max_x_main, max_y_main
