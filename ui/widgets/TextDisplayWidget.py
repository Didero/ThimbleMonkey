from PySide6 import QtWidgets

from models.FileEntry import FileEntry
from ui.widgets.BaseFileEntryDisplayWidget import BaseFileEntryDisplayWidget


class TextDisplayWidget(QtWidgets.QPlainTextEdit, BaseFileEntryDisplayWidget):
	def __init__(self, fileEntry: FileEntry, text: str):
		super().__init__()
		self._fileEntry = fileEntry
		self.setPlainText(text)
		self.setReadOnly(True)
		self.setTabStopDistance(self.tabStopDistance() / 2)
