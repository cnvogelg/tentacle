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
        self._model.addSerialLog.connect(self._on_add_serial_log)
        self._model.updateBusyFiles.connect(self._on_update_busy_files)
        # state
        self._enabled = False
        self._reset_state()

    def _reset_state(self):
        self._pos = [0.0, 0.0, 0.0]
        self._slice = []
        self._cur_z = 0.0
        self._width = 0
        self._height = 0
        self._tool = 0
        self._file = None
        self._x_range = None
        self._y_range = None
        self._z_range = None
        self._last_drawn = 0

    @pyqtSlot(object)
    def _on_update_busy_files(self, files):
        if not files:
            logging.info("gcode: off")
            self._enabled = False
        else:
            self._enabled = True
            self._reset_state()
            self._file = files[0]
            if not self._get_meta(self._file):
                self._enabled = False

    def _get_meta(self, name):
        logging.info("gcode: get meta for: %s", name)
        meta = self._model.files.get_meta(name)
        if meta:
            self._x_range = meta.range_x
            self._y_range = meta.range_y
            self._z_range = meta.range_z
            logging.info("gcode ranges: %r, %r, %r",
                         self._x_range, self._y_range, self._z_range)
            return True
        else:
            logging.error("gcode: no meta for: %s", name)
            return False

    @pyqtSlot(str)
    def _on_add_serial_log(self, line):
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
        elif cmd == 'T0':
            self._tool = 0
        elif cmd == 'T1':
            self._tool = 1
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
            logging.info("last slice: lines=%d, z=%s",
                         len(self._slice), self._cur_z)
            self._slice = []
            self._last_drawn = time.time()
        # store new line
        x = self._pos[0]
        y = self._pos[1]
        self._slice.append((x, y, extrude, self._tool))
        # repaint every 100ms
        t = time.time()
        delta = t - self._last_drawn
        if delta > 0.1:
            self.repaint()
            self._last_drawn = t

    def paintEvent(self, _):
        """Redraw graph."""
        if not self._enabled:
            return
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
        tool_cols = (QColor(255, 255, 0), QColor(0, 255, 255))
        last_pos = None
        last_col = None
        for seg in self._slice:
            pos = map_func(seg)
            if last_pos:
                # adjust color
                extrude = seg[2]
                tool = seg[3]
                if extrude:
                    col = tool_cols[tool]
                else:
                    col = rapid_col
                if col != last_col:
                    qp.setPen(col)
                    last_col = col
                # draw line
                # pylint: disable=E1136
                qp.drawLine(last_pos[0], last_pos[1], pos[0], pos[1])
            last_pos = pos
        # draw cursor
        cursor_col = QColor(240, 240, 240)
        cur_pos = map_func(self._pos)
        qp.setPen(cursor_col)
        qp.drawLine(cur_pos[0] - 5, cur_pos[1], cur_pos[0] + 5, cur_pos[1])
        qp.drawLine(cur_pos[0], cur_pos[1] - 5, cur_pos[0], cur_pos[1] + 5)
