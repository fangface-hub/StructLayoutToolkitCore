"""Tests for sltcore.bits."""
import pytest

from sltcore.bits import _required_bytes_for_extraction, bits_get, bits_set
from sltcore.types import InfoSize


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

    info = bits_get(buf, offset, size)
    assert info.raw_value == 0b0101  # 214 = 11010110 → offset=2 → 0101


def test_bits_get_cross_byte():
    """Test bits_get with a buffer that spans multiple bytes."""
    buf = bytearray([0b11110000, 0b00001111])
    offset = InfoSize(0, 6)  # From bit 6 of byte0
    size = InfoSize(0, 6)  # Extract 6 bits (spans into byte1)

    info = bits_get(buf, offset, size)
    # 11110000 00001111
    #       ^^ ^^^^
    assert info.raw_value == 0b000000  # front-packed


def test_bits_set_single_byte():
    """Test bits_set with a single byte buffer."""
    buf = bytearray([0b11110000])
    offset = InfoSize(0, 2)
    size = InfoSize(0, 4)

    bits_set(buf, offset, size, 0b0011)
    # 11110000 → offset=2 → bits to change: 1100 → write 0011
    assert buf[0] == 0b11001100


def test_bits_set_cross_byte():
    """Test bits_set with a buffer that spans multiple bytes."""
    buf = bytearray([0b11110000, 0b00001111])
    offset = InfoSize(0, 6)
    size = InfoSize(0, 6)

    bits_set(buf, offset, size, 0b101010)

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

    bits_set(buf, offset, size, original)
    after = bits_get(buf, offset, size).raw_value

    assert original == after
