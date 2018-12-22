"""Main App Window."""

import logging
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLabel
from PyQt5.QtCore import Qt

from tentacle.client import DataModel, FileModel
from tentacle.ui import (
    MoveWidget, FilesWidget, JobWidget, TempWidget, GCodeWidget
)


class App(QMainWindow):
    """Main Application Window of Tentacle."""

    tabs = (
        ("File", FilesWidget),
        ("Job", JobWidget),
        ("Temp", TempWidget),
        ("Move", MoveWidget),
        ("GCode", GCodeWidget)
    )

    def __init__(self, octo_client, cfg):
        """Create main window."""
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle("tentacle")

        self._setup_status()
        self._setup_client(octo_client)

        self.table_widget = QTabWidget(self)
        self._setup_tabs()
        self.setCentralWidget(self.table_widget)

    def keyPressEvent(self, event):
        """Handle key presses."""
        if event.key() == Qt.Key_Escape:
            logging.error("<Esc> pressed... quitting")
            self.close()

    def closeEvent(self, event):
        """Handle close event of Window."""
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
        self._data_model.updateState.connect(self._l_status.setText)
        self._data_model.waitTemp.connect(self._wait_temp)
        self._file_model = FileModel()
        self._file_model.attach(octo_client)
        self._data_model.files = self._file_model
        self._octo_client.error.connect(self._status_bar.showMessage)
        self._octo_client.start()

    def _setup_tabs(self):
        self._tab_widgets = {}
        for name, cls in self.tabs:
            w = cls(self._data_model, self._octo_client)
            # do we have a config
            cfg_name = name.lower()
            if cfg_name in self.cfg and hasattr(w, "configure"):
                w.configure(self.cfg[cfg_name])
            self._tab_widgets[name] = w
            self.table_widget.addTab(w, name)
        self.table_widget.setCurrentWidget(self._tab_widgets["Job"])

    def _setup_status(self):
        self._status_bar = QStatusBar()
        self._l_status = QLabel("Mode")
        self._status_bar.addPermanentWidget(self._l_status)
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Welcome to tentacle!", 2000)

    def _wait_temp(self, waiting):
        if waiting:
            self._l_status.setText("Wait Temp")
        else:
            self._l_status.setText("Printing")
