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
"""Simply utility functions to improve QOL of QM developers and QM users."""

import importlib
import inspect
import logging
import os
import re
import sys
import traceback
import warnings
from copy import deepcopy
from typing import TYPE_CHECKING, Tuple

import pandas as pd

from qiskit_metal.draw import Vector

if TYPE_CHECKING:
    from qiskit_metal import logger

__all__ = [
    'copy_update', 'dict_start_with', 'data_frame_empty_typed', 'clean_name',
    'enable_warning_traceback', 'get_traceback', 'print_traceback_easy',
    'log_error_easy', 'monkey_patch', 'can_write_to_path',
    'can_write_to_path_with_warning', 'toggle_numbers', 'bad_fillet_idxs',
    'compress_vertex_list', 'get_range_of_vertex_to_not_fillet'
]

####################################################################################
# Dictionary related


def copy_update(options, *args, deep_copy=True, **kwargs):
    """Utility funciton to merge two dictionaries.

    Args:
        options (object): Options
        deep_copy (bool): True to do a deep copy
        kwargs (dict): Dictionary of parameters

    Returns:
        dict: Merged dictionary
    """
    if deep_copy:
        options = deepcopy(options)
        options.update(*args, **kwargs)
    else:
        options = options.copy()
        options.update(*args, **kwargs)
    return options


def dict_start_with(my_dict, start_with, as_=list):
    """Case sensitive https://stackoverflow.com/questions/17106819/accessing-
    python-dict-values-with-the-key-start-characters.

    Args:
        my_dict (dict): The dictionary
        starts_with (str): String to check of
        as_ (type): A list of dict.  Defaults to list.

    Returns:
        list or dict: Parts of the dictionary with keys starting with the given text

    .. code-block:: python

        my_dict = {'name': 'Klauss', 'age': 26, 'Date of birth': '15th july'}
        dict_start_with(my_dict, 'Date')
    """
    if as_ == list:
        # start_with in k]
        return [v for k, v in my_dict.items() if k.startswith(start_with)]
    elif as_ == dict:
        return {k: v for k, v in my_dict.items() if k.startswith(start_with)}


# def display_options(*ops_names, options=None, find_dot_keys=True, do_display=True):
#     '''
#     Print html display of options dictionary by default `DEFAULT_OPTIONS`

#     Example use:
#     ---------------
#         display_options('make_transmon_pocket_v1', 'make_transmon_connector_v1')

#     or
#         dfs, html = display_options(Metal_Transmon_Pocket.__name__, do_display=False)
#     '''
#     # IDEA: display also ._hfss and ._gds etc. for those that have it and add to plugins
#     if options is None:
#         from .. import DEFAULT_OPTIONS
#         options = DEFAULT_OPTIONS

#     res = []
#     for keyname in ops_names:
#         if find_dot_keys:
#             names = list(filter(lambda x, match=keyname: x is match or
#                                 x.startswith(match+'.'), DEFAULT_OPTIONS.keys()))
#             names.sort()
#             for name in names:
#                 res += [pd.Series(options[name], name=name).to_frame()]
#         else:
#             res += [pd.Series(options[keyname], name=keyname).to_frame()]

#     from pyEPR.toolbox import display_dfs
#     res_html = display_dfs(*res, do_display=do_display)  #why not just directly call the function DataFrame_display_side_by_side(*args) ?
#     return res, res_html


def data_frame_empty_typed(column_types: dict):
    """Creates and empty DataFrame with dtypes for each column given by the
    dictionary.

    Args:
        column_types (dict): A key, dtype pairs

    Returns:
        DataFrame: An empty dataframe with the typed columns
    """
    df = pd.DataFrame()
    for name, dtype in column_types.items():
        df[name] = pd.Series(dtype=dtype)
    return df


def clean_name(text: str):
    """Clean a string to a proper variable name in python.

    Args:
        text (str): Original string

    Returns:
        str: Corrected string

    .. code-block:: python

        clean_name('32v2 g #Gmw845h$W b53wi ')

    *Output*
        `'_32v2_g__Gmw845h_W_b53wi_'`

    See https://stackoverflow.com/questions/3303312/how-do-i-convert-a-string-to-a-valid-variable-name-in-python
    """
    return re.sub('\W|^(?=\d)', '_', text)


####################################################################################
# Tracebacks

_old_warn = None


def enable_warning_traceback():
    """Show ow traceback on warning."""

    global _old_warn
    _old_warn = warnings.warn

    def warn(*args, **kwargs):
        """Warn user with traceback to warning."""
        tb = traceback.extract_stack()
        _old_warn(*args, **kwargs)
        print("".join(traceback.format_list(tb)[:-1]))

    warnings.warn = warn


def get_traceback():
    """Returns traceback string. Format each frame in the traceback as a
    string.

    Returns:
        str: Traceback string
    """
    trace_back = traceback.extract_stack()
    return "".join(traceback.format_list(trace_back)[:-1])


def print_traceback_easy(start=26):
    """Utility function to print traceback for debug. Will report in series the
    string version of the frames that we are currently in.

    Args:
        start (int): Starting position of the traceback frame.
                     Defaults to 26. Assumes runs from Jupyter notebooks.
                     In general set to zero.
    """
    print(f"\n")
    print('\n'.join(map(repr, traceback.extract_stack()[start:])))
    print('\n')


def log_error_easy(logger: logging.Logger,
                   pre_text='',
                   post_text='',
                   do_print=False):
    """Print log message.

    Args:
        logger (logging.Logger): The logger.
        pre_text (str): Initial text to write.  Defaults to ''.
        post_text (str): End text to write.  Defaults to ''.
        do_print (bool): True to do the printing, False otherwise.  Defaults to False.

    Test use:

    .. code-block:: python

        import traceback
        from qiskit_metal import logger
        from qiskit_metal.toolbox_python.utility_functions import log_error_easy

        def xx():
            exc_info = sys.exc_info()
            try:
                raise TypeError("Oups!")
            except Exception as err:
                try:
                    raise TypeError("Again !?!")
                except:
                    pass

                # exc_type, exc_value, exc_tb = sys.exc_info()
                # error = traceback.format_exception(exc_type, exc_value, exc_tb)
                # logger.error('\\n\\n'+'\\n'.join(error)+'\\n')
                log_error_easy(metal.logger)
        xx()
    """
    exc_type, exc_value, exc_tb = sys.exc_info()
    error = traceback.format_exception(exc_type, exc_value, exc_tb)
    text = f'{pre_text}\n\n' + '\n'.join(error) + f'\n{post_text}'

    logger.error(text)
    if do_print:
        print(text)


#####################################################################################


def monkey_patch(self, func, func_name=None):
    """Monkey patch a method into a class at runtime.

    Use descriptor protocol when adding method as an attribute.

    For a method on a class, when you do a.some_method, python actually does:
         a.some_method.__get__(a, type(a))

    So we're just reproducing that call sequence here explicitly.

    See: https://stackoverflow.com/questions/38485123/monkey-patching-bound-methods-in-python

    Args:
        func (function): function
        func_name (str): name of the function.  Defaults to None.
    """
    func_name = func_name or func.__name__
    setattr(self, func_name, func.__get__(self, self.__class__))
    # what happens if we reload the class or swap in real time?


####################################################################################
# Used to detect and denote potential short segments, when fillet is used.

# # Keep this method until the class QCheckLength will be fully tested.
# def which_vertex_has_potential_fillet_errors(coords: list, a_fillet: float, fillet_comparison_precision: int) -> list:
#     """Iterate through the vertex and check using critea.
#     1. If a start or end segment, is the length smaller than a_fillet.
#     2. If segment in side of LineString, is the lenght smaller than,FILLET_SCALAR times a_fillet.

#     Note, there is a rounding error issues. So when the lenght of the segment is calculated,
#     it is rounded by using fillet_comparison_precision.

#     Args:
#         coords (list): List of tuples in (x,y) format. Each tuple represents a vertex on a LineSegment.

#         a_fillet (float): The radius to fillet a vertex.

#         fillet_comparison_precision (int): There are rounding issues when comparing to (fillet * scalar).
#         Use this when calculating length of line-segment.

#     Returns:
#         list: List of idexes.  Each index corresponds to a vertex in coords, that would not fillet well.
#     """
#     vertex_of_bad = list()
#     len_coords = len(coords)
#     if len_coords <= 1:
#         return vertex_of_bad

#     # When determining the critera to fillet, scale the fillet value by FILLET_SCALAR.
#     FILLET_SCALAR = 2.0
#     scaled_fillet = a_fillet * FILLET_SCALAR

#     for index, xy in enumerate(coords):
#         # Skip the first vertex.
#         if index > 0:
#             xy_previous = coords[index-1]

#             seg_length = np.round(
#                 distance.euclidean(xy_previous, xy), fillet_comparison_precision)

#             # If at first or last segment, use just the fillet value to check, otherwise, use FILLET_SCALAR.
#             # Need to not fillet index-1 to index line segment.
#             if index == 1 or index == len_coords-1:
#                 if seg_length < a_fillet:
#                     vertex_of_bad.extend([index-1, index])
#             else:
#                 if seg_length < scaled_fillet:
#                     vertex_of_bad.extend([index-1, index])

#     # As precaution, remove duplicates from list.
#     vertex_of_bad = list(set(vertex_of_bad))
#     return vertex_of_bad


def toggle_numbers(numbers: list, totlength: int) -> list:
    """
    Given a list of integers called 'numbers', return the toggle of them from zero to totlength - 1.

    Args:
        numbers (list): Integers in the original list, in sorted order.
        totlength (int): Number of elements in complete list. Ex: [0, 1, 2, 3, ..., n - 1] has totlength n.

    Returns:
        list: A sorted list of all integers between 0 and totlength - 1, inclusive, not found in numbers.
    """
    complement = []
    if totlength:
        if not numbers:
            return [i for i in range(totlength)]
        j = 0
        for i in range(totlength):
            if i < numbers[j]:
                complement.append(i)
            else:
                j += 1
                if j >= len(numbers):
                    return complement + [k for k in range(i + 1, totlength)]
    return complement


def bad_fillet_idxs(coords: list,
                    fradius: float,
                    precision: int = 9,
                    isclosed: bool = False) -> list:
    """
    Get list of vertex indices in a linestring (isclosed = False) or polygon (isclosed = True) that cannot be filleted based on
    proximity to neighbors. By default, this list excludes the first and last vertices if the shape is a linestring.

    Args:
        coords (list): Ordered list of tuples of vertex coordinates.
        fradius (float): User-specified fillet radius from QGeometry table.
        precision (int, optional): Digits of precision used for round(). Defaults to 9.
        isclosed (bool, optional): Boolean denoting whether the shape is a linestring or polygon. Defaults to False.

    Returns:
        list: List of indices of vertices too close to their neighbors to be filleted.
    """
    length = len(coords)
    get_dist = Vector.get_distance
    if isclosed:
        return [
            i for i in range(length)
            if min(get_dist(coords[i - 1], coords[i], precision),
                   get_dist(coords[i], coords[(i + 1) %
                                              length], precision)) < 2 * fradius
        ]
    if length < 3:
        return []
    if length == 3:
        return [] if min(get_dist(coords[0], coords[1], precision),
                         get_dist(coords[1], coords[2],
                                  precision)) >= fradius else [1]
    if (get_dist(coords[0], coords[1], precision) < fradius) or (get_dist(
            coords[1], coords[2], precision) < 2 * fradius):
        badlist = [1]
    else:
        badlist = []
    for i in range(2, length - 2):
        if min(get_dist(coords[i - 1], coords[i], precision),
               get_dist(coords[i], coords[i + 1], precision)) < 2 * fradius:
            badlist.append(i)
    if (get_dist(coords[length - 3], coords[length - 2], precision) <
            2 * fradius) or (get_dist(coords[length - 2], coords[length - 1],
                                      precision) < fradius):
        badlist.append(length - 2)
    return badlist


def get_range_of_vertex_to_not_fillet(coords: list,
                                      fradius: float,
                                      precision: int = 9,
                                      add_endpoints: bool = True) -> list:
    """Provide a list of tuples for a list of integers that correspond to
    coords. Each tuple corresponds to a range of indexes within coords.  A
    range denotes vertexes that are too short to be fillet'd.

    If the range is just one point, meaning, not a segment, the tuple will contain
    the same index for start and end.

    Args:
        coords (list): Ordered list of tuples of vertex coordinates.
        fradius (float): User-specified fillet radius from QGeometry table.
        precision (int, optional): Digits of precision used for round(). Defaults to 9.
        add_endpoints (bool): Default is True.  If the second to endpoint is in list,
            add the endpoint to list.  Used for GDS, not add_qgeometry.

    Returns:
        list: A compressed list of tuples.  So, it combines adjacent vertexes into a longer one.
    """
    length = len(coords)

    # isclosed=False is for LineString
    unique_vertex = bad_fillet_idxs(coords, fradius, precision, isclosed=False)

    if add_endpoints:
        # The endpoints of LineString are never fillet'd. If the second vertex or second to last vertex
        # should not be fillet's, then don't fillet the endpoints.  This is used for warning for add_qgeometry.
        # Also used in QGDSRenderer when breaking the LineString.
        if (1 in unique_vertex) and (0 not in unique_vertex):
            unique_vertex.append(0)

        # second to last vertex in unique_vertex
        if (length - 2 in unique_vertex) and (length - 1 not in unique_vertex):
            unique_vertex.append(length - 1)

    compressed_vertex = compress_vertex_list(unique_vertex)

    return compressed_vertex


def compress_vertex_list(individual_vertex: list) -> list:
    """Given a list of vertices that should not be fillet'd, search for a range
    and make them one compressed list. If the vertex is a point and not a line
    segment, the returned tuple's start and end are the same index.

    Args:
        individual_vertex (list): List of UNIQUE ints.  Each int refers to an index of a LineString.

    Returns:
        list: A compressed list of tuples.  So, it combines adjacent vertices into a longer one.
    """
    reduced_idx = list()

    sorted_vertex = sorted(individual_vertex)
    len_vertex = len(sorted_vertex)

    if len_vertex > 0:
        # initialzie to unrealistic number.
        start = -1
        end = -1
        size_of_range = 0

        for index, item in enumerate(sorted_vertex):
            if index == 0:
                start = item
                end = item
            else:
                if item == end + 1:
                    end = item
                    size_of_range += 1
                else:
                    if size_of_range == 0:
                        # Only one vertex in range.
                        reduced_idx.append((start, end))
                        start = item
                        end = item
                    else:
                        # Two or more vertexes in range.
                        reduced_idx.append((start, end))
                        size_of_range = 0
                        start = item
                        end = item

            if index == len_vertex - 1:
                if size_of_range == 0:
                    reduced_idx.append((start, end))
                else:
                    reduced_idx.append((start, end))
        return reduced_idx
    else:
        return reduced_idx


#######################################################################################
# File checking


def can_write_to_path_with_warning(file: str) -> int:
    """Check if can write file.

    Args:
        file (str): Has the path and/or just the file name.

    Returns:
        int: 1 if access is allowed. Else returns 0, if access not given.
    """
    a_logger = logger
    # If need to use lib pathlib.
    directory_name = os.path.dirname(os.path.abspath(file))
    if os.access(directory_name, os.W_OK):
        return 1
    else:
        a_logger.warning(f'Not able to write to directory.'
                         f'File:"{file}" not written.'
                         f' Checked directory:"{directory_name}".')
        return 0


def can_write_to_path(file: str) -> Tuple[int, str]:
    """Check to see if path exists and file can be written.

    Args:
        file (str): Has the path and/or just the file name.

    Returns:
        Tuple[int, str]:
        int: 1 if access is allowed. Else returns 0, if access not given.
        str: Full path and file which was searched for.
    """
    # If need to use lib pathlib.
    directory_name = os.path.dirname(os.path.abspath(file))
    if os.access(directory_name, os.W_OK):
        return 1, directory_name
    else:
        return 0, directory_name
