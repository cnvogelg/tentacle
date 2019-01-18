"""The serial tab."""

import time

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QHBoxLayout, QPushButton
)
from PyQt5.QtGui import QFont


class SerialWidget(QWidget):
    """A serial widget."""

    def __init__(self, model, client):
        """Create camera widget."""
        super().__init__()
        # receive temps
        self._model = model
        self._client = client
        self._model.sendRaw.connect(self._on_send_raw)
        self._model.recvRaw.connect(self._on_recv_raw)
        self._model.updateState.connect(self._on_update_state)
        # ui
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        self.setLayout(layout)
        self._w_log = QPlainTextEdit()
        self._w_log.setReadOnly(True)
        self._w_log.setMaximumBlockCount(1000)
        layout.addWidget(self._w_log, 100)
        # buttons
        hlayout = QHBoxLayout()
        layout.addLayout(hlayout)
        hlayout.setContentsMargins(0, 0, 0, 0)
        self._b_connect = QPushButton("Connect")
        self._b_connect.clicked.connect(self._on_connect)
        self._b_connect.setEnabled(False)
        hlayout.addWidget(self._b_connect)
        self._b_disconnect = QPushButton("Disconnect")
        self._b_disconnect.clicked.connect(self._on_disconnect)
        self._b_disconnect.setEnabled(False)
        hlayout.addWidget(self._b_disconnect)
        # state
        self._last_ts = None

    def configure(self, cfg):
        """Configure widget from config file."""
        fnt = QFont("Courier", 8)
        if 'font_size' in cfg:
            size = int(cfg['font_size'])
            fnt.setPixelSize(size)
        if 'font_family' in cfg:
            family = cfg['font_family']
            fnt.setFamily(family)
        self._w_log.setFont(fnt)

    def _on_update_state(self, state):
        if state == "Offline":
            connect = True
            disconnect = False
        elif state == "Operational":
            connect = False
            disconnect = True
        else:
            connect = False
            disconnect = False
        self._b_connect.setEnabled(connect)
        self._b_disconnect.setEnabled(disconnect)

    def _calc_delta(self):
        now = time.time()
        if self._last_ts:
            delta = (now - self._last_ts) * 1000.0
        else:
            delta = 0
        self._last_ts = now
        return delta

    def _on_send_raw(self, line):
        delta = self._calc_delta()
        txt = '<font color="#0F0">TX %04d: %s</font>' % (delta, line)
        self._w_log.appendHtml(txt)

    def _on_recv_raw(self, line):
        delta = self._calc_delta()
        txt = "RX %04d: %s" % (delta, line)
        self._w_log.appendHtml(txt)

    def _on_connect(self):
        self._client.connect()

    def _on_disconnect(self):
        self._client.disconnect()
