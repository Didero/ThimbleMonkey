import Keys

def fromBytes(sourceBytes: bytes) -> str:
	sourceLength = len(sourceBytes)
	decodedBytes = bytearray(sourceLength)
	keyOffset = sourceLength & 0xFF
	keyLength = len(Keys.THIMBLEWEED_PARK_BNUT_KEY)
	for index in range(sourceLength):
		decodedBytes[index] = sourceBytes[index] ^ Keys.THIMBLEWEED_PARK_BNUT_KEY[(index + keyOffset) % keyLength]
	return bytes(decodedBytes).decode('utf-8')
