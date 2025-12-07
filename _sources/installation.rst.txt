.. _installation:

************
Installation
************

~~~~~~~~~~~~~~~~~~~~~~~
Outline of Installation
~~~~~~~~~~~~~~~~~~~~~~~



.. grid:: 1 1 2 3
   :gutter: 2
   :margin: 1 0 2 0

   .. grid-item-card::
      :class-card: sd-bg-light sd-border
      :class-header: sd-bg-secondary sd-text-white
      :text-align: left

      **Basic Installation**

      Legacy PyPI package (pre-0.5 only).

      - ``pip install qiskit-metal``
      - Useful when you need compatibility with older notebooks/tutorials

   .. grid-item-card::
      :class-card: sd-bg-light sd-border
      :class-header: sd-bg-primary sd-text-white
      :text-align: left

      **Advanced Installation (v0.5)**

      Install the active Quantum Metal source tree.

      **Options:**
      - **Fast path: uv** (recommended during the v0.5 transition)
      - **Conda environment setup** (best for Windows / binary-heavy stacks)
      - **Without conda** (standard Python ``venv``)

   .. grid-item-card::
      :class-card: sd-bg-light sd-border
      :class-header: sd-bg-success sd-text-white
      :text-align: left

      **Other Setup Topics**

      - Optional Jupyter Lab integration
      - Installation hints and tips
      - Common Issues / FAQ


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

Clone the repository (command line):

::

    git clone https://github.com/Qiskit/qiskit-metal.git

Or use the `GitHub Desktop GUI <https://desktop.github.com/>`_ (`cloning notes <https://help.github.com/en/desktop/contributing-to-projects/cloning-a-repository-from-github-to-github-desktop>`_).

Notes:

* On Windows, conda is recommended because binary wheels (e.g., Shapely/gdstk) are easier.
* Read this document before starting; it will save you time.

------------------------
Choose an install method
------------------------

.. tab-set::

   .. tab-item:: uv (recommended)

      **Why:** Fast, modern resolver/installer; typically the least friction for scientific stacks. Use Python 3.10 or 3.11.

      .. code-block:: sh

         # Install uv (see https://docs.astral.sh/uv/)
         curl -LsSf https://astral.sh/uv/install.sh | sh

         # Clone the repo (v0.5 is source-only for now)
         git clone https://github.com/qiskit-community/qiskit-metal.git quantum-metal
         cd quantum-metal

         uv python pin 3.11          # or 3.10
         uv venv
         source .venv/bin/activate   # Windows: .venv\\Scripts\\activate

         uv pip install -r requirements.txt
         uv pip install -e .

         # Optional: dev extras (docs, tests, lint, formatting)
         uv pip install -r requirements-dev.txt

   .. tab-item:: Conda (robust, esp. Windows)

      **Why:** Best for binary-heavy dependencies and Windows toolchains.

      .. code-block:: sh

         # Create a fresh env from environment.yml
         conda env create -n <env_name> -f environment.yml
         conda activate <env_name>
         python -m pip install --no-deps -e .

         # Or update an existing env
         conda env update -n <env_name_exist> -f environment.yml
         conda activate <env_name_exist>
         python -m pip install --no-deps -e .

      Tips:
      - Keep the trailing ``.`` in the editable install command.
      - If conflicts arise, try a new env.

   .. tab-item:: Python venv (lightweight)

      **Why:** Simple and familiar if you do not need conda’s binary packages.

      .. code-block:: sh

         python -m venv <virtual_env_path>
         source <virtual_env_path>/bin/activate     # Windows: <virtual_env_path>\\Scripts\\activate
         python -m pip install -U pip
         python -m pip install -r requirements.txt -r requirements-dev.txt -e .

      Windows note: install the latest MSVC/Windows SDK (Visual C++ Build Tools) to satisfy gdstk.

^^^^^^^^^^^^^^^^^^^^^^
(Optional) Jupyter Lab
^^^^^^^^^^^^^^^^^^^^^^

Jupyter works with **any** pathway. Install the kernel from inside the environment you plan to use.

.. tab-set::

   .. tab-item:: uv / venv

      .. code-block:: sh

         source .venv/bin/activate      # adjust to your venv; Windows: .venv\\Scripts\\activate
         python -m pip install jupyterlab ipykernel
         python -m ipykernel install --user --name quantum-metal-uv --display-name "Quantum Metal (uv)"

   .. tab-item:: conda

      .. code-block:: sh

         conda activate <env_name>
         conda install jupyterlab ipykernel
         python -m ipykernel install --user --name quantum-metal-conda --display-name "Quantum Metal (conda)"

Launch JupyterLab from the active environment:

::

    jupyter lab

Then pick the matching kernel via **Kernel → Change Kernel**.




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
