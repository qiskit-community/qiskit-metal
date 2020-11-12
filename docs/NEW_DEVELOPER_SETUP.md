# ﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿New Qiskit Metal Developer Onboarding
Developer onboarding consists of two main sections – IT administration, github access, and local git repo setup.  You’ll notice that crum.watson.ibm.com is mentioned – you may substitute any computer you wish to use, however crum.watson.ibm.com is the computer that will allow you to integrate metal in other tools (like HFSS) if you do not have your own workstation with these tools on it already.

## IT administration
The following is the list of things to request that an IT administrator set up for you on `crum.watson.ibm.com`.  This is only required if you want to use that server.  Currently, the appropriate action is to email John Walter (`jwalter@ibm.com`), copy Zlatko Minev (`zlatko.minev@ibm.com`) and Jeremy Drysdale (`jdrysda@us.ibm.com`); and ask him to do the following:

* Create an account on crum account – note the account must have the same name as your w3id account name to avoid licensing complications.
* Install Visual Studio 2019 Code on crum
* Install Visual Studio Build Tools 2019 on crum

## Github access
Email Jeremy Drysdale (`jdrysda@us.ibm.com`) or Zlatko Minev (`zlatko.minev@ibm.com`) to ask him to add you to the [qiskit-metal GitHub](https://github.ibm.com/IBM-Q-Restricted-Research/qiskit-metal).  Note: A maintainer must add you.

## Setup local git repo

### A. Create public ssh key
From your development machine

1. Open a terminal
2. Type `ssh-keygen` and press enter.  Follow the prompts to complete.

Note: 	If you do not want to enter a password manually leave that part blank.  Take note of where the ssh public key is saved

### B. Add key to GitHub
From your development machine

1. Open a web browser and navigate to the qiskit-metal git repository (`https://github.ibm.com/IBM-Q-Restricted-Research/qiskit-metal`).  Use [Firefox](https://www.mozilla.org/en-US/firefox/) or [Chrome](https://www.google.com/chrome), do not use internet explorer or Microsoft edge
2. In the upper right corner your picture (or a random pixel picture will appear), click the down arrow to the right of the picture and select the `Settings` option
3. In the left panel select `SSH and GPG keys`
4. Click the green `New SSH key` button
5. Open the `id_rsa.pub` file in the location you noted in part A step.  Paste the contents of that file in the `Key` section of the form.
6. In the `Title` section of the form fill in the part of the `id_rsa.pub` file contents starting with your shortname all the way to the end (e.g. shortname@WIN-LM01CHKSD9E).  Your shortname is the part of your w3id before the @ sign. 

### C. Setup Visual Studio 2019 Code
1. On your development machine download [Visual Studio Code](https://code.visualstudio.com/docs/).
2. Install extensions: `File -> Preferences -> Extensions`

      a. Anaconda Extension Pack 

      b. autoDocstring
  
      c. Install .VSIX
  
      d. Markdown Preview Enhanced
  
      e. PYQT Integration
  
      f. Python
  
      g. Qt for Python
  
      h. SFTP
  
      i. YAML
  
      j. GitLens

3. Open a file with simple python code: `helloworld.py` example below:
```
msg = "hello world"
print(msg)
```

Notes:

* When you open `Visual Studio Code`, select this folder or file within the folder.  You will be prompted to install python extensions, agree. 
* Agree to install linting.  
* **Do NOT agree to install telemetry data being sent to Microsoft**. There is a link to decline that option.
* Look at the bottom of Visual Studio Code screen, the version of python will be listed.  Select `env` to be `‘base’:conda`.  Substitute `base` for the name of your conda environment.

### D. Setup Visual Studio 2019 Code git access
From your development machine

1. Change your default browser to Firefox (or Chrome, or anything other than a Microsoft browser which won't work correctly) by click `Start -> Settings`, then searching for default apps.  A browser will be listed, click it and change it to `Firefox`.
2. Open `Visual Studio 2019`
3. In the `Get Started` pane on the right, click `Clone or check out code`
4. Go to the `Browse a Repository` section and click `GitHub Enterprise`
5. Enter `https://github.ibm.com/IBM-Q-Restricted-Research/` as the server address and click `sign in with Browser`.  Note: If you are asked if you want to connect to Visual Basic click `Yes`
6. You should see links to `qiskit-metal` repositories in the `Open from GitHub Enterprise` window.  Click `Clone`
7. The code should now be cloned
8. Be sure to open `Solution Explorer` to see the code
9. Install two extensions.  From the top ribbon, choose `Extensions -> Manage Extensions` and install:

      a. GitHub Extension for Visual Studio

      b. Microsoft Visual Studio Installer Projects

### E. Install git command line tool (optional)
If you want to use git though the windows command line, install git-scm to your local account.  You can download it here: `https://git-scm.com/download/win`

This tool is safe to install to your local account.  It is highly customizable, be sure to read the prompts and select the options you feel suit your needs and style best.

## VS Code Tweaks & Issues

Take a look at this [summary of a great setup](https://donjayamanne.github.io/pythonVSCodeDocs/docs/python-path/). 

### Auto Formatting
Formatting the source code as and when you save the contents of the file is supported.
Enabling this requires configuring the setting `"editor.formatOnSave": true` as identified [here](https://code.visualstudio.com/updates/v1_47#_format-on-save).

```
"editor.formatOnSave": true  
"python.formatting.provider": "autopep8"
```
Make sure that you have installed

``` 
pip install pep8   
pip install --upgrade autopep8
```
 
### Enable/Disable Linting
By default linting is enabled and uses pylint. `"python.linting.enabled": true`

If [Intellisense/Autocompletion is not working for custom modules](https://donjayamanne.github.io/pythonVSCodeDocs/docs/troubleshooting_intellisense/), then [configure the settings.json to include this custom location for autocompletion to work](https://donjayamanne.github.io/pythonVSCodeDocs/docs/autocomplete/)

You can hide unwanted files from file tree by going to the `user` section and adding these filers:

* `**/.git`
* `**/.svn`
* `**/.hg`
* `**/CVS`
* `**/.DS_Store`
* `__pycache__`

### Git Extension
Another few extensions you may find useful to install from the vs marketplace are

* gitFlow - for those of you that like the git graph functionality
* gittLab
  * When you click a line in the source code, tells you who wrote it.
  * Has powerful git diff viewer for different branches




































