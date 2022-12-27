from typing import Dict, List, Union

import Utils
from enums.Game import Game
from fileparsers.dinkhelpers.DinkOpCode import DinkOpCodeDelores, DinkOpCodeRtmi
from fileparsers.dinkhelpers.DinkFunctionDecompiler import DinkFunctionDecompiler


class DinkScript:
	def __init__(self, name: str, game: Game):
		self.name = name
		self.functionsByUid: Dict[str, DinkFunction] = {}
		self.rootFunction: Union[None, DinkFunction] = None
		self.game = game
		self.opCodeEnum: Union[DinkOpCodeDelores, DinkOpCodeRtmi]
		if game == Game.DELORES:
			self.opCodeEnum = DinkOpCodeDelores
		elif game == Game.RETURN_TO_MONKEY_ISLAND:
			self.opCodeEnum = DinkOpCodeRtmi
		else:
			raise NotImplementedError(f"Dink parsing for game '{game}' has not been implemented yet")

	def __str__(self):
		result: List[str] = [self.name]
		for uid, dinkFunction in self.functionsByUid.items():
			result.append(str(dinkFunction))
			result.append('------------------')
		return "\n".join(result)


class DinkFunction:
	def __init__(self, parentScript: DinkScript, uid: str, name: str):
		self.parentScript: DinkScript = parentScript
		self.parentScript.functionsByUid[uid] = self
		if name == '$root$':
			self.parentScript.rootFunction = self
		self.uid: str = uid
		self.name: str = name
		self.stringOffsetToString: Union[None, Dict[int, str]] = None
		self.variables: Union[None, List[Union[int, float, str]]] = None
		self.instructionOperations: Union[None, List[DinkInstructionOperation]] = None
		self.instructionLines: Union[None, List[DinkInstructionLine]] = None

	def getVariable(self, variableIndex: int) -> Union[int, float, str]:
		if variableIndex >= len(self.variables):
			print(f"WARNING: Asked for variable index {variableIndex} but there are only {len(self.variables)} variables (and {len(self.stringOffsetToString)} strings)")
			return '[[invalid variable index]]'
		return self.variables[variableIndex]

	def __str__(self):
		result: List[str] = [f"\t{self.parentScript.name} {self.name} [UID {self.uid}] ({len(self.stringOffsetToString):,} strings, {len(self.variables):,} variables)",
							 f"\t\tStrings: {list(self.stringOffsetToString.values())}"]
		varsToPrint = "; ".join([f"{index}: {var} ({type(var).__name__})" for index, var in enumerate(self.variables)])
		result.append(f"\t\tVariables: {varsToPrint}")
		for instructionLine in self.instructionLines:
			result.append(f"\t\tLine {instructionLine.lineNumber}")
			for instruction in instructionLine.getInstructionOperations():
				result.append(f"\t\t\t{instruction}")
		result.append(str(DinkFunctionDecompiler(self)))
		return "\n".join(result)


class DinkInstructionLine:
	"""A Dink instruction line consists of several instruction operations"""
	def __init__(self, parentFunction: DinkFunction, lineNumber: int, startIndex: int, endIndex: int):
		self.parentFunction: parentFunction = parentFunction
		self.lineNumber: int = lineNumber
		self.startIndex: int = startIndex
		self.endIndex: int = endIndex

	def getInstructionOperations(self) -> List["DinkInstructionOperation"]:
		return self.parentFunction.instructionOperations[self.startIndex:self.endIndex]

	@property
	def instructionCount(self) -> int:
		return self.endIndex - self.startIndex


class DinkInstructionOperation:
	def __init__(self, instructionInteger: int, parentFunction: DinkFunction):
		self.instructionInteger: int = instructionInteger
		self.parentFunction = parentFunction

		self.opCodeNumber: int = instructionInteger & 63
		self.opCode: Union[DinkOpCodeDelores, DinkOpCodeRtmi] = Utils.getIntEnumValue(self.parentFunction.parentScript.opCodeEnum, self.opCodeNumber, self.parentFunction.parentScript.opCodeEnum.UNKNOWN)
		self.parameter1 = instructionInteger >> 7
		self.parameter2 = (instructionInteger >> 16) % 256
		self.parameter3 = instructionInteger >> 23

	def toString(self) -> str:
		outputParts: List[str] = [self.opCode.name]
		opCodeEnum = self.parentFunction.parentScript.opCodeEnum
		# Some operations reference a variable wit their third parameter, add that
		if self.opCode in (opCodeEnum.OP_PUSH_CONST, opCodeEnum.OP_PUSH_LOCAL, opCodeEnum.OP_PUSH_UPVAR, opCodeEnum.OP_PUSH_GLOBAL, opCodeEnum.OP_PUSH_FUNCTION,
						   opCodeEnum.OP_PUSH_VAR, opCodeEnum.OP_PUSH_GLOBALREF, opCodeEnum.OP_PUSH_LOCALREF, opCodeEnum.OP_STORE_VAR, opCodeEnum.OP_STORE_UPVAR, opCodeEnum.OP_STORE_ROOT,
						   opCodeEnum.OP_NEW_SLOT, opCodeEnum.OP_NEW_THIS_SLOT, opCodeEnum.OP_INDEX, opCodeEnum.OP_NEW_ARRAY):
			# Pushing parameter 3 to the relevant stack
			if self.parameter3 >= len(self.parentFunction.variables):
				print(f"WARNING:DinkInstructionOperation: Invalid variable index {self.parameter3} for {self.opCode.name}, "
					  f"instruction for function {self.parentFunction.parentScript.name}-{self.parentFunction.name} only has "
					  f"{len(self.parentFunction.variables):,} variables (and {len(self.parentFunction.stringOffsetToString):,} strings) "
					  f"[{self.parameter1=}; {self.parameter2=}; {self.parameter3=}]")
				outputParts.append(f"[Invalid variable index {self.parameter3}; {len(self.parentFunction.variables):,} variables available")
			else:
				outputParts.append(f"{self.parentFunction.variables[self.parameter3]}")
		elif self.opCode in (opCodeEnum.OP_JUMP, opCodeEnum.OP_JUMP_FALSE, opCodeEnum.OP_JUMP_TRUE, opCodeEnum.OP_JUMP_TOPFALSE, opCodeEnum.OP_JUMP_TOPTRUE):
			jumpDistance = self.parameter1 & 0x3FFF
			outputParts.append(f"Jump {jumpDistance}")
			if self.opCode != opCodeEnum.OP_JUMP:
				outputParts.append(f"if {True if self.opCode in (opCodeEnum.OP_JUMP_TRUE, opCodeEnum.OP_JUMP_TOPTRUE) else False}")
		outputParts.append(f"[{self.instructionInteger=}; {self.parameter1=}; {self.parameter2=}; {self.parameter3=}]")
		return " ".join(outputParts)

	def __str__(self):
		return self.toString()

	def __repr__(self):
		return self.toString()
