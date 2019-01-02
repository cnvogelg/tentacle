"""The camera tab."""

import time
import logging

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QImage
from PyQt5.QtCore import QRect, QPoint

from tentacle.client import CamClient


class CameraWidget(QWidget):
    """A camera widget."""

    def __init__(self, model, client):
        """Create camera widget."""
        super().__init__()
        # receive temps
        self._model = model
        self._client = client
        self._url = None
        self._cam = None
        self._qimg = None

    def configure(self, cfg):
        """Configure widget from config file."""
        if 'url' in cfg:
            self._url = cfg['url']

    def showEvent(self, _):
        """Start cam recording."""
        logging.info("cam: start")
        self._last_get = time.time()
        self._cam = CamClient(self._url)
        self._cam.jpegData.connect(self._on_data)
        self._cam.start()

    def hideEvent(self, _):
        """Stop cam recording."""
        logging.info("cam: stop")
        self._cam.stop()
        self._cam = None

    def _on_data(self, jpeg_data):
        t = time.time()
        delta = t - self._last_get
        self._last_get = t
        if jpeg_data:
            qimg = QImage()
            qimg.loadFromData(jpeg_data, "JPG")
            self._qimg = qimg
        d = time.time() - t
        logging.info("cam get: %6.3f ms (last frame: %6.3f ms)",
                     d * 1000.0, delta * 1000.0)
        self.repaint()

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
