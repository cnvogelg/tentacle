"""File Set Tab."""

import logging

from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex, QSize, pyqtSlot
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QTreeView, QStyle, QMessageBox
)

from tentacle.client import FileDir, FileGCode


class FileTreeModel(QAbstractItemModel):
    """Represent a file system tree."""

    def __init__(self, root, style, parent=None):
        """Create model with root."""
        super().__init__(parent)
        self.root = root
        self.style = style

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
        return 1

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

        node = index.internalPointer()

        column = index.column()
        if role == Qt.SizeHintRole:
            w = 160 if column == 0 else 70
            return QSize(w, 20)
        elif role == Qt.DecorationRole:
            if isinstance(node, FileDir):
                return self.style.standardIcon(QStyle.SP_DirIcon)
            else:
                return self.style.standardIcon(QStyle.SP_FileIcon)
        elif role != Qt.DisplayRole:
            return None

        if column == 0:
            return node.name
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
        self._t_files.setHeaderHidden(True)
        # button row
        hlayout = QHBoxLayout()
        layout.addLayout(hlayout)
        self._b_select = QPushButton("Select")
        self._b_select.clicked.connect(self._on_select)
        hlayout.addWidget(self._b_select)
        self._b_print = QPushButton("Print")
        self._b_print.clicked.connect(self._on_print)
        hlayout.addWidget(self._b_print)
        self._b_info = QPushButton("Info")
        self._b_info.clicked.connect(self._on_info)
        hlayout.addWidget(self._b_info)
        self._b_delete = QPushButton("Delete")
        self._b_delete.clicked.connect(self._on_delete)
        hlayout.addWidget(self._b_delete)
        self._enable_buttons()

    def _on_update_file_set(self, file_set):
        self._file_set = file_set
        self._model = FileTreeModel(file_set, self.style())
        self._t_files.setModel(self._model)
        sel_model = self._t_files.selectionModel()
        sel_model.selectionChanged.connect(self._on_selection_change)

    def _on_selected_file(self, path):
        logging.info("selected file: %s", path)
        self._l_selected_file.setText(path)

    def _on_selection_change(self):
        self._enable_buttons()

    def _enable_buttons(self):
        is_gcode = False
        is_dir = False
        cur_idx = self._t_files.currentIndex()
        if cur_idx:
            data = cur_idx.internalPointer()
            if data:
                is_gcode = isinstance(data, FileGCode)
                is_dir = isinstance(data, FileDir)
        self._b_select.setEnabled(is_gcode)
        self._b_print.setEnabled(is_gcode)
        self._b_info.setEnabled(is_gcode)
        self._b_delete.setEnabled(is_gcode or is_dir)

    def _get_current_path(self):
        cur_idx = self._t_files.currentIndex()
        if cur_idx:
            data = cur_idx.internalPointer()
            if data:
                return data.get_path()

    @pyqtSlot()
    def _on_select(self):
        self._client.select(self._get_current_path())

    @pyqtSlot()
    def _on_print(self):
        self._client.select(self._get_current_path(), True)

    @pyqtSlot()
    def _on_info(self):
        info = self._client.file_info(self._get_current_path())
        from pprint import pprint
        pprint(info)
        lines = [
            "Name: " + info['display'],
            "Size: " + str(info['size'])
        ]
        gcode_analysis = info['gcodeAnalysis']
        if gcode_analysis:
            dim = gcode_analysis['dimensions']
            lines += [
                "SizeX: %8.3f" % dim['width'],
                "SizeY: %8.3f" % dim['height'],
                "SizeZ: %8.3f" % dim['depth'],
            ]
        QMessageBox.information(self, "File Info", "\n".join(lines))

    @pyqtSlot()
    def _on_delete(self):
        self._client.delete(self._get_current_path())
