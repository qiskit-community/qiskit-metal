"""
Utility display functions used in the tutorials.
@author: Zlatko K. Minev
@date: 2020
"""

from IPython.display import display, HTML, Image

################################################################

class Headings:
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
        display(HTML(cls.__h1__.replace('!!!!', text)))


### For gui programming
from PyQt5.QtWidgets import QMainWindow, QApplication
from pathlib import Path
def get_screenshot(self:QMainWindow, name='shot.png', type_='png', do_display=True, disp_ops=None):
    """
    Grad a screenshot of the main window,
    save to file, and then copy to clipboard.
    """

    path = Path(name).resolve()

    # just grab the main window
    screenshot = self.grab() # type: QtGui.QPixelMap
    screenshot.save(str(path), type_)  # Save

    QApplication.clipboard().setPixmap(screenshot)  # To clipboard
    #print(f'Screenshot copied to clipboard and saved to:\n {path}')

    if do_display:
        _disp_ops = dict(width=500)
        _disp_ops.update(disp_ops or {})
        display(Image(filename=path, **_disp_ops))


def format_dict_ala_z(dic, indent=0, key_width=20, do_repr=True, indent_all:int=2, indent_keys=5):

    indent_all_full = indent_all + indent*indent_keys

    text = ''
    for k, v in dic.items():
        if isinstance(v, dict):
            if do_repr:
                k = repr(k)
            text += f"{'':{indent_all_full}s}{k:<{key_width}s}:"+ " { \n"
            text += format_dict_ala_z(v, indent+1, key_width=key_width,do_repr=do_repr,indent_all=indent_all)
            text += f"{'':{indent_all_full+key_width}s}" + "  }" +(',' if do_repr else '') +"\n"
        else:
            if do_repr:
                k = repr(k)
                v = repr(v)+','
            text += f"{'':{indent_all_full}s}{k:<{key_width}s}: {str(v):<30s}\n"

    if indent == 0:
        if len(text) > 1:
            text = text[:-1]
    return text