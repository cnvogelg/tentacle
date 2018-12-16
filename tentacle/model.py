"""Process OctoPrint Data Model and Emit Python Model Objects."""

import logging

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class JobData:
    """Represent Jobs."""

    def __init__(self, user, file, size, est_time, fl0, fl1):
        """Create a new JobData."""
        self.user = user
        self.file = file
        self.size = size
        self.est_time = est_time
        self.fl0 = fl0
        self.fl1 = fl1


class ProgressData:
    """Progress Data."""

    def __init__(self, completion, file_pos, time, time_left, left_origin):
        """Create a new ProgressData."""
        self.completion = completion
        self.file_pos = file_pos
        self.time = time
        self.time_left = time_left
        self.left_origin = left_origin


class TempData:
    """Temperature Data."""

    def __init__(self, time, bed, tool0, tool1):
        """Create a new TempData."""
        self.time = time
        self.bed = bed
        self.tool0 = tool0
        self.tool1 = tool1


class SubModel:
    """Build a Model with attributes specified in a def dict."""

    def __init__(self, model_def):
        """Create a new model and create attributes."""
        # init model
        self._model = model_def
        for entry in model_def:
            var, _, _, default = entry
            setattr(self, var, default)

    def __repr__(self):
        """Dump a sub model."""
        entries = {}
        for entry in self._model:
            var = entry[0]
            val = getattr(self, var)
            entries[var] = val
        return "%s(%r)" % (self.__class__.__name__, entries)

    def update(self, obj):
        """Update model with values stored in a dict object."""
        dirty = False
        for entry in self._model:
            var, path, vtyp, default = entry
            value = vtyp(self._lookup(obj, path, default))
            old_value = getattr(self, var)
            if value != old_value:
                dirty = True
                setattr(self, var, value)
        return dirty

    def _lookup(self, obj, path, default):
        if isinstance(path, str):
            if path in obj:
                val = obj[path]
                if val is None:
                    return default
                else:
                    return val
            else:
                return default
        else:
            for p in path:
                if p in obj:
                    obj = obj[p]
                else:
                    return default
                if obj is None:
                    return default
            return obj


class JobModel(SubModel):
    """A Job Model."""

    def __init__(self):
        """Create a JobModel."""
        model = [
            ("user", "user", str, ""),
            ("file", ("file", "display"), str, ""),
            ("path", ("file", "path"), str, ""),
            ("size", ("file", "size"), int, 0),
            ("estTime", ("estimatedPrintTime"), float, 0.0),
            ("fl0", ("filament", "tool0", "length"), float, 0.0),
            ("fl1", ("filament", "tool1", "length"), float, 0.0),
        ]
        super().__init__(model)


class ProgressModel(SubModel):
    """A ProgressModel."""

    def __init__(self):
        """Create a ProgressModel."""
        model = [
            ("completion", "completion", float, 0.0),
            ("filepos", "filepos", int, 0),
            ("time", "printTime", float, 0.0),
            ("timeLeft", "printTimeLeft", float, 0.0),
            ("leftOrigin", "printTimeLeftOrigin", str, ""),
        ]
        super().__init__(model)


class FileDir:
    """File system directory."""

    def __init__(self, name):
        """Create a file system directory."""
        self.name = name
        self.childs = []
        self.parent = None

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
        super().__init__("<Root>")
        self.total = total
        self.free = free

    def __repr__(self):
        """Dump root."""
        return "Root(total=%d,free=%d,%r)" % (
            self.total, self.free, self.childs)


class FileGCode:
    """A GCode File."""

    def __init__(self, name):
        """Create a GCode File."""
        self.name = name
        self.parent = None

    def __repr__(self):
        """Represent gcode file."""
        return "FileGCode(%s)" % self.name


class DataModel(QObject):
    """The DataModel instance sends out signals on data change."""

    connected = pyqtSignal(str)
    disconnected = pyqtSignal(str)
    # user, file, est_print_time, tool0_fil, tool1_fil
    updateJob = pyqtSignal(JobData)
    updateState = pyqtSignal(str)
    updateProgress = pyqtSignal(ProgressData)
    updateTemps = pyqtSignal(TempData)
    updateCurrentZ = pyqtSignal(float)
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
        self._is_connected = False
        self._job = JobModel()
        self._state_text = ""
        self._progress = ProgressModel()
        self._currentZ = -1.0
        self._selected_file = ""
        self._files = None

    def attach(self, client):
        """Attach data model to octo client."""
        client.connected.connect(self.on_connect)
        client.current.connect(self.on_current)
        client.error.connect(self.on_error)
        client.history.connect(self.on_history)
        client.file_set.connect(self.on_file_set)
        client.event.connect(self.on_event)

    @pyqtSlot(dict)
    def on_connect(self, data):
        """React on connection."""
        self._is_connected = True
        version = data["version"]
        self.connected.emit("Connected (%s)" % version)

    @pyqtSlot(str)
    def on_error(self, msg):
        """React on error."""
        self._is_connected = False
        self.disconnected.emit("ERROR: " + msg)
        self.updateState.emit("Disconnected")

    @pyqtSlot(dict)
    def on_current(self, data):
        """React on new 'current' event."""
        if "job" in data:
            self._update_job(data["job"])
        if "state" in data:
            self._update_state(data["state"])
        if "progress" in data:
            self._update_progress(data["progress"])
        if "temps" in data:
            self._update_temps(data["temps"])
        if "currentZ" in data:
            currentZ = data["currentZ"]
            if currentZ is None:
                currentZ = -1.0
            if currentZ != self._currentZ:
                self._currentZ = currentZ
                self.updateCurrentZ.emit(currentZ)

    @pyqtSlot(dict)
    def on_history(self, data):
        """React on 'history' event."""
        if "temps" in data:
            self._update_temps(data["temps"])

    @pyqtSlot(dict)
    def on_file_set(self, data):
        """React on initial files set."""
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

    def _files_del_gcode_file(self, path):
        dir_node, name = self._get_dir_and_name(path)
        if dir_node:
            if dir_node.remove_child_by_name(name):
                logging.info("del file %s in %r", name, dir_node)
                self.removedFile.emit(path)
                self.updateFileSet.emit(self._files)
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

    def _update_job(self, job):
        dirty = self._job.update(job)
        if dirty:
            # pylint: disable=E1101
            jd = JobData(
                self._job.user,
                self._job.file,
                self._job.size,
                self._job.estTime,
                self._job.fl0,
                self._job.fl1,
            )
            self.updateJob.emit(jd)
            # update selected file
            file_path = self._job.path
            if file_path != self._selected_file:
                self._selected_file = file_path
                self.selectedFile.emit(file_path)

    def _update_progress(self, progress):
        dirty = self._progress.update(progress)
        if dirty:
            p = self._progress
            # pylint: disable=E1101
            pd = ProgressData(
                p.completion,
                p.filepos,
                p.time,
                p.timeLeft,
                p.leftOrigin)
            self.updateProgress.emit(pd)

    def _update_state(self, state):
        if "text" in state:
            txt = state["text"]
            if txt != self._state_text:
                self._state_text = txt
                self.updateState.emit(txt)

    def _update_temps(self, temps):
        for t in temps:
            ts = t["time"]
            bed = self._get_temp_tuple(t, "bed")
            tool0 = self._get_temp_tuple(t, "tool0")
            tool1 = self._get_temp_tuple(t, "tool1")
            self.updateTemps.emit(TempData(ts, bed, tool0, tool1))

    def _get_temp_tuple(self, t, what):
        actual = 0.0
        target = 0.0
        if what in t:
            d = t[what]
            if "actual" in d:
                actual = d["actual"]
            if "target" in d:
                target = d["target"]
        return actual, target
