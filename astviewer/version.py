""" Program version information.
"""
from importlib.metadata import version


import sys

DEBUGGING = False

PROGRAM_NAME = 'astviewer'
PYTHON_VERSION = "%d.%d.%d" % (sys.version_info[0:3])

try:
    PROGRAM_VERSION = version("astviewer")
except ImportError:
    PROGRAM_VERSION = '?.?.?'
