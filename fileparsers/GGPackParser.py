# Handles parsing the .ggpack files, that contain the other files
import io, json, os
from typing import Dict, List, Tuple, Union

from PIL import Image

import Keys, Utils
from CustomExceptions import DecodeError, PackingError
from fileparsers import DinkParser, KtxParser, GGDictParser, YackParser
from models.FileEntry import FileEntry


# This GUID is added to all the pack file indexes, not sure what it's based on
_FILE_INDEX_GUID = "b554baf88ff004c50cc0214575794b8c"

def decodeGameData(encodedGameData: bytes, decodeLengthLimit=0) -> bytes:
	"""Decodes the provided encoded game data into something parseable"""
	# From https://github.com/bgbennyboy/Thimbleweed-Park-Explorer/blob/master/ThimbleweedLibrary/BundleReader_ggpack.cs#L627
	encodedGameDataLength = len(encodedGameData)
	decodedByteArray = bytearray(encodedGameDataLength)
	decodeSum = ((len(encodedGameData)) + Keys.MAGIC_NUMBER) & 0xFFFF
	for index in range(min(encodedGameDataLength, decodeLengthLimit) if decodeLengthLimit else encodedGameDataLength):
		key1decodeByte = Keys.KEY_1[(decodeSum + Keys.MAGIC_NUMBER) & 0xFF]
		key2decodeByte = Keys.KEY_2[decodeSum]
		decodedByteArray[index] = (encodedGameData[index] ^ key1decodeByte ^ key2decodeByte)
		decodeSum = (decodeSum + Keys.KEY_1[decodeSum & 0xFF]) & 0xFFFF
	return bytes(decodedByteArray)

def getFileIndex(gameFilePath: str) -> Dict:
	with open(gameFilePath, 'rb') as gameFile:
		fileSize = os.path.getsize(gameFilePath)
		dataOffset = Utils.readInt(gameFile)
		dataSize = Utils.readInt(gameFile)
		if dataSize < 1:
			raise DecodeError(f"Invalid data size of {dataSize}")
		if dataOffset + dataSize > fileSize:
			raise DecodeError(f"Found an offset of {dataOffset:,} and a data size of {dataSize:,}, totalling {dataOffset + dataSize:,}, but the file is only {fileSize:,} bytes on disk")
		gameFile.seek(dataOffset)
		encodedFileIndex = gameFile.read(dataSize)
	decodedFileIndex = decodeGameData(encodedFileIndex)
	gameFileIndex = GGDictParser.fromGgDict(decodedFileIndex, True)
	return gameFileIndex

def getPackedFile(fileEntry: FileEntry) -> bytes:
	with open(fileEntry.packFilePath, 'rb') as gameFile:
		gameFile.seek(fileEntry.offset)
		encodedFileData = gameFile.read(fileEntry.size)
	if fileEntry.filename.endswith('.bank'):
		# sound bank files aren't encoded
		return encodedFileData
	else:
		return decodeGameData(encodedFileData)

def getConvertedPackedFile(fileEntry: FileEntry) -> Union[bytes, Dict, List, Image.Image, str]:
	fileExtension = os.path.splitext(fileEntry.filename)[-1]
	fileData = getPackedFile(fileEntry)
	# All extensions and their counts: .anim: 663, .atlas: 663, .attach: 11, .bank: 7, .blend: 112, .dink: 1, .dinky: 1, .emitter: 157, .json: 292, .ktxbz: 1,152, .lip: 19,610, .otf: 5, .png: 3, .tsv: 20, .ttf: 33, .txt: 31, .wimpy: 159, .yack: 66
	# TODO Extensions that need implementing: .bank: 7, .dink: 1
	if fileExtension in ('.atlas', '.blend', '.dinky', '.lip', '.txt'):
		# Basic text
		return fileData.decode('utf-8')
	elif fileExtension in ('.anim', '.attach'):
		# Text formatted as JSON, return a dict
		return json.loads(fileData)
	elif fileExtension in ('.emitter', '.json', '.wimpy'):
		# A GGDict, parse it to a dict and return that
		return GGDictParser.fromGgDict(fileData, True)
	elif fileExtension == '.dink':
		# Dink script, return it parsed
		return DinkParser.DinkParser.fromDink(fileData)
	elif fileExtension == '.yack':
		# Yack script, return it parsed
		return "\n\n".join(YackParser.fromYack(fileData, fileEntry.filename))
	elif fileExtension in ('.ktx', '.ktxbz'):
		# Compressed image, return it as a Pillow image
		return KtxParser.fromKtx(fileData, fileEntry.filename, 1)[0]
	elif fileExtension == '.png':
		# Basic image, return it as a Pillow image
		return Image.open(io.BytesIO(fileData))
	elif fileExtension == '.tsv':
		# Tab-separated file, return it as a list of lists of strings
		table: List[List[str]] = []
		for row in fileData.decode('utf-8').splitlines():
			rowList = []
			table.append(rowList)
			rowList.extend(row.split('\t'))
		return table
	elif fileExtension in ('.otf', '.ttf'):
		# Font files, return them as they are
		return fileData
	print(f"Unknown/unsupported file extension '{fileExtension}' for file entry '{fileEntry}'")
	return fileData

def createPackFile(filenamesToPack: Union[List[str], Tuple[str]], packFilename: str):
	"""Pack the files from the provided filenames into a ggpack that the game can recognise"""
	print(f"Creating pack file '{packFilename}' with {len(filenamesToPack):,} file(s)")
	packHeaderSize = 8  # A pack file starts with two ints, so take that into account when storing offsets
	fileOffsetsDict = {"files": [], "guid": _FILE_INDEX_GUID}
	# First collect the data we need
	encodedFilesData = bytearray()
	for filenameToPack in filenamesToPack:
		if not os.path.isfile(filenameToPack):
			raise PackingError(f"Asked to pack file '{filenameToPack}' but that file doesn't exist")
		with open(filenameToPack, 'rb') as fileToPack:
			# .bank files contain music and sounds, and are stored unencoded
			if filenameToPack.endswith('.bank'):
				encodedDataToPack = fileToPack.read()
			else:
				encodedDataToPack = decodeGameData(fileToPack.read())
			fileOffsetsDict['files'].append({"filename": os.path.basename(filenameToPack), "offset": packHeaderSize + len(encodedFilesData), "size": len(encodedDataToPack)})
			encodedFilesData.extend(encodedDataToPack)
	del encodedDataToPack  # Prevent accidentally using 'encodedDataToPack' instead of 'encodedFilesData' later, and save memory usage

	fileIndex = GGDictParser.toGgDict(fileOffsetsDict, True)
	with open(packFilename, 'wb') as packFile:
		# First write the offset to and size of the file index
		packFile.write(Utils.toWritableInt(packHeaderSize + len(encodedFilesData)))
		packFile.write(Utils.toWritableInt(len(fileIndex)))
		# Then write the encoded file data
		packFile.write(encodedFilesData)
		# And finally write the file index
		packFile.write(decodeGameData(fileIndex))
