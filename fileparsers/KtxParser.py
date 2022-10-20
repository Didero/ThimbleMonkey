# Convert KTX image files to something we can use
# The file format specification is here: https://registry.khronos.org/KTX/specs/1.0/ktxspec_v1.html

import zlib
from io import BytesIO
from typing import List

import texture2ddecoder
from PIL import Image

import Utils
from CustomExceptions import KtxError


_HEADER = b'\xAB\x4B\x54\x58\x20\x31\x31\xBB\x0D\x0A\x1A\x0A'
_ENDIANNESS_CHECK_LITTLE = b'\x04\x03\x02\x01'
_ENDIANNESS_CHECK_BIG = b'\x01\x02\x03\x04'

def _checkValue(expected, actual, errorMessagePrefix="Unexpected value"):
	if expected != actual:
		errorMessagePrefix = errorMessagePrefix
		printableExpected = Utils.getPrintableBytes(expected) if isinstance(expected, bytes) else expected
		printableActual = Utils.getPrintableBytes(actual) if isinstance(actual, bytes) else actual
		raise KtxError(f"{errorMessagePrefix}. Expected '{printableExpected}' but found '{printableActual}'")

def fromKtx(ktxData: bytes, filename: str, detailLevelsToLoad: int = -1) -> List[Image.Image]:
	"""
	Convert the provided KTX-formatted image data into a list of Pillow images, one for each mipmap (or detail) level
	:param ktxData: The KTX-formatted data to convert
	:param filename: The filename of the KTX image file. This is needed to determine whether the data is compressed or not
	:param detailLevelsToLoad: A lot of the images contain different detail levels, or mipmaps. If this number is specified, only load that number of mipmap levels, instead of all of them
	:return: A list of Pillow Images, one for each mipmap level. The first image in the list is full-size, the next one is half the size, the following quarter size, and so on
	"""
	if filename.endswith('bz'):
		# The image data is compressed, decompress it first
		ktxReader: BytesIO = BytesIO(zlib.decompress(ktxData))
	else:
		ktxReader: BytesIO = BytesIO(ktxData)
	# Header
	_checkValue(_HEADER, ktxReader.read(12), "Invalid header in KTX data")
	# A value indicating if it's little or big endian
	checkValue = ktxReader.read(4)
	if checkValue != _ENDIANNESS_CHECK_LITTLE and checkValue != _ENDIANNESS_CHECK_BIG:
		raise KtxError(f"Unexpected endian field in KTX data. Expected '{Utils.getPrintableBytes(_ENDIANNESS_CHECK_LITTLE)}' or '{Utils.getPrintableBytes(_ENDIANNESS_CHECK_BIG)}' but found {Utils.getPrintableBytes(checkValue)}'")
	# glType, whether the data is compressed or not
	_checkValue(0, Utils.readInt(ktxReader), "Unexpected glType")
	# glTypeSize, should be the 1 since glType should be compressed
	_checkValue(1, Utils.readInt(ktxReader), "Unexpected glTypeSize")
	# glFormat, should be 0x1908, GL_RGBA
	_checkValue(0x1908, Utils.readInt(ktxReader), "Unsupported glFormat")
	# glInternalFormat and glBaseInternalFormat should be 0x8e8c, GL_COMPRESSED_RGBA_BPTC_UNORM or GL_COMPRESSED_RGBA_BPTC_UNORM_ARB
	_checkValue(0x8e8c, Utils.readInt(ktxReader), "Unsupported glInternalFormat")
	_checkValue(0x8e8c, Utils.readInt(ktxReader), "Unsupported glBaseInternalFormat")

	imageWidth = Utils.readInt(ktxReader)
	imageHeight = Utils.readInt(ktxReader)
	_checkValue(0, Utils.readInt(ktxReader), "Unexpected image depth")

	# Number of array elements, should be 0
	_checkValue(0, Utils.readInt(ktxReader), "Unexpected number of array elements")
	# Number of faces, should be 1
	_checkValue(1, Utils.readInt(ktxReader), "Unexpected number of faces")

	originalMipmapCount = Utils.readInt(ktxReader)
	if detailLevelsToLoad and detailLevelsToLoad > 0:
		mipmapCount = min(originalMipmapCount, detailLevelsToLoad)
	else:
		mipmapCount = originalMipmapCount
	mipmapCount = max(1, mipmapCount)

	numberOfKeyValuePairBytes = Utils.readInt(ktxReader)
	if numberOfKeyValuePairBytes > 0:
		# Skip these for now
		print(f"[KtxParser] Skipping {numberOfKeyValuePairBytes:,} key-value pair bytes")
		ktxReader.read(numberOfKeyValuePairBytes)

	# Read in the mipmap levels
	imagesPerMipMap = []
	for mipmapLevelIndex in range(mipmapCount):
		imageBytesCount = Utils.readInt(ktxReader)
		# Each mipmap level is half the width and half the height of the previous one, so divide the original image width and height by the current mipmap level
		mipmapWidth = max(1, imageWidth // (2 ** mipmapLevelIndex))
		mipmapHeight = max(1, imageHeight // (2 ** mipmapLevelIndex))
		imageData = texture2ddecoder.decode_bc7(ktxReader.read(imageBytesCount), mipmapWidth, mipmapHeight)
		pilImage = Image.frombytes("RGBA", (mipmapWidth, mipmapHeight), imageData, 'raw', ("BGRA",))
		imagesPerMipMap.append(pilImage)
	return imagesPerMipMap
