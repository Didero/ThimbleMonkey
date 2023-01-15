import concurrent.futures
from typing import Dict, List

from PySide6 import QtCore, QtGui, QtWidgets

from fileparsers import GGPackParser
from models.FileEntry import FileEntry


class SaveProgressDialog(QtWidgets.QDialog):
	def __init__(self, fileEntriesToSave: List[FileEntry], savePath: str, shouldConvertData: bool, parent: QtWidgets.QWidget = None):
		super().__init__(parent=parent)
		self._isAllowedToClose: bool = False
		self.setWindowTitle("Save Progress")
		self.saveErrors: Dict[FileEntry, BaseException] = {}
		# Prevent this dialog from being closed by removing the 'Close' button in the titlebar
		self.setWindowFlag(QtCore.Qt.WindowType.WindowCloseButtonHint, False)

		layout = QtWidgets.QVBoxLayout(self)
		self.setLayout(layout)

		self._progressBar = QtWidgets.QProgressBar()
		self._progressBar.setMinimum(0)
		self._progressBar.setMaximum(len(fileEntriesToSave))
		self._progressBar.setFormat("%v / %m - %p %")
		self._progressBar.setValue(0)
		layout.addWidget(self._progressBar)

		self._durationLabel = QtWidgets.QLabel()
		layout.addWidget(self._durationLabel)

		self._secondsPassed: int = -1  # -1 because we're going to update the count immediately
		self._timer = QtCore.QTimer(self)
		self._timer.timeout.connect(self._onTimerUpdate)
		self._timer.setInterval(1000)
		self._onTimerUpdate()  # Fill in the duration label immediately, instead of after the first update
		self._timer.start()

		runner = _Runner(fileEntriesToSave, savePath, shouldConvertData)
		runner.fileEntrySavedSignal.connect(self._onProgressUpdate)
		runner.finishedSignal.connect(self._onFinished)
		QtCore.QThreadPool.globalInstance().start(runner)
		self.exec_()

	@QtCore.Slot()
	def _onTimerUpdate(self):
		self._secondsPassed += 1
		self._durationLabel.setText(f"Time elapsed: {self._secondsPassed // 60:.0f} minutes, {self._secondsPassed % 60:.0f} seconds")

	@QtCore.Slot(FileEntry, BaseException)
	def _onProgressUpdate(self, fileEntry: FileEntry, error=None):
		self._progressBar.setValue(self._progressBar.value() + 1)
		if error:
			self.saveErrors[fileEntry] = error

	@QtCore.Slot()
	def _onFinished(self):
		self._isAllowedToClose = True
		self.close()

	# These next three methods override default QDialog behaviour to prevent closing of the dialog before saving is done
	def closeEvent(self, closeEvent: QtGui.QCloseEvent) -> None:
		if self._isAllowedToClose:
			super().closeEvent(closeEvent)
		else:
			closeEvent.ignore()

	def accept(self) -> None:
		if self._isAllowedToClose:
			super().accept()

	def reject(self) -> None:
		if self._isAllowedToClose:
			super().reject()


class _Runner(QtCore.QRunnable, QtCore.QObject):
	fileEntrySavedSignal = QtCore.Signal(FileEntry, BaseException)
	finishedSignal = QtCore.Signal()

	def __init__(self, fileEntriesToSave: List[FileEntry], savePath: str, shouldConvertData: bool):
		QtCore.QRunnable.__init__(self)
		QtCore.QObject.__init__(self)

		self._fileEntriesToSave = fileEntriesToSave
		self._savePath = savePath
		self._shouldConvertData = shouldConvertData

	@QtCore.Slot()
	def run(self):
		with concurrent.futures.ProcessPoolExecutor(10) as pool:
			futures = []
			for fileEntry in self._fileEntriesToSave:
				futures.append(pool.submit(GGPackParser.savePackedFile, fileEntry, self._savePath, self._shouldConvertData))
			for completedFuture in concurrent.futures.as_completed(futures):
				self.fileEntrySavedSignal.emit(fileEntry, completedFuture.exception())
		self.finishedSignal.emit()
