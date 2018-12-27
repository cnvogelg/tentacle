"""The camera tab."""

import time
import logging
import requests

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QImage
from PyQt5.QtCore import QTimer, QRect, QPoint


class CameraWidget(QWidget):
    """A camera widget."""

    def __init__(self, model, client):
        """Create camera widget."""
        super().__init__()
        # receive temps
        self._model = model
        self._client = client
        self._url = None
        self._interval = 1000
        self._qimg = None
        # setup timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer)

    def configure(self, cfg):
        """Configure widget from config file."""
        if 'url' in cfg:
            self._url = cfg['url']
        if 'interval' in cfg:
            self._interval = int(cfg['interval'])

    def showEvent(self, _):
        """Start cam recording."""
        logging.info("cam: start")
        self._timer.start(self._interval)

    def hideEvent(self, _):
        """Stop cam recording."""
        logging.info("cam: stop")
        self._timer.stop()

    def _on_timer(self):
        t = time.time()
        jpeg_data = self._get_jpeg()
        if jpeg_data:
            qimg = QImage()
            qimg.loadFromData(jpeg_data, "JPG")
            self._qimg = qimg
        d = time.time() - t
        logging.info("cam get: %6.3f ms", d * 1000.0)
        self.repaint()

    def _get_jpeg(self):
        if not self._url:
            return
        r = requests.get(self._url)
        if r.status_code != 200:
            logging.error("cam: get: %s -> %d", self._url, r.status_code)
            return
        data = r.content
        logging.info("cam: get: %s -> %d", self._url, len(data))
        return data

    def paintEvent(self, _):
        """Redraw graph."""
        if not self._qimg:
            return
        t = time.time()
        size = self.size()
        rect = QRect(QPoint(0, 0), size)
        qp = QPainter()
        qp.begin(self)
        qp.drawImage(rect, self._qimg)
        qp.end()
        d = time.time() - t
        logging.info("cam paint: %6.3f ms", d * 1000.0)
