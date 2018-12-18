"""The gcode tab."""

import time
import logging

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor


class GCodeWidget(QWidget):
    """A gcode graph widget."""

    def __init__(self, model, client):
        """Create graph widget."""
        super().__init__()
        # receive temps
        self._model = model
        self._client = client
        self._model.addSerialLog.connect(self.on_add_serial_log)
        # state
        self._reset_state()

    def _reset_state(self):
        self._pos = [0.0, 0.0, 0.0]
        self._slice = []
        self._cur_z = 0.0
        self._reset_range()
        self._width = 0
        self._height = 0

    def _reset_range(self):
        self._x_range = [10000.0, -10000.0]
        self._y_range = [10000.0, -10000.0]

    @pyqtSlot(str)
    def on_add_serial_log(self, line):
        """Process gcode."""
        words = line.split()
        if not words:
            return
        cmd = words[0]
        if cmd == 'G0':
            self._parse_move(words[1:], False)
        elif cmd == 'G1':
            self._parse_move(words[1:], True)
        elif cmd == 'G28':  # auto home
            self._reset_state()
        else:
            logging.info("gcode: %s", line)

    def _parse_move(self, words, extrude):
        # update X, Y, or Z
        for word in words:
            tag = word[0]
            val = float(word[1:])
            if tag in ('X', 'Y', 'Z'):
                self._pos[ord(tag) - ord('X')] = val
        # z inc?
        if self._cur_z != self._pos[2]:
            self.repaint()
            self._cur_z = self._pos[2]
            logging.info("last slice: lines=%d, range:x=%r, y=%r, z=%s",
                         len(self._slice), self._x_range, self._y_range,
                         self._cur_z)
            self._slice = []
            self._reset_range()
        # store new line
        x = self._pos[0]
        y = self._pos[1]
        self._slice.append((x, y, extrude))
        # adjust min/max
        self._adjust_range(x, y)

    def _adjust_range(self, x, y):
        if x < self._x_range[0]:
            self._x_range[0] = x
        if x > self._x_range[1]:
            self._x_range[1] = x
        if y < self._y_range[0]:
            self._y_range[0] = y
        if y > self._y_range[1]:
            self._y_range[1] = y

    def paintEvent(self, _):
        """Redraw graph."""
        t = time.time()
        qp = QPainter()
        qp.begin(self)
        size = self.size()
        self._draw(qp, size.width(), size.height())
        qp.end()
        d = time.time() - t
        logging.info("gcode paint: %6.3f ms", d * 1000.0)

    def _get_map_func(self, w, h):
        if self._x_range[0] > self._x_range[1]:
            return None, None, None
        x_size = self._x_range[1] - self._x_range[0]
        y_size = self._y_range[1] - self._y_range[0]
        if x_size == 0 or y_size == 0:
            return None, None, None
        scale = min(w / x_size, h / y_size)
        off = [0, 0]
        off[0] = int((w - scale * x_size) / 2)
        off[1] = int((h - scale * y_size) / 2)

        def func(seg):
            return (int((seg[0] - self._x_range[0]) * scale) + off[0],
                    int((seg[1] - self._y_range[0]) * scale) + off[1])

        size = [int(x_size * scale), int(y_size * scale)]
        return func, off, size

    def _draw(self, qp, w, h):
        map_func, off, size = self._get_map_func(w, h)
        if not map_func:
            return
        # clear
        qp.setPen(QColor(64, 64, 64))
        qp.setBrush(QColor(32, 32, 32))
        qp.drawRect(off[0], off[1], size[0], size[1])
        # draw sketch
        rapid_col = QColor(0, 220, 0)
        extrude_col = QColor(255, 255, 0)
        last_pos = None
        last_col = None
        for seg in self._slice:
            pos = map_func(seg)
            if last_pos:
                # adjust color
                extrude = seg[2]
                if extrude:
                    col = extrude_col
                else:
                    col = rapid_col
                if col != last_col:
                    qp.setPen(col)
                    last_col = col
                # draw line
                # pylint: disable=E1136
                qp.drawLine(last_pos[0], last_pos[1], pos[0], pos[1])
            last_pos = pos
