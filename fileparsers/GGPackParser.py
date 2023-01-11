# Handles parsing the .ggpack files, that contain the other files
import io, json, os
from typing import Dict, List, Tuple, Union

import fsb5
from PIL import Image

import Keys, Utils
from CustomExceptions import DecodeError, PackingError
from enums.Game import Game
from fileparsers import BankParser, DinkParser, GGDictParser, KtxParser, NutParser, YackParser
from models.FileEntry import FileEntry


# This GUID is added to all the pack file indexes, not sure what it's based on
_FILE_INDEX_GUID = "b554baf88ff004c50cc0214575794b8c"

def decodeGameData(encodedGameData: bytes, game: Game, decodeLengthLimit: int = 0) -> bytes:
	if game == Game.THIMBLEWEED_PARK:
		return _decodeThimbleweedParkGamedata(encodedGameData, decodeLengthLimit)
	elif game == Game.DELORES:
		return _decodeDeloresGameData(encodedGameData, decodeLengthLimit)
	elif game == Game.RETURN_TO_MONKEY_ISLAND:
		return _decodeRtmiGameData(encodedGameData, decodeLengthLimit)
	raise NotImplementedError(f"Decoding for the game '{game}' is not implemented")

def _decodeThimbleweedParkGamedata(encodedGameData: bytes, decodeLengthLimit: int = 0) -> bytes:
	# From https://github.com/bgbennyboy/Dinky-Explorer/blob/master/ThimbleweedLibrary/UnbreakableXOR.cs#L59
	encodedGameDataLength = len(encodedGameData)
	decodedByteArray = bytearray(encodedGameDataLength)
	decodeSum = encodedGameDataLength & 255
	indexLimit = min(encodedGameDataLength, decodeLengthLimit) if decodeLengthLimit > 0 else encodedGameDataLength
	for index in range(indexLimit):
		decodedByte = (index & 255) * Keys.THIMBLEWEED_PARK_MAGIC_NUMBER
		decodedByte = (decodedByte ^ Keys.THIMBLEWEED_PARK_KEY[index & 15]) & 255
		decodedByte = (decodedByte ^ decodeSum) & 255
		decodedByteArray[index] = encodedGameData[index] ^ decodedByte
		decodeSum = decodeSum ^ decodedByteArray[index]
	# Thimbleweed Park needs some extra decoding
	for index in range(5, indexLimit - 1, 16):
		decodedByteArray[index] = decodedByteArray[index] ^ Keys.THIMBLEWEED_PARK_EXTRA_DECODE_NUMBER
		decodedByteArray[index + 1] = decodedByteArray[index + 1] ^ Keys.THIMBLEWEED_PARK_EXTRA_DECODE_NUMBER
	return bytes(decodedByteArray)

def _decodeDeloresGameData(encodedGameData: bytes, decodeLengthLimit: int = 0) -> bytes:
	# From https://github.com/fzipp/gg/blob/main/crypt/xor/twp/decode.go and https://github.com/bgbennyboy/Dinky-Explorer/blob/master/ThimbleweedLibrary/UnbreakableXOR.cs#L59
	encodedGameDataLength = len(encodedGameData)
	decodedByteArray = bytearray(encodedGameDataLength)
	decodeSum = encodedGameDataLength & 255
	for index in range(min(encodedGameDataLength, decodeLengthLimit) if decodeLengthLimit > 0 else encodedGameDataLength):
		decodedByte = (index & 255) * Keys.DELORES_MAGIC_NUMBER
		decodedByte = (decodedByte ^ Keys.DELORES_KEY[index & 15]) & 255
		decodedByte = (decodedByte ^ decodeSum) & 255
		decodedByteArray[index] = encodedGameData[index] ^ decodedByte
		decodeSum = decodeSum ^ decodedByteArray[index]
	return bytes(decodedByteArray)

def _decodeRtmiGameData(encodedGameData: bytes, decodeLengthLimit: int = 0) -> bytes:
	"""Decodes the provided encoded game data into something parseable"""
	# From https://github.com/bgbennyboy/Thimbleweed-Park-Explorer/blob/master/ThimbleweedLibrary/BundleReader_ggpack.cs#L627
	encodedGameDataLength = len(encodedGameData)
	decodedByteArray = bytearray(encodedGameDataLength)
	decodeSum = (encodedGameDataLength + Keys.RTMI_MAGIC_NUMBER) & 0xFFFF
	for index in range(min(encodedGameDataLength, decodeLengthLimit) if decodeLengthLimit > 0 else encodedGameDataLength):
		key1decodeByte = Keys.RTMI_KEY_1[(decodeSum + Keys.RTMI_MAGIC_NUMBER) & 0xFF]
		key2decodeByte = Keys.RTMI_KEY_2[decodeSum]
		decodedByteArray[index] = (encodedGameData[index] ^ key1decodeByte ^ key2decodeByte)
		decodeSum = (decodeSum + Keys.RTMI_KEY_1[decodeSum & 0xFF]) & 0xFFFF
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
	game: Game = Game.ggpackPathToGameName(gameFilePath)
	decodedFileIndex = decodeGameData(encodedFileIndex, game)
	gameFileIndex = GGDictParser.fromGgDict(decodedFileIndex, game)
	return gameFileIndex

def getPackedFile(fileEntry: FileEntry) -> bytes:
	with open(fileEntry.packFilePath, 'rb') as gameFile:
		gameFile.seek(fileEntry.offset)
		encodedFileData = gameFile.read(fileEntry.size)
	if fileEntry.fileExtension == '.assets.bank':
		# sound bank files aren't encoded
		return encodedFileData
	else:
		return decodeGameData(encodedFileData, fileEntry.game)

def getConvertedPackedFile(fileEntry: FileEntry) -> Union[bytes, Dict, fsb5.FSB5, List, Image.Image, str]:
	fileData = getPackedFile(fileEntry)
	# All extensions and their counts:
	# - Thimbleweed Park: .bnut: 187, .byack: 118, .fnt: 32, .json: 421, .lip: 14,294, .nut: 1, .ogg: 17,272, .png: 566, .tsv: 6, .txt: 42, .wav: 644, .wimpy: 163,
	# - Delores: .bank: 2, .dink: 1, .dinky: 1, .json: 61, .png: 50, .tsv: 9, .ttf: 7, .txt: 2, .wimpy: 22, .yack: 11,
	# - Return To Monkey Island: .anim: 663, .atlas: 663, .attach: 11, .bank: 7, .blend: 112, .dink: 1, .dinky: 1, .emitter: 157, .json: 292, .ktxbz: 1,152, .lip: 19,610, .otf: 5, .png: 3, .tsv: 20, .ttf: 33, .txt: 31, .wimpy: 159, .yack: 66
	# TODO Extensions that need implementing: .bank&.strings.bank: 7, .dink: 1
	if fileEntry.fileExtension in ('.atlas', '.attach', '.blend', '.byack', '.dinky', '.fnt', '.lip', '.nut', '.txt'):
		# Basic text
		return fileData.decode('utf-8')
	elif fileEntry.fileExtension == '.anim':
		# Text formatted as JSON, return a dict
		return json.loads(fileData)
	elif fileEntry.fileExtension in ('.emitter', '.json', '.wimpy'):
		# These files can be either GGDict, JSON, or plain text
		if fileData.startswith(GGDictParser.HEADER):
			return GGDictParser.fromGgDict(fileData, fileEntry.game)
		elif fileData[0] == 0x7B:  # 0x7B is the ASCII code for '{', which a plain JSON file starts with
			return json.loads(fileData)
		else:
			return fileData.decode('utf-8')
	elif fileEntry.fileExtension == '.dink':
		# Dink script, return it parsed
		return DinkParser.DinkParser.fromDinkToScripts(fileData, fileEntry.game)
	elif fileEntry.fileExtension == '.bnut':
		return NutParser.fromBytes(fileData)
	elif fileEntry.fileExtension == '.yack':
		# Yack script. RtMI needs decoding, Delores has it as plain text. Not used in Thimbleweed Park
		if fileEntry.game == Game.RETURN_TO_MONKEY_ISLAND:
			return "\n\n".join(YackParser.fromYack(fileData, fileEntry.filename))
		return fileData.decode('utf-8')
	elif fileEntry.fileExtension in ('.ktx', '.ktxbz'):
		# Compressed image, return it as a Pillow image
		return KtxParser.fromKtx(fileData, fileEntry.filename, 1)[0]
	elif fileEntry.fileExtension == '.png':
		# Basic image, return it as a Pillow image
		return Image.open(io.BytesIO(fileData))
	elif fileEntry.fileExtension == '.tsv':
		# Tab-separated file, return it as a list of lists of strings
		table: List[List[str]] = []
		for row in fileData.decode('utf-8').splitlines():
			rowList = []
			table.append(rowList)
			rowList.extend(row.split('\t'))
		return table
	elif fileEntry.fileExtension in ('.otf', '.ttf'):
		# Font files, return them as they are
		return fileData
	elif fileEntry.fileExtension in ('.ogg', '.wav'):
		# Sound data, return them as they are
		return fileData
	elif fileEntry.fileExtension == '.assets.bank':
		# Music bank file, no need to convert anything
		return BankParser.fromBytesToBank(fileData)
	print(f"Unknown/unsupported file extension '{fileEntry.fileExtension}' for file entry '{fileEntry}'")
	return fileData

def createPackFile(filenamesToPack: Union[List[str], Tuple[str]], packFilename: str, targetGame: Game):
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
			if filenameToPack.endswith('.assets.bank'):
				encodedDataToPack = fileToPack.read()
			else:
				encodedDataToPack = decodeGameData(fileToPack.read(), targetGame)
			fileOffsetsDict['files'].append({"filename": os.path.basename(filenameToPack), "offset": packHeaderSize + len(encodedFilesData), "size": len(encodedDataToPack)})
			encodedFilesData.extend(encodedDataToPack)
	del encodedDataToPack  # Prevent accidentally using 'encodedDataToPack' instead of 'encodedFilesData' later, and save memory usage

	fileIndex = GGDictParser.toGgDict(fileOffsetsDict, targetGame)
	with open(packFilename, 'wb') as packFile:
		# First write the offset to and size of the file index
		packFile.write(Utils.toWritableInt(packHeaderSize + len(encodedFilesData)))
		packFile.write(Utils.toWritableInt(len(fileIndex)))
		# Then write the encoded file data
		packFile.write(encodedFilesData)
		# And finally write the file index
		packFile.write(decodeGameData(fileIndex, targetGame))
