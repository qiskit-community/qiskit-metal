# Qiskit Metal [![](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/Qiskit/qiskit-metal) [![](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/Qiskit/qiskit-metal) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4618153.svg)](https://doi.org/10.5281/zenodo.4618153)
>  Quantum hardware design and analysis

![Welcome to Qiskit Metal!](docs/images/zkm_banner.png 'Welcome to Qiskit Metal')

### Quantum device design project
We are thrilled to ask you to join this journey to revolutionize quantum devices. This is a first-of-its-kind, open-source project for engineers and scientists to design superconducting quantum devices with ease.

Qiskit-metal is licensed under Apache 2.0. IBM reserves no copyright over outputs of qiskit-metal.

#### Get help: Slack
Use the slack channel.  Join [qiskit slack](https://ibm.co/joinqiskitslack) and then join the `#metal` channel to communicate with the developers and other participants.  You may also use this channel to inquire about collaborations.

#### Take part to the live tutorials and discussion
Through June 2021 we are offering live tutorials and Q&A. [Sign up](https://airtable.com/shrxQEgKqZCf319F3) to receive an invite to the upcoming sessions.  The streaming will also be recorded and made available for offline review.  Find [here](https://github.com/Qiskit/qiskit-metal/blob/main/README_Tutorials.md) more details on schedule and use the Slack channel to give us feedback and to request the most relevant content to you.

The streaming will also be recorded and made available [here](https://www.youtube.com/playlist?list=PLOFEBzvs-VvqHl5ZqVmhB_FcSqmLufsjb) for offline review.

## Documentation 
After installation, you can open the documentation like this
```python
import qiskit_metal
qiskit_metal.open_docs()
```

There is no need to build the docs unless you want to.  In lieu of building the docs you can find them at https://qiskit.org/documentation/metal/.

If you choose to build the docs, you do so by running `python build_docs.py` in a shell in the `docs` folder.

## Installation
### Video Instructions

<a href="https://www.youtube.com/watch?v=sYVDtnJb-ZM&ab_channel=Qiskit">
 Click for YouTube Video <br>
	<img src="https://www.gstatic.com/youtube/img/branding/youtubelogo/svg/youtubelogo.svg" alt="Qiskit Metal Install" width=250>
</a>

### Text Instructions
#### Retrieve the code
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

#### Conda environment setup (preferred setup)

If you did not yet install conda, please follow these [instructions](https://docs.conda.io/projects/conda/en/latest/user-guide/install/).
We will setup a conda environment to use the local copy of qiskit-metal you obtained in the previous section. This approach enables you to immediately observe the effect of your code modifications.

For this section you will need to use the command line. If you use github desktop, you can open one from the menu `Repository -> Open In....`

##### Option 1: A new environment
The most reliable way to set up a qiskit_metal environment is to build one from scratch using the provided conda environment specification file `environment.yml`.
To do so, first navigate to the folder created by the clone. For example:
```sh
cd qiskit-metal
```
Once you are in the folder that contains the `environemnt.yml` file, execute the following installation commands:
```sh
conda env create -n <env_name> environment.yml
conda activate <env_name>
python -m pip install -ve .
```
Execute the following command if you plan to contribute code:
```
python -m pip install -r requirements-dev.txt -ve .
```

This creates a new environment with name `<env_name>` with all the necessary library dependencies.
Then it activates the new environment.
Finally installs the local qiskit-metal code inside that environment.

The `-e` flag install qiskit\_metal in [editable mode](https://pip.pypa.io/en/stable/reference/pip_install/#cmdoption-e).
The `-v` flag is for verbose.

##### Option 2: A pre-existing environment
If convenient, you can instead try to install directly in an existing conda environment `<env_name_exist>`, if it is relatively up to date.
To do so, execute these commands in the top-level of the repository:
```
conda env update -n <env_name_exist> environment.yml
conda activate <env_name_exist>
python -m pip install -ve .
```
Execute the following command if you plan to contribute code:
```
python -m pip install -r requirements-dev.txt -ve .
```

Notes:

* It is possible that you may run into version conflicts during the above installation, as qiskit-metal requires specific library versions to work correctly on every OS.
* Remember the period (".") at the end of the third command.
* **Important**: Remember to `conda activate <env_name>` if you intend to use qiskit-metal.  See what a [conda environment is](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)

At this point you can already use qiskit-metal through jupyter notebook.
However, if you prefer using jupyter lab, you will need to execute a couple of extra steps.

##### (Optional) Jupyter lab
Launching jupyter lab will execute python code in the conda `base` environment by default.
To change environment to the Qiskit Metal one you just finished setting up, denoted by `<env_name>`, which we usually just call `metal`, you will need first to add to jupyter lab's list of available kernels. 
From the command line, run the following lines (inside an active <env_name> environment):
```sh
conda activate <env_name>
conda install ipykernel
ipython kernel install --user --name=<any_name_for_kernel>
```
Using the above command, you will now have the current conda environment in any Jupyter notebook.

Once inside `jupyter lab`, you can switch to the newly created Metal kernel to use qiskit-metal. Use the Menu `Kernel>Change Kernel`.

#### Subsequent updates of the conda environment

Package dependencies will evolve over time and could at some point require a new version of a library.
For example, we can anticipate updating `pyEPR-quantum` to enable Ansys interactions previously unsupported.
To update your local install, simply execute the metal package install command
```sh
python -m pip install -ve .
``` 
Alternatively, you can remove your conda environment by executing the commands below and later re-create a new environment following the original install instructions in section 1.
```sh
conda env list
conda env remove -n <env_name_exist>
``` 
We discourage using conda commands to update packages after the install of Qiskit Metal.
Indeed, since Qiskit Metal is installed using pip, the subsequent use of conda commands can introduce inconsistencies that could render your environment unusable.

#### Without conda: Virtual environment setup (alternative setup)

**On Windows, do this first:** It is recommended that you first install `Visual C++ 14.0`, it is required for a successful install of `gdspy`.
If you do not have `Visual C++ 14.0` installed you will be notified to install it when `gdspy` attempts to install.
You can do this by downloading and installing [C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
Be sure to select the latest versions of `MSVCv142 - VS 2019 C++ x64/x86 build tools` and `Windows 10 SDK` in the installer as suggested in [this wiki](https://wiki.python.org/moin/WindowsCompilers) referenced by the gdspy documentation.

To use a Python virtual environment, execute these commands in the top-level of the repository:
```sh
python -m venv <virtual_env_path>
source <virtual_env_path>/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt -r requirements-dev.txt -e .
```
where `<virtual_env_path>` is where you want the Python virtual environment to be installed.
On Windows, replace `source <virtual_env_path>/bin/activate` with `.\<virtual_env_path>\Scripts\activate`.

#### Installation hints

Here are some things to consider when setting up a development environment:
* If using a virtual environment, make sure `pip` is up to date. In initial environment testing, PySide2 is installable with only the latest version of `pip`.
* Add the path of your qiskit-metal folder to your PATH
* Library errors when activating conda environments, or initializing jupyter notebook/lab, indicate a conflict between python libraries in the base and sub environments. Go ahead and manually delete the library from the base environment `site-packages` folder, shows in the error message. You might need to reinstall them in the sub environment, or create a new one.
 If Jupyter notebook has trouble finding a dll for a package that works in the new environment outside of Jupyter, then try opening Jupyter notebook from the new environment instead of from `base`

### Additional steps for developers

If you are planning to develop the qiskit metal codebase, you'll want to use these instructions to [setup user environment](/docs/NEW_DEVELOPER_SETUP.md)


### Common Issues

#### pyqode/pyside

Please be aware that the environment.xml and requirements.txt each use a different `pyside` version. This is done for Windows OS users to prevent a ipython kernel crash caused by the installation of a library incompatible with `pyqode`.

For other OS users, this setup might cause `pyqode.qt` to be upgraded automatically after it is first installed. If you still observe `pyqode`-related errors, try forcing the upgrade of the pyqode.python library with `pip install pyqode.python --upgrade`.

If Windows users continue to experience GUI or other issues, try rerunning `python setup.py install` or creating a new, pristine conda environment as per above instructions. Pay particular attention to the python version, which must remain 3.7.8 for as long as qiskit-metal utilizes pyqode.

#### Jupyter Lab

If you can not start Jupyter Lab in the new environment.

Based on: https://anaconda.org/conda-forge/jupyterlab
Install Jupyter lab by
```sh
conda install -c conda-forge jupyterlab
```
Then change directory to top level of repository.
```sh
python -m pip install -e .
```

#### qutip

`qutip` may have issues finding your path if using VSCode, resulting in a `KeyError: 'physicalcpu'`. If the error occurs, please add your PATH to VSCode's settings as follows.


##### Windows:
Open Windows Command Prompt and type in
```sh
path
```
Copy the resulting output. Example: `"PATH": "\usr\local\bin:\usr\bin:\bin:\usr\sbin:\sbin"`
Then open the applicable settings.json in your VS Code. (See how to open command palette [here](https://code.visualstudio.com/docs/getstarted/tips-and-tricks). Search "settings" and click Open Workspace Settings (JSON)). Paste:
```
 "terminal.integrated.env.windows": {
        "PATH": "\usr\local\bin:\usr\bin:\bin:\usr\sbin:\sbin"
        }
```

##### MacOs:
 Open Terminal and type in
 ```sh
echo $PATH
 ```
Copy the resulting output. Example: `"PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"`
Then open the applicable settings.json in your VS Code. (See how to open command palette [here](https://code.visualstudio.com/docs/getstarted/tips-and-tricks). Search "settings" and click Open Workspace Settings (JSON)). Paste:
```
    "terminal.integrated.env.osx": {
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        }
```


## Authors and Citation

Qiskit Metal is the work of [many people](https://github.com/Qiskit/qiskit-metal/pulse/monthly) who contribute to the project at different levels. Metal was conceived and developed by [Zlatko Minev](zlatko-minev.com) at IBM; then co-led with Thomas McConkey. If you use Qiskit Metal, please cite as per the included [BibTeX file](https://github.com/Qiskit/qiskit-metal/blob/main/Qiskit_Metal.bib). For icon attributions, see [here](/qiskit_metal/_gui/_imgs/icon_attributions.txt).


## License

[Apache License 2.0](LICENSE.txt)
