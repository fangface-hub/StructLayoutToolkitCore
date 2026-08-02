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

from sltcore import InfoSize, Info , bits_get, bits_set

buf = bytearray(b"\x12\x34\x56\x78")

# Extract 4 bits at offset (1 byte, 0 bits)
value = bits_get(buf, InfoSize(1, 0), InfoSize(0, 4))
print(value.to_hex)  # 0x3

# Write 5 bits at offset (2 bytes, 3 bits)
bits_set(buf, InfoSize(2, 3), InfoSize(0, 5), 0b10101)
print(buf.hex()) # 12345578

```

## sltcore.InfoSize

InfoSize is a type that represents offsets and sizes in a unified way.
It supports addition and subtraction, and stores both byte and bit components.

It is used for both offset and size, allowing consistent structural layout definitions.

- __Field List__

  | Field | Type | Description |
  | --- | --- | --- |
  | byte | int | the byte size |
  | bit  | int | the bit size (0–7)<br> always normalized so that bit < 8 |

- __Property List__

  | Property | Type | Description |
  | --- | --- | --- |
  | bits | int | Total bit length.<br> This property converts the stored byte and bit components into a single bit count using the formula byte * 8 + bit |
  | bytes | int | Total byte length.<br> This property converts the combined bit length (byte * 8 + bit) into a byte count using integer division (bits // 8) |
  | hex_digits | int | Number of hexadecimal digits needed to represent the field.<br>Since one hex digit corresponds to 4 bits, the value is calculated as ceil(bits / 4) |
  | mask | int | Bitmask for the field size.<br>It produces a mask that covers exactly bits bits, using the formula (1 << bits) - 1.<br>This mask is typically used for extracting or normalizing values. |

## sltcore.Info

Info stores an InfoSize and a raw integer value.

This allows higher‑level code to treat extracted fields as structured units rather than plain integers.

- __Field List__

  | Field | Type | Description |
  | --- | --- | --- |
  | raw_value | int or bytearray | The internal integer representation of the field.<br>It is obtained by converting the corresponding bytes into an integer and applying the size mask so that the value fits within the bit width specified by InfoSize. |
  | info_size | InfoSize | Size descriptor for this value.<br>It provides the byte and bit length of the field and determines how the raw_value is masked, extracted, and written back into the byte sequence. |

- __Classmethod List__

  | Classmethod | Description |
  | --- | --- |
  | from_int | Creates an Info instance from an integer value, ensuring that the value fits within the specified size by applying a bitmask. |
  | from_bytes | Creates an Info instance from a bytes object, ensuring that the value fits within the specified size by applying a bitmask. |
  | from_bytearray | Creates an Info instance from a bytearray, ensuring that the value fits within the specified size by applying a bitmask. |
  | from_float | Creates an Info instance from a float value, converting it to its raw bit representation based on the specified size. |

  Example: Creating an Info from a float value
  
  ```python
  size = InfoSize(byte=0, bit=32)   # 32-bit float
  info = Info.from_float(3.14, size)
  
  print(info.raw_value)     # IEEE754 raw bits (e.g., 0x4048F5C3)
  print(info.info_size.bits)  # 32
  ```

- __Property List__

  | Property | Type | Description |
  | --- | --- | --- |
  | to_unsigned_int | int | Returns the extracted bits as an unsigned integer. |
  | to_signed_int | int | Returns the extracted bits as a signed integer. |
  | to_hex | str | Returns the extracted bits as a hexadecimal string. |
  | to_bytes | bytes | Returns the extracted bits as a bytes object. |
  | to_bool | bool | Returns the extracted bits as a boolean value. |
  | to_float | float | Returns the extracted bits as a float. |
  | byte_swap | Info | Returns a new Info instance with the byte order reversed. |

## sltcore.bits_get

bits_get extracts a field from a bytearray using an offset and size, and returns an Info object.

Input:

- bytearray buffer
- InfoSize offset
- InfoSize size

Output:

- Info containing the extracted value and its size

## sltcore.bits_set

bits_set writes a value into a bytearray at the specified offset.

Input:

- bytearray buffer
- InfoSize offset
- Info value (which includes its size)

The function masks and replaces the target bit range inside the buffer.

## Documentation

For detailed usage, examples, and parameter descriptions, refer to the docstrings via:

python

- help(sltcore.InfoSize)
- help(sltcore.Info)
- help(sltcore.bits_get)
- help(sltcore.bits_set)
