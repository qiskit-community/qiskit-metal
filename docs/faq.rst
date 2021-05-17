.. _faq:

********************************
FAQ's
********************************

Frequently asked questions.


.. _faq_setup:

----------------------
Setting up environment
----------------------


**Q: Why do I have an inactive developer path on MacOs?**

**A:** If you are seeing: ``xcrun: error: invalid active developer path (/Library/Developer/CommandLineTools), missing xcrun at /Library/Developer/CommandLineTools/usr/bin/xcrun`` you may be missing the Command Line Tools.

The Command Line Tools package for XCode should be already installed.
If not, they can be installed with: ``xcode-select —install``


**Q: Why can't qutip find my path?**

**A:** ``qutip`` may have issues finding your path if using VSCode, resulting in a ``KeyError: 'physicalcpu'``. If the error occurs, please add your PATH to VSCode's settings as follows.

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

Copy the resulting output. Example: ``"PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"``
Then open the applicable settings.json in your VS Code. (See how to open command palette `here <https://code.visualstudio.com/docs/getstarted/tips-and-tricks>`_). Search "settings" and click Open Workspace Settings (JSON)). Paste:

.. code-block:: RST

   "terminal.integrated.env.osx": {
      "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
      }

**Q: Why is the pip installation asking for a path to gdal-config?**

**A:** If you are seeing: *A GDAL API version must be specified. Provide a path to gdal-config using a GDAL_CONFIG environment variable or use a GDAL_VERSION environment variable.* you are probably trying to install qiskit-metal on a brand new environment.
This is the result of a known limitation of the PyPI windows packages ``gdal`` and ``fiona``.

*conda:*

Conda has valid ``gdal`` and ``fiona`` packages. Simply run ``conda install fiona`` before trying again to install qiskit-metal.

*python venv:*

You will need to download and install the binary wheels from `here <https://www.lfd.uci.edu/~gohlke/pythonlibs/>_`.
After downloading the wheels, install ``gdal`` first, then ``fiona``, then again ``qiskit-metal``. Replace the wheel names in the example below with the names of the files you downloaded:

.. code-block:: RST

   python -m pip install .\GDAL-3.2.3-cp38-cp38-win_amd64.whl
   python -m pip install .\Fiona-1.8.19-cp38-cp38-win_amd64.whl
   python -m pip install -e .   (replace this line with the one you executed before the error)

**Q: Why is my installation complaining about missing ``geos_c.dll``?**

**A:** Based on: `this <https://github.com/Toblerity/Shapely/pull/1108>`_, this is a known bug with the ``shapely`` package <1.8. that should be fixed with a more recent shapely package. Meanwhile, you can use the shapely package from conda by installing it as ``conda install shapely`` before installing ``qiskit-metal``, which installs the missing file as a dependency.

**Q: Why is "xcb" found but not loaded?**

**A:** it has been observed for pip installation on fresh conda environments that this error might show up: ``Could not load the Qt platform plugin "xcb" in "" even though it was found.``

Based on `this source <https://forum.qt.io/topic/93247/qt-qpa-plugin-could-not-load-the-qt-platform-plugin-xcb-in-even-though-it-was-found>`_ You might be able to resolve this error by installing the dependency with ``sudo apt-get install libxcb-xinerama0``
An alternative might be to install an older version of python (and related dependencies)

**Q: Why am I not able to start Jupyter Lab in the new environment?**

**A:** Based on: `this <https://anaconda.org/conda-forge/jupyterlab>`_, install Jupyter lab by

``conda install -c conda-forge jupyterlab``

Then re-install the qiskit-metal package with pip, for example, if you are using the github local installation flow run the following:

``python -m pip install --no-deps -e .``



.. _gui:

-------------------------------------
Getting started with GUI developement
-------------------------------------

**Q: Is there a PySide2 tutorial?**

**A:** Yes!  `This article from realpython.com <https://realpython.com/python-pyqt-gui-calculator>`_ contains a nice tutorial to help you get started!


**Q: Are there any pitfalls I may run into?**

**A:** Like anything else, yes.  `This article from enki-editor.org <http://enki-editor.org/2014/08/23/Pyqt_mem_mgmt.html>`_ describes some common pitfalls.


**Q: Is there a video tutorial for starting QT Designer?**

**A:** Yes there is, check it out `on youtube here <https://www.youtube.com/watch?v=XXPNpdaK9WA>`_.


**Q: I'm having trouble with slots and signals.  Can you help?**

**A:** Sure.  There are a few decent overviews.  A good place to start are these two:

   * `An Introduction to PyQt5 Signals, Slots and Events <https://www.learnpyqt.com/tutorials/signals-slots-events/>`_
   * `Qt for Python Signals and Slots <https://wiki.qt.io/Qt_for_Python_Signals_and_Slots>`_


.. _docs:

-------------
Documentation
-------------

**Q: I am seeing a lot of warnings when I build the docs.  How do I resolve them?**

**A:** There is no need to build the docs locally unless you *really* want to.  The docs can be accessed without building them yourself by navigating to `<https://qiskit.org/documentation/metal/>`_.

If you chose to build the docs yourself, some users may see a list of warnings when building the docs.  Warnings about matplotlib text role can be safely ignored.

You can resolve other warnings by deleting the following directories and rebuilding:

   * ``docs/_build``
   * ``docs/build``
   * ``docs/stubs``

--------------------------------
Connecting to 3rd party software
--------------------------------

**Q: I'm having trouble connecting to Ansys after running connect_ansys().**

**A:** First check to see if a project and design are already open and active in Ansys.

Activate an Ansys design by double clicking on it in the Project Manager panel.

If the error persists, there may be one or more hidden Ansys windows in the background. Close them via the task manager and try again.
