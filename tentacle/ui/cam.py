"""The camera tab."""

import time
import logging

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QImage
from PyQt5.QtCore import QRect, QPoint, QSize, Qt

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
        # ui
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        self.setLayout(layout)
        self._cam_view = CameraView()
        layout.addWidget(self._cam_view, 100)
        self._cam_info = QLabel()
        self._cam_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._cam_info)

    def configure(self, cfg):
        """Configure widget from config file."""
        if 'url' in cfg:
            self._url = cfg['url']

    def showEvent(self, _):
        """Start cam recording."""
        logging.info("cam: start")
        self._cam = CamClient(self._url)
        self._cam.jpegData.connect(self._cam_view.set_jpeg_data)
        self._cam.raisedError.connect(self._cam_info.setText)
        self._cam.updateFPS.connect(self._show_fps)
        self._cam.start()

    def hideEvent(self, _):
        """Stop cam recording."""
        logging.info("cam: stop")
        self._cam.stop()
        self._cam = None

    def _show_fps(self, fps):
        txt = "FPS: %8.3f" % fps
        self._cam_info.setText(txt)


class CameraView(QWidget):
    """Show a camera image."""

    def __init__(self):
        """Create camera widget."""
        super().__init__()
        self._qimg = None

    def set_jpeg_data(self, jpeg_data):
        """Set a new frame image."""
        t = time.time()
        if jpeg_data:
            qimg = QImage()
            qimg.loadFromData(jpeg_data, "JPG")
            self._qimg = qimg
        d = time.time() - t
        # (re)draw frame
        self.repaint()
        logging.info("cam get: %6.3f ms", d * 1000.0)

    def paintEvent(self, _):
        """Redraw graph."""
        if not self._qimg:
            return
        t = time.time()
        size = self.size()
        rect = self._center_frame(self._qimg.size(), size)
        qp = QPainter()
        qp.begin(self)
        qp.drawImage(rect, self._qimg)
        qp.end()
        d = time.time() - t
        logging.info("cam paint: %6.3f ms (rect %r)", d * 1000.0, rect)

    def _center_frame(self, img_size, draw_size):
        iw = img_size.width()
        ih = img_size.height()
        dw = draw_size.width()
        dh = draw_size.height()
        sx = dw / iw
        sy = dh / ih
        scale = min(sx, sy)
        rw = scale * iw
        rh = scale * ih
        ox = int((dw - rw) / 2)
        oy = int((dh - rh) / 2)
        return QRect(QPoint(ox, oy), QSize(rw, rh))
