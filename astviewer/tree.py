""" Contains the tree widgdet
"""
from __future__ import print_function

import ast, logging
import os.path

from astviewer.misc import class_name
from astviewer.qtpy import QtCore, QtGui, QtWidgets
from astviewer.toggle_column_mixin import ToggleColumnTreeWidget

logger = logging.getLogger(__name__)

IDX_LINE, IDX_COL = 0, 1
ROLE_POS = QtCore.Qt.UserRole
ROLE_START_POS = QtCore.Qt.UserRole
ROLE_END_POS   = QtCore.Qt.UserRole + 1

# The widget inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201, R0913


def cmpIdx(idx0, idx1):
    """ Returns negative if idx0 < idx1, zero if idx0 == idx1 and strictly positive if idx0 > idx1.

        If an idx0 or idx1 equals -1 or None, it is interpreted as the last element in a list
        and thus larger than a positive integer

        :param idx0: positive int, -1 or None
        :param idx2: positive int, -1 or None
        :return: int
    """
    assert idx0 == None or idx0 == -1 or idx0 >=0, \
        "Idx0 should be None, -1 or >= 0. Got: {!r}".format(idx0)
    assert idx1 == None or idx1 == -1 or idx1 >=0, \
        "Idx1 should be None, -1 or >= 0. Got: {!r}".format(idx1)

    # Handle -1 the same way as None
    if idx0 == -1:
        idx0 = None
    if idx1 == -1:
        idx1 = None

    if idx0 == idx1:
        return 0
    elif idx1 is None:
        return -1
    elif idx0 is None:
        return 1
    else:
        return -1 if idx0 < idx1 else 1

    
def cmpPos(pos0, pos1):
    """ Returns negative if pos0 < pos1, zero if pos0 == pos1 and strictly positive if pos0 > pos1.

        If an pos0 or pos1 equals -1 or None, it is interpreted as the last element in a list
        and thus larger than a positive integer

        :param pos0: positive int, -1 or None
        :param pos2: positive int, -1 or None
        :return: int
    """
    cmpLineNr = cmpIdx(pos0[0], pos1[0])
    if cmpLineNr != 0:
        return cmpLineNr
    else:
        return cmpIdx(pos0[1], pos1[1])


class SyntaxTreeWidget(ToggleColumnTreeWidget):
    """ Source read-ony editor that can detect double clicks.
    """
    HEADER_LABELS = ["Node", "Field", "Class", "Value", "Line : Col", "Highlight"]
    (COL_NODE, COL_FIELD, COL_CLASS, COL_VALUE, COL_POS, COL_HIGHLIGHT) = range(len(HEADER_LABELS))

    def __init__(self, parent=None):
        """ Constructor
        """
        super(SyntaxTreeWidget, self).__init__(parent=parent)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setUniformRowHeights(True)
        self.setAnimated(False)

        self.setHeaderLabels(SyntaxTreeWidget.HEADER_LABELS)
        tree_header = self.header()
        self.add_header_context_menu(checked={'Node': True}, checkable={'Node': True},
                                     enabled={'Node': False})

        # Don't stretch last column, it doesn't play nice when columns are
        # hidden and then shown again.
        tree_header.setStretchLastSection(False)


    @QtCore.Slot()
    def expand_classes(self, tree_item=None):
        """ Expands all classes and body lists so that functions and methods show
        """
        if tree_item is None:
            tree_item = self.invisibleRootItem()

        field = tree_item.text(SyntaxTreeWidget.COL_FIELD)
        klass = tree_item.text(SyntaxTreeWidget.COL_CLASS)

        tree_item.setExpanded(field == 'body' or
                              klass in ('Module', 'ClassDef'))

        # Expand children recursively
        for childIdx in range(tree_item.childCount()):
            self.expand_classes(tree_item.child(childIdx))


    @QtCore.Slot(int, int)
    def select_node(self, line_nr, column_nr):
        """ Select the node give a line and column number
        """
        found_item = self.find_item(self.invisibleRootItem(), (line_nr, column_nr))
        self.setCurrentItem(found_item) # Unselects if found_item is None


    def get_item_span(self, tree_item):
        """ Returns (start_pos, end_pos) tuple where start_pos and end_pos in turn are (line, col)
            tuples
        """
        start_pos = tree_item.data(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_START_POS)
        end_pos = tree_item.data(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_END_POS)
        return (start_pos, end_pos)



    def find_item(self, tree_item, position):
        """ Finds the deepest node item that highlights the position at line_nr column_nr and
            has a position defined itself.

            :param tree_item: look within this QTreeWidgetItem and its child items
            :param position: [line_nr, column_nr] list
        """
        item_pos = tree_item.data(SyntaxTreeWidget.COL_POS, ROLE_POS)
        item_start_pos = tree_item.data(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_START_POS)
        item_end_pos = tree_item.data(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_END_POS)

        # See if one of the children matches
        for childIdx in range(tree_item.childCount()):
            child_item = tree_item.child(childIdx)
            found_node = self.find_item(child_item, position)
            if found_node is not None:
                return found_node

        # If start_pos < position < end_pos the current node matches.
        if item_start_pos is not None and item_end_pos is not None:
            if item_pos is not None and item_start_pos < position < item_end_pos:
                return tree_item

        # No matching node found in this subtree
        return None


    def populate(self, syntax_tree, last_pos, root_label=''):
        """ Populates the tree widget.

            :param syntax_tree: result of the ast.parse() function
            :param file_name: used to set the label of the root_node
        """
        self.clear()

        # State we keep during the recursion.
        # Is needed to populate the selection column.
        to_be_updated = list([])
        from_pos = [None, None] # line, col
        to_pos   = [1, 0]

        def add_node(ast_node, parent_item, field_label):
            """ Helper function that recursively adds nodes.

                :param parent_item: The parent QTreeWidgetItem to which this node will be added
                :param field_label: Labels how this node is known to the parent
                :return: the QTreeWidgetItem that corresonds to the root item of the AST
            """
            node_item = QtWidgets.QTreeWidgetItem(parent_item)

            # Recursively descent the AST
            if isinstance(ast_node, ast.AST):
                value_str = ''
                node_str = "{} = {}".format(field_label, class_name(ast_node))

                if hasattr(ast_node, 'lineno'):
                    node_item.setData(SyntaxTreeWidget.COL_POS, ROLE_POS,
                                      (ast_node.lineno, ast_node.col_offset))

                for key, val in ast.iter_fields(ast_node):
                    add_node(val, node_item, key)

            elif isinstance(ast_node, (list, tuple)):
                value_str = ''
                node_str = "{} = {}".format(field_label, class_name(ast_node))
                for idx, elem in enumerate(ast_node):
                    add_node(elem, node_item, "{}[{:d}]".format(field_label, idx))
            else:
                value_str = repr(ast_node)
                node_str = "{} = {}".format(field_label, value_str)


            node_item.setText(SyntaxTreeWidget.COL_NODE, node_str)
            node_item.setText(SyntaxTreeWidget.COL_FIELD, field_label)
            node_item.setText(SyntaxTreeWidget.COL_CLASS, class_name(ast_node))
            node_item.setText(SyntaxTreeWidget.COL_VALUE, value_str)

            node_item.setToolTip(SyntaxTreeWidget.COL_NODE, node_str)
            node_item.setToolTip(SyntaxTreeWidget.COL_FIELD, field_label)
            node_item.setToolTip(SyntaxTreeWidget.COL_CLASS, class_name(ast_node))

            return node_item

        # End of helper function

        root_item = add_node(syntax_tree, self, root_label)
        root_item.setToolTip(SyntaxTreeWidget.COL_NODE, os.path.realpath(root_label))

        self._populate_highlighting_pass_1(self.invisibleRootItem(), last_pos)
        self._populate_highlighting_pass_2(self.invisibleRootItem())
        self._populate_text_from_data(self.invisibleRootItem())


        return root_item


    def _populate_highlighting_pass_1(self, tree_item, last_pos):
        """ Fills the highlight span for items that have a position defined. (pass 1)

            Walk depth-first and backwards through the nodes, so that we can keep track of the
            end of the span (last_pot)
        """
        max_last_pos = last_pos # The maximum last_pos at this level of recursion.

        for childIdx in range(tree_item.childCount(), 0, -1):
            child_item = tree_item.child(childIdx-1)
            children_last_pos = self._populate_highlighting_pass_1(child_item, last_pos)

            # Decorator nodes seem to be out-of order in the tree. They occur after the body but
            # their line number is smaller. This messes up the highlight spans so we don't
            # propagate their value
            if tree_item.text(SyntaxTreeWidget.COL_FIELD) != u'decorator_list':
                last_pos = children_last_pos

        pos = tree_item.data(SyntaxTreeWidget.COL_POS, ROLE_POS)
        if pos is not None:
            last_pos = pos

        assert last_pos is not None
        assert max_last_pos is not None
        cmp = cmpPos(last_pos, max_last_pos)
        if cmp < 0:
            tree_item.setData(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_START_POS, last_pos)
            tree_item.setData(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_END_POS, max_last_pos)
        elif cmp > 0:
            # This seems to occur when a function has decorators, which are located in the tree
            # after the body but have a line number that is smaller. Don't know how what to do.
            logger.warn("Nodes out of order. Invalid highlighting {}:{} : {}:{} ({})"
                        .format(last_pos[0], last_pos[1], max_last_pos[0], max_last_pos[1],
                                tree_item.text(SyntaxTreeWidget.COL_NODE)))
            tree_item.setData(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_START_POS, last_pos)
            tree_item.setData(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_END_POS, max_last_pos)
            tree_item.setForeground(SyntaxTreeWidget.COL_HIGHLIGHT,
                                    QtGui.QBrush(QtGui.QColor('red')))

        else:
            pass # No new position found in the children. These nodes will be filled in later.

        return last_pos


    @QtCore.Slot()
    def _populate_highlighting_pass_2(self, tree_item, parent_start_pos=None, parent_end_pos=None):
        """ Fill in the nodes that don't have a highlighting from their parent
        """
        start_pos = tree_item.data(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_START_POS)
        end_pos = tree_item.data(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_END_POS)

        # If the highlight span is still undefined use the value from the parent.
        if (start_pos is None and end_pos is None):
            start_pos = parent_start_pos
            end_pos = parent_end_pos
            tree_item.setData(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_START_POS, start_pos)
            tree_item.setData(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_END_POS, end_pos)

        # Populate children recursively
        for childIdx in range(tree_item.childCount()):
            self._populate_highlighting_pass_2(tree_item.child(childIdx), start_pos, end_pos)


    def _populate_text_from_data(self, tree_item):
        """ Fills the pos and highlight columns given the underlying data.
        """
        # Update the pos column
        pos = tree_item.data(SyntaxTreeWidget.COL_POS, ROLE_POS)
        if pos is None:
            text = ""
        else:
            text = "{0[0]}:{0[1]}".format(pos)

        tree_item.setText(SyntaxTreeWidget.COL_POS, text)

        # Update the highlight column
        start_pos = tree_item.data(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_START_POS)
        end_pos = tree_item.data(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_END_POS)

        text = ""

        if start_pos is not None:
            text += "{0[0]}:{0[1]}".format(start_pos)

        if end_pos is not None:
            text += " : {0[0]}:{0[1]}".format(end_pos)

        tree_item.setText(SyntaxTreeWidget.COL_HIGHLIGHT, text)

        # Recursively populate
        for childIdx in range(tree_item.childCount()):
            child_item = tree_item.child(childIdx)
            self._populate_text_from_data(child_item)

