# A simple setup script to create an executable using PyQt. 
#
# Step 1. Build first 
#   python setup.py build
# View build dir contents
# Step 2. Create MSI distribution (Windows) 
#   python setup.py bdist_msi
# View dist dir contents

application_title = "QBI Meunier Tracker" #what you want to application to be called
main_python_file = "trackerapp.py" #the name of the python file you use to run the program

import sys

from cx_Freeze import setup, Executable

base = None
if sys.platform == "win32":
    base = "Win32GUI"

includes = ["sip", "PyQt5", "matplotlib", "plotly"]

setup(
        name = application_title,
        version = "1.0",
        description = "Tracker script with GUI",
        author="Liz Cooper-Williams, QBI",
        author_email="e.cooperwilliams@uq.edu.au",
        maintainer="QBI Custom Software, UQ",
        maintainer_email="qbi@uq.edu.au",
        url="http://github.com/QBI-Microscopy/Tracking",
        license="GNU General Public License (GPL)",
        options = {"build_exe" : {"includes" : includes, "include_files" : ["tracker.ui", "tracker_progress.ui", "tracker_help.ui"], "include_msvcr" : 1},},
        executables = [Executable(main_python_file, base = base)])