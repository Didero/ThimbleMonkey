from PySide6 import QtGui, QtWidgets

from models.FileEntry import FileEntry
from ui.widgets.BaseFileEntryDisplayWidget import BaseFileEntryDisplayWidget


class FontDisplayWidget(BaseFileEntryDisplayWidget):
	TEXT = "The quick brown fox jumps over the lazy fox 0123456789 ?!@#$%^&*(){}[]/|\\*-+=;:'\",.<>"

	def __init__(self, fileEntry: FileEntry, fontData: bytes):
		super().__init__(fileEntry)

		layout = QtWidgets.QVBoxLayout()
		self.setLayout(layout)

		self._fontId = QtGui.QFontDatabase.addApplicationFontFromData(fontData)
		fontFamilies = QtGui.QFontDatabase.applicationFontFamilies(self._fontId)
		for fontFamily in fontFamilies:
			styles = QtGui.QFontDatabase.styles(fontFamily)
			label = QtWidgets.QLabel(f"Font family '{fontFamily}', style '{styles[0]}'")
			label.setFont(QtGui.QFontDatabase.font(fontFamily, styles[0], 48))
			layout.addWidget(label)
			for fontSize in range(24, 100, 12):
				label = QtWidgets.QLabel(FontDisplayWidget.TEXT)
				label.setFont(QtGui.QFontDatabase.font(fontFamily, styles[0], fontSize))
				layout.addWidget(label)
		layout.addStretch(10)

	def closeEvent(self, event: QtGui.QCloseEvent) -> None:
		# Don't let the font linger in the font database
		QtGui.QFontDatabase.removeApplicationFont(self._fontId)
		super().closeEvent(event)
