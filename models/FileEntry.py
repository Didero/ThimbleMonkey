import os
from typing import Union

from enums.Game import Game


class FileEntry:
	"""
	This class represents a packed file entry.
	It knows in which ggpack-file it is, and where
	"""

	def __init__(self, filename: str, offset: int, size: int, packFilePath: str, game: Game):
		self.filename: str = filename
		self.offset: int = offset
		self.size: int = size
		self.packFilePath: str = packFilePath

		self._fileExtension: Union[None, str] = None
		self.game: Game = game

	@property
	def fileExtension(self) -> str:
		if self._fileExtension is None:
			# Split at the first period, so we can distinguish between, for instance, '.strings.bank' and '.assets.bank'
			self._fileExtension = '.' + self.filename.split('.', 1)[-1]
		return self._fileExtension

	def __str__(self):
		return f"{self.filename} in {self.packFilePath}"
