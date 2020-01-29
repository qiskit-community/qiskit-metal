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

"""
Created on Tue May 14 17:13:40 2019

@author: Zlatko
"""

def monkey_patch(self, func):
    '''
    Debug function
    '''
    setattr(self, func.__name__, func.__get__(self, self.__class__))



from IPython.display import display, Markdown
display_md = lambda text: display(Markdown(text))

def available_libraries():
    """ Helper functions to report nicely - skip over this block
    """
    import qiskit_metal
    dir_public = lambda obj: [name for name in dir(obj) if not name.startswith('_')]

    # Print available object categories
    display_md("**Available object libraries in default library `qiskit_metal.objects`:**")
    display(dir_public(qiskit_metal.objects))

def library_objects(module):
    text = f"**The library `{module.__name__}`has objects:**"
    for name in dir(module):
        if not name.startswith('_'):
            text += f"\n - {name}"
    display_md(text)