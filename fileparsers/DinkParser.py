"""Parses the RtMI DinkParser file, which contains Dinky files, which are the game's scripts"""
# Based on https://github.com/bgbennyboy/Dinky-Explorer/blob/master/ThimbleweedLibrary/DinkDisassembler.cs. Thanks!

import json
from enum import Enum, IntEnum
from io import BytesIO
from typing import Any, Dict, List, Tuple, Union

import Utils
from CustomExceptions import DinkError

class _DinkBlockType(Enum):
	UNKNOWN = -1
	FUNCTION_START = b'\x9C\x78\x41\x34'
	FUNCTION_END = b'\x1C\xA3\x0D\x47'

	# Ordered like they appear in the Dink file
	MYSTERY_BLOCK_TYPE = b'\x25\xA1\x46\x7F'
	INFO_BLOCK_TYPE = b'\x62\x4B\xF9\x16'
	STRINGS_BLOCK_TYPE = b'\xFA\x1C\x3F\x98'
	VARIABLES_BLOCK_TYPE = b'\x3A\xC3\x4B\xFD'
	INSTRUCTIONS_BLOCK_TYPE = b'\x1D\x4D\xED\x55'
	INSTRUCTION_SEGMENTS_BLOCK_TYPE = b'\x42\x40\xD3\x62'

	@staticmethod
	def bytesToBlockType(b: bytes):
		for blockType in _DinkBlockType:
			if b == blockType.value:
				return blockType
		return _DinkBlockType.UNKNOWN

class _DinkOpCode(IntEnum):
	UNKNOWN = -1
	# Opcodes are extracted from RtMI executable
	OP_NOP = 0
	OP_PUSH_CONST = 1
	OP_PUSH_NULL = 2
	OP_PUSH_LOCAL = 3
	OP_PUSH_UPVAR = 4
	OP_PUSH_GLOBAL = 5
	OP_PUSH_FUNCTION = 6
	OP_PUSH_VAR = 7
	OP_PUSH_GLOBALREF = 8
	OP_PUSH_LOCALREF = 9
	OP_PUSH_UPVARREF = 10
	OP_PUSH_VARREF = 11
	OP_PUSH_INDEXEDREF = 12
	OP_DUP_TOP = 13
	OP_UNOT = 14
	OP_UMINUS = 15
	OP_UONECOMP = 16
	OP_MATH = 17
	OP_LAND = 18
	OP_LOR = 19
	OP_INDEX = 20
	OP_ITERATE = 21
	OP_ITERATEKV = 22
	OP_CALL = 23
	OP_FCALL = 24
	OP_CALLINDEXED = 25
	OP_CALL_NATIVE = 26
	OP_FCALL_NATIVE = 27
	OP_POP = 28
	OP_STORE_LOCAL = 29
	OP_STORE_UPVAR = 30
	OP_STORE_ROOT = 31
	OP_STORE_VAR = 32
	OP_STORE_INDEXED = 33
	OP_SET_LOCAL = 34
	OP_NULL_LOCAL = 35
	OP_MATH_REF = 36
	OP_INC_REF = 37
	OP_DEC_REF = 38
	OP_ADD_LOCAL = 39
	OP_JUMP = 40
	OP_JUMP_TRUE = 41
	OP_JUMP_FALSE = 42
	OP_JUMP_TOPTRUE = 43
	OP_JUMP_TOPFALSE = 44
	OP_TERNARY = 45
	OP_NEW_TABLE = 46
	OP_NEW_ARRAY = 47
	OP_NEW_SLOT = 48
	OP_NEW_THIS_SLOT = 49
	OP_DELETE_SLOT = 50
	OP_RETURN = 51
	OP_CLONE = 52
	OP_BREAKPOINT = 53
	OP_REMOVED = 54
	OP_LAST__ = 55  # Originally '__OP_LAST__'
	OP_LABEL_ = 56  # Originally '_OP_LABEL_'

	@staticmethod
	def intToOpCode(i: int):
		if i in _DinkOpCode.__members__.values():
			return _DinkOpCode(i)
		return _DinkOpCode.UNKNOWN

class _DinkVariableType(Enum):
	VARIABLE_TYPE_INT = 0x102
	VARIABLE_TYPE_FLOAT = 0x103
	VARIABLE_TYPE_STRING = 0x204


class _DinkScript:
	def __init__(self, name: str):
		self.name = name
		self.functions: List[_DinkFunction] = []

class _DinkFunction:
	def __init__(self, parentScript: _DinkScript, uid: str, name: str):
		self.parentScript: _DinkScript = parentScript
		self.uid: str = uid
		self.name: str = name
		self.stringOffsetToString: Union[None, Dict[int, str]] = None
		self.variables: Union[None, List[Union[int, float, str]]] = None
		self.instructions: Union[None, List[_DinkInstruction]] = None
		self.instructionSegments: Union[None, List[_DinkInstructionSegment]] = None

class _DinkInstruction:
	def __init__(self, instructionInteger: int, parentFunction: _DinkFunction):
		self.instructionInteger: int = instructionInteger
		self.parentFunction = parentFunction

		self.opCodeNumber: int = instructionInteger & 63
		self.opCode: _DinkOpCode = _DinkOpCode.intToOpCode(self.opCodeNumber)
		self.parameter1 = instructionInteger >> 7
		self.parameter2 = (instructionInteger >> 15) % 256
		self.parameter3 = instructionInteger >> 23

	def toString(self) -> str:
		if _DinkOpCode.OP_PUSH_CONST <= self.opCode <= _DinkOpCode.OP_PUSH_LOCALREF:
			# Pushing parameter 3 to the relevant stack
			if self.parameter3 >= len(self.parentFunction.variables):
				'''
				print('!!!!!!!!!!!!!!!!!!!!!!!')
				print(f"{self.parentFunction.parentScript.name} - {self.parentFunction.name}: {self.instructionInteger=}")
				print(f"{self.parentFunction.stringOffsetToString=}")
				print(f"{self.parentFunction.variables=}")
				print(f"{self.opCode.name=}: {self.parameter1=}; {self.parameter2=}; {self.parameter3=}")
				print('!!!!!!!!!!!!!!!!!!!!!!!')
				# '''
				print(f"WARNING: Invalid variable index {self.parameter3} for {self.opCode.name}, instruction for function {self.parentFunction.parentScript.name}-{self.parentFunction.name} only has {len(self.parentFunction.variables):,} variables [{self.parameter1=}; {self.parameter2=}; {self.parameter3=}")
				varName = f"[Invalid variable index {self.parameter3}; {len(self.parentFunction.variables):,} variables available"
			else:
				varName = self.parentFunction.variables[self.parameter3]
			return f"{self.opCode.name} {varName}"
		return f"{self.opCode.name}, params: '{self.parameter1}'; '{self.parameter2}'; '{self.parameter3}'"

	def __str__(self):
		return self.toString()

	def __repr__(self):
		return self.toString()

class _DinkInstructionSegment:
	def __init__(self, parentFunction: _DinkFunction, lineNumber: int, startIndex: int, endIndex: int):
		self.parentFunction: parentFunction = parentFunction
		self.lineNumber: int = lineNumber
		self.startIndex: int = startIndex
		self.endIndex: int = endIndex

	def getInstructions(self) -> List[_DinkInstruction]:
		return self.parentFunction.instructions[self.startIndex:self.endIndex]


class DinkParser:
	_MYSTERY_BLOCK_VALUE_SIZE = 0
	_MYSTERY_BLOCK_VALUE_1 = 1
	_MYSTERY_BLOCK_VALUE_2 = 1025

	@staticmethod
	def fromDink(sourceData: bytes) -> str:
		dinkReader = BytesIO(sourceData)
		scripts: Dict[str, _DinkScript] = {}
		# Read through all the functions
		while True:
			blockStart = dinkReader.read(4)
			if not blockStart:
				# Reached the end of the file, stop
				break
			elif blockStart != _DinkBlockType.FUNCTION_START.value:
				raise DinkError(f"Invalid DinkParser file, expected block start at offset {dinkReader.tell() - 4}, but found {blockStart}")
			DinkParser._readFunction(dinkReader, scripts)
		print('--------')
		resultLines: List[str] = ["WARNING: These results are probably inaccurate"]
		for scriptName, dinkScript in scripts.items():
			resultLines.append(scriptName)
			for function in dinkScript.functions:
				resultLines.append(f"\t{function.name} [UID {function.uid}] ({len(function.stringOffsetToString):,} strings, {len(function.variables):,} variables)")
				for instructionSegment in function.instructionSegments:
					resultLines.append(f"\t\tLine {instructionSegment.lineNumber}")
					for instruction in instructionSegment.getInstructions():
						resultLines.append(f"\t\t\t{instruction}")
		return "\n".join(resultLines)

	@staticmethod
	def _checkValue(expectedValue, actualValue, errorMessagePrefix="Unexpected value"):
		if expectedValue != actualValue:
			raise DinkError(f"{errorMessagePrefix}. Expected '{expectedValue}' but got '{actualValue}'")

	@staticmethod
	def _getBlockInfo(dinkReader: BytesIO, expectedBlockType: _DinkBlockType) -> Tuple[int, int]:
		"""Get the next block type, block size, and block end offset"""
		blockType = _DinkBlockType.bytesToBlockType(dinkReader.read(4))
		if blockType != expectedBlockType:
			raise DinkError(f"Expected block type {expectedBlockType} but found {blockType} at offset {dinkReader.tell()}")
		blockSize = Utils.readInt(dinkReader)
		return blockSize, dinkReader.tell() + blockSize

	@staticmethod
	def _readFunction(dinkReader: BytesIO, scripts: Dict[str, _DinkScript]) -> _DinkFunction:
		functionLength = Utils.readInt(dinkReader)
		functionEndOffset = dinkReader.tell() + functionLength

		# Mystery block, probably just a header, always the same
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, _DinkBlockType.MYSTERY_BLOCK_TYPE)
		DinkParser._checkValue(DinkParser._MYSTERY_BLOCK_VALUE_SIZE, blockSize, "Unexpected block size of Mystery block")
		DinkParser._checkValue(DinkParser._MYSTERY_BLOCK_VALUE_1, Utils.readInt(dinkReader), "Unexpected first value of Mystery block")
		DinkParser._checkValue(DinkParser._MYSTERY_BLOCK_VALUE_2, Utils.readShort(dinkReader), "Unexpected second value of Mystery block")

		# Info block, stores script and function names
		dinkFunction: _DinkFunction = DinkParser._parseInfoBlock(dinkReader, scripts)
		# Strings block, defines the strings used in the next blocks
		dinkFunction.stringOffsetToString = DinkParser._parseStringBlock(dinkReader)
		# Variables block
		dinkFunction.variables = DinkParser._parseVariablesBlock(dinkReader, dinkFunction.stringOffsetToString)
		# Instructions block
		dinkFunction.instructions = DinkParser._parseInstructionsBlock(dinkReader, dinkFunction)
		# Instruction segments block
		dinkFunction.instructionSegments = DinkParser._parseInstructionSegmentsBlock(dinkReader, dinkFunction)

		# End of the function
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, _DinkBlockType.FUNCTION_END)
		if blockSize != 0:
			raise DinkError(f"Reached end-of-function block, but it has a size of {blockSize} instead of the expected 0")
		if dinkReader.tell() != functionEndOffset:
			raise DinkError(f"Reached end of function data, but there are {functionEndOffset - dinkReader.tell():,} bytes left")
		return dinkFunction

	@staticmethod
	def _parseInfoBlock(dinkReader: BytesIO, scripts: Dict[str, _DinkScript]) -> _DinkFunction:
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, _DinkBlockType.INFO_BLOCK_TYPE)
		startOffset = dinkReader.tell()
		uid = Utils.readString(dinkReader)
		functionName = Utils.readString(dinkReader)
		scriptName = Utils.readString(dinkReader)
		unknownValue1 = Utils.readInt(dinkReader)
		unknownValue2 = Utils.readInt(dinkReader)

		if dinkReader.tell() < startOffset + blockSize:
			excessData = dinkReader.read(startOffset + blockSize - dinkReader.tell())
			#print(f"Unknown data left in info block: {excessData} [{unknownValue1=}; {unknownValue2=}]")

		if scriptName not in scripts:
			scripts[scriptName] = _DinkScript(scriptName)
		dinkFunction = _DinkFunction(scripts[scriptName], uid, functionName)
		scripts[scriptName].functions.append(dinkFunction)
		return dinkFunction

	@staticmethod
	def _parseStringBlock(dinkReader: BytesIO) -> Dict[int, str]:
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, _DinkBlockType.STRINGS_BLOCK_TYPE)
		stringBlockStartOffset = dinkReader.tell()
		stringOffsetToString: Dict[int, str] = {}
		while dinkReader.tell() < blockEndOffset:
			stringOffset = dinkReader.tell() - stringBlockStartOffset
			stringOffsetToString[stringOffset] = Utils.readString(dinkReader)
		###print(f"String block found of size {blockSize} with {len(stringOffsetToString):,} strings: {stringOffsetToString}")
		return stringOffsetToString

	@staticmethod
	def _parseVariablesBlock(dinkReader: BytesIO, stringOffsetToString: Dict[int, str]) -> List[Union[int, float, str]]:
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, _DinkBlockType.VARIABLES_BLOCK_TYPE)
		variableList: List[Union[int, float, str]] = []
		while dinkReader.tell() < blockEndOffset:
			variableType = Utils.readInt(dinkReader)
			if variableType == _DinkVariableType.VARIABLE_TYPE_INT.value:
				variableValue = Utils.readInt(dinkReader)
			elif variableType == _DinkVariableType.VARIABLE_TYPE_FLOAT.value:
				variableValue = Utils.readFloat(dinkReader)
			elif variableType == _DinkVariableType.VARIABLE_TYPE_STRING.value:
				# The variable value for a string is the offset to where the string starts, so jump there, get the string, then jump back
				variableValue = stringOffsetToString[Utils.readInt(dinkReader)]
			else:
				raise DinkError(f"Unknown variable type {variableType} (hex: {hex(variableType)}) in function at block offset {blockEndOffset - blockSize}, {blockSize=}")
			variableList.append(variableValue)
		###print(f" {len(variableList):,} variables found: {variableList[:10]}...")
		return variableList

	@staticmethod
	def _parseInstructionsBlock(dinkReader: BytesIO, parentFunction: _DinkFunction) -> List[_DinkInstruction]:
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, _DinkBlockType.INSTRUCTIONS_BLOCK_TYPE)
		instructionList = []
		while dinkReader.tell() < blockEndOffset:
			instructionList.append(_DinkInstruction(Utils.readInt(dinkReader), parentFunction))
		##print(f"  {len(instructionList):,} instructions found: {instructionList[:5]}...")
		return instructionList

	@staticmethod
	def _parseInstructionSegmentsBlock(dinkReader: BytesIO, parentFunction: _DinkFunction) -> List[_DinkInstructionSegment]:
		blockSize, blockEndOffset = DinkParser._getBlockInfo(dinkReader, _DinkBlockType.INSTRUCTION_SEGMENTS_BLOCK_TYPE)
		instructionSegments: List[_DinkInstructionSegment] = []
		while dinkReader.tell() < blockEndOffset:
			lineNumber = Utils.readInt(dinkReader)
			startIndex = Utils.readInt(dinkReader)
			endIndex = Utils.readInt(dinkReader)
			instructionSegments.append(_DinkInstructionSegment(parentFunction, lineNumber, startIndex, endIndex))
		###print(f"  {len(instructionSegments):,} instruction segments found: {instructionSegments[:5]}...")
		return instructionSegments
