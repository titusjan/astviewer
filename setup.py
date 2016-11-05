#!/usr/bin/env python
# -*- coding: utf-8 -*-


# To make a release follow these steps:
#   python setup.py sdist --formats=zip

# Then upload to PiPy with
#   twine upload dist/astviewer-1.1.1.zip

from distutils.core import setup

from astviewer.version import DEBUGGING, PROGRAM_VERSION

assert not DEBUGGING, "DEBUGGING must be False"

setup(name = 'astviewer',
    version = PROGRAM_VERSION,
    author = "Pepijn Kenter", 
    author_email = "titusjan@gmail.com",
    description = 'GUI for viewing a Python Abstract Syntax Tree.',
    long_description = open('README.txt').read(),
    url = 'https://github.com/titusjan/astviewer',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Adaptive Technologies',
        'Topic :: Software Development',
        'Topic :: Utilities'],
    packages = ['astviewer', 'astviewer.qtpy', 'astviewer.qtpy._patch'],
    package_data = {'astviewer': ['icons/*']}, # don't use data_files, it installs relative to the intallation dir (e.g. /usr/local)
    scripts = ['pyastviewer'],
    #requires = ['pyqt']
)

