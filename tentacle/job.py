from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, \
    QProgressBar, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSlot
from .util import ts_to_hms
from .model import JobData, ProgressData


class JobWidget(QWidget):
  def __init__(self, model):
    super().__init__()
    self._model = model
    self._model.updateJob.connect(self.on_updatedJob)
    self._model.updateProgress.connect(self.on_updateProgress)
    self._model.updateCurrentZ.connect(self.on_updateCurrentZ)
    # ui
    top_layout = QVBoxLayout()
    self.setLayout(top_layout)
    grid_layout = QGridLayout()
    top_layout.addLayout(grid_layout)
    grid_layout.setColumnStretch(1, 10)
    grid_layout.setColumnStretch(2, 10)
    # job
    self._l_user = QLabel(self)
    self._l_file_name = QLabel(self)
    self._l_f0 = QLabel(self)
    self._l_f1 = QLabel(self)
    self._l_file_size = QLabel(self)
    self._l_current_z = QLabel(self)
    grid_layout.addWidget(QLabel("File"), 0, 0)
    grid_layout.addWidget(self._l_file_name, 0, 1)
    grid_layout.addWidget(self._l_user, 0, 2)
    grid_layout.addWidget(QLabel("Filament"), 1, 0)
    grid_layout.addWidget(self._l_f0, 1, 1)
    grid_layout.addWidget(self._l_f1, 1, 2)
    grid_layout.addWidget(QLabel("CurrentZ"), 2, 0)
    grid_layout.addWidget(self._l_current_z, 2, 1)
    # progress
    self._l_time = QLabel(self)
    self._l_time_left = QLabel(self)
    self._l_left_origin = QLabel(self)
    self._l_file_pos = QLabel(self)
    grid_layout.addWidget(self._l_left_origin, 2, 2)
    grid_layout.addWidget(QLabel("Time"), 3, 0)
    grid_layout.addWidget(self._l_time, 3, 1)
    grid_layout.addWidget(self._l_time_left, 3, 2)
    grid_layout.addWidget(QLabel("Size"), 4, 0)
    grid_layout.addWidget(self._l_file_pos, 4, 1)
    grid_layout.addWidget(self._l_file_size, 4, 2)
    # progress bar
    hb = QHBoxLayout()
    top_layout.addLayout(hb)
    self._b_cancel = QPushButton("Cancel")
    hb.addWidget(self._b_cancel)
    self._p_completion = QProgressBar(self)
    self._p_completion.setRange(0, 100)
    hb.addWidget(self._p_completion)
    self._b_pause = QPushButton("Pause")
    hb.addWidget(self._b_pause)

  @pyqtSlot(JobData)
  def on_updatedJob(self, data):
    self._l_user.setText("@" + data.user)
    self._l_file_name.setText(data.file)
    self._l_file_size.setText(str(data.size))
    self._l_f0.setText("%3.2f" % data.fl0)
    self._l_f1.setText("%3.2f" % data.fl1)

  @pyqtSlot(ProgressData)
  def on_updateProgress(self, data):
    self._p_completion.setValue(int(data.completion))
    hms = ts_to_hms(data.time)
    self._l_time.setText("%02d:%02d:%02d" % hms)
    hms = ts_to_hms(data.time_left)
    self._l_time_left.setText("%02d:%02d:%02d" % hms)
    self._l_left_origin.setText(data.left_origin)
    self._l_file_pos.setText(str(data.file_pos))

  @pyqtSlot(float)
  def on_updateCurrentZ(self, z):
    if z < 0.0:
      self._l_current_z.setText("N/A")
    else:
      self._l_current_z.setText(str(z))
