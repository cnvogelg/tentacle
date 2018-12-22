"""The temperature tab."""

import logging
import time

from PyQt5.QtCore import pyqtSlot, QPoint
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QFontMetrics

from tentacle.client import TempData
from tentacle.util import ts_to_hms


class TempWidget(QWidget):
    """A temperature graph widget."""

    def __init__(self, model, client):
        """Create graph widget."""
        super().__init__()
        # receive temps
        self._model = model
        self._client = client
        self._model.updateTemps.connect(self.on_updateTemps)
        self.min_y = 0
        self.max_y = 100
        self.step_y = 10
        self.font_size = 8
        # data buf
        self.data_len = 320
        self.data_buf = [None] * self.data_len
        self.data_pos = 0
        # tick step: 60s
        self.tick_step = 60
        self.tick_last_ts = None
        # colors
        self.col_bg = QColor(0, 0, 0)
        self.col_grid = QColor(64, 64, 64)
        self.col_txt = QColor(255, 255, 255)
        self.col_temps = (
            QColor(128, 100, 100),
            QColor(255, 200, 200),
            QColor(100, 128, 100),
            QColor(200, 255, 200),
            QColor(100, 100, 128),
            QColor(200, 200, 255),
        )

    def configure(self, cfg):
        """Configure widget from config file."""
        if "min" in cfg:
            self.min_y = int(cfg["min"])
        if "max" in cfg:
            self.max_y = int(cfg["max"])
        if "step" in cfg:
            self.step_y = int(cfg["step"])
        if "font_size" in cfg:
            self.font_size = int(cfg["font_size"])

    @pyqtSlot(TempData)
    def on_updateTemps(self, data):
        """Temperature data processing."""
        self.data_buf[self.data_pos] = data
        self.data_pos += 1
        # scroll buffer to left
        if self.data_pos == self.data_len:
            self.data_pos = self.data_len - 1
            self.data_buf = self.data_buf[1:] + [None]
        # tick this data (will draw a vertical bar in graph)?
        self._calc_tick(data)
        # redraw widget
        self.repaint()

    def _calc_tick(self, data):
        ts = (data.time // self.tick_step) * self.tick_step
        tick = False
        if self.tick_last_ts is None:
            self.tick_last_ts = ts
            tick = True
        else:
            delta = ts - self.tick_last_ts
            if delta >= self.tick_step:
                self.tick_last_ts = ts
                tick = True
        # store tick flag
        data.tick = tick

    def resizeEvent(self, e):
        """React on initial widget resize."""
        s = e.size()
        width = s.width() - 2
        height = s.height() - 2
        logging.info("temp win size: %d x %d", width, height)
        # derive font
        self.f = self.font()
        self.f.setPixelSize(self.font_size)
        self.fm = QFontMetrics(self.f)
        # font boxes
        self.num_tr = self.fm.boundingRect("999")
        self.num_tr.moveTop(2)
        self.num_tr.moveLeft(2)
        self.time_tr = self.fm.boundingRect("99:99:99")
        # scaling
        self.t_start = height + 1
        self.t_h = self.max_y - self.min_y
        self.t_scl = height / self.t_h
        # map func
        self.map_y = lambda x: int(self.t_start - x * self.t_scl)
        # shrink buffer?
        if self.data_len > width:
            shrink = self.data_len - width
            self.data_len = width
            self.data_buf = self.data_buf[shrink:]
            if self.data_pos > shrink:
                self.data_pos -= shrink
            else:
                self.data_pos = 0

    def paintEvent(self, _):
        """Redraw graph."""
        t = time.time()
        qp = QPainter()
        qp.begin(self)
        size = self.size()
        self._draw(qp, size.width(), size.height())
        qp.end()
        d = time.time() - t
        logging.debug("temp paint: %6.3f ms", d * 1000.0)

    def _draw(self, qp, w, h):
        # blank
        qp.setPen(self.col_bg)
        qp.setBrush(QColor(32, 32, 32))
        qp.drawRect(0, 0, w, h)
        # grid
        self._draw_grid(qp, w)
        # plot graph
        x = 1
        last_data = None
        for data in self.data_buf:
            self._draw_data(qp, x, h, data, last_data)
            last_data = data
            x += 1
        # texts
        self._draw_grid_text(qp)
        self._draw_time(qp, w)
        self._draw_temps_text(qp, w, h)

    def _draw_grid(self, qp, w):
        qp.setPen(self.col_grid)
        off = self.min_y
        while off <= self.max_y:
            y = self.map_y(off)
            qp.drawLine(0, y, w, y)
            off += self.step_y

    def _draw_data(self, qp, x, h, data, last_data):
        if not data or not last_data:
            return
        # tick?
        if data.tick:
            qp.setPen(self.col_grid)
            qp.drawLine(x, 1, x, h - 1)
        # temp values
        if data.bed and last_data.bed:
            self._draw_temp(qp, x, data.bed, last_data.bed, 0)
        if data.tool0 and last_data.tool0:
            self._draw_temp(qp, x, data.tool0, last_data.tool0, 2)
        if data.tool1 and last_data.tool1:
            self._draw_temp(qp, x, data.tool1, last_data.tool1, 4)

    def _draw_temp(self, qp, x, val_pair, last_val_pair, col_off):
        # target temp
        qp.setPen(self.col_temps[col_off])
        yl = self.map_y(last_val_pair[1])
        yn = self.map_y(val_pair[1])
        qp.drawLine(x - 1, yl, x, yn)
        # current val
        qp.setPen(self.col_temps[col_off + 1])
        yl = self.map_y(last_val_pair[0])
        yn = self.map_y(val_pair[0])
        qp.drawLine(x - 1, yl, x, yn)

    def _draw_grid_text(self, qp):
        qp.setPen(self.col_txt)
        qp.setFont(self.f)
        off = self.min_y
        while off <= self.max_y:
            tr = self.num_tr
            y = self.map_y(off)
            tr.moveTop(y)
            qp.drawText(tr, 0, str(off))
            off += self.step_y * 2

    def _draw_time(self, qp, w):
        if self.data_pos == 0:
            return
        last_data = self.data_buf[self.data_pos - 1]
        if not last_data:
            return
        ts = last_data.time
        hms = ts_to_hms(ts)
        time_str = "%02d:%02d:%02d" % hms
        tr = self.time_tr
        tr.moveRight(w - 2)
        tr.moveTop(0)
        qp.drawText(tr, 0, time_str)

    def _draw_temps_text(self, qp, w, h):
        if self.data_pos == 0:
            return
        last_data = self.data_buf[self.data_pos - 1]
        if not last_data:
            return
        if last_data.bed:
            self._draw_temp_text(qp, w, h, last_data.bed, 0, "B")
        if last_data.tool0:
            self._draw_temp_text(qp, w, h, last_data.tool0, 1, "0")
        if last_data.tool1:
            self._draw_temp_text(qp, w, h, last_data.tool1, 2, "1")

    def _draw_temp_text(self, qp, w, h, vals, off, txt):
        txt = "%s: %7.2f/%4.0f" % (txt, vals[0], vals[1])
        tr = self.fm.boundingRect(txt)
        if off == 0:
            tr.moveLeft(2)
        elif off == 1:
            tr.moveCenter(QPoint(w // 2, 0))
        else:
            tr.moveRight(w - 2)
        tr.moveBottom(h - 2)
        c = self.col_temps[off * 2 + 1]
        qp.setPen(c)
        qp.drawText(tr, 0, txt)
