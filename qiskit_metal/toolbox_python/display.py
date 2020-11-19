# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""
Utility display functions used in the tutorials.

@author: Zlatko K. Minev
@date: 2020
"""

import re
from pathlib import Path
from typing import Dict as Dict_

from IPython import get_ipython
from IPython.core.magic import Magics, line_magic, magics_class
from IPython.display import HTML, Image, display

__all__ = ['get_screenshot', 'format_dict_ala_z']


@magics_class
class MetalTutorialMagics(Magics):
    """A class of status magic functions."""

    @line_magic
    def metal_print(self, line='', cell=None):  # pylint: disable=unused-argument
        """
        Print an HTML formatted message.
        """
        return display(
            HTML(f"""
    <div style="
        padding-top:10px;
        padding-bottom:10px;
        font-weight: bold;
        font-size: large;
        text-align: center;
        color: white;
        background: #12c2e9;  /* fallback for old browsers */
        background: -webkit-linear-gradient(to right, #f64f59, #c471ed, #12c2e9);  /* Chrome 10-25, Safari 5.1-6 */
        background: linear-gradient(to right, #f64f59, #c471ed, #12c2e9); /* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */
    ">
        {line}
    </div>
        """))

    @line_magic
    def metal_heading(self, line='', cell=None):  # pylint: disable=unused-argument
        """
        Print an HTML formatted message.
        """
        return display(
            HTML(f"""
    <h1 style="
        background: #12c2e9;  /* fallback for old browsers */
        background: -webkit-linear-gradient(to right, #d4418e 0%, #0652c5 74%);  /* Chrome 10-25, Safari 5.1-6 */
        background: linear-gradient(315deg, #d4418e 0%, #0652c5 74%); /* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */
        margin-top: 50px;
        border-style: outset;
        padding-top:100px;
        padding-bottom:50px;
        padding-left:25px;
        color: white;
    "> {line} <h1>
        """))


_IP = get_ipython()
if _IP is not None:
    _IP.register_magics(MetalTutorialMagics)


class Headings:
    """Headings class for printing HTML-styled heading for the tutorials.

    Legcay code. Use cell magics. See: ``MetalTutorialMagics``.
    """
    __h1__ = """
    <h1 style="
        background-color: #d4418e;
        background-image: linear-gradient(315deg, #d4418e 0%, #0652c5 74%);
        margin-top: 50px;
        border-style: outset;
        padding-top:100px;
        padding-bottom:50px;
        padding-left:25px;
        color: white;
    "> !!!! <h1>
    """.replace('\n', ' ')

    @classmethod
    def h1(cls, text):
        """Display the HTML"""
        display(HTML(cls.__h1__.replace('!!!!', text)))


# TODO: Move to module for GUI programming
def get_screenshot(self: 'QMainWindow',
                   name='shot.png',
                   type_='png',
                   do_display=True,
                   disp_ops=None):
    """
    Grad a screenshot of the main window,
    save to file, and then copy to clipboard.

    Args:
        self (QMainWindow): window to take the screenshot of
        name (str): file to save the screenshot to (Default: 'shot.png')
        type (str): type of file to save (Default: 'png')
        do_display (bool): True to display the file (Default: True)
        disp_ops (dict): disctionary of options (Default: None)
    """
    from PySide2.QtWidgets import QApplication, QMainWindow

    path = Path(name).resolve()

    # just grab the main window
    screenshot = self.grab()  # type: QtGui.QPixelMap
    screenshot.save(str(path), type_)  # Save

    QApplication.clipboard().setPixmap(screenshot)  # To clipboard
    #print(f'Screenshot copied to clipboard and saved to:\n {path}')

    if do_display:
        _disp_ops = dict(width=500)
        _disp_ops.update(disp_ops or {})
        display(Image(filename=str(path), **_disp_ops))


##########################################################################
# Shell print


class Color:
    """
    Shell/terminal color and style definitions for the cursor.

    This will work on *NIX, MacOS, and Windows (provided you enable ansi.sys).
    The class attributes are various ANSI codes for setting the color and style of the cursor.

    The following attributes use octal string representations.
    See https://www.saic.it/bach-color-linux/

    In general, `termcolor` is more stable across platforms. See `termcolor`
    """
    purple = '\033[95m'
    cyan = '\033[96m'
    darkcyan = '\033[36m'
    blue = '\033[94m'
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    bold = '\033[1m'
    BOLD = '\033[1m'
    underline = '\033[4m'
    end = '\033[0m'
    END = '\033[0m'


def style_colon_list(text: str,
                     sty1a='',
                     sty1b='',
                     sty2a=Color.blue,
                     sty2b=Color.END) -> str:
    """
    Color on the left and right sides of single :
    """
    text = re.sub('(.*?):(.*)', f'{sty1a}\g<1>{sty1b}:{sty2a}\g<2>{sty2b}',
                  text)  # *? is non-greedy
    return text


def format_dict_ala_z(dic: Dict_,
                      indent=0,
                      key_width=20,
                      do_repr=True,
                      indent_all: int = 2,
                      indent_keys=5,
                      style_dicts=True):
    """Format a nested dictionary.

    Args:
        dic (dict): Dictionary to format
        indent (int): indentation spaces (Default: 0)
        key_width (int): width of the key (Default: 20)
        do_repr (bool): True to do the cononical string representation (Default: True)
        indent_all (int): indentation for everything (Default: 2)
        indent_keys (int): indentation for the keys (Default: 5)

    Returns:
        str: string repesentation of the dictionary
    """
    indent_all_full = indent_all + indent * indent_keys

    if style_dicts:
        sty1a, sty1b = Color.BOLD, Color.END

    text = ''
    for k, v in dic.items():
        if isinstance(v, dict):
            if do_repr:
                k = repr(k)
            text += f"{'':{indent_all_full}s}{sty1a}{k:<{key_width}s}{sty1b}: {{\n"
            text += format_dict_ala_z(v,
                                      indent + 1,
                                      key_width=key_width,
                                      do_repr=do_repr,
                                      indent_all=indent_all)
            text += f"{'':{indent_all_full+key_width}s}" + \
                "  }" + (',' if do_repr else '') + "\n"
        else:
            if do_repr:
                k = repr(k)
                v = repr(v) + ','
            text += f"{'':{indent_all_full}s}{k:<{key_width}s}: {str(v):<30s}\n"

    if indent == 0:
        if len(text) > 1:
            text = text[:-1]
    return text
