# Qiskit Metal For Developers


## Development Setup for version 0.5+

The new version of Qiskit Metal (soon to be Quantum Metal) has transitioned to [uv](https://docs.astral.sh/uv/) for project/dependency management. This guide describes how to set up your local development environment in light of these updates. First, you should install uv on your system, as described by the [instructions here](https://docs.astral.sh/uv/getting-started/installation/).


### Development (virtual) environments

The next few paragraphs describe the setup. We recommend reading through it at least once before you start making contributions. Skip to the next section for instructions on how to activate venvs, run tasks, etc. 

All development activities should be carried out inside Python virtual environments (venvs). Thankfully, uv can manage all our venvs for us. In addition to this, we can use tox to orchestrate venvs to fit the needs of different development tasks: testing, linting, building docs, etc. 

All information about project dependencies can be found in the `pyproject.toml` file located in the root directory of this repository. The direct project dependencies are listed in the `requirements` section of the `[project]` table. These are required to run user code. 

Development dependencies are specified in the `[dependency-groups]` table.There are four groups available: `test`, `lint`, `docs`, and `jupyter`. These are used by tox to create a virtual environment with the required dependencies for each task. At the time of writing, the `jupyter` group is available for convenience, but unused in tasks. 
 See [PEP 735-Dependency Groups in pyproject.toml](https://peps.python.org/pep-0735/) and the [PyPA specification page for dependency groups](https://packaging.python.org/en/latest/specifications/dependency-groups/#dependency-groups) for more information. 

 The file `uv.lock` lists "locked" versions for all dependencies listed in `pyproject.toml` across different platforms. This allows uv to create reproducible environments. At present, tox does not create virtual environments using the lockfile, but the [tox-uv](https://github.com/tox-dev/tox-uv) plugin allows for this functionality to be enabled by setting the `runner` configuration variable in each tox task [as described here](https://github.com/tox-dev/tox-uv?tab=readme-ov-file#uvlock-support).


### Running tests

Tox is configured to run tests (using pytest) for Python 3.10-3.12. Use the following command to run tests for all three versions:

```
tox -m test
```

We use the pytest-rich(https://github.com/nicoddemus/pytest-rich) to provide rich output of testing progress. Tests can be run for specific versions using the following command

```
tox -e py3.12 # replace 3.12 with the version you want to run
```

### Linting and Formatting

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting. Our linting configuration is described in `pyproject.toml` under the `[tool.ruff.lint]` table. Note that this configuration is a work in progress and likely to change until further notice. The linter can be run using the following command:

```
tox -e lint
```

This will show all the linting errors and the location for each. For a summary showing the number of violations of each linting rule, use the following command:

```
tox -e lint -- --statistics
```

Formatting for the whole repository can be performed using the following command:

```
tox -e format
```

Note that we have not yet settled on a formatting configuration other than default options provided by ruff, but this may change. 


### Building docs

Documentation is built using Sphinx. Please refer to the guide presented in the [package documentation](https://qiskit-community.github.io/qiskit-metal/contributor-guide.html#contributing-to-documentation) for an extensive description. Briefly, docs can be built using tox with the following command: 

```
tox -e docs
```


## Old Instructions

**NOTE**: The following instructions are from 2020 and might be used for the `qiskit-metal<0.5`.  

[![Quick install tutorial](https://img.shields.io/badge/youtube-Quick_Install_Video-red.svg?logo=youtube)](https://www.youtube.com/watch?v=sYVDtnJb-ZM&ab_channel=Qiskit)
### Retrieve the code from GitHub

You could download the code as a zip file at the top of this page.
However we recommend investing time into setting up a proper git linkage, which will simplify the retrieval of code updates and your possible contributions back to the source code.

To do that, you will need to `git clone` this repository's main branch following one of two ways.

1. Open any command line shell that has been configured with git and execute the following command:
```sh
git clone https://github.com/Qiskit/qiskit-metal.git
```
2. Alternatively, you can download and use the user interface [GitHub Desktop GUI](https://desktop.github.com/) and refer to these [notes](https://help.github.com/en/desktop/contributing-to-projects/cloning-a-repository-from-github-to-github-desktop).

Now that you have a local copy of the code, you can install Qiskit Metal either in a virtual [conda environment](https://docs.conda.io/en/latest/miniconda.html) or in a virtual Python environment, as described below. We recommend conda.

Notes:

* For your own sanity, it is recommended to read this document in its entirety before proceeding.
* On Windows, the conda environment is strongly recommended because Shapely is difficult to install directly via pip.

### Setup in a conda environment (preferred setup)

If you did not yet install conda, please follow these [instructions](https://docs.conda.io/projects/conda/en/latest/user-guide/install/).
We will setup a conda environment to use the local copy of Qiskit Metal you obtained in the previous section. This approach enables you to immediately observe the effect of your code modifications.

For this section you will need to use the command line. If you use github desktop, you can open one from the menu `Repository -> Open In....`

#### Option 1: A new environment
The most reliable way to set up a qiskit_metal environment is to build one from scratch using the provided conda environment specification file `environment.yml`.
To do so, first navigate to the folder created by the clone. For example:
```sh
cd qiskit-metal
```
Once you are in the folder that contains the `environemnt.yml` file, execute the following installation commands:
```sh
conda env create -n <env_name> environment.yml
conda activate <env_name>
python -m pip install --no-deps -e .
```
Note the use of `--no-deps`. Indeed the `environment.yml` already instructs conda to install all the necessary package dependencies. We therefore prevent `setup.py` from overwriting them with the pip-equivalent packages, which might not be compatible with conda.

This creates a new environment with name `<env_name>` with all the necessary library dependencies.
Then it activates the new environment.
Finally installs the local Qiskit Metal code inside that environment.

The `-e` flag install qiskit\_metal in [editable mode](https://pip.pypa.io/en/stable/reference/pip_install/#cmdoption-e).
You can add the `-v` flag if you would like to observe the verbose output during the installation.

#### Option 2: A pre-existing environment
If convenient, you can instead try to install directly in an existing conda environment `<env_name_exist>`. To do so, just replace the word `create` with `update` in the commands in the previous section. Find the resulting commands updated below for simplicity:
```
conda env update -n <env_name_exist> environment.yml
conda activate <env_name_exist>
python -m pip install --no-deps -e .
```

Notes:

* It is possible that you may run into version conflicts during the above installation, as qiskit-metal requires specific library versions to work correctly on every OS. In this case, please revert to using a separate conda environment.
* **Important**: Remember to `conda activate <env_name>` if you intend to use qiskit-metal.  See what a [conda environment is](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)

#### Jupyter notebook and Jupyter lab hints
The file `environment.yml` contains jupyter. Therefore, launching `jupyter notebook` from your activated new environment `<env_name>`, will make jupyter notebook python execution default to the `<env_name>` python installation.

However, if you did not install jupyter in your `<env_name>` (to save disk space, or to use an existing favorite install), jupyter notebook will execute the python code in the `<other_env>` (typically `base`) where it was installed.

Similarly, `jupyter lab` will in general execute python code from the `base` environment.

In the two above cases, you will need to setup a jupyter kernel that points to your `<env_name>` environment, to be able to find and execute successfully the qiskit-metal package.

Check for the instructions to install a new kernel in the [FAQ](https://qiskit-community.github.io/qiskit-metal/faq.html).

#### Subsequent updates of the conda environment

Package dependencies will evolve over time and could at some point require a new version of a library.
For example, we can anticipate updating `pyEPR-quantum` to enable Ansys interactions previously unsupported.
To update your local install, simply execute the metal package install command
```sh
conda env update -n <env_name_exist> environment.yml
```
Alternatively, you can remove your conda environment by executing the commands below and later re-create a new environment following the original install instructions in section 1.
```sh
conda env list
conda env remove -n <env_name_exist>
```
Notice that using the `conda env update` command might introduce inconsistencies in your virtual environment, and render it unusable. This occurs in general when using conda install commands after any number of pip install commands.

### Setup without conda: in a virtual environment (alternative setup)

#### Prerequisites
The package dependency `gdstk`, needs C++ compilation to successfully install in a base or virtualenv. Make sure the right compiler is installed on your machine if you encounter errors during the installation process described above.
**Windows** you can install the `Visual C++ x.0` using the [C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/). Be sure to select the most current versions of `MSVC` and `Windows SDK`, as suggested in [this wiki](https://wiki.python.org/moin/WindowsCompilers).
**Linux** on Ubuntu or other Debian based systems, execute the following command `sudo apt-get install gcc g++`. Linux users might encounter other python-related errors during creation of the virtualenv or during qiskit-metal installation. You might be able to deal with those by executing `sudo apt-get install python3-dev python3-venv`. Be sure to customize the `python3` string if you are trying to use a custom installation of python.

#### Install
To create and populate the Python virtual environment, execute these commands in the top-level of the repository:
```sh
python -m venv <virtual_env_path/name>
source <virtual_env_path/name>/bin/activate
python -m pip install -U pip
python -m pip install -e .
```
add `-r requirements-dev.txt` to the last line if you intend to install also the packages required for development.
where `<virtual_env_path/name>` is the name of your new Python virtual environment. You can also specify its path. On Windows, replace the activate command line above with this one: `.\<virtual_env_path/name>\Scripts\activate`.

### Installation hints

Here are some things to consider when setting up a development environment:
* Remember to type the period (".") at the end of the pip install command.
* If using a virtual environment, make sure `pip` is up to date. In initial environment testing, PySide2 is installable with only the latest version of `pip`.
* In some setups, you might need to add the qiskit-metal folder path to your PATH variable
* Library errors when activating conda environments, or initializing jupyter notebook/lab, might indicate a conflict between python libraries in the base and sub environments. Go ahead and manually delete the library from the base environment `site-packages` folder, shown in the error message. You might need to reinstall them in the sub environment, or create a new one.
* If Jupyter notebook has trouble finding a dll for a package that works in the new environment outside of Jupyter, then try opening Jupyter notebook from the new environment instead of from `base`

### Installing other dependencies for Open-source Renderers (Gmsh and ElmerFEM)

If you want to use the recently added open-source renderers for [Gmsh](./qiskit_metal/renderers/renderer_gmsh) and [ElmerFEM](./qiskit_metal/renderers/renderer_elmer) for simulation of your design, please make sure that both of them have been installed successfully in your system before running Qiskit Metal. On Windows, Linux, and MacOS (with x86_64 architecture CPUs), Gmsh will be installed automatically using the `environment.yml` file during the conda installation step above. For more detailed steps to install ElmerFEM, please refer to [this](./README_Gmsh_Elmer.md) document.

**NOTE:** We would like to give a disclaimer for users on Apple silicon Macs (M1 and M2-series). Currently, Qiskit Metal uses PySide2 which is not natively supported on the ARM architecture. This will lead to error in instantiating the `MetalGUI` as of now. However, if you still want to use Qiskit Metal without the GUI, the process for installing Gmsh software is a bit different and can be found in [this](./README_Gmsh_Elmer.md) document.

# Other Common Issues

For other common installation issues, please refer to the [FAQ](https://qiskit-community.github.io/qiskit-metal/faq.html)

## Additional steps for developers

If you are planning to develop the qiskit metal codebase, you need extra packages, which you can install by running the following command instead of (or after) the previous one:
```
python -m pip install -r requirements-dev.txt
```
You may also want to also use these instructions to [setup user environment](/docs/NEW_DEVELOPER_SETUP.md)

## Setting up precommit hooks

If are planning on committing, you can run the following in the root of your project to link the available precommit hooks.
```
./hook_setup
```
Please make sure the command is run from the same shell you plan on using to commit. If running on Windows, please make sure that this script is run from git-bash or another Linux-style shell. Currently, the precommit hook will check for yapf formatting.

## Get more information when you commit code and CI gives linting error(s)

If are planning on committing, code and get a linting error. Sometimes the log does not have enough details to fix the error.
```
yapf --diff --recursive --style .style.yapf qiskit_metal
```
Go to directory with qiskit-metal/.style.yapf  file and run the above command to lint locally. This may give more meaningful feedback for linting failure.

## Uninstall precommit hook

```
rm /hooks/pre-commit
```

If you need to uninstall the precommit hook, go to the root of the project and run the above command.
