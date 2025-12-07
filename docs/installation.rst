.. _installation:

************
Installation
************

~~~~~~~~~~~~~~~~~~~~~~~
Outline of Installation
~~~~~~~~~~~~~~~~~~~~~~~

* **Basic Installation**: Legacy PyPI package (pre-0.5) only.
* **Advanced Installation**: Current v0.5 code from source.
  - **Fast path: uv** (recommended during the v0.5 Quantum Metal transition)
  - **Conda environment setup** (best for binary-heavy stacks and Windows)
  - **Without conda** (standard Python virtual environment)
* **Other**
    * **Optional Jupyter Lab**: Steps to integrate the environment with Jupyter Lab.
    * **Installation hints**: Tips and troubleshooting for setting up the environment.
    * **Common Issues**: FAQ and solutions to common problems.

~~~~~~~~~~~~~~~~~~
Basic Installation
~~~~~~~~~~~~~~~~~~
During the v0.5 transition to **Quantum Metal**, the PyPI package ``qiskit-metal`` remains available only in its pre-0.5 archived state. To get the current v0.5 code, use the advanced (from-source) methods below.

If you specifically need the legacy PyPI build:

::

    pip install qiskit-metal

For the active Quantum Metal v0.5 codebase, clone the repository and follow the advanced installation paths.
We will have a pip installable package for quantum-metal in a future release.

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

-----------------------------------------------
Fast path: uv (recommended during v0.5 transition)
-----------------------------------------------
**Why:** Fast, modern resolver/installer; avoids many scientific-stack issues. Works well across macOS/Linux/Windows. Stick to Python 3.10 or 3.11.

::

    # Install uv (see https://docs.astral.sh/uv/)
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Clone the repo (v0.5 is source-only for now)
    git clone https://github.com/qiskit-community/qiskit-metal.git quantum-metal
    cd quantum-metal

    uv python pin 3.11          # or 3.10
    uv venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate

    uv pip install -r requirements.txt
    uv pip install -e .

Use this path if you want the quickest setup and reproducibility with minimal dependency friction.
Optionally, you can add the development requirements, which include jupyter, testing, linting, formatting, and doc tools:

::

    uv pip install -r requirements-dev.txt

--------------------------------------------------
Conda environment setup (formerly preferred setup)
--------------------------------------------------
**Why:** Most robust for binary-heavy scientific dependencies; recommended on Windows.

If you did not yet install conda, please follow these `instructions <https://docs.conda.io/projects/conda/en/latest/user-guide/install/>`_.

We will setup a conda environment to use the local copy of qiskit-metal you created in the previous section. This approach enables you to immediately observe the effect of your code modifications.

For this section you will need to use the command line. If you use github desktop, you can open one from the menu `Repository -> Open In....`

^^^^^^^^^^^^^^^^^^^^^^^^^^^
Option 1: A new environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The most reliable way to set up a qiskit_metal environment is to build one from scratch using the provided conda environment specification file `environment.yml`.

To do so, first navigate to the root folder created by the code clone. For example:

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

The `-e` flag installs qiskit\_metal in `editable mode <https://pip.pypa.io/en/stable/reference/pip_install/#cmdoption-e>`_.

You can add the `-v` flag for verbose on-screen log information.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Option 2: A pre-existing environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If convenient, you can instead try to install directly in an existing conda environment `<env_name_exist>`, if it is relatively up to date.

To do so, execute these commands in the top-level of the repository:

::

    conda env update -n <env_name_exist> -f environment.yml
    conda activate <env_name_exist>
    python -m pip install --no-deps -e .

Notes:

* It is possible that you may run into version conflicts during the above installation, as qiskit-metal requires specific library versions to work correctly on every OS.
* Remember the period (".") at the end of the third command.
* **Important**: Remember to `conda activate <env_name>` if you intend to use qiskit-metal.  See what a `conda environment is <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_

At this point you can already use qiskit-metal through Jupyter Notebook.
However, if you prefer using JupyterLab, you will need to execute a couple of extra steps.

^^^^^^^^^^^^^^^^^^^^^^
(Optional) Jupyter Lab
^^^^^^^^^^^^^^^^^^^^^^

Jupyter can be used with **any** of the installation pathways (uv, conda, or venv).
The key is that you must install the kernel *inside the environment you plan to use*.

Follow the instructions below depending on which environment you created.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you installed using **uv**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Activate the uv-created environment (usually ``.venv``):

::

    source .venv/bin/activate
    # Windows:
    .venv\Scripts\activate

Install Jupyter and register a kernel:

::

    uv pip install jupyterlab ipykernel
    python -m ipykernel install --user --name quantum-metal-uv --display-name "Quantum Metal (uv)"

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you installed using **conda**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Activate the conda environment:

::

    conda activate <env_name>

Install Jupyter and add a kernel:

::

    conda install jupyterlab ipykernel
    python -m ipykernel install --user --name quantum-metal-conda --display-name "Quantum Metal (conda)"

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you installed using **venv**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Activate your virtual environment:

::

    source <virtual_env_path>/bin/activate
    # Windows:
    <virtual_env_path>\Scripts\activate

Install Jupyter and register the kernel:

::

    pip install jupyterlab ipykernel
    python -m ipykernel install --user --name quantum-metal-venv --display-name "Quantum Metal (venv)"

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Using the kernel in JupyterLab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Launch JupyterLab from *inside the active environment*:

::

    jupyter lab

Then, inside JupyterLab:

* Go to **Kernel → Change Kernel**
* Select the corresponding kernel:
  *Quantum Metal (uv)*, *Quantum Metal (conda)*, or *Quantum Metal (venv)*

This ensures your notebooks run with the correct version of Quantum Metal and its dependencies.




------------------------------------------------------------
Without conda: Virtual environment setup (alternative setup)
------------------------------------------------------------
**Why:** Lightweight and familiar; use if you prefer the standard venv workflow and do not need conda’s binary packages.

**On Windows, do this first:** It is recommended that you first install `Visual C++ x.0`, required for a successful install of `gdstk`.
If you do not have `Visual C++ x.0` installed, you will be notified to install it when `gdstk` attempts to install.
You can do this by downloading and installing `C++ Build Tools <https://visualstudio.microsoft.com/visual-cpp-build-tools/>`_.
Be sure to select the latest versions of `MSVC` and `Windows SDK` in the installer as suggested in `this wiki <https://wiki.python.org/moin/WindowsCompilers>`_.

To use a Python virtual environment, execute these commands in the top-level of the repository:

::

    python -m venv <virtual_env_path>
    source <virtual_env_path>/bin/activate
    python -m pip install -U pip
    python -m pip install -r requirements.txt -r requirements-dev.txt -e .

On Windows, replace `source <virtual_env_path>/bin/activate` with `.<virtual_env_path>\Scripts\activate`.

------------------
Installation hints
------------------

Here are some things to consider when setting up a development environment:

* If using a virtual environment, make sure `pip` is up to date. In initial environment testing, PySide2 is installable with only the latest version of `pip`.

* Add the path of your qiskit-metal folder to your PATH.

* Library errors when activating conda environments or initializing Jupyter Notebook/Lab indicate a conflict between Python libraries in the base and sub-environments. Go ahead and manually delete the library from the base environment `site-packages` folder shown in the error message. You might need to reinstall them in the sub-environment or create a new one.

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
