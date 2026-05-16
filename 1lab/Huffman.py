def build_canonical_codes(code_lengths):
    # Вход: {символ: длина_кода}
    # Возвращает: {символ: строка_битов}
    items = sorted(code_lengths.items(), key=lambda x: (x[1], x[0]))
    codes = {}
    cur_code = 0
    prev_len = 0
    for ch, length in items:
        if length > prev_len:
            cur_code <<= (length - prev_len)
        code_bin = bin(cur_code)[2:].zfill(length)
        codes[ch] = code_bin
        cur_code += 1
        prev_len = length
    return codes

def huffman_encode_canonical(data):
    # data: байты
    # Возвращает (сжатые_данные, {символ: длина_кода}, добавленные_биты)
    if not data:
        return b"", {}, 0

    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1

    # Построение дерева Хаффмана
    nodes = [[f, c, None, None] for c, f in freq.items()]
    while len(nodes) > 1:
        nodes.sort(key=lambda x: x[0])
        left = nodes.pop(0)
        right = nodes.pop(0)
        nodes.append([left[0] + right[0], None, left, right])
    root = nodes[0]

    # Получение длин кодов обходом в глубину
    code_lengths = {}
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if node[1] is not None:          # лист
            code_lengths[node[1]] = depth
        else:
            stack.append((node[2], depth + 1))
            stack.append((node[3], depth + 1))

    # Единственный уникальный символ: принудительная длина 1
    if len(code_lengths) == 1:
        ch = next(iter(code_lengths))
        code_lengths[ch] = 1

    codes = build_canonical_codes(code_lengths)

    # Кодирование
    bits = "".join(codes[b] for b in data)
    pad = (8 - len(bits) % 8) % 8
    bits += "0" * pad
    enc = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
    return enc, code_lengths, pad

def huffman_decode_canonical(enc, codes, pad):
    if not enc:
        return b""
    bits = "".join(f"{b:08b}" for b in enc)
    bits = bits[:len(bits) - pad] if pad else bits
    rev = {code: char for char, code in codes.items()}
    res = bytearray()
    cur = ""
    for bit in bits:
        cur += bit
        if cur in rev:
            res.append(rev[cur])
            cur = ""
    return bytes(res)

def pack_huffman(enc, code_lengths, pad):
    # Формат: pad(1), количество_символов(2),
    # для каждого: символ(1), длина_кода(1), потом сжатые данные.
    out = bytearray()
    out.append(pad)
    out.extend(len(code_lengths).to_bytes(2, 'big'))
    for ch, length in code_lengths.items():
        out.append(ch)
        out.append(length)
    out.extend(enc)
    return bytes(out)


def unpack_huffman(data):
    if len(data) < 3:
        print("len(data) < 3")
    pad = data[0]
    num = int.from_bytes(data[1:3], 'big')
    pos = 3
    code_lengths = {}
    for _ in range(num):
        if pos + 2 > len(data):
            print("pos + 2 > len(data)")
        ch = data[pos]
        length = data[pos+1]
        pos += 2
        code_lengths[ch] = length
    enc = data[pos:]
    return enc, code_lengths, pad

# Cжатие и распаковка одной байтовой строки
def huffman_compress(data):
    enc, code_lengths, pad = huffman_encode_canonical(data)
    return pack_huffman(enc, code_lengths, pad)

def huffman_decompress(compressed):
    enc, code_lengths, pad = unpack_huffman(compressed)
    codes = build_canonical_codes(code_lengths)
    return huffman_decode_canonical(enc, codes, pad)

if __name__ == "__main__":
    test_data = b"abracadabra"
    print(test_data)
    compressed = huffman_compress(test_data)
    decompressed = huffman_decompress(compressed)
    if decompressed == test_data:
        print("OK\n")
    else:
        print("ERROR\n")

    single_data = b"aaaa"
    print(single_data)
    comp_single = huffman_compress(single_data)
    decomp_single = huffman_decompress(comp_single)
    if decomp_single == single_data:
        print("OK\n")
    else:
        print("ERROR\n")