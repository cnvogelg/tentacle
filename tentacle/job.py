from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QProgressBar
from PyQt5.QtCore import pyqtSlot
from .util import ts_to_hms


class JobWidget(QWidget):
  def __init__(self, model):
    super(QWidget, self).__init__()
    self._model = model
    self._model.updateJob.connect(self.on_updatedJob)
    self._model.updateProgress.connect(self.on_updateProgress)
    # ui
    self._layout = QGridLayout()
    self._layout.setColumnStretch(1, 10)
    self._layout.setColumnStretch(2, 10)
    self.setLayout(self._layout)
    # job
    self._l_user = QLabel(self)
    self._l_file_name = QLabel(self)
    self._l_time_est = QLabel(self)
    self._l_f0 = QLabel(self)
    self._l_f1 = QLabel(self)
    self._l_file_size = QLabel(self)
    self._layout.addWidget(QLabel("File"), 0, 0)
    self._layout.addWidget(self._l_file_name, 0, 1)
    self._layout.addWidget(self._l_user, 0, 2)
    self._layout.addWidget(QLabel("Filament"), 1, 0)
    self._layout.addWidget(self._l_f0, 1, 1)
    self._layout.addWidget(self._l_f1, 1, 2)
    self._layout.addWidget(QLabel("Est.Time"), 2, 0)
    self._layout.addWidget(self._l_time_est, 2, 1)
    # progress
    self._p_completion = QProgressBar(self)
    self._p_completion.setRange(0, 100)
    self._l_time = QLabel(self)
    self._l_time_left = QLabel(self)
    self._l_left_origin = QLabel(self)
    self._l_file_pos = QLabel(self)
    self._layout.addWidget(self._l_left_origin, 2, 2)
    self._layout.addWidget(QLabel("Time"), 3, 0)
    self._layout.addWidget(self._l_time, 3, 1)
    self._layout.addWidget(self._l_time_left, 3, 2)
    self._layout.addWidget(QLabel("Size"), 4, 0)
    self._layout.addWidget(self._l_file_pos, 4, 1)
    self._layout.addWidget(self._l_file_size, 4, 2)
    self._layout.addWidget(self._p_completion, 5, 0, 1, 3)

  @pyqtSlot(str, str, int, float, float, float)
  def on_updatedJob(self, user, file_name, file_size, est_print_time,
                    t0_fila, t1_fila):
    self._l_user.setText("@" + user)
    self._l_file_name.setText(file_name)
    self._l_file_size.setText(str(file_size))
    hms = ts_to_hms(est_print_time)
    self._l_time_est.setText("%02d:%02d:%02d" % hms)
    self._l_f0.setText("%3.2f" % t0_fila)
    self._l_f1.setText("%3.2f" % t1_fila)

  @pyqtSlot(float, int, float, float, str)
  def on_updateProgress(self, completion, file_pos, time, time_left,
                        left_origin):
    self._p_completion.setValue(int(completion))
    hms = ts_to_hms(time)
    self._l_time.setText("%02d:%02d:%02d" % hms)
    hms = ts_to_hms(time_left)
    self._l_time_left.setText("%02d:%02d:%02d" % hms)
    self._l_left_origin.setText(left_origin)
    self._l_file_pos.setText(str(file_pos))
