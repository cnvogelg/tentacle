from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel


class JobWidget(QWidget):
  def __init__(self):
    super(QWidget, self).__init__()
    self._layout = QGridLayout()
    self.setLayout(self._layout)
    self._l_user = QLabel(self)
    self._l_file = QLabel(self)
    self._layout.addWidget(self._l_user, 0, 0)
    self._layout.addWidget(self._l_file, 1, 0)
    self._l_user.setText("user")
    self._l_file.setText("file")
