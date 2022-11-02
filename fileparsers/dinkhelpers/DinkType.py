from enum import Enum

class DinkBlockType(Enum):
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


class DinkVariableType(Enum):
	VARIABLE_TYPE_INT = 0x102
	VARIABLE_TYPE_FLOAT = 0x103
	VARIABLE_TYPE_STRING = 0x204
