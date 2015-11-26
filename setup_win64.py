'''
    QBI Meunier Tracker APP: setup.py (Windows 64bit MSI)
    *******************************************************************************
    Copyright (C) 2015  QBI Software, The University of Queensland

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
'''
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

build_exe_options = {
    'includes' : ['sip', 'PyQt5'],
    'packages' : ['shapely'],
    'include_files' : ['tracker.ui', 'tracker_progress.ui', 'tracker_help.ui', 'resources/',('D:\\Programs\\Python3\\Lib\\site-packages\\scipy\\special\\_ufuncs.pyd',
    '_ufuncs.pyd')],
    'include_msvcr' : 1
   }
# [Bad fix but only thing that works] NB To add Shortcut working dir - change cx_freeze/windist.py Line 61 : last None - > "TARGETDIR" 
setup(
        name = application_title,
        version = "3.0",
        description = "Tracker script with GUI",
        author="Liz Cooper-Williams, QBI",
        author_email="e.cooperwilliams@uq.edu.au",
        maintainer="QBI Custom Software, UQ",
        maintainer_email="qbi@uq.edu.au",
        url="http://github.com/QBI-Microscopy/Tracking",
        license="GNU General Public License (GPL)",
        options = {"build_exe" : build_exe_options,},
        executables = [Executable(main_python_file, base = base, targetName="trackerapp.exe",icon="resources/target.ico",
        shortcutName=application_title, shortcutDir="DesktopFolder")])