"""Job tab."""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QProgressBar,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtCore import pyqtSlot, Qt

from tentacle.util import ts_to_hms
from tentacle.client import JobData, ProgressData, TempData


class JobWidget(QWidget):
    """Job tab shows the current printing job."""

    def __init__(self, model, client):
        """Create a new Job tab."""
        super().__init__()
        self._model = model
        self._client = client
        self._model.updateJob.connect(self.on_updatedJob)
        self._model.updateProgress.connect(self.on_updateProgress)
        self._model.updateCurrentZ.connect(self.on_updateCurrentZ)
        self._model.updateState.connect(self.on_updateState)
        self._model.updateTemps.connect(self.on_updateTemps)
        # ui
        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(top_layout)
        # table
        self._table = QTableWidget(self)
        t = self._table
        t.setRowCount(6)
        t.setColumnCount(3)
        th = t.horizontalHeader()
        th.hide()
        th.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tv = t.verticalHeader()
        tv.hide()
        tv.setSectionResizeMode(QHeaderView.ResizeToContents)
        t.setEditTriggers(t.NoEditTriggers)
        t.setSelectionMode(t.NoSelection)
        t.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        t.setFocusPolicy(Qt.NoFocus)
        top_layout.addWidget(self._table, 10, Qt.AlignHCenter)
        # fill table
        self._l_user = QTableWidgetItem()
        self._l_file_name = QTableWidgetItem()
        self._l_f0 = QTableWidgetItem()
        self._l_f1 = QTableWidgetItem()
        self._l_file_size = QTableWidgetItem()
        self._l_current_z = QTableWidgetItem()
        t.setItem(0, 0, QTableWidgetItem("File"))
        t.setItem(0, 1, self._l_file_name)
        t.setItem(0, 2, self._l_user)
        t.setItem(1, 0, QTableWidgetItem("Filament"))
        t.setItem(1, 1, self._l_f0)
        t.setItem(1, 2, self._l_f1)
        t.setItem(2, 0, QTableWidgetItem("CurrentZ"))
        t.setItem(2, 1, self._l_current_z)
        # progress
        self._l_time = QTableWidgetItem()
        self._l_time_left = QTableWidgetItem()
        self._l_file_pos = QTableWidgetItem()
        t.setItem(3, 0, QTableWidgetItem("Time"))
        t.setItem(3, 1, self._l_time)
        t.setItem(3, 2, self._l_time_left)
        t.setItem(4, 0, QTableWidgetItem("Size"))
        t.setItem(4, 1, self._l_file_pos)
        t.setItem(4, 2, self._l_file_size)
        # temp
        self._l_t0 = QTableWidgetItem()
        self._l_t1 = QTableWidgetItem()
        t.setItem(5, 0, QTableWidgetItem("Temps"))
        t.setItem(5, 1, self._l_t0)
        t.setItem(5, 2, self._l_t1)
        # progress bar with control buttons
        hb = QHBoxLayout()
        hb.setContentsMargins(0, 0, 0, 0)
        top_layout.addLayout(hb)
        self._b_cancel = QPushButton("Cancel")
        self._b_cancel.clicked.connect(self.on_cancel)
        hb.addWidget(self._b_cancel)
        self._p_completion = QProgressBar(self)
        self._p_completion.setRange(0, 100)
        hb.addWidget(self._p_completion)
        self._b_pause = QPushButton("Pause")
        self._b_pause.clicked.connect(self.on_pause)
        hb.addWidget(self._b_pause)

    @pyqtSlot(JobData)
    def on_updatedJob(self, data):
        """React on changes in job parameters."""
        self._l_user.setText("@" + data.user)
        self._l_file_name.setText(data.file)
        self._l_file_size.setText(str(data.size))
        self._l_f0.setText("%3.2f" % data.fl0)
        self._l_f1.setText("%3.2f" % data.fl1)

    @pyqtSlot(ProgressData)
    def on_updateProgress(self, data):
        """React on changes in progress."""
        self._p_completion.setValue(int(data.completion))
        hms = ts_to_hms(data.time)
        self._l_time.setText("%02d:%02d:%02d" % hms)
        hms = ts_to_hms(data.time_left)
        txt = "%02d:%02d:%02d" % hms
        orig = data.left_origin[0:3]
        self._l_time_left.setText("%s  (%s)" % (txt, orig))
        self._l_file_pos.setText(str(data.file_pos))

    @pyqtSlot(float)
    def on_updateCurrentZ(self, z):
        """React on Z axis change."""
        if z < 0.0:
            self._l_current_z.setText("N/A")
        else:
            self._l_current_z.setText(str(z))

    @pyqtSlot(TempData)
    def on_updateTemps(self, data):
        """Handle Temp Update."""
        t0 = data.tool0
        t1 = data.tool1
        txt0 = "%6.2f / %6.2f" % t0
        txt1 = "%6.2f / %6.2f" % t1
        self._l_t0.setText(txt0)
        self._l_t1.setText(txt1)

    @pyqtSlot(str)
    def on_updateState(self, state):
        """React on state change."""
        on = state == "Printing"
        self._b_cancel.setEnabled(on)
        on = state in ("Printing", "Paused")
        self._b_pause.setEnabled(on)

    @pyqtSlot()
    def on_cancel(self):
        """Handle Cancel Button."""
        self._client.job_cancel()

    @pyqtSlot()
    def on_pause(self):
        """Hanle Pause Button."""
        self._client.job_pause()
