# Parses the .assets.bank files, which contain RIFF data, and the Fmod FSB section encoded in an SND chunk
# Based on https://github.com/bgbennyboy/Dinky-Explorer/blob/master/ThimbleweedLibrary/FMODBankExtractor.cs and https://github.com/SamboyCoding/Fmod5Sharp

import ctypes, multiprocessing, time
from io import BytesIO
from typing import Dict, Tuple

import fsb5, fsb5.vorbis_headers
import pyogg, pyogg.ogg, pyogg.vorbis

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

def rebuildSample(sample: fsb5.Sample) -> bytes:
    crc32 = sample.metadata[11].crc32
    try:
        setup_packet_buff = fsb5.vorbis_headers.lookup[crc32]
    except KeyError as e:
        raise ValueError('Could not find header info for crc32=%d' % crc32) from e

    info = pyogg.vorbis.vorbis_info()
    pyogg.vorbis.vorbis_info_init(info)
    comment = pyogg.vorbis.vorbis_comment()
    pyogg.vorbis.vorbis_comment_init(comment)
    state = pyogg.ogg.ogg_stream_state()
    pyogg.ogg.ogg_stream_init(state, 1)
    outbuf = BytesIO()

    id_header = _rebuild_id_header(sample.channels, sample.frequency, 0x100, 0x800)
    comment_header = _rebuild_comment_header()
    setup_header = _rebuild_setup_header(setup_packet_buff)

    pyogg.vorbis.vorbis_synthesis_headerin(info, comment, id_header)
    pyogg.vorbis.vorbis_synthesis_headerin(info, comment, comment_header)
    pyogg.vorbis.vorbis_synthesis_headerin(info, comment, setup_header)

    pyogg.ogg.ogg_stream_packetin(state, id_header)
    _write_packets(state, outbuf, pyogg.ogg.ogg_stream_pageout)
    pyogg.ogg.ogg_stream_packetin(state, comment_header)
    _write_packets(state, outbuf, pyogg.ogg.ogg_stream_pageout)
    pyogg.ogg.ogg_stream_packetin(state, setup_header)
    _write_packets(state, outbuf, pyogg.ogg.ogg_stream_pageout)
    _write_packets(state, outbuf, pyogg.ogg.ogg_stream_flush)

    packetno = setup_header.packetno
    granulepos = 0
    prev_blocksize = 0

    inbuf = fsb5.BinaryReader(BytesIO(sample.data))
    packet_size = inbuf.read_type('H')
    while packet_size:
        packetno += 1

        packet = pyogg.ogg.ogg_packet()
        buf = ctypes.create_string_buffer(inbuf.read(packet_size), packet_size)
        packet.packet = ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte))
        packet.bytes = packet_size
        packet.packetno = packetno

        try:
            packet_size = inbuf.read_type('H')
        except ValueError:
            packet_size = 0
        packet.e_o_s = 1 if not packet_size else 0

        blocksize = pyogg.vorbis.vorbis_packet_blocksize(info, packet)
        assert blocksize

        granulepos = int(granulepos + (blocksize + prev_blocksize) / 4) if prev_blocksize else 0
        packet.granulepos = granulepos
        prev_blocksize = blocksize

        pyogg.ogg.ogg_stream_packetin(state, packet)
        _write_packets(state, outbuf, pyogg.ogg.ogg_stream_pageout)

    # Cleanup (from FSB5's classes' __del__ methods
    pyogg.vorbis.vorbis_info_clear(info)
    pyogg.vorbis.vorbis_comment_clear(comment)
    pyogg.ogg.ogg_stream_clear(state)

    return bytes(outbuf.getbuffer())

def _rebuild_id_header(channels, frequency, blocksize_short, blocksize_long):
    packet = pyogg.ogg.ogg_packet()

    buf = pyogg.ogg.oggpack_buffer()
    pyogg.ogg.oggpack_writeinit(buf)
    pyogg.ogg.oggpack_write(buf, 0x01, 8)
    for c in 'vorbis':
        pyogg.ogg.oggpack_write(buf, ord(c), 8)
    pyogg.ogg.oggpack_write(buf, 0, 32)
    pyogg.ogg.oggpack_write(buf, channels, 8)
    pyogg.ogg.oggpack_write(buf, frequency, 32)
    pyogg.ogg.oggpack_write(buf, 0, 32)
    pyogg.ogg.oggpack_write(buf, 0, 32)
    pyogg.ogg.oggpack_write(buf, 0, 32)
    pyogg.ogg.oggpack_write(buf, len(bin(blocksize_short)) - 3, 4)
    pyogg.ogg.oggpack_write(buf, len(bin(blocksize_long)) - 3, 4)
    pyogg.ogg.oggpack_write(buf, 1, 1)

    if hasattr(pyogg.ogg, 'oggpack_writecheck'):
        pyogg.ogg.oggpack_writecheck(buf)

    packet.bytes = pyogg.ogg.oggpack_bytes(buf)
    bufString = ctypes.create_string_buffer(bytes(buf.buffer[:packet.bytes]), packet.bytes)
    packet.packet = ctypes.cast(ctypes.pointer(bufString), ctypes.POINTER(ctypes.c_ubyte))
    packet.b_o_s = 1
    packet.e_o_s = 0
    packet.granulepos = 0
    packet.packetno = 0
    pyogg.ogg.oggpack_writeclear(buf)

    return packet

def _rebuild_comment_header():
    packet = pyogg.ogg.ogg_packet()
    pyogg.ogg.ogg_packet_clear(packet)

    comment = pyogg.vorbis.vorbis_comment()
    pyogg.vorbis.vorbis_comment_init(comment)
    pyogg.vorbis.vorbis_commentheader_out(comment, packet)
    pyogg.vorbis.vorbis_comment_clear(comment)
    return packet

def _rebuild_setup_header(setup_packet_buff):
    packet = pyogg.ogg.ogg_packet()

    packet.packet = ctypes.cast(ctypes.pointer(ctypes.create_string_buffer(setup_packet_buff, len(setup_packet_buff))), ctypes.POINTER(ctypes.c_ubyte))
    packet.bytes = len(setup_packet_buff)
    packet.b_o_s = 0
    packet.e_o_s = 0
    packet.granulepos = 0
    packet.packetno = 2

    return packet

def _write_packets(state, buf, func):
    page = pyogg.ogg.ogg_page()
    while func(state, page):
        buf.write(bytes(page.header[:page.header_len]))
        buf.write(bytes(page.body[:page.body_len]))
