.. _installation:

************
Installation
************

==================================================
Outline of Installation
==================================================



.. grid:: 1 1 2 3
   :gutter: 2
   :margin: 1 0 2 0

   .. grid-item-card::
      :class-card: sd-bg-light sd-border
      :class-header: sd-bg-secondary sd-text-white
      :text-align: left

      **Basic Installation (PyPI)**

      Install the current Quantum Metal release from PyPI.

      - ``pip install quantum-metal``
      - For most users; matches CI-tested wheels

   .. grid-item-card::
      :class-card: sd-bg-light sd-border
      :class-header: sd-bg-primary sd-text-white
      :text-align: left

      **Installation from source (v0.5)**

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
      - Video instructions for legacy package (``qiskit-metal<0.5``)


==================================================
Basic Installation
==================================================
Quantum Metal v0.5+ is available on PyPI (Project page: https://pypi.org/project/quantum-metal/).


.. tab-set::
   .. tab-item:: pip install


      **Note:** If using this method, it is recommended to install inside a virtual environment. 

      .. code-block:: sh

         pip install quantum-metal

   .. tab-item:: Add to a uv workspace (recommended)

      .. code-block:: sh

         uv add quantum-metal

   .. tab-item:: Add to a Pixi workspace

      **Note:** This method might fail if your Pixi workspace has dependencies that are not compatible with the Quantum Metal dependencies. In such cases, the error messages might not make it obvious.

      .. code-block:: sh

         pixi add --pypi quantum-metal





If you specifically need the legacy pre-0.5 package, install ``qiskit-metal`` instead. Otherwise, use ``quantum-metal`` to get the current release.

.. For source installs or development, clone the repository and follow the advanced installation paths below.  

==================================================
Installation from source
==================================================

We recommend setting up a proper git linkage, which will simplify the retrieval of code updates and the possible contributions back to the source code. If you intend to contribute to the project, please also read the :ref:`contributor guide <contributor_guide>`.

Clone the repository (command line):

.. code-block:: sh

    git clone https://github.com/qiskit-community/qiskit-metal.git quantum-metal
    cd quantum-metal # Change to the repository directory

Or use the `GitHub Desktop GUI <https://desktop.github.com/>`_ (`cloning notes <https://help.github.com/en/desktop/contributing-to-projects/cloning-a-repository-from-github-to-github-desktop>`_).

Notes:

* On Windows, conda is recommended because binary wheels (e.g., Shapely/gdstk) are easier.
* Read this document before starting; it will save you time.

------------------------
Choose an install method
------------------------

Run the following commands in the root of the repository (i.e. the ``quantum-metal`` directory):

.. tab-set::

   .. tab-item:: uv (recommended)

      **Why:** Fast, modern resolver/installer; typically the least friction for scientific stacks. Use Python 3.10, 3.11, or 3.12. ``uv`` installations instruction are available `here <https://docs.astral.sh/uv/getting-started/installation/>`_.

      .. code-block:: sh

         # Create a new virtual environment
         uv venv --python 3.11  # could also be 3.10 or 3.12

         # Install the package in editable mode
         uv pip install -e .

         # Activate the virtual environment
         source .venv/bin/activate   # Windows: .venv\\Scripts\\activate

         # or run the python shell in the virtual environment
         uv run python

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

         # Activate the virtual environment
         source <virtual_env_path>/bin/activate     # Windows: <virtual_env_path>\\Scripts\\activate

         # Install the package
         python -m pip install -U pip
         python -m pip install -e .

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
Below we provide a detailed explanation of how to set up a virtual environment without conda, using Python venv instead. 

**Why:** Lightweight and familiar; use if you prefer the standard venv workflow and do not need conda’s binary packages.

**On Windows, do this first:** It is recommended that you first install ``Visual C++ x.0``, required for a successful install of ``gdstk``.
If you do not have ``Visual C++ x.0`` installed, you will be notified to install it when ``gdstk`` attempts to install.
You can do this by downloading and installing `C++ Build Tools <https://visualstudio.microsoft.com/visual-cpp-build-tools/>`_.
Be sure to select the latest versions of ``MSVC`` and ``Windows SDK`` in the installer as suggested in `this wiki <https://wiki.python.org/moin/WindowsCompilers>`_.

To use a Python virtual environment, execute these commands in the top-level of the repository:

::

    python -m venv <virtual_env_path>
    source <virtual_env_path>/bin/activate    # Windows: <virtual_env_path>\\Scripts\\activate
    python -m pip install -U pip
    python -m pip install -e .


------------------
Installation hints
------------------

Here are some things to consider when setting up a development environment:

* If using a virtual environment, make sure ``pip`` is up to date. 

* Add the path of your qiskit-metal folder to your PATH.

* Library errors when activating conda environments or initializing Jupyter Notebook/Lab indicate a conflict between Python libraries in the base and sub-environments. Go ahead and manually delete the library from the base environment ``site-packages`` folder shown in the error message. You might need to reinstall them in the sub-environment or create a new one.

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

If you run into problems, consult the FAQ's page :ref:`here <faq_setup>`, or open a `GitHub issue <https://github.com/qiskit-community/qiskit-metal/issues>`_.


============================================================
Video Instructions for Legacy package (qiskit-metal<0.5)
============================================================

.. attention::

   The following instructions are for the legacy ``qiskit-metal<0.5`` release. For the latest release and ``quantum-metal`` v0.5+, please follow the text instructions above. An updated video tutorial will be added soon.

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