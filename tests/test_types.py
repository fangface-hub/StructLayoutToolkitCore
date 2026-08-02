"""Tests for sltcore.types."""
import math

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


def test_info_byte_swap():
    """Test the byte_swap property."""
    # 2 bytes swap
    info = Info(0xAABB, InfoSize(2, 0))
    swapped = info.byte_swap
    assert swapped.raw_value == 0xBBAA
    assert swapped.info_size == info.info_size

    # 4 bytes swap
    info = Info(0x11223344, InfoSize(4, 0))
    swapped = info.byte_swap
    assert swapped.raw_value == 0x44332211

    # Check that it doesn't affect original
    assert info.raw_value == 0x11223344


def test_info_from_signed_int():
    """Test Info.from_signed_int class method."""
    size = InfoSize(0, 4)
    # Should mask to 4 bits
    info = Info.from_signed_int(0xFF, size)
    assert info.raw_value == 0x0F
    assert info.info_size == size


def test_info_from_signed_int_uses_two_complement_for_negative_values():
    """Negative values should be encoded as two's complement within the size."""
    size = InfoSize(0, 8)

    info = Info.from_signed_int(-1, size)
    assert info.raw_value == 0xFF
    assert info.to_signed_int == -1

    info = Info.from_signed_int(-128, size)
    assert info.raw_value == 0x80
    assert info.to_signed_int == -128


def test_info_from_unsigned_int_masks_to_size():
    """Info.from_unsigned_int should keep only the requested bit width."""
    size = InfoSize(0, 4)

    info = Info.from_unsigned_int(0xFF, size)
    assert info.raw_value == 0x0F
    assert info.info_size == size
    assert info.to_unsigned_int == 0x0F


def test_info_from_unsigned_int_preserves_small_values():
    """Small unsigned values should remain unchanged when they fit the size."""
    size = InfoSize(0, 8)

    info = Info.from_unsigned_int(0x7A, size)
    assert info.raw_value == 0x7A
    assert info.to_unsigned_int == 0x7A


def test_info_from_bytes():
    """Test Info.from_bytes class method."""
    size = InfoSize(2, 0)
    buf = b'\xAA\xBB\xCC'
    info = Info.from_bytes(buf, size)
    assert isinstance(info.raw_value, bytearray)
    assert info.raw_value == bytearray([0xAA, 0xBB, 0xCC])
    assert info.info_size == size


def test_info_from_bytearray():
    """Test Info.from_bytearray class method."""
    size = InfoSize(1, 0)
    buf = bytearray([0xDD, 0xEE])
    info = Info.from_bytearray(buf, size)
    assert isinstance(info.raw_value, bytearray)
    assert info.raw_value == bytearray([0xDD, 0xEE])
    assert info.info_size == size


def test_info_from_bytearray_returns_copy_for_byte_aligned_size():
    """Byte-aligned from_bytearray should keep a copy, not source reference."""
    size = InfoSize(2, 0)
    source = bytearray([0x10, 0x20])

    info = Info.from_bytearray(source, size)
    source[0] = 0xFF

    assert info.raw_value == bytearray([0x10, 0x20])


def test_info_from_float():
    """Test Info.from_float class method."""
    # 32-bit float 1.0
    size = InfoSize(0, 32)
    info = Info.from_float(1.0, size)
    assert info.raw_value == 0x3F800000

    # Round trip
    assert info.to_float == 1.0


def test_info_from_float_special_values():
    """Test Info.from_float with special values like infinity and NaN."""
    # Infinity
    info_inf = Info.from_float(float('inf'), InfoSize(0, 32))
    assert info_inf.to_float == float('inf')

    # Negative Infinity
    info_ninf = Info.from_float(float('-inf'), InfoSize(0, 32))
    assert info_ninf.to_float == float('-inf')

    # NaN (Note: NaN != NaN, so we check using math.isnan)
    info_nan = Info.from_float(float('nan'), InfoSize(0, 32))
    assert math.isnan(info_nan.to_float)


def test_info_from_float_zero():
    """Test Info.from_float with zero values."""
    info_pos_zero = Info.from_float(0.0, InfoSize(0, 32))
    assert info_pos_zero.raw_value == 0x00000000

    info_neg_zero = Info.from_float(-0.0, InfoSize(0, 32))
    # In IEEE 754, -0.0 has the sign bit set
    assert info_neg_zero.raw_value == 0x80000000
