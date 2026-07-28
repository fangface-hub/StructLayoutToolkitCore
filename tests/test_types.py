"""Tests for sltcore.types."""
import pytest

from sltcore.types import Info, InfoSize


def test_infosize_normalization():
    """Test InfoSize normalization of bits to bytes."""
    # 10 bits should become 1 byte and 2 bits
    size = InfoSize(0, 10)
    assert size.byte == 1
    assert size.bit == 2

    # 16 bits should become 2 bytes and 0 bits
    size = InfoSize(1, 8)
    assert size.byte == 2
    assert size.bit == 0


def test_infosize_bits_property():
    """Test the bits property of InfoSize."""
    size = InfoSize(2, 3)
    assert size.bits == 19  # 2 * 8 + 3


def test_infosize_bytes_property():
    """Test the bytes property of InfoSize (rounding up)."""
    assert InfoSize(1, 0).bytes == 1
    assert InfoSize(1, 1).bytes == 2
    assert InfoSize(1, 7).bytes == 2


def test_infosize_hex_digits():
    """Test the hex_digits property."""
    assert InfoSize(1, 0).hex_digits == 2  # 8 bits / 4
    assert InfoSize(2, 0).hex_digits == 4  # 16 bits / 4


def test_infosize_mask():
    """Test the mask property."""
    assert InfoSize(0, 3).mask == 0b111
    assert InfoSize(1, 0).mask == 0xFF


def test_infosize_arithmetic():
    """Test addition and subtraction of InfoSize."""
    s1 = InfoSize(1, 2)
    s2 = InfoSize(0, 7)

    # Addition
    added = s1 + s2
    assert added.bits == s1.bits + s2.bits

    # Subtraction
    subbed = s1 - s2
    assert subbed.bits == s1.bits - s2.bits

    with pytest.raises(ValueError):
        s2 - s1


def test_info_to_signed_int():
    """Test signed integer conversion."""
    # 8-bit signed
    info = Info(0xFF, InfoSize(1, 0))
    assert info.to_signed_int == -1

    info = Info(0x7F, InfoSize(1, 0))
    assert info.to_signed_int == 127

    # 4-bit signed
    info = Info(0b1111, InfoSize(0, 4))
    assert info.to_signed_int == -1

    info = Info(0b0111, InfoSize(0, 4))
    assert info.to_signed_int == 7


def test_info_to_bytes():
    """Test conversion to bytes object."""
    info = Info(0xAABB, InfoSize(2, 0))
    assert info.to_bytes == b'\xaa\xbb'


def test_info_to_float_16():
    """Test 16-bit float conversion."""
    # 0.0
    assert Info(0x0000, InfoSize(0, 16)).to_float == 0.0
    # 1.0 (sign=0, exp=15, fraction=0) -> 0 01111 0000000000 -> 0x3C00
    assert Info(0x3C00, InfoSize(0, 16)).to_float == 1.0


def test_info_to_float_32():
    """Test 32-bit float conversion."""
    # 1.0 (sign=0, exp=127, fraction=0) -> 0x3F800000
    assert Info(0x3F800000, InfoSize(0, 32)).to_float == 1.0


def test_info_to_float_64():
    """Test 64-bit float conversion."""
    # 1.0 (sign=0, exp=1023, fraction=0) -> 0x3FF0000000000000
    assert Info(0x3FF0000000000000, InfoSize(0, 64)).to_float == 1.0


def test_info_to_float_invalid_size():
    """Test that invalid bit sizes for float conversion raise ValueError."""
    with pytest.raises(ValueError):
        Info(0, InfoSize(0, 10)).to_float
