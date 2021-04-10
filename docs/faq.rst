.. _faq:

********************************
FAQ's
********************************

Frequently asked questions.


.. _faq_setup:

----------------------
Setting up environment
----------------------


**Why do I have an inactive developer path on MacOs?**

If you are seeing: *xcrun: error: invalid active developer path (/Library/Developer/CommandLineTools), missing xcrun at /Library/Developer/CommandLineTools/usr/bin/xcrun* you may be missing the Command Line Tools.

The Command Line Tools package for XCode should be already installed.
If not, they can be installed with: `xcode-select —install`


**Why can't qutip find my path?**

`qutip` may have issues finding your path if using VSCode, resulting in a `KeyError: 'physicalcpu'`. If the error occurs, please add your PATH to VSCode's settings as follows.

*Windows:*

Open Windows Command Prompt and type:
 
``$Env:Path``

Copy the resulting output. Example: ``"PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"``
Then open the applicable settings.json in your VS Code. (See how to open command palette here `here <https://code.visualstudio.com/docs/getstarted/tips-and-tricks>`_). Search "settings" and click Open Workspace Settings (JSON)). Paste:

.. code-block:: RST

   "terminal.integrated.env.windows": {
      "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
      }


*MacOs:*

Open Terminal and type:

``echo $PATH``

Copy the resulting output. Example: `"PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"`
Then open the applicable settings.json in your VS Code. (See how to open command palette `here <https://code.visualstudio.com/docs/getstarted/tips-and-tricks>`_). Search "settings" and click Open Workspace Settings (JSON)). Paste:

.. code-block:: RST

   "terminal.integrated.env.osx": {
      "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
      }

**Why am I not able to start Jupyter Lab in the new environment?**

Based on: `this <https://anaconda.org/conda-forge/jupyterlab>`_, install Jupyter lab by

``conda install -c conda-forge jupyterlab``

Then change directory to top level of repository.

``python -m pip install -e .``



.. _gui:

-------------------------------------
Getting started with GUI developement
-------------------------------------

**Is there a PySide2 tutorial?**

Yes!  `This article from realpython.com <https://realpython.com/python-pyqt-gui-calculator>`_ contains a nice tutorial to help you get started!


**Are there any pitfalls I may run into?**

Like anything else, yes.  `This article from enki-editor.org <http://enki-editor.org/2014/08/23/Pyqt_mem_mgmt.html>`_ describes some common pitfalls.


**Is there a video tutorial for starting QT Designer?**

Yes there is, check it out `on youtube here <https://www.youtube.com/watch?v=XXPNpdaK9WA>`_.


**I'm having trouble with slots and signals.  Can you help?**

Sure.  There are a few decent overviews.  A good place to start are these two:

   * `An Introduction to PyQt5 Signals, Slots and Events <https://www.learnpyqt.com/tutorials/signals-slots-events/>`_
   * `Qt for Python Signals and Slots <https://wiki.qt.io/Qt_for_Python_Signals_and_Slots>`_


.. _docs:

-------------
Documentation
-------------

**I am seeing a lot of warnings when I build the docs.  How do I resolve them?**

There is no need to build the docs locally unless you *really* want to.  The docs can be accessed without building them yourself by navigating to `<https://qiskit.org/documentation/metal/>`_.

If you chose to build the docs yourself, some users may see a list of warnings when building the docs.  Warnings about matplotlib text role can be safely ignored.

You can resolve other warnings by deleting the following directories and rebuilding:

   * ``docs/_build``
   * ``docs/build``
   * ``docs/stubs``

--------------------------------
Connecting to 3rd party software
--------------------------------

**I'm having trouble connecting to Ansys after running connect_ansys().**

First check to see if a project and design are already open and active in Ansys.

Activate an Ansys design by double clicking on it in the Project Manager panel.

If the error persists, there may be one or more hidden Ansys windows in the background. Close them via the task manager and try again.
