import typing
from typing import List, Union

from enums.Game import Game
from fileparsers.dinkhelpers.DinkOpCode import DinkOpCodeDelores, DinkOpCodeRtmi

if typing.TYPE_CHECKING:
	from fileparsers.dinkhelpers.DinkScript import DinkFunction, DinkInstructionLine, DinkInstructionOperation


class DinkFunctionDecompiler:
	_INDENT_LEVELS: List[str] = ["    " * i for i in range(15)]
	_COMPARISION_OPCODE_TO_STRING = {DinkOpCodeDelores.OP_EQEQ: '==', DinkOpCodeDelores.OP_NEQ: '!=', DinkOpCodeDelores.OP_LT: '<', DinkOpCodeDelores.OP_LEQ: '<=', DinkOpCodeDelores.OP_GEQ: '>=', DinkOpCodeDelores.OP_GT: '>',
									 DinkOpCodeDelores.OP_IN: 'IN'}

	def __init__(self, dinkFunction: "DinkFunction"):
		self._dinkFunction: DinkFunction = dinkFunction
		self._resultList: List[str] = [f"function {dinkFunction.parentScript.name}.{dinkFunction.name} [uid {dinkFunction.uid}] {{"]
		self._indentLevel: int = 1

		opCodeEnum: Union[DinkOpCodeDelores, DinkOpCodeRtmi] = self._dinkFunction.parentScript.opCodeEnum
		arguments: List[str] = []
		# If the indent level was increased this line, the instruction line number refers to the line where the indent should be decreased again
		# Keep track of those line numbers for formatting, but skip checking that line number if it got added this operation otherwise the added line number immediately gets removed again
		self._reduceIndentAtLineNumbers: List[int] = []
		self._indentLevelWasAdded: bool = False
		# Tables (dicts in Python) can be nested, so we need to keep track of when one starts, so we can only take the innermost arguments to make the table
		tableStartArgumentIndexes: List[int] = []
		try:
			for instructionLine in self._dinkFunction.instructionLines:
				operationIndexesToReduceIndentAt: List[int] = []
				self._indentLevelWasAdded = False  # Not all lines have operations, make sure it gets set properly then too
				for operationIndex, operation in enumerate(instructionLine.getInstructionOperations()):
					opCode = operation.opCode
					self._indentLevelWasAdded = False
					# TODO Opcodes to implement: 'OP_NOP', 'OP_PUSH_UPVAR', 'OP_PUSH_GLOBAL', 'OP_PUSH_UPVARREF', 'OP_PUSH_INDEXEDREF',
					#  'OP_DUP_TOP', 'OP_UNOT', 'OP_UMINUS', 'OP_UONECOMP', 'OP_LAND', 'OP_LOR', 'OP_ITERATE', 'OP_ITERATEKV', 'OP_CALLINDEXED', 'OP_CALL_NATIVE', 'OP_FCALL_NATIVE',
					#  'OP_POP', 'OP_STORE_VAR', 'OP_SET_LOCAL', 'OP_MATH_REF', 'OP_INC_REF', 'OP_DEC_REF', 'OP_ADD_LOCAL',
					#  'OP_TERNARY', 'OP_DELETE_SLOT', 'OP_CLONE', 'OP_REMOVED', 'OP_LAST__', 'OP_LABEL_'

					##### Pushing variables onto the stack  #####
					if opCode in (opCodeEnum.OP_PUSH_VAR, opCodeEnum.OP_PUSH_CONST, opCodeEnum.OP_PUSH_LOCAL, opCodeEnum.OP_PUSH_FUNCTION, opCodeEnum.OP_PUSH_GLOBAL, opCodeEnum.OP_PUSH_UPVAR,
								  opCodeEnum.OP_PUSH_VARREF, opCodeEnum.OP_PUSH_LOCALREF, opCodeEnum.OP_PUSH_GLOBALREF):
						# TODO Differentiate more between push types
						# TODO PUSH_LOCAL seems to refer to a function parameter when operation.parameter2 is 128, and to a variable index when operation.parameter2 is 0
						argument = self._dinkFunction.getVariable(operation.parameter3)
						if opCode == opCodeEnum.OP_PUSH_CONST and isinstance(argument, str):
							argument = '"' + argument + '"'
						elif opCode == opCodeEnum.OP_PUSH_FUNCTION:
							argument = f"function {argument}"
						else:
							argument = str(argument)  # Having arguments as strings is useful because it makse string appending easier
						arguments.append(argument)
					elif opCode == opCodeEnum.OP_PUSH_NULL:
						arguments.append('null')
					elif opCode == opCodeEnum.OP_INDEX:
						argument = self._dinkFunction.getVariable(operation.parameter3)
						if len(arguments) == 0:
							DinkFunctionDecompiler._printWarning("Missing argument, need at least one", operation)
						else:
							if arguments[-1] == argument:
								# TODO if the two variable names are identical, assume it means a class variable ('this.argument'), verify this. Maybe compare operation.parameter2 too
								arguments[-1] = f"[this].{argument}"
							else:
								arguments[-1] += f".{argument}"
					elif opCode == opCodeEnum.OP_NEW_ARRAY:
						# parameter3 points to a variable, which should be a number indicating the array size
						arraySize = self._dinkFunction.getVariable(operation.parameter3)
						if not isinstance(arraySize, int):
							DinkFunctionDecompiler._printWarning(f"Expected parameter3 to point to an int variable, but it was '{arraySize}' ({type(arraySize)})", operation)
						elif len(arguments) < arraySize:
							DinkFunctionDecompiler._printWarning(f"ArraySize parameter3 wants {arraySize} arguments, but only {len(arguments)} were provided", operation)
						else:
							argumentString = "[ " + ", ".join(DinkFunctionDecompiler._popLastArguments(arguments, arraySize, operation)) + " ]"
							arguments.append(argumentString)
					elif opCode == opCodeEnum.OP_NEW_TABLE:
						# A table is like a Python dictionary, a set of key-values. Parameter3=0 starts a new table, parameter3=1 ends it
						# Values are added to the table with 'NEW_SLOT'
						if operation.parameter3 == 0:
							tableStartArgumentIndexes.append(len(arguments))
						elif operation.parameter3 == 1:
							startArgumentIndex = tableStartArgumentIndexes.pop()
							tableArguments = arguments[startArgumentIndex:]
							arguments = arguments[:startArgumentIndex]
							arguments.append("{ " + ", ".join(tableArguments) + " }")
						else:
							DinkFunctionDecompiler._printWarning("Unexpected parameter3, should be 0 to start a new table or 1 to close that table", operation)
					elif opCode == opCodeEnum.OP_NEW_SLOT:
						slotName = self._dinkFunction.getVariable(operation.parameter3)
						if len(arguments) == 0:
							DinkFunctionDecompiler._printWarning("Need an argument, but there are none stored", operation)
							arguments.append(f"{slotName} = [[missing]]")
						else:
							arguments[-1] = f"{slotName} = {arguments[-1]}"

					##### Calling functions ######
					elif opCode in (opCodeEnum.OP_CALL, opCodeEnum.OP_FCALL):
						if len(arguments) == 0:
							DinkFunctionDecompiler._printWarning(f"function call with no function name on the stack", operation)
							callName = "[[callNameMissing]]"
						else:
							callName = arguments.pop()
						if len(arguments) != operation.parameter3:
							####DinkFunctionDecompiler._printWarning(f"Function call expected {operation.parameter3} arguments but got {len(arguments)}", operation)
							if operation.parameter3 > len(arguments):
								# Too few arguments, fill up the remainder with temporary values
								for i in range(operation.parameter3 - len(arguments)):
									arguments.append("[[missing]]")
						if operation.parameter3 == 0:
							argumentString = ""
						elif opCode == opCodeEnum.OP_FCALL:
							# FCALL should only take 'parameter3' amount of arguments from the end of the argument list, because an FCALL can be inside a CALL block
							# For instance 'myMethod("string", otherMethod(nestedValue)) would be stored as: "string", nestedValue, othermethod, FCALL with parameter3=1, mymethod, CALL with parameter3=2
							# Example: Boot.dinky, function main, the fontAddImage calls
							argumentString = ", ".join(DinkFunctionDecompiler._popLastArguments(arguments, operation.parameter3, operation))
						else:
							argumentString = ", ".join(arguments)
						callString = f"{callName}({argumentString})"
						if opCode == opCodeEnum.OP_FCALL:
							# OP_FCALL stores its result as an argument for further calls
							arguments.append(callString)
						else:
							# OP_CALL immediately executes the result, finishing the line
							self._addToResult(callString)
							arguments.clear()

					##### Storing values #####
					elif opCode in (opCodeEnum.OP_STORE_ROOT, opCodeEnum.OP_STORE_UPVAR, opCodeEnum.OP_STORE_LOCAL):
						# TODO Differentiate between store types
						varname = self._dinkFunction.getVariable(operation.parameter3)
						if len(arguments) == 0:
							DinkFunctionDecompiler._printWarning(f"No arguments provided", operation)
							varvalue = '[[unset]]'
						else:
							varvalue = arguments.pop()
						if len(arguments) > 1:
							DinkFunctionDecompiler._printWarning(f"Unexpected number of arguments, need 1 but got {len(arguments)}", operation)
						self._addToResult(f"{varname} = {varvalue}")
					elif opCode == opCodeEnum.OP_STORE_INDEXED:
						if len(arguments) != 3:
							DinkFunctionDecompiler._printWarning(f"Expected 3 arguments, but found {len(arguments)}", operation)
						value, indexableVar, index = DinkFunctionDecompiler._popLastArguments(arguments, 3, operation)
						self._addToResult(f"{indexableVar}[{index}] <- {value}")
					elif opCode == opCodeEnum.OP_NEW_THIS_SLOT:
						if len(arguments) != 2:
							DinkFunctionDecompiler._printWarning(f"Need 2 arguments, but found {len(arguments)}", operation)
						varName, slotName = DinkFunctionDecompiler._popLastArguments(arguments, 2, operation)
						slotName = slotName.strip('"')  # TODO Check if this is always true, it works for Delores Boot.dinky setFont
						self._addToResult(f"{slotName} <- {varName}")
					elif opCode == opCodeEnum.OP_INC_REF:
						if len(arguments) != 1:
							DinkFunctionDecompiler._printWarning(f"Need a single argument, but found {len(arguments)} arguments", operation)
						varToIncrease = DinkFunctionDecompiler._popLastArguments(arguments, 1, operation)[0]
						self._addToResult(f"{varToIncrease}++")

					##### Jumping, if/else, logic #####
					elif opCode in (opCodeEnum.OP_JUMP_TRUE, opCodeEnum.OP_JUMP_FALSE, opCodeEnum.OP_JUMP_TOPTRUE, opCodeEnum.OP_JUMP_TOPFALSE):
						if len(arguments) == 0:
							DinkFunctionDecompiler._printWarning("Jump without any arguments", operation)
						else:
							jumpDistance = operation.parameter1 & 0x3FFF
							negationString = '! ' if opCode in (opCodeEnum.OP_JUMP_TRUE, opCodeEnum.OP_JUMP_TOPTRUE) else ''
							if opCode in (opCodeEnum.OP_JUMP_TOPTRUE, opCodeEnum.OP_JUMP_TOPFALSE):
								# The 'TOP' jumps are inline combined checks, used for OR's
								arguments.append(' || ' if opCode == opCodeEnum.OP_JUMP_TOPTRUE else ' && ')
							else:
								argumentString = " ".join(arguments)
								# If a JUMP is the last or only entry in the operation, the line number and jump distance should be the same
								# If they differ, jump inside the current operation
								# TODO OP_JUMP* opcodes can also mean while-loops, figure out how to differentiate 'if' from 'while'
								resultString = f"if ({negationString}{argumentString}) {{"
								if jumpDistance == 0:
									# TODO: Assuming a jump distance of 0 just means a return, verify whether that's true
									resultString += " return }"
								if self._resultList and self._resultList[-1].endswith("} else {"):
									# The previous entry was an else, make that an else-if
									self._resultList.pop()
									self._reduceIndent(f"}} else {resultString}")
								else:
									self._addToResult(resultString)
								if jumpDistance > 0:
									if instructionLine.instructionCount == 1:
										# If an IF is on a line by itself, it means we jump one or more lines ahead
										self._addReduceIndentEntry(instructionLine)
									else:
										# This means we jump ahead inside the current instruction line, so encapsulate the next few operations
										operationIndexesToReduceIndentAt.append(operationIndex + jumpDistance + 1)
										self._indentLevel += 1
								arguments.clear()
					elif opCode == opCodeEnum.OP_JUMP:
						# A jump without a True or False check is probably an 'else'
						self._reduceIndent("} else {")
						self._addReduceIndentEntry(instructionLine)
						if len(arguments) > 0:
							DinkFunctionDecompiler._printWarning(f"Not expecting any arguments, but found {len(arguments)}", operation)
							arguments.clear()
					elif opCode == opCodeEnum.OP_UNOT:
						if len(arguments) == 0:
							DinkFunctionDecompiler._printWarning(f"Expected an argument, but none are on the stack", operation)
						else:
							if ' ' in arguments[-1]:
								arguments[-1] = f"!({arguments[-1]} )"
							else:
								arguments[-1] = f"!{arguments[-1]}"

					elif opCode == opCodeEnum.OP_RETURN:
						argumentString = ", ".join(arguments)
						self._addToResult(f"return {argumentString}")
						arguments.clear()

					elif self._dinkFunction.parentScript.game == Game.DELORES:
						# Some opcodes only exist in Delores
						# TODO Delores opcodes to implement: 'OP_SUB', 'OP_MUL', 'OP_DIV', 'OP_SHIFTL', 'OP_SHIFTR', 'OP_MOD', 'OP_BAND', 'OP_BOR'
						if opCode in (opCodeEnum.OP_EQEQ, opCodeEnum.OP_NEQ, opCodeEnum.OP_LT, opCodeEnum.OP_LEQ, opCodeEnum.OP_GEQ, opCodeEnum.OP_GT, opCodeEnum.OP_IN):
							if len(arguments) != 2:
								DinkFunctionDecompiler._printWarning(f"Needs 2 arguments, but there are {len(arguments)} arguments stored", operation)
							firstValue, secondValue = DinkFunctionDecompiler._popLastArguments(arguments, 2, operation)
							arguments.append(f"{firstValue} {DinkFunctionDecompiler._COMPARISION_OPCODE_TO_STRING[opCode]} {secondValue}")
						elif opCode == opCodeEnum.OP_ADD:
							if len(arguments) != 2:
								DinkFunctionDecompiler._printWarning(f"Needs 2 arguments, but there are {len(arguments)} stored", operation)
							firstValue, secondValue = DinkFunctionDecompiler._popLastArguments(arguments, 2, operation)
							arguments.append(f"{firstValue} + {secondValue}")
					elif self._dinkFunction.parentScript.game == Game.RETURN_TO_MONKEY_ISLAND:
						# Some opcodes only exist in RtMI
						# TODO RtMI opcodes to implement: 'OP_MATH', 'OP_BREAKPOINT'
						if opCode == opCodeEnum.OP_NULL_LOCAL:
							self._addToResult(f"{self._dinkFunction.getVariable(operation.parameter3)} <- null")
						elif opCode == opCodeEnum.OP_MATH:
							# TODO: Presumably parameter3 indicates the type of math, verify this and find out which values mean which comparison
							# if operation.parameter3 == 59:
							# 	# Formatting? See the first lambda in RtMI's Dead.dinky, function KKGJTNDIVSGNAUJZ, line 37
							# 	if len(arguments) != 3:
							# 		DinkFunctionDecompiler._printWarning(f"Formatting needs 3 arguments, but found {len(arguments)}", operation)
							# 		for i in range(3 - len(arguments)):
							# 			arguments.append("[[missing]]")
							# 	self._addToResult(f"")
							if operation.parameter3 == 63:
								# FIXME Assume this means equals, make it share code with Delores's OP_EQEQ
								if len(arguments) != 2:
									DinkFunctionDecompiler._printWarning(f"Equalling needs 2 arguments, but there are {len(arguments)} arguments stored", operation)
								# TODO: Make this raise an error instead of printing a warning once opcode parsing is expanded
								else:
									arguments = [f"{arguments[-2]} == {arguments[-1]}"]
							else:
								DinkFunctionDecompiler._printWarning(f"Unsupported math type {operation.parameter3}", operation)
					if operationIndex in operationIndexesToReduceIndentAt:
						if not self._indentLevelWasAdded:
							self._reduceIndent()
						operationIndexesToReduceIndentAt.remove(operationIndex)
				# End of operations for-loop
				# Check if we reached the end of an if/else block, in which case we need to add a closing bracket
				if instructionLine.lineNumber in self._reduceIndentAtLineNumbers:
					if not self._indentLevelWasAdded:
						self._reduceIndent()
						self._reduceIndentAtLineNumbers.remove(instructionLine.lineNumber)

			# End of instruction line for-loop
			# Check if we have some left-over arguments
			if len(arguments) > 0:
				# There are some arguments left, assume those are the return value
				argumentString = ", ".join(arguments)
				self._addToResult(f"return {argumentString}")
			if self._indentLevel > 1:
				print(f"Function wasn't closed properly, there are still {self._indentLevel} indent levels, where 1 is expected")
			# Close the function
			self._reduceIndent("} [end function]")
		except Exception as e:
			print(f"{type(e)} Exception while printing function {self._dinkFunction.name} in script {self._dinkFunction.parentScript.name}: {e}")
			print(f"Lines:" + "\n".join(self._resultList))
			raise e

	@staticmethod
	def _printWarning(warningMessage: str, operation: "DinkInstructionOperation"):
		print(f"WARNING:DinkFunction:{operation.parentFunction.parentScript.name}:{operation.parentFunction.name}:{operation.opCode.name} {warningMessage} [{operation}]")

	@staticmethod
	def _popLastArguments(arguments: List, argumentCount: int, operation: "DinkInstructionOperation") -> List:
		if len(arguments) < argumentCount:
			DinkFunctionDecompiler._printWarning(f"Tried to pop {argumentCount} arguments, but there are only {len(arguments)}", operation)
			for i in range(argumentCount - len(arguments)):
				arguments.append('[[missing]]')
		argumentsToReturn = arguments[-argumentCount:]
		# Remove the popped arguments from the arguments list
		if len(arguments) == argumentCount:
			arguments.clear()
		else:
			del arguments[-argumentCount:]
		return argumentsToReturn

	def _addToResult(self, resultToAdd: str):
		if self._indentLevel < 0 or self._indentLevel >= len(self._INDENT_LEVELS):
			print(f"Not enough indent levels for adding '{resultToAdd}', requested indent level is {self._indentLevel}")
			indent = self._INDENT_LEVELS[-1]
		else:
			indent = self._INDENT_LEVELS[self._indentLevel]
		self._resultList.append(f"{indent}{resultToAdd}")

	def _addReduceIndentEntry(self, targetLine: "DinkInstructionLine"):
		if targetLine.lineNumber not in self._reduceIndentAtLineNumbers:
			self._reduceIndentAtLineNumbers.append(targetLine.lineNumber)
		self._indentLevel += 1
		self._indentLevelWasAdded = True

	def _reduceIndent(self, indentCloseString: str = "}"):
		self._indentLevel -= 1
		self._addToResult(indentCloseString)

	def __str__(self):
		return "\n".join(self._resultList)
