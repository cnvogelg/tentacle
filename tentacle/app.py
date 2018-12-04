import sys
import pprint
import logging
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLabel
from PyQt5.QtCore import Qt, pyqtSlot

from .model import DataModel
from .control import ControlWidget
from .files import FilesWidget
from .job import JobWidget
from .temp import TempWidget


class App(QMainWindow):

  tabs = (
      ('Ctrl', ControlWidget),
      ('File', FilesWidget),
      ('Job', JobWidget),
      ('Temp', TempWidget)
  )

  def __init__(self, octo_client):
    super().__init__()
    self.setWindowTitle("tentacle")

    self._setup_status()
    self._setup_client(octo_client)

    self.table_widget = QTabWidget(self)
    self._setup_tabs()
    self.setCentralWidget(self.table_widget)

  def keyPressEvent(self, event):
    if event.key() == Qt.Key_Escape:
      logging.error("<Esc> pressed... quitting")
      self.close()

  def closeEvent(self, event):
    logging.info("closing app")
    self._octo_client.stop()
    event.accept()
    logging.info("done closing app")

  def _setup_client(self, octo_client):
    self._octo_client = octo_client
    self._data_model = DataModel()
    self._data_model.attach(octo_client)
    self._data_model.connected.connect(self._status_bar.showMessage)
    self._data_model.disconnected.connect(self._status_bar.showMessage)
    self._data_model.updateStateText.connect(self._l_status.setText)
    self._octo_client.start()

  def _setup_tabs(self):
    self._tab_widgets = {}
    for name, cls in self.tabs:
      w = cls(self._data_model)
      self._tab_widgets[name] = w
      self.table_widget.addTab(w, name)
    self.table_widget.setCurrentWidget(self._tab_widgets['Job'])

  def _setup_status(self):
    self._status_bar = QStatusBar()
    self._l_status = QLabel("Mode")
    self._status_bar.addPermanentWidget(self._l_status)
    self.setStatusBar(self._status_bar)
    self._status_bar.showMessage("Welcome to tentacle!", 2000)
