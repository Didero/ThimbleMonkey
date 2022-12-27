import pyogg, simpleaudio
from PySide6 import QtCore, QtWidgets

from ui import WidgetHelpers


class SimpleSoundPanel(QtWidgets.QWidget):
	def __init__(self, audioData: bytes = None, fileExtension: str = None, shouldAutoplay: bool = True, title: str = None):
		super().__init__()

		self._fileExtension: str = ""
		self._audioData = None
		self._soundFile = None
		self._player = None
		self._durationDisplayUpdateTimer = QtCore.QTimer(self)
		self._durationDisplayUpdateTimer.setInterval(1000)
		self._durationDisplayUpdateTimer.timeout.connect(self._onTimerUpdate)
		self._totalPlaytimeSeconds: int = 0
		self._totalPlaytimeDisplayString: str = SimpleSoundPanel._formatDuration(self._totalPlaytimeSeconds)
		self._currentPlayTimeSeconds: int = 0

		layout = QtWidgets.QHBoxLayout(self)
		self.setLayout(layout)
		self._titleLabel = QtWidgets.QLabel(title)
		layout.addWidget(self._titleLabel)
		self._durationLabel = QtWidgets.QLabel(self._totalPlaytimeDisplayString)
		layout.addWidget(self._durationLabel)
		WidgetHelpers.createButton("Play", self._playSound, layout)
		WidgetHelpers.createButton("Stop", self.stopSound, layout)
		self._shouldLoopCheckbox = QtWidgets.QCheckBox("Loop")
		layout.addWidget(self._shouldLoopCheckbox)
		self._saveButton = WidgetHelpers.createButton("Save", self._saveSound, layout)
		layout.addStretch(10)

		if audioData and fileExtension:
			self.setAudioData(audioData, fileExtension, shouldAutoplay, title)
		else:
			self._updateDurationLabel()
			self._saveButton.hide()

	def setAudioData(self, audioData: bytes, fileExtension: str, shouldAutoplay: bool = False, title: str = None):
		self.stopSound()
		self._fileExtension = fileExtension
		# Since we can seemingly only play files, we need to save the sound data to a temporary file
		self._audioData = audioData
		tempFile = QtCore.QTemporaryFile()
		tempFile.open()
		tempFile.write(audioData)
		tempFile.close()

		if fileExtension == '.ogg':
			self._soundFile = pyogg.VorbisFile(tempFile.fileName())
			self._totalPlaytimeSeconds = SimpleSoundPanel._getDuration(len(self._soundFile.buffer), self._soundFile.channels, self._soundFile.bytes_per_sample, self._soundFile.frequency)
		elif fileExtension == '.wav':
			self._soundFile = simpleaudio.WaveObject.from_wave_file(tempFile.fileName())
			self._totalPlaytimeSeconds = SimpleSoundPanel._getDuration(len(self._soundFile.audio_data), self._soundFile.num_channels, self._soundFile.bytes_per_sample, self._soundFile.sample_rate)
		else:
			self._soundFile = None
			raise NotImplementedError(f"Playing sound in the '{fileExtension}' sound format is not supported")
		self._totalPlaytimeDisplayString = SimpleSoundPanel._formatDuration(self._totalPlaytimeSeconds)

		if title:
			self._titleLabel.setText(title)
			self._saveButton.show()
		else:
			self._titleLabel.clear()
			self._saveButton.hide()

		if shouldAutoplay:
			self._playSound()
		else:
			self._updateDurationLabel()

	def _playSound(self):
		if self._fileExtension == '.ogg':
			self._player = simpleaudio.play_buffer(self._soundFile.buffer, self._soundFile.channels, self._soundFile.bytes_per_sample, self._soundFile.frequency)
		elif self._fileExtension == '.wav':
			self._player = self._soundFile.play()
		else:
			raise NotImplementedError(f"Playing sound for the '{self._fileExtension}' sound format is not supported")
		self._durationDisplayUpdateTimer.start()
		self._updateDurationLabel()

	def _onTimerUpdate(self):
		self._currentPlayTimeSeconds += self._durationDisplayUpdateTimer.interval() // 1000
		if self._currentPlayTimeSeconds > self._totalPlaytimeSeconds:
			# Playtime finished
			self.stopSound()
			if self._shouldLoopCheckbox.isChecked():
				self._playSound()
		else:
			self._updateDurationLabel()

	def _updateDurationLabel(self):
		timeLeft = self._totalPlaytimeSeconds - self._currentPlayTimeSeconds
		self._durationLabel.setText(f"{self._totalPlaytimeDisplayString} | {self._formatDuration(self._currentPlayTimeSeconds)} / -{self._formatDuration(timeLeft)}")

	def stopSound(self):
		if self._player is not None:
			self._player.stop()
			self._durationDisplayUpdateTimer.stop()
			self._currentPlayTimeSeconds = 0
			self._player = None
			self._updateDurationLabel()

	def _saveSound(self):
		title = self._titleLabel.text()
		if not self._audioData or not title:
			raise ValueError("Unable to save, sound data or title not set")
		# 'getSaveFilename' returns a tuple with the path and the filter used, we only need the former, hence the '[0]' at the end
		savePath = QtWidgets.QFileDialog.getSaveFileName(self, "Save Sound", dir=title + self._fileExtension)[0]
		if savePath:
			with open(savePath, 'wb') as saveFile:
				saveFile.write(self._audioData)

	@staticmethod
	def _getDuration(bufferLength: int, channelCount: int, bytesPerSample: int, frequency: float) -> int:
		# Calculation adapted from PyDub
		sampleSize = channelCount * bytesPerSample
		sampleCount = bufferLength // sampleSize
		durationInSeconds = sampleCount / frequency
		return int(durationInSeconds) + 1  # +1 because int() truncates, so rounds down

	@staticmethod
	def _formatDuration(durationSeconds: int) -> str:
		return f"{durationSeconds // 60}:{durationSeconds % 60:02d}"
