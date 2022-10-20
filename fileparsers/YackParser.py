# .yack files contain the dialogues and conversations, including the dialog options

import os
from enum import IntEnum
from io import BytesIO
from typing import List

import Keys, Utils
from CustomExceptions import YackError


class _YackOpCodes(IntEnum):
	UNKNOWN = -100
	END_PROGRAM = 0
	ACTOR_SAY = 1  # Can have an extra first argument, which is a variable check. The provided line will only be said if that condition is true
	ASSIGN = 2
	# TODO: Yack op code 3 (0x3) at line number 95 of file Carla.yack
	PAUSE = 5
	WAIT_FOR = 7
	EMIT_CODE = 8
	LABEL = 9
	GOTO_LABEL = 10  # GOTO_LABEL can also have an extra parameter, in which case it probably acts like GOTO_IF (See line 71 of Carla.yack, or lines 43-46 of BarPirates.yack, for instance)
	END_CHOICES = 11
	BEGIN_CHOICES = 12
	# TODO: Encountered unknown Yack op code 17 (0x11) at line number 20 of file HintSystemAct1.yack
	GOTO_IF = 19
	DIALOG_CHOICE_1 = 100
	DIALOG_CHOICE_2 = 101
	DIALOG_CHOICE_3 = 102
	DIALOG_CHOICE_4 = 103
	DIALOG_CHOICE_5 = 104
	DIALOG_CHOICE_6 = 105
	DIALOG_CHOICE_7 = 106
	DIALOG_CHOICE_8 = 107
	DIALOG_CHOICE_9 = 108

	@staticmethod
	def intToOpCode(i: int):
		if i in _YackOpCodes.__members__.values():
			return _YackOpCodes(i)
		return _YackOpCodes.UNKNOWN


_HEADER = b'\x00\x78\xE6\xDC'
_UNKNOWN_NUMBER = 1120122089

def _decodeYack(encodedYackBytes: bytes, yackFilename: str) -> bytes:
	"""
	Decodes the provided yack file data into something parsable by 'Yack.fromYack()'
	:param encodedYackBytes: The encoded bytes of the Yack file
	:param yackFilename: The filename of the Yack file. This is needed to determine the decoding key
	:return: The decoded yack file, ready to be parsed
	"""
	# Based on https://github.com/jonsth131/ggtool/blob/main/libdinky/src/decoder.rs
	decodedYackBytes = bytearray(len(encodedYackBytes))
	val = len(os.path.basename(yackFilename)) - 5  # Subtract the '.yack' file extension
	keyLength = len(Keys.KEY_YACK)
	for index in range(len(encodedYackBytes)):
		keyIndex = (index + val) % keyLength
		decodedYackBytes[index] = encodedYackBytes[index] ^ Keys.KEY_YACK[keyIndex]
	return bytes(decodedYackBytes)

def fromYack(encodedYackBytes: bytes, yackFilename: str) -> List[str]:
	# Based very much on https://github.com/bgbennyboy/Thimbleweed-Park-Explorer/blob/master/ThimbleweedLibrary/YackDecompiler.cs
	yackReader = BytesIO(_decodeYack(encodedYackBytes, yackFilename))
	header = yackReader.read(4)
	if header != _HEADER:
		raise YackError(f"Invalid header. Expected '{Utils.getPrintableBytes(_HEADER)}' but found '{Utils.getPrintableBytes(header)}'")
	# Read in the string list
	stringListOffset = Utils.readInt(yackReader)
	yackReader.seek(stringListOffset)
	unknownNumber = Utils.readInt(yackReader)
	##print(f"{unknownNumber=} ({hex(unknownNumber)})")
	if unknownNumber != _UNKNOWN_NUMBER:
		raise YackError(f"Unexpected unknown number, should be {_UNKNOWN_NUMBER} but was {unknownNumber}")
	stringListSize = Utils.readInt(yackReader)
	strings: List[str] = []
	for i in range(stringListSize):
		strings.append(Utils.readString(yackReader))

	# Now read in the Yack statements
	yackReader.seek(8)
	yackLines: List[str] = []
	while True:
		opCodeNumber = Utils.readNumericalByte(yackReader)
		opCode = _YackOpCodes.intToOpCode(opCodeNumber)
		if opCodeNumber == _YackOpCodes.END_PROGRAM:
			break
		lineNumber = Utils.readInt(yackReader)
		if opCode == _YackOpCodes.UNKNOWN:
			print(f"Encountered unknown Yack op code {opCodeNumber} ({hex(opCodeNumber)}) at line number {lineNumber:,} of file {yackFilename}")
		unknownValue = Utils.readInt(yackReader)
		if unknownValue != 0:
			print(f"Expected unknown value 0, but found {unknownValue}")
		parameterCount = Utils.readNumericalByte(yackReader) + 2
		parameters: List[int] = []
		parametersAsStrings: List[str] = []
		for i in range(parameterCount):
			parameter = Utils.readInt(yackReader)
			parameters.append(parameter)
			if 0 <= parameter < stringListSize:
				parametersAsStrings.append(strings[parameter])
			else:
				parametersAsStrings.append(str(parameter))
		#print(f"{lineNumber}: [{opCodeNumber=} {opCode.name}] {parametersAsStrings}")
		#print(f"{lineNumber}: [{opCodeNumber=} {opCode.name}] {parametersAsStrings}")
		joinedParameters = '; '.join(parametersAsStrings)
		yackLines.append(f"line {lineNumber}: {opCode.name} {joinedParameters}")
	return yackLines
