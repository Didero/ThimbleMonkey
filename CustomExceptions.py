class DecodeError(Exception):
	"""Raised when something goes wrong with decoding a ggpack file"""
	pass

class PackingError(Exception):
	"""Raised when something goes wrong while packing files into a new ggpack file"""
	pass


class DinkError(Exception):
	"""Raised when something goes wrong with parsing a DinkParser script file"""
	pass

class KtxError(Exception):
	"""Raised when something goes wrong with parsing a KTX image file"""
	pass

class GGDictError(Exception):
	"""Raised when something goes wrong with parsing a GGDict structure"""
	pass

class YackError(Exception):
	"""Raised when something goes wrong with parsing a Yack conversation file"""
	pass
