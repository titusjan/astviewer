""" Program version information.
"""

# IMPORTANT: this file is included in setup.py. Do not add 3rd party packages here, this
# may break setup.py if users don't have the requirements installed!

import sys

DEBUGGING = False

PROGRAM_NAME = 'astviewer'
PROGRAM_VERSION = '1.1.1'
PYTHON_VERSION = "%d.%d.%d" % (sys.version_info[0:3])
