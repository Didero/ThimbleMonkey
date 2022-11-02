from typing import Dict, List, Union

import Utils
from enums.Game import Game
from fileparsers.dinkhelpers.DinkOpCode import DinkOpCodeDelores, DinkOpCodeRtmi


class DinkScript:
	def __init__(self, name: str, game: Game):
		self.name = name
		self.functions: List[DinkFunction] = []
		self.game = game
		self.opCodeEnum = None
		if game == Game.DELORES:
			self.opCodeEnum = DinkOpCodeDelores
		elif game == Game.RETURN_TO_MONKEY_ISLAND:
			self.opCodeEnum = DinkOpCodeRtmi
		else:
			raise NotImplementedError(f"Dink parsing for game '{game}' has not been implemented yet")


class DinkFunction:
	def __init__(self, parentScript: DinkScript, uid: str, name: str):
		self.parentScript: DinkScript = parentScript
		self.uid: str = uid
		self.name: str = name
		self.stringOffsetToString: Union[None, Dict[int, str]] = None
		self.variables: Union[None, List[Union[int, float, str]]] = None
		self.instructions: Union[None, List[DinkInstruction]] = None
		self.instructionSegments: Union[None, List[DinkInstructionSegment]] = None


class DinkInstruction:
	def __init__(self, instructionInteger: int, parentFunction: DinkFunction):
		self.instructionInteger: int = instructionInteger
		self.parentFunction = parentFunction

		self.opCodeNumber: int = instructionInteger & 63
		self.opCode: Union[DinkOpCodeDelores, DinkOpCodeRtmi] = Utils.getIntEnumValue(self.parentFunction.parentScript.opCodeEnum, self.opCodeNumber, self.parentFunction.parentScript.opCodeEnum.UNKNOWN)
		self.parameter1 = instructionInteger >> 7
		self.parameter2 = (instructionInteger >> 15) % 256
		self.parameter3 = instructionInteger >> 23

	def toString(self) -> str:
		#if _DinkOpCode.OP_PUSH_CONST <= self.opCode <= _DinkOpCode.OP_PUSH_LOCALREF:
		outputString = self.opCode.name
		opCodeEnum = self.parentFunction.parentScript.opCodeEnum
		if self.opCode in (opCodeEnum.OP_PUSH_CONST, opCodeEnum.OP_PUSH_NULL, opCodeEnum.OP_PUSH_LOCAL, opCodeEnum.OP_PUSH_UPVAR, opCodeEnum.OP_PUSH_GLOBAL,
						   opCodeEnum.OP_PUSH_FUNCTION, opCodeEnum.OP_PUSH_VAR, opCodeEnum.OP_PUSH_GLOBALREF, opCodeEnum.OP_PUSH_LOCALREF):
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
				print(f"WARNING: Invalid variable index {self.parameter3} for {self.opCode.name}, "
					  f"instruction for function {self.parentFunction.parentScript.name}-{self.parentFunction.name} only has "
					  f"{len(self.parentFunction.variables):,} variables (and {len(self.parentFunction.stringOffsetToString):,} strings) "
					  f"[{self.parameter1=}; {self.parameter2=}; {self.parameter3=}]")
				outputString += f" [Invalid variable index {self.parameter3}; {len(self.parentFunction.variables):,} variables available"
			else:
				outputString += f" {self.parentFunction.variables[self.parameter3]}"
		outputString += f" [{self.parameter1=}; {self.parameter2=}; {self.parameter3=}]"
		return outputString

	def __str__(self):
		return self.toString()

	def __repr__(self):
		return self.toString()


class DinkInstructionSegment:
	def __init__(self, parentFunction: DinkFunction, lineNumber: int, startIndex: int, endIndex: int):
		self.parentFunction: parentFunction = parentFunction
		self.lineNumber: int = lineNumber
		self.startIndex: int = startIndex
		self.endIndex: int = endIndex

	def getInstructions(self) -> List[DinkInstruction]:
		return self.parentFunction.instructions[self.startIndex:self.endIndex]
