def mtf_encode(data: bytes) -> bytes:
    table = bytearray(range(256))
    out = bytearray()
    for b in data:
        i = 0
        while table[i] != b:
            i += 1
        out.append(i)
        table = bytearray([b]) + table[:i] + table[i+1:]
    return bytes(out)

def mtf_decode(data: bytes) -> bytes:
    table = bytearray(range(256))
    out = bytearray()
    for idx in data:
        b = table[idx]
        out.append(b)
        table = bytearray([b]) + table[:idx] + table[idx+1:]
    return bytes(out)

if __name__ == "__main__":
    test_data = b"abracadabra"
    encoded = mtf_encode(test_data)
    decoded = mtf_decode(encoded)
    print(f"Original: {test_data}")
    print(f"Encoded: {encoded}")
    print(f"Decoded: {decoded}")
    assert test_data == decoded
    print("Тестирование завершено!")