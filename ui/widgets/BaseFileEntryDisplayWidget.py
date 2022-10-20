from PySide6 import QtCore, QtGui, QtWidgets

from models.FileEntry import FileEntry


class BaseFileEntryDisplayWidget(QtWidgets.QWidget):
	close: QtCore.Signal = QtCore.Signal(FileEntry)

	def __init__(self, fileEntry: FileEntry):
		super().__init__()
		self._fileEntry = fileEntry

	def closeEvent(self, event: QtGui.QCloseEvent) -> None:
		self.close.emit(self._fileEntry)
		super().closeEvent(event)
