from enum import IntEnum


class DinkOpCodeDelores(IntEnum):
	UNKNOWN = -1
	# Opcodes are extracted from Delores executable
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
	OP_ADD = 17
	OP_SUB = 18
	OP_MUL = 19
	OP_DIV = 20
	OP_SHIFTL = 21
	OP_SHIFTR = 22
	OP_MOD = 23
	OP_EQEQ = 24
	OP_NEQ = 25
	OP_LT = 26
	OP_GT = 27
	OP_LEQ = 28
	OP_GEQ = 29
	OP_LAND = 30
	OP_LOR = 31
	OP_BAND = 32
	OP_BOR = 33
	OP_IN = 34
	OP_INDEX = 35
	OP_ITERATE = 36
	OP_ITERATEKV = 37
	OP_CALL = 38
	OP_FCALL = 39
	OP_CALLINDEXED = 40
	OP_CALL_NATIVE = 41
	OP_FCALL_NATIVE = 42
	OP_POP = 43
	OP_STORE_LOCAL = 44
	OP_STORE_UPVAR = 45
	OP_STORE_ROOT = 46
	OP_STORE_VAR = 47
	OP_STORE_INDEXED = 48
	OP_SET_LOCAL = 49
	OP_MATH_REF = 50
	OP_INC_REF = 51
	OP_DEC_REF = 52
	OP_ADD_LOCAL = 53
	OP_JUMP = 54
	OP_JUMP_TRUE = 55
	OP_JUMP_FALSE = 56
	OP_JUMP_TOPTRUE = 57
	OP_JUMP_TOPFALSE = 58
	OP_TERNARY = 59
	OP_NEW_TABLE = 60
	OP_NEW_ARRAY = 61
	OP_NEW_SLOT = 62
	OP_NEW_THIS_SLOT = 63
	OP_DELETE_SLOT = 64
	OP_RETURN = 65
	OP_CLONE = 66
	OP_REMOVED = 67
	OP_LAST__ = 68  # Originally '__OP_LAST__'
	OP_LABEL_ = 69  # Originally '_OP_LABEL_'

class DinkOpCodeRtmi(IntEnum):
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