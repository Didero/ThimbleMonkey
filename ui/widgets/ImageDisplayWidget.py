from PySide6 import QtCore, QtGui, QtWidgets

from models.FileEntry import FileEntry
from ui.widgets.BaseFileEntryDisplayWidget import BaseFileEntryDisplayWidget


class ImageDisplayWidget(QtWidgets.QGraphicsView, BaseFileEntryDisplayWidget):
	_BACKGROUND_BRUSH = QtGui.QBrush(QtCore.Qt.darkGray)

	def __init__(self, fileEntry: FileEntry, image: QtGui.QPixmap):
		super().__init__()
		self._fileEntry = fileEntry
		self.setBackgroundBrush(self._BACKGROUND_BRUSH)
		self._scene = QtWidgets.QGraphicsScene(self)
		self.setScene(self._scene)
		self._baseImage = image
		self._imageItem: QtWidgets.QGraphicsPixmapItem = self._scene.addPixmap(self._baseImage)
		self._fitImageIfTooLarge()

	def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
		super().resizeEvent(event)
		self._fitImageIfTooLarge()

	def _fitImageIfTooLarge(self):
		# Only shrink the image if it's too large, don't enlarge it if it's too small
		if self._baseImage.width() > self.width() or self._baseImage.height() > self.height():
			self.fitInView(self._imageItem, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
