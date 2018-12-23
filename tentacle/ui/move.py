"""The Move tab."""

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QPushButton,
    QRadioButton,
    QHBoxLayout,
    QLabel,
    QSlider
)


class MoveWidget(QWidget):
    """A Move Printer Heads Widget."""

    def __init__(self, model, client):
        """Create a new Move widget."""
        super().__init__()
        self._model = model
        self._client = client
        # layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        # x,y
        self._b_xn = QPushButton("x-")
        self._b_xn.clicked.connect(lambda: self.on_move(-1.0, 0.0, 0.0))
        self._b_xp = QPushButton("x+")
        self._b_xp.clicked.connect(lambda: self.on_move(+1.0, 0.0, 0.0))
        self._b_yn = QPushButton("y-")
        self._b_yn.clicked.connect(lambda: self.on_move(0.0, -1.0, 0.0))
        self._b_yp = QPushButton("y+")
        self._b_yp.clicked.connect(lambda: self.on_move(0.0, +1.0, 0.0))
        self._b_home_xy = QPushButton("Hxy")
        self._b_home_xy.clicked.connect(
            lambda: self.on_home(True, True, False))
        # z
        self._b_zn = QPushButton("z-")
        self._b_zn.clicked.connect(lambda: self.on_move(0.0, 0.0, -1.0))
        self._b_zp = QPushButton("z+")
        self._b_zp.clicked.connect(lambda: self.on_move(0.0, 0.0, +1.0))
        self._b_home_z = QPushButton("Hz")
        self._b_home_z.clicked.connect(
            lambda: self.on_home(False, False, True))
        # extra
        self._b_home = QPushButton("Home")
        self._b_home.clicked.connect(lambda: self.on_home(True, True, True))
        self._b_unload = QPushButton("Unload")
        self._b_unload.clicked.connect(self.on_unload)
        # scale
        self._r_scale_01mm = QRadioButton("0.1")
        self._r_scale_01mm.setChecked(True)
        self._r_scale_1mm = QRadioButton("1")
        self._r_scale_10mm = QRadioButton("10")
        self._r_scale_50mm = QRadioButton("50")
        self._r_scale_01mm.toggled.connect(lambda: self.on_scale(0.1))
        self._r_scale_1mm.toggled.connect(lambda: self.on_scale(1))
        self._r_scale_10mm.toggled.connect(lambda: self.on_scale(10))
        self._r_scale_50mm.toggled.connect(lambda: self.on_scale(50))
        # x,y
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(grid)
        grid.addWidget(self._b_yn, 0, 1)
        grid.addWidget(self._b_xn, 1, 0)
        grid.addWidget(self._b_xp, 1, 2)
        grid.addWidget(self._b_yp, 2, 1)
        grid.addWidget(self._b_home_xy, 1, 1)
        # z
        grid.addWidget(self._b_zn, 0, 3)
        grid.addWidget(self._b_zp, 2, 3)
        grid.addWidget(self._b_home_z, 1, 3)
        # extra
        grid.addWidget(self._b_home, 3, 0, 1, 2)
        grid.addWidget(self._b_unload, 3, 2, 1, 2)
        # scale
        lay = QHBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(lay)
        lay.addWidget(QLabel("Scale (mm)"))
        lay.addWidget(self._r_scale_01mm)
        lay.addWidget(self._r_scale_1mm)
        lay.addWidget(self._r_scale_10mm)
        lay.addWidget(self._r_scale_50mm)
        # feedrate
        lay = QHBoxLayout()
        layout.addLayout(lay)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QLabel("Feed Rate"))
        self._s_feed_rate = self._setup_feed_rate_slider()
        self._s_feed_rate.valueChanged.connect(self._on_feed_rate_slider)
        lay.addWidget(self._s_feed_rate)
        self._b_reset_rate = QPushButton(" 100% ")
        self._b_reset_rate.clicked.connect(self._on_feed_reset_button)
        lay.addWidget(self._b_reset_rate)
        # fill ui
        layout.addStretch(1)
        # params
        self._scale = 0.1
        self._unload_z = 100
        self._feed_rate = 100

    def _setup_feed_rate_slider(self):
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(50)
        slider.setMaximum(150)
        slider.setValue(100)
        slider.setPageStep(10)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(10)
        slider.setTracking(False)
        return slider

    def configure(self, cfg):
        """Configure widget from config."""
        if "unload_z" in cfg:
            self._unload_z = float(cfg["unload_z"])

    def on_scale(self, new_scale):
        """React on scale radio buttons."""
        self._scale = new_scale
        logging.info("scale: %g", self._scale)

    def on_unload(self):
        """React on Unload button."""
        logging.info("unload: %g", self._unload_z)
        self._client.jog(0.0, 0.0, self._unload_z)

    def on_home(self, x, y, z):
        """React on Home buttons."""
        logging.info("home: x=%s, y=%s, z=%s", x, y, z)
        self._client.home(x, y, z)

    def on_move(self, x, y, z):
        """React on move buttons."""
        x *= self._scale
        y *= self._scale
        z *= self._scale
        logging.info("move: x=%s, y=%s, z=%s", x, y, z)
        self._client.jog(x, y, z)

    def _on_feed_rate_slider(self):
        value = self._s_feed_rate.value()
        self._b_reset_rate.setText("%03d%%" % value)
        self._feed_rate = value
        self._client.feedrate(value)

    def _on_feed_reset_button(self):
        self._b_reset_rate.setText("100%")
        self._s_feed_rate.setValue(100)
        self._feed_rate = 100
        self._client.feedrate(100)
