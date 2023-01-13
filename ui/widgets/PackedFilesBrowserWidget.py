import os
from fnmatch import fnmatch
from typing import List

from PySide6 import QtCore, QtWidgets

from models.FileEntry import FileEntry
from ui import WidgetHelpers


class PackedFilesBrowserWidget(QtWidgets.QWidget):
	loadFileSignal = QtCore.Signal(FileEntry)
	_COLUMN_DATA_USER_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole)
	_LOWERCASE_NAME_COLUMN_INDEX: int = 0
	_FILE_ENTRY_COLUMN_INDEX: int = 1

	def __init__(self):
		super().__init__()

		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(layout)

		# File browser that shows the packed files
		self._fileBrowser = QtWidgets.QTreeWidget()
		self._fileBrowser.setHeaderLabels(('Filename', 'Source', 'Size (bytes)'))
		self._fileBrowser.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
		self._fileBrowser.setMinimumWidth(450)
		self._fileBrowser.sizePolicy().setHorizontalPolicy(QtWidgets.QSizePolicy.MinimumExpanding)
		self._fileBrowser.setUniformRowHeights(True)
		self._fileBrowser.itemClicked.connect(self._emitLoadFileEvent)
		layout.addWidget(self._fileBrowser)

		# Label that shows the number of files, or how many files were filtered
		self._fileCountLabel = QtWidgets.QLabel('')
		self._fileCountLabel.setContentsMargins(5, 0, 0, 0)
		layout.addWidget(self._fileCountLabel)

		# Filter widgets
		filterContainer = QtWidgets.QWidget()
		filterContainerLayout = QtWidgets.QHBoxLayout()
		filterContainerLayout.setContentsMargins(5, 0, 0, 0)
		filterContainer.setLayout(filterContainerLayout)

		filterContainerLayout.addWidget(QtWidgets.QLabel('Filter:'))
		self._filterTextInput = QtWidgets.QLineEdit()
		self._filterTextInput.returnPressed.connect(self._onFilter)
		filterContainerLayout.addWidget(self._filterTextInput)

		WidgetHelpers.createButton('🔍', self._onFilter, filterContainerLayout)
		WidgetHelpers.createButton('X', self._clearFileBrowserFilter, filterContainerLayout)
		layout.addWidget(filterContainer)

	def showFilesInFileBrowser(self, packedFileEntries: List[FileEntry]):
		self._fileBrowser.clear()
		if packedFileEntries:
			# Disable sorting while adding new entries, for performance
			self._fileBrowser.setSortingEnabled(False)
			# Add all the entries
			for packedFileEntry in packedFileEntries:
				treeItem = QtWidgets.QTreeWidgetItem(self._fileBrowser)
				treeItem.setText(0, packedFileEntry.filename)
				treeItem.setText(1, os.path.basename(packedFileEntry.packFilePath))
				treeItem.setText(2, f"{packedFileEntry.size:,}")
				# Put a lowercase name hidden in a column, for case-insensitive filtering
				treeItem.setData(self._LOWERCASE_NAME_COLUMN_INDEX, self._COLUMN_DATA_USER_ROLE, packedFileEntry.filename.lower())
				# Put the actual file entry hidden a column, so we can retrieve it when an treeItem is clicked
				treeItem.setData(self._FILE_ENTRY_COLUMN_INDEX, self._COLUMN_DATA_USER_ROLE, packedFileEntry)
				self._fileBrowser.addTopLevelItem(treeItem)
			# Update the column widths
			for i in range(0, self._fileBrowser.columnCount()):
				self._fileBrowser.resizeColumnToContents(i)
			# Re-enable sorting
			self._fileBrowser.setSortingEnabled(True)
		self._onFilter()  # Filtering also updates the file count label

	def _updateFileCountLabel(self):
		filterText = self._filterTextInput.text().strip()
		if self._fileBrowser.topLevelItemCount() == 0:
			labelText = "No files loaded"
		elif filterText:
			# Count how many file items are visible
			visibleItemCount = 0
			for treeItemIndex in range(self._fileBrowser.topLevelItemCount()):
				treeItem = self._fileBrowser.topLevelItem(treeItemIndex)
				if not treeItem.isHidden():
					visibleItemCount += 1
			# The file browser is filtered, show how many files are visible
			labelText = f"Showing {visibleItemCount:,} of {self._fileBrowser.topLevelItemCount():,} files for '{filterText}'"
		else:
			# Files aren't filtered, show how many files there are in total
			labelText = f"{self._fileBrowser.topLevelItemCount():,} files found"
		self._fileCountLabel.setText(labelText)

	@QtCore.Slot(QtWidgets.QTreeWidgetItem, int)
	def _emitLoadFileEvent(self, itemToLoad: QtWidgets.QTreeWidgetItem, clickedColumnIndex: int):
		fileEntryToLoad = itemToLoad.data(self._FILE_ENTRY_COLUMN_INDEX, self._COLUMN_DATA_USER_ROLE)
		self.loadFileSignal.emit(fileEntryToLoad)

	@QtCore.Slot()
	def _onFilter(self, *args):
		self.filterFileBrowser(self._filterTextInput.text().strip())

	def filterFileBrowser(self, filterText: str):
		if self._filterTextInput.text() != filterText:
			self._filterTextInput.setText(filterText)
		if not filterText:
			self._clearFileBrowserFilter()
			return
		filterText = filterText.lower()
		# Make sure we always get partial matches ('.?tf' should get all .otf and .ttf files, instead of having to add * to the front and back every time)
		filterText = f"*{filterText}*"
		for treeItemIndex in range(self._fileBrowser.topLevelItemCount()):
			treeItem = self._fileBrowser.topLevelItem(treeItemIndex)
			treeItem.setHidden(not fnmatch(treeItem.data(self._LOWERCASE_NAME_COLUMN_INDEX, self._COLUMN_DATA_USER_ROLE), filterText))
		# Update the status text
		self._updateFileCountLabel()

	@QtCore.Slot(bool)
	def _clearFileBrowserFilter(self, *args):
		self._filterTextInput.clear()
		for treeItemIndex in range(self._fileBrowser.topLevelItemCount()):
			self._fileBrowser.topLevelItem(treeItemIndex).setHidden(False)
		self._updateFileCountLabel()

	def getFilteredFileEntries(self) -> List[FileEntry]:
		fileEntries: List[FileEntry] = []
		for treeItemIndex in range(self._fileBrowser.topLevelItemCount()):
			treeItem = self._fileBrowser.topLevelItem(treeItemIndex)
			if not treeItem.isHidden():
				fileEntries.append(treeItem.data(self._FILE_ENTRY_COLUMN_INDEX, self._COLUMN_DATA_USER_ROLE))
		return fileEntries

	def getAllFileEntries(self) -> List[FileEntry]:
		fileEntries: List[FileEntry] = []
		for treeItemIndex in range(self._fileBrowser.topLevelItemCount()):
			treeItem = self._fileBrowser.topLevelItem(treeItemIndex)
			fileEntries.append(treeItem.data(self._FILE_ENTRY_COLUMN_INDEX, self._COLUMN_DATA_USER_ROLE))
		return fileEntries

