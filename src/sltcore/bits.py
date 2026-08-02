"""Bit-level operations for structured data layouts."""
from sltcore.types import Info, InfoSize


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
    if offset.bit == 0 and size.bit == 0:
        return Info(raw_value=buf[offset.byte:offset.byte + size.byte],
                    info_size=size)

    # Correct byte span (handles cross-byte bit ranges)
    need = _required_bytes_for_extraction(offset, size)

    # Extract bytes
    chunk = buf[offset.byte:offset.byte + need]
    value = int.from_bytes(chunk, "big")

    # Front-pack
    shift = (need * 8) - size.bits - offset.bit
    value >>= shift

    # Mask to exact bit length
    value &= (1 << size.bits) - 1

    return Info(raw_value=value, info_size=size)


def bits_set(buf: bytearray, offset: InfoSize, size: InfoSize,
             value: int | bytearray) -> None:
    """
    Set a bit slice in `buf` starting at `offset` and spanning `size`.
    `value` is an integer whose lower `size.bits` bits are written.
    """
    if isinstance(value, bytearray):
        if offset.bit == 0 and size.bit == 0:
            buf[offset.byte:offset.byte + size.byte] = value[:size.byte]
            return
        value = int.from_bytes(value[:size.bytes], "big") & size.mask

    # Correct byte span
    need = _required_bytes_for_extraction(offset, size)

    start = offset.byte
    end = start + need

    # Read existing bytes
    chunk = int.from_bytes(buf[start:end], "big")

    # Compute shift
    shift = (need * 8) - size.bits - offset.bit

    # Build mask
    mask = ((1 << size.bits) - 1) << shift

    # Clear target field and insert new value
    chunk = (chunk & ~mask) | ((value << shift) & mask)

    # Write back
    buf[start:end] = chunk.to_bytes(need, "big")


def _required_bytes_for_extraction(offset: InfoSize, size: InfoSize) -> int:
    """
    Calculates the number of bytes required to extract a bit slice
    starting at the given offset and spanning the given size.

    Parameters:
    - offset (InfoSize): The bit offset from the start of the buffer.
    - size (InfoSize): The number of bits to extract.

    Returns:
    - int: The number of bytes required to extract the specified bit slice.
    """
    return (offset.bit + size.bits + 7) // 8
