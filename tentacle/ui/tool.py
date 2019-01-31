"""The Tool tab."""

import logging

from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGroupBox,
    QButtonGroup,
    QRadioButton,
    QLineEdit
)


class ToolWidget(QWidget):
    """Tool Operations Widget."""

    def __init__(self, model, client):
        """Create a new Tool widget."""
        super().__init__()
        self._model = model
        self._client = client
        self._model.updateTemps.connect(self.on_update_temps)
        # param
        self._t0_temps = [1, 2]
        self._t1_temps = [1, 2]
        self._bd_temps = [1, 2]
        # layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        # --- target temp ---
        # tool0
        self._t0_label = QLabel("Tool0")
        self._t0_temp = QLabel("000")
        self._t0_target = QLabel("000")
        self._t0_off = QPushButton("Off")
        self._t0_off.clicked.connect(lambda: self._set_tool(0, 0))
        self._t0_set1 = QPushButton("180")
        self._t0_set1.clicked.connect(
            lambda: self._set_tool(0, self._t0_temps[0]))
        self._t0_set2 = QPushButton("210")
        self._t0_set2.clicked.connect(
            lambda: self._set_tool(0, self._t0_temps[1]))
        # tool1
        self._t1_label = QLabel("Tool1")
        self._t1_temp = QLabel("000")
        self._t1_target = QLabel("000")
        self._t1_off = QPushButton("Off")
        self._t1_off.clicked.connect(lambda: self._set_tool(1, 0))
        self._t1_set1 = QPushButton("180")
        self._t1_set1.clicked.connect(
            lambda: self._set_tool(1, self._t1_temps[0]))
        self._t1_set2 = QPushButton("210")
        self._t1_set2.clicked.connect(
            lambda: self._set_tool(1, self._t1_temps[1]))
        # bed
        self._bd_label = QLabel("Bed")
        self._bd_temp = QLabel("000")
        self._bd_target = QLabel("000")
        self._bd_off = QPushButton("Off")
        self._bd_off.clicked.connect(lambda: self._set_bed(0))
        self._bd_set1 = QPushButton("180")
        self._bd_set1.clicked.connect(
            lambda: self._set_bed(self._bd_temps[0]))
        self._bd_set2 = QPushButton("210")
        self._bd_set2.clicked.connect(
            lambda: self._set_bed(self._bd_temps[1]))
        # tool, bed grid
        group = QGroupBox("Target Temperature")
        layout.addWidget(group)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        group.setLayout(grid)
        # tool0
        grid.addWidget(self._t0_label, 0, 0)
        grid.addWidget(self._t0_temp, 0, 1)
        grid.addWidget(self._t0_off, 0, 2)
        grid.addWidget(self._t0_set1, 0, 3)
        grid.addWidget(self._t0_set2, 0, 4)
        grid.addWidget(self._t0_target, 0, 5)
        # tool1
        grid.addWidget(self._t1_label, 1, 0)
        grid.addWidget(self._t1_temp, 1, 1)
        grid.addWidget(self._t1_off, 1, 2)
        grid.addWidget(self._t1_set1, 1, 3)
        grid.addWidget(self._t1_set2, 1, 4)
        grid.addWidget(self._t1_target, 1, 5)
        # bed
        grid.addWidget(self._bd_label, 2, 0)
        grid.addWidget(self._bd_temp, 2, 1)
        grid.addWidget(self._bd_off, 2, 2)
        grid.addWidget(self._bd_set1, 2, 3)
        grid.addWidget(self._bd_set2, 2, 4)
        grid.addWidget(self._bd_target, 2, 5)
        # --- filament ---
        group = QGroupBox("Filament")
        layout.addWidget(group)
        glayout = QVBoxLayout()
        glayout.setContentsMargins(0, 0, 0, 0)
        group.setLayout(glayout)
        # tool selection
        but_grp = QButtonGroup()
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        glayout.addLayout(hlayout)
        self._rb_tool0 = QRadioButton("Tool 0")
        self._rb_tool0.setChecked(True)
        hlayout.addWidget(self._rb_tool0)
        but_grp.addButton(self._rb_tool0)
        self._rb_tool1 = QRadioButton("Tool 1")
        hlayout.addWidget(self._rb_tool1)
        but_grp.addButton(self._rb_tool1)
        # amount
        hlayout.addSpacing(1)
        self._b_dec_amount = QPushButton("-")
        hlayout.addWidget(self._b_dec_amount)
        self._t_amount = QLineEdit("5")
        hlayout.addWidget(self._t_amount)
        self._b_inc_amount = QPushButton("+")
        hlayout.addWidget(self._b_inc_amount)

        # fill
        layout.addStretch(1)

    def configure(self, cfg):
        """Configure widget from config."""
        temp_map = {
            't0_temp1': ('_t0_temps', 0, '_t0_set1'),
            't0_temp2': ('_t0_temps', 1, '_t0_set2'),
            't1_temp1': ('_t1_temps', 0, '_t1_set1'),
            't1_temp2': ('_t1_temps', 1, '_t1_set2'),
            'bed_temp1': ('_bd_temps', 0, '_bd_set1'),
            'bed_temp2': ('_bd_temps', 1, '_bd_set2')
        }
        for key in temp_map:
            if key in cfg:
                var, idx, widget = temp_map[key]
                array = getattr(self, var)
                temp = cfg[key]
                array[idx] = int(temp)
                getattr(self, widget).setText(str(temp))

    def on_update_temps(self, data):
        self._t0_temp.setText(str(data.tool0[0]))
        self._t1_temp.setText(str(data.tool1[0]))
        self._bd_temp.setText(str(data.bed[0]))
        self._t0_target.setText(str(data.tool0[1]))
        self._t1_target.setText(str(data.tool1[1]))
        self._bd_target.setText(str(data.bed[1]))

    def _set_tool(self, num, temp):
        logging.info("set tool target: %d: %d", num, temp)
        self._client.tool_target(num, temp)

    def _set_bed(self, temp):
        logging.info("set bed target: %d", temp)
        self._client.bed_target(temp)
