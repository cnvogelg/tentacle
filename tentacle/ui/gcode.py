"""The gcode tab."""

import time
import logging
import math

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor

from tentacle.range import RangeXYZ, RangeXY


class GCodeWidget(QWidget):
    """A gcode graph widget."""

    def __init__(self, model, client):
        """Create graph widget."""
        super().__init__()
        # receive temps
        self._model = model
        self._client = client
        self._model.sendGCode.connect(self._on_send_gcode)
        self._model.updateBusyFiles.connect(self._on_update_busy_files)
        # ranges
        self._def_range = RangeXY()
        self._meta_range = RangeXYZ()
        # state
        self._grid_x = 10
        self._grid_y = 10
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
        self._last_drawn = 0
        self._last_range = None
        self._cur_range = RangeXY()

    def configure(self, cfg):
        """Configure widget from config."""
        # setup default (print bed) range
        x_range = [float(cfg['min_x']), float(cfg['max_x'])]
        y_range = [float(cfg['min_y']), float(cfg['max_y'])]
        self._def_range = RangeXY(x_range, y_range)
        logging.info("gcode def range: %r", self._def_range)
        # setup grid
        if 'grid_x' in cfg:
            self._grid_x = float(cfg['grid_x'])
        if 'grid_y' in cfg:
            self._grid_y = float(cfg['grid_y'])

    @pyqtSlot(object)
    def _on_update_busy_files(self, files):
        if not files:
            logging.info("gcode: off")
            self._enabled = False
        else:
            self._enabled = True
            self._reset_state()
            self._file = files[0]
            self._set_meta_range(self._file)

    def _set_meta_range(self, name):
        logging.info("gcode: get meta for: %s", name)
        meta = self._model.files.get_meta(name)
        if meta:
            self._meta_range = RangeXYZ(meta.range_x,
                                        meta.range_y,
                                        meta.range_z)
            logging.info("gcode: meta range: %r", self._meta_range)
        else:
            logging.error("gcode: no meta available for: %s", name)

    @pyqtSlot(str)
    def _on_send_gcode(self, line):
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
            self.repaint()
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
            try:
                val = float(word[1:])
                if tag in ('X', 'Y', 'Z'):
                    self._pos[ord(tag) - ord('X')] = val
            except ValueError as e:
                logging.error("error parsing move Gcode: %s", tag)
        # z inc?
        if self._cur_z != self._pos[2]:
            self.repaint()
            self._cur_z = self._pos[2]
            logging.info("last slice: lines=%d, z=%s",
                         len(self._slice), self._cur_z)
            self._slice = []
            self._last_drawn = time.time()
            if self._last_range:
                self._last_range.merge(self._cur_range)
            else:
                self._last_range = self._cur_range
            logging.info("last range: %r", self._last_range)
            self._cur_range = RangeXY()
        # store new line
        x = self._pos[0]
        y = self._pos[1]
        self._cur_range.update(x, y)
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

        # get widget dimension
        size = self.size()
        w = size.width()
        h = size.height()

        t = time.time()
        qp = QPainter()
        qp.begin(self)

        # get ranges
        xy_range, z_range = self._pick_ranges()

        # draw xy geo
        if xy_range:
            map_func, off, size = self._get_map_func(w, h, xy_range)
            if map_func:
                self._draw_box(qp, off, size)
                self._draw_grid(qp, map_func, xy_range, off, size)
                self._draw_layer(qp, map_func)
                self._draw_cursor(qp, map_func)

        # draw z bar
        if z_range:
            self._draw_z(qp, h, z_range)

        qp.end()
        d = time.time() - t
        logging.info("gcode paint: %6.3f ms", d * 1000.0)

    def _pick_ranges(self):
        # prefer the meta range
        if self._meta_range and self._meta_range.is_valid():
            logging.info("pick meta range: %r", self._meta_range)
            return self._meta_range, self._meta_range.get_z_range()
        # use range of last layer
        elif self._last_range and self._last_range.is_valid():
            logging.info("pick last range: %r", self._last_range)
            return self._last_range, None
        # use range of current layer
        elif self._cur_range and self._cur_range.is_valid():
            logging.info("pick cur range: %r", self._cur_range)
            return self._cur_range, None
        # use default (print bed) range        
        elif self._def_range and self._def_range.is_valid():
            logging.info("pick def range: %r", self._def_range)
            return self._def_range, None
        # no range found
        else:
            logging.warn("pick no range!")
            return None, None

    def _get_map_func(self, w, h, xy_range):
        # check if range is valid
        x_range = xy_range.get_x_range()
        y_range = xy_range.get_y_range()
        if not x_range.is_valid() or not y_range.is_valid():
            return None, None, None

        # calc scale
        x_array = x_range.get_array()
        y_array = y_range.get_array()
        x_size = x_array[1] - x_array[0]
        y_size = y_array[1] - y_array[0]
        scale = min(w / x_size, h / y_size)
        off = [0, 0]
        off[0] = int((w - scale * x_size) / 2)
        off[1] = int((h - scale * y_size) / 2)

        def func(seg):
            return (int((seg[0] - x_array[0]) * scale) + off[0],
                    int((seg[1] - y_array[0]) * scale) + off[1])

        size = [int(x_size * scale), int(y_size * scale)]
        return func, off, size

    def _draw_box(self, qp, off, size):
        qp.setPen(QColor(64, 64, 64))
        qp.setBrush(QColor(32, 32, 32))
        qp.drawRect(off[0], off[1], size[0], size[1])

    def _draw_grid(self, qp, map_func, xy_range, off, size):
        qp.setPen(QColor(64, 64, 64))

        x_array = xy_range.get_x_range().get_array()
        x_grid = self._grid_x
        x_pos = math.ceil(x_array[0] / x_grid) * x_grid
        x_end = x_array[1]
        while x_pos <= x_end:
            x, _ = map_func([x_pos, 0])
            qp.drawLine(x, off[1], x, off[1] + size[1])
            x_pos += x_grid

        y_array = xy_range.get_y_range().get_array()
        y_grid = self._grid_y
        y_pos = math.ceil(y_array[0] / y_grid) * y_grid
        y_end = y_array[1]
        while y_pos <= y_end:
            _, y = map_func([0, y_pos])
            qp.drawLine(off[0], y, off[0] + size[0], y)
            y_pos += y_grid

    def _draw_layer(self, qp, map_func):
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

    def _draw_cursor(self, qp, map_func):
        # draw cursor
        cursor_col = QColor(128, 172, 240)
        cur_pos = map_func(self._pos)
        qp.setPen(cursor_col)
        qp.drawLine(cur_pos[0] - 5, cur_pos[1], cur_pos[0] + 5, cur_pos[1])
        qp.drawLine(cur_pos[0], cur_pos[1] - 5, cur_pos[0], cur_pos[1] + 5)

    def _draw_z(self, qp, h, z_range):
        z_array = z_range.get_array()
        z_size = z_array[1] - z_array[0]
        z_pos = self._cur_z - z_array[0]
        y = int(z_pos * (h-2) / z_size)
        # bar
        qp.setPen(QColor(64, 64, 64))
        qp.setBrush(QColor(32, 32, 32))
        qp.drawRect(0, 0, 10, h)
        qp.fillRect(1, 1, 8, y, QColor(128, 140, 180))
