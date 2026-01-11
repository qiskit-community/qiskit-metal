from typing import List, Tuple
from qiskit_metal.designs.design_base import QDesign


def get_min_bounding_box(design: QDesign, qcomp_ids: List[int], case: int,
                         logger) -> Tuple[float]:
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
            min_x, min_y, max_x, max_y = design._components[
                qcomp_id].qgeometry_bounds()
            min_x_main = min(min_x, min_x_main)
            min_y_main = min(min_y, min_y_main)
            max_x_main = max(max_x, max_x_main)
            max_y_main = max(max_y, max_y_main)
    return min_x_main, min_y_main, max_x_main, max_y_main
