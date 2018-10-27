from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class SubModel:
  def __init__(self, model_def):
    # init model
    self._model = model_def
    for entry in model_def:
      var, path, vtyp, default = entry
      setattr(self, var, default)

  def update(self, obj):
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
    if type(path) is str:
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
  def __init__(self):
    model = [('user', 'user', str, ''),
             ('file', ('file', 'display'), str, ''),
             ('size', ('file', 'size'), int, 0),
             ('estTime', ('estimatedPrintTime'), float, 0.0),
             ('fl0', ('filament', 'tool0', 'length'), float, 0.0),
             ('fl1', ('filament', 'tool1', 'length'), float, 0.0)]
    super().__init__(model)


class ProgressModel(SubModel):
  def __init__(self):
    model = [('completion', 'completion', float, 0.0),
             ('filepos', 'filepos', int, 0),
             ('time', 'printTime', float, 0.0),
             ('timeLeft', 'printTimeLeft', float, 0.0),
             ('leftOrigin', 'printTimeLeftOrigin', str, '')]
    super().__init__(model)


class DataModel(QObject):

  connected = pyqtSignal(str)
  disconnected = pyqtSignal(str)
  # user, file, est_print_time, tool0_fil, tool1_fil
  updateJob = pyqtSignal(str, str, int, float, float, float)
  updateStateText = pyqtSignal(str)
  updateProgress = pyqtSignal(float, int, float, float, str)

  def __init__(self):
    super().__init__()
    self._is_connected = False
    self._job = JobModel()
    self._state_text = ''
    self._progress = ProgressModel()

  def attach(self, client):
    client.connected.connect(self.on_connect)
    client.current.connect(self.on_current)
    client.error.connect(self.on_error)

  @pyqtSlot(dict)
  def on_connect(self, data):
    self._is_connected = True
    version = data['version']
    self.connected.emit("Connected (%s)" % version)

  @pyqtSlot(str)
  def on_error(self, msg):
    self._is_connected = False
    self.disconnected.emit("ERROR: " + msg)

  @pyqtSlot(dict)
  def on_current(self, data):
    if 'job' in data:
      self._update_job(data['job'])
    if 'state' in data:
      self._update_state(data['state'])
    if 'progress' in data:
      self._update_progress(data['progress'])

  def _update_job(self, job):
    dirty = self._job.update(job)
    if dirty:
      self.updateJob.emit(self._job.user, self._job.file, self._job.size,
                          self._job.estTime, self._job.fl0, self._job.fl1)

  def _update_progress(self, progress):
    dirty = self._progress.update(progress)
    if dirty:
      p = self._progress
      self.updateProgress.emit(p.completion, p.filepos,
                               p.time, p.timeLeft, p.leftOrigin)

  def _update_state(self, state):
    if 'text' in state:
      txt = state['text']
      if txt != self._state_text:
        self._state_text = txt
        self.updateStateText.emit(txt)
