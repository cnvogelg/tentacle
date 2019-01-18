"""Main App Window."""

import logging

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QLabel, QMenu, QPushButton
)
from PyQt5.QtCore import Qt, QPoint

from tentacle.client import DataModel, FileModel
from tentacle.ui import (
    MoveWidget, FilesWidget, JobWidget, TempWidget, GCodeWidget,
    CameraWidget, SerialWidget, ToolWidget
)
from .cmds import Commands


class App(QMainWindow):
    """Main Application Window of Tentacle."""

    tabs = (
        ("File", FilesWidget),
        ("Job", JobWidget),
        ("Temp", TempWidget),
        ("Tool", ToolWidget),
        ("Move", MoveWidget),
        ("GCode", GCodeWidget),
        ("Cam", CameraWidget),
        ("Ser", SerialWidget)
    )

    def __init__(self, octo_client, cfg):
        """Create main window."""
        super().__init__()
        self.cfg = cfg
        self._cmds = Commands(cfg)

        self.setWindowTitle("tentacle")

        self._setup_status()
        self._setup_client(octo_client)

        self.table_widget = QTabWidget(self)
        self._setup_tabs()
        self.setCentralWidget(self.table_widget)

        self._screen_no = 0

    def keyPressEvent(self, event):
        """Handle key presses."""
        key = event.key()
        if key == Qt.Key_Escape:
            self._handle_menu()
        elif key == Qt.Key_Up:
            self._cmds.backlight_on()
        elif key == Qt.Key_Down:
            self._cmds.backlight_off()
        elif key == Qt.Key_Space:
            self._screenshot()

    def _handle_menu(self):
        # ensure that we see something
        self._cmds.backlight_on()
        # build menu
        menu = QMenu(self)
        toggle_act = menu.addAction("Toggle Backlight")
        restart_act = menu.addAction("Restart OctoPrint")
        menu.addSeparator()
        reboot_act = menu.addAction("Reboot System")
        poweroff_act = menu.addAction("Power off System")
        menu.addSeparator()
        quit_act = menu.addAction("Quit Tentacle")
        menu.setActiveAction(quit_act)
        x = (self.width() - menu.width()) // 2
        y = (self.height() - menu.height()) // 2
        action = menu.exec_(QPoint(x, y))
        if action == quit_act:
            logging.error("quitting...")
            self.close()
        elif action == toggle_act:
            self._cmds.backlight_toggle()
        elif action == restart_act:
            self._cmds.restart_octoprint()
        elif action == reboot_act:
            self._cmds.reboot_system()
        elif action == poweroff_act:
            self._cmds.poweroff_system()

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
        self._b_menu = QPushButton("\u2630")
        self._b_menu.clicked.connect(self._handle_menu)
        self._status_bar.addPermanentWidget(self._l_status)
        self._status_bar.addPermanentWidget(self._b_menu)
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Welcome to tentacle!", 2000)

    def _wait_temp(self, waiting):
        if waiting:
            self._l_status.setText("Wait Temp")
        else:
            self._l_status.setText("Printing")

    def _screenshot(self):
        pixmap = self.grab()
        file_name = "tentacle-grab-%03d.png" % self._screen_no
        pixmap.save(file_name)
        logging.info("saved screenshot '%s'", file_name)
        self._screen_no += 1
