from typing import List

from PySide6 import QtWidgets

from models.FileEntry import FileEntry
from ui.widgets.BaseFileEntryDisplayWidget import BaseFileEntryDisplayWidget


class TableDisplayWidget(QtWidgets.QTableWidget, BaseFileEntryDisplayWidget):
	def __init__(self, fileEntry: FileEntry, tableData: List[List[str]]):
		super().__init__()
		self._fileEntry = fileEntry
		self.setSortingEnabled(False)
		headerStrings: List[str] = tableData.pop(0)
		self.setHorizontalHeaderLabels(headerStrings)
		self.setColumnCount(len(headerStrings))
		self.setRowCount(len(tableData))
		for rowIndex, row in enumerate(tableData):
			for columnIndex, cellText in enumerate(row):
				cellItem = QtWidgets.QTableWidgetItem(cellText)
				self.setItem(rowIndex, columnIndex, cellItem)
		self.setSortingEnabled(True)
