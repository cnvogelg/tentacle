"""File Set Tab."""

from PyQt5.QtWidgets import QWidget


class FilesWidget(QWidget):
    """File Set Tab shows all files."""

    def __init__(self, model, client):
        """Create a new file set tab."""
        super().__init__()
        self._model = model
        self._client = client
