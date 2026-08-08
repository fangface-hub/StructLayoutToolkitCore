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

from sltcore import InfoSize, Info, bits_get, bits_set

buf = bytearray(b"\x12\x34\x56\x78")

# Extract 4 bits at offset (1 byte, 0 bits)
value = bits_get(buf, InfoSize(1, 0), InfoSize(0, 4))
print(value.to_hex)  # 0x3

# Write 5 bits at offset (2 bytes, 3 bits)
bits_set(
  buf,
  InfoSize(2, 3),
  Info(0b10101, InfoSize(0, 5)),
)
print(buf.hex()) # 12345578

```

## sltcore.InfoSize

InfoSize is a type that represents offsets and sizes in a unified way.
It supports addition, subtraction, multiplication, and division by integers, and stores both byte and bit components.

Multiplication scales the size by an integer factor, while division uses floor division for positive integer divisors. This makes it easy to express repeated sizes or half-sized layouts in a consistent way.

```python
size = InfoSize(1, 2)
print(size * 3)   # 3 * (1 byte, 2 bits)
print(size / 2)   # floor division by 2
```

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

- __JSON Conversion__

  | Method | Description |
  | --- | --- |
  | to_json | Serializes InfoSize to a JSON string. |
  | from_json | Deserializes InfoSize from a JSON string or dict payload. |

  Example:

  ```python
  size = InfoSize(byte=1, bit=10)  # normalized to (2, 2)
  json_text = size.to_json()

  restored = InfoSize.from_json(json_text)
  print(restored.byte, restored.bit)  # 2 2
  ```

## sltcore.Info

Info stores an InfoSize and a raw integer value.

It also supports an optional `scale` value, which defaults to `1.0` and
represents the value of one least-significant bit.

The scaled conversion helpers use this field when converting between raw
values and numeric values. In particular, `from_float` and `from_int`
divide by `scale` before storing raw data, and `to_float` and `to_int`
multiply the stored value by `scale` when reading it back.

This allows higher‑level code to treat extracted fields as structured units rather than plain integers.

- __Field List__

  | Field | Type | Description |
  | --- | --- | --- |
  | raw_value | int or bytearray | The internal integer representation of the field.<br>It is obtained by converting the corresponding bytes into an integer and applying the size mask so that the value fits within the bit width specified by InfoSize. |
  | info_size | InfoSize | Size descriptor for this value.<br>It provides the byte and bit length of the field and determines how the raw_value is masked, extracted, and written back into the byte sequence. |

- __Classmethod List__

  | Classmethod | Description |
  | --- | --- |
  | from_bool | Creates an Info instance from a boolean value. |
  | from_signed_int | Creates an Info instance from a signed integer value using two's-complement encoding for the requested bit width. |
  | from_unsigned_int | Creates an Info instance from an unsigned integer value while masking it to the requested bit width. |
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

- __JSON Conversion__

  | Method | Description |
  | --- | --- |
  | to_json | Serializes Info to a JSON string. |
  | from_json | Deserializes Info from a JSON string or dict payload. |

  Notes:

  - For integer raw values, payload stores `raw_value.type = "int"`.
  - For bytearray raw values, payload stores `raw_value.type = "bytearray"` and hex text.
  - `scale` is preserved in both directions.

  Example:

  ```python
  info = Info.from_unsigned_int(0x2A, InfoSize(0, 8), scale=0.5)
  json_text = info.to_json()

  restored = Info.from_json(json_text)
  print(restored.raw_value)  # 42
  print(restored.scale)      # 0.5

  info_bytes = Info.from_bytearray(bytearray([0xAA, 0xBB]), InfoSize(2, 0))
  restored_bytes = Info.from_json(info_bytes.to_json())
  print(restored_bytes.to_bytes.hex())  # aabb
  ```

Example: Creating an Info with a scale

```python
size = InfoSize(byte=0, bit=10)
info = Info.from_int(5, size, scale=0.5)

print(info.raw_value)  # 10
print(info.to_float)   # 5.0
```

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
