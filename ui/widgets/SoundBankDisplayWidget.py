import traceback

import fsb5
from PySide6 import QtCore, QtGui, QtWidgets

from fileparsers import BankParser
from models.FileEntry import FileEntry
from ui import WidgetHelpers
from ui.widgets.BaseFileEntryDisplayWidget import BaseFileEntryDisplayWidget
from ui.widgets.SimpleSoundPanel import SimpleSoundPanel


class SoundBankDisplayWidget(BaseFileEntryDisplayWidget):
	def __init__(self, fileEntry: FileEntry, soundbank: fsb5.FSB5):
		super().__init__(fileEntry)
		layout = QtWidgets.QVBoxLayout(self)
		self.setLayout(layout)

		self._soundPanel = SimpleSoundPanel()
		layout.addWidget(self._soundPanel)

		sampleSelectionWidget = QtWidgets.QTreeWidget(self)
		sampleSelectionWidget.setHeaderLabels(('Name', 'Duration'))
		sampleSelectionWidget.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
		sampleSelectionWidget.setMinimumWidth(450)
		sampleSelectionWidget.sizePolicy().setHorizontalPolicy(QtWidgets.QSizePolicy.MinimumExpanding)
		sampleSelectionWidget.setUniformRowHeights(True)
		sampleSelectionWidget.itemClicked.connect(self._onSampleSelected)
		sampleSelectionWidget.header().setStretchLastSection(False)
		sampleSelectionWidget.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
		layout.addWidget(sampleSelectionWidget)

		self._soundbank = soundbank

		sampleSelectionWidget.setSortingEnabled(False)
		for sampleIndex, sample in enumerate(self._soundbank.samples):
			#layout.addWidget(SimpleSoundPanel(parsedSample, False, f"{sampleIndex+1}. {sample.name}"))
			sampleTreeItem = QtWidgets.QTreeWidgetItem(sampleSelectionWidget)
			sampleTreeItem.setText(0, sample.name)
			sampleDuration = 1 + sample.samples // sample.frequency
			sampleTreeItem.setText(1, f"{sampleDuration // 60}:{sampleDuration % 60:02d}")
			# Store the sample index so we can find it again
			sampleTreeItem.setData(0, int(QtCore.Qt.ItemDataRole.UserRole), sampleIndex)
		sampleSelectionWidget.setSortingEnabled(True)

		sampleCountLabel = QtWidgets.QLabel(f"{len(self._soundbank.samples):,} sounds loaded")
		layout.addWidget(sampleCountLabel)

	@QtCore.Slot(QtWidgets.QTreeWidgetItem, int)
	def _onSampleSelected(self, itemToLoad: QtWidgets.QTreeWidgetItem, clickedColumnIndex: int):
		sampleIndexToLoad = itemToLoad.data(0, int(QtCore.Qt.ItemDataRole.UserRole))
		sampleToLoad = self._soundbank.samples[sampleIndexToLoad]
		try:
			parsedSample = BankParser.rebuildSample(self._soundbank, sampleToLoad)
		except Exception as e:
			traceback.print_exc()
			WidgetHelpers.showErrorMessage("Error while loading sound",
										   f"Something went wrong when trying to play the selected sound.\nThat could mean a problem with loading the Ogg Vorbis libraries.\n\nThe exact error is: {e}")
		else:
			self._soundPanel.setAudioData(parsedSample, '.ogg', True, sampleToLoad.name)

	@staticmethod
	def _getDuration(bufferLength: int, channelCount: int, bytesPerSample: int, frequency: float) -> int:
		# Calculation copied from PyDub
		sampleSize = channelCount * bytesPerSample
		sampleCount = bufferLength // sampleSize
		durationInSeconds = sampleCount / frequency
		return int(durationInSeconds) + 1  # +1 because int() truncates, so rounds down

	def closeEvent(self, event: QtGui.QCloseEvent) -> None:
		self._soundPanel.stopSound()
		super().closeEvent(event)
