"""Process OctoPrint Data Model and Emit Python Model Objects."""

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
    updateBusyFiles = pyqtSignal(object)
    addSerialLog = pyqtSignal(str)
    waitTemp = pyqtSignal(bool)

    def __init__(self):
        """Create a new DataModel instance."""
        super().__init__()
        self._is_connected = False
        self._job = JobModel()
        self._state_text = ""
        self._progress = ProgressModel()
        self._currentZ = -1.0
        self._wait_temp = False
        self._busy_files = None

    def attach(self, client):
        """Attach data model to octo client."""
        client.connected.connect(self.on_connect)
        client.current.connect(self.on_current)
        client.error.connect(self.on_error)
        client.history.connect(self.on_history)

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
        if "logs" in data:
            self._parse_logs(data['logs'])
        if "busyFiles" in data:
            self._update_busy_files(data['busyFiles'])

    @pyqtSlot(dict)
    def on_history(self, data):
        """React on 'history' event."""
        if "temps" in data:
            self._update_temps(data["temps"])
        if "logs" in data:
            self._parse_logs(data['logs'])

    def _update_busy_files(self, busy_files):
        file_list = []
        for entry in busy_files:
            # local files for now
            if entry['origin'] == 'local':
                file_list.append(entry['path'])
        if file_list != self._busy_files:
            self._busy_files = file_list
            self.updateBusyFiles.emit(self._busy_files)

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

    def _parse_logs(self, logs):
        for entry in logs:
            if entry.startswith("Send: "):
                line = entry[6:]
                gcode = self._sanitize_gcode(line)
                if gcode:
                    self.addSerialLog.emit(gcode)
                    self._handle_temp_wait(gcode)

    def _handle_temp_wait(self, gcode):
        # wait temp?
        if gcode.startswith('M109'):
            if not self._wait_temp:
                self._wait_temp = True
                self.waitTemp.emit(True)
        else:
            if self._wait_temp:
                self._wait_temp = False
                self.waitTemp.emit(False)

    def _sanitize_gcode(self, line):
        # skip line number
        if line[0] == 'N':
            pos = line.find(' ')
            line = line[pos+1:]
        # skip checksum
        pos = line.rfind('*')
        if pos != -1:
            line = line[0:pos]
        # ignore temp calls
        if line == 'M105':
            return None
        # ignore messages
        if line.startswith('M117'):
            return None
        return line
