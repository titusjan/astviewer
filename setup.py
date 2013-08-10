from distutils.core import setup

setup(name = 'astviewer',
    version = '1.0.0', 
    author = "Pepijn Kenter", 
    author_email = "titusjan@gmail.com", 
    py_modules = ['astviewer'], 
    scripts = ['pyastviewer'],
    requires = ['PySide (>=1.1.2)']
)

