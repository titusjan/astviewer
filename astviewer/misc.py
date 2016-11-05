""" Miscellaneous routines and constants.
"""
import logging, sys, traceback
import os.path
import astviewer.qtpy
import astviewer.qtpy._version as qtpy_version

from astviewer.version import DEBUGGING, PROGRAM_NAME, PROGRAM_VERSION, PYTHON_VERSION
from astviewer.qtpy import QtCore, QtWidgets

logger=logging.getLogger(__name__)

QT_API = astviewer.qtpy.API
QT_API_NAME = astviewer.qtpy.API_NAME
QTPY_VERSION = '.'.join(map(str, qtpy_version.version_info))

ABOUT_MESSAGE = ("{}: {}\n\nPython: {}\n{} (api={})"
                 .format(PROGRAM_NAME, PROGRAM_VERSION, PYTHON_VERSION, QT_API_NAME, QT_API))



def program_directory():
    """ Returns the program directory where this program is installed
    """
    return os.path.abspath(os.path.dirname(__file__))


def icons_directory():
    """ Returns the program directory where this program is installed
    """
    return os.path.join(program_directory(), 'icons')


###########
# Logging #
###########

def logging_basic_config(level):
    """ Setup basic config logging. Useful for debugging to quickly setup a useful logger"""
    fmt = '%(filename)25s:%(lineno)-4d : %(levelname)-7s: %(message)s'
    logging.basicConfig(level=level, format=fmt)

# pylint: disable=redefined-outer-name

def log_dictionary(dictionary, msg='', logger=None, level='debug', item_prefix='  '):
    """ Writes a log message with key and value for each item in the dictionary.

        :param dictionary: the dictionary to be logged
        :type dictionary: dict
        :param name: An optional message that is logged before the contents
        :type name: string
        :param logger: A logging.Logger object to log to. If not set, the 'main' logger is used.
        :type logger: logging.Logger or a string
        :param level: log level. String or int as described in the logging module documentation.
            Default: 'debug'.
        :type level: string or int
        :param item_prefix: String that will be prefixed to each line. Default: two spaces.
        :type item_prefix: string
    """
    level_nr = logging.getLevelName(level.upper())

    if logger is None:
        logger = logging.getLogger('main')

    if msg :
        logger.log(level_nr, "Logging dictionary: {}".format(msg))

    if not dictionary:
        logger.log(level_nr,"{}<empty dictionary>".format(item_prefix))
        return

    max_key_len = max([len(k) for k in dictionary.keys()])

    for key, value in sorted(dictionary.items()):
        logger.log(level_nr, "{0}{1:<{2}s} = {3}".format(item_prefix, key, max_key_len, value))


# pylint: enable=redefined-outer-name

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


class ResizeDetailsMessageBox(QtWidgets.QMessageBox):
    """ Message box that enlarges when the 'Show Details' button is clicked.
        Can be used to better view stack traces. I could't find how to make a resizeable message
        box but this it the next best thing.

        Taken from:
        http://stackoverflow.com/questions/2655354/how-to-allow-resizing-of-qmessagebox-in-pyqt4
    """
    def __init__(self, detailsBoxWidth=700, detailBoxHeight=300, *args, **kwargs):
        """ Constructor
            :param detailsBoxWidht: The width of the details text box (default=700)
            :param detailBoxHeight: The heights of the details text box (default=700)
        """
        super(ResizeDetailsMessageBox, self).__init__(*args, **kwargs)
        self.detailsBoxWidth = detailsBoxWidth
        self.detailBoxHeight = detailBoxHeight


    def resizeEvent(self, event):
        """ Resizes the details box if present (i.e. when 'Show Details' button was clicked)
        """
        result = super(ResizeDetailsMessageBox, self).resizeEvent(event)

        details_box = self.findChild(QtWidgets.QTextEdit)
        if details_box is not None:
            #details_box.setFixedSize(details_box.sizeHint())
            details_box.setFixedSize(QtCore.QSize(self.detailsBoxWidth, self.detailBoxHeight))

        return result



def handleException(exc_type, exc_value, exc_traceback):
    """ Causes the application to quit in case of an unhandled exception (as God intended)
        Shows an error dialog before quitting when not in debugging mode.
    """

    traceback.format_exception(exc_type, exc_value, exc_traceback)

    logger.critical("Bug: uncaught {}".format(exc_type.__name__),
                    exc_info=(exc_type, exc_value, exc_traceback))
    if DEBUGGING:
        sys.exit(1)
    else:
        # Constructing a QApplication in case this hasn't been done yet.
        if not QtWidgets.qApp:
            _app = QtWidgets.QApplication()

        #msgBox = QtWidgets.QMessageBox()
        msgBox = ResizeDetailsMessageBox()
        msgBox.setText("Bug: uncaught {}".format(exc_type.__name__))
        msgBox.setInformativeText(str(exc_value))
        lst = traceback.format_exception(exc_type, exc_value, exc_traceback)
        msgBox.setDetailedText("".join(lst))
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.exec_()
        sys.exit(1)


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

