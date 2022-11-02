import struct
from enum import Enum, IntEnum
from typing import BinaryIO, Type

def _parseFromFormatString(dataToParse: bytes, formatString: str):
	return struct.unpack(formatString, dataToParse)[0]

def parseInt(dataToParse: bytes, startIndex: int = 0) -> int:
	return _parseFromFormatString(dataToParse[startIndex: startIndex + 4], '<i')

def readInt(f: BinaryIO) -> int:
	return parseInt(f.read(4))

def parseFloat(dataToParse: bytes, startIndex: int = 0) -> float:
	return _parseFromFormatString(dataToParse[startIndex: startIndex + 4], '<f')

def readFloat(f: BinaryIO) -> float:
	return parseFloat(f.read(4))

def parseShort(dataToParse: bytes, startIndex: int = 0) -> int:
	return _parseFromFormatString(dataToParse[startIndex: startIndex + 2], '<h')

def readShort(f: BinaryIO) -> int:
	return parseShort(f.read(2))

def readNumericalByte(f: BinaryIO) -> int:
	return _parseFromFormatString(f.read(1), '<b')

def readUnsignedByte(f: BinaryIO) -> int:
	return _parseFromFormatString(f.read(1), '<B')

def readString(f: BinaryIO) -> str:
	"""Reads a \x00-terminated string from the provided file or file-like object"""
	stringBytes = bytearray()
	c: bytes = f.read(1)
	while c != b'\x00':
		stringBytes.extend(c)
		c = f.read(1)
	return stringBytes.decode('utf-8')

def getStringFromBytes(data: bytes, startIndex: int) -> str:
	terminatedIndex = data.find(b'\x00', startIndex)
	stringAsBytes = data[startIndex: terminatedIndex]
	try:
		return stringAsBytes.decode('utf-8')
	except UnicodeDecodeError as e:
		print(f"Unable to convert {getPrintableBytes(stringAsBytes)} ({stringAsBytes}) to a string, {startIndex=}")
		raise e


def toWritableInt(numberToWrite: int) -> bytes:
	return struct.pack('<i', numberToWrite)

def toWritableShort(numberToWrite: int) -> bytes:
	return struct.pack('<h', numberToWrite)

def toStringInt(i: int) -> str:
	"""The file index uses a null-terminated string representation of a number for the offset and size. This method creates such a string from the provided number"""
	return str(i) + '\x00'

def getPrintableBytes(b: bytes) -> str:
	return b.hex(' ', 1)

def getEnumValue(enumToSearch: Type[Enum], valueToSearchFor, defaultValue):
	for enumEntry in enumToSearch:
		if valueToSearchFor == enumEntry.value:
			return enumEntry
	return defaultValue

def getIntEnumValue(intEnum: Type[IntEnum], intToSearchFor: int, defaultValue):
	if intToSearchFor in intEnum.__members__.values():
		return intEnum(intToSearchFor)
	return defaultValue
