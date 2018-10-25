import sys
import pprint
import logging
from PyQt5.QtWidgets import QMainWindow, QTabWidget
from PyQt5.QtCore import Qt, pyqtSlot

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
    self.setGeometry(0, 0, 320, 240)

    self.table_widget = QTabWidget(self)
    self._setup_tabs()
    self.setCentralWidget(self.table_widget)

    self._setup_client(octo_client)
    self._welcome()

  def keyPressEvent(self, event):
    if event.key() == Qt.Key_Escape:
      logging.info("<Esc> pressed... quitting")
      self.close()

  def closeEvent(self, event):
    logging.info("closing app")
    self._octo_client.stop()
    event.accept()
    logging.info("done closing app")

  def _setup_client(self, octo_client):
    self._octo_client = octo_client
    self._octo_client.connected.connect(self._on_octo_connected)
    self._octo_client.error.connect(self._on_octo_error)
    self._octo_client.current.connect(self._on_octo_current)
    self._octo_client.start()

  def _setup_tabs(self):
    self._tab_widgets = {}
    for name, cls in self.tabs:
      w = cls()
      self._tab_widgets[name] = w
      self.table_widget.addTab(w, name)
    self.table_widget.setCurrentWidget(self._tab_widgets['Job'])

  def _welcome(self):
    self.statusBar().showMessage("Welcome to tentacle!")

  @pyqtSlot(dict)
  def _on_octo_connected(self, event):
    version = event['version']
    self.statusBar().showMessage("Connected: %s" % version)

  @pyqtSlot(str)
  def _on_octo_error(self, error):
    self.statusBar().showMessage("Error: %s" % error)

  @pyqtSlot(dict)
  def _on_octo_current(self, event):
    pprint.pprint(event)
