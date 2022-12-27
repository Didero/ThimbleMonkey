from PySide6 import QtGui, QtWidgets

from models.FileEntry import FileEntry
from ui.widgets.BaseFileEntryDisplayWidget import BaseFileEntryDisplayWidget
from ui.widgets.SimpleSoundPanel import SimpleSoundPanel


class SoundDisplayWidget(BaseFileEntryDisplayWidget):
	def __init__(self, fileEntry: FileEntry, audioData: bytes):
		super().__init__(fileEntry)
		self._soundPanel = SimpleSoundPanel(audioData, fileEntry.fileExtension, True)
		layout = QtWidgets.QHBoxLayout(self)
		self.setLayout(layout)

		layout.addWidget(self._soundPanel)

	def closeEvent(self, event: QtGui.QCloseEvent) -> None:
		self._soundPanel.stopSound()
		super().closeEvent(event)
