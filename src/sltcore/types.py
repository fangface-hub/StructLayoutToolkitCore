"""Type definitions for structured data layouts and bit-level operations."""
from dataclasses import dataclass


@dataclass(frozen=True)
class InfoSize:
    """Represents a size in bytes and bits."""
    byte: int = 0
    bit: int = 0

    def __post_init__(self):
        """Ensures that the bit count is normalized to be less than 8,
           and adjusts the byte count accordingly."""
        extra_bytes, new_bits = divmod(self.bit, 8)
        object.__setattr__(self, "byte", self.byte + extra_bytes)
        object.__setattr__(self, "bit", new_bits)

    @property
    def bits(self) -> int:
        """Returns the total size in bits."""
        return self.byte * 8 + self.bit

    @property
    def bytes(self) -> int:
        """Returns the total size in bytes,
           rounding up if there are leftover bits."""
        return (self.bits + 7) // 8  # round up

    @property
    def hex_digits(self) -> int:
        """Returns the number of hexadecimal digits
           needed to represent the size in bits."""
        return self.bits // 4

    @property
    def mask(self) -> int:
        """Returns a bitmask corresponding to the size in bits."""
        return (1 << self.bits) - 1

    def __add__(self, other: "InfoSize") -> "InfoSize":
        """ Adds two InfoSize instances together, returning a new InfoSize
            with the combined byte and bit counts, normalized to ensure
            the bit count is less than 8."""
        return InfoSize(self.byte + other.byte, self.bit + other.bit)

    def __sub__(self, other: "InfoSize") -> "InfoSize":
        """ Subtracts one InfoSize from another, returning a new InfoSize
            with the resulting byte and bit counts, normalized to ensure
            the bit count is less than 8. Raises ValueError if the result
            would be negative."""
        total_bits = self.bits - other.bits
        if total_bits < 0:
            raise ValueError("InfoSize subtraction resulted in negative size")
        return InfoSize(0, total_bits)


@dataclass(frozen=True)
class Info:
    """Represents a slice of bits extracted from a bytearray,
       along with its size information."""
    raw_value: int
    info_size: InfoSize

    @property
    def to_unsigned_int(self) -> int:
        """Returns the extracted bits as an unsigned integer."""
        return self.raw_value

    @property
    def to_signed_int(self) -> int:
        """Returns the extracted bits as a signed integer."""
        raw = self.to_unsigned_int
        bits = self.info_size.bits
        sign_bit = 1 << (bits - 1)
        return (raw ^ sign_bit) - sign_bit

    @property
    def to_hex(self) -> str:
        """Returns the extracted bits as a hexadecimal string."""
        return hex(self.to_unsigned_int)

    @property
    def to_bytes(self) -> bytes:
        """Returns the extracted bits as a bytes object."""
        value = self.to_unsigned_int
        byte_len = self.info_size.bytes
        return value.to_bytes(byte_len, byteorder="big")

    @property
    def to_bool(self) -> bool:
        """Returns the extracted bits as a boolean value."""
        return bool(self.to_unsigned_int)

    @property
    def to_float(self) -> float:
        """Returns the extracted bits as a float."""
        raw_int = self.to_unsigned_int
        return _float_from_bits(raw_int, self.info_size.bits)


def _float_from_bits(raw: int, bits: int) -> float:
    """Converts a raw integer representation of a float
       to a Python float, based on the specified bit size.
       Supports 16, 32, and 64 bits.
    """
    if bits == 16:
        # IEEE754 half precision
        s = (raw >> 15) & 0x1
        e = (raw >> 10) & 0x1F
        f = raw & 0x3FF

        if e == 0:
            if f == 0:
                return -0.0 if s else 0.0
            return (-1)**s * (f / 2**10) * 2**(-14)
        elif e == 31:
            if f == 0:
                return float('-inf') if s else float('inf')
            return float('nan')
        else:
            return (-1)**s * (1 + f / 2**10) * 2**(e - 15)

    elif bits == 32:
        # IEEE754 single precision
        # struct を使わずに変換する高速版
        s = (raw >> 31) & 0x1
        e = (raw >> 23) & 0xFF
        f = raw & 0x7FFFFF

        if e == 0:
            return (-1)**s * (f / 2**23) * 2**(-126)
        elif e == 255:
            if f == 0:
                return float('-inf') if s else float('inf')
            return float('nan')
        else:
            return (-1)**s * (1 + f / 2**23) * 2**(e - 127)

    elif bits == 64:
        # IEEE754 double precision
        s = (raw >> 63) & 0x1
        e = (raw >> 52) & 0x7FF
        f = raw & 0xFFFFFFFFFFFFF

        if e == 0:
            return (-1)**s * (f / 2**52) * 2**(-1022)
        elif e == 2047:
            if f == 0:
                return float('-inf') if s else float('inf')
            return float('nan')
        else:
            return (-1)**s * (1 + f / 2**52) * 2**(e - 1023)

    else:
        raise ValueError(''.join([
            f"Unsupported bit size for float conversion: {bits}. ",
            "Only 16, 32, and 64 are supported."
        ]))
