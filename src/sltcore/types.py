"""Type definitions for structured data layouts and bit-level operations."""
import math
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

    @classmethod
    def from_int(cls, value: int, size: InfoSize):
        """Creates an Info instance from an integer value, ensuring that
           the value fits within the specified size by applying a bitmask. """
        return cls(value & size.mask, size)

    @classmethod
    def from_bytes(cls, buf: bytes, size: InfoSize):
        """Creates an Info instance from a bytes object, ensuring that
           the value fits within the specified size by applying a bitmask."""
        return cls(int.from_bytes(buf[:size.bytes], "big") & size.mask, size)

    @classmethod
    def from_bytearray(cls, buf: bytearray, size: InfoSize):
        """Creates an Info instance from a bytearray, ensuring that
           the value fits within the specified size by applying a bitmask."""
        return cls(int.from_bytes(buf[:size.bytes], "big") & size.mask, size)

    @classmethod
    def from_float(cls, value: float, size: InfoSize):
        """Creates an Info instance from a float value, converting it to
           its raw bit representation based on the specified size."""
        raw = _float_to_bits(value, size.bits)
        return cls(raw, size)

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

    @property
    def byte_swap(self) -> "Info":
        """Returns a new Info instance with the byte order reversed."""
        swapped_value = int.from_bytes(self.to_bytes[::-1], byteorder="big")
        return Info(swapped_value, self.info_size)


def _float_from_bits(raw: int, bits: int) -> float:
    """Converts a raw integer representation of a float
       to a Python float, based on the specified bit size.
       Supports 16, 32, and 64 bits.
    """
    if bits == 16:
        # IEEE754 half-precision (16bit) → float32
        s = (raw >> 15) & 0x0001
        e = (raw >> 10) & 0x001F
        f = raw & 0x03FF

        if e == 0:
            if f == 0:
                return (-1)**s * 0.0
            return (-1)**s * (f / 2**10) * 2**(-14)
        elif e == 31:
            if f == 0:
                return float('inf') if s == 0 else float('-inf')
            return float('nan')
        else:
            return (-1)**s * (1 + f / 2**10) * 2**(e - 15)
    elif bits == 32:
        # IEEE754 single precision
        # High-speed version without using struct
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


def _float_to_bits(value: float, bits: int) -> int:
    """Converts a Python float to its raw integer representation
       based on the specified bit size. Supports 16, 32, and 64 bits.
    """
    # Determine the sign and absolute value
    # Use math.copysign to correctly detect negative zero
    sign = 1 if math.copysign(1.0, value) < 0 else 0
    v = abs(value)

    # Handle zero
    if v == 0.0:
        return sign << (bits - 1)

    # NaN / Inf
    if math.isnan(value):
        if bits == 16:
            return 0x7E00
        if bits == 32:
            return 0x7FC00000
        if bits == 64:
            return 0x7FF8000000000000

    # Handle infinity
    if math.isinf(value):
        if bits == 16:
            return (sign << 15) | 0x7C00
        if bits == 32:
            return (sign << 31) | 0x7F800000
        if bits == 64:
            return (sign << 63) | 0x7FF0000000000000

    # Compute exponent and mantissa
    e = int(math.floor(math.log(v, 2)))
    mant = v / (2**e) - 1.0

    if bits == 16:
        exp = e + 15
        frac = int(mant * (2**10))
        return (sign << 15) | (exp << 10) | frac

    elif bits == 32:
        exp = e + 127
        frac = int(mant * (2**23))
        return (sign << 31) | (exp << 23) | frac

    elif bits == 64:
        exp = e + 1023
        frac = int(mant * (2**52))
        return (sign << 63) | (exp << 52) | frac

    else:
        raise ValueError(f"Unsupported float bit size: {bits}")
