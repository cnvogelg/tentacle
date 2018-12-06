from PyQt5.QtWidgets import QWidget


class ControlWidget(QWidget):
  def __init__(self, model, client):
    super().__init__()
    self._model = model
    self._client = client
