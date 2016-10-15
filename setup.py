from distutils.core import setup

from astviewer.misc import DEBUGGING

assert DEBUGGING == False, "DEBUGGING must be False"

setup(name = 'astviewer',
    version = '1.1.0-dev',
    author = "Pepijn Kenter", 
    author_email = "titusjan@gmail.com", 
    py_modules = ['astviewer'], 
    scripts = ['pyastviewer'],
    requires = ['PySide (>=1.1.2)']
)

