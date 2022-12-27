"""Parses the RtMI DinkParser file, which contains Dinky files, which are the game's scripts"""
# Based on https://github.com/bgbennyboy/Dinky-Explorer/blob/master/ThimbleweedLibrary/DinkDisassembler.cs. Thanks!

from collections import OrderedDict
from io import BytesIO
from typing import Dict, List, Tuple, Union

import Utils
from CustomExceptions import DinkError
from enums.Game import Game
from fileparsers.dinkhelpers.DinkType import DinkBlockType, DinkVariableType
from fileparsers.dinkhelpers.DinkScript import DinkScript, DinkFunction, DinkInstructionOperation, DinkInstructionLine


class DinkParser:
	_MYSTERY_BLOCK_VALUE_SIZE = 0
	_MYSTERY_BLOCK_VALUE_1 = 1
	_MYSTERY_BLOCK_VALUE_2 = 1025

	@staticmethod
	def fromDink(sourceData: bytes, game: Game) -> str:
		"""
		Converts the provided Dink filedata into human-readable text
		:param sourceData: The sourcedata to parse into Dink text
		:param game: Which game the sourcedata is from. This is needed because parsing between games is slightly different
		:return: The multiline text that can be shown to a user
		"""
		scripts = DinkParser.fromDinkToScripts(sourceData, game)
		return DinkParser.fromDinkScriptDictToStrings(scripts)

	@staticmethod
	def fromDinkToScripts(sourceData: bytes, game: Game) -> Dict[str, DinkScript]:
		"""
		Converts the provided Dink filedata into parsed DinkScripts
		:param sourceData: The soucedata, probably read from a file or through a FileEntry
		:param game: Which game the sourcedata is from. This is needed because parsing between games is slightly different
		:return: A dictionary with the keys being script names and the values being the parsed script objects
		"""
		dinkReader = BytesIO(sourceData)
		scripts: OrderedDict[str, DinkScript] = OrderedDict()
		# Read through all the functions
		while True:
			blockStart = dinkReader.read(4)
			if not blockStart:
				# Reached the end of the file, stop
				break
			elif blockStart != DinkBlockType.FUNCTION_START.value:
				raise DinkError(f"Invalid DinkParser file, expected block start at offset {dinkReader.tell() - 4}, but found {blockStart}")
			DinkParser._readFunction(dinkReader, scripts, game)
		return scripts

	@staticmethod
	def fromDinkScriptDictToStrings(scripts: Dict[str, DinkScript]) -> str:
		"""
		Turns the provided DinkScripts into human-readable text
		:param scripts: The script names and objects to turn into human-readable text
		:return: The multiline text that can be shown to a user
		"""
		resultLines: List[str] = ["WARNING: These results are probably inaccurate"]
		for scriptName, script in scripts.items():
			resultLines.append(str(script))
		return "\n".join(resultLines)

	@staticmethod
	def _checkValue(expectedValue, actualValue, errorMessagePrefix="Unexpected value"):
		if expectedValue != actualValue:
			raise DinkError(f"{errorMessagePrefix}. Expected '{expectedValue}' but got '{actualValue}'")

	@staticmethod
	def _getBlockInfo(dinkReader: BytesIO, expectedBlockType: DinkBlockType) -> Tuple[int, int]:
		"""Get the next block type, block size, and block end offset"""
		blockType = Utils.getEnumValue(DinkBlockType, dinkReader.read(4), DinkBlockType.UNKNOWN)
		if blockType != expectedBlockType:
			raise DinkError(f"Expected block type {expectedBlockType} but found {blockType} at offset {dinkReader.tell()}")
		blockSize = Utils.readInt(dinkReader)
		return blockSize, dinkReader.tell() + blockSize

	@staticmethod
	def _readFunction(dinkReader: BytesIO, scripts: Dict[str, DinkScript], game: Game) -> DinkFunction:
		functionLength = Utils.readInt(dinkReader)
		functionEndOffset = dinkReader.tell() + functionLength

		# Mystery block, probably just a header, always the same
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, DinkBlockType.MYSTERY_BLOCK_TYPE)
		DinkParser._checkValue(DinkParser._MYSTERY_BLOCK_VALUE_SIZE, blockSize, "Unexpected block size of Mystery block")
		DinkParser._checkValue(DinkParser._MYSTERY_BLOCK_VALUE_1, Utils.readInt(dinkReader), "Unexpected first value of Mystery block")
		DinkParser._checkValue(DinkParser._MYSTERY_BLOCK_VALUE_2, Utils.readShort(dinkReader), "Unexpected second value of Mystery block")

		# Info block, stores script and function names
		dinkFunction: DinkFunction = DinkParser._parseInfoBlock(dinkReader, scripts, game)
		# Strings block, defines the strings used in the next blocks
		dinkFunction.stringOffsetToString = DinkParser._parseStringBlock(dinkReader)
		# Variables block
		dinkFunction.variables = DinkParser._parseVariablesBlock(dinkReader, dinkFunction.stringOffsetToString)
		# Instructions block
		dinkFunction.instructionOperations = DinkParser._parseInstructionsBlock(dinkReader, dinkFunction)
		# Instruction segments block
		dinkFunction.instructionLines = DinkParser._parseInstructionSegmentsBlock(dinkReader, dinkFunction)

		# End of the function
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, DinkBlockType.FUNCTION_END)
		if blockSize != 0:
			raise DinkError(f"Reached end-of-function block, but it has a size of {blockSize} instead of the expected 0")
		if dinkReader.tell() != functionEndOffset:
			raise DinkError(f"Reached end of function data, but there are {functionEndOffset - dinkReader.tell():,} bytes left")
		return dinkFunction

	@staticmethod
	def _parseInfoBlock(dinkReader: BytesIO, scripts: Dict[str, DinkScript], game: Game) -> DinkFunction:
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, DinkBlockType.INFO_BLOCK_TYPE)
		startOffset = dinkReader.tell()
		uid = Utils.readString(dinkReader)
		functionName = Utils.readString(dinkReader)
		scriptName = Utils.readString(dinkReader)
		unknownByte1 = Utils.readNumericalByte(dinkReader)
		unknownByte2 = Utils.readNumericalByte(dinkReader)
		numberOfExtraValues = Utils.readNumericalByte(dinkReader)
		unknownByte3 = Utils.readNumericalByte(dinkReader)
		possibleConstantsCount = Utils.readInt(dinkReader)  # TODO: Possibly number of constants in RtMI. Big negative number in Delores though

		if dinkReader.tell() < startOffset + blockSize:
			excessData = dinkReader.read(startOffset + blockSize - dinkReader.tell())

		if scriptName not in scripts:
			scripts[scriptName] = DinkScript(scriptName, game)
		dinkFunction = DinkFunction(scripts[scriptName], uid, functionName)
		return dinkFunction

	@staticmethod
	def _parseStringBlock(dinkReader: BytesIO) -> Dict[int, str]:
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, DinkBlockType.STRINGS_BLOCK_TYPE)
		stringBlockStartOffset = dinkReader.tell()
		stringOffsetToString: Dict[int, str] = {}
		while dinkReader.tell() < blockEndOffset:
			stringOffset = dinkReader.tell() - stringBlockStartOffset
			stringOffsetToString[stringOffset] = Utils.readString(dinkReader)
		return stringOffsetToString

	@staticmethod
	def _parseVariablesBlock(dinkReader: BytesIO, stringOffsetToString: Dict[int, str]) -> List[Union[int, float, str]]:
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, DinkBlockType.VARIABLES_BLOCK_TYPE)
		variableList: List[Union[int, float, str]] = []
		while dinkReader.tell() < blockEndOffset:
			variableType = Utils.readInt(dinkReader)
			if variableType == DinkVariableType.VARIABLE_TYPE_INT.value:
				variableValue = Utils.readInt(dinkReader)
			elif variableType == DinkVariableType.VARIABLE_TYPE_FLOAT.value:
				variableValue = Utils.readFloat(dinkReader)
			elif variableType == DinkVariableType.VARIABLE_TYPE_STRING.value:
				# The variable value for a string is the offset to where the string starts, so jump there, get the string, then jump back
				variableValue = stringOffsetToString[Utils.readInt(dinkReader)]
			else:
				raise DinkError(f"Unknown variable type {variableType} (hex: {hex(variableType)}) in function at block offset {blockEndOffset - blockSize}, {blockSize=}")
			variableList.append(variableValue)
		return variableList

	@staticmethod
	def _parseInstructionsBlock(dinkReader: BytesIO, parentFunction: DinkFunction) -> List[DinkInstructionOperation]:
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, DinkBlockType.INSTRUCTIONS_BLOCK_TYPE)
		instructionList = []
		while dinkReader.tell() < blockEndOffset:
			instructionList.append(DinkInstructionOperation(Utils.readInt(dinkReader), parentFunction))
		return instructionList

	@staticmethod
	def _parseInstructionSegmentsBlock(dinkReader: BytesIO, parentFunction: DinkFunction) -> List[DinkInstructionLine]:
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, DinkBlockType.INSTRUCTION_SEGMENTS_BLOCK_TYPE)
		instructionSegments: List[DinkInstructionLine] = []
		while dinkReader.tell() < blockEndOffset:
			lineNumber = Utils.readInt(dinkReader)
			startIndex = Utils.readInt(dinkReader)
			endIndex = Utils.readInt(dinkReader)
			instructionSegments.append(DinkInstructionLine(parentFunction, lineNumber, startIndex, endIndex))
		return instructionSegments
