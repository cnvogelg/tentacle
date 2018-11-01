from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class JobData:
  def __init__(self, user, file, size, est_time, fl0, fl1):
    self.user = user
    self.file = file
    self.size = size
    self.est_time = est_time
    self.fl0 = fl0
    self.fl1 = fl1


class ProgressData:
  def __init__(self, completion, file_pos, time, time_left, left_origin):
    self.completion = completion
    self.file_pos = file_pos
    self.time = time
    self.time_left = time_left
    self.left_origin = left_origin


class TempData:
  def __init__(self, time, bed, tool0, tool1):
    self.time = time
    self.bed = bed
    self.tool0 = tool0
    self.tool1 = tool1


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
  updateJob = pyqtSignal(JobData)
  updateStateText = pyqtSignal(str)
  updateProgress = pyqtSignal(ProgressData)
  updateTemps = pyqtSignal(TempData)

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
    client.history.connect(self.on_history)

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
    if 'temps' in data:
      self._update_temps(data['temps'])

  @pyqtSlot(dict)
  def on_history(self, data):
    if 'temps' in data:
      self._update_temps(data['temps'])

  def _update_job(self, job):
    dirty = self._job.update(job)
    if dirty:
      jd = JobData(self._job.user, self._job.file, self._job.size,
                   self._job.estTime, self._job.fl0, self._job.fl1)
      self.updateJob.emit(jd)

  def _update_progress(self, progress):
    dirty = self._progress.update(progress)
    if dirty:
      p = self._progress
      pd = ProgressData(p.completion, p.filepos,
                        p.time, p.timeLeft, p.leftOrigin)
      self.updateProgress.emit(pd)

  def _update_state(self, state):
    if 'text' in state:
      txt = state['text']
      if txt != self._state_text:
        self._state_text = txt
        self.updateStateText.emit(txt)

  def _update_temps(self, temps):
    for t in temps:
      ts = t['time']
      bed = self._get_temp_tuple(t, 'bed')
      tool0 = self._get_temp_tuple(t, 'tool0')
      tool1 = self._get_temp_tuple(t, 'tool1')
      self.updateTemps.emit(TempData(ts, bed, tool0, tool1))

  def _get_temp_tuple(self, t, what):
    actual = 0.0
    target = 0.0
    if what in t:
      d = t[what]
      if 'actual' in d:
        actual = d['actual']
      if 'target' in d:
        target = d['target']
    return actual, target
