"""Bit-level operations for structured data layouts."""
from src.sltcore.types import Info, InfoSize


def bits_get(buf: bytearray, offset: InfoSize, size: InfoSize) -> Info:
    """ Extracts a slice of bits from the given bytearray
        starting at the specified bit offset and spanning
        the specified bit size. Returns an Info object containing
        the extracted raw value and an InfoSize representing 
        the size of the extracted data.
    Parameters:
    - buf (bytearray): The source bytearray to extract bits from.
    - offset (InfoSize): The bit offset from the start of buf to begin
      extraction.
    - size (InfoSize): The number of bits to extract.

    Returns:
    - Info: An Info object where raw_value contains the extracted bits as an
      integer, and info_size indicates the size of the extracted data.

    Notes:
    - The extraction returns the bits as an integer in the raw_value
      field of the Info object.
    - Only the necessary byte range is extracted.
    - Leading and trailing unwanted bits are masked out.
    - The returned Info object's raw_value is front-packed, meaning
      the first bit of the extracted range aligns with the most
      significant bit of raw_value.
    """
    # Extract only the necessary byte range
    chunk = buf[offset.byte:offset.byte + size.required_bytes]

    # Convert to int
    value = int.from_bytes(chunk, "big")

    # Right-shift to front-pack the extracted bits
    shift = (size.required_bytes * 8) - size.bits - offset.bit
    if shift > 0:
        value >>= shift

    # Mask to exact bit length
    value &= (1 << size.bits) - 1

    return Info(raw_value=value, info_size=size)


def bits_set(buf: bytearray, offset: InfoSize, size: InfoSize,
             value: int) -> None:
    """
    Set a bit slice in `buf` starting at `offset` and spanning `size`.
    `value` is an integer whose lower `size.bits` bits are written.
    """

    # Extract the target byte range
    start = offset.byte
    end = start + size.required_bytes

    # Read existing bytes as int
    chunk = int.from_bytes(buf[start:end], "big")

    # Compute shift amount (same as bits_get)
    shift = (size.required_bytes * 8) - size.bits - offset.bit

    # Build mask for the target bitfield
    mask = ((1 << size.bits) - 1) << shift

    # Clear the target field and insert new value
    chunk = (chunk & ~mask) | ((value << shift) & mask)

    # Write back
    buf[start:end] = chunk.to_bytes(size.required_bytes, "big")
