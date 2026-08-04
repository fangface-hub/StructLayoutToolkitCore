"""Tests for sltcore.bits."""

from sltcore.bits import _required_bytes_for_extraction, bits_get, bits_set
from sltcore.types import Info, InfoSize


def test_required_bytes_for_extraction():
    """Test the _required_bytes_for_extraction function
       with various scenarios."""
    # offset.bit + size.bits < 8 → 1 byte
    assert _required_bytes_for_extraction(InfoSize(0, 0), InfoSize(0, 7)) == 1

    # Exactly 8 → 1 byte
    assert _required_bytes_for_extraction(InfoSize(0, 0), InfoSize(0, 8)) == 1

    # 9 → 2 bytes
    assert _required_bytes_for_extraction(InfoSize(0, 0), InfoSize(0, 9)) == 2

    # With offset.bit
    assert _required_bytes_for_extraction(InfoSize(0, 3), InfoSize(0, 5)) == 1
    assert _required_bytes_for_extraction(InfoSize(0, 6), InfoSize(0, 4)) == 2


def test_bits_get_single_byte():
    """Test bits_get with a single byte buffer."""
    buf = bytearray([0b11010110])  # 214
    offset = InfoSize(0, 2)  # bit offset = 2
    size = InfoSize(0, 4)  # 4 bits

    info = bits_get(buf, offset, size, scale=0.5)
    assert info.raw_value == 0b0101  # 214 = 11010110 → offset=2 → 0101
    assert info.scale == 0.5


def test_bits_get_cross_byte():
    """Test bits_get with a buffer that spans multiple bytes."""
    buf = bytearray([0b11110000, 0b00001111])
    offset = InfoSize(0, 6)  # From bit 6 of byte0
    size = InfoSize(0, 6)  # Extract 6 bits (spans into byte1)

    info = bits_get(buf, offset, size, scale=0.25)
    # 11110000 00001111
    #       ^^ ^^^^
    assert info.raw_value == 0b000000  # front-packed
    assert info.scale == 0.25


def test_bits_set_single_byte():
    """Test bits_set with a single byte buffer."""
    buf = bytearray([0b11110000])
    offset = InfoSize(0, 2)
    size = InfoSize(0, 4)

    bits_set(buf, offset, Info(0b0011, size))
    # 11110000 → offset=2 → bits to change: 1100 → write 0011
    assert buf[0] == 0b11001100


def test_bits_set_cross_byte():
    """Test bits_set with a buffer that spans multiple bytes."""
    buf = bytearray([0b11110000, 0b00001111])
    offset = InfoSize(0, 6)
    size = InfoSize(0, 6)

    bits_set(buf, offset, Info(0b101010, size))

    # Comparing with a manually calculated mask is fine, but
    # confirming it matches by re-extracting with bits_get
    # is more abstract and robust
    info = bits_get(buf, offset, size)

    assert info.raw_value == 0b101010


def test_bits_get_set_roundtrip():
    """Test that bits_get followed by bits_set returns the original value."""
    buf = bytearray([0xAA, 0xBB, 0xCC, 0xDD])

    offset = InfoSize(0, 5)
    size = InfoSize(0, 10)

    # Verify original value is restored through get -> set cycle
    original = bits_get(buf, offset, size).raw_value

    bits_set(buf, offset, Info(original, size))
    after = bits_get(buf, offset, size).raw_value

    assert original == after


def test_bits_get_byte_aligned_returns_slice():
    """When both offset.bit and size.bit are 0,
       raw_value is a bytearray slice."""
    buf = bytearray([0x11, 0x22, 0x33, 0x44])
    info = bits_get(buf, InfoSize(1, 0), InfoSize(2, 0), scale=2.0)

    assert isinstance(info.raw_value, bytearray)
    assert info.raw_value == bytearray([0x22, 0x33])
    assert info.info_size == InfoSize(2, 0)
    assert info.scale == 2.0


def test_bits_get_zero_size_byte_aligned_returns_empty_slice():
    """Byte-aligned zero-length extraction should return an empty slice."""
    buf = bytearray([0xAA, 0xBB])
    info = bits_get(buf, InfoSize(1, 0), InfoSize(0, 0))

    assert isinstance(info.raw_value, bytearray)
    assert info.raw_value == bytearray()
    assert info.info_size == InfoSize(0, 0)


def test_bits_set_bytearray_byte_aligned_sets_slice():
    """Byte-aligned write with bytearray value should set target slice."""
    buf = bytearray([0x00, 0x00, 0x00, 0x00])

    bits_set(
        buf,
        InfoSize(1, 0),
        Info(bytearray([0xAA, 0xBB]), InfoSize(2, 0)),
    )

    assert buf == bytearray([0x00, 0xAA, 0xBB, 0x00])


def test_bits_set_bytearray_non_aligned_uses_lower_bits_path():
    """Non-aligned bytearray write uses lower bits like integer writes."""
    buf = bytearray([0b11110000, 0b00001111])
    offset = InfoSize(0, 6)
    size = InfoSize(0, 6)

    bits_set(
        buf,
        offset,
        Info(bytearray([0b10101000]), InfoSize(0, 6)),
    )
    info = bits_get(buf, offset, size)

    assert info.raw_value == 0b101000
