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

import traceback
import warnings
from copy import deepcopy

import pandas as pd

####################################################################################
# Dictionary related


def copy_update(options, *args, deep_copy=True, **kwargs):
    '''
    Utility funciton to merge two dictionaries
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
    my_dict = {'name': 'Klauss', 'age': 26, 'Date of birth': '15th july'}
    dict_start_with(my_dict, 'Date')
    '''
    if as_ == list:
        # start_with in k]
        return [v for k, v in my_dict.items() if k.startswith(start_with)]
    elif as_ == dict:
        return {k: v for k, v in my_dict.items() if k.startswith(start_with)}


def display_options(*ops_names, options=None, find_dot_keys=True, do_display=True):
    '''
    Print html display of options dictionary by default `DEFAULT_OPTIONS`

    Example use:
    ---------------
        display_options('make_transmon_pocket_v1', 'make_transmon_connector_v1')

    or
        dfs, html = display_options(Metal_Transmon_Pocket.__name__, do_display=False)
    '''
    # IDEA: display also ._hfss and ._gds etc. for those that have it and add to plugins
    if options is None:
        from .. import DEFAULT_OPTIONS
        options = DEFAULT_OPTIONS

    res = []
    for keyname in ops_names:
        if find_dot_keys:
            names = list(filter(lambda x, match=keyname: x is match or
                                x.startswith(match+'.'), DEFAULT_OPTIONS.keys()))
            names.sort()
            for name in names:
                res += [pd.Series(options[name], name=name).to_frame()]
        else:
            res += [pd.Series(options[keyname], name=keyname).to_frame()]

    from pyEPR.toolbox import display_dfs
    res_html = display_dfs(*res, do_display=do_display)  #why not just directly call the function DataFrame_display_side_by_side(*args) ?
    return res, res_html

def data_frame_empty_typed(column_types:dict):
    """Creates and empty DataFrame with dtypes for each column given
    by the dicitonary,

    Arguments:
        column_types {dict} -- key, dtype pairs

    Returns:
        DataFrame
    """
    df = pd.DataFrame()
    for name, dtype in column_types.items():
        df[name] = pd.Series(dtype=dtype)
    return df


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
    Returns tracekback string
    '''
    tb = traceback.extract_stack()
    return "".join(traceback.format_list(tb)[:-1])


def print_traceback_easy(start=26):
    '''
    Utility funciton to print traceback for debug
    '''
    print(f"\n")
    print('\n'.join(map(repr, traceback.extract_stack()[start:])))
    print('\n')

import logging, sys
def log_error_easy(logger:logging.Logger, pre_text='', post_text='', do_print=False):
    """
    Print

    Arguments:
        logger {logging.Logger} -- [description]
    Test use:

    .. code-block : python

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

                #exc_type, exc_value, exc_tb = sys.exc_info()
                #error = traceback.format_exception(exc_type, exc_value, exc_tb)
                #logger.error('\n\n'+'\n'.join(error)+'\n')
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


def monkey_patch(self, func):
    '''
    Debug function
    '''
    setattr(self, func.__name__, func.__get__(self, self.__class__))
