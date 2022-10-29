import json, os
from typing import List
from weakref import WeakValueDictionary

from PIL import ImageQt
from PIL.Image import Image
from PySide6 import QtCore, QtGui, QtWidgets

from fileparsers import GGPackParser
from models.FileEntry import FileEntry
from ui import WidgetHelpers
from ui.widgets.BaseFileEntryDisplayWidget import BaseFileEntryDisplayWidget
from ui.widgets.FontDisplayWidget import FontDisplayWidget
from ui.widgets.ImageDisplayWidget import ImageDisplayWidget
from ui.widgets.PackedFilesBrowserWidget import PackedFilesBrowserWidget
from ui.widgets.TableDisplayWidget import TableDisplayWidget
from ui.widgets.TextDisplayWidget import TextDisplayWidget


class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, pathToLoadOnStart: str = None):
		super().__init__()
		self.resize(1920, 1280)
		self._centerWindowOnScreen()
		self._initUi()
		self._initMenuBar()
		self.setStatusBar(QtWidgets.QStatusBar(self))
		if pathToLoadOnStart:
			self.setGamePath(pathToLoadOnStart)
		# Store the opened subwindows in here, so we can't open one file multiple times (Don't use filenames for this, with mods there can be duplicates)
		self._displayedFileEntries: WeakValueDictionary[FileEntry, QtWidgets.QMdiSubWindow] = WeakValueDictionary()

	def _centerWindowOnScreen(self):
		frameGm = self.frameGeometry()
		screen = QtGui.QGuiApplication.primaryScreen()
		centerPoint = screen.availableGeometry().center()
		frameGm.moveCenter(centerPoint)
		self.move(frameGm.topLeft())

	def _initUi(self):
		self.setWindowTitle(QtWidgets.QApplication.applicationName())
		# Create the central widget that will hold all our layouts and controls
		centerWidget = QtWidgets.QSplitter(self)
		centerWidget.setContentsMargins(0, 0, 0, 0)
		self.setCentralWidget(centerWidget)

		# File browser on the left
		self.packedFileBrowser = PackedFilesBrowserWidget()
		self.packedFileBrowser.loadFileSignal.connect(self.loadFileFromFileBrowser)
		centerWidget.addWidget(self.packedFileBrowser)

		# Allow multiple file windows open in the main area
		self.centerDisplayArea = QtWidgets.QMdiArea()
		self.centerDisplayArea.setContentsMargins(0, 0, 0, 0)
		self.centerDisplayArea.setViewMode(QtWidgets.QMdiArea.ViewMode.TabbedView)
		self.centerDisplayArea.setTabsMovable(True)
		self.centerDisplayArea.setTabsClosable(True)
		self.centerDisplayArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
		self.centerDisplayArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
		centerWidget.addWidget(self.centerDisplayArea)

	def _initMenuBar(self):
		fileMenu = self.menuBar().addMenu("&File")
		WidgetHelpers.createMenuAction(fileMenu, "&Load game folder...", self._browseForGamePath, "Load the game files in the provided folder")
		fileMenu.addSeparator()
		WidgetHelpers.createMenuAction(fileMenu, "&Save curent tab data", lambda: self.saveTabData(False), "Save tab data exactly how it's stored")
		WidgetHelpers.createMenuAction(fileMenu, "&Export current tab data", lambda: self.saveTabData(True), "Export the tab data as something usable")
		fileMenu.addSeparator()
		WidgetHelpers.createMenuAction(fileMenu, "E&xit", self.close, "Exits the application")

		tabMenu = self.menuBar().addMenu("&Tabs")
		WidgetHelpers.createMenuAction(tabMenu, "Close &all tabs", self._closeAllTabs, "Close all the opened file display tabs")
		WidgetHelpers.createMenuAction(tabMenu, "Close &other tabs", self._closeOtherTabs, "Closes all the opened file display tabs, except the current tab")
		WidgetHelpers.createMenuAction(tabMenu, "Close tabs to the &left", self._closeTabsToLeft, "Closes all file display tabs to the left of the current tab")
		WidgetHelpers.createMenuAction(tabMenu, "Close tabs to the &right", self._closeTabsToRight, "Closes all file display tabs to the right of the current tab")

	def updateWindowTitle(self, titleSuffix: str = None):
		if titleSuffix:
			self.setWindowTitle(f"{QtWidgets.QApplication.applicationName()} - {titleSuffix}")
		else:
			self.setWindowTitle(QtWidgets.QApplication.applicationName())

	@QtCore.Slot()
	def _browseForGamePath(self):
		path = QtWidgets.QFileDialog.getExistingDirectory(self, "Load RtMI Game Folder")
		# 'path' is None if the file dialog is dismissed
		if path:
			self.setGamePath(path)

	def setGamePath(self, gamePath: str):
		packedFileEntries: List[FileEntry] = []
		for fn in os.listdir(gamePath):
			gameFilePath = os.path.join(gamePath, fn)
			if '.ggpack' not in fn or os.path.isdir(gameFilePath):
				continue
			fileIndex = GGPackParser.getFileIndex(gameFilePath)
			for fileEntryData in fileIndex['files']:
				fileEntry = FileEntry(fileEntryData['filename'], fileEntryData['offset'], fileEntryData['size'], gameFilePath)
				packedFileEntries.append(fileEntry)
		self.updateWindowTitle(gamePath)
		self.packedFileBrowser.showFilesInFileBrowser(packedFileEntries)

	@QtCore.Slot(FileEntry)
	def loadFileFromFileBrowser(self, fileEntryToLoad: FileEntry):
		if fileEntryToLoad in self._displayedFileEntries and self._displayedFileEntries[fileEntryToLoad] in self.centerDisplayArea.subWindowList():
			subwindow = self._displayedFileEntries[fileEntryToLoad]
			self.centerDisplayArea.setActiveSubWindow(subwindow)
		else:
			if fileEntryToLoad in self._displayedFileEntries:
				# Apparently the window isn't shown anymore, forget it
				self._displayedFileEntries.pop(fileEntryToLoad)
			self.showFileData(fileEntryToLoad)

	def showFileData(self, fileEntryToShow: FileEntry):
		dataToShow = GGPackParser.getConvertedPackedFile(fileEntryToShow)
		widgetToShow: BaseFileEntryDisplayWidget = None
		if isinstance(dataToShow, str):
			widgetToShow = TextDisplayWidget(fileEntryToShow, dataToShow)
		elif isinstance(dataToShow, dict):
			widgetToShow = TextDisplayWidget(fileEntryToShow, json.dumps(dataToShow, indent=2))
		elif isinstance(dataToShow, Image):
			widgetToShow = ImageDisplayWidget(fileEntryToShow, ImageQt.toqpixmap(dataToShow))
		elif isinstance(dataToShow, List) and isinstance(dataToShow[0], List) and isinstance(dataToShow[0][0], str):
			widgetToShow = TableDisplayWidget(fileEntryToShow, dataToShow)
		elif isinstance(dataToShow, bytes):
			# These need a bit more parsing, depending on file extension
			fileExtension = os.path.splitext(fileEntryToShow.filename)[-1]
			if fileExtension in ('.otf', '.ttf'):
				widgetToShow = FontDisplayWidget(fileEntryToShow, dataToShow)
		if not widgetToShow:
			raise NotImplementedError(f"Showing file entry '{fileEntryToShow}' has not been implemented yet")
		newSubWindow = self.centerDisplayArea.addSubWindow(widgetToShow)
		newSubWindow.setWindowTitle(fileEntryToShow.filename)
		self._displayedFileEntries[fileEntryToShow] = newSubWindow
		widgetToShow.close.connect(self._handleClosedSubwindow)
		newSubWindow.show()

	def saveTabData(self, shouldConvertData: bool):
		"""
		Saves the current tab's data to disk.
		:param shouldConvertData: If True, saves exactly how it's stored in the game (ktxbz als ktxbz, ggdicted-json as ggdicted-json, ect). If False, Exports the data into something that can be used outside the game (ktxbz to png, gdicted-jsons to actual jsons, etc)
		"""
		activeSubWindow = self.centerDisplayArea.activeSubWindow()
		if activeSubWindow:
			for fileEntry, subWindow in self._displayedFileEntries.items():
				if subWindow == activeSubWindow:
					# Some files don't need converting, they can be saved as-is
					if not shouldConvertData or fileEntry.fileExtension in ('.bank', '.otf', '.png', '.tsv', '.ttf', 'txt'):
						# 'getSaveFilename' returns a tuple with the path and the filter used, we only need the former, hence the '[0]' at the end
						savePath = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", dir=fileEntry.filename)[0]
						# If the user cancels, the dialog returns None
						if savePath:
							savePath = savePath[0]
							with open(savePath, 'wb') as saveFile:
								saveFile.write(GGPackParser.getPackedFile(fileEntry))
					else:
						# Since files now don't get saved as their original extension, add a suffix if needed
						fileData = GGPackParser.getConvertedPackedFile(fileEntry)
						saveDialogFilterString = fileEntry.filename
						if isinstance(fileData, str):
							saveDialogFilterString += '.txt'
						elif isinstance(fileData, dict):
							saveDialogFilterString += '.json'
							fileData = json.dumps(fileData, indent=2)
						elif isinstance(fileData, Image):
							saveDialogFilterString += '.png'
						# 'getSaveFilename' returns a tuple with the path and the filter used, we only need the former, hence the '[0]' at the end
						savePath = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", dir=saveDialogFilterString)[0]
						# If the user cancels, the dialog returns None
						if savePath:
							if isinstance(fileData, Image):
								fileData.save(savePath)
							else:
								writeMode = 'w' if isinstance(fileData, str) else 'wb'
								with open(savePath, writeMode) as saveFile:
									saveFile.write(fileData)
					return
			else:
				print(f"Active subwindow and fileEntry not found in tab list")

	@QtCore.Slot(FileEntry)
	def _handleClosedSubwindow(self, fileEntryOfClosedSubwindow: FileEntry):
		self._displayedFileEntries.pop(fileEntryOfClosedSubwindow, None)

	def _closeAllTabs(self):
		self.centerDisplayArea.closeAllSubWindows()
		self._displayedFileEntries.clear()

	def _closeOtherTabs(self):
		self.__closeSomeTabs(True, True)

	def _closeTabsToLeft(self):
		self.__closeSomeTabs(True, False)

	def _closeTabsToRight(self):
		self.__closeSomeTabs(False, True)

	def __closeSomeTabs(self, closeBeforeCurrent: bool, closeAfterCurrent: bool):
		activeSubwindow = self.centerDisplayArea.activeSubWindow()
		if not activeSubwindow:
			# If no subwindow is active, for instance if none exist, no need to do anything
			return
		subwindowList = self.centerDisplayArea.subWindowList(QtWidgets.QMdiArea.WindowOrder.CreationOrder)
		if len(subwindowList) == 1:
			# No other subwindows, so no need to close anything
			return
		activeSubwindowIndex = subwindowList.index(activeSubwindow)
		if closeBeforeCurrent:
			for subwindow in subwindowList[:activeSubwindowIndex]:
				subwindow.close()
		if closeAfterCurrent:
			for subwindow in subwindowList[activeSubwindowIndex + 1:]:
				subwindow.close()
