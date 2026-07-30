# StructLayoutToolkitCore

stlcore is a minimal, high‑cohesion core library for bit‑accurate binary slicing. It provides the fundamental primitives (bits_get, bits_set, InfoSize) required to build struct layout analyzers, binary editors, protocol inspectors, and low‑level testing tools. Designed for clarity, correctness, and composability.

## What You Can Do After Installing sltcore

sltcore provides a minimal and consistent bit-level abstraction layer for building higher‑level tools such as binary editors, protocol analyzers, and structured layout systems.

After installing the package, you can:

- Extract arbitrary bit ranges from a bytearray using bits_get
- Write arbitrary bit ranges into a bytearray using bits_set
- Represent sizes and offsets uniformly with InfoSize
- Build structured binary layouts on top of a stable bit‑operation core

## Quick Examples: bits_get / bits_set

```python

from sltcore.types import InfoSize, Info
from sltcore.bits import bits_get, bits_set

buf = bytearray(b"\x12\x34\x56\x78")

# Extract 4 bits at offset (1 byte, 0 bits)
value = bits_get(buf, InfoSize(1, 0), InfoSize(0, 4))
print(value.to_hex)  # 0x3

# Write 5 bits at offset (2 bytes, 3 bits)
bits_set(buf, InfoSize(2, 3), InfoSize(0, 5), 0b10101)
print(buf.hex()) # 12345578

```

## sltcore.type.InfoSize

InfoSize is a type that represents offsets and sizes in a unified way.
It supports addition and subtraction, and stores both byte and bit components.

- byte: the byte component
- bit: the bit component (0–7)

always normalized so that bit < 8

It is used for both offset and size, allowing consistent structural layout definitions.

## sltcore.type.Info

Info stores an InfoSize and a raw integer value.

- The value returned by bits_get is an Info instance
- The value passed to bits_set is also an Info instance

This allows higher‑level code to treat extracted fields as structured units rather than plain integers.

## sltcore.bits.bits_get

bits_get extracts a field from a bytearray using an offset and size, and returns an Info object.

Input:

- bytearray buffer
- InfoSize offset
- InfoSize size

Output:

- Info containing the extracted value and its size

## sltcore.bits.bits_set

bits_set writes a value into a bytearray at the specified offset.

Input:

- bytearray buffer
- InfoSize offset
- Info value (which includes its size)

The function masks and replaces the target bit range inside the buffer.

## Documentation

For detailed usage, examples, and parameter descriptions, refer to the docstrings via:

python

- help(sltcore.type.InfoSize)
- help(sltcore.type.Info)
- help(sltcore.bits.bits_get)
- help(sltcore.bits.bits_set)
