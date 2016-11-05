# -*- coding: utf-8 -*-

""" Miscellaneous Qt routines.
"""
from __future__ import print_function
import logging, os

from astviewer.qtpy import QtCore, QtGui, QtSvg
from astviewer.misc import program_directory, log_dictionary
from astviewer.version import DEBUGGING

logger = logging.getLogger(__name__)



class IconFactory(object):
    """ A factory class that generates QIcons for use in the tree.

        The factory contains a icon registry that contains for registered glyphs, the location of
        an SVG file. The SVG files originate from the snip-icon library.
        See http://www.snipicons.com/

        The getIcon method can optionally set the fill color of the icons. It also caches the
        generated QItem objects to that they only have to be created once.
    """

    ICONS_DIRECTORY = os.path.join(program_directory(), 'icons')
    #ICON_SIZE = 32 # Render in this size

    # Registered glyph names
    PY_NODE = "py-node"
    AST_NODE = "ast-node"
    LIST_NODE = "list-node"

    _singleInstance = None

    def __init__(self):
        """ Constructor
        """
        self._icons = {}
        self._registry = {}
        self.colorsToBeReplaced = ('#008BFF', '#00AAFF')
        self.renderSizes = [16, 24, 32, 64]

        self.registerIcon(None, None) # no icon
        self.registerIcon("",   None) # no icon
        self.registerIcon("pynode.svg", IconFactory.PY_NODE)
        self.registerIcon("astnode.svg",   IconFactory.AST_NODE)
        self.registerIcon("list-l.svg", IconFactory.LIST_NODE)


    @classmethod
    def singleton(cls):
        """ Returns the IconFactory singleton.
        """
        if cls._singleInstance is None:
            cls._singleInstance = cls()
        return cls._singleInstance


    def registerIcon(self, fileName, glyph):
        """ Register an icon SVG file given a glyph.

            :param fileName: filename to the SVG file.
                If the filename is a relative path, the ICONS_DIRECTORY will be prepended.
            :param glyph: a string describing the glyph (e.g. 'file', 'array')
            :return: QIcon
        """
        if fileName and not os.path.isabs(fileName):
            fileName = os.path.join(self.ICONS_DIRECTORY, fileName)

        self._registry[glyph] = fileName


    def getIcon(self, glyph, color=None):
        """ Returns a QIcon given a glyph name and color.

            The resulting icon is cached so that it only needs to be rendered once.

            :param glyph: name of a registered glyph (e.g. 'file', 'array')
            :param color: '#RRGGBB' string (e.g. '#FF0000' for red)
            :return: QtGui.QIcon
        """
        try:
            fileName = self._registry[glyph]
        except KeyError:
            logger.warning("Unregistered icon glyph: {}".format(glyph))
            log_dictionary(self._registry, "registry", logger=logger)
            raise

        return self.loadIcon(fileName, color=color)


    def loadIcon(self, fileName, color=None):
        """ Reads SVG from a file name and creates an QIcon from it.

            Optionally replaces the color. Caches the created icons.

            :param fileName: absolute path to an icon file.
                If False/empty/None, None returned, which yields no icon.
            :param color: '#RRGGBB' string (e.g. '#FF0000' for red)
            :return: QtGui.QIcon
        """
        if not fileName:
            return None

        key = (fileName, color)
        if key not in self._icons:
            try:
                with open(fileName, 'r') as inputFile:
                    svg = inputFile.read()

                self._icons[key] = self.createIconFromSvg(svg, color=color)
            except Exception as ex:
                # It's preferable to show no icon in case of an error rather than letting
                # the application fail. Icons are a (very) nice to have.
                logger.warning("Unable to read icon: {}".format(ex))
                if DEBUGGING:
                    raise
                else:
                    return None

        return self._icons[key]


    def createIconFromSvg(self, svg, color=None, colorsToBeReplaced=None):
        """ Creates a QIcon given an SVG string.

            Optionally replaces the colors in colorsToBeReplaced by color.

            :param svg: string containing Scalable Vector Graphics XML
            :param color: '#RRGGBB' string (e.g. '#FF0000' for red)
            :param colorsToBeReplaced: optional list of colors to be replaced by color
                If None, it will be set to the fill colors of the snip-icon libary
            :return: QtGui.QIcon
        """
        if colorsToBeReplaced is None:
            colorsToBeReplaced = self.colorsToBeReplaced

        if color:
            for oldColor in colorsToBeReplaced:
                svg = svg.replace(oldColor, color)

        # From http://stackoverflow.com/questions/15123544/change-the-color-of-an-svg-in-qt
        qByteArray = QtCore.QByteArray()
        qByteArray.append(svg)
        svgRenderer = QtSvg.QSvgRenderer(qByteArray)
        icon = QtGui.QIcon()
        for size in self.renderSizes:
            pixMap = QtGui.QPixmap(QtCore.QSize(size, size))
            pixMap.fill(QtCore.Qt.transparent)
            pixPainter = QtGui.QPainter(pixMap)
            pixPainter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
            pixPainter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            svgRenderer.render(pixPainter)
            pixPainter.end()
            icon.addPixmap(pixMap)

        return icon
