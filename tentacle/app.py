"""Main App Window."""

import subprocess
import logging

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QLabel, QMenu
)
from PyQt5.QtCore import Qt, QPoint

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
        self._reboot_cmd = None
        self._restart_cmd = None
        self._backlight_on_cmd = None
        self._backlight_off_cmd = None
        self._backlight = False
        self._configure(cfg)

        self.setWindowTitle("tentacle")

        self._setup_status()
        self._setup_client(octo_client)

        self.table_widget = QTabWidget(self)
        self._setup_tabs()
        self.setCentralWidget(self.table_widget)
        self._backlight_on()

    def _configure(self, cfg):
        if 'menu' in cfg:
            menu = cfg['menu']
            if 'restart' in menu:
                self._restart_cmd = menu['restart']
            if 'reboot' in menu:
                self._reboot_cmd = menu['reboot']
        if 'backlight' in cfg:
            bl = cfg['backlight']
            if 'on' in bl:
                self._backlight_on_cmd = bl['on']
            if 'off' in bl:
                self._backlight_off_cmd = bl['off']

    def keyPressEvent(self, event):
        """Handle key presses."""
        key = event.key()
        if key == Qt.Key_Escape:
            self._backlight_on()
            self._handle_menu()
        elif key == Qt.Key_Up:
            self._backlight_on()
        elif key == Qt.Key_Down:
            self._backlight_off()

    def _handle_menu(self):
        menu = QMenu(self)
        restart_act = menu.addAction("Restart OctoPrint")
        reboot_act = menu.addAction("Reboot System")
        quit_act = menu.addAction("Quit Tentacle")
        menu.setActiveAction(quit_act)
        x = (self.width() - menu.width()) // 2
        y = (self.height() - menu.height()) // 2
        action = menu.exec_(QPoint(x, y))
        if action == quit_act:
            logging.error("quitting...")
            self.close()
        elif action == restart_act:
            logging.info("restarting...")
            self._run_cmd(self._restart_cmd)
        elif action == reboot_act:
            logging.info("rebooting...")
            self._run_cmd(self._reboot_cmd)

    def _run_cmd(self, cmd):
        if cmd:
            args = cmd.split()
            ret = subprocess.call(args)
            if ret == 0:
                logging.info("run_cmd: %r", args)
            else:
                logging.error("run_cmd: %r -> %d", args, ret)
            return ret
        else:
            return 0

    def _backlight_on(self):
        if not self._backlight:
            ret = self._run_cmd(self._backlight_on_cmd)
            logging.info("backlight on: ret=%d", ret)
            if ret == 0:
                self._backlight = True
        else:
            logging.info("backlight already on!")

    def _backlight_off(self):
        if self._backlight:
            ret = self._run_cmd(self._backlight_off_cmd)
            logging.info("backlight off: ret=%d", ret)
            if ret == 0:
                self._backlight = False
        else:
            logging.info("backlight already off!")

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
