import json, os, traceback
import time
from typing import List, Union
from weakref import WeakValueDictionary

import fsb5
from PIL import ImageQt
from PIL.Image import Image
from PySide6 import QtCore, QtGui, QtWidgets

from enums.Game import Game
from fileparsers import GGPackParser
from fileparsers.dinkhelpers.DinkScript import DinkScript
from models.FileEntry import FileEntry
from ui import WidgetHelpers
from ui.dialogs.SaveProgressDialog import SaveProgressDialog
from ui.widgets.BaseFileEntryDisplayWidget import BaseFileEntryDisplayWidget
from ui.widgets.DinkDisplayWidget import DinkDisplayWidget
from ui.widgets.FontDisplayWidget import FontDisplayWidget
from ui.widgets.ImageDisplayWidget import ImageDisplayWidget
from ui.widgets.PackedFilesBrowserWidget import PackedFilesBrowserWidget
from ui.widgets.SoundBankDisplayWidget import SoundBankDisplayWidget
from ui.widgets.SoundDisplayWidget import SoundDisplayWidget
from ui.widgets.TableDisplayWidget import TableDisplayWidget
from ui.widgets.TextDisplayWidget import TextDisplayWidget


class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, pathToLoadOnStart: str = None, filterOnStart: str = None):
		super().__init__()
		self.resize(1920, 1080)
		self._centerWindowOnScreen()
		self._initUi()
		self._initMenuBar()
		self.setStatusBar(QtWidgets.QStatusBar(self))
		# Accept drops to enable drag&drop-ing a folder to load it (see the methods 'dragEnterEvent' and 'dropEvent')
		self.setAcceptDrops(True)

		self.gamePath: str = ''
		# Store the opened subwindows in here, so we can't open one file multiple times (Don't use filenames for this, with mods there can be duplicates)
		self._displayedFileEntries: WeakValueDictionary[FileEntry, QtWidgets.QMdiSubWindow] = WeakValueDictionary()

		if pathToLoadOnStart:
			self.setGamePath(pathToLoadOnStart)
		if filterOnStart:
			self.packedFileBrowser.filterFileBrowser(filterOnStart)

	def _centerWindowOnScreen(self):
		frameGm = self.frameGeometry()
		screen = QtGui.QGuiApplication.primaryScreen()
		centerPoint = screen.availableGeometry().center()
		frameGm.moveCenter(centerPoint)
		self.move(frameGm.topLeft())

	def _initUi(self):
		self.updateWindowTitle()
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
		saveSubmenu = fileMenu.addMenu("&Save...")
		convertAndSaveSubmenu = fileMenu.addMenu("&Convert and save...")
		for submenu, shouldConvert, saveDialogTitlePrefix in ((saveSubmenu, False, "Save"), (convertAndSaveSubmenu, True, "Convert And Save")):
			# 'isChecked' is a possible default value from PySide6, and we need to make 'shouldConvert' local to the lambda otherwise it'll just be the last value (in this case True)
			WidgetHelpers.createMenuAction(submenu, "&current tab", lambda isChecked=False, shouldConvert=shouldConvert: self.saveFileEntries([self.getCurrentTabFileEntry()], shouldConvert, f"{saveDialogTitlePrefix} Current Tab"))
			WidgetHelpers.createMenuAction(submenu, "&open tabs", lambda isChecked=False, shouldConvert=shouldConvert: self.saveFileEntries(list(self._displayedFileEntries.keys()), shouldConvert, f"{saveDialogTitlePrefix} Open Tabs"))
			WidgetHelpers.createMenuAction(submenu, "&filtered files", lambda isChecked=False, shouldConvert=shouldConvert: self.saveFileEntries(self.packedFileBrowser.getFilteredFileEntries(), shouldConvert, f"{saveDialogTitlePrefix} Filtered Files"))
			WidgetHelpers.createMenuAction(submenu, "&all files", lambda isChecked=False, shouldConvert=shouldConvert: self.saveFileEntries(self.packedFileBrowser.getAllFileEntries(), shouldConvert, f"{saveDialogTitlePrefix} All Files"))
		fileMenu.addSeparator()
		WidgetHelpers.createMenuAction(fileMenu, "E&xit", self.close, "Exits the application")

		tabMenu = self.menuBar().addMenu("&Tabs")
		WidgetHelpers.createMenuAction(tabMenu, "Close &all tabs", self._closeAllTabs, "Close all the opened file display tabs")
		WidgetHelpers.createMenuAction(tabMenu, "Close &other tabs", self._closeOtherTabs, "Closes all the opened file display tabs, except the current tab")
		WidgetHelpers.createMenuAction(tabMenu, "Close tabs to the &left", self._closeTabsToLeft, "Closes all file display tabs to the left of the current tab")
		WidgetHelpers.createMenuAction(tabMenu, "Close tabs to the &right", self._closeTabsToRight, "Closes all file display tabs to the right of the current tab")

		linksMenu = self.menuBar().addMenu("&Links")
		WidgetHelpers.createMenuAction(linksMenu, "&ThimbleMonkey on GitHub", lambda: QtGui.QDesktopServices.openUrl("https://github.com/Didero/ThimbleMonkey"))
		WidgetHelpers.createMenuAction(linksMenu, "ThimbleMonkey &Releases", lambda: QtGui.QDesktopServices.openUrl("https://github.com/Didero/ThimbleMonkey/releases"))
		linksMenu.addSeparator()
		WidgetHelpers.createMenuAction(linksMenu, "Thimbleweed &Park", lambda: QtGui.QDesktopServices.openUrl("https://thimbleweedpark.com"))
		WidgetHelpers.createMenuAction(linksMenu, "Delores on &GitHub", lambda: QtGui.QDesktopServices.openUrl("https://github.com/grumpygamer/DeloresDev"))
		WidgetHelpers.createMenuAction(linksMenu, "&Delores on Steam", lambda: QtGui.QDesktopServices.openUrl("https://store.steampowered.com/app/1305720/Delores_A_Thimbleweed_Park_MiniAdventure"))
		WidgetHelpers.createMenuAction(linksMenu, "Return To &Monkey Island", lambda: QtGui.QDesktopServices.openUrl("https://returntomonkeyisland.com"))
		linksMenu.addSeparator()
		WidgetHelpers.createMenuAction(linksMenu, "Terrible Toy&box", lambda: QtGui.QDesktopServices.openUrl("https://terribletoybox.com"))

	def updateWindowTitle(self, titleSuffix: str = None):
		windowTitle = f"{QtWidgets.QApplication.applicationName()} v1.0.0"
		if titleSuffix:
			windowTitle += f" - {titleSuffix}"
		self.setWindowTitle(windowTitle)

	@QtCore.Slot()
	def _browseForGamePath(self):
		path = QtWidgets.QFileDialog.getExistingDirectory(self, "Load Game Folder", dir=self.gamePath)
		# 'path' is None if the file dialog is dismissed
		if path:
			self.setGamePath(path)

	def setGamePath(self, gamePath: str):
		packedFileEntries: List[FileEntry] = []
		packedFilePaths = self._getPackFilesInFolder(gamePath)
		if len(packedFilePaths) == 0:
			WidgetHelpers.showErrorMessage("No files found", f"The folder\n{gamePath}\ndoes not contain any supported game files")
			return
		for packFilePath in packedFilePaths:
			try:
				fileIndex = GGPackParser.getFileIndex(packFilePath)
				game = Game.ggpackPathToGameName(packFilePath)
				for fileEntryData in fileIndex['files']:
					fileEntry = FileEntry(fileEntryData['filename'], fileEntryData['offset'], fileEntryData['size'], packFilePath, game)
					packedFileEntries.append(fileEntry)
			except Exception as e:
				traceback.print_exc()
				WidgetHelpers.showErrorMessage("Error Opening GGPack", f"An error occurred while trying to load '{packFilePath}':\n\n{e}")
		self.gamePath = gamePath
		self.updateWindowTitle(gamePath)
		self.packedFileBrowser.showFilesInFileBrowser(packedFileEntries)

	def _getPackFilesInFolder(self, pathToCheck: str) -> List[str]:
		if not os.path.exists(pathToCheck):
			print(f"Provided path to check for ggpack files '{pathToCheck}' does not exist")
			return []
		packPaths: List[str] = []
		for fn in os.listdir(pathToCheck):
			gameFilePath = os.path.join(pathToCheck, fn)
			if os.path.isdir(gameFilePath):
				if fn == 'Resources':
					# Thimbleweed Park stores its ggpacks in the 'Resources' subfolder
					packPaths.extend(self._getPackFilesInFolder(gameFilePath))
				elif fn.endswith('.app'):
					# MacOS stores its games inside an .app executable folder, find the ggpacks inside there
					packPaths.extend(self._getPackFilesInFolder(os.path.join(gameFilePath, 'Contents', 'Resources')))
				elif fn == 'Contents':
					# If the .app folder itself is dragged onto ThimbleMonkey, we need to look inside the Contents/Resources folder
					packPaths.extend(self._getPackFilesInFolder(os.path.join(gameFilePath, 'Resources')))
			elif '.ggpack' in fn:
				packPaths.append(gameFilePath)
		return packPaths

	@QtCore.Slot(FileEntry)
	def loadFileFromFileBrowser(self, fileEntryToLoad: FileEntry):
		if fileEntryToLoad in self._displayedFileEntries and self._displayedFileEntries[fileEntryToLoad] in self.centerDisplayArea.subWindowList():
			subwindow = self._displayedFileEntries[fileEntryToLoad]
			self.centerDisplayArea.setActiveSubWindow(subwindow)
		else:
			if fileEntryToLoad in self._displayedFileEntries:
				# Apparently the window isn't shown anymore, forget it
				self._displayedFileEntries.pop(fileEntryToLoad)
			try:
				self.showFileData(fileEntryToLoad)
			except Exception as e:
				traceback.print_exc()
				WidgetHelpers.showErrorMessage("Error Showing File", f"An error occurred while trying to display '{fileEntryToLoad.filename}':\n\n{e}")

	def showFileData(self, fileEntryToShow: FileEntry):
		dataToShow = GGPackParser.getConvertedPackedFile(fileEntryToShow)
		widgetToShow: Union[None, BaseFileEntryDisplayWidget] = None
		if isinstance(dataToShow, str):
			widgetToShow = TextDisplayWidget(fileEntryToShow, dataToShow)
		elif isinstance(dataToShow, dict):
			firstDictEntry = next(iter(dataToShow.items()))[1]
			if isinstance(firstDictEntry, DinkScript):
				widgetToShow = DinkDisplayWidget(fileEntryToShow, dataToShow)
			else:
				widgetToShow = TextDisplayWidget(fileEntryToShow, json.dumps(dataToShow, indent=2))
		elif isinstance(dataToShow, Image):
			widgetToShow = ImageDisplayWidget(fileEntryToShow, ImageQt.toqpixmap(dataToShow))
		elif isinstance(dataToShow, List) and isinstance(dataToShow[0], List) and isinstance(dataToShow[0][0], str):
			widgetToShow = TableDisplayWidget(fileEntryToShow, dataToShow)
		elif isinstance(dataToShow, bytes):
			# These need a bit more parsing, depending on file extension
			if fileEntryToShow.fileExtension in ('.otf', '.ttf'):
				widgetToShow = FontDisplayWidget(fileEntryToShow, dataToShow)
			elif fileEntryToShow.fileExtension in ('.mp3', '.ogg', '.wav'):
				widgetToShow = SoundDisplayWidget(fileEntryToShow, dataToShow)
		elif isinstance(dataToShow, fsb5.FSB5):
			widgetToShow = SoundBankDisplayWidget(fileEntryToShow, dataToShow)
		if not widgetToShow:
			raise NotImplementedError(f"Showing files with extension '{fileEntryToShow.fileExtension}' has not been implemented yet")
		fileEntryToShow.convertedData = dataToShow
		newSubWindow = self.centerDisplayArea.addSubWindow(widgetToShow)
		newSubWindow.setWindowTitle(fileEntryToShow.filename)
		self._displayedFileEntries[fileEntryToShow] = newSubWindow
		widgetToShow.close.connect(self._handleClosedSubwindow)
		newSubWindow.show()

	def getCurrentTabFileEntry(self) -> Union[None, FileEntry]:
		activeSubWindow = self.centerDisplayArea.activeSubWindow()
		if activeSubWindow:
			for fileEntry, subWindow in self._displayedFileEntries.items():
				if subWindow == activeSubWindow:
					return fileEntry
		return None

	def saveFileEntries(self, fileEntries: List[FileEntry], shouldConvertData: bool, saveDialogTitle="Save Files To Folder"):
		if not fileEntries or fileEntries[0] is None:
			WidgetHelpers.showErrorMessage("Nothing To Save", "There are no file entries to save")
			return
		elif len(fileEntries) > 100:
			if not WidgetHelpers.askConfirmation("Many Files To Save", f"This would save {len(fileEntries):,} files, which might take a while,\nand might use a lot of memory and/or CPU power.", "Are you sure you want to continue?"):
				return
		savePath = QtWidgets.QFileDialog.getExistingDirectory(self, saveDialogTitle, dir=self.gamePath)
		if not savePath:
			# User cancelled
			return
		startTime = time.perf_counter()
		# Open the progress dialog, which also does the saving
		saveProgressDialog = SaveProgressDialog(fileEntries, savePath, shouldConvertData, self)
		# Show the results
		saveDuration = time.perf_counter() - startTime
		if saveDuration > 60:
			saveDurationString = f"{saveDuration // 60:.0f} minutes and {saveDuration % 60:.0f} seconds"
		else:
			saveDurationString = f"{saveDuration:.0f} seconds"
		saveTypeString = "converting and saving" if shouldConvertData else "saving"
		finishTitle = f"Finished {saveTypeString.title()}"
		finishMessage = f"Finished {saveTypeString} {len(fileEntries):,} files to\n{savePath}\nin {saveDurationString}."
		if len(saveProgressDialog.saveErrors) > 0:
			finishMessage += f"\n{len(saveProgressDialog.saveErrors):,} save errors:"
			for errorFileEntry, error in saveProgressDialog.saveErrors.items():
				finishMessage += f"\n{errorFileEntry.filename}: {error}"
			WidgetHelpers.showErrorMessage(finishTitle, finishMessage)
		else:
			WidgetHelpers.showInfoMessage(finishTitle, finishMessage)

	@QtCore.Slot(FileEntry)
	def _handleClosedSubwindow(self, fileEntryOfClosedSubwindow: FileEntry):
		fileEntryOfClosedSubwindow.convertedData = None
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

	def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
		# Handle a file or folder dragged onto the window. Only allow folders
		if not event.mimeData().hasUrls():
			return event.ignore()
		urls = event.mimeData().urls()
		# Only accept a single dropped item, to avoid confusion
		if len(urls) != 1:
			return event.ignore()
		# Only accept a folder as a new gamepath
		url: QtCore.QUrl = urls[0]
		if not url.isLocalFile():
			return event.ignore()
		dragFilePath = url.toLocalFile()
		if not os.path.isdir(dragFilePath):
			return event.ignore()
		# Everything's good, mark the dragged item as acceptable
		event.accept()

	def dropEvent(self, event: QtGui.QDropEvent) -> None:
		# We can just get the path without any checks, because those checks are done in the 'dragEnterEvent' method
		dropPath = event.mimeData().urls()[0].toLocalFile()
		self.setGamePath(dropPath)
