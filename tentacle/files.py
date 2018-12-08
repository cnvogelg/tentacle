"""File Set Tab."""

import logging

from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex, QSize
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QTreeView
)


class FileTreeModel(QAbstractItemModel):
    """Represent a file system tree."""

    def __init__(self, root, parent=None):
        """Create model with root."""
        super().__init__(parent)
        self.root = root

    def rowCount(self, parent):
        """Return number of rows in parent."""
        if not parent.isValid():
            node = self.root
        else:
            node = parent.internalPointer()
        if hasattr(node, 'num_children'):
            return node.num_children()
        return 0

    def columnCount(self, _):
        """Return number of columns in parent."""
        return 3

    def index(self, row, column, parent):
        """Return index in parent."""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            node = self.root
        else:
            node = parent.internalPointer()

        if not hasattr(node, 'num_children'):
            return QModelIndex()
        n = node.num_children()
        if row > n:
            return QModelIndex()
        return self.createIndex(row, column, node.get_children()[row])

    def parent(self, index):
        """Return parent of given index."""
        if not index.isValid():
            return QModelIndex()

        child_node = index.internalPointer()
        parent_node = child_node.parent

        if parent_node == self.root:
            return QModelIndex()

        # row of parent
        if parent_node.parent:
            parent_row = parent_node.parent.get_children().index(parent_node)
        else:
            parent_row = 0

        return self.createIndex(parent_row, 0, parent_node)

    def data(self, index, role):
        """Return data of given index."""
        if not index.isValid():
            return None

        column = index.column()
        if role == Qt.SizeHintRole:
            w = 160 if column == 0 else 70
            return QSize(w, 20)
        elif role != Qt.DisplayRole:
            return None

        node = index.internalPointer()
        if column == 0:
            return node.name
        elif column == 1:
            if hasattr(node, 'size'):
                return str(node.size)
            else:
                return "0"
        elif column == 2:
            if hasattr(node, 'data'):
                return str(node.date)
            else:
                return ""

    def flags(self, index):
        """Return flags of tree item."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        """Return data for header."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ("Name", "Size", "Date")[section]
        return None


class FilesWidget(QWidget):
    """File Set Tab shows all files."""

    NAME, SIZE, DATE = range(3)

    def __init__(self, model, client):
        """Create a new file set tab."""
        super().__init__()
        self._model = model
        self._client = client
        # connect to model
        self._model.updateFileSet.connect(self._on_update_file_set)
        self._model.selectedFile.connect(self._on_selected_file)
        # layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        # active file label
        hlayout = QHBoxLayout()
        layout.addLayout(hlayout)
        hlayout.addWidget(QLabel("Selected:"))
        self._l_selected_file = QLabel("n/a")
        hlayout.addWidget(self._l_selected_file)
        # dir tree
        self._t_files = QTreeView()
        layout.addWidget(self._t_files)
        self._t_files.setRootIsDecorated(False)
        self._t_files.setAlternatingRowColors(True)
        # button row
        hlayout = QHBoxLayout()
        layout.addLayout(hlayout)
        self._b_select = QPushButton("Select")
        hlayout.addWidget(self._b_select)
        self._b_print = QPushButton("Print")
        hlayout.addWidget(self._b_print)
        self._b_info = QPushButton("Info")
        hlayout.addWidget(self._b_info)
        self._b_delete = QPushButton("Delete")
        hlayout.addWidget(self._b_delete)

    def _on_update_file_set(self, file_set):
        self._file_set = file_set
        self._model = FileTreeModel(file_set)
        self._t_files.setModel(self._model)

    def _on_selected_file(self, path):
        logging.info("selected file: %s", path)
        self._l_selected_file.setText(path)
