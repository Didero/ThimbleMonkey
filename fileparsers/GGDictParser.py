"""
Thimbleweed Park, Delores, and Return To Monkey Island store some data in a specialised format called a GGDict
This class can read, parse, and write them
"""

from enum import Enum
from io import BytesIO
from typing import Any, Dict, List

import Utils
from CustomExceptions import DecodeError, GGDictError
from enums.Game import Game


class _ValueType(Enum):
	NULL = b'\x01'
	DICT = b'\x02'
	ARRAY = b'\x03'
	STRING = b'\x04'
	INTEGER = b'\x05'
	FLOAT = b'\x06'
	VECTOR2D = b'\x09'
	VECTOR2DPAIR = b'\x0A'
	VECTOR2DTRIPLET = b'\x0B'


_HEADER = b'\x01\x02\x03\x04'
_VERSION_HEADER = b'\x01\x00\x00\x00'
_FILE_INDEX_END = b'\xFF\xFF\xFF\xFF'
_STRING_OFFSETS_START = b'\x07'
_STRINGS_START = b'\x08'


def fromGgDict(sourceData: bytes, sourceGame: Game):
	"""
	This class parses the provided data into a GGDict, if it's valid
	:param sourceData: The data to parse into a GGDict
	:param sourceGame: The game that the source data came from. This is needed beacuse some parts of ggdict parsing differ between games
	:return: The parsed structure, usually a dictionary
	"""
	# Verify the header to see if the source data is parsable
	if sourceData[0:4] != _HEADER or sourceData[4:8] != _VERSION_HEADER:
		raise DecodeError(f"Invalid header. Should be '{Utils.getPrintableBytes(_HEADER)} {Utils.getPrintableBytes(_VERSION_HEADER)}, but is {Utils.getPrintableBytes(sourceData[0:8])}")
	sourceDataLength = len(sourceData)
	# Get the start offset of the file index entries
	offsetsListStart = Utils.parseInt(sourceData, 8) + 1
	##print(f"{offsetsListStart=:,} ({hex(offsetsListStart)})")
	if offsetsListStart >= sourceDataLength:
		raise DecodeError(f"String offsets supposedly start at offset {offsetsListStart:,} but there are only {sourceDataLength:,} bytes available")
	elif offsetsListStart < 12:
		raise DecodeError(f"Invalid index start offset of {offsetsListStart:,}, too small")
	# Iterate over the offsets and retrieve the string at each location
	stringList: List[str] = []
	totalStringLength: int = 0
	for currentOffsetsListOffset in range(offsetsListStart, sourceDataLength, 4):
		stringOffset = Utils.parseInt(sourceData, currentOffsetsListOffset)
		if stringOffset <= -1:
			# '-1' signals the end of the offsets list, so we can stop
			break
		stringList.append(Utils.getStringFromBytes(sourceData, stringOffset))
		totalStringLength += len(stringList[-1])
	if len(stringList) == 0:
		raise GGDictError("Provided GGDict does not contain any strings, unable to parse")
	# The section after the offsetsListStart explains how the strings are organised
	sourceDataAsIo = BytesIO(sourceData)
	sourceDataAsIo.seek(12)
	return _readValue(sourceDataAsIo, stringList, sourceGame == Game.RETURN_TO_MONKEY_ISLAND)

def _readValue(sourceData: BytesIO, stringList: List[str], useShortStringIndex: bool):
	valueType = sourceData.read(1)
	if valueType == _ValueType.NULL.value:
		return None
	if valueType == _ValueType.DICT.value:
		return _readDictionary(sourceData, stringList, useShortStringIndex)
	elif valueType == _ValueType.ARRAY.value:
		return _readArray(sourceData, stringList, useShortStringIndex)
	elif valueType == _ValueType.STRING.value:
		return _readString(sourceData, stringList, useShortStringIndex)
	elif valueType == _ValueType.INTEGER.value:
		return _readInteger(sourceData, stringList, useShortStringIndex)
	elif valueType == _ValueType.FLOAT.value:
		return _readFloat(sourceData, stringList, useShortStringIndex)
	elif valueType in (_ValueType.VECTOR2D.value, _ValueType.VECTOR2DPAIR.value, _ValueType.VECTOR2DTRIPLET.value):
		# TODO: Parse these into something more useful than strings
		return _readString(sourceData, stringList, useShortStringIndex)
	else:
		raise GGDictError(f"Encountered unknown value type {valueType} ({hex(valueType[0])}) at offset {sourceData.tell():,} ({hex(sourceData.tell())})")

def _readDictionary(sourceData: BytesIO, stringList: List[str], useShortStringIndex: bool) -> Dict[str, Any]:
	# Dictionary of values
	result = {}
	itemCount = Utils.readInt(sourceData)
	for itemIndex in range(itemCount):
		keyName = _readString(sourceData, stringList, useShortStringIndex)
		value = _readValue(sourceData, stringList, useShortStringIndex)
		if keyName in result:
			print(f"Duplicate key '{keyName}', old value is {result[keyName]}, overwriting with {value}")
		result[keyName] = value
	_verifyBlockIsClosed(sourceData, _ValueType.DICT)
	return result

def _readArray(sourceData: BytesIO, stringList: List[str], useShortStringIndex: bool) -> List[Any]:
	itemCount = Utils.readInt(sourceData)
	result = []
	for itemIndex in range(itemCount):
		result.append(_readValue(sourceData, stringList, useShortStringIndex))
	# An array also ends with the array marker
	_verifyBlockIsClosed(sourceData, _ValueType.ARRAY)
	return result

def _readString(sourceData: BytesIO, stringList: List[str], useShortStringIndex: bool) -> str:
	stringIndex = Utils.readShort(sourceData) if useShortStringIndex else Utils.readInt(sourceData)
	if stringIndex < 0 or stringIndex >= len(stringList):
		raise GGDictError(f"Invalid string index {stringIndex} at offset {sourceData.tell()} ({hex(sourceData.tell())}), string list contains {len(stringList):,} strings. StringList is {stringList}")
	return stringList[stringIndex]

def _readInteger(sourceData: BytesIO, stringList: List[str], useShortStringIndex: bool) -> int:
	return int(_readString(sourceData, stringList, useShortStringIndex), 10)

def _readFloat(sourceData: BytesIO, stringList: List[str], useShortStringIndex: bool) -> float:
	return float(_readString(sourceData, stringList, useShortStringIndex))

def _verifyBlockIsClosed(sourceData, valueTypeToClose: _ValueType):
	closeByte = sourceData.read(1)
	if closeByte != valueTypeToClose.value:
		raise GGDictError(f"ValueType wasn't closed properly. Expected {valueTypeToClose.value} but was {closeByte} (At position {sourceData.tell():,})")

def toGgDict(valueToConvert, targetGame: Game) -> bytes:
	"""
	Convert the provided value into a GGDict structure that Thimbleweed Park, Delores, and Return To Monkey Island can understand
	:param valueToConvert: The value to convert. Should usually be a dictionary
	:param targetGame: The game that the ggdict is for. This is needed beacuse some parts of ggdict parsing differ between games
	:return: The GGDict structure
	"""
	# Create the dict structure itself first. Later we'll add the offsets and the stringlist, but we need this size to be able to calculate offsets
	stringList: List[str] = []
	ggdictOutput = bytearray()
	_writeValue(ggdictOutput, stringList, targetGame == Game.RETURN_TO_MONKEY_ISLAND, valueToConvert)
	# Now we can create the string offsets and strings (The +4 is for the int indicating the offset where the string offsets list starts)
	stringIndexOffset = len(_HEADER) + len(_VERSION_HEADER) + 4 + len(ggdictOutput)
	output = bytearray()
	output.extend(_HEADER)
	output.extend(_VERSION_HEADER)
	output.extend(Utils.toWritableInt(stringIndexOffset))
	output.extend(ggdictOutput)
	# Now we can start writing the string list
	stringListOutput = bytearray()
	stringListOffsets: List[int] = []
	for s in stringList:
		stringListOffsets.append(len(stringListOutput))
		stringListOutput.extend(bytes(s, encoding='utf-8'))
		stringListOutput.extend(b'\x00')  # Strings are 0-terminated
	# The string offsets should be from the start of the ggdict, so add the ints (4 bytes) we're going to write for each string offset, plus the block closing and opening indicators
	baseStringOffset = stringIndexOffset + len(stringList) * 4 + len(_FILE_INDEX_END) + len(_STRING_OFFSETS_START) + len(_STRINGS_START)
	output.extend(_STRING_OFFSETS_START)
	for stringListOffset in stringListOffsets:
		output.extend(Utils.toWritableInt(baseStringOffset + stringListOffset))
	output.extend(_FILE_INDEX_END)
	output.extend(_STRINGS_START)
	output.extend(stringListOutput)
	return bytes(output)

def _writeValue(output: bytearray, stringList: List[str], useShortStringIndex: bool, value: Any):
	if isinstance(value, dict):
		_writeDictionary(output, stringList, useShortStringIndex, value)
	elif isinstance(value, list):
		_writeArray(output, stringList, useShortStringIndex, value)
	elif isinstance(value, str):
		_writeString(output, stringList, useShortStringIndex, value)
	elif isinstance(value, int):
		_writeInteger(output, stringList, useShortStringIndex, value)
	else:
		raise GGDictError(f"Writing value type '{type(value)}' hasn't been implemented yet ({value=})")

def _writeDictionary(output: bytearray, stringList: List[str], useShortStringIndex: bool, d: Dict[str, Any]):
	output.extend(_ValueType.DICT.value)
	output.extend(Utils.toWritableInt(len(d)))
	for key in d:
		_writeString(output, stringList, useShortStringIndex, key, False)
		_writeValue(output, stringList, useShortStringIndex, d[key])
	# Close off the dict
	output.extend(_ValueType.DICT.value)

def _writeArray(output: bytearray, stringList: List[str], useShortStringIndex: bool, l: List[Any]):
	output.extend(_ValueType.ARRAY.value)
	output.extend(Utils.toWritableInt(len(l)))
	for value in l:
		_writeValue(output, stringList, useShortStringIndex, value)
	output.extend(_ValueType.ARRAY.value)

def _writeString(output: bytearray, stringList: List[str], useShortStringIndex: bool, s: str, addValueType: bool = True):
	if addValueType:
		output.extend(_ValueType.STRING.value)
	if s not in stringList:
		stringList.append(s)
		keyIndex = len(stringList) - 1
	else:
		keyIndex = stringList.index(s)
	output.extend(Utils.toWritableShort(keyIndex) if useShortStringIndex else Utils.toWritableInt(keyIndex))

def _writeInteger(output: bytearray, stringList: List[str], useShortStringIndex: bool, i: int):
	output.extend(_ValueType.INTEGER.value)
	_writeString(output, stringList, useShortStringIndex, str(i), False)
