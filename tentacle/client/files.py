"""Files Model for OctoClient."""

import logging

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class FileBase:
    """File node base class."""

    def __init__(self, name):
        """Initialize base node."""
        self.name = name
        self.parent = None

    def get_path(self):
        """Return file path up to root."""
        if self.parent and self.parent.name != "":
            return "/".join((self.parent.get_path(), self.name))
        else:
            return self.name


class FileDir(FileBase):
    """File system directory."""

    def __init__(self, name):
        """Create a file system directory."""
        super().__init__(name)
        self.childs = []

    def __repr__(self):
        """Dump dir."""
        return "Dir(%r,%r)" % (self.name, self.childs)

    def add_child(self, child):
        """Add a new child to directory."""
        self.childs.append(child)
        child.parent = self

    def num_children(self):
        """Return number of children."""
        return len(self.childs)

    def get_children(self):
        """Return children array."""
        return self.childs

    def get_child_by_name(self, name):
        """Return child with given name or None."""
        for c in self.childs:
            if c.name == name:
                return c

    def remove_child_by_name(self, name):
        """Remove a child given by name."""
        i = 0
        for c in self.childs:
            if c.name == name:
                del self.childs[i]
                return True
            i += 1
        return False


class FileRoot(FileDir):
    """Root of a file system tree."""

    def __init__(self, total, free):
        """Create a file system root."""
        super().__init__("")
        self.total = total
        self.free = free

    def __repr__(self):
        """Dump root."""
        return "Root(total=%d,free=%d,%r)" % (
            self.total, self.free, self.childs)


class FileGCode(FileBase):
    """A GCode File."""

    def __init__(self, name):
        """Create a gcode file."""
        super().__init__(name)
        self.meta = None

    def __repr__(self):
        """Represent gcode file."""
        return "FileGCode(%s, meta=%r)" % (self.name, self.meta)


class FileMeta:
    """File Meta Data."""

    def __init__(self, range_x, range_y, range_z):
        """Create file meta data."""
        self.range_x = range_x
        self.range_y = range_y
        self.range_z = range_z

    def __repr__(self):
        """Represent file meta data."""
        return "Meta(X=%r, Y=%r, Z=%r)" % (
            self.range_x, self.range_y, self.range_z)


class FileModel(QObject):
    """The DataModel instance sends out signals on data change."""

    # file set signals
    updateFileSet = pyqtSignal(FileRoot)
    addedFile = pyqtSignal(str)
    removedFile = pyqtSignal(str)
    selectedFile = pyqtSignal(str)
    addedFolder = pyqtSignal(str)
    removedFolder = pyqtSignal(str)

    def __init__(self):
        """Create a new DataModel instance."""
        super().__init__()
        self._selected_file = ""
        self._files = FileRoot(0, 0)
        self._meta_cache = {}
        self._client = None

    def attach(self, client):
        """Attach data model to octo client."""
        client.file_set.connect(self.on_file_set)
        client.event.connect(self.on_event)
        self._client = client

    def get_meta(self, path):
        """Retrieve meta info of file."""
        if path in self._meta_cache:
            logging.info("file meta from cache: %s", path)
            return self._meta_cache[path]
        # try to get info
        file_info = self._client.file_info(path)
        if file_info:
            logging.info("file meta retrieved: %s: %s", path, file_info)
            self._files_set_meta(path, file_info)
            return self._meta_cache[path]
        else:
            logging.error("can't get file info: %s", path)

    @pyqtSlot(dict)
    def on_file_set(self, data):
        """React on initial files set."""
        logging.info("got file set")
        free = data['free']
        total = data['total']
        root = FileRoot(free, total)
        self._convert_file_children(data['files'], root)
        self.updateFileSet.emit(root)
        self._files = root

    @pyqtSlot(dict)
    def on_event(self, data):
        """React on events."""
        if 'type' in data and 'payload' in data:
            payload = data['payload']
            event_type = data['type']
            if event_type == 'FileAdded':
                path = payload['path']
                file_type = payload['type']
                if file_type[0] == 'machinecode':
                    self._files_add_gcode_file(path)
            elif event_type == 'FileRemoved':
                path = payload['path']
                file_type = payload['type']
                if file_type[0] == 'machinecode':
                    self._files_del_gcode_file(path)
            elif event_type == 'FileSelected':
                path = payload['path']
                self.selectedFile.emit(path)
                self._selected_file = path
            elif event_type == 'FileDeselected':
                self.selectedFile.emit("")
                self._selected_file = ""
            elif event_type == 'FolderAdded':
                path = payload['path']
                self._files_add_dir(path)
            elif event_type == 'FolderRemoved':
                path = payload['path']
                self._files_del_dir(path)
            elif event_type == 'MetadataAnalysisFinished':
                path = payload['path']
                result = payload['result']
                self._files_set_meta(path, result)

    def _get_dir_and_name(self, path):
        p = path.split('/')
        n = len(p)
        if n == 0:
            logging.error("invalid path: %s", path)
            return None, None
        elif n == 1:
            return self._files, p[0]
        else:
            node = self._files
            for name in p[:-1]:
                node = node.get_child_by_name(name)
                if node is None:
                    logging.error("invalid path: %s", path)
                    return None, None
            return node, p[-1]

    def _files_add_gcode_file(self, path):
        dir_node, name = self._get_dir_and_name(path)
        if dir_node:
            logging.info("add file %s to %r", name, dir_node)
            dir_node.add_child(FileGCode(name))
            self.addedFile.emit(path)
            self.updateFileSet.emit(self._files)
        else:
            logging.error("invalid add file %s", path)

    def _files_set_meta(self, path, meta):
        dir_node, name = self._get_dir_and_name(path)
        if dir_node:
            node = dir_node.get_child_by_name(name)
            if node:
                pa = meta['printingArea']
                sxi = pa['minX']
                sxa = pa['maxX']
                syi = pa['minY']
                sya = pa['maxY']
                szi = pa['minZ']
                sza = pa['maxZ']
                meta = FileMeta((sxi, sxa), (syi, sya), (szi, sza))
                node.meta = meta
                self._meta_cache[path] = meta
                logging.info("set meta data: %s: %s", path, meta)
            else:
                logging.error("invaid node: %s", path)
        else:
            logging.error("invalid node: %s", path)

    def _files_del_gcode_file(self, path):
        dir_node, name = self._get_dir_and_name(path)
        if dir_node:
            if dir_node.remove_child_by_name(name):
                logging.info("del file %s in %r", name, dir_node)
                self.removedFile.emit(path)
                self.updateFileSet.emit(self._files)
                # remove file from cache
                if path in self._meta_cache:
                    del self._meta_cache[path]
            else:
                logging.error("can't remove file %s", path)
        else:
            logging.error("invalid del file %s", path)

    def _files_add_dir(self, path):
        dir_node, name = self._get_dir_and_name(path)
        if dir_node:
            logging.info("add dir %s to %r", name, dir_node)
            dir_node.add_child(FileDir(name))
            self.addedFolder.emit(path)
            self.updateFileSet.emit(self._files)
        else:
            logging.error("invalid add dir %s", path)

    def _files_del_dir(self, path):
        dir_node, name = self._get_dir_and_name(path)
        if dir_node:
            if dir_node.remove_child_by_name(name):
                logging.info("del dir %s in %r", name, dir_node)
                self.removedFolder.emit(path)
                self.updateFileSet.emit(self._files)
            else:
                logging.error("can't remove dir %s", path)
        else:
            logging.error("invalid del dir %s", path)

    def _convert_file_children(self, data, node):
        for item in data:
            item_type = item['type']
            name = item['display']
            if item_type == "folder":
                new_node = FileDir(name)
                self._convert_file_children(item['children'], new_node)
                node.add_child(new_node)
            elif item_type == "machinecode":
                new_node = FileGCode(name)
                node.add_child(new_node)
