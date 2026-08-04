"""Type definitions for structured data layouts and bit-level operations."""
import math
import struct
from dataclasses import dataclass, field
from functools import total_ordering


def _has_struct_half():
    """Checks if the current Python environment supports
       half-precision (16-bit) floats in the struct module."""
    try:
        struct.pack(">e", 1.0)
        return True
    except struct.error:
        return False


@total_ordering
@dataclass(frozen=True)
class InfoSize:
    """Represents a size in bytes and bits."""
    byte: int = field(default=0, metadata={"desc": "byte size"})
    bit: int = field(default=0, metadata={"desc": "bit size"})

    def __post_init__(self):
        """Ensures that the bit count is normalized to be less than 8,
           and adjusts the byte count accordingly."""
        extra_bytes = self.bit >> 3
        new_bits = self.bit & 7
        object.__setattr__(self, "byte", self.byte + extra_bytes)
        object.__setattr__(self, "bit", new_bits)

    def __str__(self) -> str:
        """Returns a string representation of the size
           in the format 'X bytes, Y bits'."""
        return f"{self.byte} bytes, {self.bit} bits"

    def __eq__(self, other: object) -> bool:
        """Checks equality between two InfoSize instances
           based on their total size in bits."""
        if not isinstance(other, InfoSize):
            return NotImplemented
        return self.bits == other.bits

    def __lt__(self, other: "InfoSize") -> bool:
        """Compares two InfoSize instances based on their total size in bits."""
        return self.bits < other.bits

    @property
    def bits(self) -> int:
        """Returns the total size in bits."""
        return (self.byte << 3) | self.bit

    @property
    def bytes(self) -> int:
        """Returns the total size in bytes,
           rounding up if there are leftover bits."""
        return (self.bits + 7) >> 3

    @property
    def hex_digits(self) -> int:
        """Returns the number of hexadecimal digits
           needed to represent the size in bits."""
        return self.bits >> 2

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


@total_ordering
@dataclass(frozen=True)
class Info:
    """Represents a slice of bits extracted from a bytearray,
       along with its size information."""
    raw_value: int | bytearray = field(
        default=0, metadata={"desc": "raw value as integer or bytearray"})
    info_size: InfoSize = field(default_factory=InfoSize,
                                metadata={"desc": "size information"})
    scale: float = field(default=1.0, metadata={"desc": "LSB scale"})

    def __str__(self) -> str:
        """Returns a string representation of the Info instance,
           showing the raw value and its size."""
        return ("Info("
                f"raw_value={self.raw_value}, "
                f"info_size={self.info_size}, "
                f"scale={self.scale})")

    def __eq__(self, other: object) -> bool:
        """Checks equality between two Info instances based on their raw values
           and size information."""
        if not isinstance(other, Info):
            return NotImplemented
        return (self.raw_value == other.raw_value
                and self.info_size == other.info_size
                and self.scale == other.scale)

    def __lt__(self, other: "Info") -> bool:
        """Compares two Info instances based on their raw values
           and size information."""
        if not isinstance(other, Info):
            return NotImplemented
        if self.info_size != other.info_size:
            return self.info_size < other.info_size
        return self.to_float < other.to_float

    @classmethod
    def from_unsigned_int(cls, value: int, size: InfoSize, scale: float = 1.0):
        """Creates an Info instance from an unsigned integer value,
           ensuring that the value fits within the specified size by
           applying a bitmask."""
        return cls(value & size.mask, size, scale)

    @classmethod
    def from_bool(cls, value: bool, size: InfoSize, scale: float = 1.0):
        """Creates an Info instance from a boolean value."""
        return cls.from_unsigned_int(int(value), size, scale)

    @classmethod
    def from_signed_int(cls, value: int, size: InfoSize, scale: float = 1.0):
        """Creates an Info instance from a signed integer value using two's
           complement encoding for the requested bit width."""
        if size.bits == 0:
            return cls(0, size, scale)
        return cls(value % (1 << size.bits), size, scale)

    @classmethod
    def from_bytes(cls, buf: bytes, size: InfoSize, scale: float = 1.0):
        """Creates an Info instance from a bytes object, ensuring that
           the value fits within the specified size by applying a bitmask."""
        if size.bit == 0:
            return cls(bytearray(buf), size, scale)
        return cls(
            int.from_bytes(buf[:size.bytes], "big") & size.mask, size, scale)

    @classmethod
    def from_bytearray(cls, buf: bytearray, size: InfoSize, scale: float = 1.0):
        """Creates an Info instance from a bytearray, ensuring that
           the value fits within the specified size by applying a bitmask."""
        if size.bit == 0:
            return cls(bytearray(buf), size, scale)
        return cls(
            int.from_bytes(buf[:size.bytes], "big") & size.mask, size, scale)

    @classmethod
    def from_float(cls, value: float, size: InfoSize, scale: float = 1.0):
        """Creates an Info instance from a float value, converting it to
           its raw bit representation based on the specified size."""
        raw = _value_to_raw(value, size.bits, scale)
        return cls(raw, size, scale)

    @classmethod
    def from_int(cls, value: int, size: InfoSize, scale: float = 1.0):
        """Creates an Info instance from a scaled integer value."""
        return cls.from_float(float(value), size, scale)

    @property
    def to_unsigned_int(self) -> int:
        """Returns the extracted bits as an unsigned integer."""
        if isinstance(self.raw_value, bytearray):
            return int.from_bytes(self.raw_value[:self.info_size.bytes],
                                  "big") & self.info_size.mask
        return self.raw_value

    @property
    def to_signed_int(self) -> int:
        """Returns the extracted bits as a signed integer."""
        if self.info_size.bits == 0:
            return 0
        raw = self.to_unsigned_int
        bits = self.info_size.bits
        sign_bit = 1 << (bits - 1)
        return (raw ^ sign_bit) - sign_bit

    @property
    def to_int(self) -> int:
        """Returns the scaled numeric value as an integer."""
        return int(round(self.to_float))

    @property
    def to_hex(self) -> str:
        """Returns the extracted bits as a hexadecimal string."""
        return hex(self.to_unsigned_int)

    @property
    def to_bytes(self) -> bytes:
        """Returns the extracted bits as a bytes object."""
        byte_len = self.info_size.bytes
        if isinstance(self.raw_value, bytearray):
            return bytes(self.raw_value[:byte_len])
        value = self.to_unsigned_int
        return value.to_bytes(byte_len, byteorder="big")

    @property
    def to_bool(self) -> bool:
        """Returns the extracted bits as a boolean value."""
        return bool(self.to_unsigned_int)

    @property
    def to_float(self) -> float:
        """Returns the extracted bits as a scaled float."""
        raw_int = self.to_unsigned_int
        try:
            return (FLOAT_FROM_BITS_DISPATCH[self.info_size.bits](raw_int) *
                    self.scale)
        except KeyError:
            return float(raw_int) * self.scale

    @property
    def byte_swap(self) -> "Info":
        """Returns a new Info instance with the byte order reversed."""
        swapped_value = int.from_bytes(self.to_bytes[::-1], byteorder="big")
        return Info(swapped_value, self.info_size, self.scale)


def _value_to_raw(value: float, bits: int, scale: float) -> int:
    """Converts a scaled numeric value into a raw integer representation."""
    if scale == 0:
        raise ValueError("scale must not be zero")
    scaled_value = value / scale
    try:
        return FLOAT_TO_BITS_DISPATCH[bits](scaled_value)
    except KeyError:
        if bits == 0:
            return 0
        return int(round(scaled_value)) & ((1 << bits) - 1)


def _float_from_bits_half(raw: int) -> float:
    """Converts a raw half-precision float without struct support."""
    s = (raw >> 15) & 0x0001
    e = (raw >> 10) & 0x001F
    f = raw & 0x03FF

    if e == 0:
        if f == 0:
            return (-1)**s * 0.0
        return (-1)**s * (f / 2**10) * 2**(-14)
    if e == 31:
        if f == 0:
            return float('inf') if s == 0 else float('-inf')
        return float('nan')
    return (-1)**s * (1 + f / 2**10) * 2**(e - 15)


def _float_to_bits_half(value: float) -> int:
    """Converts a Python float to half-precision bits without struct support."""
    sign = 1 if math.copysign(1.0, value) < 0 else 0
    v = abs(value)

    if v == 0.0:
        return sign << 15
    if math.isnan(value):
        return 0x7E00
    if math.isinf(value):
        return (sign << 15) | 0x7C00

    e = int(math.floor(math.log(v, 2)))
    mant = v / (2**e) - 1.0

    exp = e + 15
    frac = int(mant * (2**10))
    return (sign << 15) | (exp << 10) | frac


def _build_float_from_bits_dispatch() -> dict[int, callable]:
    """Builds a dispatch table for converting raw bits to floats."""
    return {
        16: (lambda raw: struct.unpack('>e', struct.pack('>H', raw))[0])
        if _has_struct_half() else _float_from_bits_half,
        32:
        lambda raw: struct.unpack('>f', struct.pack('>I', raw))[0],
        64:
        lambda raw: struct.unpack('>d', struct.pack('>Q', raw))[0],
    }


def _build_float_to_bits_dispatch() -> dict[int, callable]:
    """Builds a dispatch table for converting floats to raw bits."""
    return {
        16: (lambda value: struct.unpack('>H', struct.pack('>e', value))[0])
        if _has_struct_half() else _float_to_bits_half,
        32:
        lambda value: struct.unpack('>I', struct.pack('>f', value))[0],
        64:
        lambda value: struct.unpack('>Q', struct.pack('>d', value))[0],
    }


FLOAT_FROM_BITS_DISPATCH = _build_float_from_bits_dispatch()
FLOAT_TO_BITS_DISPATCH = _build_float_to_bits_dispatch()
