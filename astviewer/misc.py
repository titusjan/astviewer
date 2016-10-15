""" Miscellaneous routines and constants.
"""
import logging, sys
import astviewer.qtpy as qtpy
import astviewer.qtpy._version as qtpy_version

from astviewer.qtpy import QtCore, QtWidgets

DEBUGGING = True

PROGRAM_NAME = 'astview'
PROGRAM_VERSION = '1.1.0-dev'
PYTHON_VERSION = "%d.%d.%d" % (sys.version_info[0:3])
QT_API = qtpy.API
QTPY_VERSION = '.'.join(map(str, qtpy_version.version_info))

ABOUT_MESSAGE = ("{}: {}\n\nPython: {}\nQt API: {}"
                 .format(PROGRAM_NAME, PROGRAM_VERSION, PYTHON_VERSION, QT_API))

###########
# Logging #
###########

def logging_basic_config(level):
    """ Setup basic config logging. Useful for debugging to quickly setup a useful logger"""
    fmt = '%(filename)20s:%(lineno)-4d : %(levelname)-7s: %(message)s'
    logging.basicConfig(level=level, format=fmt)


#################
# Type checking #
#################


def class_name(obj):
    """ Returns the class name of an object"""
    return obj.__class__.__name__


def check_class(obj, target_class, allow_none = False):
    """ Checks that the  obj is a (sub)type of target_class.
        Raises a TypeError if this is not the case.
    """
    if not isinstance(obj, target_class):
        if not (allow_none and obj is None):
            raise TypeError("obj must be a of type {}, got: {}"
                            .format(target_class, type(obj)))

############
# Qt stuff #
############

def get_qsettings():
    """ Creates a QSettings object for this application.
        We do not set the application and organization in the QApplication object to
        prevent side-effects in case the AstViewer is imported.
    """
    return QtCore.QSettings("titusjan.nl", PROGRAM_NAME)


def get_qapplication_instance():
    """ Returns the QApplication instance. Creates one if it doesn't exist.
    """
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    check_class(app, QtWidgets.QApplication)
    return app
