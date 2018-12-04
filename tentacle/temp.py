from PyQt5.QtCore import pyqtSlot, QMargins, QDateTime
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter
from PyQt5.QtChart import QLineSeries, QChartView, QValueAxis, QDateTimeAxis
from .model import TempData


class TempWidget(QWidget):
  def __init__(self, model, x_range=10):
    super(QWidget, self).__init__()
    self._x_range = x_range * 60 # in seconds
    self._x_begin = 0
    # ui
    self._layout = QVBoxLayout()
    self._layout.setContentsMargins(0, 0, 0, 0)
    self.setLayout(self._layout)
    self._chart_view = QChartView()
    self._chart_view.setRenderHint(QPainter.Antialiasing)
    self._layout.addWidget(self._chart_view)
    # chart
    chart = self._chart_view.chart()
    self._setup_chart(chart)
    # model connections
    self._model = model
    self._model.updateTemps.connect(self.on_updateTemps)

  def _setup_chart(self, chart):
    self._ref_time = None
    self._datas = []
    chart.setBackgroundRoundness(0)
    chart.setMargins(QMargins(0, 0, 0, 0))
    chart.legend().setVisible(False)
    self._axis_x = self._setup_axis_x()
    self._axis_y = self._setup_axis_y()
    for i in range(6):
      d = QLineSeries()
      if i < 3:
        p = d.pen()
        p.setWidth(1)
        d.setPen(p)
      self._datas.append(d)
      chart.addSeries(d)
      chart.setAxisX(self._axis_x, d)
      chart.setAxisY(self._axis_y, d)

  def _setup_axis_y(self):
    a = QValueAxis()
    a.setRange(0, 250)
    a.setTickCount(6)
    a.setMinorTickCount(4)
    a.setLabelFormat("%.0f")
    f = self.font()
    f.setPixelSize(8)
    a.setLabelsFont(f)
    a.setTitleVisible(False)
    return a

  def _setup_axis_x(self):
    a = QDateTimeAxis()
    a.setFormat("hh:mm:ss")
    f = self.font()
    f.setPixelSize(8)
    a.setLabelsFont(f)
    return a

  @pyqtSlot(TempData)
  def on_updateTemps(self, data):
    # time since epoch in seconds
    time = data.time
    # move range if necessary
    begin = time - self._x_range
    if begin > self._x_begin:
      self._x_begin = begin
      self._axis_x.setMin(QDateTime.fromMSecsSinceEpoch(begin * 1000))
      self._axis_x.setMax(QDateTime.fromMSecsSinceEpoch(time * 1000))
    # add new points (in ms resolution)
    time *= 1000
    d = self._datas
    d[0].append(time, data.bed[1])
    d[1].append(time, data.tool0[1])
    d[2].append(time, data.tool1[1])
    d[3].append(time, data.bed[0])
    d[4].append(time, data.tool0[0])
    d[5].append(time, data.tool1[0])
    # cleanup old points
    begin *= 1000
    for d in self._datas:
      while True:
        v = d.at(0)
        if v.x() < begin:
          d.remove(0)
        else:
          break
