# About the project
**bishoujoDE** is a desktop application written in Python, using PyGObject and Gtk4. It was made to work on Linux, in a Gnome Desktop Environment, so it might not be ideal if you have a different desktop environment. The audio and image assets are not included in the repository because they belong to VOICEVOX (link text https://voicevox.hiroshiba.jp/). Before choosing assets, specially on VOICEVOX, please check the licensing information associated with said asset. The particular image file for 中国うさぎ and her voice are free to use under the conditions of this project, but that might not be the case for other use-cases or for other characters.

# Setting up the environment
## Cloning the repository
* Find a appropriate directory and use `git clone` to download the repository files.

## System wide setup
* Install python3, python3-gi, python3-gi-cairo and libgtk-4-dev system wide.
* Create the virtual environment for the master branch with the flag to use system packages, using `python3 -m venv .venv_master --system-site-packages`.
* Create the virtual environment for the dev branch with `python3 -m venv .venv_dev --system-site-packages`.

## Virtual environment local setup
* Activate the master venv with `source .venv_master/bin/activate`.
* Install pip-tools in order to download the python dependencies, using `pip install pip-tools`.
* Compile the `requirements.in` file, which contains the list of dependencies, using `pip-compile requirements.in`.
* The previous step generated a `requirements.txt` file, which you can use to download dependencies with `pip-sync requirements.txt`.
* Repeat that step with the dev branch by:
  * running `deactivate` to deactivate the virtual environment,
  * running `git checkout dev` to change branches,
  * and repeating the steps taken in the master branch to get pip-tools, compiling the requirements and syncing them.

# Setting up audio files
* Documentation pending... for now, you can check the paths on serifu.json and make sure you have audio files there with the corresponding names.

# Setting up the portrait
* Documentation pending...
