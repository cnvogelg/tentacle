"""The serial tab."""

import time

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PyQt5.QtGui import QFont


class SerialWidget(QWidget):
    """A serial widget."""

    def __init__(self, model, client):
        """Create camera widget."""
        super().__init__()
        # receive temps
        self._model = model
        self._client = client
        self._model.addSerialLog.connect(self._on_add_serial_log)
        # ui
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        self.setLayout(layout)
        self._w_log = QPlainTextEdit()
        self._w_log.setReadOnly(True)
        self._w_log.setFont(QFont("Courier", 8))
        self._w_log.setMaximumBlockCount(1000)
        layout.addWidget(self._w_log, 100)

    def configure(self, cfg):
        """Configure widget from config file."""

    def _on_add_serial_log(self, line):
        t = time.time()
        tstr = time.strftime("%H:%M:%S", time.localtime(t))
        ms = int(t * 1000) % 1000
        txt = "%s.%03d: %s" % (tstr, ms, line)
        self._w_log.appendPlainText(txt)
