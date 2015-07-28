# Tracking
A simple project for handling particle tracking data from the Meunier lab
See Wiki for further information

# Installation
A 64bit Windows installation is provided. 

# Manual Installation
## Requirements
Python 3.4+
PyQt5 (installed/copied) to Python<version>/Lib/site-packages
matplotlib
numpy
plotly

# Python
From a terminal window, check your python version with:
>python --version
Python v3.4.3

If not, install from: https://www.python.org/downloads/release/python-340/

Windows: Install from a MSI file appropriate to your system
MAC OSX: Install from DMG file appropriate to your system
Linux OSes: Python3 should already be installed but default maybe Python2.7
try >python3 --version
(it is possible to change the system default through redirecting the symlink for /usr/local/bin/python)
otherwise see https://www.python.org/download/other/

# PyQt5
Manual installation of PyQt5 : http://pyqt.sourceforge.net/Docs/PyQt5/installation.html
This involves download (SIP and PyQt5), make and install commands

# Matplotlib
Usually installed via python pip installer:
>pip install matplotlib

# Numpy
Usually installed via python pip installer:
>pip install numpy

# Plotly
(see https://plot.ly/python/getting-started/)
Usually installed via python pip installer:
>pip install plotly

In addition: an online plotly account is used  - see https://plot.ly which needs to be activated.
You will need to run the interactive console (ie >python):
>>>import plotly;
>>>plotly.tools.set_credentials_file(username='qbisoftware',api_key='4oklhj4uhy')

To view the plot online: please contact e.cooperwilliams@uq.edu.au for the password
