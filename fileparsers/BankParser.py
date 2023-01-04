# Parses the .assets.bank files, which contain RIFF data, and the Fmod FSB section encoded in an SND chunk
# Based on https://github.com/bgbennyboy/Dinky-Explorer/blob/master/ThimbleweedLibrary/FMODBankExtractor.cs and https://github.com/SamboyCoding/Fmod5Sharp

import multiprocessing, time
from typing import Dict, Tuple

import fsb5

import Keys


_byteReverseLookup = []
# Pre-fill the conversion array since there's only 256 possibilities, speeds up reversing
for i in range(256):
    rev = (i >> 4) | ((i & 0xF) << 4)
    rev = ((rev & 0xCC) >> 2) | ((rev & 0x33) << 2)
    rev = ((rev & 0xAA) >> 1) | ((rev & 0x55) << 1)
    _byteReverseLookup.append(rev)
del i, rev


def _decode(bytesToDecode: bytes) -> bytearray:
    numberOfSections = 8
    startTime = time.perf_counter()
    numberOfBytesToDecode = len(bytesToDecode)
    sectionSize = len(bytesToDecode) // numberOfSections
    currentSectionIndex = 0
    asyncResults = []
    with multiprocessing.Pool(numberOfSections) as pool:
        while currentSectionIndex < numberOfBytesToDecode:
            asyncResult = pool.apply_async(__decodeSection, (bytesToDecode[currentSectionIndex:min(currentSectionIndex + sectionSize, numberOfBytesToDecode)], currentSectionIndex))
            asyncResults.append(asyncResult)
            currentSectionIndex += sectionSize
        pool.close()
        pool.join()
    decodedBytes = bytearray(numberOfBytesToDecode)
    for asyncResult in asyncResults:
        startIndex, decodedSection = asyncResult.get()
        decodedBytes[startIndex:startIndex + len(decodedSection)] = decodedSection
    print(f"Decoding to bytes after {time.perf_counter() - startTime} seconds")
    return decodedBytes

def __decodeSection(sectionToDecode: bytes, startIndex: int) -> Tuple[int, bytearray]:
    decodedBytes = bytearray(len(sectionToDecode))
    maxKeyIndex = len(Keys.RTMI_KEY_SOUNDBANK) - 1
    keyIndex = startIndex % len(Keys.RTMI_KEY_SOUNDBANK)
    for i in range(len(sectionToDecode)):
        decodedBytes[i] = _byteReverseLookup[sectionToDecode[i]] ^ Keys.RTMI_KEY_SOUNDBANK[keyIndex]
        if keyIndex == maxKeyIndex:
            keyIndex = 0
        else:
            keyIndex += 1
    return (startIndex, decodedBytes)

def fromBytesToBank(sourceData: bytes, shouldDecodeData: bool = True) -> fsb5.FSB5:
    """Converts the BANK music and sound data into something useful"""
    if shouldDecodeData:
        decodedSourceData = _decode(sourceData)
    else:
        decodedSourceData = sourceData
    fsbStartIndex = decodedSourceData.index(b'FSB5')
    soundbank = fsb5.FSB5(decodedSourceData[fsbStartIndex:])
    return soundbank

def fromBankToBytesDict(soundbank: fsb5.FSB5) -> Dict[str, bytes]:
    """Converts the BANK sound data into a dict with filenames as the keys and the sounddata as values"""
    sounds = {}
    for sample in soundbank.samples:
        sounds[sample.name + '.ogg'] = bytes(soundbank.rebuild_sample(sample))
    return sounds
