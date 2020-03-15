import sys

digit_encoding = [
    0x7E,
    0x30,
    0x6D,
    0x79,
    0x33,
    0x5B,
    0x5F,
    0x70,
    0x7F,
    0x7B,
]


def binary_digits(value):
    sign = int(value < 0)
    digits = tuple(f"{abs(value):03}")
    bits = tuple(digit_encoding[int(_)] for _ in digits)
    return (sign,) + bits


def write_unsigned(data):
    for address in range(256):
        sign, hundreds, tens, units = binary_digits(address)
        data[address] = units
        data[address + 256] = tens
        data[address + 512] = hundreds
        data[address + 768] = sign


def write_signed(data):
    values = list(range(128)) + list(range(-128, 0))
    for offset, value in enumerate(values):
        sign, hundreds, tens, units = binary_digits(value)
        address = 1024 + offset
        data[address] = units
        data[address + 256] = tens
        data[address + 512] = hundreds
        data[address + 768] = sign


def main():
    data = bytearray([0] * 2048)
    write_unsigned(data)
    write_signed(data)
    sys.stdout.buffer.write(data)


if __name__ == "__main__":
    main()
