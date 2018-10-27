from PyQt5.QtWidgets import QWidget


class FilesWidget(QWidget):
  def __init__(self, model):
    super(QWidget, self).__init__()
    self._model = model
