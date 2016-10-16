""" Contains the tree widgdet
"""
from __future__ import print_function

import ast, logging

from astviewer.misc import class_name
from astviewer.qtpy import QtCore, QtGui, QtWidgets
from astviewer.toggle_column_mixin import ToggleColumnTreeWidget

logger = logging.getLogger(__name__)

IDX_LINE, IDX_COL = 0, 1
ROLE_START_POS = QtCore.Qt.UserRole
ROLE_END_POS   = QtCore.Qt.UserRole + 1

# The widget inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=R0901, R0902, R0904, W0201, R0913


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
        self.add_header_context_menu(checkable={'Node': False}, enabled={'Node': False})

        # Don't stretch last column, it doesn't play nice when columns are
        # hidden and then shown again.
        tree_header.setStretchLastSection(False)



    @QtCore.Slot(int, int)
    def select_node(self, line_nr, column_nr):
        """ Select the node give a line and column number
        """
        found_item = self.find_item(self.invisibleRootItem(), [line_nr, column_nr])
        self.setCurrentItem(found_item) # Unselects if found_item is None


    def find_item(self, tree_item, position):
        """ Finds the deepest node item that highlights the position at line_nr column_nr

            :param tree_item: look within this QTreeWidgetItem and its child items
            :param position: [line_nr, column_nr] list
        """
        item_start_pos = tree_item.data(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_START_POS)
        item_end_pos = tree_item.data(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_END_POS)
        # logger.debug("  find_item: {}: {!r} : {!r}"
        #              .format(tree_item.text(SyntaxTreeWidget.COL_NODE), item_start_pos, item_end_pos))

        # See if one of the children matches
        for childIdx in range(tree_item.childCount()):
            child_item = tree_item.child(childIdx)
            found_node = self.find_item(child_item, position)
            if found_node is not None:
                return found_node

        # If start_pos < position < end_pos the current node matches.
        if item_start_pos is not None and item_end_pos is not None:
            if item_start_pos < position < item_end_pos:
                return tree_item

        # No matching node found in this subtree
        return None


    def populate(self, syntax_tree, root_label=''):
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

        state = dict(from_line = None, from_col = None, to_line = 1, to_col = 0)

        def add_node(ast_node, parent_item, field_label):
            """ Helper function that recursively adds nodes.

                :param parent_item: The parent QTreeWidgetItem to which this node will be added
                :param field_label: Labels how this node is known to the parent
            """
            node_item = QtWidgets.QTreeWidgetItem(parent_item)

            if hasattr(ast_node, 'lineno'):
                position_str = "{:d} : {:d}".format(ast_node.lineno, ast_node.col_offset)

                # If we find a new position string we set the items found since the last time
                # to 'old_line : old_col : new_line : new_col' and reset the list
                # of to-be-updated nodes
                if ast_node.lineno != to_pos[IDX_LINE] or ast_node.col_offset != to_pos[IDX_COL]:

                    # We cannot just say from_pos = to_pos, this creates a new from_pos variable.
                    # A special quirk of Python is that – if no global statement is in effect –
                    # assignments to names always go into the innermost scope.
                    from_pos[IDX_LINE], from_pos[IDX_COL] = to_pos[IDX_LINE], to_pos[IDX_COL]
                    to_pos[IDX_LINE], to_pos[IDX_COL] = ast_node.lineno, ast_node.col_offset
                    for elem in to_be_updated:
                        elem.setText(SyntaxTreeWidget.COL_HIGHLIGHT,
                                     "{0[0]}:{0[1]} : {1[0]}:{1[1]}".format(from_pos, to_pos))
                        elem.setData(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_START_POS, from_pos)
                        elem.setData(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_END_POS, to_pos)

                    to_be_updated[:] = [node_item]
                else:
                    to_be_updated.append(node_item)
            else:
                to_be_updated.append(node_item)
                position_str = ""

            # Recursively descent the AST
            if isinstance(ast_node, ast.AST):
                value_str = ''
                node_str = "{} = {}".format(field_label, class_name(ast_node))
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
            node_item.setText(SyntaxTreeWidget.COL_POS, position_str)

            return node_item

        # End of helper function

        root_item = add_node(syntax_tree, self, root_label)
        self.setCurrentItem(root_item)
        self.expandToDepth(1)
        #self.expandAll()

        # Fill highlight column for remainder of nodes
        for elem in to_be_updated:
            elem.setText(SyntaxTreeWidget.COL_HIGHLIGHT,
                         "{0[0]}:{0[1]} : {1}".format(to_pos, "<eof>:<eol>"))
            elem.setData(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_START_POS, to_pos)
            #elem.setData(SyntaxTreeWidget.COL_HIGHLIGHT, ROLE_END_POS, to_pos) # TODO: what here?

