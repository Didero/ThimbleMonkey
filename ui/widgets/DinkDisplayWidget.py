from typing import Dict, List

from PySide6 import QtCore, QtGui, QtWidgets

from fileparsers.dinkhelpers.DinkScript import DinkScript
from models.FileEntry import FileEntry
from ui.widgets.BaseFileEntryDisplayWidget import BaseFileEntryDisplayWidget
from ui.widgets.TextDisplayWidget import TextDisplayWidget


class DinkDisplayWidget(BaseFileEntryDisplayWidget):
	def __init__(self, fileEntry: FileEntry, scripts: Dict[str, DinkScript]):
		super().__init__(fileEntry)

		layout = QtWidgets.QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(layout)

		self._codeDisplayWidget = TextDisplayWidget(fileEntry, "")
		functionBrowser = QtWidgets.QTreeWidget()
		functionBrowser.setColumnCount(1)
		functionBrowser.setMaximumWidth(200)
		functionBrowser.headerItem().setHidden(True)
		functionBrowser.itemClicked.connect(self._onFunctionBrowserItemSelected)
		layout.addWidget(self._codeDisplayWidget)
		layout.addWidget(functionBrowser)

		for scriptName, script in scripts.items():
			scriptItem = QtWidgets.QTreeWidgetItem(functionBrowser)
			scriptItem.setText(0, scriptName)
			# Store the block number for the script in the entry
			scriptItem.setData(0, QtCore.Qt.ItemDataRole.UserRole, self._codeDisplayWidget.blockCount())
			self._codeDisplayWidget.appendPlainText(scriptName)
			for uid, dinkFunction in script.functionsByUid.items():
				functionItem = QtWidgets.QTreeWidgetItem(scriptItem)
				functionItem.setText(0, dinkFunction.name)
				functionItem.setData(0, QtCore.Qt.ItemDataRole.UserRole, self._codeDisplayWidget.blockCount())
				self._codeDisplayWidget.appendPlainText(str(dinkFunction))
		# Appending text scrolls to the end, scroll back to the top
		self._codeDisplayWidget.moveCursor(QtGui.QTextCursor.MoveOperation.Start)

	@QtCore.Slot(QtWidgets.QTreeWidgetItem, int)
	def _onFunctionBrowserItemSelected(self, clickedItem: QtWidgets.QTreeWidgetItem, clickedColumnIndex: int):
		# First scroll all the way down, so we're forced to scroll up, meaning the target line/block will be at the top of the text window
		self._codeDisplayWidget.moveCursor(QtGui.QTextCursor.MoveOperation.End)
		# Scroll to the text block stored in the function item
		targetBlockIndex = clickedItem.data(0, QtCore.Qt.ItemDataRole.UserRole)
		targetBlock = self._codeDisplayWidget.document().findBlockByNumber(targetBlockIndex)
		self._codeDisplayWidget.setTextCursor(QtGui.QTextCursor(targetBlock))
