""" Contains the source editor widget
"""
from __future__ import print_function

import logging

from astviewer.qtpy import QtCore, QtGui, QtWidgets


logger = logging.getLogger(__name__)

# The widget inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201, R0913


class SourceEditor(QtWidgets.QPlainTextEdit):
    """ Source read-ony editor that can detect double clicks.
    """
    sigTextClicked = QtCore.Signal(int, int)
    
    def __init__(self, parent=None):
        """ Constructor
        """
        super(SourceEditor, self).__init__(parent=parent)

        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(13)
        
        self.setReadOnly(True)
        self.setFont(font)
        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.setStyleSheet("selection-color: black; selection-background-color: yellow;")


    def mousePressEvent(self, mouseEvent):
        """ On mouse press the sigTextClicked(line_nr, column_nr) is emited.
        """
        cursor = self.cursorForPosition(mouseEvent.pos())
        # Since the word wrap is off, there is one block par line. BLock numbers are zero-based
        # but code lines start at 1.
        self.sigTextClicked.emit(cursor.blockNumber() + 1, cursor.positionInBlock())



    def select_text(self, from_pos, to_line_pos):
        """ Selects a text in the range from_line:col ... to_line:col
            
            from_pos and to_line_pos should be a (line, column) tuple
            If from_pos is None, the selection starts at the beginning of the document
            If to_line_pos is None, the selection goes to the end of the document
        """
        text_cursor = self.textCursor()
        
        if from_pos is None:
            text_cursor.movePosition(QtGui.QTextCursor.Start, QtGui.QTextCursor.MoveAnchor)
        else:
            from_line, from_col = from_pos
            # findBlockByLineNumber seems to be 0-based.
            from_text_block = self.document().findBlockByLineNumber(from_line - 1)
            from_pos = from_text_block.position() + from_col
            text_cursor.setPosition(from_pos, QtGui.QTextCursor.MoveAnchor)

        if to_line_pos is None:
            text_cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
        else:
            to_line, to_col = to_line_pos
            to_text_block = self.document().findBlockByLineNumber(to_line - 1)
            to_pos = to_text_block.position() + to_col
            text_cursor.setPosition(to_pos, QtGui.QTextCursor.KeepAnchor)
        
        self.setTextCursor(text_cursor)
        self.ensureCursorVisible()
