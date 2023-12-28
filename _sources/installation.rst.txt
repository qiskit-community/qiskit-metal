.. _installation:

************
Installation
************

~~~~~~~~~~~~~~~~~~
Basic Installation
~~~~~~~~~~~~~~~~~~
Please refer to the `PyPI deploy instructions <https://pypi.org/project/qiskit-metal/>`_

~~~~~~~~~~~~~~~~~~~~~
Advanced Installation
~~~~~~~~~~~~~~~~~~~~~

==================
Video Instructions
==================

.. raw:: html

    <a href="https://www.youtube.com/watch?v=sYVDtnJb-ZM&ab_channel=Qiskit">
    Click for YouTube Video</a><br><br>
    <table>
        <tr><td width="22%">
        <a href="https://www.youtube.com/watch?v=sYVDtnJb-ZM&ab_channel=Qiskit">
	        <img src="https://www.gstatic.com/youtube/img/branding/youtubelogo/svg/youtubelogo.svg" width="100">
        </a>
        </td><td width="78%"></td></tr>
    </table>

=================
Text Instructions
=================
We recommend setting up a proper git linkage, which will simplify the retrieval of code updates and the possible contributions back to the source code.

To do that, you will need to `git clone` this repository's main branch following one of two ways.

1. Open any command line shell that has been configured with git and execute the following command:

::

    git clone https://github.com/Qiskit/qiskit-metal.git


2. Alternatively, you can download and use the user interface `GitHub Desktop GUI <https://desktop.github.com/>`_ and refer to these `notes <https://help.github.com/en/desktop/contributing-to-projects/cloning-a-repository-from-github-to-github-desktop>`_.

Now that you have a local copy of the code, you can install Qiskit Metal either in a virtual `conda environment <https://docs.conda.io/en/latest/miniconda.html>`_ or in a virtual Python environment, as described below. We recommend conda.

Notes:

* For your own sanity, it is recommended to read this document in its entirety before proceeding.
* On Windows, the conda environment is strongly recommended because Shapely is difficult to install directly via pip.

-----------------------------------------
Conda environment setup (preferred setup)
-----------------------------------------

If you did not yet install conda, please follow these `instructions <https://docs.conda.io/projects/conda/en/latest/user-guide/install/>`_.

We will setup a conda environment to use the local copy of qiskit-metal you created in the previous section. This approach enables you to immediately observe the effect of your code modifications.

For this section you will need to use the command line. If you use github desktop, you can open one from the menu `Repository -> Open In....`

^^^^^^^^^^^^^^^^^^^^^^^^^^^
Option 1: A new environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The most reliable way to set up a qiskit_metal environment is to build one from scratch using the provided conda environment specification file `environment.yml`.

To do so, first navigate to the folder created by the clone. For example:

::

    cd qiskit-metal

Once you are in the folder that contains the `environment.yml` file, execute the following installation commands:

::

    conda env create -n <env_name> -f environment.yml
    conda activate <env_name>
    python -m pip install --no-deps -e .

This creates a new environment with name `<env_name>` with all the necessary library dependencies.
Then it activates the new environment.
Finally installs the local qiskit-metal code inside that environment.

The `-e` flag install qiskit\_metal in `editable mode <https://pip.pypa.io/en/stable/reference/pip_install/#cmdoption-e>`_.

You can add the `-v` flag for verbose on-screen log information.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Option 2: A pre-existing environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If convenient, you can instead try to install directly in an existing conda environment `<env_name_exist>`, if it is relatively up to date.

To do so, execute these commands in the top-level of the repository:

::

    conda env update -n <env_name_exist> environment.yml
    conda activate <env_name_exist>
    python -m pip install --no-deps -e .

Notes:

* It is possible that you may run into version conflicts during the above installation, as qiskit-metal requires specific library versions to work correctly on every OS.
* Remember the period (".") at the end of the third command.
* **Important**: Remember to `conda activate <env_name>` if you intend to use qiskit-metal.  See what a `conda environment is <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_

At this point you can already use qiskit-metal through jupyter notebook.
However, if you prefer using jupyter lab, you will need to execute a couple of extra steps.

^^^^^^^^^^^^^^^^^^^^^^
(Optional) Jupyter lab
^^^^^^^^^^^^^^^^^^^^^^
Launching jupyter lab will execute python code in the conda `base` environment by default.

To change environment to the Qiskit Metal one you just finished setting up, denoted by `<env_name>`, which we usually just call `metal`, you will need first to add to jupyter lab's list of available kernels. 

From the command line, run the following lines (inside an active <env_name> environment):

::

    conda activate <env_name>
    conda install ipykernel
    ipython kernel install --user --name=<any_name_for_kernel>

Using the above command, you will now have the current conda environment in any Jupyter notebook.

Once inside `jupyter lab`, you can switch to the newly created Metal kernel to use qiskit-metal. Use the Menu `Kernel>Change Kernel`.

-------------------------------------------
Subsequent updates of the conda environment
-------------------------------------------

Package dependencies will evolve over time and could at some point require a new version of a library.
For example, we can anticipate updating `pyEPR-quantum` to enable Ansys interactions previously unsupported.
To update your local install, simply execute the metal package install command

::

    python -m pip install -ve .

Alternatively, you can remove your conda environment by executing the commands below and later re-create a new environment following the original install instructions in section 1.

::

    conda env list
    conda env remove -n <env_name_exist>

We discourage using conda commands to update packages after the install of Qiskit Metal.
Indeed, since Qiskit Metal is installed using pip, the subsequent use of conda commands can introduce inconsistencies that could render your environment unusable.

------------------------------------------------------------
Without conda: Virtual environment setup (alternative setup)
------------------------------------------------------------

**On Windows, do this first:** It is recommended that you first install `Visual C++ 14.0`, it is required for a successful install of `gdspy`.
If you do not have `Visual C++ 14.0` installed you will be notified to install it when `gdspy` attempts to install.
You can do this by downloading and installing `C++ Build Tools <https://visualstudio.microsoft.com/visual-cpp-build-tools/>`_.
Be sure to select the latest versions of `MSVCv142 - VS 2019 C++ x64/x86 build tools` and `Windows 10 SDK` in the installer as suggested in `this wiki <https://wiki.python.org/moin/WindowsCompilers>`_ referenced by the gdspy documentation.

To use a Python virtual environment, execute these commands in the top-level of the repository:
::

    python -m venv <virtual_env_path>
    source <virtual_env_path>/bin/activate
    python -m pip install -U pip
    python -m pip install -r requirements.txt -r requirements-dev.txt -e .


where `<virtual_env_path>` is where you want the Python virtual environment to be installed.
On Windows, replace `source <virtual_env_path>/bin/activate` with `.\<virtual_env_path>\Scripts\activate`.

------------------
Installation hints
------------------

Here are some things to consider when setting up a development environment:

* If using a virtual environment, make sure `pip` is up to date. In initial environment testing, PySide2 is installable with only the latest version of `pip`.

* Add the path of your qiskit-metal folder to your PATH

* Library errors when activating conda environments, or initializing jupyter notebook/lab, indicate a conflict between python libraries in the base and sub environments. Go ahead and manually delete the library from the base environment `site-packages` folder, shows in the error message. You might need to reinstall them in the sub environment, or create a new one.

--------------------------
Setting up precommit hooks
--------------------------

If are planning on committing, you can run the following in the root of your project to link the available precommit hooks.
::

    ./hook_setup

Please make sure the command is run from the same shell you plan on using to commit. If running on Windows, please make sure that this script is run from git-bash or another Linux-style shell. Currently, the precommit hook will check for yapf formatting.

=============
Common Issues
=============

If you run into problems, consult the FAQ's page :ref:`here <faq_setup>`.
