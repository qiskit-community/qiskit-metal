# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

'''
Simply utility functions to improve QOL of QM developers and QM users

@date: 2019
@author: Zlatko K. Minev (IBM)
@modified: Thomas McConkey 2019/10/16
'''

import logging
import re
import sys
import traceback
import warnings
import logging
import sys
import os
import pandas as pd
import numpy as np
from scipy.spatial import distance
from typing import Tuple

from copy import deepcopy
from qiskit_metal import logger

__all__ = ['copy_update', 'dict_start_with', 'data_frame_empty_typed', 'clean_name',
           'enable_warning_traceback', 'get_traceback', 'print_traceback_easy', 'log_error_easy',
           'monkey_patch', 'are_there_potential_fillet_errors', 'compress_list', 'can_write_to_path', 'can_write_to_path_with_warning']

####################################################################################
# Dictionary related


def copy_update(options, *args, deep_copy=True, **kwargs):
    '''
    Utility funciton to merge two dictionaries

    Args:
        options (object): options
        deep_copy (bool): True to do a deep copy
        kwargs (dict): dictionary of parameters

    Returns:
        dict: merged dictionary
    '''
    if deep_copy:
        options = deepcopy(options)
        options.update(*args, **kwargs)
    else:
        options = options.copy()
        options.update(*args, **kwargs)
    return options


def dict_start_with(my_dict, start_with, as_=list):
    ''' Case sensitive
    https://stackoverflow.com/questions/17106819/accessing-python-dict-values-with-the-key-start-characters

    Args:
        my_dict (dict): the dictionary
        starts_with (str): string to check of
        as_ (type): list of dict (Default: list)

    Returns:
        list or dict: parts of the dictionary with keys starting with the given text

    .. code-block:: python

        my_dict = {'name': 'Klauss', 'age': 26, 'Date of birth': '15th july'}
        dict_start_with(my_dict, 'Date')

    '''
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
    """Creates and empty DataFrame with dtypes for each column given
    by the dicitonary,

    Arguments:
        column_types (dict): key, dtype pairs

    Returns:
        DataFrame: empty dataframe with the typed columns
    """
    df = pd.DataFrame()
    for name, dtype in column_types.items():
        df[name] = pd.Series(dtype=dtype)
    return df


def clean_name(text: str):
    """Clean a string to a proper variable name in python

    Arguments:
        text (str): original string

    Returns:
        str: corrected string

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
    """
    Show ow traceback on warning
    """

    global _old_warn
    _old_warn = warnings.warn

    def warn(*args, **kwargs):
        '''
        Warn user with traceback to warning
        '''
        tb = traceback.extract_stack()
        _old_warn(*args, **kwargs)
        print("".join(traceback.format_list(tb)[:-1]))
    warnings.warn = warn


def get_traceback():
    '''
    Returns traceback string. Format each frame in the traceback as a string.

    Returns:
        str: traceback string
    '''
    trace_back = traceback.extract_stack()
    return "".join(traceback.format_list(trace_back)[:-1])


def print_traceback_easy(start=26):
    '''
    Utility funciton to print traceback for debug.
    Will report in series the string version of the frames that we are currently in.

    Args:
        start (int): Starting position of the traceback frame.
                     Default: 26. Assumes runs from Jupyter notebooks.
                     In general set to zero.
    '''
    print(f"\n")
    print('\n'.join(map(repr, traceback.extract_stack()[start:])))
    print('\n')


def log_error_easy(logger: logging.Logger, pre_text='', post_text='', do_print=False):
    """
    Print

    Arguments:
        logger (logging.Logger): the logger
        pre_text (str): initial text to write (Default: '')
        post_text (str): end text to write (Default: '')
        do_print (bool): True to do the printing, False otherwise (Default: False)
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
    text = f'{pre_text}\n\n'+'\n'.join(error)+f'\n{post_text}'

    logger.error(text)
    if do_print:
        print(text)

#####################################################################################


def monkey_patch(self, func, func_name=None):
    '''
    Monkey patch a method into a class at runtime

    Use descriptor protocol when adding method as an attribute.

    For a method on a class, when you do a.some_method, python actually does:
         a.some_method.__get__(a, type(a))

    so we're just reproducing that call sequence here explicitly.

    See: https://stackoverflow.com/questions/38485123/monkey-patching-bound-methods-in-python

    Args:
        func (function): function
        func_name (str): name of the function (Default: None)
    '''
    func_name = func_name or func.__name__
    setattr(self, func_name, func.__get__(self, self.__class__))
    # what happens if we reload the class or swap in real time?


####################################################################################
# Used to detect and denote potential short segments, when fillet is used.

def compress_list(individual_seg: list) -> list:
    """Given a list of segments that should not be fillet'd,
    search for adjacent segments and make them one compressed list.

    Args:
        individual_seg (list): List of tuples of two ints.  Each int refers to an index of a LineString.

    Returns:
        list: A compresses list of individual_segs.  So, it combines adjacent segments into a longer one.
    """
    reduced_idx = list()
    len_compressed = len(individual_seg)
    if len_compressed > 0:
        last_unique_seg = (-1, -1)  # set to a non-logical tuple

        for index, item in enumerate(individual_seg):
            if index == 0:
                last_unique_seg = item
            else:
                if min(item) == max(last_unique_seg):
                    last_unique_seg = (min(last_unique_seg), max(item))
                else:
                    reduced_idx.append(last_unique_seg)
                    last_unique_seg = item
            if index == len_compressed-1:
                reduced_idx.append(last_unique_seg)
        return reduced_idx

    else:
        return reduced_idx


def are_there_potential_fillet_errors(coords: list, a_fillet: float, fillet_scalar: float, fillet_comparison_precision: int) -> list:
    """Iterate throught the vertex and check using critea.
    1. If a start or end segment, is the length smaller than a_fillet.
    2. If segment in side of LineString, is the lenght smaller than,fillet_scalar times a_fillet.

    Note, there is a rounding error issues. So when the lenght of the segment is calculated,
    it is rounded by using fillet_comparison_precision.

    Args:
        coords (list): List of tuples in (x,y) format. Each tuple represents a vertex on a LineSegment.

        fillet_scalar (float): When determining the critera to fillet, scale the fillet value by fillet_scalar.

        a_fillet (float): The radius to fillet a vertex.

        fillet_comparison_precision (int): There are rounding issues when comparing to (fillet * scalar).
        Use this when calculating length of line-segment.

    Returns:
        list: List of tuples.  Each tuple corresponds to a range of segments that are too short and would not fillet well.
        The tuple is (start_index, end_index).  The index corresponds to index in coords.
    """
    range_vertex_of_bad = list()
    len_coords = len(coords)
    if len_coords <= 1:
        return range_vertex_of_bad

    scaled_fillet = a_fillet * fillet_scalar

    for index, xy in enumerate(coords):
        # Skip the first vertex.
        if index > 0:
            xy_previous = coords[index-1]

            seg_length = np.round(
                distance.euclidean(xy_previous, xy), fillet_comparison_precision)

            # If at first or last segment, use just the fillet value to check, otherwise, use fillet_scalar.
            # Need to not fillet index-1 to index line segment.
            if index == 1 or index == len_coords-1:
                if seg_length < a_fillet:
                    range_vertex_of_bad.append((index-1, index))
            else:
                if seg_length < scaled_fillet:
                    range_vertex_of_bad.append((index-1, index))

    return compress_list(range_vertex_of_bad)

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
    """ Check to see if path exists and file can be written.

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
