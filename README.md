﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿[![Build Status](https://travis.ibm.com/IBM-Q-Restricted-Research/qiskit-metal.svg?token=p3Ak3Pz4fK3rsU99vhd2&branch=v0.2-dev)](https://travis.ibm.com/IBM-Q-Restricted-Research/qiskit-metal)

# Qiskit Metal [![](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/zlatko-minev/pyEPR) [![](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/zlatko-minev/pyEPR)
>  Quantum Creator: VLSI and Sims 

## Installation

To setup a development environment, first `git clone` this repository.

* On your computer, clone the repository from qiskit-metal/v0.2-dev:
`git clone git@github.ibm.com:IBM-Q-Restricted-Research/qiskit-metal.git --branch v0.2-dev`

* Note: If you don't have git installed, you can download and use [GitHub Desktop GUI](https://desktop.github.com/) and see these [notes](https://help.github.com/en/desktop/contributing-to-projects/cloning-a-repository-from-github-to-github-desktop).

Then Qiskit Metal can either be installed using a [conda environment](https://docs.conda.io/en/latest/miniconda.html) or a Python virtual environment, as described below. We recommend conda. 

Notes:

* For your own sanity, it is recommended to read this document in its entirety before proceeding.
* On Windows, the conda environment is strongly recommended because Shapely is difficult to install directly via pip.

### Conda environment setup (preferred setup)

To use a conda environment, assuming [you have conda installed](https://docs.conda.io/projects/conda/en/latest/user-guide/install/), we will install the qiskit_metal package locally. 

##### Option 1: A new environment

The most reliable way to set up a qiskit_metal environment is to build one from scratch using the provided conda environment specification file `environment.yml`.
To do so, execute these commands in the top-level of the repository:

```
conda env create -n <env_name> environment.yml
conda activate <env_name>
python -m pip install -e .
```

This will first create a new environment with name `<env_name>`, which you can choose to name `metal` for example.
Then we activate the new environment.
Finally, we install the local package inside that environment.
The -e flag install qiskit\_metal in [editable mode](https://pip.pypa.io/en/stable/reference/pip_install/#cmdoption-e).

##### Option 2: Install into an existing environment

For convenience, you can try to install directly in an existing environment such as the `base` environment, if it is relatively up to date.
To install qiskit_metal and its depenencies into an existing environment named `<env_name>`, execute these commands in the top-level of the repository:

```
conda env update -n <env_name> environment.yml
conda activate <env_name>
python -m pip install -e .
```

##### Notes on using conda

It is possible that you may run into version issues in the above if previously installed packages conflict with the requirements of qiskit_metal.

**Important**: Every time you intend to develop code using this environment, you MUST first run the command: `conda activate <env_name>`.  See what a [conda environment is](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)

To use the new environment inside jupyter lab you will need to follow these additional steps right after the above:

```
conda install ipykernel
ipython kernel install --user --name=<any_name_for_kernel>
```

This will create a kernel based on the environment that is "active" at the moment and you will be able to select that kernel inside jupyter lab.

### Without conda: Virtual environment setup (alternative setup)

**Do this first:** It is recommended that you first install `Visual C++ 14.0`, it is required for a successful install of `gdspy`.  If you do not have `Visual C++ 14.0` installed you will be notified to install it when `gdspy` attempts to install.  You can do this by downloading and installing [C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

To use a Python virtual environment, execute these commands in the top-level of the repository:

```
python -m venv <virtual_env_path>
source <virtual_env_path>/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt -r requirements-dev.txt -e .
```

where `<virtual_env_path>` is where you want the Python virtual environment to be installed.
On Windows, replace `source <virtual_env_path>/bin/activate` with `.\<virtual_env_path>\Scripts\activate`.


### Additional steps for developers
If you are planning to develop the qiskmit metal codebase, you'll want to use these instructions to [setup user environment](/docs/NEW_DEVELOPER_SETUP.md)


## Installation hints

Here are some things to consider when setting up a development environment:

* If using a virtual environment, make sure `pip` is up to date. In initial environment testing, PyQt5 was not installable with recent (but not the latest) versions of `pip`.

## Docs and how to use

[Conda User Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)

[Python Setup and Usage](https://docs.python.org/3/using/)

[Python Language Reference](https://docs.python.org/3/reference/index.html)

[Python How-To's](https://docs.python.org/3/howto/index.html)

[Python Tutorials](https://docs.python.org/3/tutorial/index.html)

[Python Style Guide](https://www.python.org/dev/peps/pep-0008/)

[Metal Docs](/docs)

[Docstring cheat sheet](/docs/docstring_cheat_sheet.md)


## Authors and Citation

Qiskit Metal is the work of [many people](https://github.ibm.com/IBM-Q-Restricted-Research/qiskit-metal/pulse/monthly) who contribute to the project at different levels. Metal was conceived and developed by Zlatko Minev at IBM, then co-led with Thomas McConkey. If you use Qiskit, please cite as per the included [BibTeX file](https://github.com/Qiskit/qiskit/blob/master/Qiskit.bib).For icon attributions, see [here](/qiskit_metal/_gui/_imgs/icon_attributions.txt).


## License

[Apache License 2.0](LICENSE.txt)






















